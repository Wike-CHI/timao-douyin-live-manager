# AST_module - 本地语音采集与转写

`AST_module` 提供提猫直播助手的语音采集、预处理与 SenseVoice/FunASR 转写服务。模块聚焦于本地部署场景，支持实时音频推理以及调试辅助工具。

## 功能一览
- 🎤 麦克风实时采集与环形缓冲
- 🧹 采样率与位深转换、基础降噪
- 🗣️ SenseVoice 小型模型本地识别
- ⚙️ 可插拔回调与任务管理
- 🔄 模拟转写服务用于降级与测试

## 关键文件
- `ast_service.py`：模块统一入口，负责生命周期管理
- `audio_capture.py`：音频采集、缓冲与分片
- `sensevoice_service.py`：FunASR/SenseVoice 推理封装
- `mock_transcription.py`：无模型环境下的占位实现
- `config.py`：配置模板及生成辅助方法

## 快速体验
```python
import asyncio
from AST_module import ASTService, create_ast_config, TranscriptionResult

async def main():
    config = create_ast_config(chunk_duration=1.0, min_confidence=0.5)
    service = ASTService(config)

    def handle_result(result: TranscriptionResult) -> None:
        print(f"转录: {result.text} (置信度: {result.confidence:.2f})")

    service.add_transcription_callback("demo", handle_result)

    try:
        await service.initialize()
        await service.start_transcription(room_id="demo-room")
        await asyncio.sleep(10)
    finally:
        await service.stop_transcription()
        await service.cleanup()

asyncio.run(main())
```

## 常用配置
`create_ast_config` 支持下列常用参数：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `model_id` | SenseVoice/FunASR 模型名称 | `iic/SenseVoiceSmall` |
| `chunk_duration` | 单次推理音频时长 (秒) | `1.0` |
| `min_confidence` | 结果置信度过滤阈值 | `0.5` |
| `save_audio` | 是否落盘原始音频 | `False` |

若需进一步定制可直接修改 `AST_module/config.py`。

## 与 FastAPI 集成示例
```python
from fastapi import FastAPI
from AST_module import get_ast_service

app = FastAPI()
ast_service = get_ast_service()

@app.on_event("startup")
async def startup() -> None:
    await ast_service.initialize()

@app.on_event("shutdown")
async def shutdown() -> None:
    await ast_service.cleanup()
```

## 降级策略
SenseVoice 依赖 FunASR 生态。若模型或依赖加载失败，`AST_service` 会自动切换到 `mock_transcription`，保证接口可用并提供带标记的占位结果，便于前端联调。

## 调试建议
- 将 `save_audio` 设为 `True` 以捕获输入切片，结合 `audio_logs/` 中的文件排查音频质量问题。
- 开启 `DEBUG` 级别日志可查看模型初始化与推理耗时。
- 如果需要自定义模型路径，可在 `config.py` 中新增对应的 `model_id` 映射或直接修改 `SenseVoiceConfig`。

---

如需进一步扩展（例如热词、长音频拼接），建议在 `sensevoice_service.py` 内新增策略，并通过 `ASTService` 的回调分发结果。
