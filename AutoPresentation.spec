# -*- mode: python ; coding: utf-8 -*-
# Configuration PyInstaller : produit dist/AutoPresentation.exe (un seul fichier, sans console).

a = Analysis(
    ["app.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=["win32com", "win32com.client", "pythoncom", "pywintypes"],
    hookspath=[],
    runtime_hooks=[],
    excludes=["pytest", "unittest.mock"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="AutoPresentation",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)
