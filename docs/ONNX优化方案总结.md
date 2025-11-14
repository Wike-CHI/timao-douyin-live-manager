# SenseVoice ONNX 优化方案总结

## 📋 方案概述

将服务器上的PyTorch SenseVoice模型转换为ONNX格式，在保持架构不变的前提下，显著降低内存和磁盘占用。

## 🎯 优化目标

### 资源优化
```
内存占用:
  PyTorch: 2.5-4GB峰值 → ONNX: 1.5-2.5GB峰值 (节省40%)

磁盘占用:
  PyTorch模型: 897MB → ONNX模型: 400-600MB
  可卸载torch相关包: 节省3-4GB

推理性能:
  PyTorch CPU: 基准 → ONNX CPU: 持平或提升10-20%
```

### 架构优势
- ✅ 保持客户端-服务器架构不变
- ✅ 无需修改客户端代码
- ✅ 支持PyTorch/ONNX动态切换
- ✅ 支持热切换（重启即可）

## 📁 文件结构

```
项目根目录/
├── server/
│   └── modules/
│       └── ast/
│           ├── sensevoice_service.py          # PyTorch版本（原有）
│           └── sensevoice_onnx_service.py     # ONNX版本（新增）
│
├── scripts/
│   ├── export_models_to_onnx.py               # 模型导出脚本
│   ├── verify_onnx_model.py                   # 模型验证脚本
│   ├── compare_pytorch_onnx_accuracy.py       # 性能对比脚本
│   └── cleanup_disk.sh                        # 磁盘清理脚本
│
└── docs/
    ├── ONNX部署指南.md                         # 部署说明
    └── ONNX优化方案总结.md                     # 本文档
```

## 🚀 快速开始

### 1. 导出ONNX模型

```bash
# 确保PyTorch模型已下载
python scripts/export_models_to_onnx.py
```

### 2. 验证模型

```bash
python scripts/verify_onnx_model.py
```

### 3. 启用ONNX后端

```bash
export SENSEVOICE_USE_ONNX=true
./scripts/构建与启动/start-backend.sh
```

### 4. 性能测试（可选）

```bash
python scripts/compare_pytorch_onnx_accuracy.py
```

## 🔧 技术实现

### 模型导出

- **工具**: torch.onnx.export 或 FunASR.export()
- **格式**: ONNX Opset 14
- **优化**: 不量化，保持全精度以确保准确率

### ONNX Runtime配置

```python
@dataclass
class SenseVoiceONNXConfig:
    onnx_model_path: str = "server/models/onnx/sensevoice_small.onnx"
    inter_op_num_threads: int = 4  # 根据CPU核心数调整
    intra_op_num_threads: int = 4
    enable_mem_pattern: bool = True  # 内存优化
    enable_cpu_mem_arena: bool = True
```

### 动态后端切换

```python
# 环境变量控制
USE_ONNX_BACKEND = os.getenv("SENSEVOICE_USE_ONNX", "false").lower() == "true"

if USE_ONNX_BACKEND and ONNX_AVAILABLE:
    sv = SenseVoiceONNXService(SenseVoiceONNXConfig())
else:
    sv = SenseVoiceService(SenseVoiceConfig(...))
```

## 📊 实施阶段

### ✅ 阶段1: 模型导出（已完成）

- [x] 创建导出脚本
- [x] 支持FunASR export和手动export双模式
- [x] 模型大小验证

### ✅ 阶段2: ONNX适配器（已完成）

- [x] 实现SenseVoiceONNXService
- [x] 兼容PyTorch版本接口
- [x] 内存监控和性能优化

### ✅ 阶段3: 服务集成（已完成）

- [x] 修改live_audio_stream_service.py
- [x] 支持动态后端切换
- [x] 环境变量控制

### ✅ 阶段4: 测试工具（已完成）

- [x] 模型验证脚本
- [x] 性能对比脚本
- [x] 磁盘清理脚本

### ✅ 阶段5: 文档（已完成）

- [x] 部署指南
- [x] 方案总结
- [x] 故障排除说明

### ⏳ 阶段6: 生产验证（待用户执行）

- [ ] 在测试环境运行1周
- [ ] 对比准确率和稳定性
- [ ] 生产环境部署

### 🔮 阶段7: 优化清理（可选）

- [ ] 卸载PyTorch依赖（节省3-4GB）
- [ ] 长期监控性能指标
- [ ] 根据实际情况调整配置

## 💡 使用建议

### 何时使用ONNX版本

✅ **推荐使用场景:**
- 服务器内存紧张（< 10GB）
- 需要降低资源占用
- CPU推理场景
- 稳定的ASR需求

⚠️  **暂时保留PyTorch场景:**
- 需要热词支持（ONNX版本暂未实现）
- 需要自定义模型微调
- GPU加速场景（需额外配置）

### 性能调优

**4核服务器配置:**
```python
inter_op_num_threads = 2
intra_op_num_threads = 2
```

**8核服务器配置:**
```python
inter_op_num_threads = 4
intra_op_num_threads = 4
```

## 🔍 监控指标

### 内存监控

```
正常: ✅ ONNX运行正常: 内存2500MB, 调用500次
警告: ⚠️  ONNX内存占用: 3200MB (调用次数: 1000)
严重: ❌ ONNX内存占用严重: 4200MB，建议重启
```

### 性能指标

| 指标 | 目标值 | 说明 |
|-----|-------|------|
| 实时因子 | < 0.5x | 良好 |
| 推理时间 | < 200ms | 1秒音频 |
| 内存占用 | < 3GB | 峰值 |
| 初始化时间 | < 10s | 首次加载 |

## 🐛 故障排除

### 常见问题

**Q1: ONNX模型导出失败**
```bash
# 检查PyTorch和ONNX版本
pip list | grep -E "torch|onnx"

# 确保模型已下载
ls -lh server/models/.cache/modelscope/iic/SenseVoiceSmall
```

**Q2: 推理结果为空**
```bash
# 验证模型
python scripts/verify_onnx_model.py

# 检查输入音频格式（PCM16, 16kHz, 单声道）
```

**Q3: 性能不如预期**
```bash
# 调整线程数配置
# 编辑 server/modules/ast/sensevoice_onnx_service.py

# 查看CPU占用
top -p $(pgrep -f uvicorn)
```

### 回退方案

```bash
# 立即回退到PyTorch
export SENSEVOICE_USE_ONNX=false
./scripts/构建与启动/start-backend.sh
```

## 📈 预期效果

### 短期（1天）
- ✅ ONNX模型成功导出和验证
- ✅ 服务正常启动和运行
- ✅ 基本功能测试通过

### 中期（1周）
- ✅ 准确率对比验证
- ✅ 稳定性测试
- ✅ 内存占用降低40%

### 长期（1月）
- ✅ 可选择卸载PyTorch
- ✅ 磁盘空间节省3-4GB
- ✅ 系统稳定性提升

## 🎓 技术原理

### ONNX优势

1. **轻量级推理引擎**
   - 不需要完整的深度学习框架
   - 内存占用更少

2. **优化的计算图**
   - 编译时优化
   - 减少运行时开销

3. **跨平台支持**
   - CPU优化
   - 可扩展到GPU（需配置）

### VAD策略

ONNX版本使用**轻量级RMS VAD**:
```python
# 快速静音检测
rms = np.sqrt(np.mean(speech ** 2))
if rms < threshold:
    return silence
```

优势:
- ✅ 几乎零内存开销
- ✅ 实时性能极佳
- ✅ 适合直播场景

## 📚 参考资料

- [FunASR官方文档](https://github.com/alibaba-damo-academy/FunASR)
- [ONNX Runtime文档](https://onnxruntime.ai/docs/)
- [PyTorch ONNX Export](https://pytorch.org/docs/stable/onnx.html)

## 🤝 贡献指南

改进建议:
1. 优化ONNX模型导出流程
2. 添加热词支持到ONNX版本
3. 实现GPU加速配置
4. 完善监控和告警

## 📝 更新日志

### v1.0.0 (2025-01-14)
- ✅ 完成ONNX模型导出脚本
- ✅ 实现ONNX适配器服务
- ✅ 集成到现有服务架构
- ✅ 提供完整测试和部署文档

---

**维护者**: 提猫直播助手团队  
**最后更新**: 2025-01-14  
**状态**: ✅ 已完成开发，待生产验证

