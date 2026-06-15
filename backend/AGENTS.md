# Backend agent guide

## Current scope (Part 2)

- Backend is a minimal FastAPI scaffold running in Docker.
- Routes currently implemented:
	- `GET /health` for readiness checks.
	- `GET /api/hello` for API smoke validation.
	- `GET /` serving static `backend/app/static/index.html`.

## Runtime model

- Backend runs in a container from the root multi-stage `Dockerfile`.
- Python dependencies are managed with `uv` using `backend/pyproject.toml`.
- App entrypoint: `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

## What this backend does not include yet

- Authentication/session endpoints.
- Database integration.
- Kanban board persistence APIs.
- AI/OpenRouter connectivity.

## Expectations for next phases

- Keep API surface minimal and focused per plan part.
- Add tests alongside each new endpoint and behavior.
- Preserve compatibility with static frontend serving from FastAPI.