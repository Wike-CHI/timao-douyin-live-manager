# PyTorch SenseVoice + VAD 优化建议

## 当前状态

✅ **系统资源充足**
- 磁盘: 20GB 可用
- 内存: 3GB 可用
- PyTorch SenseVoice Small + VAD 已就绪

## 优化策略

### 1. 内存优化配置

当前配置已包含内存监控，在 `sensevoice_service.py` 中：

```python
# 每100次调用检查内存
if memory_mb > 3500:  # 超过3.5GB警告
    gc.collect()  # 执行垃圾回收
    
if memory_mb > 4500:  # 超过4.5GB严重警告
    logger.error("建议重启服务")
```

### 2. VAD策略

**当前使用双VAD策略:**
- **轻量级RMS VAD**: 快速静音检测（几乎无开销）
- **FSMN VAD**: 精确语音检测（可选，在FunASR内部）

**优化建议:**
```python
# live_audio_stream_service.py 中的VAD参数
vad_min_rms: float = 0.015         # 能量阈值
vad_min_speech_sec: float = 0.35   # 最小语音时长
vad_min_silence_sec: float = 0.60  # 最小静音时长
```

### 3. 定期清理

**系统缓存清理** (每月)
```bash
# 使用bleachbit清理
bleachbit --clean system.cache system.tmp
```

**Python缓存清理** (每周)
```bash
# pip缓存
pip cache purge

# Python字节码
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

**日志清理** (每周)
```bash
# 清理旧日志
find . -name "*.log" -mtime +7 -delete

# 截断大日志
truncate -s 0 backend.log nohup.out
```

### 4. 监控指标

**正常运行指标:**
```
内存占用: 2.5-3.5GB (正常)
         > 4GB (需要垃圾回收)
         > 4.5GB (建议重启)

推理时间: < 200ms (良好)
         < 500ms (可接受)
         > 500ms (需要优化)

准确率: > 95% (优秀)
       > 90% (良好)
       < 90% (需要调整)
```

### 5. 性能调优

#### A. 降低batch_size（如果内存紧张）
```python
# sensevoice_service.py
batch_size: int = 1  # 已经是最小值
```

#### B. 调整chunk参数（平衡实时性和准确率）
```python
chunk_size: int = 3200      # 减小可降低延迟但可能影响准确率
chunk_shift: int = 800       # 减小可提高实时性
```

#### C. 禁用不必要的功能
```python
# 如果不需要标点模型，可以禁用以节省内存
punc_model_id: Optional[str] = None
```

### 6. 备份和恢复

**定期备份模型**
```bash
# 备份模型文件
tar -czf sensevoice_backup_$(date +%Y%m%d).tar.gz \
    server/models/.cache/modelscope/iic/SenseVoiceSmall/
```

**快速恢复**
```bash
# 如果模型损坏，从备份恢复
tar -xzf sensevoice_backup_YYYYMMDD.tar.gz -C /
```

### 7. 长期维护

**每月检查:**
- [ ] 磁盘空间 (保持 > 10GB 可用)
- [ ] 内存使用 (峰值 < 4GB)
- [ ] 日志大小 (< 1GB)
- [ ] 模型完整性

**每季度:**
- [ ] 更新依赖包 (慎重，先测试)
- [ ] 检查FunASR/SenseVoice更新
- [ ] 性能基准测试

## 故障排除

### 内存不足
```bash
# 立即清理
pip cache purge
bleachbit --clean system.cache

# 重启服务
./scripts/构建与启动/start-backend.sh
```

### 推理变慢
```bash
# 检查CPU占用
top -p $(pgrep -f uvicorn)

# 检查模型状态
python -c "
from server.modules.ast.sensevoice_service import SenseVoiceService
svc = SenseVoiceService()
print(svc.get_model_info())
"
```

### 准确率下降
1. 检查音频质量
2. 调整VAD阈值
3. 更新热词库
4. 考虑重新加载模型

## 资源

- [FunASR官方文档](https://github.com/alibaba-damo-academy/FunASR)
- [SenseVoice模型](https://www.modelscope.cn/models/iic/SenseVoiceSmall)
- 项目内部文档: `docs/直播音频方案/`

---

**最后更新**: 2025-11-14
**适用版本**: SenseVoice Small + PyTorch 2.2.1

