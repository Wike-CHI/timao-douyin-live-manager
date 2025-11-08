#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试科大讯飞ASR配置

快速验证科大讯飞ASR是否配置正确
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from server.modules.ast.iflytek_asr_adapter import IFlyTekASRService, IFlyTekConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_iflytek_config():
    """测试科大讯飞配置"""
    logger.info("=" * 80)
    logger.info("测试科大讯飞ASR配置")
    logger.info("=" * 80)
    
    # 从环境变量读取配置
    app_id = os.getenv("IFLYTEK_APP_ID", "")
    api_key = os.getenv("IFLYTEK_API_KEY", "")
    api_secret = os.getenv("IFLYTEK_API_SECRET", "")
    
    if not app_id:
        logger.error("❌ 缺少 IFLYTEK_APP_ID 环境变量")
        logger.info("请设置: export IFLYTEK_APP_ID=你的APP_ID")
        return False
    
    if not api_key:
        logger.error("❌ 缺少 IFLYTEK_API_KEY 环境变量")
        logger.info("请设置: export IFLYTEK_API_KEY=你的API_KEY")
        return False
    
    if not api_secret:
        logger.error("❌ 缺少 IFLYTEK_API_SECRET 环境变量")
        logger.info("请设置: export IFLYTEK_API_SECRET=你的API_SECRET")
        return False
    
    logger.info(f"✅ APP_ID: {app_id[:8]}...")
    logger.info(f"✅ API_KEY: {api_key[:8]}...")
    logger.info(f"✅ API_SECRET: {api_secret[:8]}...")
    
    # 创建服务
    config = IFlyTekConfig(
        app_id=app_id,
        api_key=api_key,
        api_secret=api_secret
    )
    
    service = IFlyTekASRService(config)
    
    # 测试初始化
    logger.info("\n正在测试连接...")
    success = await service.initialize()
    
    if not success:
        logger.error("❌ 科大讯飞ASR初始化失败")
        logger.error("请检查:")
        logger.error("1. 凭证是否正确")
        logger.error("2. 网络连接是否正常")
        logger.error("3. 是否开通了实时语音识别服务")
        return False
    
    logger.info("✅ 科大讯飞ASR初始化成功")
    
    # 测试转录
    logger.info("\n正在测试转录...")
    # 生成1秒的静音音频
    sample_rate = 16000
    audio_data = bytes([0] * (sample_rate * 2))  # 16bit
    
    result = await service.transcribe_audio(audio_data, session_id="test")
    
    logger.info(f"转录结果: {result}")
    
    if result.get("success"):
        logger.info("✅ 转录测试成功")
    else:
        logger.error(f"❌ 转录测试失败: {result.get('error')}")
        return False
    
    # 清理
    await service.cleanup()
    
    logger.info("\n" + "=" * 80)
    logger.info("🎉 所有测试通过！科大讯飞ASR配置正确")
    logger.info("=" * 80)
    logger.info("\n下一步:")
    logger.info("1. 在 .env 文件中添加: USE_IFLYTEK_ASR=1")
    logger.info("2. 重启服务: pm2 restart backend")
    logger.info("3. 查看日志: pm2 logs backend")
    logger.info("")
    
    return True


async def test_real_audio():
    """测试真实音频（如果有）"""
    logger.info("\n" + "=" * 80)
    logger.info("测试真实音频识别（需要录音设备）")
    logger.info("=" * 80)
    
    try:
        import pyaudio
    except ImportError:
        logger.warning("⚠️ pyaudio未安装，跳过真实音频测试")
        return True
    
    # 读取配置
    config = IFlyTekConfig(
        app_id=os.getenv("IFLYTEK_APP_ID", ""),
        api_key=os.getenv("IFLYTEK_API_KEY", ""),
        api_secret=os.getenv("IFLYTEK_API_SECRET", "")
    )
    
    service = IFlyTekASRService(config)
    await service.initialize()
    
    # 录音
    logger.info("正在录音5秒，请说话...")
    
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=1024
    )
    
    frames = []
    for i in range(0, int(16000 / 1024 * 5)):  # 5秒
        data = stream.read(1024)
        frames.append(data)
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    audio_data = b''.join(frames)
    logger.info(f"录音完成，音频长度: {len(audio_data)}字节")
    
    # 转录
    logger.info("正在转录...")
    result = await service.transcribe_audio(audio_data, session_id="test_real")
    
    logger.info(f"识别结果: {result.get('text', '')}")
    logger.info(f"置信度: {result.get('confidence', 0)}")
    
    await service.cleanup()
    
    return True


async def main():
    """运行所有测试"""
    logger.info("🚀 科大讯飞ASR配置测试\n")
    
    # 测试1: 配置和连接
    result1 = await test_iflytek_config()
    
    if not result1:
        logger.error("\n❌ 配置测试失败，请检查配置后重试")
        return 1
    
    # 测试2: 真实音频（可选）
    try:
        user_input = input("\n是否测试真实音频识别？(需要麦克风) [y/N]: ")
        if user_input.lower() == 'y':
            await test_real_audio()
    except KeyboardInterrupt:
        logger.info("\n测试被中断")
    except Exception as e:
        logger.error(f"真实音频测试失败: {e}")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

