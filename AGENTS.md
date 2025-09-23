# Repository Guidelines

## Project Structure & Module Organization
- `electron/` hosts the desktop shell; `main.js` launches `server/app.py` and renders the UI.
- `server/` contains Flask (`app.py`), FastAPI (`app/main.py`), helpers in `utils/`, NLP in `nlp/`, ingest pipelines in `ingest/`, and AI logic in `ai/`.
- Streaming, speech, and audio models live in `AST_module/`; web assets stay in `frontend/`.
- Documentation and legacy collectors are under `docs/`; tests land in `tests/` or `server/tests/`.

## Build, Test, and Development Commands
- `npm ci` installs Node dependencies; `pip install -r requirements.txt` plus `pip install -r server/requirements.txt` sets up Python stacks.
- `npm run dev` boots Electron with Flask; `npm run electron` runs the UI alone for quick UI iteration.
- `uvicorn server.app.main:app --reload --port 8000` starts the FastAPI AST service.
- Ship checks: `npm run build`, `npm run lint`, and `npm test` before releasing.

## Coding Style & Naming Conventions
- Python uses 4-space indent, snake_case functions, PascalCase classes, and type hints where feasible; format with `black`, lint with `flake8`.
- JavaScript uses 2-space indent, camelCase for functions/variables, PascalCase for components; resolve `npm run lint` issues before merging.
- Prefer `server/utils/logger` for logging and reuse `server/utils/ring_buffer.py` for bounded buffers.

## Testing Guidelines
- Python tests belong in `tests/` or `server/tests/` as `test_*.py`; run with `pytest` covering REST, SSE, and websocket paths.
- Frontend or Electron specs reside in `electron/__tests__/` or `frontend/js/__tests__/` as `*.spec.js`; stub remote calls.
- Record audio fixtures and AST inputs so SenseVoice runs remain reproducible.

## Commit & Pull Request Guidelines
- Follow Conventional Commits (`feat:`, `fix:`, `chore:`) with subjects under ~70 characters.
- PRs link issues, outline executed tests, and attach UI captures or API traces when behavior shifts.
- Call out whether changes touch Flask, FastAPI, or both, and summarize any side effects.

## Security & Configuration Tips
- Keep secrets and local model paths out of git; document SenseVoice/FunASR model download locations and checksums in PR notes.
- Review Flask (`server/app.py`) and FastAPI (`server/app/main.py`) CORS and websocket origins before deployment.
- Confirm config edits remain Electron-friendly, especially readiness probes under `/api/stream/comments`.

## Agent Playbook
- Lean on Codex for route scaffolding, tuning ring buffers, and iterating hotword detection (`server/nlp/hotwords.py`).
- Update LLM prompts in `server/ai/tips.py` with measured regressions; outline side effects before large refactors.
