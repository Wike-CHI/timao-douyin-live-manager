# SenseVoice 修复后启动指南

## 审查人

叶维哲

## 🎉 修复完成

SenseVoice 模型路径配置已全部修复！现在可以正常使用实时音频转写功能。

## 📋 修复内容

### 问题
- ❌ VAD 模型路径错误：`server/models/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch`
- ❌ 导致 SenseVoice 初始化失败

### 解决方案
- ✅ 修正为正确路径：`server/modules/models/.cache/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch`
- ✅ 修复了 5 个文件中的路径配置
- ✅ 所有测试通过

## 🚀 启动步骤

### 方法 1：使用一键启动（推荐）

```bash
# 确保虚拟环境已激活
.venv\Scripts\activate

# 一键启动
npm run dev
```

### 方法 2：分步启动

```bash
# 1. 启动后端（端口 11111）
npm run dev:backend

# 2. 在新终端启动前端（端口 10065）
npm run dev:renderer

# 3. 在新终端启动 Electron
npm run dev:electron
```

### 方法 3：使用一体化启动器

```bash
npm run start:integrated
```

## ✅ 验证 SenseVoice

### 1. 检查后端健康

```bash
curl http://127.0.0.1:11111/api/live_audio/health
```

**预期响应**：
```json
{
  "healthy": true,
  "model_present": true,
  "vad_present": true,
  "model_dir": "D:\\gsxm\\timao-douyin-live-manager\\server\\modules\\models\\.cache\\models\\iic\\SenseVoiceSmall",
  "vad_dir": "D:\\gsxm\\timao-douyin-live-manager\\server\\modules\\models\\.cache\\models\\iic\\speech_fsmn_vad_zh-cn-16k-common-pytorch"
}
```

### 2. 运行测试脚本

```bash
python tests/integration/test_sensevoice_model_paths.py
```

**预期输出**：
```
✅ 所有测试通过！模型路径配置正确。
```

### 3. 测试实时转写

1. 启动应用后，进入"直播管理"页面
2. 输入抖音直播间 URL
3. 点击"开始录制"
4. 检查日志中是否有：
   ```
   ✅ SenseVoice model initialized successfully
   ```
5. 等待音频转写结果

## 📊 系统要求

### 最低配置

- **内存**: 8GB RAM（推荐 16GB）
- **存储**: 2GB 可用空间（用于模型缓存）
- **网络**: 首次启动需联网下载模型

### 模型大小

- SenseVoiceSmall: ~300MB
- VAD 模型: ~150MB
- 总计: ~500MB

## 🔧 常见问题

### Q1: 首次启动很慢？

**A**: 首次启动会从 ModelScope 下载模型，需要 5-10 分钟。请耐心等待。

**日志示例**：
```
[Backend] Downloading Model from https://www.modelscope.cn to directory: D:\gsxm\timao-douyin-live-manager\server\modules\models\.cache\models\iic\SenseVoiceSmall
```

### Q2: 下载失败？

**A**: 检查网络连接，确保能访问 `https://www.modelscope.cn`

**解决方案**：
1. 检查网络连接
2. 关闭代理/VPN（可能干扰下载）
3. 重启后端服务重试

### Q3: 模型已下载但仍然失败？

**A**: 检查模型文件完整性

```bash
# 检查 SenseVoiceSmall 模型文件
dir "D:\gsxm\timao-douyin-live-manager\server\modules\models\.cache\models\iic\SenseVoiceSmall\model.pt"

# 检查 VAD 模型文件
dir "D:\gsxm\timao-douyin-live-manager\server\modules\models\.cache\models\iic\speech_fsmn_vad_zh-cn-16k-common-pytorch\model.pt"
```

如果文件缺失或损坏：
```bash
# 删除缓存目录
Remove-Item -Recurse -Force "server\modules\models\.cache"

# 重启后端，重新下载
npm run dev:backend
```

### Q4: 还有旧的模型路径？

**A**: 测试显示发现旧路径，可以安全删除：

```bash
# 删除旧路径（如果存在）
Remove-Item -Recurse -Force "server\models\models"
```

**注意**：删除后不会影响功能，因为新路径已正确配置。

## 📈 性能优化

### 加快后续启动速度

模型下载完成后，后续启动会快很多：
- SenseVoice 初始化: 约 **5-10 秒**
- 总启动时间: 约 **15-20 秒**

### 内存使用

- SenseVoice 运行时: 约 **1-2GB RAM**
- 建议空闲内存: 至少 **4GB**

## 🎯 下一步

1. ✅ 系统已启动并运行
2. ✅ SenseVoice 已正确初始化
3. ✅ 可以开始使用实时转写功能

### 开始使用

1. 打开应用（Electron 窗口）
2. 进入"直播管理"页面
3. 输入抖音直播间 URL
4. 点击"开始录制"
5. 实时查看转写结果

## 📚 相关文档

- [SenseVoice 模型路径修复说明](../问题修复/SenseVoice模型路径修复说明.md)
- [演示测试快速启动](./演示测试快速启动.md)
- [端口硬编码配置](../配置说明/端口硬编码配置.md)

## 🆘 需要帮助？

如果遇到问题：

1. **查看日志**：检查后端日志中的错误信息
2. **运行测试**：`python tests/integration/test_sensevoice_model_paths.py`
3. **检查健康**：`curl http://127.0.0.1:11111/api/live_audio/health`
4. **重启服务**：`npm run dev`

## ✨ 总结

经过修复后：
- ✅ 5 个文件的路径已全部修正
- ✅ 所有测试通过
- ✅ 模型自动下载和加载正常
- ✅ 实时转写功能可用

**现在可以正常使用所有功能了！**

