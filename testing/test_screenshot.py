#!/usr/bin/env python3
"""
Test script for screenshot capture functionality
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from screenshot_module import ScreenshotCapture
from perplexity_module import PerplexityClient
import json

def test_screenshot_functionality():
    """Test the screenshot and vision API functionality"""
    
    # Load config for API key
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except:
        config = {'openai_api_key': ''}
    
    root = tk.Tk()
    root.title("Screenshot Vision Test")
    root.geometry("500x400")
    
    # Initialize components
    screenshot_capture = ScreenshotCapture()
    perplexity_client = PerplexityClient(config.get('perplexity_api_key', ''))
    
    # Result display
    result_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=15)
    result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def capture_and_analyze():
        """Capture screenshot and analyze with Vision API"""
        result_text.insert(tk.END, "Capturing screenshot...\n")
        result_text.update()
        
        def process_screenshot():
            try:
                # Capture screenshot excluding this test window
                base64_image = screenshot_capture.capture_and_encode(
                    exclude_window_title="Screenshot Vision Test",
                    resize=True,
                    format='PNG'
                )
                
                if base64_image:
                    root.after(0, lambda: result_text.insert(tk.END, "Screenshot captured! Analyzing with AI...\n"))
                    root.after(0, lambda: result_text.update())
                    
                    # Analyze with Perplexity Vision API
                    answer = perplexity_client.analyze_image(base64_image, 'detailed')
                    
                    # Display result
                    root.after(0, lambda: result_text.insert(tk.END, f"\nAI Analysis:\n{answer}\n"))
                    root.after(0, lambda: result_text.insert(tk.END, "-" * 50 + "\n"))
                    root.after(0, lambda: result_text.see(tk.END))
                    
                else:
                    root.after(0, lambda: result_text.insert(tk.END, "Failed to capture screenshot.\n"))
                    
            except Exception as e:
                root.after(0, lambda: result_text.insert(tk.END, f"Error: {e}\n"))
            
            finally:
                root.after(0, lambda: capture_btn.config(state='normal', text="📸 Capture & Analyze"))
        
        # Disable button and run in thread
        capture_btn.config(state='disabled', text="📸 Processing...")
        thread = threading.Thread(target=process_screenshot, daemon=True)
        thread.start()
    
    def test_basic_capture():
        """Test basic screenshot capture without AI"""
        result_text.insert(tk.END, "Testing basic screenshot capture...\n")
        
        try:
            base64_image = screenshot_capture.capture_and_encode(
                exclude_window_title="Screenshot Vision Test"
            )
            
            if base64_image:
                result_text.insert(tk.END, f"Screenshot captured successfully! Size: {len(base64_image)} characters\n")
            else:
                result_text.insert(tk.END, "Failed to capture screenshot.\n")
                
        except Exception as e:
            result_text.insert(tk.END, f"Error: {e}\n")
        
        result_text.insert(tk.END, "-" * 30 + "\n")
        result_text.see(tk.END)
    
    def clear_results():
        """Clear the results"""
        result_text.delete(1.0, tk.END)
    
    # Buttons
    button_frame = ttk.Frame(root)
    button_frame.pack(fill=tk.X, padx=10, pady=5)
    
    capture_btn = ttk.Button(button_frame, text="📸 Capture & Analyze", command=capture_and_analyze)
    capture_btn.pack(side=tk.LEFT, padx=(0, 5))
    
    test_btn = ttk.Button(button_frame, text="Test Basic Capture", command=test_basic_capture)
    test_btn.pack(side=tk.LEFT, padx=(0, 5))
    
    clear_btn = ttk.Button(button_frame, text="Clear", command=clear_results)
    clear_btn.pack(side=tk.LEFT)
    
    # Status
    api_status = "✅ Perplexity API Key Configured" if config.get('perplexity_api_key') else "❌ No Perplexity API Key"
    status_label = ttk.Label(root, text=f"Status: {api_status}")
    status_label.pack(pady=5)
    
    # Instructions
    instructions = ttk.Label(root, text="Open some content in another window, then click 'Capture & Analyze'")
    instructions.pack(pady=5)
    
    root.mainloop()

if __name__ == "__main__":
    print("Starting screenshot vision test...")
    test_screenshot_functionality()