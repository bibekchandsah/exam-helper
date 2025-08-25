#!/usr/bin/env python3
"""
Demo script showing the new model selection feature
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
from llm_module import LLMClient

class ModelSelectionDemo:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OpenAI Model Selection Demo")
        self.root.geometry("500x400")
        
        self.load_config()
        self.setup_gui()
        
    def load_config(self):
        """Load configuration"""
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {
                'openai_api_key': '',
                'openai_model': 'gpt-3.5-turbo',
                'working_models': []
            }
    
    def setup_gui(self):
        """Setup the demo GUI"""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_frame, text="🤖 OpenAI Model Selection Demo", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # API Key section
        ttk.Label(main_frame, text="API Key:").pack(anchor=tk.W)
        self.api_key_var = tk.StringVar(value=self.config.get('openai_api_key', ''))
        api_key_entry = ttk.Entry(main_frame, textvariable=self.api_key_var, show='*', width=60)
        api_key_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Model selection section
        model_frame = ttk.LabelFrame(main_frame, text="Model Selection", padding=10)
        model_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Current model
        current_frame = ttk.Frame(model_frame)
        current_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(current_frame, text="Current Model:").pack(side=tk.LEFT)
        self.current_model_label = ttk.Label(current_frame, text=self.config.get('openai_model', 'gpt-3.5-turbo'),
                                           font=('Arial', 10, 'bold'), foreground='blue')
        self.current_model_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Model dropdown
        dropdown_frame = ttk.Frame(model_frame)
        dropdown_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(dropdown_frame, text="Select Model:").pack(side=tk.LEFT)
        
        working_models = self.config.get('working_models', ['gpt-3.5-turbo', 'gpt-4'])
        self.model_var = tk.StringVar(value=self.config.get('openai_model', 'gpt-3.5-turbo'))
        self.model_combo = ttk.Combobox(dropdown_frame, textvariable=self.model_var,
                                       values=working_models, state='readonly', width=20)
        self.model_combo.pack(side=tk.LEFT, padx=(10, 10))
        
        # Scan button
        self.scan_btn = ttk.Button(dropdown_frame, text="🔍 Scan Models", command=self.scan_models)
        self.scan_btn.pack(side=tk.LEFT)
        
        # Status
        self.status_label = ttk.Label(model_frame, text="Ready", foreground='green')
        self.status_label.pack(pady=(5, 0))
        
        # Test section
        test_frame = ttk.LabelFrame(main_frame, text="Test Model", padding=10)
        test_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Question input
        ttk.Label(test_frame, text="Test Question:").pack(anchor=tk.W)
        self.question_var = tk.StringVar(value="What is the capital of France?")
        question_entry = ttk.Entry(test_frame, textvariable=self.question_var, width=60)
        question_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Test button
        test_btn = ttk.Button(test_frame, text="🧪 Test Current Model", command=self.test_model)
        test_btn.pack(pady=(0, 10))
        
        # Response area
        self.response_text = tk.Text(test_frame, height=8, wrap=tk.WORD)
        self.response_text.pack(fill=tk.BOTH, expand=True)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Apply Model", command=self.apply_model).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Save Config", command=self.save_config).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(button_frame, text="Close", command=self.root.destroy).pack(side=tk.RIGHT)
    
    def scan_models(self):
        """Scan for working models"""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showwarning("Warning", "Please enter your API key first.")
            return
        
        self.scan_btn.config(text="Scanning...", state='disabled')
        self.status_label.config(text="Scanning models...", foreground='orange')
        self.root.update()
        
        try:
            client = LLMClient(api_key)
            working_models = client.get_working_models()
            
            if working_models:
                self.model_combo['values'] = working_models
                self.config['working_models'] = working_models
                
                self.status_label.config(text=f"✓ Found {len(working_models)} models", foreground='green')
                messagebox.showinfo("Success", f"Found {len(working_models)} working models:\n" + 
                                  "\n".join(working_models))
            else:
                self.status_label.config(text="✗ No models found", foreground='red')
                messagebox.showerror("Error", "No working models found. Please check your API key.")
        
        except Exception as e:
            self.status_label.config(text="✗ Scan failed", foreground='red')
            messagebox.showerror("Error", f"Failed to scan models: {str(e)}")
        
        finally:
            self.scan_btn.config(text="🔍 Scan Models", state='normal')
    
    def apply_model(self):
        """Apply the selected model"""
        selected_model = self.model_var.get()
        self.config['openai_model'] = selected_model
        self.current_model_label.config(text=selected_model)
        self.status_label.config(text=f"Model changed to {selected_model}", foreground='blue')
    
    def test_model(self):
        """Test the current model"""
        api_key = self.api_key_var.get().strip()
        question = self.question_var.get().strip()
        
        if not api_key:
            messagebox.showwarning("Warning", "Please enter your API key first.")
            return
        
        if not question:
            messagebox.showwarning("Warning", "Please enter a test question.")
            return
        
        try:
            current_model = self.config.get('openai_model', 'gpt-3.5-turbo')
            client = LLMClient(api_key, current_model)
            
            self.response_text.delete(1.0, tk.END)
            self.response_text.insert(tk.END, f"Testing model: {current_model}\n")
            self.response_text.insert(tk.END, f"Question: {question}\n\n")
            self.response_text.insert(tk.END, "Getting response...\n")
            self.root.update()
            
            response = client.get_answer(question, "short")
            
            self.response_text.delete(1.0, tk.END)
            self.response_text.insert(tk.END, f"Model: {current_model}\n")
            self.response_text.insert(tk.END, f"Question: {question}\n\n")
            self.response_text.insert(tk.END, f"Response:\n{response}")
            
        except Exception as e:
            self.response_text.delete(1.0, tk.END)
            self.response_text.insert(tk.END, f"Error testing model: {str(e)}")
    
    def save_config(self):
        """Save configuration"""
        self.config['openai_api_key'] = self.api_key_var.get()
        
        try:
            with open('config.json', 'w') as f:
                json.dump(self.config, f, indent=2)
            messagebox.showinfo("Success", "Configuration saved!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {str(e)}")
    
    def run(self):
        """Run the demo"""
        self.root.mainloop()

if __name__ == "__main__":
    demo = ModelSelectionDemo()
    demo.run()