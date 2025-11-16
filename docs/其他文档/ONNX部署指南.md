# SenseVoice ONNX 部署指南

## 概述

本指南介绍如何在服务器上部署ONNX版本的SenseVoice模型，以降低内存占用和提升性能。

## 预期收益

```
内存占用：
├─ PyTorch: 2.5-4GB峰值
└─ ONNX: 1.5-2.5GB峰值 (节省40%)

磁盘占用：
├─ PyTorch模型: 897MB
├─ torch/torchaudio: 3-4GB
└─ ONNX模型: 400-600MB

推理速度：
├─ PyTorch CPU: 基准
└─ ONNX CPU: 持平或提升10-20%
```

## 前提条件

1. **已安装依赖**
   ```bash
   pip install onnxruntime>=1.23.0
   ```

2. **PyTorch SenseVoice已运行过**
   - 确保模型已下载到本地
   - 位置: `server/models/.cache/modelscope/iic/SenseVoiceSmall`

## 部署步骤

### 第1步: 导出ONNX模型

```bash
# 导出模型（需要几分钟）
python scripts/export_models_to_onnx.py
```

**预期输出:**
```
🔧 加载 SenseVoice 模型...
✅ 模型加载成功
🔄 导出 ONNX 模型...
✅ 模型导出成功: sensevoice_small.onnx (500.0MB)
```

**导出位置:** `server/models/onnx/sensevoice_small.onnx`

### 第2步: 验证ONNX模型

```bash
# 验证模型可以正常推理
python scripts/verify_onnx_model.py
```

**预期输出:**
```
✅ 验证通过! ONNX模型可以正常工作
   平均推理时间: 150ms
   实时因子: 0.15x ✅ 良好
```

### 第3步: 启用ONNX后端

#### 方法1: 环境变量（推荐）

```bash
# 设置环境变量
export SENSEVOICE_USE_ONNX=true

# 启动服务
./scripts/构建与启动/start-backend.sh
```

#### 方法2: 修改启动脚本

编辑 `scripts/构建与启动/start-backend.sh`:

```bash
# 在文件开头添加
export SENSEVOICE_USE_ONNX=true
```

### 第4步: 验证运行状态

启动服务后，查看日志确认：

```
✅ 成功标志:
[INFO] 🚀 使用ONNX后端进行语音转写
[INFO] 加载ONNX模型: server/models/onnx/sensevoice_small.onnx
[INFO] ✅ ONNX模型加载成功
[INFO] ✅ SenseVoice 初始化成功 (后端: ONNX)
```

## 性能对比测试

```bash
# 运行性能对比测试
python scripts/compare_pytorch_onnx_accuracy.py

# 使用自己的音频文件测试
python scripts/compare_pytorch_onnx_accuracy.py /path/to/audio.wav
```

## 故障排除

### 问题1: ONNX模型不存在

**错误信息:**
```
❌ ONNX模型不存在: server/models/onnx/sensevoice_small.onnx
```

**解决方案:**
```bash
# 重新导出模型
python scripts/export_models_to_onnx.py
```

### 问题2: onnxruntime未安装

**错误信息:**
```
ModuleNotFoundError: No module named 'onnxruntime'
```

**解决方案:**
```bash
pip install onnxruntime>=1.23.0
```

### 问题3: 推理失败

**检查步骤:**
1. 验证ONNX模型: `python scripts/verify_onnx_model.py`
2. 检查日志中的错误信息
3. 尝试回退到PyTorch版本

### 问题4: 性能不如预期

**优化建议:**
1. 检查CPU线程数配置
2. 确认没有其他进程占用CPU
3. 查看内存监控日志

## 回退到PyTorch版本

如果遇到问题，可以随时回退：

```bash
# 禁用ONNX后端
export SENSEVOICE_USE_ONNX=false

# 或者取消设置
unset SENSEVOICE_USE_ONNX

# 重启服务
./scripts/构建与启动/start-backend.sh
```

## 清理PyTorch依赖（可选）

⚠️ **警告**: 仅在ONNX版本稳定运行至少1周后考虑

如果ONNX版本运行稳定，可以卸载PyTorch以释放磁盘空间：

```bash
# 1. 备份当前环境
pip freeze > requirements_pytorch_backup.txt

# 2. 卸载PyTorch相关包
pip uninstall torch torchaudio torchvision pytorch-wpe -y

# 3. 释放磁盘空间
# 预计释放: 3-4GB
```

**回滚方法:**
```bash
# 从备份恢复PyTorch
pip install torch>=2.0.0 torchaudio>=2.0.0 pytorch-wpe>=0.0.1
```

## 配置参数

### ONNX Runtime 配置

编辑 `server/modules/ast/sensevoice_onnx_service.py`:

```python
@dataclass
class SenseVoiceONNXConfig:
    # 线程配置（根据服务器CPU核心数调整）
    inter_op_num_threads: int = 4  # 操作间线程数
    intra_op_num_threads: int = 4  # 操作内线程数
    
    # VAD配置
    vad_min_rms: float = 0.015  # 音量阈值
    silence_rms_threshold: float = 320.0  # 静音检测阈值
```

**推荐配置:**
- 4核服务器: `inter_op_num_threads=2, intra_op_num_threads=2`
- 8核服务器: `inter_op_num_threads=4, intra_op_num_threads=4`

## 监控指标

### 内存监控

服务会自动监控内存使用：

```
✅ 正常: ONNX运行正常: 内存2500MB, 调用500次
⚠️  警告: ONNX内存占用: 3200MB (调用次数: 1000)
❌ 严重: ONNX内存占用严重: 4200MB，建议重启
```

### 性能指标

- **实时因子**: < 0.5x 良好，< 1.0x 可用
- **推理时间**: < 200ms 良好
- **内存占用**: < 3GB 正常

## 常见问题

### Q1: ONNX和PyTorch准确率一样吗？

A: 理论上应该完全一致。如果有差异：
1. 运行对比测试: `python scripts/compare_pytorch_onnx_accuracy.py`
2. 检查ONNX导出是否完整
3. 考虑重新导出模型

### Q2: 可以在生产环境使用吗？

A: 建议先在测试环境验证至少1周，确认稳定性和准确率后再部署到生产环境。

### Q3: 支持GPU加速吗？

A: 当前配置使用CPU。如果服务器有GPU，可以修改:

```python
# 修改 sensevoice_onnx_service.py
providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
```

### Q4: 模型更新后需要重新导出吗？

A: 是的。如果SenseVoice模型更新，需要重新运行导出脚本。

## 技术支持

遇到问题请提供：
1. 错误日志
2. 系统配置（CPU、内存）
3. Python和依赖包版本
4. ONNX模型文件大小

---

**最后更新**: 2025-01-14
**版本**: 1.0.0

