@echo off
echo ========================================
echo    Exam Helper Optimized Builder
echo ========================================
echo.
echo This build excludes heavy ML libraries
echo for faster compilation and smaller size.
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

echo Python found. Starting optimized build...
echo.

REM Run the optimized build script
python build_optimized.py

echo.
echo Build process completed.
echo Check the output above for any errors.
echo.
pause