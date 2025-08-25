#!/usr/bin/env python3
"""
Test script for Perplexity API functionality
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from perplexity_module import PerplexityClient

def test_perplexity_api():
    """Test the Perplexity API functionality"""
    
    root = tk.Tk()
    root.title("Perplexity API Test")
    root.geometry("500x400")
    
    # Initialize Perplexity client
    api_key = "pplx-QUjO6gaeFj3qxhAAoRZjYbLGiUWIpqZDRVAbOC79z6RGf78910"
    perplexity_client = PerplexityClient(api_key)
    
    # Result display
    result_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=15)
    result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Question input
    input_frame = ttk.Frame(root)
    input_frame.pack(fill=tk.X, padx=10, pady=5)
    
    ttk.Label(input_frame, text="Test Question:").pack(anchor=tk.W)
    question_entry = tk.Entry(input_frame, width=60)
    question_entry.pack(fill=tk.X, pady=5)
    question_entry.insert(0, "What is the capital of France?")
    
    def test_text_api():
        """Test text-based API"""
        question = question_entry.get().strip()
        if not question:
            return
            
        result_text.insert(tk.END, f"Question: {question}\n")
        result_text.insert(tk.END, "Processing with Perplexity...\n")
        result_text.update()
        
        def process_question():
            try:
                answer = perplexity_client.get_text_answer(question, 'detailed')
                root.after(0, lambda: result_text.insert(tk.END, f"Answer: {answer}\n"))
                root.after(0, lambda: result_text.insert(tk.END, "-" * 50 + "\n"))
                root.after(0, lambda: result_text.see(tk.END))
            except Exception as e:
                root.after(0, lambda: result_text.insert(tk.END, f"Error: {e}\n"))
            finally:
                root.after(0, lambda: text_btn.config(state='normal', text="Test Text API"))
        
        text_btn.config(state='disabled', text="Processing...")
        thread = threading.Thread(target=process_question, daemon=True)
        thread.start()
    
    def validate_api():
        """Validate API key"""
        result_text.insert(tk.END, "Validating API key...\n")
        result_text.update()
        
        def check_key():
            try:
                is_valid = perplexity_client.validate_api_key()
                status = "✅ Valid" if is_valid else "❌ Invalid"
                root.after(0, lambda: result_text.insert(tk.END, f"API Key Status: {status}\n"))
                root.after(0, lambda: result_text.insert(tk.END, "-" * 30 + "\n"))
                root.after(0, lambda: result_text.see(tk.END))
            except Exception as e:
                root.after(0, lambda: result_text.insert(tk.END, f"Validation Error: {e}\n"))
            finally:
                root.after(0, lambda: validate_btn.config(state='normal', text="Validate API Key"))
        
        validate_btn.config(state='disabled', text="Validating...")
        thread = threading.Thread(target=check_key, daemon=True)
        thread.start()
    
    def clear_results():
        """Clear the results"""
        result_text.delete(1.0, tk.END)
    
    # Buttons
    button_frame = ttk.Frame(root)
    button_frame.pack(fill=tk.X, padx=10, pady=5)
    
    text_btn = ttk.Button(button_frame, text="Test Text API", command=test_text_api)
    text_btn.pack(side=tk.LEFT, padx=(0, 5))
    
    validate_btn = ttk.Button(button_frame, text="Validate API Key", command=validate_api)
    validate_btn.pack(side=tk.LEFT, padx=(0, 5))
    
    clear_btn = ttk.Button(button_frame, text="Clear", command=clear_results)
    clear_btn.pack(side=tk.LEFT)
    
    # Status
    status_label = ttk.Label(root, text="Perplexity API Test - Ready")
    status_label.pack(pady=5)
    
    # Instructions
    instructions = ttk.Label(root, text="Test the Perplexity API functionality")
    instructions.pack(pady=5)
    
    root.mainloop()

if __name__ == "__main__":
    print("Starting Perplexity API test...")
    test_perplexity_api()