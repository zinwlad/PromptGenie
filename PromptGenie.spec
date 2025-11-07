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
    excludes=['PyQt6', 'PySide2', 'PySide6'],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

# Создаем исполняемый файл
app = EXE(
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
    console=False,  # Скрываем консоль при запуске
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)