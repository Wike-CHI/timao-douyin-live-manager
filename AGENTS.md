# Repository Guidelines

## Project Structure & Module Organization
- `electron/`: desktop shell; `main.js` launches `server/app.py` and renders the UI.
- `server/`: Flask `app.py` (REST/SSE) and FastAPI at `server/app/main.py` (AST). Helpers in `utils/`, NLP in `nlp/`, ingestion in `ingest/`, AI logic in `ai/`.
- `AST_module/`: streaming, speech, and audio models.
- `frontend/`: web assets.
- `docs/`: documentation and legacy collectors.
- `tests/` or `server/tests/`: Python tests. UI tests in `electron/__tests__/` and `frontend/js/__tests__/`.

## Build, Test, and Development Commands
- `npm ci` — install Node dependencies.
- `pip install -r requirements.all.txt` — install all Python stacks (FastAPI + AST + tools).
- `npm run dev` — start Electron with Flask backend.
- `npm run electron` — run UI only for fast iteration.
- `uvicorn server.app.main:app --reload --port 8000` — start FastAPI AST locally.
- `npm run build` | `npm run lint` | `npm test` — ship checks before release.
- `pytest` — run Python tests.

## Coding Style & Naming Conventions
- Python: 4-space indent; `snake_case` functions; `PascalCase` classes; type hints; format with `black`; lint with `flake8`.
- JavaScript: 2-space indent; `camelCase` vars/functions; `PascalCase` components; resolve `npm run lint` issues before merge.
- Use `server/utils/logger` for logging and `server/utils/ring_buffer.py` for bounded buffers.

## Testing Guidelines
- Python tests `test_*.py` in `tests/` or `server/tests/`; cover REST, SSE, and websockets.
- Frontend/Electron: `*.spec.js` in `electron/__tests__/` or `frontend/js/__tests__/`; stub remote calls.
- Record audio fixtures and AST inputs; make SenseVoice runs reproducible.
- Run tests: `pytest` and `npm test`.

## Commit & Pull Request Guidelines
- Conventional Commits (`feat:`, `fix:`, `chore:`); subjects ~70 characters.
- PRs link issues; describe changes; list executed tests; attach UI captures or API traces when behavior changes.
- Call out whether changes touch Flask (`server/app.py`), FastAPI (`server/app/main.py`), or both; note side effects.

## Security & Configuration Tips
- Keep secrets and local model paths out of git; document SenseVoice/FunASR downloads and checksums.
- Review CORS and websocket origins in `server/app.py` and `server/app/main.py` before deployment.
- Confirm config remains Electron-friendly; verify readiness under `/api/stream/comments`.
