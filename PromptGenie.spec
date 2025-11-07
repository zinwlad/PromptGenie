# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# Путь к директории с исходниками (где лежит .spec и .py)
base_path = os.path.abspath('.')

# Список файлов данных, которые нужно включить
data_files = [
    ('theme_prompts.json', '.'),
    ('keyword_library.json', '.'),
    # Добавьте другие файлы, если понадобятся (например, icons/, docs/ и т.д.)
]

# Анализ
a = Analysis(
    ['PromptGenie_qt.py'],
    pathex=[base_path],
    binaries=[],
    datas=data_files,
    hiddenimports=[],
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
    console=False,  # <-- скрывает консоль при запуске
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(base_path, 'icon.ico') if os.path.exists(os.path.join(base_path, 'icon.ico')) else None,
)