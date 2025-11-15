# SenseVoice 模型路径修复说明

## 审查人

叶维哲

## 问题描述

**错误信息**：
```
Failed to load SenseVoice model: D:\gsxm\timao-douyin-live-manager\server\models\models\iic\speech_fsmn_vad_zh-cn-16k-common-pytorch is not registered
```

**根本原因**：
VAD 模型路径配置错误。多个文件中使用了错误的路径：
- 错误路径：`server/models/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch`
- 正确路径：`server/modules/models/.cache/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch`

## 问题分析

### 路径计算错误

在多个文件中，`project_root` 的计算方式不正确：

```python
# 错误示例
project_root = Path(__file__).resolve().parents[1]
# 在 server/modules/ast/sensevoice_service.py 中
# parents[1] 指向 server/modules/
# 导致路径变成：server/modules/models/models/iic/...

# 正确应该是
project_root = Path(__file__).resolve().parents[2]
# parents[2] 指向 server/
# 路径应该是：server/modules/models/.cache/models/iic/...
```

### FunASR 缓存机制

FunASR 从 ModelScope 下载模型时，会自动保存到：
```
server/modules/models/.cache/models/iic/
├── SenseVoiceSmall/
│   └── model.pt
└── speech_fsmn_vad_zh-cn-16k-common-pytorch/
    └── model.pt
```

但我们的代码在错误的位置查找模型。

## 修复内容

### 修改的文件列表

1. **`server/modules/ast/sensevoice_service.py`**
   - 修复 `_resolve_small_model_id()` 函数
   - 修复 `_resolve_vad_model_id()` 函数
   - 将 `project_root` 从 `parents[1]` 改为 `parents[2]`
   - 路径从 `models/models/iic/` 改为 `modules/models/.cache/models/iic/`

2. **`server/app/services/live_audio_stream_service.py`**
   - 修复 `_resolve_vad_model_id()` 函数
   - 路径从 `server/models/models/iic/` 改为 `server/modules/models/.cache/models/iic/`

3. **`server/app/api/live_audio.py`**
   - 修复健康检查 API 中的路径
   - 更新 `model_dir` 和 `vad_dir` 的路径

4. **`server/utils/bootstrap.py`**
   - 修复 `ensure_models()` 函数
   - 更新模型检查和下载的路径
   - 更新错误提示信息中的路径

5. **`server/modules/ast/config.py`**
   - 修复 `_autodetect_vad_model()` 函数
   - 路径从 `models/iic/` 改为 `.cache/models/iic/`

### 修复前后对比

#### 修复前（错误）

```python
# sensevoice_service.py
project_root = Path(__file__).resolve().parents[1]  # ❌ 指向 server/modules/
local_vad = project_root / "models" / "models" / "iic" / "speech_fsmn_vad_zh-cn-16k-common-pytorch"
# 结果：server/modules/models/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch
```

#### 修复后（正确）

```python
# sensevoice_service.py
project_root = Path(__file__).resolve().parents[2]  # ✅ 指向 server/
cache_vad = project_root / "modules" / "models" / ".cache" / "models" / "iic" / "speech_fsmn_vad_zh-cn-16k-common-pytorch"
# 结果：server/modules/models/.cache/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch
```

## 验证步骤

### 1. 检查模型是否已下载

```bash
# 检查 SenseVoiceSmall 模型
dir /s /b "D:\gsxm\timao-douyin-live-manager\server\modules\models\.cache\models\iic\SenseVoiceSmall"

# 检查 VAD 模型
dir /s /b "D:\gsxm\timao-douyin-live-manager\server\modules\models\.cache\models\iic\speech_fsmn_vad_zh-cn-16k-common-pytorch"
```

### 2. 测试 API 健康检查

```bash
# 启动后端服务
npm run dev:backend

# 在另一个终端测试
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

### 3. 测试实时音频转写

启动直播录制后，检查日志是否有 SenseVoice 初始化成功的信息：
```
✅ SenseVoice model initialized successfully
```

## 相关文件

### 模型目录结构

```
server/
└── modules/
    └── models/
        └── .cache/
            └── models/
                └── iic/
                    ├── SenseVoiceSmall/
                    │   ├── model.pt
                    │   ├── configuration.json
                    │   └── ...
                    └── speech_fsmn_vad_zh-cn-16k-common-pytorch/
                        ├── model.pt
                        ├── configuration.json
                        └── ...
```

### 下载脚本

如果模型未自动下载，可以手动运行：
```bash
# 下载 SenseVoiceSmall
python server/tools/download_sensevoice.py

# 下载 VAD 模型
python server/tools/download_vad_model.py
```

## 测试结果

修复后，SenseVoice 应该能够正确初始化：

```
[Backend] 2025-11-14 22:xx:xx - server.modules.ast.sensevoice_service - INFO - Loading SenseVoice model: iic/SenseVoiceSmall
[Backend] 2025-11-14 22:xx:xx - root - INFO - Loading pretrained params from D:\gsxm\timao-douyin-live-manager\server\modules\models\.cache\models\iic\SenseVoiceSmall\model.pt
[Backend] 2025-11-14 22:xx:xx - root - INFO - Loading ckpt: ..., status: <All keys matched successfully>
[Backend] 2025-11-14 22:xx:xx - root - INFO - Building VAD model.
[Backend] 2025-11-14 22:xx:xx - server.modules.ast.sensevoice_service - INFO - ✅ SenseVoice model initialized successfully
```

## 注意事项

1. **首次启动会下载模型**：如果模型未预先下载，FunASR 会从 ModelScope 自动下载，需要等待几分钟
2. **网络连接**：确保能够访问 `https://www.modelscope.cn`
3. **磁盘空间**：确保有足够的磁盘空间（约 500MB）
4. **Python 依赖**：确保已安装 `funasr` 和相关依赖

## 后续建议

1. **统一路径管理**：考虑创建一个中心化的路径配置模块
2. **模型预下载**：在部署脚本中预先下载模型，避免首次启动延迟
3. **错误提示优化**：如果模型加载失败，提供更清晰的错误信息和解决方案

## 总结

这次修复解决了 SenseVoice VAD 模型路径配置错误的问题。关键是：
1. ✅ 正确计算 `project_root`（向上查找到 `server/` 目录）
2. ✅ 使用正确的缓存路径（`.cache/models/iic/`）
3. ✅ 确保所有文件使用一致的路径规范
4. ✅ 让 FunASR 的自动下载机制正常工作

