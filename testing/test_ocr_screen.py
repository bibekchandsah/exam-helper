#!/usr/bin/env python3
"""
Test script for OCR Screen functionality
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

def test_ocr_screen():
    """Test OCR screen capture and text extraction"""
    config = load_config()
    gemini_api_key = config.get('gemini_api_key', '')
    
    if not gemini_api_key:
        print("❌ No Gemini API key found in config.json")
        print("Please add your Gemini API key to config.json")
        return
    
    print("📝 Testing OCR Screen functionality...")
    print("=" * 50)
    
    # Initialize components
    gemini_client = GeminiClient(gemini_api_key)
    screenshot_capture = ScreenshotCapture()
    
    print("✅ Components initialized")
    print("📸 Taking test screenshot for OCR...")
    
    try:
        # Capture screenshot
        base64_image = screenshot_capture.capture_and_encode(
            exclude_window_title="Test",
            resize=True,
            format='PNG'
        )
        
        if base64_image:
            print("✅ Screenshot captured successfully")
            print("🔍 Extracting text with Gemini OCR...")
            
            # Test both response modes
            print("\n" + "=" * 50)
            print("📋 SHORT MODE EXTRACTION:")
            print("-" * 50)
            
            short_response = gemini_client.extract_text_content(base64_image, "short")
            print(short_response)
            
            print("\n" + "=" * 50)
            print("📋 DETAILED MODE EXTRACTION:")
            print("-" * 50)
            
            detailed_response = gemini_client.extract_text_content(base64_image, "detailed")
            print(detailed_response)
            
            print("\n" + "=" * 50)
            
            # Check if responses are meaningful
            if len(short_response) > 20 and not short_response.startswith("Error"):
                print("✅ OCR Screen test successful!")
                
                # Check for common question patterns
                question_indicators = ['?', 'A)', 'B)', 'C)', 'D)', 'A.', 'B.', 'C.', 'D.', 'question', 'answer']
                if any(indicator in short_response for indicator in question_indicators):
                    print("🎯 Detected questions or multiple choice options!")
                else:
                    print("📄 Text extracted successfully (no questions detected)")
            else:
                print("⚠️ Response might be too generic or an error occurred")
                
        else:
            print("❌ Failed to capture screenshot")
            
    except Exception as e:
        print(f"❌ Error during OCR test: {e}")

def main():
    print("OCR Screen Test")
    print("=" * 50)
    print("This will capture your current screen and extract text using Gemini OCR")
    print("Make sure you have some text, questions, or documents visible on screen")
    print("Best results with:")
    print("- Multiple choice questions")
    print("- Text documents")
    print("- Forms or surveys")
    print("- Mathematical problems")
    print()
    
    input("Press Enter to continue...")
    print()
    
    test_ocr_screen()
    
    print("\n" + "=" * 50)
    print("OCR Test completed!")
    print("\nTip: The OCR function works best with:")
    print("- Clear, readable text")
    print("- High contrast (dark text on light background)")
    print("- Questions with multiple choice options")
    print("- Structured documents")

if __name__ == "__main__":
    main()