#!/usr/bin/env python3
"""
Test script for Gemini API integration
"""

import json
import google.generativeai as genai
from gemini_module import GeminiClient

def load_config():
    """Load API key from config"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        return config.get('gemini_api_key', '')
    except FileNotFoundError:
        print("❌ config.json not found")
        return ''

def test_available_models(api_key):
    """Test what models are available"""
    if not api_key:
        print("❌ No Gemini API key found in config.json")
        return
    
    try:
        genai.configure(api_key=api_key)
        print("🔍 Available Gemini models:")
        print("-" * 40)
        
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                print(f"✅ {model.name}")
                print(f"   Supports: {', '.join(model.supported_generation_methods)}")
                print()
                
    except Exception as e:
        print(f"❌ Error listing models: {e}")

def test_text_generation(api_key):
    """Test basic text generation"""
    if not api_key:
        return
        
    try:
        client = GeminiClient(api_key)
        print("🧪 Testing text generation...")
        
        response = client.get_text_answer("What is 2+2?", "short")
        print(f"✅ Text response: {response}")
        
    except Exception as e:
        print(f"❌ Text generation error: {e}")

def test_image_analysis(api_key):
    """Test image analysis with a simple test image"""
    if not api_key:
        return
        
    try:
        import base64
        from PIL import Image
        import io
        
        # Create a simple test image with text
        img = Image.new('RGB', (200, 100), color='white')
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        client = GeminiClient(api_key)
        print("🖼️ Testing image analysis...")
        
        response = client.analyze_image(img_base64, "short")
        print(f"✅ Image analysis response: {response}")
        
    except Exception as e:
        print(f"❌ Image analysis error: {e}")

def main():
    print("Gemini API Test")
    print("=" * 50)
    
    # Load API key
    api_key = load_config()
    
    if not api_key:
        print("❌ No Gemini API key found!")
        print("Please add your Gemini API key to config.json")
        print("Get your key from: https://makersuite.google.com/app/apikey")
        return
    
    print(f"✅ API key loaded: {api_key[:10]}...")
    print()
    
    # Test available models
    test_available_models(api_key)
    
    # Test text generation
    test_text_generation(api_key)
    print()
    
    # Test image analysis
    test_image_analysis(api_key)
    
    print("\n" + "=" * 50)
    print("✅ Gemini API test completed!")

if __name__ == "__main__":
    main()