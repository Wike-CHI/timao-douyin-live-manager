#!/usr/bin/env python3
"""测试智能说话人分离切换功能"""

import sys
import os
import time
import numpy as np
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

def test_smart_switching():
    """测试智能切换功能"""
    print("=== 测试智能说话人分离切换功能 ===")
    
    try:
        from app.services.online_diarizer import OnlineDiarizer
        
        # 创建启用智能切换的分离器
        diarizer = OnlineDiarizer(
            sr=16000,
            max_speakers=2,
            enroll_sec=4.0,
            smooth=0.2,
            single_speaker_mode=True,  # 默认单人模式
            auto_switch=True  # 启用智能切换
        )
        
        print(f"✓ OnlineDiarizer 创建成功")
        print(f"  - 单人模式: {diarizer.single_speaker_mode}")
        print(f"  - 智能切换: {diarizer.auto_switch}")
        print(f"  - 聚类阈值: {diarizer.cluster_threshold}")
        print(f"  - 多人检测阈值: {diarizer.multi_speaker_threshold}")
        print(f"  - 置信度阈值: {diarizer.confidence_threshold}")
        
        return diarizer
        
    except Exception as e:
        print(f"✗ OnlineDiarizer 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_single_speaker_scenario(diarizer):
    """测试单人场景"""
    print("\n=== 测试单人场景 ===")
    
    if diarizer is None:
        print("✗ 分离器为空，跳过测试")
        return False
    
    try:
        # 生成单一说话人的音频数据
        duration = 1.0
        sample_rate = 16000
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples)
        
        # 单一说话人：稳定的低频信号
        audio = (np.sin(2 * np.pi * 200 * t) * 16384).astype(np.int16)
        pcm = audio.tobytes()
        
        print("处理单人音频数据...")
        labels = []
        
        for i in range(8):  # 处理8秒音频
            label, debug = diarizer.feed(pcm, duration)
            labels.append(label)
            
            print(f"  轮次 {i+1}: 标签={label}")
            print(f"    - 多人检测: {diarizer.state.multi_speaker_detected}")
            print(f"    - 多人置信度: {diarizer.state.multi_speaker_confidence:.3f}")
            print(f"    - 稳定单人时长: {diarizer.state.stable_single_duration:.1f}s")
            print(f"    - 聚类数量: {len(diarizer.state.clusters)}")
        
        # 验证结果
        unique_labels = set(labels)
        print(f"\n单人场景结果:")
        print(f"  - 检测到的标签: {unique_labels}")
        print(f"  - 是否保持单人模式: {not diarizer.state.multi_speaker_detected}")
        print(f"  - 最终聚类数量: {len(diarizer.state.clusters)}")
        
        # 单人场景应该只有一个标签，且不应该检测到多人
        success = (
            len(unique_labels) <= 1 and
            not diarizer.state.multi_speaker_detected and
            len(diarizer.state.clusters) <= 1
        )
        
        print(f"  - 单人场景测试: {'✓ 通过' if success else '✗ 失败'}")
        return success
        
    except Exception as e:
        print(f"✗ 单人场景测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multi_speaker_scenario(diarizer):
    """测试多人场景"""
    print("\n=== 测试多人场景 ===")
    
    if diarizer is None:
        print("✗ 分离器为空，跳过测试")
        return False
    
    try:
        # 重置分离器状态
        diarizer.state.multi_speaker_detected = False
        diarizer.state.multi_speaker_confidence = 0.0
        diarizer.state.stable_single_duration = 0.0
        
        duration = 1.0
        sample_rate = 16000
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples)
        
        # 说话人1：低频信号
        audio1 = (np.sin(2 * np.pi * 200 * t) * 16384).astype(np.int16)
        pcm1 = audio1.tobytes()
        
        # 说话人2：高频信号（差异较大）
        audio2 = (np.sin(2 * np.pi * 1000 * t) * 16384).astype(np.int16)
        pcm2 = audio2.tobytes()
        
        print("处理多人音频数据...")
        labels = []
        
        # 先处理说话人1的音频（建立基线）
        print("\n--- 建立说话人1基线 ---")
        for i in range(4):
            label, debug = diarizer.feed(pcm1, duration)
            labels.append(label)
            print(f"  轮次 {i+1}: 标签={label}, 多人置信度={diarizer.state.multi_speaker_confidence:.3f}")
        
        # 然后引入说话人2的音频
        print("\n--- 引入说话人2 ---")
        for i in range(6):
            label, debug = diarizer.feed(pcm2, duration)
            labels.append(label)
            
            print(f"  轮次 {i+1}: 标签={label}")
            print(f"    - 多人检测: {diarizer.state.multi_speaker_detected}")
            print(f"    - 多人置信度: {diarizer.state.multi_speaker_confidence:.3f}")
            print(f"    - 聚类数量: {len(diarizer.state.clusters)}")
            
            # 如果检测到多人，记录切换时间
            if diarizer.state.multi_speaker_detected:
                print(f"    - ✓ 成功检测到多人，在第 {i+1} 轮次切换")
                break
        
        # 验证结果
        unique_labels = set(labels)
        print(f"\n多人场景结果:")
        print(f"  - 检测到的标签: {unique_labels}")
        print(f"  - 是否检测到多人: {diarizer.state.multi_speaker_detected}")
        print(f"  - 最终聚类数量: {len(diarizer.state.clusters)}")
        print(f"  - 最终置信度: {diarizer.state.multi_speaker_confidence:.3f}")
        
        # 多人场景应该检测到多个说话者
        success = (
            diarizer.state.multi_speaker_detected or
            len(diarizer.state.clusters) > 1 or
            diarizer.state.multi_speaker_confidence > 0.5
        )
        
        print(f"  - 多人场景测试: {'✓ 通过' if success else '✗ 失败'}")
        return success
        
    except Exception as e:
        print(f"✗ 多人场景测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_live_service_integration():
    """测试LiveAudioStreamService集成"""
    print("\n=== 测试LiveAudioStreamService集成 ===")
    
    try:
        from app.services.live_audio_stream_service import LiveAudioStreamService
        
        # 设置环境变量为多人模式（启用智能切换）
        os.environ["LIVE_DIARIZER_MAX_SPEAKERS"] = "2"
        
        # 创建服务实例
        service = LiveAudioStreamService()
        print("✓ LiveAudioStreamService 实例创建成功")
        
        # 检查分离器配置
        if service._diarizer is not None:
            print(f"✓ 说话人分离器已初始化")
            print(f"  - 单人模式: {getattr(service._diarizer, 'single_speaker_mode', False)}")
            print(f"  - 智能切换: {getattr(service._diarizer, 'auto_switch', False)}")
            print(f"  - 聚类阈值: {getattr(service._diarizer, 'cluster_threshold', 'N/A')}")
            print(f"  - 最大说话人数: {service._diarizer.max_speakers}")
            
            # 检查是否正确启用了智能切换
            auto_switch_enabled = getattr(service._diarizer, 'auto_switch', False)
            single_mode_default = getattr(service._diarizer, 'single_speaker_mode', False)
            
            success = auto_switch_enabled and single_mode_default
            print(f"  - 智能切换配置: {'✓ 正确' if success else '✗ 错误'}")
            return success
        else:
            print("✗ 说话人分离器未初始化")
            return False
            
    except Exception as e:
        print(f"✗ LiveAudioStreamService 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试智能说话人分离切换功能...\n")
    
    # 测试1: 创建智能切换分离器
    diarizer = test_smart_switching()
    
    # 测试2: 单人场景测试
    single_success = test_single_speaker_scenario(diarizer)
    
    # 测试3: 多人场景测试
    multi_success = test_multi_speaker_scenario(diarizer)
    
    # 测试4: 服务集成测试
    integration_success = test_live_service_integration()
    
    # 总结
    print("\n" + "="*60)
    print("智能切换功能测试结果总结:")
    print(f"  - 分离器创建: {'✓' if diarizer is not None else '✗'}")
    print(f"  - 单人场景: {'✓' if single_success else '✗'}")
    print(f"  - 多人场景: {'✓' if multi_success else '✗'}")
    print(f"  - 服务集成: {'✓' if integration_success else '✗'}")
    
    overall_success = all([
        diarizer is not None,
        single_success,
        multi_success,
        integration_success
    ])
    
    print(f"\n整体功能状态: {'✓ 成功' if overall_success else '✗ 需要调试'}")
    
    if overall_success:
        print("\n🎉 智能说话人分离切换功能测试成功！")
        print("系统现在能够：")
        print("  - 默认以单人模式启动")
        print("  - 自动检测多个说话者")
        print("  - 智能切换到多人分离模式")
        print("  - 避免频繁的模式切换")
    else:
        print("\n⚠️  智能切换功能需要进一步调试，请检查上述失败的测试项。")

if __name__ == "__main__":
    main()