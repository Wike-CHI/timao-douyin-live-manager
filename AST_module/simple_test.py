#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的SenseVoice服务测试脚本
用于验证导入错误修复是否成功
"""

import sys
import os
import asyncio
import logging

# 添加上级目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        
        # 检查是否使用了模拟服务
        if "缺少以下依赖包" in str(model_info) or not model_info.get("initialized", False):
            logger.info("✅ 正确使用了模拟服务（因为缺少依赖包）")
        else:
            logger.info("✅ 使用了真实SenseVoice模型")
        
        # 清理服务
        await service.cleanup()
        logger.info("✅ SenseVoice服务清理成功")
        
        return True
        
    except Exception as e:
        logger.error(f"SenseVoice服务测试失败: {e}")
        return False

if __name__ == "__main__":
    logger.info("开始简单的SenseVoice服务测试")
    result = asyncio.run(test_sensevoice_service())
    if result:
        logger.info("✅ 测试通过")
    else:
        logger.error("❌ 测试失败")
    sys.exit(0 if result else 1)