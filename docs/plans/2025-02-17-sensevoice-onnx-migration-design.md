# SenseVoice ONNX 迁移设计文档

**日期**: 2025-02-17
**状态**: 已批准
**目标**: 将 SenseVoice 语音识别从 FunASR/PyTorch 激进迁移到 sherpa-onnx

## 背景

当前项目使用 FunASR + PyTorch 进行语音识别，依赖体积约 2.7GB，存在以下问题：
- 安装包体积过大
- numba/llvmlite 在 Python 3.11 上有兼容性问题
- 内存占用高，需要复杂的内存管理

## 目标

- 依赖体积减少 90%+ (~2.7GB → ~80MB)
- 完全移除 FunASR/PyTorch 依赖
- 保持现有功能：转录、热词、并发控制
- 遵循 TDD 开发原则

## 架构变更

### 依赖变更

```
移除：
- torch >= 2.0.0
- torchaudio >= 2.0.0
- torchvision >= 0.17.1
- funasr >= 1.2.0
- numba == 0.59.1
- llvmlite == 0.42.0
- librosa >= 0.10.0
- hydra-core >= 1.3.0
- omegaconf >= 2.3.0
- umap-learn >= 0.5.0
- pytorch-wpe >= 0.0.1

新增：
- sherpa-onnx >= 1.10.0

保留：
- onnxruntime >= 1.23.0 (已有)
- numpy >= 1.24.0 (已有)
- soundfile >= 0.12.0 (已有)
```

### 文件变更

| 文件 | 操作 | 说明 |
|------|------|------|
| `sensevoice_service.py` | 重写 | 核心迁移 |
| `config.py` | 修改 | 移除 FunASR 特有配置 |
| `requirements.txt` | 修改 | 更新依赖 |
| `ast_service.py` | 微调 | 适配新接口 |
| `tools/prepare_torch.py` | 删除 | 不再需要 |
| `tools/download_sensevoice.py` | 重写 | 改为下载 ONNX 模型 |

## 核心组件设计

### SenseVoiceConfig

```python
@dataclass
class SenseVoiceConfig:
    """sherpa-onnx SenseVoice 配置"""

    model_dir: str = "models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17"
    language: str = "auto"  # auto/zh/en/ja/ko/yue
    use_itn: bool = True
    hotword_weight: float = 3.0
    max_concurrent: int = 4
    timeout_seconds: float = 10.0
    device: str = "cpu"
```

### SenseVoiceService 接口

```python
class SenseVoiceService:
    """sherpa-onnx SenseVoice 服务封装"""

    async def initialize(self) -> bool
    async def transcribe_audio(audio_data: bytes, ...) -> Dict[str, Any]
    def update_hotwords(session_id: Optional[str], terms: Iterable[str]) -> None
    async def cleanup()
    def get_model_info() -> Dict[str, Any]
```

## 数据流

```
音频输入 (PCM 16-bit, 16kHz)
    │
    ▼
ASTService._process_audio_chunk()
    ├── 静音检测 (RMS < 320)
    └── 调用 SenseVoiceService.transcribe_audio()
    │
    ▼
SenseVoiceService.transcribe_audio()
    ├── 并发控制 (Semaphore)
    ├── bytes → numpy 转换
    └── 组装热词
    │
    ▼
_transcribe_with_lock() (线程池)
    ├── 创建 sherpa_onnx.Stream
    ├── accept_waveform()
    ├── decode_stream()
    └── 提取结果
    │
    ▼
返回 {"success", "text", "confidence", "timestamp", "words"}
```

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| 模型未初始化 | 返回 `{"success": False, "error": "模型未就绪"}` |
| 音频为空 | 返回 `{"success": True, "type": "silence"}` |
| 转录超时 | 记录日志，返回错误 |
| 模型文件缺失 | 初始化失败 |

## TDD 测试策略

### 测试文件

```
server/tests/
├── test_sensevoice_onnx_service.py    # 单元测试
├── test_sensevoice_onnx_integration.py # 集成测试
└── fixtures/
    └── test_audio_16k.wav             # 测试音频
```

### 测试用例

- 配置测试：默认配置、自定义路径
- 初始化测试：成功、失败
- 转录测试：静音、中文、热词
- 热词测试：全局、会话、组装

### 开发顺序

```
RED → GREEN → REFACTOR 循环
```

## 实施步骤

```
Phase 1: 环境准备
├── 更新 requirements.txt
├── 创建 ONNX 模型下载脚本
└── 准备测试音频

Phase 2: 测试先行 (RED)
├── 配置测试
├── 初始化测试
├── 转录测试
├── 热词测试
└── 集成测试

Phase 3: 实现代码 (GREEN)
├── 重写 SenseVoiceConfig
├── 重写 SenseVoiceService
├── 实现热词功能
└── 更新配置文件

Phase 4: 重构优化 (REFACTOR)
├── 移除冗余代码
├── 优化内存管理
└── 添加性能监控

Phase 5: 清理
├── 删除旧代码
├── 更新文档
└── 运行完整测试
```

## 验收标准

```bash
# 1. 所有测试通过
pytest server/tests/test_sensevoice_onnx*.py -v

# 2. 依赖体积减少 > 90%

# 3. 功能验证
python -c "from server.modules.ast.sensevoice_service import SenseVoiceService; print('OK')"

# 4. 启动服务无报错
npm run dev:backend
```

## 风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| sherpa-onnx 热词支持有限 | 查阅文档，必要时使用关键词后处理 |
| API 差异导致兼容问题 | 保持接口签名不变，内部适配 |
| 识别准确率下降 | 对比测试，必要时调整参数 |

## 预估收益

- **体积**: 2.7GB → 80MB (减少 96%)
- **启动速度**: 预计提升 50%+
- **内存占用**: 预计减少 60%+
- **兼容性**: 彻底解决 numba 问题
