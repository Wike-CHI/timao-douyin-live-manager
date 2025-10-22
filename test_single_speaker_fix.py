#!/usr/bin/env python3
"""测试单人说话人分离功能修复"""

import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

def test_single_speaker_mode():
    """测试单人模式的说话人分离功能"""
    print("=== 测试单人模式说话人分离功能 ===")
    
    try:
        from app.services.online_diarizer import OnlineDiarizer
        
        # 测试单人模式初始化
        print("\n--- 测试单人模式初始化 ---")
        diarizer_single = OnlineDiarizer(
            sr=16000, 
            max_speakers=1, 
            enroll_sec=4.0, 
            smooth=0.2, 
            single_speaker_mode=True
        )
        print("✓ 单人模式 OnlineDiarizer 初始化成功")
        print(f"  - 单人模式: {diarizer_single.single_speaker_mode}")
        print(f"  - 聚类阈值: {diarizer_single.cluster_threshold}")
        print(f"  - 最大说话人数: {diarizer_single.max_speakers}")
        
        # 测试多人模式初始化（对比）
        print("\n--- 测试多人模式初始化（对比） ---")
        diarizer_multi = OnlineDiarizer(
            sr=16000, 
            max_speakers=2, 
            enroll_sec=4.0, 
            smooth=0.2, 
            single_speaker_mode=False
        )
        print("✓ 多人模式 OnlineDiarizer 初始化成功")
        print(f"  - 单人模式: {diarizer_multi.single_speaker_mode}")
        print(f"  - 聚类阈值: {diarizer_multi.cluster_threshold}")
        print(f"  - 最大说话人数: {diarizer_multi.max_speakers}")
        
        return diarizer_single, diarizer_multi
        
    except Exception as e:
        print(f"✗ OnlineDiarizer 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def test_single_speaker_processing(diarizer_single, diarizer_multi):
    """测试单人模式的音频处理"""
    if diarizer_single is None or diarizer_multi is None:
        print("✗ 分离器为空，跳过处理测试")
        return
    
    print("\n=== 测试单人模式音频处理 ===")
    
    try:
        import numpy as np
        
        # 生成测试音频数据（模拟同一个人的不同音调）
        duration = 1.0  # 1秒
        sample_rate = 16000
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples)
        
        # 模拟同一个人的不同音调/情绪状态
        # 音调1：正常说话
        audio1 = (np.sin(2 * np.pi * 300 * t) * 0.7 * 16384).astype(np.int16)
        pcm1 = audio1.tobytes()
        
        # 音调2：稍高音调（同一人激动时）
        audio2 = (np.sin(2 * np.pi * 400 * t) * 0.8 * 16384).astype(np.int16)
        pcm2 = audio2.tobytes()
        
        # 音调3：稍低音调（同一人平静时）
        audio3 = (np.sin(2 * np.pi * 250 * t) * 0.6 * 16384).astype(np.int16)
        pcm3 = audio3.tobytes()
        
        print("✓ 测试音频数据生成成功（模拟同一人不同音调）")
        
        # 测试单人模式处理
        print("\n--- 单人模式处理结果 ---")
        single_labels = []
        single_clusters = []
        
        for i, pcm in enumerate([pcm1, pcm2, pcm3, pcm1, pcm2, pcm3], 1):
            label, debug = diarizer_single.feed(pcm, duration)
            single_labels.append(label)
            single_clusters.append(debug.get('clusters', 0))
            print(f"  轮次 {i}: 标签={label}, 聚类数={debug.get('clusters', 0)}, 调试={debug}")
        
        # 测试多人模式处理（对比）
        print("\n--- 多人模式处理结果（对比） ---")
        multi_labels = []
        multi_clusters = []
        
        for i, pcm in enumerate([pcm1, pcm2, pcm3, pcm1, pcm2, pcm3], 1):
            label, debug = diarizer_multi.feed(pcm, duration)
            multi_labels.append(label)
            multi_clusters.append(debug.get('clusters', 0))
            print(f"  轮次 {i}: 标签={label}, 聚类数={debug.get('clusters', 0)}, 调试={debug}")
        
        # 分析结果
        print("\n--- 结果分析 ---")
        print(f"单人模式:")
        print(f"  - 标签列表: {single_labels}")
        print(f"  - 聚类数变化: {single_clusters}")
        print(f"  - 最终聚类数: {single_clusters[-1] if single_clusters else 0}")
        print(f"  - 标签一致性: {'✓' if len(set(single_labels)) == 1 else '✗'}")
        
        print(f"多人模式:")
        print(f"  - 标签列表: {multi_labels}")
        print(f"  - 聚类数变化: {multi_clusters}")
        print(f"  - 最终聚类数: {multi_clusters[-1] if multi_clusters else 0}")
        print(f"  - 标签一致性: {'✓' if len(set(multi_labels)) <= 1 else '✗'}")
        
        # 验证修复效果
        single_success = (
            len(set(single_labels)) == 1 and  # 标签一致
            all(label == "host" for label in single_labels) and  # 都是主播
            single_clusters[-1] <= 1  # 最多1个聚类
        )
        
        print(f"\n单人模式修复效果: {'✓ 成功' if single_success else '✗ 失败'}")
        
        return single_success
        
    except Exception as e:
        print(f"✗ 音频处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_live_service_integration():
    """测试LiveAudioStreamService集成"""
    print("\n=== 测试LiveAudioStreamService集成 ===")
    
    try:
        from app.services.live_audio_stream_service import LiveAudioStreamService
        
        # 设置环境变量为单人模式
        os.environ["LIVE_DIARIZER_MAX_SPEAKERS"] = "1"
        
        # 创建服务实例
        service = LiveAudioStreamService()
        print("✓ LiveAudioStreamService 实例创建成功")
        
        # 检查分离器配置
        if service._diarizer is not None:
            print(f"✓ 说话人分离器已初始化")
            print(f"  - 单人模式: {getattr(service._diarizer, 'single_speaker_mode', False)}")
            print(f"  - 聚类阈值: {getattr(service._diarizer, 'cluster_threshold', 'N/A')}")
            print(f"  - 最大说话人数: {service._diarizer.max_speakers}")
            
            # 检查是否正确启用了单人模式
            single_mode_enabled = getattr(service._diarizer, 'single_speaker_mode', False)
            return single_mode_enabled
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
    print("开始测试单人说话人分离功能修复...")
    
    # 测试1: 基本功能测试
    diarizer_single, diarizer_multi = test_single_speaker_mode()
    
    # 测试2: 音频处理测试
    processing_success = test_single_speaker_processing(diarizer_single, diarizer_multi)
    
    # 测试3: 服务集成测试
    integration_success = test_live_service_integration()
    
    # 总结
    print("\n" + "="*50)
    print("测试结果总结:")
    print(f"  - 基本功能: {'✓' if diarizer_single is not None else '✗'}")
    print(f"  - 音频处理: {'✓' if processing_success else '✗'}")
    print(f"  - 服务集成: {'✓' if integration_success else '✗'}")
    
    overall_success = all([
        diarizer_single is not None,
        processing_success,
        integration_success
    ])
    
    print(f"\n整体修复状态: {'✓ 成功' if overall_success else '✗ 需要进一步调试'}")
    
    if overall_success:
        print("\n🎉 单人说话人分离功能修复成功！")
        print("现在单人直播间应该只会识别出一个主播，不会出现错误的guest标签。")
    else:
        print("\n⚠️  修复未完全成功，请检查上述失败的测试项。")

if __name__ == "__main__":
    main()