# SenseVoice持续转录优化方案

**审查人**: 叶维哲  
**创建日期**: 2025-11-09  
**目标**: 确保SenseVoice能持续转录，不只是第一句话

---

## 当前问题分析

### 已完成的修复 ✅

1. **音频分块优化**
   - `chunk_seconds`: 0.8秒 → 1.6秒
   - 解决了"window size"错误
   
2. **日志优化**
   - window size错误：ERROR → DEBUG
   - 减少日志噪音

### 仍需优化的问题

1. **内存占用**
   - SenseVoice模型加载后占用2-4GB内存
   - 长时间运行可能内存泄漏
   
2. **CPU占用**
   - 实时转录CPU占用较高
   - 需要优化推理频率

3. **持续转录保障**
   - 确保不会在第一句话后停止
   - VAD参数优化

---

## 优化方案

### 1. VAD参数微调

**目标**: 更灵敏地检测语音，避免漏掉句子

**当前配置**:
```python
chunk_seconds: 1.6秒
vad_min_silence_sec: 0.60秒  # 静音阈值
vad_min_speech_sec: 0.35秒   # 语音阈值
```

**优化配置**:
```python
chunk_seconds: 1.6秒  # 保持
vad_min_silence_sec: 0.50秒  # 降低：更快检测到静音结束
vad_min_speech_sec: 0.30秒   # 降低：更快检测到语音开始
vad_min_rms: 0.015  # 降低：对更弱的声音也敏感
```

### 2. 内存优化

**优化点**:
1. 定期清理缓冲区
2. 限制历史数据大小
3. 模型推理后立即释放中间变量

**实现**:
```python
# 限制句子缓冲区大小
MAX_SENTENCE_BUFFER = 100  # 最多保留100句

# 定期清理（每5分钟）
if len(self._sentences) > MAX_SENTENCE_BUFFER:
    self._sentences = self._sentences[-MAX_SENTENCE_BUFFER:]
```

### 3. CPU优化

**优化点**:
1. 跳过静音音频的转录
2. 使用批处理（已有batch_size=1，保持）
3. 降低推理频率（如果实时性要求不高）

**实现**:
```python
# 静音检测：跳过RMS过低的音频
rms = pcm16_rms(audio_chunk)
if rms < 0.01:  # 静音阈值
    return {"success": True, "type": "silence", "text": ""}
```

### 4. 持续转录保障

**关键点**:
1. 确保VAD不会"卡住"
2. 音频流不中断
3. 错误时自动恢复

**检查点**:
```python
# 检查转录是否停止（超过30秒无输出）
last_transcription_time = time.time()

if time.time() - last_transcription_time > 30:
    logger.warning("转录可能停止，重启ASR服务")
    await restart_asr_service()
```

---

## 具体实现

### 修改1: 优化VAD参数

**文件**: `server/app/services/live_audio_stream_service.py`

```python
# 行234左右
self.chunk_seconds: float = 1.6  # 保持
self.vad_min_silence_sec: float = 0.50  # 从0.60降低
self.vad_min_speech_sec: float = 0.30   # 从0.35降低
```

### 修改2: 添加内存监控

**文件**: `server/modules/ast/sensevoice_service.py`

```python
import gc
import psutil

async def transcribe_audio(self, audio_data: bytes, **kwargs):
    # 定期检查内存（每100次调用）
    self._call_count = getattr(self, '_call_count', 0) + 1
    
    if self._call_count % 100 == 0:
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        if memory_mb > 3000:  # 超过3GB
            logger.warning(f"内存占用过高: {memory_mb:.0f}MB，执行垃圾回收")
            gc.collect()
            
            # 如果还是很高，考虑重启模型
            if memory_mb > 4000:
                logger.error(f"内存占用严重: {memory_mb:.0f}MB，需要重启")
```

### 修改3: 静音快速跳过

**文件**: `server/app/services/live_audio_stream_service.py`

```python
# 在转录前检查RMS
rms = pcm16_rms(pcm16)
if rms < 0.01:  # 静音
    return {
        "success": True,
        "type": "silence",
        "text": "",
        "confidence": 0.0
    }
```

### 修改4: 持续转录监控

**文件**: `server/app/services/live_audio_stream_service.py`

```python
class LiveAudioStreamService:
    def __init__(self):
        # ...
        self._last_transcription_time = time.time()
        self._transcription_monitor_task = None
    
    async def _monitor_transcription(self):
        """监控转录是否停止"""
        while self.is_running:
            await asyncio.sleep(30)  # 每30秒检查一次
            
            elapsed = time.time() - self._last_transcription_time
            if elapsed > 60:  # 超过60秒无输出
                logger.warning(f"⚠️ 转录已停止{elapsed:.0f}秒，可能需要重启")
                # 可以发送告警或自动重启
```

---

## 测试验证

### 测试1: 持续转录测试

```bash
# 启动服务
pm2 restart backend

# 监控日志
pm2 logs backend | grep -E "转录|transcription|silence"

# 预期：持续看到转录输出，不会停在第一句
```

### 测试2: 内存监控

```bash
# 查看内存占用
watch -n 5 'ps aux | grep python | grep -v grep'

# 预期：内存占用稳定在2-3GB，不会持续增长
```

### 测试3: CPU监控

```bash
# 查看CPU占用
top -p $(pgrep -f "python.*uvicorn")

# 预期：CPU占用稳定在30-50%，不会持续100%
```

---

## 环境变量配置

可以通过环境变量调整参数：

```bash
# .env 文件
LIVE_VAD_CHUNK_SEC=1.6           # 音频分块时长
LIVE_VAD_MIN_RMS=0.015           # RMS阈值
SENSEVOICE_DEVICE=cuda:0         # 使用GPU（如果有）
```

---

## 监控指标

### 关键指标

| 指标 | 正常范围 | 告警阈值 |
|------|---------|---------|
| 内存占用 | 2-3GB | >4GB |
| CPU占用 | 30-50% | >80% |
| 转录延迟 | <500ms | >2s |
| 无输出时长 | <30s | >60s |

### 日志关键词

监控以下日志：
```bash
# 正常转录
✅ 转录成功

# 静音（正常）
DEBUG: 音频片段太短或无有效语音

# 异常
❌ 转录失败
⚠️ 转录已停止

# 内存
⚠️ 内存占用过高
```

---

## 故障排查

### 问题1: 转录停在第一句

**检查**:
```bash
# 查看VAD参数
pm2 logs backend | grep "chunk_seconds\|vad_min"

# 查看是否有错误
pm2 logs backend | grep -i error | tail -20
```

**解决**:
1. 降低VAD阈值（更灵敏）
2. 增加chunk_seconds（1.6→2.0秒）
3. 检查音频流是否中断

### 问题2: 内存持续增长

**检查**:
```bash
# 监控内存
watch -n 1 'ps aux | grep python | grep -v grep | awk "{print \$6/1024\" MB\"}"'
```

**解决**:
1. 启用定期垃圾回收
2. 限制缓冲区大小
3. 重启服务（临时方案）

### 问题3: CPU占用过高

**检查**:
```bash
# 查看CPU占用
top -p $(pgrep -f "python.*uvicorn")
```

**解决**:
1. 启用GPU推理（如果有）
2. 增加chunk_seconds（减少推理频率）
3. 启用静音快速跳过

---

## 实施计划

### 阶段1: 快速优化（5分钟）

1. 调整VAD参数
2. 重启服务
3. 观察效果

### 阶段2: 监控优化（10分钟）

1. 添加内存监控
2. 添加转录监控
3. 测试验证

### 阶段3: 深度优化（可选）

1. GPU加速（如果有）
2. 模型量化
3. 分布式部署

---

## 预期效果

优化后：
- ✅ 持续转录，不会停在第一句
- ✅ 内存占用稳定（2-3GB）
- ✅ CPU占用降低（30-50%）
- ✅ 转录延迟<500ms
- ✅ 无明显错误日志

---

## 下一步

1. 立即执行优化
2. 监控运行效果
3. 根据实际情况调整参数

