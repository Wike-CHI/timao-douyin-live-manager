#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试集成后的讯飞ASR服务
"""

import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv("server/.env")

# 导入集成后的服务
from server.modules.ast.iflytek_asr_adapter import IFlyTekASRService

logging.basicConfig(
    level=logging.DEBUG,  # 改为DEBUG级别
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

async def test_xfyun_service():
    """测试讯飞ASR服务"""
    logger = logging.getLogger(__name__)
    
    # 1. 初始化服务（自动从环境变量读取配置）
    logger.info("=" * 60)
    logger.info("测试讯飞ASR服务")
    logger.info("=" * 60)
    
    service = IFlyTekASRService()
    
    # 2. 初始化
    logger.info("\n[1] 初始化服务...")
    success = await service.initialize()
    if not success:
        logger.error("❌ 服务初始化失败")
        return
    logger.info("✅ 服务初始化成功")
    
    # 3. 查找测试音频文件
    logger.info("\n[2] 查找测试音频文件...")
    test_file = "records/sessions/live_douyin_小桃🎤_20251109_1762647197/小桃🎤_20251109_081317_009.mp4"
    if not Path(test_file).exists():
        logger.error(f"❌ 测试文件不存在: {test_file}")
        return
    logger.info(f"✅ 找到测试文件: {test_file}")
    
    # 4. 转写文件
    logger.info("\n[3] 开始转写...")
    result = await service.transcribe_file(test_file)
    
    # 5. 输出结果
    logger.info("\n[4] 转写结果:")
    logger.info("=" * 60)
    if result.get("success"):
        logger.info(f"✅ 转写成功")
        logger.info(f"文本: {result['text']}")
        logger.info(f"置信度: {result['confidence']}")
    else:
        logger.error(f"❌ 转写失败: {result.get('error', '未知错误')}")
    logger.info("=" * 60)
    
    # 6. 清理
    logger.info("\n[5] 清理资源...")
    await service.cleanup()
    logger.info("✅ 资源已清理")
    logger.info("\n测试完成！\n")

if __name__ == "__main__":
    asyncio.run(test_xfyun_service())

