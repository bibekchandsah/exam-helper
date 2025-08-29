#!/usr/bin/env python3
"""
Test script for toggle functionality
"""

import tkinter as tk
from tkinter import ttk
import time
import threading

def test_toggle_functionality():
    """Simple test window to verify toggle buttons work"""
    
    root = tk.Tk()
    root.title("Toggle Test")
    root.geometry("300x200")
    
    # Test variables
    ocr_running = tk.BooleanVar(value=False)
    audio_running = tk.BooleanVar(value=False)
    
    def toggle_ocr():
        current = ocr_running.get()
        ocr_running.set(not current)
        ocr_btn.config(text="Stop OCR" if not current else "Start OCR")
        ocr_status.config(text=f"OCR: {'On' if not current else 'Off'}", 
                         foreground='green' if not current else 'red')
        print(f"OCR toggled: {not current}")
        
    def toggle_audio():
        current = audio_running.get()
        audio_running.set(not current)
        audio_btn.config(text="Disable Audio" if not current else "Enable Audio")
        audio_status.config(text=f"Audio: {'On' if not current else 'Off'}", 
                           foreground='green' if not current else 'red')
        print(f"Audio toggled: {not current}")
    
    # Status labels
    status_frame = ttk.Frame(root)
    status_frame.pack(fill=tk.X, padx=10, pady=10)
    
    ocr_status = ttk.Label(status_frame, text="OCR: Off", foreground='red')
    ocr_status.pack(side=tk.LEFT)
    
    audio_status = ttk.Label(status_frame, text="Audio: Off", foreground='red')
    audio_status.pack(side=tk.RIGHT)
    
    # Control buttons
    control_frame = ttk.Frame(root)
    control_frame.pack(fill=tk.X, padx=10, pady=10)
    
    ocr_btn = ttk.Button(control_frame, text="Start OCR", command=toggle_ocr)
    ocr_btn.pack(side=tk.LEFT, padx=(0, 5))
    
    audio_btn = ttk.Button(control_frame, text="Enable Audio", command=toggle_audio)
    audio_btn.pack(side=tk.LEFT, padx=(0, 5))
    
    # Info label
    info_label = ttk.Label(root, text="Test the toggle buttons above.\nCheck console for output.")
    info_label.pack(pady=20)
    
    root.mainloop()

if __name__ == "__main__":
    print("Starting toggle functionality test...")
    test_toggle_functionality()