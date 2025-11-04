#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后端服务打包脚本
使用PyInstaller将Python后端服务打包为可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

class BackendBuilder:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.build_dir = self.base_dir / "backend_build"
        self.dist_dir = self.base_dir / "backend_dist"
        self.spec_file = self.build_dir / "backend_service.spec"
        
    def clean_build(self):
        """清理构建目录"""
        print("🧹 清理构建目录...")
        
        # 清理目录
        for dir_path in [self.build_dir, self.dist_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path, ignore_errors=True)
            dir_path.mkdir(parents=True, exist_ok=True)
        
        print("   ✅ 构建目录清理完成")
    
    def collect_dependencies(self):
        """收集所有依赖文件"""
        print("📦 收集项目依赖...")
        
        # 查找所有requirements.txt文件
        req_files = []
        
        # 现在主要使用 server/requirements.txt (已合并所有依赖)
        search_dirs = [
            self.base_dir / "server",  # 统一的依赖文件
            self.base_dir,  # 根目录的requirements.txt（兼容）
        ]
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
                
            req_file = search_dir / "requirements.txt"
            if req_file.exists():
                req_files.append(req_file)
                print(f"   发现依赖文件: {req_file.relative_to(self.base_dir)}")
        
        # 合并所有依赖，处理版本冲突
        merged_req = self.build_dir / "merged_requirements.txt"
        all_deps = {}  # 使用字典来处理版本冲突
        
        for req_file in req_files:
            try:
                with open(req_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # 跳过相对路径依赖
                            if line.startswith('../') or line.startswith('./'):
                                print(f"   跳过相对路径依赖: {line}")
                                continue
                            
                            # 解析包名和版本
                            if '==' in line:
                                pkg_name = line.split('==')[0].strip()
                                version = line.split('==')[1].strip()
                                # 保留最新的精确版本
                                if pkg_name not in all_deps or '==' in all_deps[pkg_name]:
                                    all_deps[pkg_name] = line
                            elif '>=' in line:
                                pkg_name = line.split('>=')[0].strip()
                                # 如果没有精确版本，使用范围版本
                                if pkg_name not in all_deps or '>=' in all_deps[pkg_name]:
                                    all_deps[pkg_name] = line
                            else:
                                # 其他格式的依赖
                                pkg_name = line.split()[0] if ' ' in line else line
                                if pkg_name not in all_deps:
                                    all_deps[pkg_name] = line
            except Exception as e:
                print(f"   警告: 读取 {req_file} 失败: {e}")
        
        # 写入合并后的依赖文件
        with open(merged_req, 'w', encoding='utf-8') as f:
            for dep in sorted(all_deps.values()):
                f.write(f"{dep}\n")
        
        print(f"   ✅ 合并依赖文件: {merged_req}")
        return merged_req
    
    def generate_spec_file(self):
        """生成PyInstaller spec文件"""
        print("📝 生成PyInstaller配置文件...")
        
        spec_content = '''# -*- mode: python ; coding: utf-8 -*-

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
    'numpy',
    'torch',
    'torchaudio',
    'transformers',
    'librosa',
    'soundfile',
    'pyaudio',
    'pandas',
    'scipy',
    'scikit-learn',
    # 新整合的模块
    'server.modules',
    'server.modules.ast',
    'server.modules.ast.sensevoice_service',
    'server.modules.ast.audio_capture',
    'server.modules.ast.postprocess',
    'server.modules.ast.acrcloud_client',
    'server.modules.douyin',
    'server.modules.douyin.liveMan',
    'server.modules.douyin.ac_signature',
    'server.modules.streamcap',
    'server.modules.streamcap.platforms',
    'server.modules.streamcap.media',
    'funasr',
    'sentencepiece',
    'jieba',
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
    [str(BASE_DIR / 'scripts' / 'service_launcher.py')],
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
'''
        
        with open(self.spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        print(f"   ✅ 生成配置文件: {self.spec_file}")
    
    def install_dependencies(self):
        """安装打包依赖"""
        print("🔧 安装打包依赖...")
        
        # 安装PyInstaller
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", 
                "pyinstaller>=5.0"
            ], check=True)
            print("   ✅ PyInstaller安装完成")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ PyInstaller安装失败: {e}")
            return False
        
        # 跳过依赖安装，假设环境已经配置好
        print("   ⚠️ 跳过依赖安装，假设运行环境已配置")
        print("   💡 如需安装依赖，请手动运行: pip install -r requirements.txt")
        
        return True
    
    def build_executable(self):
        """构建可执行文件"""
        print("🔨 开始构建后端服务可执行文件...")
        
        try:
            # 运行PyInstaller
            cmd = [
                sys.executable, "-m", "PyInstaller",
                "--clean",
                "--noconfirm",
                "--distpath", str(self.dist_dir),
                "--workpath", str(self.build_dir / "work"),
                str(self.spec_file)
            ]
            
            print(f"   执行命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                cwd=self.base_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("   ✅ 构建成功!")
                
                # 检查输出文件
                exe_file = self.dist_dir / "timao_backend_service.exe"
                if exe_file.exists():
                    size_mb = exe_file.stat().st_size / (1024 * 1024)
                    print(f"   📦 可执行文件: {exe_file}")
                    print(f"   📊 文件大小: {size_mb:.1f} MB")
                    return True
                else:
                    print("   ❌ 未找到生成的可执行文件")
                    return False
            else:
                print(f"   ❌ 构建失败:")
                print(f"   stdout: {result.stdout}")
                print(f"   stderr: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"   ❌ 构建过程出错: {e}")
            return False
    
    def run(self):
        """运行完整的构建流程"""
        print("🎯 开始后端服务打包流程")
        print("=" * 50)
        
        try:
            # 1. 清理构建目录
            self.clean_build()
            
            # 2. 安装依赖
            if not self.install_dependencies():
                return False
            
            # 3. 生成spec文件
            self.generate_spec_file()
            
            # 4. 构建可执行文件
            if not self.build_executable():
                return False
            
            print("=" * 50)
            print("🎉 后端服务打包完成!")
            print(f"📁 输出目录: {self.dist_dir}")
            
            return True
            
        except Exception as e:
            print(f"❌ 打包失败: {e}")
            return False

def main():
    """主函数"""
    builder = BackendBuilder()
    success = builder.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()