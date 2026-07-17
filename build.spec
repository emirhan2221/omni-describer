# clean_build.spec
# A fresh, from-scratch configuration for PyInstaller.

# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules

# Part 1: Gather all the necessary Python modules.
hidden_imports = [
    *collect_submodules('google.generativeai'),
    *collect_submodules('google.api_core'),
    *collect_submodules('google.auth'),
    *collect_submodules('cryptography'),
    'pyttsx3.drivers.sapi5',
    'pygame._sdl2.font',
    'openai',
    'grpc._cython',
    'accessible_output2'
]

# Part 2: Gather all the necessary data files and binaries.
added_files = [
    ('audio_describer/bin', 'bin'),
    ('audio_describer/notifs', 'notifs'),
    ('audio_describer/doc', 'doc'),
    ('audio_describer/locale', 'locale')
]

# Part 3: Define the main analysis.
a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'torch', 'torchaudio', 'torchvision',
        'numpy', 'pandas', 'scipy', 'sklearn',
        'IPython', 'Cython', 'astroid', 'pylint',
        'av', 'matplotlib', 'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,  # Remove encryption here; handled by CLI
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Part 4: Configure the final executable.
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='omni_describer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Part 5: Collect everything into a single folder for distribution.
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='omni_describer_dist',
)
