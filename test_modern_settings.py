#!/usr/bin/env python3
"""
Simple test script for the modern settings window
"""

import tkinter as tk
import json
import os
import sys

def test_modern_settings():
    """Test the modern settings window"""
    
    try:
        print("Importing SettingsWindow...")
        # Import the main application to access the SettingsWindow class
        from exam_helper import SettingsWindow
        print("✓ Import successful")
        
        # Create a test config
        test_config = {
            'openai_api_key': '',
            'gemini_api_key': '',
            'perplexity_api_key': '',
            'scan_interval': 3,
            'live_screen_interval': 5,
            'audio_enabled': True,
            'ocr_enabled': True,
            'live_screen_enabled': False,
            'openai_model': 'gpt-4o',
            'gemini_model': 'gemini-1.5-flash',
            'working_models': ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo', 'gpt-4o', 'gpt-4o-mini'],
            'working_gemini_models': ['gemini-1.5-flash', 'gemini-1.5-pro'],
            'use_custom_prompt': False,
            'custom_image_prompt': "What's in this image? Please analyze and describe what you see."
        }
        print("✓ Test config created")
        
        def save_callback():
            """Mock save callback"""
            print("Settings saved!")
            print("Current config:", test_config)
        
        print("Creating root window...")
        # Create root window (hidden)
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        print("✓ Root window created")
        
        print("Creating settings window...")
        # Create and show the modern settings window
        settings_window = SettingsWindow(root, test_config, save_callback)
        print("✓ Settings window created")
        
        # Make sure the window is visible
        settings_window.window.deiconify()
        settings_window.window.lift()
        settings_window.window.focus_force()
        print("✓ Settings window should now be visible")
        
        # Run the GUI
        print("Starting GUI main loop...")
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    print("Testing Modern Settings Window...")
    print("This will open the new modern settings interface.")
    print("Features to test:")
    print("- Modern dark theme")
    print("- Scrollable interface") 
    print("- Modern input fields")
    print("- Custom checkboxes")
    print("- Styled buttons")
    print("- Model scanning (requires valid API keys)")
    print("\nStarting test...")
    
    test_modern_settings()