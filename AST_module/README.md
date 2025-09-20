# AST_module - 音频语音转录模块

提猫直播助手的核心语音识别模块，提供实时音频采集、处理和转录功能。

## 🎯 功能特性

- 🎤 **实时音频采集**: 支持麦克风音频流实时采集
- 🔧 **音频预处理**: 自动格式转换、降噪、标准化
- 🗣️ **中文语音识别**: 基于VOSK本地模型，支持流式转录
- 📊 **高精度转录**: 置信度评估和质量控制
- ⚡ **异步处理**: 全异步架构，低延迟响应
- 🔌 **回调支持**: 灵活的转录结果回调机制

## 📦 安装依赖

```bash
# 核心依赖
pip install pyaudio numpy scipy aiohttp

# 可选: VOSK (如果需要直接集成)
pip install vosk
```

## 🚀 快速开始

### 基础使用

```python
import asyncio
from AST_module import ASTService, TranscriptionResult

async def main():
    # 创建AST服务
    ast = ASTService()
    
    # 设置转录回调
    def on_transcription(result: TranscriptionResult):
        print(f"转录: {result.text} (置信度: {result.confidence:.2f})")
    
    ast.add_transcription_callback("main", on_transcription)
    
    try:
        # 初始化服务
        if await ast.initialize():
            # 开始转录
            await ast.start_transcription("room_123")
            
            # 运行10秒
            await asyncio.sleep(10)
            
            # 停止转录
            await ast.stop_transcription()
    finally:
        await ast.cleanup()

# 运行
asyncio.run(main())
```

### 自定义配置

```python
from AST_module import ASTService, create_ast_config

# 创建自定义配置
config = create_ast_config(
    model_path="./custom-model",
    sample_rate=16000,
    chunk_duration=2.0,      # 2秒音频块
    min_confidence=0.7,      # 更高置信度要求
    save_audio=True          # 保存音频文件用于调试
)

# 使用自定义配置
ast = ASTService(config)
```

### 集成到FastAPI

```python
from fastapi import FastAPI, WebSocket
from AST_module import get_ast_service

app = FastAPI()
ast = get_ast_service()

@app.on_event("startup")
async def startup():
    await ast.initialize()

@app.on_event("shutdown") 
async def shutdown():
    await ast.cleanup()

@app.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    await websocket.accept()
    
    # 设置回调发送转录结果
    def send_result(result):
        asyncio.create_task(
            websocket.send_json({
                "text": result.text,
                "confidence": result.confidence,
                "timestamp": result.timestamp
            })
        )
    
    ast.add_transcription_callback(f"ws_{id(websocket)}", send_result)
    
    try:
        await ast.start_transcription("live_room")
        # 保持连接
        while True:
            await websocket.receive_text()
    finally:
        ast.remove_transcription_callback(f"ws_{id(websocket)}")
        await ast.stop_transcription()
```

## 🏗️ 架构设计

```
AST_module/
├── ast_service.py      # 主服务类
├── audio_capture.py    # 音频采集和处理
├── vosk_service_v2.py  # VOSK语音识别服务
├── config.py          # 配置管理
├── __init__.py        # 模块入口
├── ast_design.md      # 架构设计文档
└── README.md          # 使用说明
```

### 核心组件

1. **ASTService**: 主服务类，协调所有组件
2. **AudioCapture**: 音频采集器，处理麦克风输入
3. **AudioProcessor**: 音频预处理器，格式转换和优化
4. **VoskServiceV2**: VOSK语音识别引擎封装
5. **AudioBuffer**: 音频缓冲区，用于数据管理

## 🔧 配置选项

### AudioConfig

```python
@dataclass
class AudioConfig:
    sample_rate: int = 16000        # 采样率 (Hz)
    channels: int = 1               # 声道数 (1=单声道)
    chunk_size: int = 1024          # 音频块大小
    format: int = pyaudio.paInt16   # 音频格式
    input_device_index: int = None  # 输入设备索引
```

### ASTConfig

```python
@dataclass  
class ASTConfig:
    audio_config: AudioConfig           # 音频配置
    vosk_model_path: str               # VOSK模型路径
    vosk_server_port: int = 2700       # VOSK服务端口
    chunk_duration: float = 1.0        # 音频块时长(秒)
    min_confidence: float = 0.5        # 最小置信度阈值
    buffer_duration: float = 10.0      # 缓冲区时长(秒)
    save_audio_files: bool = False     # 是否保存音频文件
    audio_output_dir: str = "./logs"   # 音频输出目录
```

## 📊 转录结果

```python
@dataclass
class TranscriptionResult:
    text: str              # 转录文本
    confidence: float      # 置信度 (0-1)
    timestamp: float       # 时间戳
    duration: float        # 音频时长
    is_final: bool        # 是否为最终结果
    words: list           # 词级别信息
    room_id: str          # 房间ID
    session_id: str       # 会话ID
```

## 🚀 性能优化

### 1. 音频处理优化

```python
# 减少音频块大小以降低延迟
config = create_ast_config(chunk_duration=0.5)

# 提高采样率以改善质量
config = create_ast_config(sample_rate=22050)
```

### 2. 置信度过滤

```python
# 提高置信度阈值过滤噪音
config = create_ast_config(min_confidence=0.8)
```

### 3. 缓冲区调优

```python
# 减少缓冲区大小以节省内存
config = create_ast_config(buffer_duration=5.0)
```

## 🔍 调试和监控

### 启用音频文件保存

```python
config = create_ast_config(save_audio=True)
```

### 查看服务状态

```python
status = ast.get_status()
print(f"转录次数: {status['stats']['successful_transcriptions']}")
print(f"平均置信度: {status['stats']['average_confidence']:.2f}")
```

### 日志配置

```python
import logging
logging.basicConfig(level=logging.INFO)

# AST模块会输出详细的日志信息
```

## ⚠️ 注意事项

1. **VOSK模型**: 确保 `vosk-model-cn-0.22` 模型文件存在
2. **音频设备**: 确保麦克风设备可用且有权限访问
3. **资源管理**: 使用完毕后务必调用 `cleanup()` 清理资源
4. **并发限制**: 同一时间只能运行一个转录会话
5. **网络依赖**: VOSK服务模式需要本地网络连接

## 🐛 故障排除

### 常见问题

1. **音频设备错误**
```python
# 列出可用设备
ast.audio_capture._list_audio_devices()
```

2. **VOSK模型加载失败**
```bash
# 检查模型路径
ls -la ./vosk-api/vosk-model-cn-0.22/
```

3. **转录结果为空**
- 检查麦克风权限
- 调整置信度阈值
- 确认音频输入音量

## 📈 性能指标

- **转录延迟**: < 2秒 (1秒音频块)
- **内存使用**: ~1.5GB (包含VOSK模型)
- **CPU使用**: 10-30% (取决于音频处理量)
- **准确率**: 80-95% (取决于音频质量和语言环境)

## 🤝 集成示例

查看 `/docs/` 目录下的完整集成示例：
- FastAPI后端集成
- WebSocket实时通信
- 前端JavaScript客户端

---

**版本**: v1.0.0  
**维护**: 提猫科技AST团队  
**更新**: 2025-01-20