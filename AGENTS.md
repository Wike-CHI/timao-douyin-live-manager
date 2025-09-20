# Repository Guidelines

## Project Structure & Module Organization
- `electron/` hosts the desktop shell; `main.js` boots the Flask API and loads the renderer UI.
- `server/` runs Flask (`app.py`) and FastAPI (`app/main.py`) services with shared helpers in `utils/`, NLP flows in `nlp/`, and ingest jobs in `ingest/`.
- Speech tooling sits in `AST_module/`, VOSK assets in `vosk-api/`, prototype UIs in `frontend/`, and legacy collectors in `f2/`; additional references live in `docs/`.

## Build, Test, and Development Commands
- Install JavaScript deps with `npm ci`; bootstrap Flask deps via `pip install -r requirements.txt` and FastAPI extras via `pip install -r server/requirements.txt`.
- Start the full Electron + Flask stack using `npm run dev`, or launch only the shell for UI debugging with `npm run electron`.
- Package the desktop app with `npm run build`; lint JS via `npm run lint` and run renderer tests through `npm test`.
- Spin up the experimental FastAPI stack for AST workflows with `uvicorn server.app.main:app --reload --port 8000`.

## Coding Style & Naming Conventions
- Use 4-space indentation for Python, keep modules snake_case, classes PascalCase, and functions snake_case with type hints when available.
- JavaScript uses 2-space indentation, camelCase for functions/variables, and PascalCase for components. Run `npm run lint` and address `eslint` feedback before committing.
- Format Python code with `black`, enforce linting via `flake8`, and log through `server/utils/` helpers instead of `print`.

## Testing Guidelines
- House Jest specs under `electron/__tests__/` or `frontend/js/__tests__/`, using `*.spec.js` filenames and mocking network calls for determinism.
- Python tests belong under `tests/` (or scoped `server/tests/`) and should start with `test_`. Use `pytest` for new suites and cover success, failure, and websocket flows.
- Validate AST integrations with short end-to-end scripts when practical, capturing audio sample paths in the test notes.

## Commit & Pull Request Guidelines
- Follow the existing Conventional Commits style (`feat:`, `fix:`, `chore:`), keep subjects under ~70 chars, and bundle one logical change per commit.
- PRs should link issues, list executed tests, and include UI screenshots or API traces when behavior changes. Call out FastAPI vs Flask impacts explicitly.

## Security & Configuration Tips
- Keep secrets out of version control; avoid committing modified `config.json` or local model paths.
- Document VOSK model downloads and checksums when sharing updates, and double-check CORS/websocket origins in both Flask and FastAPI configs before release.
