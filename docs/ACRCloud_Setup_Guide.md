# ACRCloud 音乐识别服务配置指南

## 概述

ACRCloud 是一个专业的音频识别服务，可以识别背景音乐、歌曲等音频内容。本项目集成了 ACRCloud 服务，用于在直播过程中自动识别背景音乐，并相应调整音频处理策略。

## 功能特性

- **实时音乐识别**: 自动识别直播中的背景音乐
- **智能音频过滤**: 检测到音乐时自动调整VAD参数，减少误识别
- **音乐信息展示**: 显示识别到的歌曲名称、艺术家等信息
- **可配置参数**: 支持调整识别精度、频率等参数

## 注册 ACRCloud 账号

1. 访问 [ACRCloud 官网](https://www.acrcloud.com/)
2. 点击 "Sign Up" 注册账号
3. 登录后进入控制台
4. 创建新的项目 (Project)
5. 选择 "Audio & Video Recognition" 服务类型
6. 获取以下配置信息：
   - **Host**: 服务器地址 (如: identify-eu-west-1.acrcloud.com)
   - **Access Key**: 访问密钥
   - **Access Secret**: 访问密钥

## 安装依赖

ACRCloud 功能需要安装官方 Python SDK：

```bash
# 进入项目目录
cd d:\gsxm\timao-douyin-live-manager

# 安装 ACRCloud SDK
pip install acrcloud_sdk_python

# 或者使用项目内置的 SDK
pip install -e ./acrcloud_sdk_python
```

## 配置环境变量

在项目根目录的 `.env` 文件中添加以下配置：

```bash
# ==================== ACRCloud 音乐识别配置 ====================

# 启用 ACRCloud 音乐识别服务
ACR_ENABLE=1

# ACRCloud 服务配置（需要注册 ACRCloud 账号获取）
ACR_HOST=identify-eu-west-1.acrcloud.com
ACR_ACCESS_KEY=your_access_key_here
ACR_SECRET_KEY=your_secret_key_here

# ACRCloud 识别参数
ACR_MIN_SCORE=0.65          # 最小匹配分数 (0.0-1.0)
ACR_TIMEOUT=10              # 识别超时时间(秒)

# 实时音频处理参数
LIVE_ACR_SEGMENT_SEC=10     # 音频片段长度(秒) 4-15
LIVE_ACR_COOLDOWN_SEC=25    # 识别间隔(秒) 5-120
LIVE_ACR_MATCH_HOLD_SEC=6   # 匹配保持时间(秒) 1-60
```

### 配置说明

| 参数 | 说明 | 默认值 | 范围 |
|------|------|--------|------|
| `ACR_ENABLE` | 是否启用 ACRCloud 服务 | 0 | 0/1 |
| `ACR_HOST` | ACRCloud 服务器地址 | - | - |
| `ACR_ACCESS_KEY` | 访问密钥 | - | - |
| `ACR_SECRET_KEY` | 访问密钥 | - | - |
| `ACR_MIN_SCORE` | 最小匹配分数 | 0.65 | 0.0-1.0 |
| `ACR_TIMEOUT` | 识别超时时间 | 10 | 3-60 |
| `LIVE_ACR_SEGMENT_SEC` | 音频片段长度 | 10 | 4-15 |
| `LIVE_ACR_COOLDOWN_SEC` | 识别间隔 | 25 | 5-120 |
| `LIVE_ACR_MATCH_HOLD_SEC` | 匹配保持时间 | 6 | 1-60 |

## 测试配置

创建测试脚本验证 ACRCloud 配置：

```python
# test_acrcloud.py
import os
from AST_module.acrcloud_client import load_acr_client_from_env

# 测试 ACRCloud 配置
client, error = load_acr_client_from_env()

if client:
    print("✅ ACRCloud 配置成功")
    print(f"服务器: {os.getenv('ACR_HOST')}")
    print(f"最小分数: {os.getenv('ACR_MIN_SCORE', '0.65')}")
else:
    print(f"❌ ACRCloud 配置失败: {error}")
```

运行测试：

```bash
cd server
python test_acrcloud.py
```

## 使用方式

### 1. 启动服务

配置完成后，重启 FastAPI 服务：

```bash
cd server
python -m uvicorn app.main:app --host 0.0.0.0 --port 10090 --reload
```

### 2. 查看状态

通过 API 查看 ACRCloud 状态：

```bash
curl http://localhost:10090/api/live_audio/status
```

返回结果包含音乐识别信息：

```json
{
  "advanced": {
    "music_last_title": "歌曲名称",
    "music_last_score": 0.85,
    "music_last_detected_at": 1635724800.0,
    "music_guard_active": true,
    "music_match_hold_until": 1635724806.0
  }
}
```

### 3. 实时监控

在直播过程中，系统会：

1. **自动识别音乐**: 每隔 25 秒尝试识别背景音乐
2. **调整音频处理**: 检测到音乐时提高音乐过滤强度
3. **显示音乐信息**: 在状态接口中显示识别到的歌曲信息
4. **智能过滤**: 在音乐播放期间减少语音误识别

## 性能优化

### 1. 参数调优

根据使用场景调整参数：

**高精度场景**（音乐识别要求高）：
```bash
ACR_MIN_SCORE=0.8
LIVE_ACR_SEGMENT_SEC=12
LIVE_ACR_COOLDOWN_SEC=20
```

**低延迟场景**（实时性要求高）：
```bash
ACR_MIN_SCORE=0.6
LIVE_ACR_SEGMENT_SEC=8
LIVE_ACR_COOLDOWN_SEC=30
```

**节省成本场景**（减少 API 调用）：
```bash
ACR_MIN_SCORE=0.7
LIVE_ACR_SEGMENT_SEC=15
LIVE_ACR_COOLDOWN_SEC=60
```

### 2. 监控使用量

定期检查 ACRCloud 控制台的使用统计，避免超出配额。

## 故障排除

### 1. 常见错误

**错误**: `acrcloud_sdk_python 未安装`
```bash
# 解决方案
pip install acrcloud_sdk_python
```

**错误**: `缺少 ACR_HOST / ACR_ACCESS_KEY / ACR_SECRET_KEY 配置`
```bash
# 检查 .env 文件配置
cat .env | grep ACR_
```

**错误**: `ACRCloud 识别失败`
```bash
# 检查网络连接和密钥是否正确
curl -I https://identify-eu-west-1.acrcloud.com
```

### 2. 调试模式

启用详细日志：

```bash
# 在 .env 中添加
DEBUG=true
PYTHON_ENV=development
```

查看日志：

```bash
tail -f logs/uvicorn.log | grep ACRCloud
```

### 3. 禁用 ACRCloud

如果遇到问题，可以临时禁用：

```bash
# 在 .env 中设置
ACR_ENABLE=0
```

## 最佳实践

1. **合理设置识别间隔**: 避免频繁调用 API 导致费用过高
2. **调整匹配分数**: 根据实际需求平衡准确性和召回率
3. **监控使用量**: 定期检查 API 调用次数和费用
4. **备份配置**: 保存好 Access Key 和 Secret Key
5. **测试验证**: 在生产环境使用前充分测试

## 相关文档

- [ACRCloud 官方文档](https://docs.acrcloud.com/)
- [Python SDK 文档](https://github.com/acrcloud/acrcloud_sdk_python)
- [音频调优指南](./live_audio_tuning.md)