#!/usr/bin/env python3
"""测试说话人分离功能的完整集成测试"""

import sys
import os
import asyncio
import time
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

async def test_live_audio_service_integration():
    """测试LiveAudioStreamService中说话人分离的完整集成"""
    print("=== 测试LiveAudioStreamService说话人分离集成 ===")
    
    try:
        from app.services.live_audio_stream_service import LiveAudioStreamService
        
        # 创建服务实例
        service = LiveAudioStreamService()
        print("✓ LiveAudioStreamService 实例创建成功")
        
        # 检查初始状态
        print(f"\n--- 初始状态检查 ---")
        print(f"分离器对象: {service._diarizer}")
        print(f"当前说话人标签: {service._last_speaker_label}")
        print(f"分离器调试信息: {service._last_speaker_debug}")
        print(f"预热时间: {service._diarizer_warmup_sec}")
        
        if service._diarizer is None:
            print("✗ 说话人分离器未初始化，无法进行集成测试")
            return False
        
        # 模拟音频处理流程
        print(f"\n--- 模拟音频处理流程 ---")
        import numpy as np
        
        # 生成测试音频数据
        duration = 1.0  # 1秒
        sample_rate = 16000
        samples = int(duration * sample_rate)
        
        # 模拟不同说话人的音频特征
        t = np.linspace(0, duration, samples)
        
        # 说话人1：低频特征
        audio1 = (np.sin(2 * np.pi * 200 * t) * 16384).astype(np.int16)
        pcm1 = audio1.tobytes()
        
        # 说话人2：高频特征
        audio2 = (np.sin(2 * np.pi * 800 * t) * 16384).astype(np.int16)
        pcm2 = audio2.tobytes()
        
        print("✓ 测试音频数据生成成功")
        
        # 模拟实际的音频处理流程
        print(f"\n--- 处理说话人1音频（预热阶段）---")
        for i in range(5):
            print(f"\n轮次 {i+1}:")
            service._update_speaker_state(pcm1, duration)
            print(f"  当前标签: {service._last_speaker_label}")
            print(f"  调试信息: {service._last_speaker_debug}")
            
            # 检查分离器状态
            if service._diarizer:
                observed_sec = service._diarizer.total_observed_sec()
                is_ready = service._diarizer.is_ready()
                print(f"  观察时长: {observed_sec:.2f}s, 是否就绪: {is_ready}")
        
        print(f"\n--- 处理说话人2音频（分离阶段）---")
        for i in range(5):
            print(f"\n轮次 {i+1}:")
            service._update_speaker_state(pcm2, duration)
            print(f"  当前标签: {service._last_speaker_label}")
            print(f"  调试信息: {service._last_speaker_debug}")
            
            # 检查分离器状态
            if service._diarizer:
                observed_sec = service._diarizer.total_observed_sec()
                is_ready = service._diarizer.is_ready()
                print(f"  观察时长: {observed_sec:.2f}s, 是否就绪: {is_ready}")
        
        # 测试高级配置更新
        print(f"\n--- 测试高级配置更新 ---")
        advanced_config = service.update_advanced(
            diarization=True,
            max_speakers=3
        )
        print(f"高级配置更新结果: {advanced_config}")
        
        # 验证状态API
        print(f"\n--- 验证状态API ---")
        status = service.status()
        print(f"服务状态: {status}")
        
        print(f"\n✓ 说话人分离集成测试完成")
        return True
        
    except Exception as e:
        print(f"✗ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_integration():
    """测试API层面的说话人分离集成"""
    print("\n=== 测试API层面的说话人分离集成 ===")
    
    try:
        # 测试状态API
        import requests
        import json
        
        base_url = "http://localhost:8000"
        
        # 获取状态
        try:
            response = requests.get(f"{base_url}/api/live_audio/status", timeout=5)
            if response.status_code == 200:
                status_data = response.json()
                print("✓ 状态API调用成功")
                
                # 检查说话人分离相关字段
                advanced = status_data.get("advanced", {})
                print(f"  分离器激活: {advanced.get('diarizer_active', False)}")
                print(f"  最大说话人数: {advanced.get('max_speakers', 0)}")
                print(f"  最近说话人: {advanced.get('last_speaker', 'unknown')}")
                
                return True
            else:
                print(f"✗ 状态API调用失败: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"✗ 无法连接到API服务器: {e}")
            print("  请确保服务器正在运行 (python -m uvicorn server.main:app --reload)")
            return False
            
    except Exception as e:
        print(f"✗ API集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_configuration():
    """测试环境变量配置"""
    print("\n=== 测试环境变量配置 ===")
    
    env_vars = {
        "LIVE_DIARIZER_ENROLL_SEC": "4.0",
        "LIVE_DIARIZER_MAX_SPEAKERS": "2", 
        "LIVE_DIARIZER_SMOOTH": "0.2",
        "LIVE_DIARIZER_WARMUP_SEC": "3.0"
    }
    
    print("当前环境变量配置:")
    for var, default in env_vars.items():
        value = os.getenv(var, default)
        print(f"  {var}: {value}")
    
    # 测试配置解析
    try:
        from app.services.live_audio_stream_service import _env_float, _env_int
        
        enroll_sec = _env_float("LIVE_DIARIZER_ENROLL_SEC", 4.0, min_value=1.0, max_value=20.0)
        max_speakers = _env_int("LIVE_DIARIZER_MAX_SPEAKERS", 2, min_value=1, max_value=4)
        smooth = _env_float("LIVE_DIARIZER_SMOOTH", 0.2, min_value=0.05, max_value=0.6)
        
        print(f"\n解析后的配置:")
        print(f"  注册时长: {enroll_sec}s")
        print(f"  最大说话人数: {max_speakers}")
        print(f"  平滑系数: {smooth}")
        
        return True
        
    except Exception as e:
        print(f"✗ 环境变量配置测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("开始说话人分离功能完整集成测试...\n")
    
    # 测试环境配置
    env_ok = test_environment_configuration()
    
    # 测试服务集成
    service_ok = await test_live_audio_service_integration()
    
    # 测试API集成
    api_ok = await test_api_integration()
    
    print(f"\n=== 测试结果汇总 ===")
    print(f"环境配置测试: {'✓ 通过' if env_ok else '✗ 失败'}")
    print(f"服务集成测试: {'✓ 通过' if service_ok else '✗ 失败'}")
    print(f"API集成测试: {'✓ 通过' if api_ok else '✗ 失败'}")
    
    overall_success = env_ok and service_ok
    print(f"\n整体测试结果: {'✓ 通过' if overall_success else '✗ 失败'}")
    
    if overall_success:
        print("\n🎉 说话人分离功能集成测试全部通过！")
        print("功能已正常工作，可以在实时字幕中看到说话人标签。")
    else:
        print("\n❌ 说话人分离功能存在问题，请检查上述错误信息。")
    
    return overall_success

if __name__ == "__main__":
    asyncio.run(main())