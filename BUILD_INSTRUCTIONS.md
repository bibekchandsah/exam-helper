# Building Exam Helper Executable

## Quick Start
Run the automated build script:
```bash
python build_exe.py
```

## Manual Build Process

### 1. Install Build Dependencies
```bash
pip install -r build_requirements.txt
```

### 2. Install All Project Dependencies
```bash
pip install -r requirements.txt
```

### 3. Build Options

#### Option A: Automated Build (Recommended)
```bash
python build_exe.py
```

#### Option B: Manual PyInstaller Command
```bash
pyinstaller --onefile --windowed --icon=icon.png --add-data "config.json;." --add-data "icon.png;." --add-data "prompt.txt;." --hidden-import=PIL._tkinter_finder --hidden-import=win32clipboard --hidden-import=pyaudio --name=ExamHelper exam_helper.py
```

#### Option C: Using Spec File
```bash
pyinstaller --clean exam_helper.spec
```

## Build Output
- `dist/ExamHelper.exe` - The standalone executable
- `ExamHelper_Distribution/` - Ready-to-distribute folder

## Distribution
The `ExamHelper_Distribution` folder contains:
- `ExamHelper.exe` - Main application
- `README.txt` - User instructions

## Troubleshooting

### Common Issues

1. **Missing modules error**
   - Add missing modules to `hiddenimports` in the spec file
   - Use `--hidden-import=module_name` flag

2. **Large file size**
   - Use `--exclude-module` to remove unused modules
   - Consider using `--onedir` instead of `--onefile` for faster startup

3. **Antivirus false positives**
   - This is common with PyInstaller executables
   - Users may need to add exception in their antivirus
   - Consider code signing for production distribution

4. **Missing data files**
   - Ensure all required files are in `datas` section of spec file
   - Use `--add-data` flag for additional files

### Advanced Options

#### Reduce File Size
```bash
pyinstaller --onefile --windowed --strip --upx-dir=/path/to/upx exam_helper.py
```

#### Debug Build
```bash
pyinstaller --onefile --console --debug=all exam_helper.py
```

#### Include Additional Files
```bash
pyinstaller --add-data "additional_file.txt;." --add-data "folder/*;folder/" exam_helper.py
```

## Testing the Executable
1. Test on a clean Windows machine without Python installed
2. Verify all features work correctly
3. Check that config files are created properly
4. Test with different user permissions

## Code Signing (Optional)
For production distribution, consider code signing:
```bash
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com ExamHelper.exe
```