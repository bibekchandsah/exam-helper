#!/usr/bin/env python3
"""
Build script for creating standalone executable of Exam Helper
"""
import os
import sys
import subprocess
import shutil
import time
from pathlib import Path

def install_pyinstaller():
    """Install PyInstaller if not already installed"""
    try:
        import PyInstaller
        print("✓ PyInstaller already installed")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller installed successfully")

def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✓ Cleaned {dir_name} directory")

def create_spec_file(quick_build=False):
    """Create PyInstaller spec file with proper configuration"""
    # Set UPX compression based on build type
    upx_setting = "False" if quick_build else "True"
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['exam_helper.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.json', '.'),
        ('icon.png', '.'),
        ('prompt.txt', '.'),
        ('ocr_module.py', '.'),
        ('audio_module.py', '.'),
        ('llm_module.py', '.'),
        ('stealth_module.py', '.'),
        ('screenshot_module.py', '.'),
        ('gemini_module.py', '.'),
        ('perplexity_module.py', '.'),
    ],
    hiddenimports=[
        # Core modules from your application
        'ocr_module',
        'audio_module', 
        'llm_module',
        'stealth_module',
        'screenshot_module',
        'gemini_module',
        'perplexity_module',
        # GUI and system libraries
        'PIL._tkinter_finder',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'tkinter.scrolledtext',
        'win32clipboard',
        'win32con',
        'win32api',
        'win32gui',
        'pywintypes',
        # Audio processing
        'pyaudio',
        'speech_recognition',
        'wave',
        'audioop',
        # Computer vision and OCR
        'cv2',
        'numpy',
        'pytesseract',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageGrab',
        # AI and API libraries
        'openai',
        'google.generativeai',
        'google.ai.generativelanguage',
        'google.auth',
        'google.auth.transport.requests',
        # System interaction
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
        'pygetwindow',
        'psutil',
        'requests',
        'urllib3',
        'certifi',
        # Standard library modules that might be missed
        'threading',
        'queue',
        'json',
        'base64',
        'io',
        'datetime',
        'logging',
        'os',
        'sys',
        'time',
        'pathlib',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        # Exclude heavy ML libraries that might not be needed
        'tensorflow',
        'torch',
        'torchvision',
        'matplotlib.tests',
        'numpy.tests',
        'scipy.tests',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ExamHelper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx={upx_setting},
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True if you want console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.png'
)
'''
    
    with open('exam_helper.spec', 'w') as f:
        f.write(spec_content)
    print("✓ Created exam_helper.spec file")

def build_executable():
    """Build the executable using PyInstaller with real-time progress"""
    print("Building executable... This may take a few minutes.")
    print("Progress will be shown below:")
    print("-" * 50)
    
    # Build using the spec file
    cmd = [sys.executable, "-m", "PyInstaller", "--clean", "--log-level", "INFO", "exam_helper.spec"]
    
    try:
        # Use Popen for real-time output
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Track progress indicators
        progress_indicators = [
            ("INFO: PyInstaller:", "Initializing PyInstaller"),
            ("INFO: Loading module", "Loading modules"),
            ("INFO: Analyzing", "Analyzing dependencies"),
            ("INFO: Processing", "Processing files"),
            ("INFO: Looking for", "Searching for imports"),
            ("INFO: Building", "Building components"),
            ("INFO: Copying", "Copying files"),
            ("INFO: Building EXE", "Creating executable"),
            ("INFO: Building directory", "Building directory structure"),
            ("INFO: Appending PKG", "Packaging files"),
            ("INFO: Building COLLECT", "Finalizing build")
        ]
        
        current_step = 0
        total_steps = len(progress_indicators)
        start_time = time.time()
        
        # Read output line by line
        for line in process.stdout:
            line = line.strip()
            if line:
                # Check for progress indicators
                for i, (indicator, description) in enumerate(progress_indicators):
                    if indicator in line and i >= current_step:
                        current_step = i + 1
                        percentage = int((current_step / total_steps) * 100)
                        elapsed = time.time() - start_time
                        
                        # Estimate remaining time
                        if current_step > 1:
                            estimated_total = elapsed * (total_steps / current_step)
                            remaining = max(0, estimated_total - elapsed)
                            time_str = f" (ETA: {remaining:.0f}s)"
                        else:
                            time_str = ""
                        
                        # Create progress bar
                        bar_length = 20
                        filled_length = int(bar_length * percentage // 100)
                        bar = '█' * filled_length + '░' * (bar_length - filled_length)
                        
                        print(f"[{percentage:3d}%] {bar} {description}{time_str}")
                        break
                else:
                    # Print other important lines
                    if any(keyword in line.lower() for keyword in ['error', 'warning', 'failed', 'missing']):
                        print(f"      ⚠️  {line}")
                    elif "INFO: Building EXE from EXE-00.toc completed successfully" in line:
                        elapsed = time.time() - start_time
                        print(f"[100%] ████████████████████ Build completed in {elapsed:.1f}s")
        
        # Wait for process to complete
        return_code = process.wait()
        
        if return_code == 0:
            print("-" * 50)
            print("✓ Build completed successfully!")
            return True
        else:
            print(f"✗ Build failed with return code: {return_code}")
            return False
            
    except Exception as e:
        print(f"✗ Build failed with error: {e}")
        return False

def create_distribution_folder():
    """Create a clean distribution folder"""
    dist_folder = Path("ExamHelper_Distribution")
    
    if dist_folder.exists():
        shutil.rmtree(dist_folder)
    
    dist_folder.mkdir()
    
    # Copy the executable
    exe_path = Path("dist/ExamHelper.exe")
    if exe_path.exists():
        shutil.copy2(exe_path, dist_folder / "ExamHelper.exe")
        print(f"✓ Copied executable to {dist_folder}")
    else:
        print("✗ Executable not found in dist folder")
        return False
    
    # Create README for distribution
    readme_content = """# Exam Helper - Standalone Application

## Installation
1. Extract all files to a folder of your choice
2. Run ExamHelper.exe

## Requirements
- Windows 10/11
- No additional software installation required (all dependencies are bundled)

## Features
- Screen capture and OCR
- Live screen monitoring
- Audio recording and transcription
- AI-powered question answering
- Multiple AI model support (OpenAI, Gemini, Perplexity)

## Configuration
The application will create a config.json file on first run where you can:
- Add your API keys for different AI services
- Customize recording durations
- Select preferred AI models

## Troubleshooting
- If the application doesn't start, try running as administrator
- Make sure Windows Defender isn't blocking the executable
- Check that your antivirus software allows the application to run

## Support
For issues or questions, please refer to the original documentation.
"""
    
    with open(dist_folder / "README.txt", 'w') as f:
        f.write(readme_content)
    
    print(f"✓ Created distribution folder: {dist_folder}")
    return True

def main():
    """Main build process"""
    print("=== Exam Helper Executable Builder ===")
    print()
    
    # Ask user for build type
    print("Build options:")
    print("1. Full build (optimized, slower)")
    print("2. Quick build (faster, larger file)")
    choice = input("Choose build type (1 or 2, default=1): ").strip()
    
    quick_build = choice == "2"
    if quick_build:
        print("Using quick build mode...")
    else:
        print("Using full build mode...")
    print()
    
    # Step 1: Install PyInstaller
    install_pyinstaller()
    
    # Step 2: Clean previous builds
    clean_build_dirs()
    
    # Step 3: Create spec file
    create_spec_file(quick_build)
    
    # Step 4: Build executable
    if not build_executable():
        print("Build failed. Please check the error messages above.")
        return False
    
    # Step 5: Create distribution folder
    if not create_distribution_folder():
        print("Failed to create distribution folder.")
        return False
    
    print()
    print("=== Build Complete! ===")
    print("Your executable is ready in the 'ExamHelper_Distribution' folder")
    print("You can now distribute this folder to users.")
    print()
    print("Files created:")
    print("- ExamHelper_Distribution/ExamHelper.exe (main executable)")
    print("- ExamHelper_Distribution/README.txt (user instructions)")
    
    return True

if __name__ == "__main__":
    main()