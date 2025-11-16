# ONNX SenseVoice 快速使用指南

## 🚀 3分钟快速开始

### 步骤1: 导出模型 (首次)

```bash
cd /www/wwwroot/wwwroot/timao-douyin-live-manager
python scripts/export_models_to_onnx.py
```

**预期时间**: 2-5分钟  
**输出位置**: `server/models/onnx/sensevoice_small.onnx`

### 步骤2: 验证模型

```bash
python scripts/verify_onnx_model.py
```

**预期输出**:
```
✅ 验证通过! ONNX模型可以正常工作
   平均推理时间: 150ms
   实时因子: 0.15x ✅ 良好
```

### 步骤3: 启用ONNX

```bash
# 设置环境变量
export SENSEVOICE_USE_ONNX=true

# 重启服务
./scripts/构建与启动/start-backend.sh
```

### 步骤4: 确认运行

查看日志确认ONNX后端已启用:

```bash
tail -f logs/backend.log | grep ONNX
```

预期日志:
```
[INFO] 🚀 使用ONNX后端进行语音转写
[INFO] ✅ ONNX模型加载成功
[INFO] ✅ SenseVoice 初始化成功 (后端: ONNX)
```

## ✅ 完成！

现在您的服务正在使用ONNX后端，享受：
- 💾 **40%更少的内存占用**
- 📦 **更小的磁盘空间**
- ⚡ **相同或更快的推理速度**

## 🔄 切换回PyTorch

如果需要回退:

```bash
export SENSEVOICE_USE_ONNX=false
./scripts/构建与启动/start-backend.sh
```

## 📊 性能对比

```bash
# 可选：运行性能测试
python scripts/compare_pytorch_onnx_accuracy.py
```

## 💡 常见问题

**Q: 导出失败怎么办？**  
A: 确保PyTorch模型已下载到本地，重试导出脚本

**Q: 推理结果不正确？**  
A: 运行验证脚本检查模型，考虑重新导出

**Q: 内存还是很高？**  
A: 运行清理脚本: `bash scripts/cleanup_disk.sh`

## 📚 详细文档

- [完整部署指南](./ONNX部署指南.md)
- [方案总结](./ONNX优化方案总结.md)

---

**遇到问题？** 查看日志或参考详细文档中的故障排除部分。

