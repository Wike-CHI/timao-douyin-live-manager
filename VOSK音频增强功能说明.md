# VOSK语音识别增强功能使用指南

## 概述

本项目在原有VOSK语音识别功能基础上，新增了强大的**降噪和麦克风增强功能**，显著提升语音转录效果，特别适用于噪声环境下的实时语音识别。

## 新增功能特性

### 🎧 音频增强核心功能

1. **实时降噪处理**
   - 自适应噪声门控制
   - 高通滤波器去除低频噪声
   - 谱减法降噪算法
   - 可调节降噪强度（0-100%）

2. **麦克风增强**
   - 自动增益控制(AGC)
   - 动态压缩器平衡音量
   - 人声频段突出处理
   - 可调节增益目标（10-100%）

3. **音频质量监测**
   - 实时音频质量评估
   - 信噪比计算
   - 音量水平监控
   - 智能质量提示

### 🔧 增强版识别器

在VOSK原有功能基础上，新增：

- **EnhancedKaldiRecognizer** - 集成音频增强的识别器
- 自动音频预处理流水线
- 实时性能监测和统计
- 灵活的增强参数控制

## 使用方法

### 1. Python API 使用

```python
from vosk import Model, EnhancedKaldiRecognizer
import pyaudio

# 初始化模型
model = Model(model_path="your_model_path")

# 创建增强版识别器
recognizer = EnhancedKaldiRecognizer(
    model, 
    16000,  # 采样率
    enable_audio_enhancement=True,
    noise_reduction_strength=0.6,  # 降噪强度
    gain_target=0.8  # 增益目标
)

# 配置识别参数
recognizer.SetWords(True)
recognizer.SetMaxAlternatives(3)

# 音频流处理
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, 
                rate=16000, input=True, frames_per_buffer=4000)

print("开始语音识别（带音频增强）...")
while True:
    data = stream.read(4000, exception_on_overflow=False)
    
    if recognizer.AcceptWaveform(data):
        result = recognizer.Result()
        print(f"识别结果: {result}")
    else:
        partial = recognizer.PartialResult()
        print(f"实时结果: {partial}")
```

### 2. 动态调整增强参数

```python
# 调整降噪强度 (0.0-1.0)
recognizer.SetNoiseReduction(0.7)

# 调整增益目标 (0.0-1.0)  
recognizer.SetGainTarget(0.8)

# 启用/禁用音频增强
recognizer.EnableAudioEnhancement(True)

# 获取增强统计信息
stats = recognizer.GetEnhancementStats()
print(f"处理块数: {stats['processed_chunks']}")
print(f"平均增强时间: {stats['average_enhancement_time']:.2f}ms")
```

### 3. Web界面使用

打开 `AST_local_test.html` 文件，新的音频增强面板包含：

#### 音频增强控制面板
- **启用音频增强**: 总开关
- **降噪强度**: 滑动条调节（0-100%）
- **麦克风增益**: 滑动条调节（10-100%）  
- **自动增益控制**: 启用/禁用AGC

#### 状态监控面板
- **音频增强**: 显示当前开关状态
- **降噪级别**: 显示当前降噪强度
- **音频质量**: 实时质量评估（优秀/良好/较差）

#### 实时音频监控
- 音量条实时显示麦克风输入音量
- 颜色编码指示音量状态：
  - 🔴 红色：音量过低/过高
  - 🟠 橙色：音量较低
  - 🟢 绿色：理想音量范围

## 技术实现原理

### 音频处理流水线

```
原始音频 → 高通滤波 → 噪声门 → 带通增强 → 自动增益 → 动态压缩 → 输出
```

1. **高通滤波**: 去除80Hz以下低频噪声
2. **自适应噪声门**: 基于能量分布的动态阈值
3. **人声频段增强**: 300-3400Hz带通滤波突出人声
4. **自动增益控制**: 目标RMS水平维持
5. **动态压缩**: 平衡音量动态范围

### 关键技术特性

- **Web Audio API**: 浏览器端实时音频处理
- **自适应算法**: 根据环境自动调整参数
- **低延迟设计**: <5ms音频处理延迟
- **兼容性**: 支持Chrome、Edge、Firefox等现代浏览器

## 性能优化

### 推荐设置

| 环境类型 | 降噪强度 | 麦克风增益 | 自动增益 |
|----------|----------|------------|----------|
| 安静环境 | 30-50%   | 60-80%     | 启用     |
| 办公环境 | 50-70%   | 70-90%     | 启用     |
| 噪声环境 | 70-90%   | 80-100%    | 启用     |
| 会议室   | 40-60%   | 50-70%     | 启用     |

### 性能监测

系统提供详细的性能统计：

```javascript
// Web界面统计信息
- 处理块数: 实际处理的音频块数量
- 成功识别: 有效识别次数
- 音频增强开销: 增强处理时间占比
- 平均响应时间: 从音频到结果的时间
```

## 常见问题解决

### 1. 音质问题
**问题**: 识别准确率低
**解决**:
- 增加降噪强度到60-80%
- 调整麦克风增益到70-90%
- 确保麦克风距离嘴部15-30cm

### 2. 延迟问题
**问题**: 音频处理延迟高
**解决**:
- 降低降噪强度到30-50%
- 关闭部分增强功能
- 检查CPU使用率

### 3. 兼容性问题
**问题**: 浏览器不支持某些功能
**解决**:
- 使用Chrome 90+或Edge 90+
- 确保HTTPS环境（本地可用localhost）
- 检查麦克风权限设置

## 更新日志

### v2.0.0 (当前版本)
- ✅ 新增EnhancedKaldiRecognizer类
- ✅ 实现实时降噪算法
- ✅ 添加麦克风增强功能
- ✅ 集成音频质量监测
- ✅ 优化Web界面控制面板
- ✅ 添加性能统计和监控

### v1.0.0 (基础版本)
- ✅ 基础VOSK语音识别
- ✅ Web界面单元测试
- ✅ 多语言支持

## 技术支持

如需技术支持或有改进建议，请联系开发团队或提交Issue。

---

**注意**: 音频增强功能需要现代浏览器支持Web Audio API，建议使用Chrome 90+或Edge 90+以获得最佳体验。