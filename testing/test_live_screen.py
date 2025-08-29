#!/usr/bin/env python3
"""
Test script for Live Screen functionality
"""

import json
import time
from gemini_module import GeminiClient
from screenshot_module import ScreenshotCapture

def load_config():
    """Load API key from config"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print("❌ config.json not found")
        return {}

def test_live_screen():
    """Test live screen capture and analysis"""
    config = load_config()
    gemini_api_key = config.get('gemini_api_key', '')
    
    if not gemini_api_key:
        print("❌ No Gemini API key found in config.json")
        print("Please add your Gemini API key to config.json")
        return
    
    print("🔴 Testing Live Screen functionality...")
    print("=" * 50)
    
    # Initialize components
    gemini_client = GeminiClient(gemini_api_key)
    screenshot_capture = ScreenshotCapture()
    
    print("✅ Components initialized")
    print("📸 Taking test screenshot...")
    
    try:
        # Capture screenshot
        base64_image = screenshot_capture.capture_and_encode(
            exclude_window_title="Test",
            resize=True,
            format='PNG'
        )
        
        if base64_image:
            print("✅ Screenshot captured successfully")
            print("🤖 Analyzing with Gemini...")
            
            # Analyze with Gemini
            response = gemini_client.analyze_image(base64_image, "short")
            
            print("\n" + "=" * 50)
            print("📋 ANALYSIS RESULT:")
            print("-" * 50)
            print(response)
            print("=" * 50)
            
            # Check if response is meaningful
            if len(response) > 20 and not response.startswith("Error"):
                print("✅ Live screen test successful!")
            else:
                print("⚠️ Response might be too generic or an error occurred")
                
        else:
            print("❌ Failed to capture screenshot")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")

def main():
    print("Live Screen Test")
    print("=" * 50)
    print("This will capture your current screen and analyze it with Gemini")
    print("Make sure you have some text or questions visible on screen")
    print()
    
    input("Press Enter to continue...")
    print()
    
    test_live_screen()
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    main()