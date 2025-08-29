# Exam Helper - Build Guide

This guide will help you compile your Exam Helper application into a standalone executable (.exe) file using PyInstaller.

## Prerequisites

1. **Python 3.7+** installed on your system
2. **All dependencies** installed (run `pip install -r requirements.txt`)
3. **PyInstaller** (will be installed automatically by the build scripts)

## Build Methods

### Method 1: Advanced Build Script (Recommended)

Use the comprehensive build script with progress tracking:

```bash
# Run the advanced build script
python build_exe.py
```

Or double-click: `build_executable.bat`

**Features:**
- Real-time progress tracking
- Optimized build options
- Automatic cleanup
- Creates distribution folder with README
- Includes all your custom modules

### Method 2: Simple Build Script

For a quick and simple build:

```bash
# Double-click this file
build_simple.bat
```

**Features:**
- One-click build process
- All modules automatically included
- Creates single executable file

### Method 3: Manual PyInstaller Command

If you prefer to run PyInstaller manually:

```bash
# Install PyInstaller
pip install pyinstaller

# Create the executable
pyinstaller --onefile --windowed --name "ExamHelper" --icon "icon.png" \
    --add-data "config.json;." \
    --add-data "icon.png;." \
    --add-data "prompt.txt;." \
    --add-data "ocr_module.py;." \
    --add-data "audio_module.py;." \
    --add-data "llm_module.py;." \
    --add-data "stealth_module.py;." \
    --add-data "screenshot_module.py;." \
    --add-data "gemini_module.py;." \
    --add-data "perplexity_module.py;." \
    --hidden-import "ocr_module" \
    --hidden-import "audio_module" \
    --hidden-import "llm_module" \
    --hidden-import "stealth_module" \
    --hidden-import "screenshot_module" \
    --hidden-import "gemini_module" \
    --hidden-import "perplexity_module" \
    exam_helper.py
```

## What Gets Included

The build process automatically includes:

### Your Custom Modules
- `ocr_module.py` - OCR functionality
- `audio_module.py` - Audio capture and processing
- `llm_module.py` - LLM client for OpenAI
- `stealth_module.py` - Stealth window functionality
- `screenshot_module.py` - Screenshot capture
- `gemini_module.py` - Google Gemini integration
- `perplexity_module.py` - Perplexity AI integration

### Configuration Files
- `config.json` - Application configuration
- `icon.png` - Application icon
- `prompt.txt` - Custom prompts

### Dependencies
- All Python libraries from `requirements.txt`
- Windows-specific libraries (win32, etc.)
- GUI libraries (tkinter, PIL)
- AI/ML libraries (openai, google-generativeai)
- Audio/video libraries (pyaudio, cv2)

## Build Output

After successful build, you'll find:

```
dist/
├── ExamHelper.exe          # Your standalone executable

ExamHelper_Distribution/    # (Method 1 only)
├── ExamHelper.exe         # Standalone executable
└── README.txt             # User instructions
```

## Troubleshooting

### Common Issues

1. **Missing modules error**
   - Make sure all your `.py` files are in the same directory
   - Check that all imports in `exam_helper.py` are working

2. **PyInstaller not found**
   - Run: `pip install pyinstaller`

3. **Build fails with import errors**
   - Install missing dependencies: `pip install -r requirements.txt`

4. **Executable doesn't start**
   - Try building with console mode first (remove `--windowed` flag)
   - Check Windows Defender/antivirus settings

5. **Large executable size**
   - Use Method 1 with "Full build" option for optimization
   - Consider using `--exclude-module` for unused libraries

### Debug Mode

To build with console window for debugging:

```bash
pyinstaller --onefile --console --name "ExamHelper_Debug" exam_helper.py
```

## Distribution

The final executable (`ExamHelper.exe`) is completely standalone and can be:
- Copied to any Windows computer
- Run without Python installation
- Distributed to users without additional setup

## File Size Optimization

To reduce executable size:
1. Use Method 1 with "Full build" option (enables UPX compression)
2. Remove unused imports from your Python files
3. Consider excluding large unused libraries

## Security Notes

- Some antivirus software may flag PyInstaller executables as suspicious
- Add the executable to your antivirus whitelist if needed
- The executable is safe - it's just your Python code bundled with the interpreter