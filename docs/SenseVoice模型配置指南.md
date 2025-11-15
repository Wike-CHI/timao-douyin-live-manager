# SenseVoice + VAD 模型配置指南

**审查人**: 叶维哲  
**最后更新**: 2025-11-14  
**版本**: 1.0

---

## 📋 配置概述

本文档详细说明如何在 PM2 中配置 SenseVoice + VAD 模型，确保服务器启动后能够正确识别和加载语音识别模型。

### 核心配置内容

- ✅ 模型路径环境变量
- ✅ VAD 参数优化配置
- ✅ PyTorch CPU 性能优化
- ✅ 内存限制调整（3GB）
- ✅ ModelScope 缓存配置

---

## 🔧 配置文件修改

### 1. ecosystem.config.js 配置

已在 `ecosystem.config.js` 中添加以下环境变量：

#### 模型路径配置

```javascript
// ========== SenseVoice + VAD 模型配置 ==========
// 模型根目录
MODEL_ROOT: '/www/wwwroot/wwwroot/timao-douyin-live-manager/server/models/models/iic',

// SenseVoice 模型路径
SENSEVOICE_MODEL_PATH: '/www/wwwroot/wwwroot/timao-douyin-live-manager/server/models/models/iic/SenseVoiceSmall',

// VAD 模型路径
VAD_MODEL_PATH: '/www/wwwroot/wwwroot/timao-douyin-live-manager/server/models/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch',

// 模型加载配置
ENABLE_MODEL_PRELOAD: '1',  // 启用模型预加载
MODEL_CACHE_DIR: '/www/wwwroot/wwwroot/timao-douyin-live-manager/.cache/modelscope',
```

#### VAD 参数优化

```javascript
// VAD 参数优化
LIVE_VAD_CHUNK_SEC: '1.6',        // VAD 分块时长
LIVE_VAD_MIN_SILENCE_SEC: '0.50',  // 最小静音时长
LIVE_VAD_MIN_SPEECH_SEC: '0.30',   // 最小语音时长
LIVE_VAD_HANGOVER_SEC: '0.40',     // 挂起时间
LIVE_VAD_MIN_RMS: '0.015',         // RMS 阈值
LIVE_VAD_MUSIC_DETECT: '1',        // 启用音乐检测
```

#### PyTorch 性能优化

```javascript
// PyTorch 配置（优化CPU推理）
OMP_NUM_THREADS: '4',              // OpenMP 线程数
MKL_NUM_THREADS: '4',              // MKL 线程数
PYTORCH_CPU_ALLOC_CONF: 'max_split_size_mb:512',  // PyTorch 内存分配
```

#### ModelScope 配置

```javascript
// ModelScope 配置
MODELSCOPE_CACHE: '/www/wwwroot/wwwroot/timao-douyin-live-manager/.cache/modelscope',
MODELSCOPE_SDK_DEBUG: '0',
```

#### 内存限制调整

```javascript
// 最大内存限制（超过后自动重启）
// SenseVoice Small (~2.3GB) + VAD (~140MB) + 运行内存
// 建议至少 3GB，留有余量避免频繁重启
max_memory_restart: '3G',
```

---

## 🚀 应用配置

### 方法 1: 重新加载配置（推荐）

```bash
# 1. 停止当前服务
pm2 delete timao-backend

# 2. 重新加载配置文件
pm2 start ecosystem.config.js

# 3. 保存配置
pm2 save

# 4. 设置开机自启
pm2 startup
```

### 方法 2: 更新环境变量

```bash
# 重启并更新环境变量
pm2 restart timao-backend --update-env

# 保存配置
pm2 save
```

---

## ✅ 验证配置

### 自动验证（推荐）

运行自动验证脚本：

```bash
cd /www/wwwroot/wwwroot/timao-douyin-live-manager
./scripts/部署与运维/verify-model-config.sh
```

**预期输出**:

```
========================================
SenseVoice + VAD 模型配置验证
========================================

=== 1. 模型文件检查 ===
[1] 检查: SenseVoice 模型目录
   ✅ 通过 - 目录应存在
[2] 检查: SenseVoice model.pt
   ✅ 通过 - 文件应存在（~2.3GB）
...

检查结果: 14/14 项通过
✅ 所有检查通过！模型配置正常。
```

### 手动验证

#### 1. 验证环境变量

```bash
# 查看 PM2 进程环境变量
pm2 env 0 | grep -E "SENSEVOICE|VAD|MODEL"

# 预期输出示例：
# SENSEVOICE_MODEL_PATH=/www/wwwroot/.../SenseVoiceSmall
# VAD_MODEL_PATH=/www/wwwroot/.../speech_fsmn_vad_zh-cn-16k-common-pytorch
# ENABLE_MODEL_PRELOAD=1
# MODEL_ROOT=/www/wwwroot/.../server/models/models/iic
# OMP_NUM_THREADS=4
# MKL_NUM_THREADS=4
```

#### 2. 验证模型文件

```bash
# 检查 SenseVoice 模型
ls -lh server/models/models/iic/SenseVoiceSmall/model.pt
# 预期：文件存在，约 2.3GB

# 检查 VAD 模型
ls -lh server/models/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch/model.pt
# 预期：文件存在，约 140MB

# 查看模型目录大小
du -sh server/models/models/iic/SenseVoiceSmall/
du -sh server/models/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch/
```

#### 3. 验证模型加载

```bash
# 查看启动日志
pm2 logs timao-backend --lines 200 | grep -i "sensevoice\|vad"

# 查看模型初始化成功标志
pm2 logs timao-backend | grep "✅ SenseVoice"

# 预期输出：
# ✅ SenseVoice + VAD 初始化成功（本地PyTorch模型）
```

#### 4. 验证 API 健康

```bash
# 检查后端健康状态
curl http://127.0.0.1:11111/health

# 预期输出：
# {"status":"healthy","service":"提猫直播助手","version":"1.1.0"}
```

---

## 📊 性能指标

### 模型资源占用

| 组件 | 内存占用 | 磁盘空间 | 加载时间 |
|------|---------|---------|---------|
| SenseVoice Small | ~2.3GB | ~2.3GB | 30-60秒 |
| VAD 模型 | ~140MB | ~140MB | 5-10秒 |
| 运行缓存 | ~200MB | ~500MB | - |
| **总计** | **~2.7GB** | **~3GB** | **35-70秒** |

### 系统要求

- **最低内存**: 4GB（系统 1GB + 模型 2.7GB + 其他 0.3GB）
- **推荐内存**: 8GB+
- **磁盘空间**: 至少 5GB 可用
- **CPU**: 4 核心以上（支持 AVX2 指令集更佳）

---

## 🔍 故障排除

### 问题 1: 环境变量未生效

**症状**: `pm2 env 0` 查询不到新增的环境变量

**解决方案**:

```bash
# 1. 删除并重新加载配置
pm2 delete timao-backend
pm2 start ecosystem.config.js

# 2. 保存配置
pm2 save

# 3. 验证
pm2 env 0 | grep SENSEVOICE
```

### 问题 2: 模型加载失败

**症状**: 日志中出现 "❌ SenseVoice初始化失败"

**排查步骤**:

```bash
# 1. 检查模型文件完整性
ls -lh server/models/models/iic/SenseVoiceSmall/model.pt
ls -lh server/models/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch/model.pt

# 2. 检查系统内存
free -h
# 确保至少有 3GB 可用内存

# 3. 检查磁盘空间
df -h

# 4. 重新下载模型（如果文件损坏）
python server/tools/download_sensevoice.py
python server/tools/download_vad_model.py

# 5. 清理缓存后重试
rm -rf .cache/modelscope/*
pm2 restart timao-backend --update-env
```

### 问题 3: 模型加载慢

**症状**: 服务启动需要 1-2 分钟

**说明**: 这是正常现象！SenseVoice Small 模型约 2.3GB，首次加载需要时间。

**优化建议**:

1. 使用 SSD 而非 HDD
2. 确保系统内存充足（至少 4GB 可用）
3. 增加 PyTorch 线程数（已在配置中）
4. 避免与其他高内存进程同时启动

**监控加载进度**:

```bash
# 实时查看日志
pm2 logs timao-backend

# 等待看到以下标志：
# ✅ SenseVoice + VAD 初始化成功（本地PyTorch模型）
```

### 问题 4: 内存不足重启

**症状**: PM2 频繁自动重启，日志显示内存超限

**解决方案**:

```bash
# 1. 检查当前内存使用
pm2 show timao-backend | grep memory

# 2. 如果确实内存不足，调整限制（不推荐低于 2.5GB）
# 编辑 ecosystem.config.js，修改：
max_memory_restart: '4G'  # 从 3GB 增加到 4GB

# 3. 重新加载配置
pm2 delete timao-backend
pm2 start ecosystem.config.js
pm2 save
```

### 问题 5: PyTorch 依赖缺失

**症状**: 日志中出现 torch 相关错误

**解决方案**:

```bash
# 1. 激活虚拟环境
source .venv/bin/activate

# 2. 检查 PyTorch 安装
pip list | grep torch

# 3. 如果缺失，重新安装
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 4. 安装 FunASR
pip install funasr modelscope

# 5. 重启服务
pm2 restart timao-backend --update-env
```

---

## 📚 相关文档

- [PM2使用指南.md](./PM2使用指南.md) - PM2 详细使用说明
- [宝塔面板部署教程.md](./宝塔面板部署教程.md) - 服务器部署指南
- [语音转写参数优化建议.md](../server/语音转写参数优化建议.md) - VAD 参数调优

---

## 🎯 快速检查清单

配置完成后，请确认以下所有项：

- [ ] ✅ `ecosystem.config.js` 已添加模型配置
- [ ] ✅ PM2 服务已重新加载配置
- [ ] ✅ 环境变量验证通过（`pm2 env 0`）
- [ ] ✅ 模型文件存在且完整
- [ ] ✅ 系统内存充足（至少 4GB 可用）
- [ ] ✅ 磁盘空间充足（至少 5GB 可用）
- [ ] ✅ PM2 进程状态为 `online`
- [ ] ✅ 日志中有模型初始化成功标志
- [ ] ✅ API 健康检查通过
- [ ] ✅ `pm2 save` 已执行

---

## 💡 最佳实践

1. **定期监控**: 每周检查一次内存和磁盘使用情况
2. **日志清理**: 每月清理一次 PM2 日志（`pm2 flush`）
3. **缓存管理**: 每季度清理一次 ModelScope 缓存
4. **性能测试**: 更新模型后测试语音识别准确率
5. **备份配置**: 修改配置前备份 `ecosystem.config.js`

---

## 🔄 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| 1.0 | 2025-11-14 | 初始版本，添加完整模型配置 |

---

**问题反馈**: 如遇到问题，请检查 PM2 日志并参考故障排除章节。

