#!/usr/bin/env python3
"""
Optimized build script for Exam Helper - excludes heavy ML libraries
"""
import os
import sys
import subprocess
import shutil
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

def build_optimized_executable():
    """Build executable with optimized settings to avoid heavy ML libraries"""
    print("Building optimized executable...")
    print("This will exclude heavy ML libraries like TensorFlow and PyTorch")
    print("-" * 60)
    
    # Check if module files exist
    required_modules = [
        'ocr_module.py', 'audio_module.py', 'llm_module.py', 
        'stealth_module.py', 'screenshot_module.py', 
        'gemini_module.py', 'perplexity_module.py'
    ]
    
    missing_modules = []
    for module in required_modules:
        if not os.path.exists(module):
            missing_modules.append(module)
    
    if missing_modules:
        print("⚠️  Warning: The following module files are missing:")
        for module in missing_modules:
            print(f"   - {module}")
        print("The build will continue, but these modules won't be included.")
        print()
    
    # Build command with optimized settings
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "ExamHelper",
        "--clean",
        
        # Add data files
        "--add-data", "config.json;.",
        "--add-data", "prompt.txt;.",
    ]
    
    # Add icon if it exists
    if os.path.exists("icon.png"):
        cmd.extend(["--icon", "icon.png", "--add-data", "icon.png;."])
    
    # Add module files that exist
    for module in required_modules:
        if os.path.exists(module):
            cmd.extend(["--add-data", f"{module};."])
    
    # Essential hidden imports only
    essential_imports = [
        # Your custom modules
        "ocr_module", "audio_module", "llm_module", 
        "stealth_module", "screenshot_module", 
        "gemini_module", "perplexity_module",
        
        # GUI essentials
        "tkinter", "tkinter.ttk", "tkinter.messagebox", 
        "tkinter.filedialog", "tkinter.scrolledtext",
        
        # Windows essentials
        "win32clipboard", "win32con", "win32api", "win32gui",
        
        # Core libraries
        "PIL", "PIL.Image", "PIL.ImageGrab", "PIL.ImageTk",
        "numpy", "cv2", "pytesseract",
        
        # Audio
        "pyaudio", "speech_recognition", "wave",
        
        # API clients
        "openai", "google.generativeai", "requests",
        
        # System
        "pynput", "pynput.keyboard", "pynput.mouse",
        "pygetwindow", "psutil",
    ]
    
    for imp in essential_imports:
        cmd.extend(["--hidden-import", imp])
    
    # Exclude heavy libraries
    excludes = [
        "tensorflow", "torch", "torchvision", "torchaudio",
        "matplotlib", "scipy", "pandas", "sklearn",
        "jupyter", "notebook", "IPython",
        "pytest", "unittest", "doctest",
    ]
    
    for exc in excludes:
        cmd.extend(["--exclude-module", exc])
    
    # Add main file
    cmd.append("exam_helper.py")
    
    print("Running PyInstaller with optimized settings...")
    print("Command:", " ".join(cmd[:10]) + "... (truncated)")
    print()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Build completed successfully!")
            
            # Check if executable was created
            exe_path = Path("dist/ExamHelper.exe")
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"✓ Executable created: {exe_path}")
                print(f"✓ File size: {size_mb:.1f} MB")
                return True
            else:
                print("✗ Executable not found in dist folder")
                return False
        else:
            print("✗ Build failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"✗ Build failed with error: {e}")
        return False

def main():
    """Main build process"""
    print("=== Exam Helper Optimized Builder ===")
    print("This build excludes heavy ML libraries for faster compilation")
    print()
    
    # Step 1: Install PyInstaller
    install_pyinstaller()
    
    # Step 2: Clean previous builds
    clean_build_dirs()
    
    # Step 3: Build executable
    if build_optimized_executable():
        print()
        print("=== Build Complete! ===")
        print("Your optimized executable is ready in the 'dist' folder")
        print("File: dist/ExamHelper.exe")
        print()
        print("This build should be much smaller and faster than the full build.")
    else:
        print()
        print("Build failed. Try the simple build method instead:")
        print("python build_exe.py")

if __name__ == "__main__":
    main()