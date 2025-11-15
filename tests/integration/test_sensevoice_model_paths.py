#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SenseVoice 模型路径测试

审查人：叶维哲

测试 SenseVoice 模型路径配置是否正确。
"""

import sys
from pathlib import Path
import logging

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_model_paths():
    """测试模型路径配置"""
    logger.info("=" * 60)
    logger.info("测试 SenseVoice 模型路径配置")
    logger.info("=" * 60)
    
    # 预期的模型路径
    expected_model_dir = project_root / "server" / "modules" / "models" / ".cache" / "models" / "iic" / "SenseVoiceSmall"
    expected_vad_dir = project_root / "server" / "modules" / "models" / ".cache" / "models" / "iic" / "speech_fsmn_vad_zh-cn-16k-common-pytorch"
    
    logger.info(f"\n项目根目录: {project_root}")
    logger.info(f"\n预期 SenseVoiceSmall 路径:\n  {expected_model_dir}")
    logger.info(f"  存在: {expected_model_dir.exists()}")
    
    logger.info(f"\n预期 VAD 模型路径:\n  {expected_vad_dir}")
    logger.info(f"  存在: {expected_vad_dir.exists()}")
    
    # 检查是否存在旧的错误路径
    old_model_dir = project_root / "server" / "models" / "models" / "iic" / "SenseVoiceSmall"
    old_vad_dir = project_root / "server" / "models" / "models" / "iic" / "speech_fsmn_vad_zh-cn-16k-common-pytorch"
    
    if old_model_dir.exists():
        logger.warning(f"\n⚠️ 发现旧的 SenseVoiceSmall 路径:\n  {old_model_dir}")
        logger.warning("  建议删除或移动到正确位置")
    
    if old_vad_dir.exists():
        logger.warning(f"\n⚠️ 发现旧的 VAD 路径:\n  {old_vad_dir}")
        logger.warning("  建议删除或移动到正确位置")
    
    return expected_model_dir, expected_vad_dir


def test_sensevoice_config():
    """测试 SenseVoice 配置"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 SenseVoice 配置模块")
    logger.info("=" * 60)
    
    try:
        from server.modules.ast.sensevoice_service import SenseVoiceService
        
        logger.info("\n✅ SenseVoice 模块导入成功")
        
        # 创建服务实例（不初始化）
        service = SenseVoiceService()
        logger.info(f"✅ SenseVoice 服务实例创建成功")
        logger.info(f"  配置: model_id={service.config.model_id}")
        
        return True
    except Exception as e:
        logger.error(f"\n❌ SenseVoice 配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bootstrap_paths():
    """测试 bootstrap 模块的路径配置"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 Bootstrap 模块路径配置")
    logger.info("=" * 60)
    
    try:
        from server.utils.bootstrap import ensure_models
        
        logger.info("\n✅ Bootstrap 模块导入成功")
        
        # 检查模型（不下载）
        result = ensure_models()
        logger.info(f"  模型检查结果: {result}")
        
        if result.get("model"):
            logger.info("  ✅ SenseVoiceSmall 模型已存在")
        else:
            logger.warning("  ⚠️ SenseVoiceSmall 模型未找到（需要下载）")
        
        if result.get("vad"):
            logger.info("  ✅ VAD 模型已存在")
        else:
            logger.warning("  ⚠️ VAD 模型未找到（需要下载）")
        
        return True
    except Exception as e:
        logger.error(f"\n❌ Bootstrap 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_path_resolution():
    """测试路径解析逻辑"""
    logger.info("\n" + "=" * 60)
    logger.info("测试路径解析逻辑")
    logger.info("=" * 60)
    
    # 测试 sensevoice_service.py 的路径计算
    service_file = project_root / "server" / "modules" / "ast" / "sensevoice_service.py"
    logger.info(f"\nSenseVoice 服务文件: {service_file}")
    logger.info(f"  存在: {service_file.exists()}")
    
    # 模拟路径计算
    if service_file.exists():
        # Path(__file__).resolve().parents[2] 应该指向 server/
        service_root = service_file.resolve().parents[2]
        logger.info(f"\n路径计算测试 (parents[2]):")
        logger.info(f"  计算结果: {service_root}")
        logger.info(f"  预期: {project_root / 'server'}")
        
        if service_root == project_root / "server":
            logger.info("  ✅ 路径计算正确")
            
            # 测试完整路径
            cache_vad = service_root / "modules" / "models" / ".cache" / "models" / "iic" / "speech_fsmn_vad_zh-cn-16k-common-pytorch"
            logger.info(f"\n计算的 VAD 路径:")
            logger.info(f"  {cache_vad}")
            logger.info(f"  存在: {cache_vad.exists()}")
            
            return True
        else:
            logger.error("  ❌ 路径计算错误")
            return False
    else:
        logger.warning("  ⚠️ SenseVoice 服务文件不存在")
        return False


def main():
    """主测试函数"""
    logger.info("\n" + "🔧" * 30)
    logger.info("SenseVoice 模型路径修复验证测试")
    logger.info("🔧" * 30)
    
    results = []
    
    # 测试 1: 检查路径
    logger.info("\n[测试 1/4] 检查模型路径")
    test_model_paths()
    
    # 测试 2: 路径解析
    logger.info("\n[测试 2/4] 验证路径解析逻辑")
    results.append(("路径解析", test_path_resolution()))
    
    # 测试 3: SenseVoice 配置
    logger.info("\n[测试 3/4] 测试 SenseVoice 配置")
    results.append(("SenseVoice 配置", test_sensevoice_config()))
    
    # 测试 4: Bootstrap 路径
    logger.info("\n[测试 4/4] 测试 Bootstrap 路径")
    results.append(("Bootstrap 路径", test_bootstrap_paths()))
    
    # 汇总结果
    logger.info("\n" + "=" * 60)
    logger.info("测试结果汇总")
    logger.info("=" * 60)
    
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        logger.info(f"  {test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    logger.info("\n" + "=" * 60)
    if all_passed:
        logger.info("✅ 所有测试通过！模型路径配置正确。")
        logger.info("=" * 60)
        return 0
    else:
        logger.error("❌ 部分测试失败！请检查上述错误信息。")
        logger.info("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())

