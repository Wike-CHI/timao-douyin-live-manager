# Repository Guidelines

## Project Structure & Module Organization
- `electron/`: desktop shell; `main.js` boots Flask (`server/app.py`) and renders the bundled UI.
- `server/`: backend services. Flask REST/SSE lives in `app.py`; FastAPI AST lives in `app/main.py`; helpers in `utils/`, NLP in `nlp/`, ingestion in `ingest/`, and AI logic in `ai/`.
- `AST_module/`: speech, streaming, and audio pipelines shared by Flask and FastAPI.
- `frontend/`: web assets and renderer bundles; snapshot tests under `frontend/js/__tests__/`.
- `docs/`: process docs and legacy collectors; keep architectural updates here.
- `tests/` & `server/tests/`: Python suites; Electron specs in `electron/__tests__/`.

## Build, Test, and Development Commands
- `npm ci`: install pinned Node dependencies for the Electron shell and frontend.
- `pip install -r requirements.all.txt`: set up Python environments (Flask, FastAPI, AST tooling).
- `npm run dev`: start Electron with the Flask API for end-to-end local work.
- `npm run electron`: launch the UI against mock data for fast iteration.
- `uvicorn server.app.main:app --reload --port 8000`: run the AST FastAPI service standalone.
- `npm run build` | `npm run lint` | `npm test`: release gate checks; run before pushing.
- `pytest`: execute Python tests across Flask, FastAPI, and ingestion helpers.

## Coding Style & Naming Conventions
- Python: 4-space indent, `snake_case` functions, `PascalCase` classes, type hints. Format with `black`, lint with `flake8`.
- JavaScript/TypeScript: 2-space indent, `camelCase` functions, `PascalCase` React components. Fix `npm run lint` issues prior to review.
- Shared utilities: prefer `server/utils/logger` for logging and `server/utils/ring_buffer.py` for bounded queues.

## Testing Guidelines
- Name Python tests `test_*.py`; cover REST routes, SSE streams, and websocket edge cases.
- UI tests live in `electron/__tests__/` and `frontend/js/__tests__/`; mock remote endpoints.
- Record audio fixtures and AST inputs so SenseVoice/FunASR runs stay reproducible.
- Run `pytest` and `npm test` before submitting a PR; capture failures in the PR description.

## Commit & Pull Request Guidelines
- Use Conventional Commits (`feat:`, `fix:`, `chore:`); keep subjects under ~70 characters.
- Link issues, describe intended behavior, and list validation steps in every PR.
- Highlight whether changes touch Flask (`server/app.py`), FastAPI (`server/app/main.py`), or both, and call out any deployment or model updates.

## Security & Configuration Tips
- Keep secrets, tokens, and local model paths out of git; document SenseVoice/FunASR download steps in `docs/`.
- Review CORS/websocket origins in `server/app.py` and `server/app/main.py` before release.
- Verify `/api/stream/comments` readiness when adjusting streaming configs to remain Electron-friendly.
