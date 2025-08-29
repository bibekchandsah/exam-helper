#!/usr/bin/env python3
"""
Test script for audio visualization functionality
"""

import tkinter as tk
from audio_module import AudioCapture
import threading
import time

class AudioVisualizationTest:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Audio Visualization Test")
        self.root.geometry("300x200")
        
        # Colors
        self.colors = {
            'bg_primary': '#1a1a1a',
            'bg_secondary': '#2d2d2d',
            'bg_tertiary': '#3d3d3d',
            'accent': '#4a9eff',
            'success': '#00d4aa',
            'warning': '#ffb347',
            'error': '#ff6b6b',
            'text_primary': '#ffffff',
            'text_secondary': '#b0b0b0'
        }
        
        self.root.configure(bg=self.colors['bg_primary'])
        
        # Initialize audio capture
        self.audio_capture = AudioCapture()
        self.is_monitoring = False
        
        # Create GUI
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the test GUI"""
        main_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="Audio Visualization Test", 
                              font=('Arial', 12, 'bold'),
                              fg=self.colors['text_primary'], 
                              bg=self.colors['bg_primary'])
        title_label.pack(pady=(0, 10))
        
        # Audio waveform visualization canvas
        self.audio_canvas = tk.Canvas(main_frame, 
                                     width=400, height=100,
                                     bg='#1a1a1a',
                                     highlightthickness=0)
        self.audio_canvas.pack(pady=10)
        
        # Audio level and threshold info
        info_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        info_frame.pack(pady=5)
        
        self.audio_level_label = tk.Label(info_frame, text="Level: 0", 
                                         font=('Arial', 10),
                                         fg=self.colors['text_secondary'], 
                                         bg=self.colors['bg_primary'])
        self.audio_level_label.pack(side=tk.LEFT, padx=(0, 20))
        
        self.threshold_label = tk.Label(info_frame, text="Threshold: 300", 
                                       font=('Arial', 10),
                                       fg='#ffb347',
                                       bg=self.colors['bg_primary'])
        self.threshold_label.pack(side=tk.LEFT)
        
        # Control buttons
        button_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        button_frame.pack(pady=10)
        
        self.start_btn = tk.Button(button_frame, text="Start Monitoring", 
                                  command=self.start_monitoring,
                                  bg=self.colors['success'], 
                                  fg='white',
                                  font=('Arial', 10),
                                  relief='flat',
                                  padx=10, pady=5)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = tk.Button(button_frame, text="Stop Monitoring", 
                                 command=self.stop_monitoring,
                                 bg=self.colors['error'], 
                                 fg='white',
                                 font=('Arial', 10),
                                 relief='flat',
                                 padx=10, pady=5)
        self.stop_btn.pack(side=tk.LEFT)
        
    def start_monitoring(self):
        """Start audio monitoring"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.audio_capture.start_audio_monitoring()
            self.update_visualization()
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            
    def stop_monitoring(self):
        """Stop audio monitoring"""
        if self.is_monitoring:
            self.is_monitoring = False
            self.audio_capture.stop_audio_monitoring()
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            
    def update_visualization(self):
        """Update the audio visualization (voice translator style)"""
        if not self.is_monitoring:
            return
            
        try:
            # Get current audio data
            current_rms = self.audio_capture.get_current_rms()
            rms_history = self.audio_capture.get_rms_history()
            max_rms_seen = self.audio_capture.get_max_rms_seen()
            threshold = self.audio_capture.get_threshold_level()
            
            # Clear canvas
            self.audio_canvas.delete("all")
            
            canvas_width = 450
            canvas_height = 120
            
            # Update level label
            self.audio_level_label.config(text=f"Level: {int(current_rms)}")
            
            # Draw background grid
            self.draw_background_grid(canvas_width, canvas_height)
            
            # Draw threshold line
            self.draw_threshold_line(canvas_width, canvas_height, threshold, max_rms_seen)
            
            # Draw current level bar
            self.draw_current_level(canvas_width, canvas_height, current_rms, max_rms_seen, threshold)
            
            # Draw RMS history waveform
            self.draw_rms_history(canvas_width, canvas_height, rms_history, max_rms_seen)
                
        except Exception as e:
            print(f"Visualization error: {e}")
        
        # Schedule next update
        if self.is_monitoring:
            self.root.after(50, self.update_visualization)
            
    def draw_background_grid(self, canvas_width, canvas_height):
        """Draw background grid"""
        # Horizontal lines
        for i in range(0, canvas_height, 24):
            self.audio_canvas.create_line(0, i, canvas_width, i, fill='#333333', width=1)
        
        # Vertical lines
        for i in range(0, canvas_width, 50):
            self.audio_canvas.create_line(i, 0, i, canvas_height, fill='#333333', width=1)
    
    def draw_threshold_line(self, canvas_width, canvas_height, threshold, max_rms_seen):
        """Draw threshold line"""
        if max_rms_seen > 0:
            threshold_y = canvas_height - (threshold / max_rms_seen) * canvas_height
            threshold_y = max(0, min(canvas_height, threshold_y))
            
            # Draw dashed threshold line
            self.audio_canvas.create_line(0, threshold_y, canvas_width, threshold_y, 
                                       fill='#FF9800', width=2, dash=(5, 5))
            
            # Add threshold label
            self.audio_canvas.create_text(canvas_width - 5, threshold_y - 10, 
                                       text="Threshold", fill='#FF9800', 
                                       font=('Arial', 8), anchor='ne')
    
    def draw_current_level(self, canvas_width, canvas_height, current_rms, max_rms_seen, threshold):
        """Draw current level bar"""
        if max_rms_seen > 0 and current_rms > 0:
            # Calculate bar height
            bar_height = (current_rms / max_rms_seen) * canvas_height
            bar_height = max(0, min(canvas_height, bar_height))
            
            # Determine color
            if current_rms > threshold:
                color = '#4CAF50'  # Green for speech
            else:
                color = '#2196F3'  # Blue for background noise
            
            # Draw level bar on the right side
            bar_width = 30
            x1 = canvas_width - bar_width - 5
            x2 = canvas_width - 5
            y1 = canvas_height - bar_height
            y2 = canvas_height
            
            self.audio_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=color)
            
            # Add level text
            if bar_height > 15:
                self.audio_canvas.create_text((x1 + x2) / 2, y1 + 10, 
                                           text=f"{int(current_rms)}", 
                                           fill='white', font=('Arial', 8))
                                           
        # Update level label color
        if current_rms > threshold:
            self.audio_level_label.config(fg='#4CAF50')
        elif current_rms > threshold * 0.5:
            self.audio_level_label.config(fg='#FF9800')
        else:
            self.audio_level_label.config(fg=self.colors['text_secondary'])
    
    def draw_rms_history(self, canvas_width, canvas_height, rms_history, max_rms_seen):
        """Draw RMS history waveform"""
        if len(rms_history) < 2 or max_rms_seen <= 0:
            return
        
        # Calculate points for the waveform
        points = []
        waveform_width = canvas_width - 40  # Exclude level bar area
        
        for i, rms in enumerate(rms_history):
            x = (i / len(rms_history)) * waveform_width
            y = canvas_height - (rms / max_rms_seen) * canvas_height
            y = max(0, min(canvas_height, y))
            points.extend([x, y])
        
        # Draw waveform line
        if len(points) >= 4:
            self.audio_canvas.create_line(points, fill='#00BCD4', width=2, smooth=True)
            
        # Fill area under the curve
        if len(points) >= 4:
            fill_points = points.copy()
            fill_points.extend([waveform_width, canvas_height, 0, canvas_height])
            self.audio_canvas.create_polygon(fill_points, fill='#00BCD4', 
                                         outline='', stipple='gray25')
            
    def run(self):
        """Run the test application"""
        try:
            self.root.mainloop()
        finally:
            self.stop_monitoring()
            self.audio_capture.cleanup()

if __name__ == "__main__":
    app = AudioVisualizationTest()
    app.run()