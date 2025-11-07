# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['I:\\MY_PROGRAMS\\PromptGenie\\PromptGenie_qt.py'],
    pathex=[],
    binaries=[],
    datas=[('I:\\MY_PROGRAMS\\PromptGenie/theme_prompts.json', '.'), ('I:\\MY_PROGRAMS\\PromptGenie/keyword_library.json', '.')],
    hiddenimports=['PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'pyperclip'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='PromptGenie',
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
    icon='NONE',
)
