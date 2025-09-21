# Repository Guidelines

## Project Structure & Module Organization
- `electron/` is the desktop shell; `main.js` spawns `server/app.py` and renders the UI.
- `server/` hosts Flask (`app.py`), FastAPI (`app/main.py`), helpers (`utils/`), NLP (`nlp/`), ingest (`ingest/`), and AI (`ai/`).
- Streaming and speech assets live in `AST_module/` and `vosk-api/`; web assets sit in `frontend/`; documentation and legacy collectors stay in `docs/` and `f2/`.

## Flask API Development
- `server/app.py` provides REST endpoints plus `/api/stream/comments` SSE; keep responses lightweight for Electron readiness probes.
- Reuse `server/utils/ring_buffer.py` for bounded streaming buffers instead of ad-hoc queues.
- Tweak hotword detection inside `server/nlp/hotwords.py` and update LLM prompt templates in `server/ai/tips.py`.

## Build, Test, and Development Commands
- Install deps: `npm ci`, `pip install -r requirements.txt`, and `pip install -r server/requirements.txt` for FastAPI extras.
- Run stacks: `npm run dev` (Electron + Flask), `npm run electron` (UI only), `uvicorn server.app.main:app --reload --port 8000` (FastAPI AST).
- Ship and sanity-check: `npm run build`, `npm run lint`, `npm test`.

## Coding Style & Naming Conventions
- Python: 4-space indent, snake_case modules/functions, PascalCase classes, type hints when practical. Format with `black`, lint with `flake8`, and use `server/utils/logger` for logging.
- JavaScript: 2-space indent, camelCase variables/functions, PascalCase components. Resolve all `npm run lint` findings before committing.

## Testing Guidelines
- Place Jest specs in `electron/__tests__/` or `frontend/js/__tests__/` using `*.spec.js`; stub network calls.
- Python tests belong in `tests/` or `server/tests/`, named `test_*.py`; run with `pytest` covering success, failure, SSE, and websocket paths.
- Document audio fixtures when validating AST integrations so runs are reproducible.

## Commit & Pull Request Guidelines
- Follow Conventional Commits (`feat:`, `fix:`, `chore:`), keep subjects under ~70 chars, and isolate logical changes.
- PRs link issues, list executed tests, and attach UI captures or API traces for behavior shifts; note whether changes touch Flask, FastAPI, or both.

## Security & Configuration Tips
- Keep secrets out of git, including `config.json` edits and local model paths; record VOSK download locations and checksums in PR notes.
- Review CORS and websocket origins in Flask (`server/app.py`) and FastAPI (`server/app/main.py`) before deployment.

## Agent Playbook
- Use Codex for rapid route scaffolding, data-structure tuning (e.g., ring buffers), and optimizing hotword or prompt workflows.
- Align larger refactors with the 6A workflow and outline side effects before merging.
