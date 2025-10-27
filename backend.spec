# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# 项目根目录
project_root = Path(os.getcwd())

# 数据文件和隐藏导入
datas = [
    (str(project_root / 'server'), 'server'),
    (str(project_root / 'AST_module'), 'AST_module'),
    (str(project_root / 'DouyinLiveWebFetcher'), 'DouyinLiveWebFetcher'),
    (str(project_root / 'config'), 'config'),
    (str(project_root / 'schemas'), 'schemas'),
    (str(project_root / 'models'), 'models'),
]

# 隐藏导入的模块
hiddenimports = [
    'uvicorn',
    'fastapi',
    'pydantic',
    'sqlalchemy',
    'asyncio',
    'websockets',
    'json',
    'logging',
    'datetime',
    'pathlib',
    'typing',
    'server.main',
    'server.api',
    'server.websocket',
    'server.database',
    'server.models',
    'server.schemas',
    'server.utils',
    'AST_module',
    'DouyinLiveWebFetcher',
]

a = Analysis(
    ['server/app/main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='backend',
)