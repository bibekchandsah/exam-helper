#!/usr/bin/env python3
"""
Installation script for Exam Helper dependencies
"""

import subprocess
import sys
import os
import platform

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install {package}: {e}")
        return False

def check_tesseract():
    """Check if Tesseract OCR is installed"""
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Tesseract OCR is installed")
            return True
    except FileNotFoundError:
        pass
    
    print("✗ Tesseract OCR not found")
    print("Please install Tesseract OCR:")
    if platform.system() == "Windows":
        print("  Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("  Or use: winget install UB-Mannheim.TesseractOCR")
    elif platform.system() == "Darwin":
        print("  Use: brew install tesseract")
    else:
        print("  Use: sudo apt-get install tesseract-ocr")
    
    return False

def main():
    print("Installing Exam Helper dependencies...")
    print("=" * 50)
    
    # Required packages
    packages = [
        "pillow>=9.0.0",
        "pytesseract>=0.3.10",
        "pyaudio>=0.2.11",
        "speechrecognition>=3.10.0",
        "openai>=1.0.0",
        "google-generativeai>=0.3.0",
        "pynput>=1.7.6",
        "pygetwindow>=0.0.9",
        "pywin32>=306",
        "numpy>=1.21.0",
        "opencv-python>=4.5.0",
        "psutil>=5.8.0",
        "requests>=2.25.0"
    ]
    
    failed_packages = []
    
    # Install packages
    for package in packages:
        if not install_package(package):
            failed_packages.append(package)
    
    print("\n" + "=" * 50)
    
    # Check Tesseract
    tesseract_ok = check_tesseract()
    
    # Summary
    print("\nInstallation Summary:")
    print("=" * 20)
    
    if failed_packages:
        print(f"✗ Failed to install: {', '.join(failed_packages)}")
    else:
        print("✓ All Python packages installed successfully")
    
    if not tesseract_ok:
        print("✗ Tesseract OCR needs manual installation")
    
    if not failed_packages and tesseract_ok:
        print("\n🎉 All dependencies installed successfully!")
        print("You can now run: python exam_helper.py")
    else:
        print("\n⚠️  Some dependencies need attention before running the application")
    
    # Additional setup instructions
    print("\nAdditional Setup:")
    print("1. Add your OpenAI API key in the settings")
    print("2. Ensure microphone permissions are granted")
    print("3. Run as administrator for full stealth mode functionality")

if __name__ == "__main__":
    main()