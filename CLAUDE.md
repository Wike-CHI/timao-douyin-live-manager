# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**提猫直播助手 (TalkingCat)** is an Electron desktop application with a FastAPI backend for Douyin (TikTok China) live stream assistance. It provides real-time danmaku (bullet comments) fetching, local speech-to-text (SenseVoice), AI-powered script generation, and live stream replay capabilities.

## Development Commands

```bash
# Full development (recommended)
npm run dev                    # Start backend + frontend + Electron

# Individual services
npm run dev:renderer           # Vite dev server only (port 10200)
npm run dev:backend            # Backend only (port 11111)
npm run dev:electron           # Electron only (waits for renderer)

# Build and release
npm run build                  # Build frontend + electron-builder
npm run build:win64            # Windows x64 portable build
npm run release                # Build for release with defaults

# Testing
pytest                         # Python tests (tests/, server/tests/)
pytest server/tests/test_live_audio.py::TestLiveAudioAPI  # Specific test
npm run lint                   # ESLint for electron/

# Port and process management
npm run kill:ports             # Kill ports 11111 and 10200
npm run health:all             # Check all services health

# Clean
npm run clean                  # Clean dist folders
npm run clean:apply            # Clean with Python cache cleaner
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

Pytest markers defined in `pytest.ini`:
- `asyncio` - Async tests
- `integration` - Integration tests
- `unit` - Unit tests
- `redis` - Redis-related tests
- `slow` - Slow-running tests

Run specific tests:
```bash
pytest tests/                           # All tests
pytest tests/ -k "live"                 # Filter by keyword
pytest tests/ --co                      # List tests without running
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

- Python dependencies: `requirements.txt` (轻量级，使用 sherpa-onnx 替代 PyTorch)
- Node dependencies are managed separately in `electron/renderer/`
- Model files for SenseVoice ONNX are stored in `models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/`
- Logs are stored in `logs/` directory
- Replay files are stored in `records/` directory
- The project uses `loguru` for logging with UTF-8 encoding support

## Dependencies Installation

```bash
# Python (轻量级依赖，约80MB)
pip install -r requirements.txt

# Node (automatically installs electron/renderer deps via postinstall)
npm ci
```

## AST (Audio Speech Transcription)

AST 模块使用 sherpa-onnx 进行语音识别：
- 模型: SenseVoice ONNX (~200MB)
- 依赖: sherpa-onnx + onnxruntime (~80MB)
- 无需 PyTorch/FunASR (减少依赖体积约2.6GB)
