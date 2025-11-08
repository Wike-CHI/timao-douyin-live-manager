#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 FunASR 导入和相关依赖"""

import sys
import os

print("Python 版本:", sys.version)
print("Python 路径:", sys.executable)
print("当前目录:", os.getcwd())
print()

# 测试 funasr 导入
print("=" * 60)
print("测试 FunASR 导入...")
try:
    import funasr
    print("✅ FunASR 导入成功")
    print("FunASR 模块路径:", funasr.__file__)
    if hasattr(funasr, '__version__'):
        print("FunASR 版本:", funasr.__version__)
    
    # 测试 AutoModel
    try:
        from funasr import AutoModel
        print("✅ AutoModel 导入成功")
    except Exception as e:
        print(f"❌ AutoModel 导入失败: {e}")
except ImportError as e:
    print(f"❌ FunASR 导入失败: {e}")
    print("可能的原因:")
    print("  1. funasr 未安装")
    print("  2. 虚拟环境未激活")
    print("  3. Python 路径配置错误")

print()
print("=" * 60)
print("测试 FunASR 依赖包...")

required_packages = {
    'editdistance': 'editdistance',
    'hydra': 'hydra-core',
    'jaconv': 'jaconv',
    'jamo': 'jamo',
    'jieba': 'jieba',
    'librosa': 'librosa',
    'oss2': 'oss2',
    'sentencepiece': 'sentencepiece',
    'soundfile': 'soundfile',
    'tensorboardX': 'tensorboardX',
    'umap': 'umap-learn',
    'pytorch_wpe': 'pytorch-wpe'
}

missing_deps = []
installed_deps = []

for module_name, package_name in required_packages.items():
    try:
        __import__(module_name)
        installed_deps.append(package_name)
        print(f"✅ {package_name} 已安装")
    except ImportError:
        missing_deps.append(package_name)
        print(f"❌ {package_name} 未安装")

print()
if missing_deps:
    print(f"缺少 {len(missing_deps)} 个依赖包:")
    for pkg in missing_deps:
        print(f"  - {pkg}")
    print()
    print("安装命令:")
    print(f"pip install {' '.join(missing_deps)}")
else:
    print("✅ 所有依赖包已安装")

print()
print("=" * 60)
print("总结:")
print(f"  已安装: {len(installed_deps)} 个")
print(f"  缺少: {len(missing_deps)} 个")

