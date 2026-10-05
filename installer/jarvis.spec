# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification file for building JARVIS standalone desktop application."""

import os
from pathlib import Path

block_cipher = None
project_root = os.path.abspath(os.path.join(SPECPATH, ".."))

datas = [
    (os.path.join(project_root, "frontend", "dist"), os.path.join("frontend", "dist")),
    (os.path.join(project_root, "config", "settings.json"), "config"),
    (os.path.join(project_root, "memory"), "memory"),
]

hiddenimports = [
    "PySide6",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineCore",
    "ctypes",
    "sqlite3",
    "json",
    "urllib",
    "webbrowser",
    "actions",
    "actions.system_controls",
    "actions.screen",
    "actions.browser",
    "automation",
    "automation.workflows",
    "ai",
    "ai.provider",
    "memory",
    "memory.store",
    "voice",
    "voice.windows_recognizer",
    "voice.windows_synthesizer",
    "wake",
    "wake.wake_detector",
    "security",
    "security.activity_log",
]

a = Analysis(
    [os.path.join(project_root, "main.py")],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="JARVIS",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Windowed desktop application (no cmd prompt popup)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="JARVIS",
)
