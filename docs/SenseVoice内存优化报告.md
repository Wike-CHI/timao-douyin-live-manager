# SenseVoice内存优化报告

**审查人**: 叶维哲  
**优化日期**: 2025-11-14  
**问题描述**: 服务器在使用SenseVoiceSmall+VAD转写3句话后因内存不足(OOM)而自动重启

---

## 📊 问题诊断

### 系统环境
- **总内存**: 7.4GB
- **可用内存**: 2.4GB
- **Swap使用**: 3.9GB/4.0GB ⚠️ (严重内存压力)
- **进程内存**: ~2.5GB

### OOM确认
通过 `dmesg` 确认进程被OOM killer终止：
```
Out of memory: Killed process 442170 (python) total-vm:6542504kB, anon-rss:2843996kB
```

---

## 🔧 优化措施

### 1. 增强内存监控机制

**文件**: `server/modules/ast/sensevoice_service.py`

**优化前**:
- 每100次调用检查一次
- 每5分钟检查一次
- 超过3.5GB警告
- 超过4.5GB报错

**优化后**:
- 每20次调用检查一次 (5倍频率)
- 每1分钟检查一次 (5倍频率)
- 超过2GB主动执行垃圾回收
- 超过2.5GB警告 (降低阈值)
- 超过3GB报错 (降低阈值)

### 2. 减小配置参数降低内存峰值

**文件**: `server/modules/ast/sensevoice_service.py` - `SenseVoiceConfig`

| 参数 | 优化前 | 优化后 | 说明 |
|------|--------|--------|------|
| `chunk_size` | 3200 | 1600 | 减少50%，降低单次处理内存 |
| `chunk_shift` | 800 | 400 | 减少50%，保持25%重叠率 |
| `encoder_chunk_look_back` | 4 | 2 | 减少50%，降低上下文缓存 |
| `decoder_chunk_look_back` | 1 | 1 | 保持不变 |
| `batch_size` | 1 | 1 | 已是最小值 |

**预期效果**:
- 降低单次转写内存峰值约30-40%
- 轻微增加转写次数（因为chunk更小）
- 保持转写准确性

### 3. 添加显式内存释放

**文件**: `server/modules/ast/sensevoice_service.py` - `transcribe_audio()`

在音频处理完成后立即释放numpy数组和结果对象：

```python
# 🔧 立即释放音频数据和结果，减少内存占用
del speech
del raw_results
```

**效果**: 避免大对象在内存中停留过长时间

---

## 🧪 自动测试脚本

**文件**: `tests/test_sensevoice_memory.py`

### 测试覆盖

1. **配置参数验证**: 确认所有参数已正确优化
2. **内存监控机制**: 验证监控触发和垃圾回收
3. **内存释放验证**: 确认处理后内存正确释放
4. **连续转写场景**: 模拟实际使用，50次连续转写
5. **垃圾回收触发**: 验证计数器和阈值触发

### 运行测试

```bash
cd /www/wwwroot/wwwroot/timao-douyin-live-manager
python tests/test_sensevoice_memory.py
```

**成功标准**:
- 所有配置参数验证通过
- 连续50次转写内存峰值增长 < 600MB
- 清理后内存增长 < 100MB
- 平均转写速度 < 2秒/次

---

## 📋 应用优化

### 重启服务

```bash
cd /www/wwwroot/wwwroot/timao-douyin-live-manager
pm2 restart timao-backend
```

### 监控内存使用

```bash
# 实时监控PM2进程
pm2 monit

# 查看内存使用
free -h

# 查看进程内存
pm2 info timao-backend

# 查看日志中的内存警告
tail -f logs/pm2-out.log | grep "内存"
```

---

## 📈 预期效果

### 内存占用
- **模型加载**: ~1.8-2.2GB (不变)
- **单次转写峰值**: ~2.5-2.8GB (降低30-40%)
- **连续转写稳定**: ~2.3-2.6GB (降低20-30%)

### 稳定性提升
- **转写次数**: 从3句提升到至少20-30句不重启
- **内存预警**: 更早发现并清理内存
- **OOM风险**: 显著降低

---

## 🚨 长期建议

### 1. 系统层面
- **增加物理内存**: 当前7.4GB对于AI模型较紧张，建议升级到16GB
- **调整Swap**: 如增加内存，可减少Swap使用

### 2. 应用层面
- **限制并发**: 控制同时转写的会话数（当前最多3个）
- **定期重启**: 每天定时重启服务释放内存碎片
- **模型轻量化**: 未来考虑使用量化模型或更小的模型

### 3. 监控告警
- **内存告警**: 超过2.5GB时发送告警
- **Swap告警**: Swap使用超过50%时告警
- **自动重启**: 内存超过3GB自动重启服务

---

## ✅ 验证清单

- [x] 修改SenseVoice内存监控机制
- [x] 优化SenseVoice配置参数
- [x] 添加显式内存释放
- [x] 编写自动测试脚本
- [ ] 重启PM2服务
- [ ] 运行自动测试
- [ ] 实际转写测试（转写>10句）
- [ ] 监控24小时稳定性

---

## 📝 修改文件清单

1. `server/modules/ast/sensevoice_service.py` - 核心优化
2. `tests/test_sensevoice_memory.py` - 自动测试脚本
3. `docs/SenseVoice内存优化报告.md` - 本文档

**审查人**: 叶维哲  
**提交日期**: 2025-11-14

