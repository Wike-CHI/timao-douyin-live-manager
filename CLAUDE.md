# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**提猫直播助手 (TalkingCat)** is an Electron desktop application with a FastAPI backend for Douyin (TikTok China) live stream assistance. It provides real-time danmaku (bullet comments) fetching, local speech-to-text (SenseVoice), AI-powered script generation, and live stream replay capabilities.

## Development Commands

```bash
# Full development (recommended)
pnpm run dev                    # Start backend + frontend + Electron

# Individual services
pnpm run dev:renderer           # Vite dev server only (port 10200)
pnpm run dev:backend            # Backend only (port 11111)
pnpm run dev:electron           # Electron only (waits for renderer)

# Build and release
pnpm run build                  # Build frontend + electron-builder
pnpm run build:win64            # Windows x64 portable build
pnpm run release                # Build for release with defaults

# Testing
pnpm run test                   # Python tests via uv
uv run pytest tests/            # Run specific test path
uv run pytest server/tests/test_live_audio.py::TestLiveAudioAPI  # Specific test
pnpm run lint                   # ESLint for electron/

# Port and process management
pnpm run kill:ports             # Kill ports 11111 and 10200
pnpm run health:all             # Check all services health

# Clean
pnpm run clean                  # Clean dist folders
pnpm run clean:apply            # Clean with Python cache cleaner

# Dependency management
pnpm run deps:install           # Install all deps (pnpm + uv)
pnpm run deps:update            # Update all deps
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Electron Main Process (electron/main.js)                   │
├─────────────────────────────────────────────────────────────┤
│  Floating Window          Main Browser Window              │
│  (React + Vite on :10200)                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ FastAPI Backend (server/app/main.py)                       │
│ Port: 11111 (dev) / 8090 (prod)                            │
├─────────────────────────────────────────────────────────────┤
│  REST API Routes          │  WebSocket                     │
│  /api/live_audio/*        │  /api/live_audio/ws            │
│  /api/douyin/*            │                                │
│  /api/ai/*                │                                │
└─────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│ Douyin      │      │ SenseVoice  │      │ AI Gateway  │
│ Danmaku     │      │ AST Module  │      │ (LangChain) │
│ (WebSocket) │      │ (Local ASR) │      │ Qwen/OpenAI │
└─────────────┘      └─────────────┘      └─────────────┘
```

## Key Entry Points

| Path | Purpose |
|------|---------|
| `electron/main.js` | Electron main process |
| `server/app/main.py` | FastAPI backend entry |
| `electron/renderer/src/main.tsx` | React frontend entry |
| `electron/preload.js` | IPC bridge between processes |

## Core Directories

- `electron/renderer/src/` - React frontend (Vite + Tailwind + Zustand)
- `server/app/` - FastAPI backend (REST + WebSocket routes, models, services)
- `server/modules/` - Core feature modules:
  - `ast/` - Audio-to-text (sherpa-onnx/SenseVoice ONNX)
  - `douyin/` - Douyin danmaku fetching
  - `streamcap/` - Stream capture
- `server/ai/` - AI/LangChain workflows
- `server/nlp/` - Chinese NLP (jieba, SnowNLP)
- `scripts/` - Utility scripts organized by category (Chinese naming)

## AI Gateway Configuration

Configure in `.env`:
```bash
AI_SERVICE=qwen           # qwen, openai, deepseek, doubao, chatglm
AI_API_KEY=sk-xxx
AI_MODEL=qwen-plus
```

AI gateway manager UI: http://localhost:10090/static/ai_gateway_manager.html

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `BACKEND_PORT` | FastAPI port | 11111 (dev) / 8090 (prod) |
| `VITE_FASTAPI_URL` | Frontend API target | Inherited from backend |
| `DISABLE_SSL_VERIFY` | Skip SSL verification | 1 |

## Testing

Pytest markers defined in `pyproject.toml`:
- `asyncio` - Async tests
- `integration` - Integration tests
- `unit` - Unit tests
- `slow` - Slow-running tests

Run specific tests:
```bash
uv run pytest tests/                    # All tests
uv run pytest tests/ -k "live"          # Filter by keyword
uv run pytest tests/ --co               # List tests without running
```

## Port Reference

| Port | Service |
|------|---------|
| 10200 | Vite dev server (frontend) |
| 11111 | FastAPI backend (dev) |
| 8090 | FastAPI backend (production) |

## Documentation

Chinese documentation in `docs/`:
- `docs/guides/` - Quick start, deployment, packaging guides
- `docs/runbooks/` - Troubleshooting SOPs
- `docs/reference/` - Port, command, configuration baselines
- `docs/AI方案与集成/` - AI gateway documentation
- `docs/直播音频方案/` - Audio streaming architecture

## Important Notes

- **Python**: `pyproject.toml` (uv, 轻量级核心依赖 ~50MB)
- **Node**: `pnpm-workspace.yaml` (pnpm workspace)
- **Mini-Agent**: `Mini-Agent/` (uv workspace member)
- **Models**: `models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/`
- **Logs**: `logs/` directory
- **Records**: `records/` directory

## Dependencies Installation

### Quick Start
```bash
# 1. Install tools (if not installed)
npm install -g pnpm
pip install uv

# 2. Install core dependencies (minimal ~50MB)
pnpm run setup

# 3. Add optional features as needed
uv sync --extra ai          # AI features (~200MB)
uv sync --extra audio       # Speech recognition (~80MB)
uv sync --extra nlp         # Chinese NLP
uv sync --extra data        # Data processing (numpy, pandas)

# Or install everything
uv sync --all-extras
```

### Dependency Groups
| Group | Size | Description |
|-------|------|-------------|
| core | ~50MB | FastAPI, pydantic, httpx, loguru |
| ai | ~200MB | langchain, openai, dashscope |
| audio | ~80MB | sherpa-onnx, onnxruntime |
| nlp | ~20MB | jieba, snownlp |
| data | ~100MB | numpy, pandas |
| dev | ~50MB | pytest, ruff |

## AST (Audio Speech Transcription)

AST 模块使用 sherpa-onnx 进行语音识别：
- 模型: SenseVoice ONNX (~200MB)
- 依赖: sherpa-onnx + onnxruntime (~80MB)
- 无需 PyTorch/FunASR (减少依赖体积约2.6GB)

## Agent Architecture (v2)

项目正在迁移到 **Pydantic AI Agent 架构**，提供更清晰的代码结构和更好的可维护性。

### 新 API (v2)

| Endpoint | Description |
|----------|-------------|
| `GET /api/v2/settings/voice` | 获取语音设置 |
| `PUT /api/v2/settings/voice` | 更新语音设置 |
| `POST /api/v2/settings/voice/reset` | 重置语音设置 |
| `GET /api/v2/settings/ai` | 获取 AI 设置 |
| `PUT /api/v2/settings/ai` | 更新 AI 设置 |
| `POST /api/v2/voice/transcribe` | 语音转写 |

### 使用 Agent

```python
from server.agents.voice import VoiceAgent, VoiceAgentConfig

# 创建 Agent
config = VoiceAgentConfig(
    model="sensevoice",  # sensevoice, whisper, funasr
    language="auto",     # auto, zh, en, ja, ko, yue
    enable_vad=True,
)
agent = VoiceAgent(config)

# 执行转写
result = await agent.transcribe("audio.wav")
print(result.text)
```

### 运行时配置

前端可实时切换语音模型，无需重启服务：

```typescript
import { settingsService } from './services/settingsService';

// 更新语音模型
await settingsService.updateVoiceSettings({
  model: 'whisper',
  language: 'en',
});
```

### Agent 目录结构

```
server/agents/
├── __init__.py
├── base.py              # BaseAgent, AgentResult 基类
└── voice/
    ├── __init__.py
    └── agent.py         # VoiceAgent, VoiceAgentConfig

server/services/voice/
├── __init__.py
└── transcribe.py        # TranscriberBase, SenseVoiceTranscriber
```

