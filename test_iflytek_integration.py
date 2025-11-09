#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
讯飞ASR集成测试
验证讯飞ASR在项目中的完整集成
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from loguru import logger

# 加载环境变量
load_dotenv("server/.env")

# 导入项目中的讯飞服务
try:
    from server.modules.ast.iflytek_asr_adapter import (
        IFlyTekASRService,
        IFlyTekConfig,
    )
    IFLYTEK_AVAILABLE = True
except ImportError as e:
    logger.error(f"❌ 导入讯飞ASR服务失败: {e}")
    IFLYTEK_AVAILABLE = False
    sys.exit(1)


async def test_iflytek_service():
    """测试讯飞ASR服务"""
    
    logger.info("=" * 60)
    logger.info("讯飞ASR集成测试")
    logger.info("=" * 60)
    
    # 1. 检查环境变量
    logger.info("步骤1: 检查环境变量...")
    app_id = os.getenv("XFYUN_APPID")
    api_key = os.getenv("XFYUN_API_KEY")
    api_secret = os.getenv("XFYUN_API_SECRET")
    use_iflytek = os.getenv("USE_IFLYTEK_ASR")
    
    if not app_id or not api_key or not api_secret:
        logger.error("❌ 讯飞配置缺失")
        logger.error("   需要设置: XFYUN_APPID, XFYUN_API_KEY, XFYUN_API_SECRET")
        return False
    
    logger.info(f"✓ XFYUN_APPID: {app_id}")
    logger.info(f"✓ XFYUN_API_KEY: {api_key[:8]}...")
    logger.info(f"✓ USE_IFLYTEK_ASR: {use_iflytek}")
    logger.info("")
    
    # 2. 初始化服务
    logger.info("步骤2: 初始化讯飞ASR服务...")
    try:
        service = IFlyTekASRService()
        success = await service.initialize()
        
        if not success:
            logger.error("❌ 服务初始化失败")
            return False
        
        logger.info("✓ 服务初始化成功")
        logger.info("")
        
    except Exception as e:
        logger.error(f"❌ 初始化异常: {e}", exc_info=True)
        return False
    
    # 3. 测试转写
    logger.info("步骤3: 测试音频转写...")
    
    # 查找测试音频
    test_audio_dirs = [
        ".",  # 当前目录
        "records/sessions",
        "data/test",
    ]
    
    test_pcm = None
    for dir_path in test_audio_dirs:
        if os.path.exists(dir_path):
            # 查找PCM文件
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    if file.endswith(".pcm"):
                        test_pcm = os.path.join(root, file)
                        break
                if test_pcm:
                    break
        if test_pcm:
            break
    
    if not test_pcm:
        logger.warning("⚠ 未找到测试PCM文件，跳过转写测试")
        logger.info("提示：可以先运行 test_xfyun_asr.py 生成PCM文件")
        logger.info("")
    else:
        logger.info(f"测试PCM: {test_pcm}")
        
        try:
            with open(test_pcm, 'rb') as f:
                audio_data = f.read()
            
            logger.info(f"音频大小: {len(audio_data) / 1024:.2f}KB")
            
            # 调用转写
            result = await service.transcribe_audio(audio_data, session_id="test_session")
            
            if result.get("success"):
                text = result.get("text", "")
                logger.info("")
                logger.info("=" * 60)
                logger.info("转写结果:")
                logger.info("=" * 60)
                logger.info(text)
                logger.info("=" * 60)
                logger.info(f"✓ 转写成功！共 {len(text)} 字")
                logger.info("")
            else:
                logger.error("❌ 转写失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 转写异常: {e}", exc_info=True)
            return False
    
    # 4. 清理
    logger.info("步骤4: 清理会话...")
    try:
        await service.close_session("test_session")
        logger.info("✓ 会话已关闭")
        logger.info("")
    except Exception as e:
        logger.warning(f"⚠ 清理异常: {e}")
    
    logger.info("=" * 60)
    logger.info("✅ 讯飞ASR集成测试通过！")
    logger.info("=" * 60)
    
    return True


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # 运行测试
    success = asyncio.run(test_iflytek_service())
    
    if not success:
        sys.exit(1)

