#!/usr/bin/env python3
"""
Diagnostic script for Exam Helper
Checks all dependencies and configurations
"""

import sys
import os
import platform
import subprocess
import json

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    else:
        print("✅ Python version OK")
        return True

def check_package(package_name, import_name=None):
    """Check if a Python package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print(f"✅ {package_name} installed")
        return True
    except ImportError:
        print(f"❌ {package_name} not installed")
        return False

def check_tesseract():
    """Check Tesseract OCR installation"""
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✅ Tesseract OCR: {version}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Check common Windows paths
    if platform.system() == "Windows":
        paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
        ]
        
        for path in paths:
            if os.path.exists(path):
                print(f"✅ Tesseract found at: {path}")
                print("   (May need manual PATH configuration)")
                return True
    
    print("❌ Tesseract OCR not found")
    print("   Install with: winget install UB-Mannheim.TesseractOCR")
    return False

def check_openai_config():
    """Check OpenAI configuration"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            
        api_key = config.get('openai_api_key', '')
        if api_key and len(api_key) > 10:
            print("✅ OpenAI API key configured")
            
            # Test the API key
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                print("✅ OpenAI API key working")
                return True
            except Exception as e:
                print(f"❌ OpenAI API key error: {e}")
                return False
        else:
            print("❌ OpenAI API key not configured")
            return False
            
    except FileNotFoundError:
        print("❌ config.json not found")
        return False
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def check_audio_devices():
    """Check audio devices"""
    try:
        import pyaudio
        
        audio = pyaudio.PyAudio()
        device_count = audio.get_device_count()
        
        print(f"✅ Audio devices found: {device_count}")
        
        # Find default input device
        try:
            default_input = audio.get_default_input_device_info()
            print(f"   Default input: {default_input['name']}")
        except:
            print("   ❌ No default input device")
            
        audio.terminate()
        return True
        
    except Exception as e:
        print(f"❌ Audio system error: {e}")
        return False

def main():
    print("Exam Helper Diagnostic Tool")
    print("=" * 40)
    
    checks = []
    
    # Check Python version
    checks.append(check_python_version())
    
    print("\nPython Packages:")
    print("-" * 20)
    
    # Check required packages
    packages = [
        ('pillow', 'PIL'),
        ('pytesseract', 'pytesseract'),
        ('pyaudio', 'pyaudio'),
        ('speechrecognition', 'speech_recognition'),
        ('openai', 'openai'),
        ('pynput', 'pynput'),
        ('pygetwindow', 'pygetwindow'),
        ('pywin32', 'win32gui'),
        ('numpy', 'numpy'),
        ('opencv-python', 'cv2'),
        ('psutil', 'psutil')
    ]
    
    for package, import_name in packages:
        checks.append(check_package(package, import_name))
    
    print("\nExternal Dependencies:")
    print("-" * 25)
    
    # Check Tesseract
    checks.append(check_tesseract())
    
    print("\nConfiguration:")
    print("-" * 15)
    
    # Check OpenAI config
    checks.append(check_openai_config())
    
    print("\nSystem:")
    print("-" * 10)
    
    # Check audio
    checks.append(check_audio_devices())
    
    # Print OS info
    print(f"Operating System: {platform.system()} {platform.release()}")
    
    print("\n" + "=" * 40)
    print("Summary:")
    
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"🎉 All checks passed ({passed}/{total})")
        print("You should be able to run the Exam Helper!")
    else:
        print(f"⚠️  {total - passed} issues found ({passed}/{total} passed)")
        print("Please fix the issues above before running the application.")
    
    print("\nNext steps:")
    if passed < total:
        print("1. Install missing dependencies")
        print("2. Configure OpenAI API key in config.json")
        print("3. Run this diagnostic again")
    else:
        print("1. Run: python exam_helper.py")
        print("2. Configure your API key in Settings if not done")

if __name__ == "__main__":
    main()