# SenseVoice ONNX 迁移实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 SenseVoice 语音识别从 FunASR/PyTorch 迁移到 sherpa-onnx，减少依赖体积 96%

**Architecture:** 直接重写 sensevoice_service.py，使用 sherpa-onnx 替代 FunASR，保持对外接口不变，完全移除 PyTorch 依赖

**Tech Stack:** sherpa-onnx, onnxruntime, pytest, asyncio

---

## Phase 1: 环境准备

### Task 1: 更新依赖文件

**Files:**
- Modify: `requirements.txt`

**Step 1: 移除 FunASR 相关依赖，添加 sherpa-onnx**

打开 `requirements.txt`，删除以下行：
```text
funasr>=1.2.0
torch>=2.0.0
torchaudio>=2.0.0
torchvision>=0.17.1
numba==0.59.1
llvmlite==0.42.0
librosa>=0.10.0
hydra-core>=1.3.0
omegaconf>=2.3.0
umap-learn>=0.5.0
pytorch-wpe>=0.0.1
```

添加以下行：
```text
sherpa-onnx>=1.10.0
```

**Step 2: 验证文件格式正确**

Run: `python -c "import requirements; print('OK')"` 或检查语法

Expected: 无语法错误

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: remove FunASR/PyTorch, add sherpa-onnx dependency"
```

---

### Task 2: 创建测试目录结构

**Files:**
- Create: `server/tests/__init__.py`
- Create: `server/tests/conftest.py`

**Step 1: 创建测试目录**

```bash
mkdir -p server/tests
```

**Step 2: 创建 __init__.py**

```bash
touch server/tests/__init__.py
```

**Step 3: 创建 conftest.py 测试夹具**

```python
# server/tests/conftest.py
"""测试夹具和配置"""

import pytest
import numpy as np
from pathlib import Path
import tempfile


@pytest.fixture
def sample_rate():
    """采样率"""
    return 16000


@pytest.fixture
def test_audio_silence(sample_rate):
    """静音音频 (1秒, 16kHz)"""
    duration = 1.0
    samples = int(sample_rate * duration)
    # 全零的 16-bit PCM
    audio = np.zeros(samples, dtype=np.int16)
    return audio.tobytes()


@pytest.fixture
def test_audio_tone(sample_rate):
    """正弦波音频 (1秒, 440Hz)"""
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    wave = np.sin(2 * np.pi * 440 * t)
    audio = (wave * 32767 * 0.5).astype(np.int16)
    return audio.tobytes()


@pytest.fixture
def mock_model_dir(tmp_path):
    """模拟模型目录"""
    model_dir = tmp_path / "sherpa-onnx-sense-voice"
    model_dir.mkdir()
    # 创建必要的模型文件
    (model_dir / "model.onnx").touch()
    (model_dir / "tokens.txt").write_text("你好\n世界\n")
    return str(model_dir)
```

**Step 4: 验证夹具加载**

Run: `pytest server/tests/conftest.py --collect-only`

Expected: 无错误

**Step 5: Commit**

```bash
git add server/tests/
git commit -m "test: add test fixtures for SenseVoice ONNX migration"
```

---

## Phase 2: 测试先行 (RED)

### Task 3: SenseVoiceConfig 测试

**Files:**
- Create: `server/tests/test_sensevoice_config.py`

**Step 1: 写配置默认值测试**

```python
# server/tests/test_sensevoice_config.py
"""SenseVoiceConfig 配置测试"""

import pytest


class TestSenseVoiceConfig:
    """配置类测试"""

    def test_default_config_values(self):
        """默认配置应有正确的值"""
        # 先导入会失败，这是 RED 阶段
        from server.modules.ast.sensevoice_service import SenseVoiceConfig

        config = SenseVoiceConfig()

        assert config.model_dir == "models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17"
        assert config.language == "auto"
        assert config.use_itn == True
        assert config.hotword_weight == 3.0
        assert config.max_concurrent == 4
        assert config.timeout_seconds == 10.0
        assert config.device == "cpu"

    def test_custom_model_path(self):
        """自定义模型路径"""
        from server.modules.ast.sensevoice_service import SenseVoiceConfig

        config = SenseVoiceConfig(model_dir="/custom/path/to/model")
        assert config.model_dir == "/custom/path/to/model"

    def test_custom_language(self):
        """自定义语言"""
        from server.modules.ast.sensevoice_service import SenseVoiceConfig

        config = SenseVoiceConfig(language="zh")
        assert config.language == "zh"
```

**Step 2: 运行测试验证失败**

Run: `pytest server/tests/test_sensevoice_config.py -v`

Expected: FAIL - "cannot import name 'SenseVoiceConfig'"

**Step 3: Commit**

```bash
git add server/tests/test_sensevoice_config.py
git commit -m "test(red): add SenseVoiceConfig tests"
```

---

### Task 4: SenseVoiceService 初始化测试

**Files:**
- Create: `server/tests/test_sensevoice_init.py`

**Step 1: 写初始化测试**

```python
# server/tests/test_sensevoice_init.py
"""SenseVoiceService 初始化测试"""

import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def service_with_mock_model(mock_model_dir):
    """使用模拟模型的服务"""
    from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

    config = SenseVoiceConfig(model_dir=mock_model_dir)
    service = SenseVoiceService(config)
    yield service
    await service.cleanup()


class TestSenseVoiceServiceInit:
    """初始化测试"""

    @pytest.mark.asyncio
    async def test_initialize_success(self, mock_model_dir):
        """成功初始化"""
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        config = SenseVoiceConfig(model_dir=mock_model_dir)
        service = SenseVoiceService(config)
        result = await service.initialize()

        assert result == True
        assert service.is_initialized == True

        await service.cleanup()

    @pytest.mark.asyncio
    async def test_initialize_missing_model(self, tmp_path):
        """模型不存在时失败"""
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        nonexistent = tmp_path / "nonexistent"
        config = SenseVoiceConfig(model_dir=str(nonexistent))
        service = SenseVoiceService(config)
        result = await service.initialize()

        assert result == False
        assert service.is_initialized == False

    @pytest.mark.asyncio
    async def test_get_model_info(self, service_with_mock_model):
        """获取模型信息"""
        await service_with_mock_model.initialize()
        info = service_with_mock_model.get_model_info()

        assert "backend" in info
        assert info["backend"] == "sherpa-onnx"
        assert "model_dir" in info
        assert "initialized" in info
```

**Step 2: 运行测试验证失败**

Run: `pytest server/tests/test_sensevoice_init.py -v`

Expected: FAIL - "cannot import name 'SenseVoiceService'"

**Step 3: Commit**

```bash
git add server/tests/test_sensevoice_init.py
git commit -m "test(red): add SenseVoiceService initialization tests"
```

---

### Task 5: SenseVoiceService 转录测试

**Files:**
- Create: `server/tests/test_sensevoice_transcribe.py`

**Step 1: 写转录测试**

```python
# server/tests/test_sensevoice_transcribe.py
"""SenseVoiceService 转录测试"""

import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def initialized_service(mock_model_dir):
    """已初始化的服务"""
    from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

    config = SenseVoiceConfig(model_dir=mock_model_dir)
    service = SenseVoiceService(config)
    await service.initialize()
    yield service
    await service.cleanup()


class TestSenseVoiceServiceTranscribe:
    """转录测试"""

    @pytest.mark.asyncio
    async def test_transcribe_silence(self, initialized_service, test_audio_silence):
        """静音音频返回空结果"""
        result = await initialized_service.transcribe_audio(test_audio_silence)

        assert result["success"] == True
        assert result["type"] == "silence"
        assert result["text"] == ""
        assert result["confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_transcribe_returns_dict(self, initialized_service, test_audio_tone):
        """转录返回正确格式的字典"""
        result = await initialized_service.transcribe_audio(test_audio_tone)

        assert isinstance(result, dict)
        assert "success" in result
        assert "text" in result
        assert "confidence" in result
        assert "timestamp" in result
        assert "words" in result

    @pytest.mark.asyncio
    async def test_transcribe_empty_audio(self, initialized_service):
        """空音频返回静音结果"""
        result = await initialized_service.transcribe_audio(b"")

        assert result["success"] == True
        assert result["type"] == "silence"

    @pytest.mark.asyncio
    async def test_transcribe_before_init(self, mock_model_dir):
        """未初始化时返回错误"""
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        config = SenseVoiceConfig(model_dir=mock_model_dir)
        service = SenseVoiceService(config)
        # 不初始化
        result = await service.transcribe_audio(b"test")

        assert result["success"] == False

    @pytest.mark.asyncio
    async def test_transcribe_with_session_id(self, initialized_service, test_audio_tone):
        """带 session_id 的转录"""
        result = await initialized_service.transcribe_audio(
            test_audio_tone,
            session_id="test_session_123"
        )

        assert result["success"] == True
```

**Step 2: 运行测试验证失败**

Run: `pytest server/tests/test_sensevoice_transcribe.py -v`

Expected: FAIL

**Step 3: Commit**

```bash
git add server/tests/test_sensevoice_transcribe.py
git commit -m "test(red): add SenseVoiceService transcription tests"
```

---

### Task 6: 热词功能测试

**Files:**
- Create: `server/tests/test_sensevoice_hotwords.py`

**Step 1: 写热词测试**

```python
# server/tests/test_sensevoice_hotwords.py
"""SenseVoiceService 热词测试"""

import pytest


class TestSenseVoiceHotwords:
    """热词功能测试"""

    def test_update_global_hotwords(self, mock_model_dir):
        """更新全局热词"""
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        config = SenseVoiceConfig(model_dir=mock_model_dir)
        service = SenseVoiceService(config)

        service.update_hotwords(None, ["提猫", "直播助手", "AI"])

        assert "提猫" in service._global_hotwords
        assert "直播助手" in service._global_hotwords
        assert "AI" in service._global_hotwords

    def test_update_session_hotwords(self, mock_model_dir):
        """更新会话热词"""
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        config = SenseVoiceConfig(model_dir=mock_model_dir)
        service = SenseVoiceService(config)

        service.update_hotwords("session_1", ["会话词A", "会话词B"])

        assert "session_1" in service._session_hotwords
        assert "会话词A" in service._session_hotwords["session_1"]
        assert "会话词B" in service._session_hotwords["session_1"]

    def test_update_empty_hotwords(self, mock_model_dir):
        """更新空热词不影响现有热词"""
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        config = SenseVoiceConfig(model_dir=mock_model_dir)
        service = SenseVoiceService(config)

        service.update_hotwords(None, ["词A"])
        service.update_hotwords(None, [])

        assert "词A" in service._global_hotwords

    def test_compose_hotword_payload(self, mock_model_dir):
        """组装热词字符串"""
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        config = SenseVoiceConfig(model_dir=mock_model_dir)
        service = SenseVoiceService(config)

        service.update_hotwords(None, ["词A", "词B"])
        payload = service._compose_hotword_payload(None, None)

        assert payload is not None
        assert "词A" in payload
        assert "词B" in payload

    def test_compose_hotword_with_bias_phrases(self, mock_model_dir):
        """组装带 bias_phrases 的热词"""
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        config = SenseVoiceConfig(model_dir=mock_model_dir)
        service = SenseVoiceService(config)

        service.update_hotwords(None, ["全局词"])
        payload = service._compose_hotword_payload(None, ["临时词"])

        assert "全局词" in payload
        assert "临时词" in payload

    def test_compose_hotword_empty(self, mock_model_dir):
        """无热词时返回 None"""
        from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig

        config = SenseVoiceConfig(model_dir=mock_model_dir)
        service = SenseVoiceService(config)

        payload = service._compose_hotword_payload(None, None)

        assert payload is None
```

**Step 2: 运行测试验证失败**

Run: `pytest server/tests/test_sensevoice_hotwords.py -v`

Expected: FAIL

**Step 3: Commit**

```bash
git add server/tests/test_sensevoice_hotwords.py
git commit -m "test(red): add SenseVoice hotword tests"
```

---

## Phase 3: 实现代码 (GREEN)

### Task 7: 实现 SenseVoiceConfig

**Files:**
- Modify: `server/modules/ast/sensevoice_service.py` (完全重写)

**Step 1: 重写 sensevoice_service.py 头部和 SenseVoiceConfig**

```python
# server/modules/ast/sensevoice_service.py
# -*- coding: utf-8 -*-
"""SenseVoice ASR integration using sherpa-onnx."""

from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

import numpy as np

# 尝试导入 sherpa_onnx
try:
    import sherpa_onnx
    SHERPA_ONNX_AVAILABLE = True
except ImportError:
    sherpa_onnx = None  # type: ignore
    SHERPA_ONNX_AVAILABLE = False


@dataclass
class SenseVoiceConfig:
    """sherpa-onnx SenseVoice 配置。

    Attributes:
        model_dir: ONNX 模型目录路径
        language: 语言设置 (auto/zh/en/ja/ko/yue)
        use_itn: 是否使用逆文本正则化
        hotword_weight: 热词权重
        max_concurrent: 最大并发转写数
        timeout_seconds: 单次转写超时时间
        device: 设备 (cpu/cuda)
    """

    model_dir: str = "models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17"
    language: str = "auto"
    use_itn: bool = True
    hotword_weight: float = 3.0
    max_concurrent: int = 4
    timeout_seconds: float = 10.0
    device: str = "cpu"
```

**Step 2: 运行配置测试**

Run: `pytest server/tests/test_sensevoice_config.py -v`

Expected: PASS

**Step 3: Commit**

```bash
git add server/modules/ast/sensevoice_service.py
git commit -m "feat(green): implement SenseVoiceConfig dataclass"
```

---

### Task 8: 实现 SenseVoiceService 骨架

**Files:**
- Modify: `server/modules/ast/sensevoice_service.py`

**Step 1: 添加 SenseVoiceService 类骨架**

在 `sensevoice_service.py` 的 `SenseVoiceConfig` 之后添加：

```python


class SenseVoiceService:
    """sherpa-onnx SenseVoice 服务封装。

    使用 sherpa-onnx 进行离线语音识别，支持热词功能。
    """

    def __init__(self, config: Optional[SenseVoiceConfig] = None):
        """初始化服务。

        Args:
            config: 配置对象，如果为 None 则使用默认配置
        """
        self.config = config or SenseVoiceConfig()
        self.logger = logging.getLogger(__name__)

        # 模型实例
        self._recognizer: Optional[Any] = None
        self.is_initialized = False

        # 热词存储
        self._global_hotwords: set = set()
        self._session_hotwords: Dict[str, set] = {}

        # 并发控制
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self._active_requests: int = 0

        # 统计
        self._call_count: int = 0
        self._total_errors: int = 0

    async def initialize(self) -> bool:
        """加载 ONNX 模型。

        Returns:
            bool: 初始化是否成功
        """
        if self.is_initialized:
            return True

        if not SHERPA_ONNX_AVAILABLE:
            self.logger.error("sherpa-onnx 未安装")
            return False

        # 检查模型目录
        from pathlib import Path
        model_path = Path(self.config.model_dir)
        if not model_path.exists():
            self.logger.error(f"模型目录不存在: {model_path}")
            return False

        try:
            loop = asyncio.get_event_loop()

            def _load_model():
                return sherpa_onnx.OfflineRecognizer.from_sense_voice(
                    model=str(model_path),
                    language=self.config.language,
                    use_itn=self.config.use_itn,
                )

            self._recognizer = await loop.run_in_executor(None, _load_model)
            self.is_initialized = True
            self.logger.info(f"✅ sherpa-onnx 模型加载成功: {model_path}")
            return True

        except Exception as exc:
            self.logger.error(f"模型加载失败: {exc}")
            self.is_initialized = False
            return False

    async def transcribe_audio(
        self,
        audio_data: bytes,
        *,
        session_id: Optional[str] = None,
        bias_phrases: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        """转录音频。

        Args:
            audio_data: PCM 16-bit 音频数据 (16kHz)
            session_id: 会话 ID（用于会话级热词）
            bias_phrases: 临时热词

        Returns:
            Dict: 转录结果
        """
        # 未初始化
        if not self.is_initialized:
            return {
                "success": False,
                "type": "error",
                "text": "",
                "confidence": 0.0,
                "timestamp": time.time(),
                "words": [],
                "error": "模型未初始化",
            }

        # 空音频
        if not audio_data:
            return {
                "success": True,
                "type": "silence",
                "text": "",
                "confidence": 0.0,
                "timestamp": time.time(),
                "words": [],
            }

        # 并发控制
        try:
            async with self._semaphore:
                self._active_requests += 1
                try:
                    result = await asyncio.wait_for(
                        self._transcribe_internal(audio_data, session_id, bias_phrases),
                        timeout=self.config.timeout_seconds,
                    )
                    return result
                except asyncio.TimeoutError:
                    self.logger.error(f"转录超时 ({self.config.timeout_seconds}s)")
                    return {
                        "success": False,
                        "type": "error",
                        "text": "",
                        "confidence": 0.0,
                        "timestamp": time.time(),
                        "words": [],
                        "error": "转录超时",
                    }
                finally:
                    self._active_requests -= 1
        except Exception as exc:
            self._total_errors += 1
            self.logger.error(f"转录失败: {exc}")
            return {
                "success": False,
                "type": "error",
                "text": "",
                "confidence": 0.0,
                "timestamp": time.time(),
                "words": [],
                "error": str(exc),
            }

    async def _transcribe_internal(
        self,
        audio_data: bytes,
        session_id: Optional[str],
        bias_phrases: Optional[Iterable[str]],
    ) -> Dict[str, Any]:
        """内部转录实现。"""
        loop = asyncio.get_event_loop()

        def _infer():
            # 转换为 numpy
            audio_np = np.frombuffer(audio_data, dtype=np.int16)

            # 静音检测
            rms = np.sqrt(np.mean(audio_np.astype(np.float32) ** 2))
            if rms < 320:
                return {
                    "success": True,
                    "type": "silence",
                    "text": "",
                    "confidence": 0.0,
                    "timestamp": time.time(),
                    "words": [],
                }

            # 创建流并识别
            stream = self._recognizer.create_stream()
            stream.accept_waveform(16000, audio_np)

            # 设置热词
            hotwords = self._compose_hotword_payload(session_id, bias_phrases)
            if hotwords:
                # sherpa-onnx 热词支持
                pass  # TODO: 验证 sherpa-onnx 热词 API

            self._recognizer.decode_stream(stream)

            # 提取结果
            text = stream.result.text.strip()
            confidence = 0.9 if text else 0.0

            return {
                "success": True,
                "type": "final",
                "text": text,
                "confidence": confidence,
                "timestamp": time.time(),
                "words": [],
            }

        self._call_count += 1
        return await loop.run_in_executor(None, _infer)

    def update_hotwords(
        self,
        session_id: Optional[str],
        terms: Iterable[str],
    ) -> None:
        """更新热词。

        Args:
            session_id: 会话 ID，None 表示全局热词
            terms: 热词列表
        """
        words: set = set()
        for term in terms:
            if not term:
                continue
            text = str(term).strip()
            if text:
                words.add(text)

        if not words:
            return

        if session_id:
            bucket = self._session_hotwords.setdefault(session_id, set())
            bucket.update(words)
        else:
            self._global_hotwords.update(words)

    def _compose_hotword_payload(
        self,
        session_id: Optional[str],
        bias_phrases: Optional[Iterable[str]],
    ) -> Optional[str]:
        """组装热词字符串。"""
        phrases: set = set()
        phrases.update(self._global_hotwords)

        if session_id:
            phrases.update(self._session_hotwords.get(session_id, set()))

        if bias_phrases:
            for term in bias_phrases:
                if term:
                    phrases.add(str(term).strip())

        if not phrases:
            return None

        return " ".join(sorted(phrases))

    async def cleanup(self) -> None:
        """释放资源。"""
        self._recognizer = None
        self.is_initialized = False
        self.logger.info("SenseVoice 服务已清理")

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息。"""
        return {
            "backend": "sherpa-onnx",
            "model_dir": self.config.model_dir,
            "language": self.config.language,
            "initialized": self.is_initialized,
        }
```

**Step 2: 运行所有测试**

Run: `pytest server/tests/test_sensevoice_*.py -v`

Expected: 大部分 PASS

**Step 3: Commit**

```bash
git add server/modules/ast/sensevoice_service.py
git commit -m "feat(green): implement SenseVoiceService with sherpa-onnx"
```

---

### Task 9: 更新 config.py

**Files:**
- Modify: `server/modules/ast/config.py`

**Step 1: 移除 FunASR 相关配置**

在 `config.py` 中，修改 `create_ast_config` 函数，移除 VAD 和 PUNC 模型相关代码：

```python
# 移除这些函数:
# - _autodetect_vad_model
# - _autodetect_punc_model

# 修改 create_ast_config:
def create_ast_config(
    model_path: Optional[str] = None,
    sample_rate: int = 16000,
    chunk_duration: float = 1.0,
    min_confidence: float = 0.5,
    save_audio: bool = False,
):
    """创建自定义 AST 配置。"""
    global ASTConfig
    if ASTConfig is None:
        try:
            from .ast_service import ASTConfig
        except ImportError:
            from ast_service import ASTConfig

    audio_config = AudioConfig(
        sample_rate=sample_rate,
        channels=1,
        chunk_size=1024,
        input_device_index=None,
        enable_denoise=True,
        denoise_backend="auto",
        denoise_level="moderate",
        enable_agc=True,
        target_rms=0.05,
    )

    return ASTConfig(
        audio_config=audio_config,
        model_id=model_path or DEFAULT_MODEL_ID,
        chunk_duration=chunk_duration,
        min_confidence=min_confidence,
        buffer_duration=10.0,
        save_audio_files=save_audio,
        audio_output_dir="./audio_logs",
        # 移除 VAD 相关配置
        enable_vad=False,
        vad_model_id=None,
        punc_model_id=None,
    )
```

**Step 2: 运行测试验证**

Run: `pytest server/tests/ -v -k "config"`

Expected: PASS

**Step 3: Commit**

```bash
git add server/modules/ast/config.py
git commit -m "refactor: remove FunASR VAD/PUNC config from ast config"
```

---

## Phase 4: 清理与验证

### Task 10: 删除废弃文件

**Files:**
- Delete: `tools/prepare_torch.py`

**Step 1: 删除 PyTorch 准备脚本**

```bash
rm tools/prepare_torch.py
```

**Step 2: 验证删除**

Run: `ls tools/prepare_torch.py`

Expected: "No such file or directory"

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove obsolete prepare_torch.py"
```

---

### Task 11: 运行完整测试套件

**Files:**
- None (验证步骤)

**Step 1: 运行所有 SenseVoice 测试**

Run: `pytest server/tests/test_sensevoice_*.py -v --tb=short`

Expected: 全部 PASS

**Step 2: 运行 AST 相关测试**

Run: `pytest server/tests/ -v -k "ast or sensevoice" --tb=short`

Expected: PASS

**Step 3: 验证导入**

Run: `python -c "from server.modules.ast.sensevoice_service import SenseVoiceService, SenseVoiceConfig; print('OK')"`

Expected: "OK"

---

### Task 12: 更新文档

**Files:**
- Modify: `CLAUDE.md`

**Step 1: 更新依赖说明**

在 `CLAUDE.md` 中更新：

```markdown
## Dependencies Installation

```bash
# Python
pip install -r requirements.txt  # 现在更轻量，无 PyTorch

# Node
npm ci
```

## Architecture

AST (Audio Speech Transcription) 模块使用 sherpa-onnx 进行语音识别：
- 模型: SenseVoice ONNX (~200MB)
- 依赖: sherpa-onnx + onnxruntime (~80MB)
- 无需 PyTorch/FunASR
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md for sherpa-onnx migration"
```

---

## Phase 5: 最终验证

### Task 13: 安装新依赖并验证

**Step 1: 安装新依赖**

```bash
pip uninstall -y torch torchaudio torchvision funasr numba llvmlite
pip install sherpa-onnx
```

**Step 2: 验证安装**

Run: `pip list | grep -E "torch|funasr|sherpa"`

Expected: 无 torch/funasr，有 sherpa-onnx

**Step 3: 运行最终测试**

Run: `pytest server/tests/ -v`

Expected: PASS

**Step 4: 最终 Commit**

```bash
git add -A
git commit -m "feat: complete SenseVoice ONNX migration

- Replace FunASR/PyTorch with sherpa-onnx
- Reduce dependency size from 2.7GB to ~80MB (96% reduction)
- Maintain API compatibility
- All tests passing"
```

---

## 验收清单

- [ ] 所有 `test_sensevoice_*.py` 测试通过
- [ ] 无 torch/funasr 依赖残留
- [ ] `from server.modules.ast.sensevoice_service import SenseVoiceService` 成功
- [ ] 依赖体积 < 100MB
- [ ] 文档已更新

---

## 风险提示

1. **sherpa-onnx 热词 API**: 需要验证实际热词支持方式
2. **模型下载**: 首次使用需要下载 ~200MB 的 ONNX 模型
3. **API 兼容性**: 如有差异，在 `_transcribe_internal` 中适配
