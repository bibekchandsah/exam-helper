#!/usr/bin/env python3
"""
Test script for screen capture functionality
"""

import tkinter as tk
from tkinter import ttk
import time
from ocr_module import OCRCapture

def test_screen_capture():
    """Test the screen capture functionality"""
    
    root = tk.Tk()
    root.title("Screen Capture Test")
    root.geometry("400x300")
    
    # Initialize OCR
    ocr = OCRCapture()
    
    # Result display
    result_text = tk.Text(root, wrap=tk.WORD, height=10)
    result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def capture_screen():
        """Capture screen and display result"""
        result_text.insert(tk.END, "Capturing screen...\n")
        result_text.update()
        
        # Capture screen
        text = ocr.capture_screen_text_immediate()
        
        if text:
            result_text.insert(tk.END, f"Captured text:\n{text}\n")
            result_text.insert(tk.END, "-" * 40 + "\n")
        else:
            result_text.insert(tk.END, "No text found.\n")
            result_text.insert(tk.END, "-" * 40 + "\n")
            
        result_text.see(tk.END)
    
    def clear_results():
        """Clear the results"""
        result_text.delete(1.0, tk.END)
    
    # Buttons
    button_frame = ttk.Frame(root)
    button_frame.pack(fill=tk.X, padx=10, pady=5)
    
    capture_btn = ttk.Button(button_frame, text="📸 Capture Screen", command=capture_screen)
    capture_btn.pack(side=tk.LEFT, padx=(0, 5))
    
    clear_btn = ttk.Button(button_frame, text="Clear", command=clear_results)
    clear_btn.pack(side=tk.LEFT)
    
    # Status
    status_label = ttk.Label(root, text=f"Tesseract available: {ocr.tesseract_available}")
    status_label.pack(pady=5)
    
    # Instructions
    instructions = ttk.Label(root, text="Click 'Capture Screen' to test OCR functionality")
    instructions.pack(pady=5)
    
    root.mainloop()

if __name__ == "__main__":
    test_screen_capture()