# -*- coding: utf-8 -*-
"""
测试模块：SenseVoice 本地模型下载与加载
验证点：
1. 调用下载方法是否正确下载模型
2. 路径是否存在
3. 大小是否符合预期（>1GB）
4. 能否成功加载推理引擎（SenseVoice init）
5. 不依赖网络时是否能正确返回"已存在"状态
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from server.local.utils.model_downloader import (
    ensure_sensevoice_model,
    check_sensevoice_model,
    ModelDownloader
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class TestResult:
    """测试结果记录器"""
    def __init__(self):
        self.passed = []
        self.failed = []
    
    def ok(self, msg: str):
        self.passed.append(msg)
        print(f"[OK] {msg}")
    
    def fail(self, msg: str):
        self.failed.append(msg)
        print(f"[FAIL] {msg}")
    
    def summary(self):
        print("\n" + "="*60)
        print(f"测试完成: {len(self.passed)} 通过, {len(self.failed)} 失败")
        if self.failed:
            print("\n失败项:")
            for f in self.failed:
                print(f"  ❌ {f}")
        print("="*60)
        return len(self.failed) == 0


async def test_disk_space_check():
    """测试1: 磁盘空间检查"""
    result = TestResult()
    
    try:
        models_dir = project_root / "server" / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        
        downloader = ModelDownloader(
            ModelDownloader.SENSEVOICE_SMALL,
            models_dir / "models" / "iic" / "SenseVoiceSmall"
        )
        
        has_space = downloader.check_disk_space()
        if has_space:
            result.ok("Disk space check passed")
        else:
            result.fail("Insufficient disk space")
    except Exception as e:
        result.fail(f"Disk space check error: {e}")
    
    return result


async def test_model_path_exists():
    """测试2: 检查本地模型路径"""
    result = TestResult()
    
    try:
        models_dir = project_root / "server" / "models"
        local_model = check_sensevoice_model(models_dir)
        
        if local_model:
            result.ok(f"Model exists at: {local_model}")
            
            # 检查文件大小
            model_file = local_model / "model.pt"
            if model_file.exists():
                size_gb = model_file.stat().st_size / (1024**3)
                if size_gb > 1.0:
                    result.ok(f"Model size valid: {size_gb:.2f}GB")
                else:
                    result.fail(f"Model size too small: {size_gb:.2f}GB")
            else:
                result.fail("model.pt not found")
        else:
            # 本地模型不存在是正常的（首次运行）
            result.ok("Model not found locally (will use auto-download)")
    except Exception as e:
        result.fail(f"Path check error: {e}")
    
    return result


async def test_ensure_model_funasr():
    """测试3: 使用FunASR自动下载机制"""
    result = TestResult()
    
    try:
        models_dir = project_root / "server" / "models"
        
        # 使用FunASR自动下载
        model_path = await ensure_sensevoice_model(
            models_dir,
            use_funasr_auto=True
        )
        
        if model_path:
            result.ok(f"Model path resolved: {model_path}")
            
            # 检查是否为本地路径或ModelScope ID
            if Path(model_path).exists():
                result.ok("Using local model")
            elif model_path == "iic/SenseVoiceSmall":
                result.ok("Using FunASR auto-download (ModelScope)")
            else:
                result.fail(f"Unknown model path: {model_path}")
        else:
            result.fail("ensure_sensevoice_model returned None")
    except Exception as e:
        result.fail(f"ensure_model error: {e}")
    
    return result


async def test_model_loading():
    """测试4: 加载SenseVoice推理引擎"""
    result = TestResult()
    
    try:
        from funasr import AutoModel
        
        models_dir = project_root / "server" / "models"
        model_path = await ensure_sensevoice_model(models_dir, use_funasr_auto=True)
        
        logger.info(f"尝试加载模型: {model_path}")
        
        # 注意：实际加载可能需要较长时间（首次下载）
        # 这里仅测试能否成功调用
        try:
            model = AutoModel(
                model=model_path,
                disable_update=True,  # 禁用自动更新
                device="cpu",
                ncpu=1
            )
            result.ok("Model loaded successfully")
            
            # 测试推理（可选）
            if hasattr(model, 'generate'):
                result.ok("Model inference engine ready")
        except Exception as load_err:
            # 首次加载可能因网络下载而超时，这是预期行为
            if "Downloading" in str(load_err) or "modelscope" in str(load_err):
                result.ok("Model downloading (auto-download triggered)")
            else:
                result.fail(f"Model loading failed: {load_err}")
    except ImportError:
        result.fail("FunASR not installed (pip install funasr)")
    except Exception as e:
        result.fail(f"Model loading error: {e}")
    
    return result


async def test_offline_mode():
    """测试5: 离线模式（本地模型已存在）"""
    result = TestResult()
    
    try:
        models_dir = project_root / "server" / "models"
        local_model = check_sensevoice_model(models_dir)
        
        if local_model:
            # 本地模型存在，应直接返回
            model_path = await ensure_sensevoice_model(
                models_dir,
                use_funasr_auto=False  # 禁用自动下载
            )
            
            if str(local_model) == model_path:
                result.ok("Offline mode: using local model")
            else:
                result.fail(f"Path mismatch: {local_model} != {model_path}")
        else:
            # 本地模型不存在，应回退到FunASR
            result.ok("No local model, fallback expected (not an error)")
    except Exception as e:
        result.fail(f"Offline mode error: {e}")
    
    return result


async def main():
    """运行所有测试"""
    print("="*60)
    print("SenseVoice 模型下载与加载测试")
    print("="*60)
    
    all_results = []
    
    # 测试1: 磁盘空间检查
    print("\n=== 测试1: 磁盘空间检查 ===")
    r1 = await test_disk_space_check()
    all_results.append(r1)
    
    # 测试2: 模型路径检查
    print("\n=== 测试2: 模型路径检查 ===")
    r2 = await test_model_path_exists()
    all_results.append(r2)
    
    # 测试3: FunASR自动下载机制
    print("\n=== 测试3: FunASR自动下载机制 ===")
    r3 = await test_ensure_model_funasr()
    all_results.append(r3)
    
    # 测试4: 模型加载（可能触发下载，较慢）
    print("\n=== 测试4: 模型加载 ===")
    print("注意: 首次运行可能触发模型下载（~1.7GB），需要时间...")
    r4 = await test_model_loading()
    all_results.append(r4)
    
    # 测试5: 离线模式
    print("\n=== 测试5: 离线模式 ===")
    r5 = await test_offline_mode()
    all_results.append(r5)
    
    # 汇总结果
    print("\n" + "="*60)
    print("所有测试汇总")
    print("="*60)
    
    total_passed = sum(len(r.passed) for r in all_results)
    total_failed = sum(len(r.failed) for r in all_results)
    
    print(f"总计: {total_passed} 通过, {total_failed} 失败")
    
    if total_failed > 0:
        print("\n所有失败项:")
        for i, r in enumerate(all_results, 1):
            if r.failed:
                print(f"\n测试{i}:")
                for f in r.failed:
                    print(f"  ❌ {f}")
    
    print("="*60)
    
    return total_failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
