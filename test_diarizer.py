#!/usr/bin/env python3
"""测试说话人分离功能"""

import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

def test_diarizer_import():
    """测试说话人分离器的导入"""
    print("=== 测试说话人分离器导入 ===")
    
    try:
        from app.services.online_diarizer import OnlineDiarizer
        print("✓ OnlineDiarizer 直接导入成功")
        
        # 测试初始化
        diarizer = OnlineDiarizer(sr=16000, max_speakers=2, enroll_sec=4.0, smooth=0.2)
        print("✓ OnlineDiarizer 初始化成功")
        print(f"  - 采样率: {diarizer.sr}")
        print(f"  - 最大说话人数: {diarizer.max_speakers}")
        print(f"  - 注册时长: {diarizer.enroll_sec}")
        print(f"  - 平滑系数: {diarizer.smooth}")
        
        return diarizer
        
    except Exception as e:
        print(f"✗ OnlineDiarizer 导入或初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_live_audio_service_diarizer():
    """测试 LiveAudioStreamService 中的说话人分离器"""
    print("\n=== 测试 LiveAudioStreamService 中的说话人分离器 ===")
    
    try:
        from app.services.live_audio_stream_service import LiveAudioStreamService, OnlineDiarizer
        print(f"✓ LiveAudioStreamService 导入成功")
        print(f"✓ OnlineDiarizer 从 live_audio_stream_service 导入: {OnlineDiarizer}")
        
        # 创建服务实例
        service = LiveAudioStreamService()
        print("✓ LiveAudioStreamService 实例创建成功")
        
        # 检查分离器状态
        print(f"  - 分离器对象: {service._diarizer}")
        print(f"  - 当前说话人标签: {service._last_speaker_label}")
        print(f"  - 分离器调试信息: {service._last_speaker_debug}")
        print(f"  - 预热时间: {service._diarizer_warmup_sec}")
        
        if service._diarizer is not None:
            print("✓ 说话人分离器已成功初始化")
            print(f"  - 分离器类型: {type(service._diarizer)}")
            print(f"  - 观察时长: {service._diarizer.total_observed_sec()}")
            print(f"  - 是否就绪: {service._diarizer.is_ready()}")
        else:
            print("✗ 说话人分离器未初始化")
            
        return service
        
    except Exception as e:
        print(f"✗ LiveAudioStreamService 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_diarizer_functionality(diarizer):
    """测试说话人分离器的基本功能"""
    print("\n=== 测试说话人分离器功能 ===")
    
    if diarizer is None:
        print("✗ 分离器为空，跳过功能测试")
        return
    
    try:
        import numpy as np
        
        # 生成测试音频数据（模拟16kHz, 16bit PCM）
        duration = 1.0  # 1秒
        sample_rate = 16000
        samples = int(duration * sample_rate)
        
        # 生成两种不同的音频信号（模拟不同说话人）
        t = np.linspace(0, duration, samples)
        
        # 说话人1：低频信号
        audio1 = (np.sin(2 * np.pi * 200 * t) * 16384).astype(np.int16)
        pcm1 = audio1.tobytes()
        
        # 说话人2：高频信号
        audio2 = (np.sin(2 * np.pi * 800 * t) * 16384).astype(np.int16)
        pcm2 = audio2.tobytes()
        
        print("✓ 测试音频数据生成成功")
        
        # 测试分离器处理
        print("\n--- 处理说话人1音频 ---")
        for i in range(3):
            label1, debug1 = diarizer.feed(pcm1, duration)
            print(f"  轮次 {i+1}: 标签={label1}, 调试信息={debug1}")
        
        print("\n--- 处理说话人2音频 ---")
        for i in range(3):
            label2, debug2 = diarizer.feed(pcm2, duration)
            print(f"  轮次 {i+1}: 标签={label2}, 调试信息={debug2}")
        
        print(f"\n✓ 分离器功能测试完成")
        print(f"  - 总观察时长: {diarizer.total_observed_sec():.2f}秒")
        print(f"  - 是否就绪: {diarizer.is_ready()}")
        
    except Exception as e:
        print(f"✗ 分离器功能测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_environment_variables():
    """测试环境变量配置"""
    print("\n=== 测试环境变量配置 ===")
    
    env_vars = [
        "LIVE_DIARIZER_ENROLL_SEC",
        "LIVE_DIARIZER_MAX_SPEAKERS", 
        "LIVE_DIARIZER_SMOOTH",
        "LIVE_DIARIZER_WARMUP_SEC"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        print(f"  {var}: {value if value else '未设置（使用默认值）'}")

def main():
    """主测试函数"""
    print("开始测试说话人分离功能...\n")
    
    # 测试环境变量
    test_environment_variables()
    
    # 测试直接导入
    diarizer = test_diarizer_import()
    
    # 测试服务中的分离器
    service = test_live_audio_service_diarizer()
    
    # 测试分离器功能
    if diarizer:
        test_diarizer_functionality(diarizer)
    elif service and service._diarizer:
        test_diarizer_functionality(service._diarizer)
    
    print("\n说话人分离功能测试完成！")

if __name__ == "__main__":
    main()