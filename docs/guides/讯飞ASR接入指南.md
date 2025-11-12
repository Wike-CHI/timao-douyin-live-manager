# 讯飞ASR快速接入指南

## ✅ 已完成

1. **核心代码**: `server/app/services/xfyun_asr.py`
2. **音频转换**: `server/app/utils/audio_converter.py`
3. **测试脚本**: `tests/integration/test_xfyun_asr.py`

---

## 🚀 快速开始（3步完成）

### 1. 配置环境变量

```bash
# server/.env 添加
XFYUN_APPID=3f3b2c39
XFYUN_API_KEY=4cb3fb678a09e3072fb8889d840ef6a2
XFYUN_API_SECRET=MTg2ZTFlZjJlYWYyYzVjZWJhMmIyYzUz
```

### 2. 安装依赖

```bash
# 进入虚拟环境
source .venv/bin/activate

# 安装websockets
pip install websockets

# 安装ffmpeg（音频转换）
apt-get update && apt-get install -y ffmpeg
```

### 3. 测试运行

```bash
# 自动查找测试音频
python tests/integration/test_xfyun_asr.py

# 或指定音频文件
python tests/integration/test_xfyun_asr.py records/sessions/xxx.mp4
```

---

## 📊 API信息

### 免费额度
- **每日时长**: 5小时
- **到期时间**: 2026-11-09
- **计费方式**: 按音频时长（不是用户时间）

### 支持格式
- **输入**: mp3, wav, m4a, mp4（自动转换）
- **输出**: 文本字符串
- **语言**: 中英文 + 202种方言自动识别

---

## 💻 代码示例

### 基础使用

```python
from server.app.services.xfyun_asr import XfyunASR
import asyncio

async def main():
    # 初始化
    asr = XfyunASR(
        app_id="3f3b2c39",
        api_key="4cb3fb678a09e3072fb8889d840ef6a2",
        api_secret="MTg2ZTFlZjJlYWYyYzVjZWJhMmIyYzUz"
    )
    
    # 转写音频文件（自动转换格式）
    from server.app.utils.audio_converter import AudioConverter
    converter = AudioConverter()
    
    # 1. 转换为PCM格式
    pcm_file = converter.convert_to_pcm("input.mp3")
    
    # 2. 调用ASR
    result = await asr.transcribe_audio_file(pcm_file)
    
    print(f"转写结果: {result}")

asyncio.run(main())
```

### 集成到现有服务

```python
# server/app/services/live_audio_service.py

from server.app.services.xfyun_asr import XfyunASR
from server.app.utils.audio_converter import AudioConverter
import os

class LiveAudioService:
    def __init__(self):
        # 初始化讯飞ASR
        self.asr = XfyunASR(
            app_id=os.getenv("XFYUN_APPID"),
            api_key=os.getenv("XFYUN_API_KEY"),
            api_secret=os.getenv("XFYUN_API_SECRET")
        )
        self.converter = AudioConverter()
    
    async def transcribe_audio(self, audio_file: str) -> str:
        """转写音频文件"""
        try:
            # 1. 转换格式
            pcm_file = self.converter.convert_to_pcm(audio_file)
            
            # 2. 调用ASR
            result = await self.asr.transcribe_audio_file(pcm_file)
            
            # 3. 清理临时文件
            if os.path.exists(pcm_file):
                os.remove(pcm_file)
            
            return result
        except Exception as e:
            logger.error(f"转写失败: {e}")
            return ""
```

---

## 🔍 核心功能

### 1. 签名生成（自动）
```python
# 已实现：_generate_signature()
# - 参数升序排序
# - URL编码
# - HMAC-SHA1加密
# - Base64编码
```

### 2. WebSocket通信（自动）
```python
# 已实现：transcribe_audio()
# - 握手连接
# - 发送音频（40ms/1280字节）
# - 接收结果
# - 解析文本
```

### 3. 音频转换（自动）
```python
# 已实现：AudioConverter
# - 任意格式 → PCM
# - 16k采样率
# - 16bit
# - 单声道
```

---

## ⚠️ 注意事项

### 音频格式要求
```
讯飞API要求:
- 格式: PCM (raw audio)
- 采样率: 16000Hz
- 位深: 16bit
- 声道: 单声道 (mono)

已自动处理：
- 输入任意格式（mp3/wav/m4a/mp4）
- 自动转换为PCM
- 自动清理临时文件
```

### 发送速率控制
```python
# 已实现：每40ms发送1280字节
chunk_size = 1280  # 16k * 16bit * 1ch * 40ms = 1280 bytes
await asyncio.sleep(0.04)  # 40ms间隔

# 太快会报错：100001 上传音频速度超出限制
# 太慢会超时：37005 客户端长时间未传音频
```

### 超时控制
```python
# 音频发送间隔超时：15秒
# 结果接收超时：10秒

# 已实现超时处理
response = await asyncio.wait_for(ws.recv(), timeout=10.0)
```

---

## 📈 成本估算

```
当前配置：
- 免费额度：5小时/天
- 到期：2026-11-09（1年）

实际使用：
- 1分钟音频 = 转写时间约10秒
- 每天转写100次×1分钟 = 100分钟 = 1.67小时
- 完全在免费额度内 ✅

超额收费（如果用完免费额度）：
- 按实际音频时长计费
- 预估：￥0.002-0.01/分钟
```

---

## 🐛 常见问题

### 1. WebSocket连接失败
```bash
# 检查网络
curl -I https://office-api-ast-dx.iflyaisol.com/

# 检查防火墙
# 确保允许WebSocket连接
```

### 2. 签名错误（100002）
```python
# 检查：
# 1. APPID是否正确
# 2. APIKey是否正确
# 3. APISecret是否正确
# 4. UTC时间格式是否正确
```

### 3. ffmpeg未安装
```bash
# Ubuntu/Debian
apt-get update && apt-get install -y ffmpeg

# CentOS/RHEL
yum install -y ffmpeg
```

### 4. 转写结果为空
```python
# 可能原因：
# 1. 音频时长太短（<1秒）
# 2. 音频格式不正确
# 3. 音频质量太差（噪音过大）
# 4. 音频内容无人声

# 建议：
# - 使用测试脚本验证
# - 检查音频信息（采样率、声道等）
```

---

## 🎯 下一步

### 立即可测试
```bash
# 1. 配置环境变量（已有）
# 2. 安装依赖
pip install websockets
apt-get install -y ffmpeg

# 3. 运行测试
python tests/integration/test_xfyun_asr.py
```

### 集成到项目
```python
# 在 live_audio_service.py 中
# 替换现有的 transcribe_audio() 方法
# 调用讯飞ASR即可
```

---

## 审查人
叶维哲 - 2025-11-09

