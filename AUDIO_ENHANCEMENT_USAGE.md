# 音频增强功能使用说明

## 概述

本项目实现了基于VOSK的音频增强功能，包括降噪和麦克风增强，旨在提高语音识别的准确性和转录效果。音频增强功能通过以下方式实现：

1. 高通滤波 - 去除低频噪声
2. 自适应降噪 - 使用噪声门控制和谱减法
3. 人声增强 - 突出人声频段(300-3400 Hz)
4. 自动增益控制(AGC) - 标准化音频电平
5. 动态压缩 - 优化动态范围

## 功能特点

### 1. 专业级音频处理流水线
- **高通滤波器**: 去除80Hz以下的低频噪声
- **带通滤波器**: 突出300-3400Hz的人声频段
- **自适应降噪**: 基于短时能量分析的动态噪声门
- **自动增益控制**: 保持稳定的音频电平
- **动态范围压缩**: 优化音频动态范围

### 2. 实时处理能力
- 支持实时音频流处理
- 低延迟处理(平均<1ms)
- 适用于长语音处理(>20秒)

## 使用方法

### 1. 基本使用

```python
from audio_enhancer import AudioEnhancer

# 创建音频增强器
enhancer = AudioEnhancer(sample_rate=16000)

# 设置参数
enhancer.set_noise_reduction(0.5)  # 降噪强度(0.0-1.0)
enhancer.set_gain_target(0.7)      # 自动增益目标(0.1-1.0)

# 增强音频数据
enhanced_audio = enhancer.enhance_audio(raw_audio_bytes)
```

### 2. 与VOSK集成使用

```python
import vosk
from audio_enhancer import EnhancedKaldiRecognizer

# 初始化VOSK模型
model = vosk.Model(model_name="vosk-model-small-cn-0.22")
recognizer = vosk.KaldiRecognizer(model, 16000)
recognizer.SetWords(True)

# 创建增强版识别器
enhanced_recognizer = EnhancedKaldiRecognizer(
    recognizer,
    enable_audio_enhancement=True,
    noise_reduction_strength=0.5,
    gain_target=0.7
)

# 启用音频增强
enhanced_recognizer.EnableAudioEnhancement(True)

# 处理音频数据
if enhanced_recognizer.AcceptWaveform(audio_chunk):
    result = enhanced_recognizer.Result()
```

## 参数说明

### AudioEnhancer参数
- `sample_rate`: 采样率，默认16000Hz
- `noise_reduction_factor`: 降噪因子，默认0.3
- `auto_gain_target`: 自动增益目标，默认0.7
- `compressor_ratio`: 压缩比，默认3.0
- `compressor_threshold`: 压缩阈值，默认0.5

### EnhancedKaldiRecognizer参数
- `enable_audio_enhancement`: 是否启用音频增强，默认True
- `noise_reduction_strength`: 降噪强度(0.0-1.0)，默认0.5
- `gain_target`: 自动增益目标(0.1-1.0)，默认0.7

## 测试结果

### 长语音实时处理测试
- **音频文件**: tests/录音 (12).m4a
- **时长**: 28.95秒
- **标准识别器**:
  - 平均置信度: 0.705
  - 总处理时间: 9.57秒
  - 平均块处理时间: 40.29毫秒
- **增强版识别器**:
  - 平均置信度: 0.700
  - 总处理时间: 9.17秒
  - 平均块处理时间: 39.10毫秒
  - 平均增强时间: 0.39毫秒

## 性能优化

### 处理速度
- 音频增强平均处理时间: <1ms/块
- 实时处理能力: 支持16kHz音频流
- 内存占用: 低内存 footprint

### 稳定性
- 错误处理: 完善的异常处理机制
- 降级处理: 增强功能不可用时自动降级到原始识别器
- 兼容性: 与现有VOSK API完全兼容

## 依赖库

- `scipy`: 用于数字信号处理
- `numpy`: 用于数值计算
- `pydub`: 用于音频格式转换(测试用)

安装依赖:
```bash
pip install scipy numpy pydub
```

## 文件说明

- `audio_enhancer.py`: 音频增强核心模块
- `long_audio_realtime_test.py`: 长语音实时处理测试脚本
- `long_audio_realtime_test_report.txt`: 测试报告
- `long_audio_test.log`: 详细测试日志

## 注意事项

1. 音频增强功能需要安装scipy库
2. 增强功能可能会轻微改变识别结果文本(由于音频处理)
3. 建议根据实际应用场景调整参数
4. 长语音处理时建议监控内存使用情况