@echo off
echo Installing Tesseract OCR...
echo.

REM Try winget first (Windows 10/11)
winget install UB-Mannheim.TesseractOCR
if %errorlevel% == 0 (
    echo.
    echo Tesseract installed successfully!
    echo You may need to restart your command prompt.
    pause
    exit /b 0
)

echo.
echo Winget installation failed. Trying alternative methods...
echo.

REM Try chocolatey if available
choco --version >nul 2>&1
if %errorlevel% == 0 (
    echo Installing via Chocolatey...
    choco install tesseract
    if %errorlevel% == 0 (
        echo Tesseract installed successfully via Chocolatey!
        pause
        exit /b 0
    )
)

echo.
echo Automatic installation failed.
echo Please manually download and install Tesseract from:
echo https://github.com/UB-Mannheim/tesseract/wiki
echo.
echo After installation, make sure tesseract.exe is in your PATH
echo or the application will find it automatically.
echo.
pause