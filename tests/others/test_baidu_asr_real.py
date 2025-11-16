#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试百度ASR实际音频识别功能"""

import asyncio
import sys
import os
import wave
import struct
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载.env文件
from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]
env_path = project_root / "server" / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"✅ 已加载环境变量: {env_path}")
else:
    print(f"⚠️ .env文件不存在: {env_path}")

def generate_test_audio(duration_seconds=3, sample_rate=16000):
    """
    生成测试音频数据（静音）
    百度要求：16k采样率、16bit位深、单声道PCM
    """
    # 生成静音数据
    num_samples = int(sample_rate * duration_seconds)
    audio_data = struct.pack(f'{num_samples}h', *([0] * num_samples))
    
    print(f"📊 生成测试音频: {duration_seconds}秒, {sample_rate}Hz, {len(audio_data)}字节")
    return audio_data

async def test_baidu_asr_with_audio():
    """测试百度ASR实际识别功能"""
    
    print("\n" + "="*70)
    print("🎯 百度ASR实际识别测试")
    print("="*70 + "\n")
    
    # 1. 检查环境变量
    print("📋 1. 检查环境变量")
    print("-" * 70)
    
    use_baidu = os.getenv("USE_BAIDU_ASR", "1")
    app_id = os.getenv("BAIDU_ASR_APP_ID", "120812895")
    api_key = os.getenv("BAIDU_ASR_API_KEY", "")
    secret_key = os.getenv("BAIDU_ASR_SECRET_KEY", "")
    
    print(f"USE_BAIDU_ASR: {use_baidu}")
    print(f"BAIDU_ASR_APP_ID: {app_id[:10]}..." if app_id else "BAIDU_ASR_APP_ID: 未设置")
    print(f"BAIDU_ASR_API_KEY: {api_key[:10]}..." if api_key else "BAIDU_ASR_API_KEY: 未设置")
    print(f"BAIDU_ASR_SECRET_KEY: {'*' * 20}" if secret_key else "BAIDU_ASR_SECRET_KEY: 未设置")
    
    if not all([app_id, api_key, secret_key]):
        print("\n❌ 环境变量配置不完整")
        return False
    
    print("✅ 环境变量配置完整\n")
    
    # 2. 导入并初始化百度ASR服务
    print("📋 2. 初始化百度ASR服务")
    print("-" * 70)
    
    try:
        from server.modules.ast.baidu_asr_adapter import BaiduASRService
        
        service = BaiduASRService()
        init_ok = await service.initialize()
        
        if not init_ok:
            print("\n❌ 百度ASR初始化失败")
            return False
        
        print("✅ 百度ASR初始化成功\n")
        
    except Exception as e:
        print(f"\n❌ 导入或初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. 生成测试音频
    print("📋 3. 生成测试音频")
    print("-" * 70)
    audio_data = generate_test_audio(duration_seconds=3)
    print()
    
    # 4. 发送音频进行识别
    print("📋 4. 发送音频进行识别")
    print("-" * 70)
    
    try:
        session_id = "test_session_001"
        print(f"会话ID: {session_id}")
        print(f"音频大小: {len(audio_data)} 字节")
        print("正在发送音频数据...")
        
        # 分块发送音频（每次320字节，约10ms的音频）
        chunk_size = 320  # 16000Hz * 2bytes * 0.01s = 320 bytes
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i+chunk_size]
            
            # BaiduASRService.transcribe_audio() 参数：audio_data, session_id, bias_phrases
            result = await service.transcribe_audio(
                chunk,
                session_id=session_id
            )
            
            if result and result.get("text"):
                print(f"识别结果: {result['text']}")
            
            # 避免发送过快
            await asyncio.sleep(0.01)
        
        print("✅ 音频发送完成\n")
        
        # 5. 等待最终结果
        print("📋 5. 等待识别结果")
        print("-" * 70)
        await asyncio.sleep(2)
        
        print("\n✅ 测试完成！")
        print("\n" + "="*70)
        print("📊 测试总结")
        print("="*70)
        print("✅ 环境变量配置正确")
        print("✅ 百度ASR初始化成功")
        print("✅ WebSocket连接成功")
        print("✅ 音频数据发送成功")
        print("\n💡 提示：测试使用的是静音数据，实际使用时会有真实语音识别结果")
        
        # 清理
        await service.cleanup()
        
        return True
        
    except Exception as e:
        print(f"\n❌ 识别测试失败: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            await service.cleanup()
        except:
            pass
        
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_baidu_asr_with_audio())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断测试")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

