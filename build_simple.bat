@echo off
echo ========================================
echo    Simple PyInstaller Build
echo ========================================
echo.

REM Install PyInstaller if not present
pip install pyinstaller

echo Building executable with PyInstaller...
echo.

REM Build with all your modules included
pyinstaller --onefile ^
    --windowed ^
    --name "ExamHelper" ^
    --icon "icon.png" ^
    --add-data "config.json;." ^
    --add-data "icon.png;." ^
    --add-data "prompt.txt;." ^
    --add-data "ocr_module.py;." ^
    --add-data "audio_module.py;." ^
    --add-data "llm_module.py;." ^
    --add-data "stealth_module.py;." ^
    --add-data "screenshot_module.py;." ^
    --add-data "gemini_module.py;." ^
    --add-data "perplexity_module.py;." ^
    --hidden-import "ocr_module" ^
    --hidden-import "audio_module" ^
    --hidden-import "llm_module" ^
    --hidden-import "stealth_module" ^
    --hidden-import "screenshot_module" ^
    --hidden-import "gemini_module" ^
    --hidden-import "perplexity_module" ^
    --hidden-import "tkinter" ^
    --hidden-import "tkinter.ttk" ^
    --hidden-import "PIL" ^
    --hidden-import "numpy" ^
    --hidden-import "cv2" ^
    --hidden-import "pyaudio" ^
    --hidden-import "speech_recognition" ^
    --hidden-import "openai" ^
    --hidden-import "google.generativeai" ^
    --hidden-import "pynput" ^
    --hidden-import "pytesseract" ^
    --hidden-import "win32clipboard" ^
    --hidden-import "win32con" ^
    --hidden-import "pygetwindow" ^
    --hidden-import "psutil" ^
    --hidden-import "requests" ^
    exam_helper.py

echo.
echo Build completed! Check the 'dist' folder for your executable.
echo.
pause