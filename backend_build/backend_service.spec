# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(SPECPATH).parent

# 数据文件收集
datas = []

# 收集配置文件
config_files = [
    "config.json",
]

for config_file in config_files:
    config_path = BASE_DIR / config_file
    if config_path.exists():
        datas.append((str(config_path), "."))

# 隐藏导入
hiddenimports = [
    'uvicorn',
    'uvicorn.main',
    'uvicorn.server',
    'fastapi',
    'fastapi.applications',
    'pydantic',
    'sqlalchemy',
    'requests',
    'websockets',
    'flet',
    'flet_core',
    'numpy',
    'torch',
    'torchaudio',
    'transformers',
    'librosa',
    'soundfile',
    'pyaudio',
    'opencv-python',
    'pillow',
    'matplotlib',
    'seaborn',
    'pandas',
    'scipy',
    'scikit-learn',
]

# 排除模块
excludes = [
    'tkinter',
    'matplotlib.backends._backend_tk',
    'PIL._tkinter_finder',
]

# 二进制文件
binaries = []

# 主分析
a = Analysis(
    [str(BASE_DIR / 'service_launcher.py')],
    pathex=[str(BASE_DIR)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 去重
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 生成可执行文件
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='timao_backend_service',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
