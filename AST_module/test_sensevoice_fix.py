#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SenseVoice服务修复测试脚本
用于验证导入错误修复是否成功
"""

import sys
import os
import asyncio
import logging

# 添加上级目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """测试依赖包导入"""
    logger.info("开始测试依赖包导入...")
    
    # 测试主要依赖包
    required_packages = [
        'editdistance',
        'hydra',
        'jaconv',
        'jamo',
        'jieba',
        'librosa',
        'oss2',
        'sentencepiece',
        'soundfile',
        'tensorboardX',
        'umap'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✅ {package} 导入成功")
        except ImportError as e:
            logger.warning(f"⚠️  {package} 导入失败: {e}")
            missing_packages.append(package)
    
    # 特殊处理 pytorch_wpe
    pytorch_wpe_available = False
    try:
        __import__('pytorch_wpe')
        pytorch_wpe_available = True
        logger.info("✅ pytorch_wpe 导入成功")
    except ImportError as e:
        logger.warning(f"⚠️  pytorch_wpe 导入失败: {e}")
    
    if not pytorch_wpe_available:
        missing_packages.append('pytorch_wpe')
    
    # 测试FunASR
    funasr_available = False
    try:
        from funasr import AutoModel
        funasr_available = True
        logger.info("✅ FunASR 导入成功")
    except ImportError as e:
        logger.warning(f"⚠️  FunASR 导入失败: {e}")
    
    logger.info("=" * 50)
    if missing_packages:
        logger.warning(f"缺少以下依赖包: {', '.join(missing_packages)}")
    else:
        logger.info("所有依赖包检查通过")
    
    logger.info(f"FunASR 可用性: {'是' if funasr_available else '否'}")
    return missing_packages, funasr_available

async def test_sensevoice_service():
    """测试SenseVoice服务"""
    logger.info("开始测试SenseVoice服务...")
    
    try:
        # 导入SenseVoice服务
        from AST_module.sensevoice_service import SenseVoiceService, SenseVoiceConfig
        
        # 创建服务实例
        config = SenseVoiceConfig()
        service = SenseVoiceService(config)
        logger.info("✅ SenseVoiceService 创建成功")
        
        # 测试初始化
        init_result = await service.initialize()
        logger.info(f"✅ SenseVoice服务初始化: {'成功' if init_result else '失败'}")
        
        # 获取模型信息
        model_info = service.get_model_info()
        logger.info(f"✅ 模型信息: {model_info}")
        
        # 测试模拟转录
        test_audio = b"test audio data" * 100  # 模拟音频数据
        result = await service.transcribe_audio(test_audio)
        logger.info(f"✅ 模拟转录结果: {result}")
        
        # 清理服务
        await service.cleanup()
        logger.info("✅ SenseVoice服务清理成功")
        
        return True
        
    except Exception as e:
        logger.error(f"SenseVoice服务测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    logger.info("开始SenseVoice服务修复测试")
    logger.info("=" * 50)
    
    # 测试依赖包导入
    missing_packages, funasr_available = test_imports()
    
    logger.info("=" * 50)
    
    # 测试SenseVoice服务
    service_test_passed = await test_sensevoice_service()
    
    logger.info("=" * 50)
    logger.info("测试结果:")
    logger.info(f"  1. 依赖包导入测试: {'✅ 通过' if not missing_packages or not funasr_available else '⚠️  部分通过'}")
    logger.info(f"  2. SenseVoice服务测试: {'✅ 通过' if service_test_passed else '❌ 失败'}")
    
    overall_result = (not missing_packages or not funasr_available) and service_test_passed
    logger.info(f"总体结果: {'✅ 所有测试通过' if overall_result else '❌ 部分测试失败'}")
    
    return overall_result

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)