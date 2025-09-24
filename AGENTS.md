# Repository Guidelines

## Project Structure & Module Organization
- `electron/`: desktop shell; `main.js` launches `server/app.py` and renders the UI.
- `server/`: Flask `app.py` (REST/SSE) and FastAPI `app/main.py` (AST); helpers in `utils/`, NLP in `nlp/`, ingestion in `ingest/`, and AI logic in `ai/`.
- `AST_module/`: streaming, speech, and audio models; `frontend/`: web assets.
- `docs/`: documentation and legacy collectors; `tests/` or `server/tests/`: Python tests.

## Build, Test, and Development Commands
- `npm ci` — install Node dependencies.
- `pip install -r requirements.txt` && `pip install -r server/requirements.txt` — install Python stacks.
- `npm run dev` — start Electron with Flask backend.
- `npm run electron` — run UI only for fast UI iteration.
- `uvicorn server.app.main:app --reload --port 8000` — start FastAPI AST service.
- `npm run build` | `npm run lint` | `npm test` — ship checks before release.

## Coding Style & Naming Conventions
- Python: 4-space indent; snake_case functions; PascalCase classes; type hints; format with `black`; lint with `flake8`.
- JavaScript: 2-space indent; camelCase vars/functions; PascalCase components; resolve `npm run lint` issues before merge.
- Use `server/utils/logger` for logging; reuse `server/utils/ring_buffer.py` for bounded buffers.

## Testing Guidelines
- Python: tests in `tests/` or `server/tests/` named `test_*.py`; run with `pytest`. Cover REST, SSE, and websockets.
- Frontend/Electron: tests in `electron/__tests__/` or `frontend/js/__tests__/` as `*.spec.js`; stub remote calls.
- Record audio fixtures and AST inputs so SenseVoice runs are reproducible.

## Commit & Pull Request Guidelines
- Conventional Commits (`feat:`, `fix:`, `chore:`); subjects ~70 characters.
- PRs link issues, list executed tests, and attach UI captures or API traces when behavior changes.
- Call out whether changes touch Flask (`server/app.py`), FastAPI (`server/app/main.py`), or both; note side effects.

## Security & Configuration Tips
- Keep secrets and local model paths out of git; document SenseVoice/FunASR download locations and checksums in PR notes.
- Review CORS and websocket origins in `server/app.py` and `server/app/main.py` before deployment.
- Confirm config edits remain Electron-friendly; verify readiness under `/api/stream/comments`.

## Agent Playbook
- Lean on Codex for route scaffolding, tuning ring buffers, and iterating hotword detection (`server/nlp/hotwords.py`).
- Update LLM prompts in `server/ai/tips.py` with measured regressions; outline side effects before large refactors.
