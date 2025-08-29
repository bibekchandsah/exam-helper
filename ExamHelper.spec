# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['exam_helper.py'],
    pathex=[],
    binaries=[],
    datas=[('config.json', '.'), ('prompt.txt', '.'), ('icon.png', '.'), ('ocr_module.py', '.'), ('audio_module.py', '.'), ('llm_module.py', '.'), ('stealth_module.py', '.'), ('screenshot_module.py', '.'), ('gemini_module.py', '.'), ('perplexity_module.py', '.')],
    hiddenimports=['ocr_module', 'audio_module', 'llm_module', 'stealth_module', 'screenshot_module', 'gemini_module', 'perplexity_module', 'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog', 'tkinter.scrolledtext', 'win32clipboard', 'win32con', 'win32api', 'win32gui', 'PIL', 'PIL.Image', 'PIL.ImageGrab', 'PIL.ImageTk', 'numpy', 'cv2', 'pytesseract', 'pyaudio', 'speech_recognition', 'wave', 'openai', 'google.generativeai', 'requests', 'pynput', 'pynput.keyboard', 'pynput.mouse', 'pygetwindow', 'psutil'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tensorflow', 'torch', 'torchvision', 'torchaudio', 'matplotlib', 'scipy', 'pandas', 'sklearn', 'jupyter', 'notebook', 'IPython', 'pytest', 'unittest', 'doctest'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ExamHelper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.png'],
)
