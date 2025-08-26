#!/usr/bin/env python3
"""
Test script for OpenAI audio transcription functionality
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import sys
import os

# Add current directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from audio_module import AudioCapture
except ImportError as e:
    print(f"Error importing audio module: {e}")
    print("Make sure all required packages are installed:")
    print("pip install pyaudio numpy speechrecognition openai requests")
    sys.exit(1)

class OpenAIAudioTest:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎙️ OpenAI Audio Transcription Test")
        self.root.geometry("600x400")
        self.root.configure(bg='#1a1a1a')
        
        # Colors
        self.colors = {
            'bg_primary': '#1a1a1a',
            'bg_secondary': '#2d2d2d',
            'text_primary': '#ffffff',
            'text_secondary': '#b0b0b0',
            'success': '#00d4aa',
            'warning': '#ffb347',
            'accent': '#4a9eff',
            'error': '#ff6b6b'
        }
        
        try:
            self.audio_capture = AudioCapture()
            self.api_key = None
            self.setup_gui()
        except Exception as e:
            messagebox.showerror("Audio Error", f"Failed to initialize audio: {e}")
            self.root.destroy()
            return
        
    def setup_gui(self):
        """Setup the test GUI"""
        # Title
        title_frame = tk.Frame(self.root, bg=self.colors['bg_secondary'])
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(title_frame, text="OpenAI Audio Transcription Test", 
                              font=('Segoe UI', 16, 'bold'),
                              fg=self.colors['text_primary'], 
                              bg=self.colors['bg_secondary'])
        title_label.pack(pady=15)
        
        # API Key section
        api_frame = tk.Frame(self.root, bg=self.colors['bg_secondary'])
        api_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        api_label = tk.Label(api_frame, text="OpenAI API Key:", 
                            font=('Segoe UI', 12, 'bold'),
                            fg=self.colors['text_primary'], 
                            bg=self.colors['bg_secondary'])
        api_label.pack(pady=(10, 5))
        
        api_button_frame = tk.Frame(api_frame, bg=self.colors['bg_secondary'])
        api_button_frame.pack(pady=(0, 10))
        
        self.api_key_btn = tk.Button(api_button_frame, text="🔑 Set API Key", 
                                    command=self.set_api_key,
                                    bg=self.colors['accent'], 
                                    fg='white',
                                    font=('Segoe UI', 11, 'bold'),
                                    relief='flat',
                                    padx=20, pady=8,
                                    cursor='hand2')
        self.api_key_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.api_status_label = tk.Label(api_button_frame, text="❌ No API Key", 
                                        font=('Segoe UI', 10),
                                        fg=self.colors['error'], 
                                        bg=self.colors['bg_secondary'])
        self.api_status_label.pack(side=tk.LEFT)
        
        # Instructions
        instructions_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        instructions_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        instructions = tk.Label(instructions_frame, 
                               text="1. Set your OpenAI API key\n2. Click 'Record Audio' and speak for 5 seconds\n3. View the transcription result below",
                               font=('Segoe UI', 11),
                               fg=self.colors['text_secondary'], 
                               bg=self.colors['bg_primary'],
                               justify=tk.LEFT)
        instructions.pack(pady=10)
        
        # Record button
        record_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        record_frame.pack(pady=15)
        
        self.record_btn = tk.Button(record_frame, text="🎙️ Record Audio (5s)", 
                                   command=self.record_audio,
                                   bg=self.colors['success'], 
                                   fg='white',
                                   font=('Segoe UI', 14, 'bold'),
                                   relief='flat',
                                   padx=30, pady=12,
                                   cursor='hand2',
                                   state='disabled')
        self.record_btn.pack()
        
        # Status label
        self.status_label = tk.Label(self.root, text="Ready - Set API key to begin", 
                                    font=('Segoe UI', 12),
                                    fg=self.colors['text_secondary'], 
                                    bg=self.colors['bg_primary'])
        self.status_label.pack(pady=10)
        
        # Result display
        result_frame = tk.Frame(self.root, bg=self.colors['bg_secondary'])
        result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        result_label = tk.Label(result_frame, text="Transcription Result:", 
                               font=('Segoe UI', 12, 'bold'),
                               fg=self.colors['text_primary'], 
                               bg=self.colors['bg_secondary'])
        result_label.pack(pady=(15, 5), anchor='w', padx=15)
        
        # Text widget for result
        from tkinter import scrolledtext
        self.result_text = scrolledtext.ScrolledText(
            result_frame, 
            wrap=tk.WORD, 
            font=('Segoe UI', 11),
            bg='#1e1e1e', 
            fg='white',
            insertbackground='white',
            selectbackground=self.colors['accent'],
            height=8
        )
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
    def set_api_key(self):
        """Set OpenAI API key"""
        api_key = simpledialog.askstring(
            "OpenAI API Key", 
            "Enter your OpenAI API key:",
            show='*'  # Hide the key as it's typed
        )
        
        if api_key and api_key.strip():
            self.api_key = api_key.strip()
            self.api_status_label.config(text="✅ API Key Set", fg=self.colors['success'])
            self.record_btn.config(state='normal')
            self.status_label.config(text="Ready to record audio", fg=self.colors['success'])
        else:
            self.api_status_label.config(text="❌ No API Key", fg=self.colors['error'])
            self.record_btn.config(state='disabled')
            
    def record_audio(self):
        """Record and transcribe audio"""
        if not self.api_key:
            messagebox.showerror("Error", "Please set your OpenAI API key first")
            return
            
        # Update UI
        self.record_btn.config(text="🔴 Recording...", state='disabled')
        self.status_label.config(text="Recording for 5 seconds - speak now!", fg=self.colors['warning'])
        
        # Start recording in a separate thread
        import threading
        recording_thread = threading.Thread(target=self._perform_recording, daemon=True)
        recording_thread.start()
        
    def _perform_recording(self):
        """Perform the actual recording and transcription"""
        try:
            # Record and transcribe
            transcription = self.audio_capture.record_and_transcribe_with_openai(
                duration=5,
                api_key=self.api_key,
                prompt="Please transcribe this audio accurately. Provide only the transcription without any additional commentary."
            )
            
            # Update UI in main thread
            if transcription:
                self.root.after(0, lambda: self._show_result(transcription, True))
            else:
                self.root.after(0, lambda: self._show_result("Failed to transcribe audio", False))
                
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.root.after(0, lambda: self._show_result(error_msg, False))
            
        finally:
            # Re-enable button
            self.root.after(0, lambda: self.record_btn.config(text="🎙️ Record Audio (5s)", state='normal'))
            
    def _show_result(self, result, success):
        """Show the transcription result"""
        # Clear previous result
        self.result_text.delete(1.0, tk.END)
        
        # Add timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Insert result
        if success:
            self.result_text.insert(tk.END, f"[{timestamp}] Transcription:\n{result}\n")
            self.status_label.config(text="Transcription completed successfully!", fg=self.colors['success'])
        else:
            self.result_text.insert(tk.END, f"[{timestamp}] Error:\n{result}\n")
            self.status_label.config(text="Transcription failed", fg=self.colors['error'])
            
    def run(self):
        """Run the test application"""
        try:
            print("Starting OpenAI Audio Test...")
            print("Make sure you have a valid OpenAI API key with access to gpt-4o-audio-preview")
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Clean up resources"""
        try:
            self.audio_capture.cleanup()
            print("Cleanup completed")
        except Exception as e:
            print(f"Cleanup error: {e}")

if __name__ == "__main__":
    print("🎙️ OpenAI Audio Transcription Test")
    print("=" * 40)
    
    try:
        test = OpenAIAudioTest()
        test.run()
    except Exception as e:
        print(f"Test failed to start: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you have a valid OpenAI API key")
        print("2. Check that your microphone is working")
        print("3. Install required packages: pip install openai requests")
        input("Press Enter to exit...")