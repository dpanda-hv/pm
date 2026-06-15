FROM node:20-bookworm-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend /app/frontend
RUN npm run build

FROM ghcr.io/astral-sh/uv:0.8.0-python3.12-bookworm-slim AS backend-builder

WORKDIR /app

COPY backend/pyproject.toml /app/backend/pyproject.toml
RUN cd /app/backend && uv sync --no-dev

COPY backend /app/backend
RUN cd /app/backend && uv sync --no-dev

FROM ghcr.io/astral-sh/uv:0.8.0-python3.12-bookworm-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/backend

COPY --from=backend-builder /app/backend/.venv /app/backend/.venv
COPY --from=backend-builder /app/backend/app /app/backend/app
COPY --from=frontend-builder /app/frontend/out /app/backend/app/static

ENV PATH="/app/backend/.venv/bin:${PATH}"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
