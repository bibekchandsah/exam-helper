# -*- mode: python ; coding: utf-8 -*-

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
    hooksconfig={},
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
    upx=False,
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
