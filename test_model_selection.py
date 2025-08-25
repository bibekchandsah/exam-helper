#!/usr/bin/env python3
"""
Test script for OpenAI model selection functionality
"""

import json
from llm_module import LLMClient

def load_config():
    """Load API key from config"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print("Config file not found. Please run the main application first.")
        return None

def test_model_selection():
    """Test model selection and detection"""
    print("🔍 Testing OpenAI Model Selection")
    print("=" * 50)
    
    # Load config
    config = load_config()
    if not config:
        return
    
    api_key = config.get('openai_api_key', '')
    if not api_key:
        print("❌ No OpenAI API key found in config.json")
        print("Please set your API key in the settings first.")
        return
    
    # Test LLM client
    print(f"🔑 Using API key: {api_key[:10]}...")
    
    # Create client with default model
    current_model = config.get('openai_model', 'gpt-3.5-turbo')
    print(f"📋 Current configured model: {current_model}")
    
    client = LLMClient(api_key, current_model)
    
    # Test current model
    print(f"\n🧪 Testing current model: {client.get_current_model()}")
    try:
        response = client.get_answer("What is 2+2?", "short")
        print(f"✅ Response: {response}")
    except Exception as e:
        print(f"❌ Error with current model: {e}")
    
    # Scan for working models
    print(f"\n🔍 Scanning for working models...")
    working_models = client.get_working_models()
    
    if working_models:
        print(f"✅ Found {len(working_models)} working models:")
        for i, model in enumerate(working_models, 1):
            print(f"  {i}. {model}")
        
        # Test switching models
        if len(working_models) > 1:
            print(f"\n🔄 Testing model switching...")
            for model in working_models[:2]:  # Test first 2 models
                print(f"\n📝 Testing {model}:")
                client.set_model(model)
                try:
                    response = client.get_answer("What is the capital of France?", "short")
                    print(f"✅ {model}: {response}")
                except Exception as e:
                    print(f"❌ {model}: {e}")
    else:
        print("❌ No working models found!")
        print("This could mean:")
        print("  - Invalid API key")
        print("  - No access to any models")
        print("  - Network connectivity issues")
    
    print(f"\n📊 Summary:")
    print(f"  - Current model: {client.get_current_model()}")
    print(f"  - Working models: {len(working_models)}")
    print(f"  - Models checked: {client.models_checked}")

if __name__ == "__main__":
    test_model_selection()