#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
讯飞ASR测试脚本
快速测试语音识别功能
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from loguru import logger

from server.app.services.xfyun_asr import XfyunASR
from server.app.utils.audio_converter import AudioConverter


async def test_asr():
    """测试讯飞ASR"""
    
    # 加载环境变量
    load_dotenv("server/.env")
    
    # 读取配置
    app_id = os.getenv("XFYUN_APPID", "3f3b2c39")
    api_key = os.getenv("XFYUN_API_KEY", "4cb3fb678a09e3072fb8889d840ef6a2")
    api_secret = os.getenv("XFYUN_API_SECRET", "MTg2ZTFlZjJlYWYyYzVjZWJhMmIyYzUz")
    
    logger.info("=" * 60)
    logger.info("讯飞语音识别测试")
    logger.info("=" * 60)
    logger.info(f"APPID: {app_id}")
    logger.info(f"API Key: {api_key[:8]}...")
    logger.info("")
    
    # 初始化ASR
    asr = XfyunASR(app_id, api_key, api_secret)
    
    # 查找测试音频
    test_audio_dirs = [
        "records/sessions",
        "data/test",
        "."
    ]
    
    test_audio = None
    for dir_path in test_audio_dirs:
        if os.path.exists(dir_path):
            # 查找音频文件
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    if file.endswith((".mp3", ".wav", ".m4a", ".mp4")):
                        test_audio = os.path.join(root, file)
                        break
                if test_audio:
                    break
        if test_audio:
            break
    
    if not test_audio:
        logger.warning("未找到测试音频文件")
        logger.info("请提供音频文件路径:")
        logger.info("  python test_xfyun_asr.py <audio_file>")
        logger.info("")
        logger.info("支持格式: mp3, wav, m4a, mp4")
        return
    
    # 如果命令行提供了文件
    if len(sys.argv) > 1:
        test_audio = sys.argv[1]
    
    logger.info(f"测试音频: {test_audio}")
    
    # 获取音频信息
    converter = AudioConverter()
    audio_info = converter.get_audio_info(test_audio)
    
    if audio_info:
        logger.info(f"音频时长: {audio_info['duration']:.2f}秒")
        logger.info(f"采样率: {audio_info['sample_rate']}Hz")
        logger.info(f"声道数: {audio_info['channels']}")
        logger.info(f"编码: {audio_info['codec']}")
        logger.info(f"文件大小: {audio_info['size'] / 1024 / 1024:.2f}MB")
        logger.info("")
    
    # 转换为PCM格式
    logger.info("步骤1: 转换音频格式...")
    try:
        pcm_file = converter.convert_to_pcm(test_audio)
        logger.info(f"✓ 转换成功: {pcm_file}")
    except Exception as e:
        logger.error(f"✗ 转换失败: {e}")
        return
    
    # 调用ASR
    logger.info("")
    logger.info("步骤2: 调用讯飞ASR...")
    try:
        result = await asr.transcribe_audio_file(pcm_file)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("转写结果:")
        logger.info("=" * 60)
        if result:
            logger.info(result)
            logger.info("")
            logger.info(f"✓ 转写成功！共 {len(result)} 字")
        else:
            logger.warning("✗ 转写结果为空")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"✗ 转写失败: {e}", exc_info=True)
    
    # 清理临时文件
    if os.path.exists(pcm_file):
        os.remove(pcm_file)
        logger.info(f"已清理临时文件: {pcm_file}")


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # 运行测试
    asyncio.run(test_asr())

