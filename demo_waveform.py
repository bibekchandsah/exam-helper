#!/usr/bin/env python3
"""
Demo script showing the new waveform audio visualization
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

# Add current directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from audio_module import AudioCapture
except ImportError as e:
    print(f"Error importing audio module: {e}")
    print("Make sure all required packages are installed:")
    print("pip install pyaudio numpy speechrecognition")
    sys.exit(1)

class WaveformDemo:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎤 Audio Waveform Visualization Demo")
        self.root.geometry("500x300")
        self.root.configure(bg='#1a1a1a')
        
        # Colors matching the main app
        self.colors = {
            'bg_primary': '#1a1a1a',
            'bg_secondary': '#2d2d2d',
            'text_primary': '#ffffff',
            'text_secondary': '#b0b0b0',
            'success': '#00d4aa',
            'warning': '#ffb347',
            'accent': '#4a9eff'
        }
        
        try:
            self.audio_capture = AudioCapture()
            self.is_monitoring = False
            self.setup_gui()
        except Exception as e:
            messagebox.showerror("Audio Error", f"Failed to initialize audio: {e}")
            self.root.destroy()
            return
        
    def setup_gui(self):
        """Setup the demo GUI"""
        # Title
        title_frame = tk.Frame(self.root, bg=self.colors['bg_secondary'])
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(title_frame, text="Audio Waveform Visualization Demo", 
                              font=('Segoe UI', 14, 'bold'),
                              fg=self.colors['text_primary'], 
                              bg=self.colors['bg_secondary'])
        title_label.pack(pady=10)
        
        # Instructions
        instructions = tk.Label(self.root, 
                               text="Click 'Start Monitoring' and speak to see the waveform visualization.\nThe orange line shows the recommended speaking threshold.",
                               font=('Segoe UI', 10),
                               fg=self.colors['text_secondary'], 
                               bg=self.colors['bg_primary'],
                               justify=tk.CENTER)
        instructions.pack(pady=(0, 15))
        
        # Waveform canvas
        canvas_frame = tk.Frame(self.root, bg=self.colors['bg_secondary'])
        canvas_frame.pack(pady=10, padx=20, fill=tk.X)
        
        canvas_title = tk.Label(canvas_frame, text="Audio Level Monitor", 
                               font=('Segoe UI', 11, 'bold'),
                               fg=self.colors['text_primary'], 
                               bg=self.colors['bg_secondary'])
        canvas_title.pack(pady=(10, 5))
        
        self.audio_canvas = tk.Canvas(canvas_frame, 
                                     width=450, height=120,
                                     bg='#1a1a1a',
                                     highlightthickness=0)
        self.audio_canvas.pack(pady=(0, 10))
        
        # Level info
        info_frame = tk.Frame(canvas_frame, bg=self.colors['bg_secondary'])
        info_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.level_label = tk.Label(info_frame, text="Level: 0", 
                                   font=('Segoe UI', 10),
                                   fg=self.colors['text_secondary'], 
                                   bg=self.colors['bg_secondary'])
        self.level_label.pack(side=tk.LEFT)
        
        self.threshold_label = tk.Label(info_frame, text="Threshold: 300", 
                                       font=('Segoe UI', 10),
                                       fg=self.colors['warning'], 
                                       bg=self.colors['bg_secondary'])
        self.threshold_label.pack(side=tk.RIGHT)
        
        # Control buttons
        button_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        button_frame.pack(pady=15)
        
        self.start_btn = tk.Button(button_frame, text="🎤 Start Monitoring", 
                                  command=self.start_monitoring,
                                  bg=self.colors['success'], 
                                  fg='white',
                                  font=('Segoe UI', 11, 'bold'),
                                  relief='flat',
                                  padx=20, pady=8,
                                  cursor='hand2')
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = tk.Button(button_frame, text="⏹️ Stop Monitoring", 
                                 command=self.stop_monitoring,
                                 bg='#ff6b6b', 
                                 fg='white',
                                 font=('Segoe UI', 11, 'bold'),
                                 relief='flat',
                                 padx=20, pady=8,
                                 cursor='hand2',
                                 state='disabled')
        self.stop_btn.pack(side=tk.LEFT)
        
    def start_monitoring(self):
        """Start audio monitoring"""
        try:
            if not self.is_monitoring:
                self.is_monitoring = True
                self.audio_capture.start_audio_monitoring()
                self.update_visualization()
                self.start_btn.config(state='disabled')
                self.stop_btn.config(state='normal')
                print("Audio monitoring started")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start monitoring: {e}")
            
    def stop_monitoring(self):
        """Stop audio monitoring"""
        if self.is_monitoring:
            self.is_monitoring = False
            self.audio_capture.stop_audio_monitoring()
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            # Clear the canvas
            self.audio_canvas.delete("all")
            print("Audio monitoring stopped")
            
    def update_visualization(self):
        """Update the waveform visualization"""
        if not self.is_monitoring:
            return
            
        try:
            # Get audio data
            audio_level = self.audio_capture.get_current_audio_level()
            waveform_data = self.audio_capture.get_waveform_data()
            threshold = self.audio_capture.get_threshold_level()
            
            # Clear canvas
            self.audio_canvas.delete("all")
            
            canvas_width = 450
            canvas_height = 120
            center_y = canvas_height // 2
            
            # Draw subtle grid
            grid_color = '#333333'
            for i in range(0, canvas_width, 50):
                self.audio_canvas.create_line(i, 0, i, canvas_height, fill=grid_color, width=1)
            for i in range(0, canvas_height, 24):
                self.audio_canvas.create_line(0, i, canvas_width, i, fill=grid_color, width=1)
            
            # Draw threshold line (dotted orange)
            threshold_y = center_y - (threshold * center_y)
            for x in range(0, canvas_width, 10):
                self.audio_canvas.create_line(x, threshold_y, x+5, threshold_y, fill='#ffb347', width=2)
            
            # Draw waveform
            if len(waveform_data) > 1:
                points_to_show = min(len(waveform_data), canvas_width)
                step = len(waveform_data) / points_to_show if points_to_show > 0 else 1
                
                waveform_points = []
                for i in range(points_to_show):
                    data_index = int(i * step)
                    if data_index < len(waveform_data):
                        amplitude = waveform_data[data_index]
                        x = (i / points_to_show) * canvas_width
                        y = center_y - (amplitude * center_y * 0.9)
                        waveform_points.extend([x, y])
                
                if len(waveform_points) >= 4:
                    # Draw waveform with glow effect
                    self.audio_canvas.create_line(waveform_points, fill='#00d4aa', width=3, smooth=True)
                    self.audio_canvas.create_line(waveform_points, fill='#ffffff', width=1, smooth=True)
            
            # Draw center reference line
            self.audio_canvas.create_line(0, center_y, canvas_width, center_y, fill='#555555', width=1)
            
            # Update info labels
            level_value = int(audio_level * 1000)
            threshold_value = int(threshold * 1000)
            
            self.level_label.config(text=f"Level: {level_value}")
            self.threshold_label.config(text=f"Threshold: {threshold_value}")
            
            # Color code level based on threshold
            if audio_level > threshold:
                self.level_label.config(fg='#00d4aa')  # Green - good level
            elif audio_level > threshold * 0.5:
                self.level_label.config(fg='#ffb347')  # Orange - moderate
            else:
                self.level_label.config(fg=self.colors['text_secondary'])  # Gray - low
                
        except Exception as e:
            print(f"Visualization error: {e}")
        
        # Schedule next update
        if self.is_monitoring:
            self.root.after(50, self.update_visualization)
            
    def run(self):
        """Run the demo"""
        try:
            print("Starting Audio Waveform Demo...")
            print("Make sure your microphone is working and permissions are granted.")
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\nDemo interrupted by user")
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.is_monitoring:
                self.stop_monitoring()
            self.audio_capture.cleanup()
            print("Cleanup completed")
        except Exception as e:
            print(f"Cleanup error: {e}")

if __name__ == "__main__":
    print("🎤 Audio Waveform Visualization Demo")
    print("=" * 40)
    
    try:
        demo = WaveformDemo()
        demo.run()
    except Exception as e:
        print(f"Demo failed to start: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure your microphone is connected and working")
        print("2. Check that Python has microphone permissions")
        print("3. Install required packages: pip install pyaudio numpy speechrecognition")
        input("Press Enter to exit...")