"""
测试Python运行时环境
验证嵌入式Python环境的功能完整性

测试内容:
1. Python版本检查
2. 核心依赖库导入测试
3. FunASR模型加载测试
4. FastAPI服务启动测试
5. 内存占用监控
"""

import sys
import os
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any
import psutil


class TestResult:
    """测试结果收集器"""
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def ok(self, message: str):
        print(f"✅ [OK] {message}")
        self.passed.append(message)
    
    def fail(self, message: str):
        print(f"❌ [FAIL] {message}")
        self.failed.append(message)
    
    def warn(self, message: str):
        print(f"⚠️ [WARN] {message}")
        self.warnings.append(message)
    
    def summary(self):
        total = len(self.passed) + len(self.failed)
        print(f"\n{'='*60}")
        print(f"测试总结")
        print(f"{'='*60}")
        print(f"通过: {len(self.passed)}/{total}")
        print(f"失败: {len(self.failed)}/{total}")
        print(f"警告: {len(self.warnings)}")
        print(f"通过率: {len(self.passed)/total*100:.1f}%")
        
        if self.failed:
            print(f"\n失败的测试:")
            for msg in self.failed:
                print(f"  - {msg}")
        
        if self.warnings:
            print(f"\n警告:")
            for msg in self.warnings:
                print(f"  - {msg}")


class PythonRuntimeTester:
    """Python运行时测试器"""
    
    def __init__(self, python_path: Optional[str] = None):
        """
        初始化测试器
        
        Args:
            python_path: Python可执行文件路径
                        None = 使用系统Python（开发环境测试）
                        指定路径 = 测试嵌入式Python（打包后测试）
        """
        self.python_path = python_path or sys.executable
        self.result = TestResult()
        self.project_root = Path(__file__).parent.parent
        self.runtime_path = self.project_root / "python-runtime"
    
    def run_python_command(self, code: str) -> Dict[str, Any]:
        """
        运行Python命令并返回结果
        
        Returns:
            {
                'returncode': int,
                'stdout': str,
                'stderr': str,
                'success': bool
            }
        """
        try:
            result = subprocess.run(
                [self.python_path, '-c', code],
                capture_output=True,
                text=True,
                timeout=30,
                env=self._get_env()
            )
            return {
                'returncode': result.returncode,
                'stdout': result.stdout.strip(),
                'stderr': result.stderr.strip(),
                'success': result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': 'Command timeout',
                'success': False
            }
        except Exception as e:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'success': False
            }
    
    def _get_env(self) -> dict:
        """获取环境变量"""
        env = os.environ.copy()
        
        # 如果是嵌入式Python，添加PYTHONPATH
        if self.runtime_path.exists():
            env['PYTHONPATH'] = str(self.project_root / 'server')
        
        return env
    
    def test_python_version(self):
        """测试1: Python版本检查"""
        print(f"\n{'='*60}")
        print(f"测试1: Python版本检查")
        print(f"{'='*60}")
        
        code = "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
        result = self.run_python_command(code)
        
        if result['success']:
            version = result['stdout']
            print(f"Python版本: {version}")
            
            major, minor, _ = version.split('.')
            if int(major) == 3 and int(minor) >= 8:
                self.result.ok(f"Python版本符合要求 (>= 3.8): {version}")
            else:
                self.result.fail(f"Python版本过低 (< 3.8): {version}")
        else:
            self.result.fail(f"无法获取Python版本: {result['stderr']}")
    
    def test_core_imports(self):
        """测试2: 核心依赖库导入测试"""
        print(f"\n{'='*60}")
        print(f"测试2: 核心依赖库导入测试")
        print(f"{'='*60}")
        
        # 必需依赖
        required_packages = [
            ('fastapi', 'FastAPI Web框架'),
            ('uvicorn', 'ASGI服务器'),
            ('pydantic', '数据验证'),
            ('numpy', '数值计算'),
            ('torch', '深度学习框架'),
        ]
        
        # 可选依赖（用于FunASR）
        optional_packages = [
            ('funasr', 'FunASR语音识别'),
        ]
        
        for package, desc in required_packages:
            code = f"import {package}; print('{package} OK')"
            result = self.run_python_command(code)
            
            if result['success']:
                self.result.ok(f"{desc} ({package}): 导入成功")
            else:
                self.result.fail(f"{desc} ({package}): 导入失败 - {result['stderr']}")
        
        for package, desc in optional_packages:
            code = f"import {package}; print('{package} OK')"
            result = self.run_python_command(code)
            
            if result['success']:
                self.result.ok(f"{desc} ({package}): 导入成功")
            else:
                self.result.warn(f"{desc} ({package}): 导入失败 - {result['stderr']}")
    
    def test_package_versions(self):
        """测试3: 依赖库版本检查"""
        print(f"\n{'='*60}")
        print(f"测试3: 依赖库版本检查")
        print(f"{'='*60}")
        
        packages_to_check = [
            ('torch', '2.0.0'),
            ('fastapi', '0.100.0'),
            ('uvicorn', '0.20.0'),
        ]
        
        for package, min_version in packages_to_check:
            code = f"""
import {package}
try:
    version = {package}.__version__
    print(version)
except AttributeError:
    print('unknown')
"""
            result = self.run_python_command(code)
            
            if result['success']:
                version = result['stdout']
                print(f"{package}: {version}")
                
                if version != 'unknown':
                    self.result.ok(f"{package} 版本: {version}")
                else:
                    self.result.warn(f"{package} 无法获取版本信息")
            else:
                self.result.warn(f"{package} 版本检查失败")
    
    def test_funasr_model_init(self):
        """测试4: FunASR模型初始化测试"""
        print(f"\n{'='*60}")
        print(f"测试4: FunASR模型初始化测试")
        print(f"{'='*60}")
        
        # 注意：这个测试可能需要联网下载模型
        code = """
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'  # 使用镜像加速

try:
    from funasr import AutoModel
    
    # 仅测试模型类创建，不实际加载权重（避免下载）
    print("FunASR AutoModel 导入成功")
    
    # 检查ModelScope缓存目录
    from pathlib import Path
    cache_path = Path.home() / ".cache" / "modelscope" / "hub" / "models" / "iic" / "SenseVoiceSmall"
    
    if cache_path.exists():
        print(f"ModelScope缓存模型已存在: {cache_path}")
    else:
        print("ModelScope缓存模型不存在，首次使用需下载")
    
except Exception as e:
    print(f"ERROR: {e}")
"""
        result = self.run_python_command(code)
        
        if result['success'] and 'ERROR' not in result['stdout']:
            print(result['stdout'])
            self.result.ok("FunASR模型初始化测试通过")
        else:
            error_msg = result['stderr'] or result['stdout']
            self.result.warn(f"FunASR模型初始化失败（可能需要首次下载）: {error_msg}")
    
    def test_fastapi_service(self):
        """测试5: FastAPI服务启动测试"""
        print(f"\n{'='*60}")
        print(f"测试5: FastAPI服务启动测试")
        print(f"{'='*60}")
        
        # 创建临时测试服务
        code = """
from fastapi import FastAPI
import uvicorn
import sys

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok", "python_version": f"{sys.version_info.major}.{sys.version_info.minor}"}

# 测试app创建是否成功
print("FastAPI app 创建成功")
print(f"路由数量: {len(app.routes)}")
"""
        result = self.run_python_command(code)
        
        if result['success']:
            print(result['stdout'])
            self.result.ok("FastAPI服务创建成功")
        else:
            self.result.fail(f"FastAPI服务创建失败: {result['stderr']}")
    
    def test_local_service_import(self):
        """测试6: 本地服务模块导入测试"""
        print(f"\n{'='*60}")
        print(f"测试6: 本地服务模块导入测试")
        print(f"{'='*60}")
        
        code = f"""
import sys
from pathlib import Path

# 添加项目根目录到搜索路径
project_root = Path(r'{self.project_root}')
sys.path.insert(0, str(project_root))

try:
    # 测试导入本地服务
    from server.local.main import app
    print(f"本地服务导入成功")
    print(f"FastAPI routes: {{len(app.routes)}}")
    
except ImportError as e:
    print(f"ERROR: {{e}}")
"""
        result = self.run_python_command(code)
        
        if result['success'] and 'ERROR' not in result['stdout']:
            print(result['stdout'])
            self.result.ok("本地服务模块导入成功")
        else:
            error_msg = result['stderr'] or result['stdout']
            self.result.fail(f"本地服务模块导入失败: {error_msg}")
    
    def test_memory_usage(self):
        """测试7: 内存占用监控"""
        print(f"\n{'='*60}")
        print(f"测试7: 内存占用监控")
        print(f"{'='*60}")
        
        # 获取当前Python进程内存占用
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        print(f"当前进程内存占用: {memory_mb:.1f} MB")
        
        # 测试导入torch后的内存占用
        code = """
import psutil
import os

# 导入前
process = psutil.Process(os.getpid())
mem_before = process.memory_info().rss / 1024 / 1024

# 导入torch
import torch

# 导入后
mem_after = process.memory_info().rss / 1024 / 1024

print(f"导入torch前: {mem_before:.1f} MB")
print(f"导入torch后: {mem_after:.1f} MB")
print(f"增加: {mem_after - mem_before:.1f} MB")
"""
        result = self.run_python_command(code)
        
        if result['success']:
            print(result['stdout'])
            self.result.ok("内存占用监控完成")
        else:
            self.result.warn(f"内存占用监控失败: {result['stderr']}")
    
    def test_runtime_size(self):
        """测试8: 运行时目录大小检查"""
        print(f"\n{'='*60}")
        print(f"测试8: 运行时目录大小检查")
        print(f"{'='*60}")
        
        if not self.runtime_path.exists():
            self.result.warn(f"python-runtime目录不存在: {self.runtime_path}")
            return
        
        total_size = 0
        file_count = 0
        
        for file in self.runtime_path.rglob('*'):
            if file.is_file():
                total_size += file.stat().st_size
                file_count += 1
        
        size_mb = total_size / 1024 / 1024
        
        print(f"运行时目录: {self.runtime_path}")
        print(f"文件数量: {file_count}")
        print(f"总大小: {size_mb:.1f} MB")
        
        if size_mb < 200:
            self.result.ok(f"运行时大小合理: {size_mb:.1f} MB")
        elif size_mb < 500:
            self.result.warn(f"运行时大小偏大: {size_mb:.1f} MB")
        else:
            self.result.fail(f"运行时大小过大: {size_mb:.1f} MB (建议 < 200MB)")
    
    def run_all_tests(self):
        """运行所有测试"""
        print(f"\n{'='*60}")
        print(f"Python运行时环境测试")
        print(f"{'='*60}")
        print(f"Python路径: {self.python_path}")
        print(f"项目根目录: {self.project_root}")
        print(f"运行时目录: {self.runtime_path}")
        
        # 执行测试
        self.test_python_version()
        self.test_core_imports()
        self.test_package_versions()
        self.test_funasr_model_init()
        self.test_fastapi_service()
        self.test_local_service_import()
        self.test_memory_usage()
        self.test_runtime_size()
        
        # 显示总结
        self.result.summary()
        
        return len(self.result.failed) == 0


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='测试Python运行时环境')
    parser.add_argument(
        '--python',
        help='Python可执行文件路径（默认使用系统Python）',
        default=None
    )
    
    args = parser.parse_args()
    
    # 创建测试器
    tester = PythonRuntimeTester(python_path=args.python)
    
    # 运行测试
    success = tester.run_all_tests()
    
    # 返回退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
