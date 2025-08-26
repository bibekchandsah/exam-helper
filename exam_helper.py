import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import time
import json
import os
from datetime import datetime
import logging
import numpy as np

# Import modules for different functionalities
from ocr_module import OCRCapture
from audio_module import AudioCapture
from llm_module import LLMClient
from stealth_module import StealthWindow
from screenshot_module import ScreenshotCapture
from gemini_module import GeminiClient
from perplexity_module import PerplexityClient

class ExamHelper:
    def __init__(self):
        self.setup_logging()
        self.load_config()
        
        # Initialize components
        self.ocr_capture = OCRCapture()
        self.audio_capture = AudioCapture()
        self.screenshot_capture = ScreenshotCapture()
        self.llm_client = LLMClient(self.config.get('openai_api_key', ''), self.config.get('openai_model', 'gpt-3.5-turbo'))
        self.gemini_client = GeminiClient(self.config.get('gemini_api_key', ''))
        self.perplexity_client = PerplexityClient(self.config.get('perplexity_api_key', ''))
        
        # Threading and queues
        self.question_queue = queue.Queue()
        self.answer_queue = queue.Queue()
        self.running = True
        
        # Store last AI response for copying
        self.last_ai_response = ""
        
        # Thread control flags
        self.ocr_running = False
        self.audio_running = False
        self.live_screen_running = False
        self.last_ai_response = ""  # Store the last AI response for copying
        self.ocr_thread = None
        self.audio_thread = None
        self.live_screen_thread = None
        
        # GUI setup
        self.setup_gui()
        self.setup_stealth()
        self.setup_hotkeys()
        
        # Start background threads
        self.start_background_threads()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('exam_helper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_config(self):
        """Load configuration from config.json"""
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {
                'openai_api_key': '',
                'gemini_api_key': '',
                'perplexity_api_key': '',
                'scan_interval': 3,
                'live_screen_interval': 5,
                'audio_enabled': True,
                'ocr_enabled': True,
                'live_screen_enabled': False,
                'response_mode': 'short',  # 'short' or 'detailed'
                'always_on_top': True,
                'openai_model': 'gpt-3.5-turbo',
                'gemini_model': 'gemini-1.5-flash',
                'working_models': [],
                'working_gemini_models': [],
                'selected_image_model': 'OpenAI GPT-4o',  # Default image recognition model
                'use_custom_prompt': False,  # Whether to use custom prompt or hardcoded prompt
                'custom_image_prompt': "What's in this image? Please analyze and describe what you see."  # Default prompt
            }
            self.save_config()
            
    def save_config(self):
        """Save configuration to config.json"""
        with open('config.json', 'w') as f:
            json.dump(self.config, f, indent=2)
        
        # Update LLM client with new model if it changed
        if hasattr(self, 'llm_client') and self.llm_client:
            new_model = self.config.get('openai_model', 'gpt-3.5-turbo')
            if self.llm_client.get_current_model() != new_model:
                self.llm_client.set_model(new_model)
                self.logger.info(f"Updated LLM model to: {new_model}")
                
                # Update model label in GUI
                if hasattr(self, 'model_label'):
                    self.model_label.config(text=f"🤖 {new_model}")
        
        # Update API key if it changed
        if hasattr(self, 'llm_client') and self.llm_client:
            new_api_key = self.config.get('openai_api_key', '')
            if self.llm_client.api_key != new_api_key:
                self.llm_client.api_key = new_api_key
                if new_api_key:
                    from openai import OpenAI
                    self.llm_client.client = OpenAI(api_key=new_api_key)
                    # Reset model checking when API key changes
                    self.llm_client.models_checked = False
                    self.llm_client.working_models = []
                else:
                    self.llm_client.client = None
        
        # Refresh response model dropdown if working models changed
        self.refresh_response_model_dropdown()
    
    def refresh_response_model_dropdown(self):
        """Refresh the response model dropdown with updated working models"""
        if hasattr(self, 'response_model_combo'):
            # Update response models with new working models
            self.response_models = {}
            
            # Add OpenAI models from config
            working_models = self.config.get('working_models', [])
            if not working_models:
                working_models = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo', 'gpt-4o', 'gpt-4o-mini']
            
            for model in working_models:
                self.response_models[f"OpenAI {model}"] = f"openai_{model}"
            
            # Add Gemini models
            gemini_models = {
                'Gemini 1.5 Flash': 'gemini_flash',
                'Gemini 1.5 Pro': 'gemini_pro'
            }
            self.response_models.update(gemini_models)
            
            # Update dropdown values
            self.response_model_combo['values'] = list(self.response_models.keys())
            
            # Ensure current selection is still valid
            current_selection = self.selected_response_model.get()
            if current_selection not in self.response_models:
                # Set to current openai_model from config
                current_model = self.config.get('openai_model', 'gpt-4o')
                display_model = f"OpenAI {current_model}"
                if display_model in self.response_models:
                    self.selected_response_model.set(display_model)
                elif self.response_models:
                    # Fallback to first available model
                    self.selected_response_model.set(list(self.response_models.keys())[0])
    
    def center_window(self, window, width, height):
        """Center a window on the screen"""
        # Get screen dimensions
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        # Calculate position coordinates
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # Set window geometry
        window.geometry(f"{width}x{height}+{x}+{y}")
    
    def setup_gui(self):
        """Setup the modern GUI window"""
        self.root = tk.Tk()
        self.root.title("✨ Exam Helper Pro")
        
        # Set window icon
        try:
            # For PNG files, use iconphoto directly
            if os.path.exists("icon.png"):
                icon_image = tk.PhotoImage(file="icon.png")
                self.root.iconphoto(True, icon_image)
            elif os.path.exists("icon.ico"):
                # Use iconbitmap only for .ico files
                self.root.iconbitmap("icon.ico")
        except Exception as e:
            self.logger.warning(f"Could not load icon: {e}")
        
        # Set window size and center it
        window_width = 735
        window_height = 840
        self.center_window(self.root, window_width, window_height)
        
        # Modern dark theme colors
        self.colors = {
            'bg_primary': '#1a1a1a',      # Main background
            'bg_secondary': '#2d2d2d',    # Secondary background
            'bg_tertiary': '#3d3d3d',     # Tertiary background
            'accent': '#4a9eff',          # Blue accent
            'accent_hover': '#6bb6ff',    # Lighter blue
            'success': '#00d4aa',         # Green for success
            'warning': '#ffb347',         # Orange for warning
            'error': '#ff6b6b',           # Red for error
            'text_primary': '#ffffff',    # Primary text
            'text_secondary': '#b0b0b0',  # Secondary text
            'border': '#404040'           # Border color
        }
        
        # Configure modern styling
        self.root.configure(bg=self.colors['bg_primary'])
        
        # Make window always on top and floating (based on config)
        self.root.attributes('-topmost', self.config.get('always_on_top', True))
        self.root.attributes('-alpha', 0.96)
        
        # Setup modern ttk style
        self.setup_modern_style()
        
        # Create main frame with modern styling
        main_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Modern header with title and status
        header_frame = tk.Frame(main_frame, bg=self.colors['bg_secondary'], relief='flat', bd=0)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Title
        title_label = tk.Label(header_frame, text="🤖 AI Exam Assistant", 
                              font=('Segoe UI', 14, 'bold'),
                              fg=self.colors['text_primary'], 
                              bg=self.colors['bg_secondary'])
        title_label.pack(pady=10)
        
        # Status indicators frame
        status_frame = tk.Frame(header_frame, bg=self.colors['bg_secondary'])
        status_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        # Main status
        self.status_label = tk.Label(status_frame, text="● Ready", 
                                   font=('Segoe UI', 9),
                                   fg=self.colors['success'], 
                                   bg=self.colors['bg_secondary'])
        self.status_label.pack(side=tk.LEFT)
        
        # Model indicator
        model_name = self.config.get('openai_model', 'gpt-3.5-turbo')
        self.model_label = tk.Label(status_frame, text=f"🤖 {model_name}", 
                                   font=('Segoe UI', 8),
                                   fg=self.colors['text_secondary'], 
                                   bg=self.colors['bg_secondary'])
        self.model_label.pack(side=tk.LEFT, padx=(15, 0))
        
        # Status indicators with modern styling
        indicators_frame = tk.Frame(status_frame, bg=self.colors['bg_secondary'])
        indicators_frame.pack(side=tk.RIGHT)
        
        self.live_screen_status_label = tk.Label(indicators_frame, text="Live", 
                                               font=('Segoe UI', 8),
                                               fg=self.colors['error'], 
                                               bg=self.colors['bg_secondary'])
        self.live_screen_status_label.pack(side=tk.RIGHT, padx=(8, 0))
        
        self.ocr_status_label = tk.Label(indicators_frame, text="OCR", 
                                       font=('Segoe UI', 8),
                                       fg=self.colors['error'], 
                                       bg=self.colors['bg_secondary'])
        self.ocr_status_label.pack(side=tk.RIGHT, padx=(8, 0))
        
        self.audio_status_label = tk.Label(indicators_frame, text="Audio", 
                                         font=('Segoe UI', 8),
                                         fg=self.colors['error'], 
                                         bg=self.colors['bg_secondary'])
        self.audio_status_label.pack(side=tk.RIGHT, padx=(8, 0))
        
        # Modern control buttons frame
        control_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Create modern buttons with custom styling
        button_style = {
            'font': ('Segoe UI', 9),
            'relief': 'flat',
            'bd': 0,
            'padx': 8,
            'pady': 6,
            'cursor': 'hand2'
        }
        
        # Single row with all modern buttons
        control_row = tk.Frame(control_frame, bg=self.colors['bg_primary'])
        control_row.pack(fill=tk.X)
        
        # Hide button
        self.toggle_btn = tk.Button(control_row, text="👁️ Hide", 
                                   bg=self.colors['bg_tertiary'], 
                                   fg=self.colors['text_primary'],
                                   activebackground=self.colors['accent'],
                                   activeforeground='white',
                                   command=self.toggle_visibility, **button_style)
        self.toggle_btn.pack(side=tk.LEFT, padx=(0, 4))
        
        # Mode button
        self.mode_btn = tk.Button(control_row, text="⚡ Short", 
                                 bg=self.colors['bg_tertiary'], 
                                 fg=self.colors['text_primary'],
                                 activebackground=self.colors['accent'],
                                 activeforeground='white',
                                 command=self.toggle_response_mode, **button_style)
        self.mode_btn.pack(side=tk.LEFT, padx=(0, 4))
        

        
        # Audio toggle button
        self.audio_btn = tk.Button(control_row, text="🎤 Audio", 
                                  bg=self.colors['bg_tertiary'], 
                                  fg=self.colors['text_primary'],
                                  activebackground=self.colors['warning'],
                                  activeforeground='white',
                                  command=self.toggle_audio_scanning, **button_style)
        self.audio_btn.pack(side=tk.LEFT, padx=(0, 4))
        
        # Capture Screen button (merged functionality)
        self.capture_btn = tk.Button(control_row, text="📸 Capture Screen", 
                                    bg=self.colors['accent'], 
                                    fg='white',
                                    activebackground=self.colors['accent_hover'],
                                    activeforeground='white',
                                    command=self.capture_screen_with_selected_model, **button_style)
        self.capture_btn.pack(side=tk.LEFT, padx=(0, 4))
        
        # OCR Screen button
        self.ocr_screen_btn = tk.Button(control_row, text="📝 Extract", 
                                       bg=self.colors['accent'], 
                                       fg='white',
                                       activebackground=self.colors['accent_hover'],
                                       activeforeground='white',
                                       command=self.ocr_screen_now, **button_style)
        self.ocr_screen_btn.pack(side=tk.LEFT, padx=(0, 4))
        
        # Live Screen button
        self.live_screen_btn = tk.Button(control_row, text="🔴 Live", 
                                        bg=self.colors['error'], 
                                        fg='white',
                                        activebackground='#ff8a8a',
                                        activeforeground='white',
                                        command=self.toggle_live_screen, **button_style)
        self.live_screen_btn.pack(side=tk.LEFT, padx=(0, 4))
        
        # Always on top modern checkbox
        self.always_on_top_var = tk.BooleanVar(value=self.config.get('always_on_top', True))
        checkbox_frame = tk.Frame(control_row, bg=self.colors['bg_primary'])
        checkbox_frame.pack(side=tk.RIGHT)
        
        self.always_on_top_cb = tk.Checkbutton(
            checkbox_frame,
            text="📌 Always on Top",
            variable=self.always_on_top_var,
            command=self.toggle_always_on_top,
            bg=self.colors['bg_primary'],
            fg=self.colors['text_secondary'],
            selectcolor=self.colors['bg_tertiary'],
            activebackground=self.colors['bg_primary'],
            activeforeground=self.colors['text_primary'],
            font=('Segoe UI', 8),
            relief='flat',
            bd=0
        )
        self.always_on_top_cb.pack()
        
        # Image Model Selector Section
        model_section = tk.Frame(main_frame, bg=self.colors['bg_secondary'], relief='flat', bd=0)
        model_section.pack(fill=tk.X, pady=(0, 15))
        
        # Model selector header
        model_header_frame = tk.Frame(model_section, bg=self.colors['bg_secondary'])
        model_header_frame.pack(pady=(12, 8), fill=tk.X, padx=15)
        
        model_header = tk.Label(model_header_frame, text="🤖 Model Selection", 
                               font=('Segoe UI', 11, 'bold'),
                               fg=self.colors['text_primary'], 
                               bg=self.colors['bg_secondary'])
        model_header.pack(side=tk.LEFT)
        
        # Model selector dropdown frame - two columns
        model_selector_frame = tk.Frame(model_section, bg=self.colors['bg_secondary'])
        model_selector_frame.pack(fill=tk.X, padx=15, pady=(0, 12))
        
        # Left column - Image Recognition Model
        image_model_frame = tk.Frame(model_selector_frame, bg=self.colors['bg_secondary'])
        image_model_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        image_model_label = tk.Label(image_model_frame, text="📸 Image Recognition Model", 
                                    font=('Segoe UI', 9, 'bold'),
                                    fg=self.colors['text_secondary'], 
                                    bg=self.colors['bg_secondary'])
        image_model_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Available image models
        self.image_models = {
            'OpenAI GPT-4o': 'openai_gpt4o',
            'OpenAI GPT-4o-mini': 'openai_gpt4o_mini', 
            'OpenAI GPT-4 Turbo': 'openai_gpt4_turbo',
            'Gemini Pro Vision': 'gemini_pro_vision',
            'Gemini Flash': 'gemini_flash'
        }
        
        # Create styled combobox
        self.setup_model_selector_style()
        
        image_combo_frame = tk.Frame(image_model_frame, bg=self.colors['bg_secondary'])
        image_combo_frame.pack(fill=tk.X)
        
        self.selected_image_model = tk.StringVar(value=self.config.get('selected_image_model', 'OpenAI GPT-4o'))
        self.image_model_combo = ttk.Combobox(
            image_combo_frame,
            textvariable=self.selected_image_model,
            values=list(self.image_models.keys()),
            state='readonly',
            style='Modern.TCombobox',
            font=('Segoe UI', 9),
            width=22
        )
        self.image_model_combo.pack(side=tk.LEFT, padx=(0, 8))
        
        # Image model status indicator
        self.image_model_status_label = tk.Label(image_combo_frame, text="✅ Ready", 
                                               font=('Segoe UI', 8),
                                               fg=self.colors['success'], 
                                               bg=self.colors['bg_secondary'])
        self.image_model_status_label.pack(side=tk.LEFT)
        
        # Right column - AI Response Model
        response_model_frame = tk.Frame(model_selector_frame, bg=self.colors['bg_secondary'])
        response_model_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        response_model_label = tk.Label(response_model_frame, text="💬 AI Response Model", 
                                       font=('Segoe UI', 9, 'bold'),
                                       fg=self.colors['text_secondary'], 
                                       bg=self.colors['bg_secondary'])
        response_model_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Available response models (OpenAI + Gemini)
        self.response_models = {}
        
        # Add OpenAI models from config
        working_models = self.config.get('working_models', [])
        if not working_models:
            working_models = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo', 'gpt-4o', 'gpt-4o-mini']
        
        for model in working_models:
            self.response_models[f"OpenAI {model}"] = f"openai_{model}"
        
        # Add Gemini models
        gemini_models = {
            'Gemini 1.5 Flash': 'gemini_flash',
            'Gemini 1.5 Pro': 'gemini_pro'
        }
        self.response_models.update(gemini_models)
        
        response_combo_frame = tk.Frame(response_model_frame, bg=self.colors['bg_secondary'])
        response_combo_frame.pack(fill=tk.X)
        
        self.selected_response_model = tk.StringVar(value=self.config.get('openai_model', 'gpt-4o'))
        # Convert current model to display format
        current_model = self.config.get('openai_model', 'gpt-4o')
        display_model = f"OpenAI {current_model}"
        if display_model in self.response_models:
            self.selected_response_model.set(display_model)
        
        self.response_model_combo = ttk.Combobox(
            response_combo_frame,
            textvariable=self.selected_response_model,
            values=list(self.response_models.keys()),
            state='readonly',
            style='Modern.TCombobox',
            font=('Segoe UI', 9),
            width=22
        )
        self.response_model_combo.pack(side=tk.LEFT, padx=(0, 8))
        
        # Response model status indicator
        self.response_model_status_label = tk.Label(response_combo_frame, text="✅ Ready", 
                                                  font=('Segoe UI', 8),
                                                  fg=self.colors['success'], 
                                                  bg=self.colors['bg_secondary'])
        self.response_model_status_label.pack(side=tk.LEFT)
        
        # Bind model selection changes
        self.image_model_combo.bind('<<ComboboxSelected>>', self.on_image_model_change)
        self.response_model_combo.bind('<<ComboboxSelected>>', self.on_response_model_change)
        
        # Modern manual input section
        input_section = tk.Frame(main_frame, bg=self.colors['bg_secondary'], relief='flat', bd=0)
        input_section.pack(fill=tk.X, pady=(0, 15))
        
        # Input header with info button
        header_frame = tk.Frame(input_section, bg=self.colors['bg_secondary'])
        header_frame.pack(pady=(12, 8), fill=tk.X, padx=15)
        
        input_header = tk.Label(header_frame, text="💬 Ask a Question", 
                               font=('Segoe UI', 11, 'bold'),
                               fg=self.colors['text_primary'], 
                               bg=self.colors['bg_secondary'])
        input_header.pack(side=tk.LEFT)
        
        # Info button with hover effect
        info_btn = tk.Label(header_frame, text="ⓘ", 
                           font=('Segoe UI', 11),
                           fg=self.colors['text_secondary'], 
                           bg=self.colors['bg_secondary'],
                           cursor='hand2',
                           padx=4, pady=2)
        info_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Add smooth hover effect to info button
        def on_info_enter(event):
            info_btn.config(fg=self.colors['accent'], bg=self.colors['bg_tertiary'])
            # Subtle scale effect
            info_btn.config(font=('Segoe UI', 12))
        
        def on_info_leave(event):
            info_btn.config(fg=self.colors['text_secondary'], bg=self.colors['bg_secondary'])
            # Return to normal size
            info_btn.config(font=('Segoe UI', 11))
        
        info_btn.bind('<Enter>', on_info_enter)
        info_btn.bind('<Leave>', on_info_leave)
        
        # Create modern tooltip for info button
        def create_tooltip(widget, text):
            def on_enter(event):
                tooltip = tk.Toplevel()
                tooltip.wm_overrideredirect(True)
                
                # Calculate position to avoid screen edges
                x_pos = event.x_root + 15
                y_pos = event.y_root + 25
                
                # Adjust if tooltip would go off screen
                screen_width = tooltip.winfo_screenwidth()
                screen_height = tooltip.winfo_screenheight()
                
                if x_pos + 200 > screen_width:  # Approximate tooltip width
                    x_pos = event.x_root - 200
                if y_pos + 60 > screen_height:  # Approximate tooltip height
                    y_pos = event.y_root - 60
                
                tooltip.wm_geometry(f"+{x_pos}+{y_pos}")
                tooltip.configure(bg='black')
                
                # Make tooltip stay on top if main window is on top
                try:
                    if self.always_on_top_var.get():
                        tooltip.attributes('-topmost', True)
                        # Ensure it's really on top with multiple methods
                        tooltip.after(1, lambda: tooltip.lift())
                        tooltip.after(5, lambda: tooltip.focus_force())
                except:
                    # Fallback: check if main window is topmost
                    try:
                        if self.root.attributes('-topmost'):
                            tooltip.attributes('-topmost', True)
                            tooltip.after(1, lambda: tooltip.lift())
                            tooltip.after(5, lambda: tooltip.focus_force())
                    except:
                        pass
                
                # Create rounded-looking tooltip with shadow effect
                frame = tk.Frame(tooltip, bg='#1a1a1a', relief='flat', bd=0)
                frame.pack(padx=1, pady=1)
                
                label = tk.Label(frame, text=text,
                               bg='#1a1a1a', fg='#ffffff',
                               font=('Segoe UI', 9),
                               padx=12, pady=8,
                               justify=tk.LEFT)
                label.pack()
                
                widget.tooltip = tooltip
                
                # Auto-hide tooltip after 3 seconds
                tooltip.after(3000, lambda: on_leave(None))
                
            def on_leave(event):
                if hasattr(widget, 'tooltip'):
                    try:
                        widget.tooltip.destroy()
                        del widget.tooltip
                    except:
                        pass
                    
            widget.bind('<Enter>', on_enter)
            widget.bind('<Leave>', on_leave)
        
        # Add tooltip to info button
        create_tooltip(info_btn, "Enter = Submit Question\nShift+Enter = New Line")
        
        # Modern text input with rounded appearance
        input_container = tk.Frame(input_section, bg=self.colors['bg_tertiary'], relief='flat', bd=0)
        input_container.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        self.manual_input = tk.Text(input_container, 
                                   height=3, 
                                   wrap=tk.WORD,
                                   bg=self.colors['bg_tertiary'],
                                   fg=self.colors['text_primary'],
                                   insertbackground=self.colors['accent'],
                                   selectbackground=self.colors['accent'],
                                   selectforeground='white',
                                   font=('Segoe UI', 10),
                                   relief='flat',
                                   bd=0,
                                   padx=10,
                                   pady=8)
        self.manual_input.pack(fill=tk.X, padx=2, pady=2)
        
        # Add scroll handling for manual input
        def _on_input_scroll(event):
            # Allow normal scrolling but prevent propagation to parent widgets
            widget = event.widget
            if hasattr(widget, 'yview_scroll'):
                widget.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"
        
        self.manual_input.bind("<MouseWheel>", _on_input_scroll)
        
        # Add Enter key binding to submit question (Shift+Enter for new line)
        def _on_enter_key(event):
            # Check if Shift key is pressed (state & 0x1 for Shift)
            if event.state & 0x1:  # Shift key is pressed
                return  # Allow normal newline with Shift+Enter
            else:
                # Submit question on Enter only (no modifiers)
                self.submit_manual_question()
                return "break"  # Prevent default newline
        
        self.manual_input.bind("<Return>", _on_enter_key)
        
        # Add keyboard shortcuts for clear and copy
        def _on_clear_shortcut(event):
            self.clear_ai_responses()
            return "break"
        
        def _on_copy_shortcut(event):
            self.copy_last_response()
            return "break"
        
        self.root.bind("<Control-l>", _on_clear_shortcut)
        self.root.bind("<Control-Shift-C>", _on_copy_shortcut)
        
        # Modern submit button
        submit_btn = tk.Button(input_section, text="🚀 Submit Question", 
                              bg=self.colors['success'], 
                              fg='white',
                              activebackground='#00f5c4',
                              activeforeground='white',
                              font=('Segoe UI', 9, 'bold'),
                              relief='flat',
                              bd=0,
                              padx=20,
                              pady=8,
                              cursor='hand2',
                              command=self.submit_manual_question)
        submit_btn.pack(pady=(0, 12))
        
        # Modern answer display section
        answer_section = tk.Frame(main_frame, bg=self.colors['bg_secondary'], relief='flat', bd=0)
        answer_section.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # AI Responses section header with buttons
        response_header_frame = tk.Frame(answer_section, bg=self.colors['bg_secondary'])
        response_header_frame.pack(pady=(12, 8), fill=tk.X, padx=15)
        
        answer_header = tk.Label(response_header_frame, text="🤖 AI Responses", 
                                font=('Segoe UI', 11, 'bold'),
                                fg=self.colors['text_primary'], 
                                bg=self.colors['bg_secondary'])
        answer_header.pack(side=tk.LEFT)
        
        # Clear button for AI responses
        clear_btn = tk.Button(response_header_frame, text="🗑️ Clear", 
                             font=('Segoe UI', 9),
                             fg='white',
                             bg='#dc3545',  # Red color for clear action
                             activebackground='#c82333',
                             activeforeground='white',
                             relief='flat',
                             bd=0,
                             padx=8,
                             pady=4,
                             cursor='hand2',
                             command=self.clear_ai_responses)
        clear_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Copy button for last response
        copy_btn = tk.Button(response_header_frame, text="📋 Copy Last", 
                            font=('Segoe UI', 9),
                            fg='white',
                            bg='#28a745',  # Green color for copy action
                            activebackground='#218838',
                            activeforeground='white',
                            relief='flat',
                            bd=0,
                            padx=8,
                            pady=4,
                            cursor='hand2',
                            command=self.copy_last_response)
        copy_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Modern scrolled text with dark theme
        display_container = tk.Frame(answer_section, bg=self.colors['bg_tertiary'], relief='flat', bd=0)
        display_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 12))
        
        # Create custom ScrolledText with dark-themed scrollbar
        text_frame = tk.Frame(display_container, bg=self.colors['bg_tertiary'])
        text_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Add hover effects and tooltips for both buttons
        def create_button_effects(button, normal_color, hover_color, tooltip_text):
            def on_hover_enter(event):
                button.config(bg=hover_color)
                
                def show_tooltip():
                    if hasattr(button, '_hover_active') and button._hover_active:
                        tooltip = tk.Toplevel()
                        tooltip.wm_overrideredirect(True)
                        tooltip.wm_geometry(f"+{event.x_root+15}+{event.y_root+25}")
                        tooltip.configure(bg='black')
                        
                        try:
                            if self.always_on_top_var.get():
                                tooltip.attributes('-topmost', True)
                        except:
                            pass
                        
                        frame = tk.Frame(tooltip, bg='#1a1a1a', relief='flat', bd=0)
                        frame.pack(padx=1, pady=1)
                        
                        label = tk.Label(frame, text=tooltip_text,
                                       bg='#1a1a1a', fg='#ffffff',
                                       font=('Segoe UI', 9),
                                       padx=12, pady=8,
                                       justify=tk.LEFT)
                        label.pack()
                        
                        button.tooltip = tooltip
                
                button._hover_active = True
                button.after(800, show_tooltip)
            
            def on_hover_leave(event):
                button.config(bg=normal_color)
                button._hover_active = False
                
                if hasattr(button, 'tooltip'):
                    try:
                        button.tooltip.destroy()
                        del button.tooltip
                    except:
                        pass
            
            button.bind('<Enter>', on_hover_enter)
            button.bind('<Leave>', on_hover_leave)
        
        # Apply effects to buttons
        create_button_effects(clear_btn, '#dc3545', '#c82333', 
                            "Clear all AI responses\nShortcut: Ctrl+L\nRequires confirmation")
        create_button_effects(copy_btn, '#28a745', '#218838', 
                            "Copy last AI response\nShortcut: Ctrl+Shift+C")
        
        text_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Create Text widget
        self.answer_display = tk.Text(
            text_frame,
            wrap=tk.WORD,
            height=12,
            bg=self.colors['bg_tertiary'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['accent'],
            selectbackground=self.colors['accent'],
            selectforeground='white',
            font=('Segoe UI', 10),
            relief='flat',
            bd=0,
            padx=12,
            pady=10,
            state='disabled'  # Make it read-only by default
        )
        
        # Create custom dark scrollbar with better visibility
        scrollbar = tk.Scrollbar(
            text_frame,
            orient='vertical',
            command=self.answer_display.yview,
            bg='#404040',                   # Slightly lighter dark background
            troughcolor='#1e1e1e',          # Very dark trough
            activebackground='#606060',     # More visible active state
            highlightbackground='#404040',  # Match background
            highlightcolor='#404040',       # Match background
            borderwidth=0,                  # No border
            relief='flat',                  # Flat relief
            width=16,                       # Wider for better visibility
            elementborderwidth=0            # No element border
        )
        
        # Configure text widget to use scrollbar
        self.answer_display.config(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.answer_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add scrollbar reference for compatibility
        self.answer_display.vbar = scrollbar
        

        
        # Add scroll handling for answer display and its scrollbar
        def _on_answer_scroll(event):
            # Allow normal scrolling but prevent propagation to parent widgets
            widget = event.widget
            if hasattr(widget, 'yview_scroll'):
                widget.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"
        
        self.answer_display.bind("<MouseWheel>", _on_answer_scroll)
        
        # Audio visualization frame (bottom left)
        self.audio_viz_frame = tk.Frame(main_frame, bg=self.colors['bg_secondary'], relief='flat', bd=0)
        # Initially hidden - will be shown when audio is enabled
        
        # Audio visualization header
        audio_viz_header = tk.Label(self.audio_viz_frame, text="Audio Level Monitor", 
                                   font=('Segoe UI', 10, 'bold'),
                                   fg=self.colors['text_primary'], 
                                   bg=self.colors['bg_secondary'])
        audio_viz_header.pack(pady=(10, 5))
        
        # Audio level display frame
        level_frame = tk.Frame(self.audio_viz_frame, bg=self.colors['bg_secondary'])
        level_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        # Current level label
        self.audio_level_label = tk.Label(level_frame, text="Level: 0", 
                                         font=('Segoe UI', 9),
                                         fg=self.colors['text_primary'], 
                                         bg=self.colors['bg_secondary'])
        self.audio_level_label.pack(side=tk.LEFT)
        
        # Threshold indicator
        self.threshold_label = tk.Label(level_frame, text="Threshold: 300", 
                                       font=('Segoe UI', 9),
                                       fg='#FF9800',  # Orange like voice translator
                                       bg=self.colors['bg_secondary'])
        self.threshold_label.pack(side=tk.RIGHT)
        
        # Canvas for visualization (same as voice translator)
        self.audio_canvas = tk.Canvas(self.audio_viz_frame, 
                                     height=60, 
                                     bg='#1e1e1e',  # Same as voice translator
                                     highlightthickness=0)
        self.audio_canvas.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Bind canvas resize
        self.audio_canvas.bind('<Configure>', self.on_canvas_resize)
        
        # Initialize canvas dimensions
        self.canvas_width = 400
        self.canvas_height = 60
        
        # Modern bottom buttons
        bottom_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        bottom_frame.pack(pady=(0, 5))
        
        # Modern settings button
        settings_btn = tk.Button(bottom_frame, text="⚙️ Settings", 
                                bg=self.colors['bg_tertiary'], 
                                fg=self.colors['text_primary'],
                                activebackground=self.colors['accent'],
                                activeforeground='white',
                                font=('Segoe UI', 9),
                                relief='flat',
                                bd=0,
                                padx=15,
                                pady=6,
                                cursor='hand2',
                                command=self.open_settings)
        settings_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        # Modern shortcuts button
        shortcuts_btn = tk.Button(bottom_frame, text="⌨️ Shortcuts", 
                                 bg=self.colors['bg_tertiary'], 
                                 fg=self.colors['text_primary'],
                                 activebackground=self.colors['accent'],
                                 activeforeground='white',
                                 font=('Segoe UI', 9),
                                 relief='flat',
                                 bd=0,
                                 padx=15,
                                 pady=6,
                                 cursor='hand2',
                                 command=self.show_shortcuts)
        shortcuts_btn.pack(side=tk.LEFT)
        
        # Developer credit link positioned in absolute bottom right corner
        developer_link = tk.Label(main_frame, 
                                 text="Developed by Bibek", 
                                 font=('Segoe UI', 8),
                                 fg=self.colors['text_secondary'], 
                                 bg=self.colors['bg_primary'],
                                 cursor='hand2')
        developer_link.place(relx=1.0, rely=1.0, anchor='se', x=-10, y=-5)
        
        # Add click handler to open website
        def open_developer_website(event):
            import webbrowser
            webbrowser.open("https://www.bibekchandsah.com.np/")
        
        developer_link.bind('<Button-1>', open_developer_website)
        
        # Add hover effects for the developer link
        def on_dev_link_enter(event):
            developer_link.config(fg=self.colors['accent'], 
                                 font=('Segoe UI', 8, 'underline'))
        
        def on_dev_link_leave(event):
            developer_link.config(fg=self.colors['text_secondary'], 
                                 font=('Segoe UI', 8))
        
        developer_link.bind('<Enter>', on_dev_link_enter)
        developer_link.bind('<Leave>', on_dev_link_leave)
        
    def setup_modern_style(self):
        """Setup modern styling for ttk widgets"""
        style = ttk.Style()
        
        # Configure modern button style
        style.theme_use('clam')
        
        style.configure('Modern.TButton',
                       background=self.colors['accent'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 9))
        
        style.map('Modern.TButton',
                 background=[('active', self.colors['accent_hover']),
                           ('pressed', self.colors['accent'])])
    
    def setup_model_selector_style(self):
        """Setup styling for the model selector combobox"""
        style = ttk.Style()
        
        # Configure modern combobox style
        style.configure('Modern.TCombobox',
                       fieldbackground=self.colors['bg_tertiary'],
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       focuscolor='none',
                       arrowcolor=self.colors['text_secondary'],
                       font=('Segoe UI', 10))
        
        style.map('Modern.TCombobox',
                 fieldbackground=[('readonly', self.colors['bg_tertiary']),
                                ('focus', self.colors['bg_tertiary'])],
                 background=[('readonly', self.colors['bg_tertiary'])],
                 foreground=[('readonly', self.colors['text_primary'])])
        
        # Configure modern frame style
        style.configure('Modern.TFrame',
                       background=self.colors['bg_secondary'],
                       borderwidth=0)
        
        # Configure modern label style
        style.configure('Modern.TLabel',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 9))
        
    def setup_stealth(self):
        """Setup stealth mode functionality"""
        self.stealth_window = StealthWindow(self.root)
        
    def setup_hotkeys(self):
        """Setup global hotkeys"""
        from pynput import keyboard
        
        def on_hide_hotkey():
            self.toggle_visibility()
            
        def on_capture_hotkey():
            self.capture_screen_now()
            
        def on_live_screen_hotkey():
            self.toggle_live_screen()
            
        def on_ocr_screen_hotkey():
            self.ocr_screen_now()
            
        # Register hotkeys
        self.hotkey_listener = keyboard.GlobalHotKeys({
            '<ctrl>+<shift>+h': on_hide_hotkey,
            '<ctrl>+<shift>+c': on_capture_hotkey,
            '<ctrl>+<shift>+l': on_live_screen_hotkey,
            '<ctrl>+<shift>+o': on_ocr_screen_hotkey
        })
        self.hotkey_listener.start()
        
    def start_background_threads(self):
        """Start background scanning threads"""
        # Always start answer processing thread
        answer_thread = threading.Thread(target=self.process_answers, daemon=True)
        answer_thread.start()
        
        # Initialize button states based on config
        if self.config.get('audio_enabled', True):
            self.start_audio_scanning()
        else:
            self.audio_btn.config(text="Enable Audio")
            self.audio_status_label.config(text="Audio: Off", foreground='red')
            
        # Initialize live screen based on config (default off for safety)
        if self.config.get('live_screen_enabled', False):
            self.start_live_screen()
        else:
            self.live_screen_btn.config(text="🔴 Live Screen")
            self.live_screen_status_label.config(text="Live: Off", foreground='red')
        
        # Initialize model statuses
        self.on_image_model_change()
        self.on_response_model_change()
        

    def audio_scan_loop(self):
        """Lightweight speech processing loop - only processes queued speech"""
        self.logger.info("Speech processing loop started")
        
        while self.running and self.audio_running:
            try:
                # Get speech from queue (non-blocking)
                audio_data = self.audio_capture.get_speech_from_queue()
                if audio_data:
                    # Process speech in this thread (not audio capture thread)
                    question = self.audio_capture.process_speech_audio(audio_data)
                    if question and self.is_likely_question(question):
                        self.question_queue.put(('Audio', question))
                        self.logger.info(f"Audio Question detected: {question[:50]}...")
                    
            except Exception as e:
                self.logger.error(f"Speech processing error: {e}")
                
            # Sleep longer since we're just checking a queue
            time.sleep(0.2)
            
    def is_likely_question(self, text):
        """Simple heuristic to determine if text is likely a question"""
        question_indicators = ['?', 'what', 'how', 'why', 'when', 'where', 'which', 'who']
        text_lower = text.lower()
        
        # Check for question mark or question words
        return ('?' in text or 
                any(indicator in text_lower for indicator in question_indicators) and
                len(text.split()) > 3)  # Minimum word count
                
    def process_answers(self):
        """Process questions and get answers from LLM"""
        while self.running:
            try:
                if not self.question_queue.empty():
                    item = self.question_queue.get()
                    
                    # Handle different types of queue items
                    if len(item) == 2:
                        source, question = item
                        # Update status
                        self.root.after(0, lambda: self.update_status("Processing question..."))
                        
                        # Get answer from selected response model
                        response_mode = self.config.get('response_mode', 'short')
                        selected_model = self.selected_response_model.get()
                        model_key = self.response_models.get(selected_model)
                        
                        if model_key and model_key.startswith('openai') and self.llm_client.client:
                            answer = self.llm_client.get_answer(question, response_mode)
                        elif model_key and model_key.startswith('gemini') and self.gemini_client.api_key:
                            answer = self.gemini_client.get_text_answer(question, response_mode)
                        else:
                            # Fallback logic
                            if self.llm_client.client:
                                answer = self.llm_client.get_answer(question, response_mode)
                            elif self.gemini_client.api_key:
                                answer = self.gemini_client.get_text_answer(question, response_mode)
                            else:
                                answer = self.perplexity_client.get_text_answer(question, response_mode)
                        
                        # Display answer
                        self.root.after(0, lambda: self.display_answer(source, question, answer))
                        self.root.after(0, lambda: self.update_status("Ready"))
                    
                    elif len(item) == 3:
                        # Handle image-based processing (source, type, data)
                        source, item_type, data = item
                        if item_type == 'image':
                            self.root.after(0, lambda: self.update_status("Processing image..."))
                            
                            response_mode = self.config.get('response_mode', 'short')
                            # Try Gemini first for image analysis, fallback to OpenAI
                            if self.gemini_client.api_key:
                                answer = self.gemini_client.analyze_image(data, response_mode)
                            else:
                                answer = self.llm_client.analyze_image(data, response_mode)
                            
                            self.root.after(0, lambda: self.display_answer(source, "Image Analysis", answer))
                            self.root.after(0, lambda: self.update_status("Ready"))
                    
            except Exception as e:
                self.logger.error(f"Answer processing error: {e}")
                self.root.after(0, lambda: self.update_status("Error processing question"))
                
            time.sleep(0.1)
            
    def submit_manual_question(self):
        """Submit manually entered question"""
        question = self.manual_input.get("1.0", tk.END).strip()
        if question:
            self.question_queue.put(('Manual', question))
            self.manual_input.delete("1.0", tk.END)
            
    def _add_to_answer_display(self, text):
        """Helper method to safely add text to read-only answer display"""
        self.answer_display.config(state='normal')
        self.answer_display.insert(tk.END, text)
        self.answer_display.see(tk.END)
        self.answer_display.config(state='disabled')
    
    def display_answer(self, source, question, answer):
        """Display answer in the GUI"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Store the last response for copying
        self.last_ai_response = answer
        
        # Use helper method to add text safely
        formatted_text = f"\n[{timestamp}] {source} Question:\n{question}\n\nAnswer:\n{answer}\n{'-' * 50}\n"
        self._add_to_answer_display(formatted_text)
        
    def update_status(self, status):
        """Update status label with modern styling"""
        if "error" in status.lower() or "failed" in status.lower():
            color = self.colors['error']
            icon = "❌"
        elif "complete" in status.lower() or "success" in status.lower():
            color = self.colors['success']
            icon = "✅"
        elif "processing" in status.lower() or "analyzing" in status.lower():
            color = self.colors['warning']
            icon = "⚡"
        else:
            color = self.colors['success']
            icon = "●"
        
        self.status_label.config(text=f"{icon} {status}", fg=color)
        
    def toggle_visibility(self):
        """Toggle window visibility"""
        if self.root.winfo_viewable():
            self.root.withdraw()
            self.toggle_btn.config(text="Show")
        else:
            self.root.deiconify()
            self.toggle_btn.config(text="Hide")
            
    def toggle_response_mode(self):
        """Toggle between short and detailed response modes"""
        current_mode = self.config.get('response_mode', 'short')
        new_mode = 'detailed' if current_mode == 'short' else 'short'
        self.config['response_mode'] = new_mode
        self.save_config()
        
        mode_text = "Detailed" if new_mode == 'detailed' else "Short"
        self.mode_btn.config(text=f"Mode: {mode_text}")
        

            
    def toggle_audio_scanning(self):
        """Toggle Audio scanning on/off"""
        if self.audio_running:
            self.stop_audio_scanning()
        else:
            self.start_audio_scanning()
            
    def start_audio_scanning(self):
        """Start Audio scanning with proper thread separation"""
        if not self.audio_running:
            self.audio_running = True
            
            # Start dedicated audio capture thread
            self.audio_capture.start_audio_monitoring()
            
            # Start speech processing thread (lightweight)
            self.audio_thread = threading.Thread(target=self.audio_scan_loop, daemon=True)
            self.audio_thread.start()
            
            # Show visualization and start GUI updates
            self.start_audio_visualization()
            
            self.audio_btn.config(text="Disable Audio")
            self.audio_status_label.config(text="Audio: On", foreground='green')
            self.config['audio_enabled'] = True
            self.save_config()
            self.update_status("Audio scanning started")
            self.logger.info("Audio scanning started")
            
    def stop_audio_scanning(self):
        """Stop Audio scanning"""
        if self.audio_running:
            self.audio_running = False
            
            # Stop audio capture thread first
            self.audio_capture.stop_audio_monitoring()
            
            # Hide visualization
            self.stop_audio_visualization()
            
            self.audio_btn.config(text="Enable Audio")
            self.audio_status_label.config(text="Audio: Off", foreground='red')
            self.config['audio_enabled'] = False
            self.save_config()
            self.update_status("Audio scanning stopped")
            self.logger.info("Audio scanning stopped")
            
    def toggle_live_screen(self):
        """Toggle Live Screen scanning on/off"""
        if self.live_screen_running:
            self.stop_live_screen()
        else:
            self.start_live_screen()
            
    def start_live_screen(self):
        """Start Live Screen scanning"""
        # Check if selected model has API key configured
        selected_model = self.selected_image_model.get()
        model_key = self.image_models.get(selected_model)
        
        if model_key.startswith('openai') and not self.config.get('openai_api_key'):
            messagebox.showwarning("API Error", "OpenAI API key is not configured.\nPlease set your API key in settings.")
            return
        elif model_key.startswith('gemini') and not self.config.get('gemini_api_key'):
            messagebox.showwarning("API Error", "Gemini API key is not configured.\nPlease set your API key in settings.")
            return
            
        if not self.live_screen_running:
            self.live_screen_running = True
            self.live_screen_thread = threading.Thread(target=self.live_screen_loop, daemon=True)
            self.live_screen_thread.start()
            self.live_screen_btn.config(text="⏹️ Stop Live")
            self.live_screen_status_label.config(text="Live: On", foreground='green')
            self.config['live_screen_enabled'] = True
            self.save_config()
            self.update_status("Live screen scanning started")
            self.logger.info("Live screen scanning started")
            
    def stop_live_screen(self):
        """Stop Live Screen scanning"""
        if self.live_screen_running:
            self.live_screen_running = False
            self.live_screen_btn.config(text="🔴 Live Screen")
            self.live_screen_status_label.config(text="Live: Off", foreground='red')
            self.config['live_screen_enabled'] = False
            self.save_config()
            self.update_status("Live screen scanning stopped")
            self.logger.info("Live screen scanning stopped")
            
    def live_screen_loop(self):
        """Continuously capture and analyze screen using selected model"""
        while self.running and self.live_screen_running:
            try:
                # Get selected model info
                selected_model = self.selected_image_model.get()
                model_key = self.image_models.get(selected_model)
                
                # Capture screenshot excluding our window
                base64_image = self.screenshot_capture.capture_and_encode(
                    exclude_window_title=self.root.title(),
                    resize=True,
                    format='JPEG' if model_key.startswith('openai') else 'PNG'
                )
                
                if base64_image:
                    self.logger.info(f"Live screen captured successfully for {selected_model}")
                    
                    # Get response mode
                    response_mode = self.config.get('response_mode', 'short')
                    
                    # Send to appropriate API based on selected model
                    if model_key.startswith('openai'):
                        answer = self._analyze_with_openai(base64_image, model_key, response_mode)
                    elif model_key.startswith('gemini'):
                        answer = self._analyze_with_gemini(base64_image, response_mode)
                    else:
                        answer = "Unsupported model selected."
                    
                    # Only display if there's meaningful content (not just "I can see..." responses)
                    if self.is_meaningful_response(answer):
                        # Display the result
                        self.root.after(0, lambda: self.display_answer("Live Screen", f"{selected_model} Analysis", answer))
                    
                else:
                    self.logger.error("Failed to capture live screen")
                    
            except Exception as e:
                self.logger.error(f"Live screen capture error: {e}")
                
            # Wait before next capture (configurable interval)
            time.sleep(self.config.get('live_screen_interval', 5))
            
    def is_meaningful_response(self, response):
        """Check if the response contains meaningful content worth displaying"""
        if not response or len(response.strip()) < 20:
            return False
            
        # Skip generic responses that don't contain questions or useful information
        generic_phrases = [
            "i can see",
            "this appears to be",
            "the image shows",
            "i don't see any questions",
            "no questions visible",
            "no text visible",
            "unable to identify",
            "cannot see any"
        ]
        
        response_lower = response.lower()
        
        # If it's mostly generic phrases, skip it
        if any(phrase in response_lower for phrase in generic_phrases) and len(response) < 100:
            return False
            
        # Look for question indicators or mathematical content
        question_indicators = ['?', 'what', 'how', 'why', 'when', 'where', 'which', 'who', 'calculate', 'solve', 'find', '=', '+', '-', '*', '/', 'answer']
        
        return any(indicator in response_lower for indicator in question_indicators)
            

            
    def ocr_screen_now(self):
        """Capture screen and extract text content using Gemini OCR"""
        if not self.gemini_client.api_key:
            messagebox.showwarning("API Error", "Gemini API key is not configured.\nPlease set your API key in settings.")
            return
            
        self.update_status("Capturing screen for OCR...")
        self.ocr_screen_btn.config(text="📝 Processing...", state='disabled')
        
        # Run OCR capture in a separate thread to avoid blocking UI
        ocr_thread = threading.Thread(target=self._perform_ocr_capture, daemon=True)
        ocr_thread.start()
        
    def _perform_ocr_capture(self):
        """Perform the actual screenshot capture and Gemini OCR processing"""
        try:
            # Capture screenshot excluding our window
            self.root.after(0, lambda: self.update_status("Taking screenshot for OCR..."))
            
            base64_image = self.screenshot_capture.capture_and_encode(
                exclude_window_title=self.root.title(),
                resize=True,
                format='PNG'
            )
            
            if base64_image:
                self.root.after(0, lambda: self.update_status("Screenshot captured - extracting text with Gemini OCR..."))
                self.logger.info("Screenshot captured for OCR successfully")
                
                # Get response mode
                response_mode = self.config.get('response_mode', 'short')
                
                # Extract text content using Gemini OCR
                extracted_text = self.gemini_client.extract_text_content(base64_image, response_mode)
                
                # Display the result
                self.root.after(0, lambda: self.display_answer("OCR Screen", "Text Extraction", extracted_text))
                self.root.after(0, lambda: self.update_status("OCR extraction complete"))
                
            else:
                self.root.after(0, lambda: self.update_status("Failed to capture screenshot for OCR"))
                self.logger.error("Failed to capture or encode screenshot for OCR")
                
        except Exception as e:
            self.logger.error(f"OCR capture error: {e}")
            self.root.after(0, lambda: self.update_status("OCR capture failed"))
            
        finally:
            # Re-enable the button
            self.root.after(0, lambda: self.ocr_screen_btn.config(text="📝 OCR Screen", state='normal'))
            
    def toggle_always_on_top(self):
        """Toggle always on top setting"""
        always_on_top = self.always_on_top_var.get()
        self.root.attributes('-topmost', always_on_top)
        self.config['always_on_top'] = always_on_top
        self.save_config()
        
        status_text = "enabled" if always_on_top else "disabled"
        self.update_status(f"Always on top {status_text}")
        self.logger.info(f"Always on top {status_text}")
    
    def on_image_model_change(self, event=None):
        """Handle image model selection change"""
        selected_model = self.selected_image_model.get()
        model_key = self.image_models.get(selected_model)
        
        # Update model status based on API key availability
        if model_key.startswith('openai'):
            if self.config.get('openai_api_key'):
                self.image_model_status_label.config(text="✅ Ready", fg=self.colors['success'])
            else:
                self.image_model_status_label.config(text="❌ No API Key", fg=self.colors['error'])
        elif model_key.startswith('gemini'):
            if self.config.get('gemini_api_key'):
                self.image_model_status_label.config(text="✅ Ready", fg=self.colors['success'])
            else:
                self.image_model_status_label.config(text="❌ No API Key", fg=self.colors['error'])
        
        # Save selected model to config
        self.config['selected_image_model'] = selected_model
        self.save_config()
        
        self.logger.info(f"Image model changed to: {selected_model}")
    
    def on_response_model_change(self, event=None):
        """Handle AI response model selection change"""
        selected_model = self.selected_response_model.get()
        model_key = self.response_models.get(selected_model)
        
        # Update model status based on API key availability
        if model_key.startswith('openai'):
            if self.config.get('openai_api_key'):
                self.response_model_status_label.config(text="✅ Ready", fg=self.colors['success'])
            else:
                self.response_model_status_label.config(text="❌ No API Key", fg=self.colors['error'])
            
            # Extract actual model name for OpenAI
            actual_model = model_key.replace('openai_', '')
            self.config['openai_model'] = actual_model
            
        elif model_key.startswith('gemini'):
            if self.config.get('gemini_api_key'):
                self.response_model_status_label.config(text="✅ Ready", fg=self.colors['success'])
            else:
                self.response_model_status_label.config(text="❌ No API Key", fg=self.colors['error'])
            
            # For Gemini models, we might need to update gemini client model
            # This would require updating the gemini_module to support model selection
            
        # Save config
        self.save_config()
        
        # Update the model label in the header
        if hasattr(self, 'model_label'):
            if model_key.startswith('openai'):
                actual_model = model_key.replace('openai_', '')
                self.model_label.config(text=f"🤖 {actual_model}")
            elif model_key.startswith('gemini'):
                self.model_label.config(text=f"🤖 {selected_model}")
        
        self.logger.info(f"Response model changed to: {selected_model}")
    
    def start_audio_visualization(self):
        """Start the audio visualization display"""
        self.audio_viz_frame.pack(fill=tk.X, pady=(0, 15), before=self.answer_display.master)
        # Start GUI-based visualization updates (no separate thread)
        self.update_audio_visualization()
        
    def stop_audio_visualization(self):
        """Stop and hide the audio visualization"""
        self.audio_viz_frame.pack_forget()
        
    def on_canvas_resize(self, event):
        """Handle canvas resize"""
        self.canvas_width = event.width
        self.canvas_height = event.height
        
    def update_audio_visualization(self):
        """Update the audio level visualization - same as voice translator"""
        try:
            # Clear canvas
            self.audio_canvas.delete("all")
            
            if not self.audio_running:
                return
            
            # Get current RMS and history from audio capture
            current_rms = self.audio_capture.get_current_rms()
            max_rms_seen = self.audio_capture.get_max_rms_seen()
            threshold = self.audio_capture.get_threshold_level()
            
            # Update level label
            self.audio_level_label.config(text=f"Level: {int(current_rms)}")
            
            # Draw background grid
            self.draw_background_grid()
            
            # Draw threshold line
            self.draw_threshold_line(threshold, max_rms_seen)
            
            # Draw current level bar
            self.draw_current_level(current_rms, max_rms_seen, threshold)
            
            # Draw RMS history waveform
            self.draw_rms_history(max_rms_seen)
            
        except Exception as e:
            pass  # Ignore visualization errors
        
        # Schedule next update (GUI thread only)
        if self.audio_running:
            self.root.after(100, self.update_audio_visualization)  # Update 10 times per second (less CPU intensive)
    
    def draw_background_grid(self):
        """Draw background grid for the visualizer - same as voice translator"""
        # Horizontal lines
        for i in range(0, self.canvas_height, 20):
            self.audio_canvas.create_line(0, i, self.canvas_width, i, 
                                       fill='#333333', width=1)
        
        # Vertical lines
        for i in range(0, self.canvas_width, 50):
            self.audio_canvas.create_line(i, 0, i, self.canvas_height, 
                                       fill='#333333', width=1)
    
    def draw_threshold_line(self, threshold, max_rms_seen):
        """Draw the silence threshold line - same as voice translator"""
        if max_rms_seen > 0:
            threshold_y = self.canvas_height - (threshold / max_rms_seen) * self.canvas_height
            threshold_y = max(0, min(self.canvas_height, threshold_y))
            
            # Draw threshold line
            self.audio_canvas.create_line(0, threshold_y, self.canvas_width, threshold_y, 
                                       fill='#FF9800', width=2, dash=(5, 5))
            
            # Add threshold label
            self.audio_canvas.create_text(self.canvas_width - 5, threshold_y - 10, 
                                       text="Threshold", fill='#FF9800', 
                                       font=('Arial', 8), anchor='ne')
    
    def draw_current_level(self, current_rms, max_rms_seen, threshold):
        """Draw current audio level bar - same as voice translator"""
        if max_rms_seen > 0 and current_rms > 0:
            # Calculate bar height
            bar_height = (current_rms / max_rms_seen) * self.canvas_height
            bar_height = max(0, min(self.canvas_height, bar_height))
            
            # Determine color based on level
            if current_rms > threshold:
                color = '#4CAF50'  # Green for speech
            else:
                color = '#2196F3'  # Blue for background noise
            
            # Draw level bar on the right side
            bar_width = 30
            x1 = self.canvas_width - bar_width - 5
            x2 = self.canvas_width - 5
            y1 = self.canvas_height - bar_height
            y2 = self.canvas_height
            
            self.audio_canvas.create_rectangle(x1, y1, x2, y2, 
                                           fill=color, outline=color)
            
            # Add level text
            if bar_height > 15:
                self.audio_canvas.create_text((x1 + x2) / 2, y1 + 10, 
                                           text=f"{int(current_rms)}", 
                                           fill='white', font=('Arial', 8))
                                           
        # Update level label color based on threshold
        if current_rms > threshold:
            self.audio_level_label.config(fg='#4CAF50')  # Green when above threshold
        elif current_rms > threshold * 0.5:
            self.audio_level_label.config(fg='#FF9800')  # Orange when moderate
        else:
            self.audio_level_label.config(fg=self.colors['text_secondary'])  # Gray when low
    
    def draw_rms_history(self, max_rms_seen):
        """Draw RMS history as a waveform - same as voice translator"""
        rms_history = self.audio_capture.get_rms_history()
        
        if len(rms_history) < 2 or max_rms_seen <= 0:
            return
        
        # Calculate points for the waveform
        points = []
        
        # Available width for waveform (excluding level bar area)
        waveform_width = self.canvas_width - 40
        
        for i, rms in enumerate(rms_history):
            x = (i / len(rms_history)) * waveform_width
            y = self.canvas_height - (rms / max_rms_seen) * self.canvas_height
            y = max(0, min(self.canvas_height, y))
            points.extend([x, y])
        
        # Draw waveform line
        if len(points) >= 4:
            self.audio_canvas.create_line(points, fill='#00BCD4', width=2, smooth=True)
            
        # Fill area under the curve
        if len(points) >= 4:
            # Add bottom points to create a filled polygon
            fill_points = points.copy()
            fill_points.extend([waveform_width, self.canvas_height, 0, self.canvas_height])
            self.audio_canvas.create_polygon(fill_points, fill='#00BCD4', 
                                         outline='', stipple='gray25')
    

    
    def capture_screen_with_selected_model(self):
        """Capture screen and analyze with the selected image model"""
        selected_model = self.selected_image_model.get()
        model_key = self.image_models.get(selected_model)
        
        # Check if API key is available for selected model
        if model_key.startswith('openai') and not self.config.get('openai_api_key'):
            messagebox.showwarning("API Error", "OpenAI API key is not configured.\nPlease set your API key in settings.")
            return
        elif model_key.startswith('gemini') and not self.config.get('gemini_api_key'):
            messagebox.showwarning("API Error", "Gemini API key is not configured.\nPlease set your API key in settings.")
            return
            
        self.update_status(f"Capturing screen with {selected_model}...")
        self.capture_btn.config(text="📸 Processing...", state='disabled')
        
        # Run capture in a separate thread to avoid blocking UI
        capture_thread = threading.Thread(target=self._perform_model_screen_capture, args=(model_key,), daemon=True)
        capture_thread.start()
    
    def _perform_model_screen_capture(self, model_key):
        """Perform the actual screenshot capture and analysis with selected model"""
        try:
            # Capture screenshot excluding our window
            self.root.after(0, lambda: self.update_status("Taking screenshot..."))
            
            base64_image = self.screenshot_capture.capture_and_encode(
                exclude_window_title=self.root.title(),
                resize=True,
                format='JPEG' if model_key.startswith('openai') else 'PNG'
            )
            
            if base64_image:
                selected_model_name = self.selected_image_model.get()
                self.root.after(0, lambda: self.update_status(f"Screenshot captured - analyzing with {selected_model_name}..."))
                self.logger.info(f"Screenshot captured successfully for {selected_model_name}")
                
                # Get response mode
                response_mode = self.config.get('response_mode', 'short')
                
                # Send to appropriate API based on model
                if model_key.startswith('openai'):
                    answer = self._analyze_with_openai(base64_image, model_key, response_mode)
                elif model_key.startswith('gemini'):
                    answer = self._analyze_with_gemini(base64_image, response_mode)
                else:
                    answer = "Unsupported model selected."
                
                # Display the result
                self.root.after(0, lambda: self.display_answer("Screen Analysis", selected_model_name, answer))
                self.root.after(0, lambda: self.update_status(f"{selected_model_name} analysis complete"))
                
            else:
                self.root.after(0, lambda: self.update_status("Failed to capture screenshot"))
                self.logger.error("Failed to capture or encode screenshot")
                
        except Exception as e:
            self.logger.error(f"Model screen capture error: {e}")
            self.root.after(0, lambda: self.update_status("Screen capture failed"))
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to analyze screen: {str(e)}"))
            
        finally:
            # Re-enable the button
            self.root.after(0, lambda: self.capture_btn.config(text="📸 Capture Screen", state='normal'))
    
    def _analyze_with_openai(self, base64_image, model_key, response_mode):
        """Analyze image with OpenAI Vision API"""
        try:
            import requests
            
            # Map model keys to actual OpenAI model names
            openai_models = {
                'openai_gpt4o': 'gpt-4o',
                'openai_gpt4o_mini': 'gpt-4o-mini',
                'openai_gpt4_turbo': 'gpt-4-turbo'
            }
            
            model_name = openai_models.get(model_key, 'gpt-4o')
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.get('openai_api_key')}"
            }
            
            # Use custom prompt only if checkbox is enabled, otherwise use hardcoded prompt
            if self.config.get('use_custom_prompt', False):
                prompt = self.config.get('custom_image_prompt', "What's in this image? Please analyze and describe what you see.")
            else:
                # Use hardcoded prompt from prompt.txt
                try:
                    with open('prompt.txt', 'r', encoding='utf-8') as f:
                        prompt = f.read().strip()
                except FileNotFoundError:
                    prompt = "What's in this image? Please analyze and describe what you see."
            
            if response_mode == 'detailed' and not self.config.get('use_custom_prompt', False):
                prompt += """
**Role:**
You are an **exam-solving and coding assistant**. Your job is to analyze images and provide the most accurate, concise answers for exam-style and coding questions. You specialize in:

* Arithmetic Aptitude
* Data Interpretation
* Verbal Ability
* Logical Reasoning
* Verbal Reasoning
* Nonverbal Reasoning
* Programming questions (code writing only)

**Task Instructions:**

1. **Multiple Choice Questions (MCQs):**

   * Solve the question logically using reasoning, calculations, or analysis.
   * Choose the **best correct option** from the given choices.
   * If no option matches your solution, reply with: **“No matched answer found.”**
   * Do **not** explain—only provide the direct answer.

2. **Programming Questions:**

   * Provide only the code solution.
   * Place it exactly where the question specifies: **“write your code here.”**

3. **Answer Formatting:**

   * Always prefix each response with the **question number**.
   * Examples:

     * `Q1: B 3/4`
     * `Q2: print("Hello World")`

4. **Non-Exam Images:**

   * If the image does not contain exam-related or coding questions, briefly describe what you see in the image.

5. **General Rules:**

   * Be accurate, concise, and logical.
   * Do not provide explanations unless the image is unrelated to exams or programming.
   * For multiple questions in one image, answer sequentially: Q1, Q2, Q3…

                """
           
            
            payload = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 10000 if response_mode == 'detailed' else 1000
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                error_msg = f"OpenAI API error: {response.status_code}"
                try:
                    error_detail = response.json().get('error', {}).get('message', 'Unknown error')
                    error_msg += f" - {error_detail}"
                except:
                    pass
                return f"Error: {error_msg}"
                
        except Exception as e:
            return f"OpenAI analysis error: {str(e)}"
    
    def _analyze_with_gemini(self, base64_image, response_mode):
        """Analyze image with Gemini Vision API"""
        try:
            # Use custom prompt only if checkbox is enabled
            custom_prompt = None
            if self.config.get('use_custom_prompt', False):
                custom_prompt = self.config.get('custom_image_prompt')
            return self.gemini_client.analyze_image(base64_image, response_mode, custom_prompt)
        except Exception as e:
            return f"Gemini analysis error: {str(e)}"
        
    def get_scanning_status(self):
        """Get current scanning status"""
        return {
            'ocr_running': self.ocr_running,
            'audio_running': self.audio_running,
            'ocr_available': self.ocr_capture.tesseract_available,
            'threads_active': {
                'ocr': self.ocr_thread.is_alive() if self.ocr_thread else False,
                'audio': self.audio_thread.is_alive() if self.audio_thread else False
            }
        }
        
    def open_settings(self):
        """Open settings window"""
        settings_window = SettingsWindow(self.root, self.config, self.save_config)
        
    def show_shortcuts(self):
        """Show keyboard shortcuts window"""
        shortcuts_window = ShortcutsWindow(self.root)
        
    def run(self):
        """Start the application"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()
            
    def on_closing(self):
        """Clean up when closing the application"""
        self.running = False
        if hasattr(self, 'hotkey_listener'):
            self.hotkey_listener.stop()
        self.root.quit()
        self.root.destroy()
    
    def clear_ai_responses(self):
        """Clear all AI responses from the display area with confirmation"""
        try:
            # Check if there's content to clear
            current_content = self.answer_display.get('1.0', tk.END).strip()
            if not current_content:
                self.update_status("No responses to clear")
                return
            
            # Ask for confirmation
            from tkinter import messagebox
            result = messagebox.askyesno(
                "Clear AI Responses", 
                "Are you sure you want to clear all AI responses?\n\nThis action cannot be undone.",
                icon='warning'
            )
            
            if result:
                # Temporarily enable the widget to clear content
                self.answer_display.config(state='normal')
                self.answer_display.delete('1.0', tk.END)
                # Disable it again to maintain read-only state
                self.answer_display.config(state='disabled')
                
                # Clear the stored last response as well
                self.last_ai_response = ""
                
                self.update_status("AI responses cleared")
                self.logger.info("AI responses area cleared by user")
            else:
                self.update_status("Clear cancelled")
                
        except Exception as e:
            self.logger.error(f"Error clearing AI responses: {e}")
            self.update_status("Error clearing responses")
    
    def copy_last_response(self):
        """Copy the last AI response to clipboard"""
        try:
            if not hasattr(self, 'last_ai_response') or not self.last_ai_response.strip():
                self.update_status("No response to copy")
                return
            
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(self.last_ai_response)
            self.root.update()  # Ensure clipboard is updated
            
            # Show success message with response preview
            preview = self.last_ai_response[:50] + "..." if len(self.last_ai_response) > 50 else self.last_ai_response
            self.update_status(f"Copied: {preview}")
            self.logger.info(f"Last AI response copied to clipboard (length: {len(self.last_ai_response)} chars)")
            
        except Exception as e:
            self.logger.error(f"Error copying response: {e}")
            self.update_status("Error copying response")


class SettingsWindow:
    def __init__(self, parent, config, save_callback):
        self.config = config
        self.save_callback = save_callback
        
        self.window = tk.Toplevel(parent)
        self.window.title("Settings")
        
        # Set window icon
        try:
            if os.path.exists("icon.png"):
                icon_image = tk.PhotoImage(file="icon.png")
                self.window.iconphoto(True, icon_image)
            elif os.path.exists("icon.ico"):
                self.window.iconbitmap("icon.ico")
        except:
            pass  # Icon loading failed, continue without icon
        
        # Center the window
        self.center_window(680, 690)
        
        self.window.transient(parent)
        self.window.grab_set()
        
        self.setup_settings_gui()
    
    def center_window(self, width, height):
        """Center the settings window on the screen"""
        # Get screen dimensions
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # Calculate position coordinates
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # Set window geometry
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
    def setup_settings_gui(self):
        """Setup settings GUI"""
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # OpenAI API Key
        ttk.Label(main_frame, text="OpenAI API Key (for text):").pack(anchor=tk.W)
        self.api_key_var = tk.StringVar(value=self.config.get('openai_api_key', ''))
        api_key_entry = ttk.Entry(main_frame, textvariable=self.api_key_var, show='*', width=50)
        api_key_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Auto-scan hint
        if not self.config.get('working_models'):
            hint_label = ttk.Label(main_frame, text="💡 Tip: After entering your API key, click 'Scan Models' to find available models", 
                                 font=('Segoe UI', 8), foreground='gray')
            hint_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Gemini API Key
        ttk.Label(main_frame, text="Gemini API Key (for vision):").pack(anchor=tk.W)
        self.gemini_key_var = tk.StringVar(value=self.config.get('gemini_api_key', ''))
        gemini_key_entry = ttk.Entry(main_frame, textvariable=self.gemini_key_var, show='*', width=50)
        gemini_key_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Perplexity API Key (optional fallback)
        ttk.Label(main_frame, text="Perplexity API Key (optional fallback):").pack(anchor=tk.W)
        self.perplexity_key_var = tk.StringVar(value=self.config.get('perplexity_api_key', ''))
        perplexity_key_entry = ttk.Entry(main_frame, textvariable=self.perplexity_key_var, show='*', width=50)
        perplexity_key_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Model Selection Section
        model_frame = ttk.Frame(main_frame)
        model_frame.pack(fill=tk.X, pady=(0, 10))
        
        # OpenAI Model Selection
        ttk.Label(model_frame, text="OpenAI Model:").pack(anchor=tk.W)
        
        openai_model_frame = ttk.Frame(model_frame)
        openai_model_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Model dropdown
        self.model_var = tk.StringVar(value=self.config.get('openai_model', 'gpt-3.5-turbo'))
        
        # Get available models from config or use default list
        working_models = self.config.get('working_models', [])
        if not working_models:
            working_models = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo', 'gpt-4o', 'gpt-4o-mini']
        
        self.model_combo = ttk.Combobox(openai_model_frame, textvariable=self.model_var, 
                                       values=working_models, state='readonly', width=25)
        self.model_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Scan OpenAI models button
        self.scan_btn = ttk.Button(openai_model_frame, text="🔍 Scan OpenAI Models", 
                                  command=self.scan_working_models)
        self.scan_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # OpenAI Model status label
        self.model_status_label = ttk.Label(openai_model_frame, text="", foreground='green')
        self.model_status_label.pack(side=tk.LEFT)
        
        # Gemini Model Selection
        ttk.Label(model_frame, text="Gemini Models:").pack(anchor=tk.W, pady=(10, 0))
        
        gemini_model_frame = ttk.Frame(model_frame)
        gemini_model_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Gemini model dropdown
        self.gemini_model_var = tk.StringVar(value=self.config.get('gemini_model', 'gemini-1.5-flash'))
        
        # Available Gemini models
        gemini_models = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro', 'gemini-pro-vision']
        
        self.gemini_model_combo = ttk.Combobox(gemini_model_frame, textvariable=self.gemini_model_var, 
                                              values=gemini_models, state='readonly', width=25)
        self.gemini_model_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Scan Gemini models button
        self.scan_gemini_btn = ttk.Button(gemini_model_frame, text="🔍 Scan Gemini Models", 
                                         command=self.scan_gemini_models)
        self.scan_gemini_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Gemini Model status label
        self.gemini_model_status_label = ttk.Label(gemini_model_frame, text="", foreground='green')
        self.gemini_model_status_label.pack(side=tk.LEFT)
        
        # Scan interval
        ttk.Label(main_frame, text="Scan Interval (seconds):").pack(anchor=tk.W)
        self.scan_interval_var = tk.StringVar(value=str(self.config.get('scan_interval', 3)))
        scan_interval_entry = ttk.Entry(main_frame, textvariable=self.scan_interval_var)
        scan_interval_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Live screen interval
        ttk.Label(main_frame, text="Live Screen Interval (seconds):").pack(anchor=tk.W)
        self.live_screen_interval_var = tk.StringVar(value=str(self.config.get('live_screen_interval', 5)))
        live_screen_interval_entry = ttk.Entry(main_frame, textvariable=self.live_screen_interval_var)
        live_screen_interval_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Enable/disable features
        self.ocr_enabled_var = tk.BooleanVar(value=self.config.get('ocr_enabled', True))
        ttk.Checkbutton(main_frame, text="Enable OCR Scanning", variable=self.ocr_enabled_var).pack(anchor=tk.W, pady=5)
        
        self.audio_enabled_var = tk.BooleanVar(value=self.config.get('audio_enabled', True))
        ttk.Checkbutton(main_frame, text="Enable Audio Scanning", variable=self.audio_enabled_var).pack(anchor=tk.W, pady=5)
        
        self.live_screen_enabled_var = tk.BooleanVar(value=self.config.get('live_screen_enabled', False))
        ttk.Checkbutton(main_frame, text="Enable Live Screen on Startup", variable=self.live_screen_enabled_var).pack(anchor=tk.W, pady=5)
        
        # Custom Image Prompt Section
        ttk.Label(main_frame, text="Custom Image Analysis Prompt:").pack(anchor=tk.W, pady=(15, 0))
        
        # Checkbox to enable/disable custom prompt
        self.use_custom_prompt_var = tk.BooleanVar(value=self.config.get('use_custom_prompt', False))
        custom_prompt_cb = ttk.Checkbutton(main_frame, text="Use Custom Prompt (when unchecked, uses hardcoded prompt)", 
                                          variable=self.use_custom_prompt_var,
                                          command=self.toggle_custom_prompt_state)
        custom_prompt_cb.pack(anchor=tk.W, pady=(5, 5))
        
        prompt_hint = ttk.Label(main_frame, text="💡 This prompt will be used for image analysis when checkbox is enabled.", 
                               font=('Segoe UI', 8), foreground='gray')
        prompt_hint.pack(anchor=tk.W, pady=(0, 5))
        
        # Create a frame for the text widget with scrollbar
        prompt_frame = ttk.Frame(main_frame)
        prompt_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Text widget for multi-line prompt
        self.custom_prompt_text = tk.Text(prompt_frame, height=4, wrap=tk.WORD, 
                                         font=('Segoe UI', 9))
        prompt_scrollbar = ttk.Scrollbar(prompt_frame, orient=tk.VERTICAL, command=self.custom_prompt_text.yview)
        self.custom_prompt_text.config(yscrollcommand=prompt_scrollbar.set)
        
        # Insert current prompt
        current_prompt = self.config.get('custom_image_prompt', "What's in this image? Please analyze and describe what you see.")
        self.custom_prompt_text.insert('1.0', current_prompt)
        
        # Pack text widget and scrollbar
        self.custom_prompt_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        prompt_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Set initial state based on checkbox
        self.toggle_custom_prompt_state()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(button_frame, text="Save", command=self.save_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side=tk.RIGHT)
        
    def scan_working_models(self):
        """Scan for working OpenAI models"""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showwarning("Warning", "Please enter your OpenAI API key first.")
            return
            
        # Start scanning in a separate thread to avoid blocking the UI
        import threading
        scan_thread = threading.Thread(target=self._perform_model_scan, args=(api_key,))
        scan_thread.daemon = True
        scan_thread.start()
    
    def _perform_model_scan(self, api_key):
        """Perform the actual model scanning in a separate thread"""
        try:
            # Update UI on main thread
            self.window.after(0, lambda: self.scan_btn.config(text="🔍 Scanning...", state='disabled'))
            self.window.after(0, lambda: self.model_status_label.config(text="Fetching available models...", foreground='orange'))
            
            # Import here to avoid circular imports
            from llm_module import LLMClient
            
            # Create temporary client to test models
            temp_client = LLMClient(api_key)
            
            # First get all available models
            self.window.after(0, lambda: self.model_status_label.config(text="Getting model list from OpenAI...", foreground='orange'))
            all_models = temp_client.get_all_available_models()
            
            if not all_models:
                self.window.after(0, lambda: self._scan_complete([], "No models found from API"))
                return
            
            # Update status with model count
            self.window.after(0, lambda: self.model_status_label.config(
                text=f"Testing {len(all_models)} models... (this may take a moment)", foreground='orange'))
            
            # Test models with progress updates
            working_models = []
            for i, model in enumerate(all_models):
                try:
                    # Update progress
                    progress_text = f"Testing {i+1}/{len(all_models)}: {model[:20]}..."
                    self.window.after(0, lambda text=progress_text: self.model_status_label.config(text=text, foreground='orange'))
                    
                    # Test the model
                    response = temp_client.client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": "Hi"}],
                        max_tokens=5,
                        timeout=15
                    )
                    working_models.append(model)
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    if "authentication" in error_msg or "api key" in error_msg:
                        self.window.after(0, lambda: self._scan_complete([], "API key authentication failed"))
                        return
                    elif "rate limit" in error_msg:
                        # If rate limited, assume the model works
                        working_models.append(model)
                    # Continue with other models for other errors
            
            # Complete the scan
            self.window.after(0, lambda: self._scan_complete(working_models, None))
            
        except Exception as e:
            error_msg = f"Failed to scan models: {str(e)}"
            self.window.after(0, lambda: self._scan_complete([], error_msg))
    
    def _scan_complete(self, working_models, error_msg):
        """Handle scan completion on the main thread"""
        try:
            if error_msg:
                self.model_status_label.config(text="✗ Scan failed", foreground='red')
                messagebox.showerror("Error", error_msg)
            elif working_models:
                # Update dropdown with working models
                self.model_combo['values'] = working_models
                
                # Set current model if it's in the working list, otherwise set first working model
                current_model = self.model_var.get()
                if current_model not in working_models:
                    self.model_var.set(working_models[0])
                
                # Update config with working models
                self.config['working_models'] = working_models
                
                # Refresh main UI response model dropdown if it exists
                if hasattr(self, 'save_callback'):
                    self.save_callback()  # This will trigger a refresh in the main UI
                
                self.model_status_label.config(text=f"✓ Found {len(working_models)} models", foreground='green')
                
                # Show results in a scrollable dialog for many models
                if len(working_models) > 10:
                    self._show_models_dialog(working_models)
                else:
                    messagebox.showinfo("Success", f"Found {len(working_models)} working models:\n\n" + 
                                      "\n".join(working_models))
            else:
                self.model_status_label.config(text="✗ No models found", foreground='red')
                messagebox.showerror("Error", "No working models found. Please check your API key.")
                
        except Exception as e:
            self.model_status_label.config(text="✗ Error", foreground='red')
            messagebox.showerror("Error", f"Error completing scan: {str(e)}")
        
        finally:
            self.scan_btn.config(text="🔍 Scan Models", state='normal')
    
    def _show_models_dialog(self, models):
        """Show a dialog with all found models in a scrollable list"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Available Models")
        dialog.geometry("400x500")
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Center the dialog on screen
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Header
        header_label = tk.Label(dialog, text=f"Found {len(models)} Working Models", 
                               font=('Arial', 12, 'bold'))
        header_label.pack(pady=10)
        
        # Scrollable list
        frame = tk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=('Courier', 10))
        for model in models:
            listbox.insert(tk.END, model)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Close button
        close_btn = tk.Button(dialog, text="Close", command=dialog.destroy)
        close_btn.pack(pady=10)
    
    def scan_gemini_models(self):
        """Scan for working Gemini models"""
        api_key = self.gemini_key_var.get().strip()
        if not api_key:
            messagebox.showwarning("Warning", "Please enter your Gemini API key first.")
            return
            
        # Start scanning in a separate thread to avoid blocking the UI
        import threading
        scan_thread = threading.Thread(target=self._perform_gemini_scan, args=(api_key,))
        scan_thread.daemon = True
        scan_thread.start()
    
    def _perform_gemini_scan(self, api_key):
        """Perform the actual Gemini model scanning in a separate thread"""
        try:
            # Update UI on main thread
            self.window.after(0, lambda: self.scan_gemini_btn.config(text="🔍 Scanning...", state='disabled'))
            self.window.after(0, lambda: self.gemini_model_status_label.config(text="Testing Gemini models...", foreground='orange'))
            
            # Import here to avoid circular imports
            from gemini_module import GeminiClient
            
            # Create temporary client to test models
            temp_client = GeminiClient(api_key)
            
            # Test available Gemini models
            test_models = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro', 'gemini-pro-vision']
            working_models = []
            
            for i, model in enumerate(test_models):
                try:
                    # Update progress
                    progress_text = f"Testing {i+1}/{len(test_models)}: {model}..."
                    self.window.after(0, lambda text=progress_text: self.gemini_model_status_label.config(text=text, foreground='orange'))
                    
                    # Test the model by making a simple request
                    import google.generativeai as genai
                    genai.configure(api_key=api_key)
                    test_model = genai.GenerativeModel(model)
                    response = test_model.generate_content("Hello")
                    
                    if response.text:
                        working_models.append(model)
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    if "authentication" in error_msg or "api key" in error_msg:
                        self.window.after(0, lambda: self._gemini_scan_complete([], "Gemini API key authentication failed"))
                        return
                    # Continue with other models for other errors
            
            # Complete the scan
            self.window.after(0, lambda: self._gemini_scan_complete(working_models, None))
            
        except Exception as e:
            error_msg = f"Failed to scan Gemini models: {str(e)}"
            self.window.after(0, lambda: self._gemini_scan_complete([], error_msg))
    
    def _gemini_scan_complete(self, working_models, error_msg):
        """Handle Gemini scan completion on the main thread"""
        try:
            if error_msg:
                self.gemini_model_status_label.config(text="✗ Scan failed", foreground='red')
                messagebox.showerror("Error", error_msg)
            elif working_models:
                # Update dropdown with working models
                self.gemini_model_combo['values'] = working_models
                
                # Set current model if it's in the working list, otherwise set first working model
                current_model = self.gemini_model_var.get()
                if current_model not in working_models:
                    self.gemini_model_var.set(working_models[0])
                
                # Update config with working Gemini models
                self.config['working_gemini_models'] = working_models
                self.config['gemini_model'] = self.gemini_model_var.get()
                
                self.gemini_model_status_label.config(text=f"✓ Found {len(working_models)} models", foreground='green')
                
                messagebox.showinfo("Success", f"Found {len(working_models)} working Gemini models:\n\n" + 
                                  "\n".join(working_models))
            else:
                self.gemini_model_status_label.config(text="✗ No models found", foreground='red')
                messagebox.showerror("Error", "No working Gemini models found. Please check your API key.")
                
        except Exception as e:
            self.gemini_model_status_label.config(text="✗ Error", foreground='red')
            messagebox.showerror("Error", f"Error completing Gemini scan: {str(e)}")
        
        finally:
            self.scan_gemini_btn.config(text="🔍 Scan Gemini Models", state='normal')
    
    def toggle_custom_prompt_state(self):
        """Toggle the state of custom prompt text widget based on checkbox"""
        if self.use_custom_prompt_var.get():
            # Enable custom prompt
            self.custom_prompt_text.config(state='normal', bg='white', fg='black')
        else:
            # Disable custom prompt (use hardcoded)
            self.custom_prompt_text.config(state='disabled', bg='#f0f0f0', fg='gray')
    
    def save_settings(self):
        """Save settings and close window"""
        try:
            self.config['openai_api_key'] = self.api_key_var.get()
            self.config['gemini_api_key'] = self.gemini_key_var.get()
            self.config['perplexity_api_key'] = self.perplexity_key_var.get()
            self.config['scan_interval'] = int(self.scan_interval_var.get())
            self.config['live_screen_interval'] = int(self.live_screen_interval_var.get())
            self.config['ocr_enabled'] = self.ocr_enabled_var.get()
            self.config['audio_enabled'] = self.audio_enabled_var.get()
            self.config['live_screen_enabled'] = self.live_screen_enabled_var.get()
            self.config['openai_model'] = self.model_var.get()
            self.config['gemini_model'] = self.gemini_model_var.get()
            self.config['use_custom_prompt'] = self.use_custom_prompt_var.get()
            self.config['custom_image_prompt'] = self.custom_prompt_text.get('1.0', tk.END).strip()
            
            self.save_callback()
            messagebox.showinfo("Settings", "Settings saved successfully!")
            self.window.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid values for all fields.")


class ShortcutsWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Keyboard Shortcuts")
        
        # Set window icon
        try:
            if os.path.exists("icon.png"):
                icon_image = tk.PhotoImage(file="icon.png")
                self.window.iconphoto(True, icon_image)
            elif os.path.exists("icon.ico"):
                self.window.iconbitmap("icon.ico")
        except:
            pass  # Icon loading failed, continue without icon
        
        # Center the window
        self.center_window(530, 550)
        
        self.window.transient(parent)
        self.window.grab_set()
        
        # Make window non-resizable for better layout
        self.window.resizable(True, True)
        
        self.setup_shortcuts_gui()
    
    def center_window(self, width, height):
        """Center the shortcuts window on the screen"""
        # Get screen dimensions
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # Calculate position coordinates
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # Set window geometry
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
    def setup_shortcuts_gui(self):
        """Setup shortcuts display GUI"""
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_frame, text="Keyboard Shortcuts", font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 15))
        
        # Create scrollable frame for shortcuts
        canvas = tk.Canvas(main_frame, height=280)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Shortcuts data
        shortcuts = [
            ("Window Controls", [
                ("Ctrl+Shift+H", "Hide/Show Window", "Toggle window visibility instantly"),
            ]),
            ("Screen Capture", [
                ("Ctrl+Shift+C", "📸 Capture Screen", "Take screenshot and analyze with AI"),
                ("Ctrl+Shift+O", "📝 OCR Screen", "Extract and format text from screen"),
                ("Ctrl+Shift+L", "🔴 Live Screen", "Toggle continuous screen monitoring"),
            ]),
            ("Button Functions", [
                ("Hide", "Toggle Visibility", "Hide/show the application window"),
                ("Mode: Short", "Response Mode", "Switch between short and detailed AI responses"),
                ("Start OCR", "OCR Scanning", "Toggle continuous text scanning from screen"),
                ("Enable Audio", "Audio Input", "Toggle microphone listening for questions"),
                ("📸 Capture", "Single Analysis", "Analyze current screen content once"),
                ("📝 OCR", "Text Extraction", "Extract formatted text from screen"),
                ("🔴 Live", "Live Monitoring", "Continuous screen analysis every 5 seconds"),
                ("Always on Top", "Window Position", "Keep window above all other applications"),
            ]),
            ("Tips & Usage", [
                ("Manual Input", "Type Questions", "Use the text box to ask questions directly"),
                ("Settings", "Configuration", "Configure API keys and scanning intervals"),
                ("Response Modes", "Short vs Detailed", "Short: Quick answers, Detailed: Full explanations"),
            ])
        ]
        
        # Display shortcuts by category
        for category, shortcut_list in shortcuts:
            # Category header
            category_frame = ttk.LabelFrame(scrollable_frame, text=category, padding=10)
            category_frame.pack(fill=tk.X, pady=(0, 10), padx=5)
            
            for shortcut_data in shortcut_list:
                if len(shortcut_data) == 3:
                    key, action, description = shortcut_data
                    
                    # Shortcut row
                    row_frame = ttk.Frame(category_frame)
                    row_frame.pack(fill=tk.X, pady=2)
                    
                    # Key combination (left side)
                    key_label = ttk.Label(row_frame, text=key, font=('Courier', 9, 'bold'), 
                                        foreground='blue', width=15)
                    key_label.pack(side=tk.LEFT)
                    
                    # Action name (middle)
                    action_label = ttk.Label(row_frame, text=action, font=('Arial', 9, 'bold'), 
                                           width=15)
                    action_label.pack(side=tk.LEFT, padx=(10, 10))
                    
                    # Description (right side)
                    desc_label = ttk.Label(row_frame, text=description, font=('Arial', 9), 
                                         wraplength=200)
                    desc_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Close button
        # close_btn = ttk.Button(main_frame, text="Close", command=self.window.destroy)
        # close_btn.pack(pady=(15, 0))
        
        # Bind mouse wheel to canvas with proper error handling
        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                # Canvas no longer exists, ignore the event
                pass
        
        # Bind to the canvas and scrollable frame instead of globally
        canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
        
        # Store the event handler for cleanup
        self._mousewheel_handler = _on_mousewheel
        
        # Bind window destruction to cleanup
        self.window.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
    def _on_window_close(self):
        """Clean up event handlers when window is closed"""
        try:
            # Unbind mouse wheel events to prevent errors
            if hasattr(self, '_mousewheel_handler'):
                self.window.unbind_all("<MouseWheel>")
        except:
            pass
        finally:
            self.window.destroy()
    

    def copy_last_response(self):
        """Copy the last AI response to clipboard"""
        try:
            if not self.last_ai_response.strip():
                self.update_status("No response to copy")
                return
            
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(self.last_ai_response)
            self.root.update()  # Ensure clipboard is updated
            
            # Show success message with response preview
            preview = self.last_ai_response[:50] + "..." if len(self.last_ai_response) > 50 else self.last_ai_response
            self.update_status(f"Copied: {preview}")
            self.logger.info(f"Last AI response copied to clipboard (length: {len(self.last_ai_response)} chars)")
            
        except Exception as e:
            self.logger.error(f"Error copying response: {e}")
            self.update_status("Error copying response")


if __name__ == "__main__":
    app = ExamHelper()
    app.run()