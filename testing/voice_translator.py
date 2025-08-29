import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import speech_recognition as sr
from googletrans import Translator, LANGUAGES
import threading
import time
import pyaudio
import numpy as np
from datetime import datetime
import queue
import sys
import collections
import audioop

class RealTimeVoiceTranslator:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        
        # Audio and translation components
        self.recognizer = sr.Recognizer()
        self.translator = Translator()
        self.microphone = None
        self.audio_queue = queue.Queue()
        self.translation_queue = queue.Queue()
        
        # State variables
        self.is_listening = False
        self.target_language = 'en'
        self.volume_gain = 1.5
        self.sensitivity_threshold = 0.01
        self.current_preset = "Quiet Room"
        
        # Audio settings
        self.chunk_size = 1024
        self.sample_rate = 16000
        self.audio_format = pyaudio.paInt16
        
        # Continuous listening settings
        self.audio_buffer = collections.deque(maxlen=int(self.sample_rate * 30))  # 30 second buffer
        self.speech_buffer = []
        self.silence_threshold = 500  # Silence detection threshold
        self.min_speech_length = 1.0  # Minimum speech length in seconds (increased for longer questions)
        self.silence_duration = 2.0  # Silence duration to trigger processing (increased to allow longer pauses)
        self.last_speech_time = 0
        self.pyaudio_instance = None
        self.audio_stream = None
        
        # Audio visualization
        self.current_rms = 0
        self.rms_history = collections.deque(maxlen=100)  # Keep last 100 RMS values
        self.max_rms_seen = 1000  # Dynamic scaling for visualization
        
        # Setup GUI components
        self.setup_gui()
        self.setup_audio()
        
        # Processing threads
        self.audio_thread = None
        self.translation_thread = None
        self.gui_update_thread = None
        
    def setup_window(self):
        self.root.title("Real-Time Voice Translator for Calls")
        self.root.geometry("800x700")
        self.root.configure(bg='#2b2b2b')
        
        # Make window stay on top option
        self.root.attributes('-topmost', False)
        
    def setup_gui(self):
        # Main frame
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="Real-Time Voice Translator", 
                              font=('Arial', 16, 'bold'), fg='white', bg='#2b2b2b')
        title_label.pack(pady=(0, 10))
        
        # Control panel
        self.setup_control_panel(main_frame)
        
        # Status panel
        self.setup_status_panel(main_frame)
        
        # Audio visualizer
        self.setup_audio_visualizer(main_frame)
        
        # Translation display
        self.setup_translation_display(main_frame)
        
        # Bottom controls
        self.setup_bottom_controls(main_frame)
        
    def setup_control_panel(self, parent):
        control_frame = tk.Frame(parent, bg='#3b3b3b', relief=tk.RAISED, bd=1)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Language selection
        lang_frame = tk.Frame(control_frame, bg='#3b3b3b')
        lang_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(lang_frame, text="Translate to:", font=('Arial', 10), 
                fg='white', bg='#3b3b3b').pack(side=tk.LEFT)
        
        self.language_var = tk.StringVar(value="English")
        language_combo = ttk.Combobox(lang_frame, textvariable=self.language_var, 
                                     values=list(self.get_common_languages().keys()),
                                     state="readonly", width=15)
        language_combo.pack(side=tk.LEFT, padx=(10, 0))
        language_combo.bind('<<ComboboxSelected>>', self.on_language_change)
        
        # Audio presets
        preset_frame = tk.Frame(control_frame, bg='#3b3b3b')
        preset_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(preset_frame, text="Audio Preset:", font=('Arial', 10), 
                fg='white', bg='#3b3b3b').pack(side=tk.LEFT)
        
        self.preset_var = tk.StringVar(value=self.current_preset)
        preset_combo = ttk.Combobox(preset_frame, textvariable=self.preset_var,
                                   values=["Quiet Room", "Noisy Place", "Low Volume", "Custom"],
                                   state="readonly", width=15)
        preset_combo.pack(side=tk.LEFT, padx=(10, 0))
        preset_combo.bind('<<ComboboxSelected>>', self.on_preset_change)
        
        # Volume gain slider
        gain_frame = tk.Frame(control_frame, bg='#3b3b3b')
        gain_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(gain_frame, text="Volume Gain:", font=('Arial', 10), 
                fg='white', bg='#3b3b3b').pack(side=tk.LEFT)
        
        self.gain_var = tk.DoubleVar(value=self.volume_gain)
        gain_scale = tk.Scale(gain_frame, from_=0.1, to=5.0, resolution=0.1,
                             orient=tk.HORIZONTAL, variable=self.gain_var,
                             bg='#3b3b3b', fg='white', highlightbackground='#3b3b3b',
                             command=self.on_gain_change)
        gain_scale.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
    def setup_status_panel(self, parent):
        status_frame = tk.Frame(parent, bg='#3b3b3b', relief=tk.RAISED, bd=1)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_label = tk.Label(status_frame, text="Ready - Click Start to begin listening", 
                                    font=('Arial', 12, 'bold'), fg='#4CAF50', bg='#3b3b3b')
        self.status_label.pack(pady=10)
    
    def setup_audio_visualizer(self, parent):
        """Setup audio level visualizer"""
        viz_frame = tk.Frame(parent, bg='#3b3b3b', relief=tk.RAISED, bd=1)
        viz_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title
        tk.Label(viz_frame, text="Audio Level Monitor", font=('Arial', 10, 'bold'), 
                fg='white', bg='#3b3b3b').pack(pady=(10, 5))
        
        # Audio level display frame
        level_frame = tk.Frame(viz_frame, bg='#3b3b3b')
        level_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        # Current level label
        self.level_label = tk.Label(level_frame, text="Level: 0", font=('Arial', 9), 
                                   fg='white', bg='#3b3b3b')
        self.level_label.pack(side=tk.LEFT)
        
        # Threshold indicator
        self.threshold_label = tk.Label(level_frame, text=f"Threshold: {self.silence_threshold}", 
                                       font=('Arial', 9), fg='#FF9800', bg='#3b3b3b')
        self.threshold_label.pack(side=tk.RIGHT)
        
        # Canvas for visualization
        self.viz_canvas = tk.Canvas(viz_frame, height=60, bg='#1e1e1e', highlightthickness=0)
        self.viz_canvas.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Bind canvas resize
        self.viz_canvas.bind('<Configure>', self.on_canvas_resize)
        
        # Initialize visualization
        self.canvas_width = 400
        self.canvas_height = 60
        
    def setup_translation_display(self, parent):
        display_frame = tk.Frame(parent, bg='#3b3b3b', relief=tk.RAISED, bd=1)
        display_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        tk.Label(display_frame, text="Translations", font=('Arial', 12, 'bold'), 
                fg='white', bg='#3b3b3b').pack(pady=(10, 5))
        
        self.translation_text = scrolledtext.ScrolledText(
            display_frame, 
            wrap=tk.WORD, 
            font=('Arial', 11),
            bg='#1e1e1e', 
            fg='white',
            insertbackground='white',
            selectbackground='#4CAF50',
            height=20
        )
        self.translation_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
    def setup_bottom_controls(self, parent):
        button_frame = tk.Frame(parent, bg='#2b2b2b')
        button_frame.pack(fill=tk.X)
        
        # Start/Stop button
        self.start_button = tk.Button(button_frame, text="Start Listening", 
                                     command=self.toggle_listening,
                                     font=('Arial', 12, 'bold'),
                                     bg='#4CAF50', fg='white', 
                                     activebackground='#45a049',
                                     width=15, height=2)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Test audio button
        test_button = tk.Button(button_frame, text="Test Audio", 
                               command=self.test_audio,
                               font=('Arial', 10),
                               bg='#2196F3', fg='white',
                               activebackground='#1976D2',
                               width=12)
        test_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear button
        clear_button = tk.Button(button_frame, text="Clear", 
                                command=self.clear_translations,
                                font=('Arial', 10),
                                bg='#FF9800', fg='white',
                                activebackground='#F57C00',
                                width=10)
        clear_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Audio devices button
        devices_button = tk.Button(button_frame, text="Audio Devices", 
                                  command=self.show_audio_devices,
                                  font=('Arial', 10),
                                  bg='#9C27B0', fg='white',
                                  activebackground='#7B1FA2',
                                  width=12)
        devices_button.pack(side=tk.LEFT)
        
        # Stay on top checkbox
        self.topmost_var = tk.BooleanVar()
        topmost_check = tk.Checkbutton(button_frame, text="Stay on Top",
                                      variable=self.topmost_var,
                                      command=self.toggle_topmost,
                                      font=('Arial', 9),
                                      fg='white', bg='#2b2b2b',
                                      selectcolor='#3b3b3b')
        topmost_check.pack(side=tk.RIGHT)
        
    def setup_audio(self):
        """Initialize audio components"""
        try:
            # Initialize PyAudio
            self.pyaudio_instance = pyaudio.PyAudio()
            
            # Initialize microphone for speech recognition
            self.microphone = sr.Microphone()
            
            # Adjust for ambient noise
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
        except Exception as e:
            self.update_status(f"Audio setup error: {str(e)}", "error")
            
    def get_common_languages(self):
        """Return common languages for translation"""
        common_langs = {
            'English': 'en',
            'Thai': 'th', 
            'Indonesian': 'id',
            'Spanish': 'es',
            'French': 'fr',
            'German': 'de',
            'Chinese': 'zh',
            'Japanese': 'ja',
            'Korean': 'ko',
            'Vietnamese': 'vi',
            'Hindi': 'hi',
            'Arabic': 'ar'
        }
        return common_langs
        
    def on_language_change(self, event=None):
        """Handle language selection change"""
        lang_name = self.language_var.get()
        lang_codes = self.get_common_languages()
        self.target_language = lang_codes.get(lang_name, 'en')
        
    def on_preset_change(self, event=None):
        """Handle preset change"""
        preset = self.preset_var.get()
        self.current_preset = preset
        
        presets = {
            "Quiet Room": {"gain": 2.0, "threshold": 200},
            "Noisy Place": {"gain": 2.5, "threshold": 600},
            "Low Volume": {"gain": 3.5, "threshold": 150},
            "Custom": {"gain": self.volume_gain, "threshold": self.silence_threshold}
        }
        
        if preset in presets:
            settings = presets[preset]
            self.volume_gain = settings["gain"]
            self.silence_threshold = settings["threshold"]
            self.gain_var.set(self.volume_gain)
            
            # Update threshold display
            if hasattr(self, 'threshold_label'):
                self.threshold_label.config(text=f"Threshold: {self.silence_threshold}")
    
    def on_gain_change(self, value):
        """Handle volume gain slider change"""
        self.volume_gain = float(value)
            
    def toggle_topmost(self):
        """Toggle window always on top"""
        self.root.attributes('-topmost', self.topmost_var.get())
        
    def toggle_listening(self):
        """Start or stop listening"""
        if not self.is_listening:
            self.start_listening()
        else:
            self.stop_listening()
            
    def start_listening(self):
        """Start the continuous listening process"""
        if not self.microphone or not self.pyaudio_instance:
            self.setup_audio()
            
        if not self.microphone or not self.pyaudio_instance:
            messagebox.showerror("Error", "No microphone available. Please check your audio devices.")
            return
            
        try:
            # Setup audio stream for continuous capture
            self.audio_stream = self.pyaudio_instance.open(
                format=self.audio_format,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            self.is_listening = True
            self.start_button.config(text="Stop Listening", bg='#f44336', activebackground='#d32f2f')
            self.update_status("Starting continuous audio capture...", "info")
            
            # Clear buffers
            self.audio_buffer.clear()
            self.speech_buffer.clear()
            
            # Start threads
            self.audio_thread = threading.Thread(target=self.continuous_audio_capture, daemon=True)
            self.translation_thread = threading.Thread(target=self.translation_processor, daemon=True)
            self.gui_update_thread = threading.Thread(target=self.gui_updater, daemon=True)
            self.viz_update_thread = threading.Thread(target=self.visualization_updater, daemon=True)
            
            self.audio_thread.start()
            self.translation_thread.start()
            self.gui_update_thread.start()
            self.viz_update_thread.start()
            
        except Exception as e:
            self.update_status(f"Failed to start audio stream: {str(e)}", "error")
            messagebox.showerror("Error", f"Could not start audio capture: {str(e)}")
        
    def stop_listening(self):
        """Stop the listening process"""
        self.is_listening = False
        
        # Close audio stream
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
            except:
                pass
                
        self.start_button.config(text="Start Listening", bg='#4CAF50', activebackground='#45a049')
        self.update_status("Stopped listening", "info")
        
    def continuous_audio_capture(self):
        """Continuously capture audio and detect speech segments"""
        while self.is_listening and self.audio_stream:
            try:
                # Read audio chunk
                data = self.audio_stream.read(self.chunk_size, exception_on_overflow=False)
                
                # Validate audio data
                if not data or len(data) == 0:
                    continue
                
                # Convert to numpy array for processing
                audio_data = np.frombuffer(data, dtype=np.int16)
                
                # Validate audio array
                if len(audio_data) == 0:
                    continue
                
                # Apply volume gain with clipping to prevent overflow
                audio_data = np.clip(audio_data * self.volume_gain, -32768, 32767).astype(np.int16)
                
                # Add to buffer
                self.audio_buffer.extend(audio_data)
                
                # Calculate RMS for voice activity detection with error handling
                try:
                    # Use float64 for calculation to prevent overflow
                    audio_float = audio_data.astype(np.float64)
                    mean_square = np.mean(audio_float**2)
                    
                    # Handle edge cases
                    if np.isnan(mean_square) or np.isinf(mean_square) or mean_square < 0:
                        rms = 0
                    else:
                        rms = np.sqrt(mean_square)
                        
                    # Ensure RMS is a valid number
                    if np.isnan(rms) or np.isinf(rms):
                        rms = 0
                        
                except (ValueError, RuntimeWarning):
                    rms = 0
                
                # Update visualization data
                self.current_rms = rms
                self.rms_history.append(rms)
                
                # Update max RMS for dynamic scaling
                if rms > self.max_rms_seen:
                    self.max_rms_seen = rms * 1.2  # Add some headroom
                
                current_time = time.time()
                
                # Voice activity detection
                if rms > self.silence_threshold:
                    # Speech detected
                    self.speech_buffer.extend(audio_data)
                    self.last_speech_time = current_time
                    
                elif self.speech_buffer and (current_time - self.last_speech_time) > self.silence_duration:
                    # Silence detected after speech - process the speech segment
                    min_samples = int(self.sample_rate * self.min_speech_length)
                    if len(self.speech_buffer) > min_samples:
                        # Convert speech buffer to audio data for recognition
                        speech_data = np.array(self.speech_buffer, dtype=np.int16)
                        
                        # Add some padding silence at the beginning and end for better recognition
                        padding_samples = int(self.sample_rate * 0.1)  # 0.1 second padding
                        silence_padding = np.zeros(padding_samples, dtype=np.int16)
                        
                        # Combine: silence + speech + silence
                        padded_audio = np.concatenate([silence_padding, speech_data, silence_padding])
                        audio_bytes = padded_audio.tobytes()
                        
                        print(f"Queuing audio segment: {len(self.speech_buffer)} samples + padding, {len(audio_bytes)} bytes total")
                        
                        # Queue for translation
                        self.audio_queue.put(audio_bytes)
                    else:
                        print(f"Speech segment too short: {len(self.speech_buffer)} samples (need {min_samples})")
                    
                    # Clear speech buffer
                    self.speech_buffer.clear()
                    
            except Exception as e:
                if self.is_listening:
                    print(f"Audio capture error: {e}")
                    time.sleep(0.1)
                
    def translation_processor(self):
        """Process audio segments for translation"""
        while self.is_listening:
            try:
                # Get audio data from queue (with timeout to allow checking is_listening)
                try:
                    audio_bytes = self.audio_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                # Create AudioData object for speech recognition
                # For 16-bit audio (paInt16), sample width is 2 bytes
                # Ensure we have enough audio data (at least 0.1 seconds)
                min_bytes = int(self.sample_rate * 0.1 * 2)  # 0.1 seconds * 2 bytes per sample
                if len(audio_bytes) < min_bytes:
                    print(f"Audio segment too short for recognition: {len(audio_bytes)} bytes (need {min_bytes})")
                    continue
                    
                audio_data = sr.AudioData(audio_bytes, self.sample_rate, 2)
                
                # Speech recognition
                try:
                    print(f"Processing audio segment of {len(audio_bytes)} bytes...")
                    
                    # First, let's test if we can recognize anything at all
                    try:
                        text = self.recognizer.recognize_google(audio_data)
                        print(f"Speech recognition successful: '{text}'")
                    except sr.UnknownValueError:
                        print("Google Speech Recognition could not understand audio")
                        continue
                    except sr.RequestError as e:
                        print(f"Could not request results from Google Speech Recognition service; {e}")
                        continue
                    
                    # Check if text is valid
                    if not text or not isinstance(text, str):
                        print(f"Invalid recognition result: {type(text)} - {text}")
                        continue
                    
                    text = text.strip()
                    if text:
                        try:
                            # Detect language and translate
                            detection = self.translator.detect(text)
                            source_lang = detection.lang if hasattr(detection, 'lang') else 'en'
                            
                            # Ensure source_lang is a valid string
                            if not isinstance(source_lang, str) or len(source_lang) < 2:
                                source_lang = 'en'  # Default to English
                                
                            print(f"Detected language: {source_lang}")
                            
                            if source_lang != self.target_language:
                                # Translate with explicit source language
                                translation = self.translator.translate(
                                    text, 
                                    src=source_lang, 
                                    dest=self.target_language
                                )
                                print(f"Translation: '{translation.text}'")
                                # Queue translation result for GUI update
                                self.translation_queue.put({
                                    'original': text,
                                    'translation': translation.text,
                                    'source_lang': source_lang,
                                    'timestamp': datetime.now()
                                })
                            else:
                                print("Same language detected")
                                self.translation_queue.put({
                                    'original': text,
                                    'translation': "Same language detected",
                                    'source_lang': source_lang,
                                    'timestamp': datetime.now()
                                })
                        except Exception as lang_error:
                            print(f"Language detection/translation error: {lang_error}")
                            # Fallback: assume English and translate anyway
                            try:
                                translation = self.translator.translate(text, dest=self.target_language)
                                self.translation_queue.put({
                                    'original': text,
                                    'translation': translation.text,
                                    'source_lang': 'en',
                                    'timestamp': datetime.now()
                                })
                            except Exception as fallback_error:
                                print(f"Fallback translation error: {fallback_error}")
                                # Show original text if translation fails
                                self.translation_queue.put({
                                    'original': text,
                                    'translation': f"Translation failed: {text}",
                                    'source_lang': 'unknown',
                                    'timestamp': datetime.now()
                                })
                            
                except Exception as e:
                    print(f"Unexpected error in translation processor: {e}")
                    import traceback
                    traceback.print_exc()
                    
            except Exception as e:
                if self.is_listening:
                    print(f"Translation processor error: {e}")
                    time.sleep(0.1)
    
    def gui_updater(self):
        """Update GUI with translation results"""
        while self.is_listening:
            try:
                # Get translation result from queue
                try:
                    result = self.translation_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                # Update GUI in main thread
                self.root.after(0, self.display_translation_result, result)
                
            except Exception as e:
                if self.is_listening:
                    print(f"GUI updater error: {e}")
                    time.sleep(0.1)
    
    def display_translation_result(self, result):
        """Display translation result in GUI (called from main thread)"""
        timestamp = result['timestamp'].strftime("%H:%M:%S")
        
        # Get language name
        lang_name = next((name for name, code in self.get_common_languages().items() 
                         if code == result['source_lang']), result['source_lang'].upper())
        
        # Format the output
        output = f"[{timestamp}] {lang_name} → {self.language_var.get()}\n"
        output += f"Original: {result['original']}\n"
        output += f"Translation: {result['translation']}\n"
        output += "-" * 50 + "\n\n"
        
        # Insert into text widget
        self.translation_text.insert(tk.END, output)
        self.translation_text.see(tk.END)
        
        # Update status
        self.update_status("Listening continuously...", "ready")
    
    def visualization_updater(self):
        """Update audio visualization in real-time"""
        while self.is_listening:
            try:
                # Update visualization every 50ms for smooth animation
                self.root.after(0, self.update_audio_visualization)
                time.sleep(0.05)
            except Exception as e:
                if self.is_listening:
                    print(f"Visualization updater error: {e}")
                    time.sleep(0.1)
    
    def on_canvas_resize(self, event):
        """Handle canvas resize"""
        self.canvas_width = event.width
        self.canvas_height = event.height
        
    def update_audio_visualization(self):
        """Update the audio level visualization"""
        try:
            # Clear canvas
            self.viz_canvas.delete("all")
            
            if not self.is_listening:
                return
            
            # Update level label
            self.level_label.config(text=f"Level: {int(self.current_rms)}")
            
            # Draw background grid
            self.draw_background_grid()
            
            # Draw threshold line
            self.draw_threshold_line()
            
            # Draw current level bar
            self.draw_current_level()
            
            # Draw RMS history waveform
            self.draw_rms_history()
            
        except Exception as e:
            pass  # Ignore visualization errors
    
    def draw_background_grid(self):
        """Draw background grid for the visualizer"""
        # Horizontal lines
        for i in range(0, self.canvas_height, 20):
            self.viz_canvas.create_line(0, i, self.canvas_width, i, 
                                       fill='#333333', width=1)
        
        # Vertical lines
        for i in range(0, self.canvas_width, 50):
            self.viz_canvas.create_line(i, 0, i, self.canvas_height, 
                                       fill='#333333', width=1)
    
    def draw_threshold_line(self):
        """Draw the silence threshold line"""
        if self.max_rms_seen > 0:
            threshold_y = self.canvas_height - (self.silence_threshold / self.max_rms_seen) * self.canvas_height
            threshold_y = max(0, min(self.canvas_height, threshold_y))
            
            # Draw threshold line
            self.viz_canvas.create_line(0, threshold_y, self.canvas_width, threshold_y, 
                                       fill='#FF9800', width=2, dash=(5, 5))
            
            # Add threshold label
            self.viz_canvas.create_text(self.canvas_width - 5, threshold_y - 10, 
                                       text="Threshold", fill='#FF9800', 
                                       font=('Arial', 8), anchor='ne')
    
    def draw_current_level(self):
        """Draw current audio level bar"""
        if self.max_rms_seen > 0 and self.current_rms > 0:
            # Calculate bar height
            bar_height = (self.current_rms / self.max_rms_seen) * self.canvas_height
            bar_height = max(0, min(self.canvas_height, bar_height))
            
            # Determine color based on level
            if self.current_rms > self.silence_threshold:
                color = '#4CAF50'  # Green for speech
            else:
                color = '#2196F3'  # Blue for background noise
            
            # Draw level bar on the right side
            bar_width = 30
            x1 = self.canvas_width - bar_width - 5
            x2 = self.canvas_width - 5
            y1 = self.canvas_height - bar_height
            y2 = self.canvas_height
            
            self.viz_canvas.create_rectangle(x1, y1, x2, y2, 
                                           fill=color, outline=color)
            
            # Add level text
            if bar_height > 15:
                self.viz_canvas.create_text((x1 + x2) / 2, y1 + 10, 
                                           text=f"{int(self.current_rms)}", 
                                           fill='white', font=('Arial', 8))
    
    def draw_rms_history(self):
        """Draw RMS history as a waveform"""
        if len(self.rms_history) < 2 or self.max_rms_seen <= 0:
            return
        
        # Calculate points for the waveform
        points = []
        history_list = list(self.rms_history)
        
        # Available width for waveform (excluding level bar area)
        waveform_width = self.canvas_width - 40
        
        for i, rms in enumerate(history_list):
            x = (i / len(history_list)) * waveform_width
            y = self.canvas_height - (rms / self.max_rms_seen) * self.canvas_height
            y = max(0, min(self.canvas_height, y))
            points.extend([x, y])
        
        # Draw waveform line
        if len(points) >= 4:
            self.viz_canvas.create_line(points, fill='#00BCD4', width=2, smooth=True)
            
        # Fill area under the curve
        if len(points) >= 4:
            # Add bottom points to create a filled polygon
            fill_points = points.copy()
            fill_points.extend([waveform_width, self.canvas_height, 0, self.canvas_height])
            self.viz_canvas.create_polygon(fill_points, fill='#00BCD4', 
                                         outline='', stipple='gray25')
            

        
    def update_status(self, message, status_type="info"):
        """Update status label"""
        colors = {
            "ready": "#4CAF50",
            "processing": "#FF9800", 
            "translating": "#2196F3",
            "error": "#f44336",
            "info": "#9E9E9E"
        }
        
        color = colors.get(status_type, "#9E9E9E")
        self.status_label.config(text=message, fg=color)
        
    def test_audio(self):
        """Test audio capture"""
        if not self.microphone:
            self.setup_audio()
            
        if not self.microphone:
            messagebox.showerror("Error", "No microphone available.")
            return
            
        def test_thread():
            try:
                self.update_status("Testing audio - speak now...", "processing")
                
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)
                    
                text = self.recognizer.recognize_google(audio)
                self.update_status(f"Test successful: '{text}'", "ready")
                
            except sr.WaitTimeoutError:
                self.update_status("Test timeout - no speech detected", "error")
            except Exception as e:
                self.update_status(f"Test failed: {str(e)}", "error")
                
        threading.Thread(target=test_thread, daemon=True).start()
        
    def show_audio_devices(self):
        """Show available audio devices"""
        try:
            p = pyaudio.PyAudio()
            devices_info = []
            
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    devices_info.append(f"Device {i}: {info['name']}")
                    
            p.terminate()
            
            if devices_info:
                message = "Available Audio Input Devices:\n\n" + "\n".join(devices_info)
            else:
                message = "No audio input devices found."
                
            messagebox.showinfo("Audio Devices", message)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not list audio devices: {str(e)}")
            
    def clear_translations(self):
        """Clear the translation display"""
        self.translation_text.delete(1.0, tk.END)
        
    def run(self):
        """Start the application"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except KeyboardInterrupt:
            self.stop_listening()
    
    def on_closing(self):
        """Handle application closing"""
        self.stop_listening()
        
        # Clean up PyAudio
        if self.pyaudio_instance:
            try:
                self.pyaudio_instance.terminate()
            except:
                pass
                
        self.root.destroy()
            
if __name__ == "__main__":
    app = RealTimeVoiceTranslator()
    app.run()