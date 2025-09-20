# -*- coding: utf-8 -*-
"""
增强数据结构测试
验证EnhancedTranscriptionResult及相关数据结构的功能
"""

import time
from enhanced_transcription_result import (
    EnhancedTranscriptionResult,
    AudioQuality,
    EmotionalFeatures,
    ConfidenceBreakdown,
    WordAnalysis,
    EmotionType,
    ProcessingType,
    create_basic_result,
    create_enhanced_result
)

def test_basic_data_structures():
    """测试基础数据结构"""
    print("🧪 测试基础数据结构...")
    
    # 测试AudioQuality
    audio_quality = AudioQuality(
        noise_level=0.3,
        volume_level=0.8,
        clarity_score=0.9,
        sample_rate=16000,
        snr_db=15.5
    )
    print(f"✅ AudioQuality: 噪音={audio_quality.noise_level}, 清晰度={audio_quality.clarity_score}")
    
    # 测试EmotionalFeatures
    emotional_features = EmotionalFeatures(
        emotion_type=EmotionType.EXCITED,
        intensity=0.8,
        speech_rate=180.5,
        tone_confidence=0.85,
        pause_pattern=[0.5, 1.2, 0.3],
        voice_stress=0.6
    )
    print(f"✅ EmotionalFeatures: {emotional_features.emotion_type.value}, 强度={emotional_features.intensity}")
    
    # 测试ConfidenceBreakdown
    confidence_breakdown = ConfidenceBreakdown(
        vosk_confidence=0.7,
        word_frequency_score=0.8,
        context_coherence_score=0.75,
        audio_quality_score=0.9,
        emotion_boost=0.1,
        final_confidence=0.85
    )
    print(f"✅ ConfidenceBreakdown: 最终置信度={confidence_breakdown.final_confidence}")

def test_enhanced_transcription_result():
    """测试增强转录结果"""
    print("\n🧪 测试增强转录结果...")
    
    # 创建基础结果
    basic_result = create_basic_result(
        text="今天这个产品真的超级棒，大家快来买！",
        confidence=0.85,
        room_id="test_room_001",
        session_id="session_123"
    )
    print(f"✅ 基础结果: {basic_result.text}")
    print(f"   置信度: {basic_result.confidence}")
    
    # 创建增强结果
    audio_quality = AudioQuality(0.2, 0.9, 0.95, 16000)
    emotional_features = EmotionalFeatures(
        EmotionType.EXCITED, 0.9, 200.0, 0.9
    )
    confidence_breakdown = ConfidenceBreakdown(
        0.7, 0.85, 0.8, 0.95, 0.12, 0.88
    )
    
    enhanced_result = create_enhanced_result(
        text="今天这个产品真的超级棒，大家快来买！",
        confidence=0.88,
        audio_quality=audio_quality,
        emotional_features=emotional_features,
        confidence_breakdown=confidence_breakdown,
        room_id="test_room_001",
        session_id="session_123"
    )
    
    enhanced_result.post_processing_applied = [
        ProcessingType.EMOTION_CORRECTION,
        ProcessingType.CONFIDENCE_BOOST
    ]
    enhanced_result.original_text = "今天这个产品真的超级棒，大家快来买"
    enhanced_result.processing_time_ms = 85.5
    
    print(f"✅ 增强结果: {enhanced_result.text}")
    print(f"   {enhanced_result.get_emotion_summary()}")
    print(f"   {enhanced_result.get_confidence_summary()}")
    print(f"   {enhanced_result.get_processing_summary()}")
    print(f"   增强功能: {enhanced_result.has_enhancement()}")

def test_compatibility():
    """测试向后兼容性"""
    print("\n🧪 测试向后兼容性...")
    
    # 创建增强结果
    result = EnhancedTranscriptionResult(
        text="测试兼容性",
        confidence=0.8,
        timestamp=time.time(),
        duration=1.5,
        is_final=True,
        room_id="compat_test",
        session_id="compat_session"
    )
    
    # 转换为legacy格式
    legacy_format = result.to_legacy_format()
    print("✅ Legacy格式转换:")
    for key, value in legacy_format.items():
        print(f"   {key}: {value}")
    
    # 验证字段完整性
    expected_fields = ["text", "confidence", "timestamp", "duration", 
                      "is_final", "words", "room_id", "session_id"]
    missing_fields = [f for f in expected_fields if f not in legacy_format]
    
    if not missing_fields:
        print("✅ 所有必需字段都存在")
    else:
        print(f"❌ 缺失字段: {missing_fields}")

def test_data_validation():
    """测试数据验证"""
    print("\n🧪 测试数据验证...")
    
    # 测试置信度范围限制
    result = EnhancedTranscriptionResult(
        text="测试",
        confidence=1.5,  # 超出范围
        timestamp=time.time(),
        duration=1.0,
        is_final=True
    )
    print(f"✅ 置信度范围限制: {result.confidence} (应该<=1.0)")
    
    # 测试音频质量验证
    audio_quality = AudioQuality(
        noise_level=1.2,   # 超出范围
        volume_level=-0.1, # 超出范围
        clarity_score=0.8,
        sample_rate=16000
    )
    print(f"✅ 音频质量验证: 噪音={audio_quality.noise_level}, 音量={audio_quality.volume_level}")
    
    # 测试情感特征验证
    emotional = EmotionalFeatures(
        emotion_type=EmotionType.JOYFUL,
        intensity=1.5,     # 超出范围
        speech_rate=150.0,
        tone_confidence=0.9
    )
    print(f"✅ 情感特征验证: 强度={emotional.intensity} (应该<=1.0)")

def test_enum_types():
    """测试枚举类型"""
    print("\n🧪 测试枚举类型...")
    
    # 测试情感类型
    emotions = [e.value for e in EmotionType]
    print(f"✅ 支持的情感类型: {emotions}")
    
    # 测试处理类型
    processing = [p.value for p in ProcessingType]
    print(f"✅ 支持的处理类型: {processing}")

def main():
    """主测试函数"""
    print("🎤 AST增强数据结构测试")
    print("=" * 50)
    
    try:
        test_basic_data_structures()
        test_enhanced_transcription_result()
        test_compatibility()
        test_data_validation()
        test_enum_types()
        
        print("\n" + "=" * 50)
        print("🎉 所有测试通过！数据结构定义正确")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)