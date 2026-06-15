FROM ghcr.io/astral-sh/uv:0.8.0-python3.12-bookworm-slim AS builder

WORKDIR /app

COPY backend/pyproject.toml /app/backend/pyproject.toml
RUN cd /app/backend && uv sync --no-dev

COPY backend /app/backend
RUN cd /app/backend && uv sync --no-dev

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/backend

COPY --from=builder /app/backend/.venv /app/backend/.venv
COPY --from=builder /app/backend/app /app/backend/app

ENV PATH="/app/backend/.venv/bin:${PATH}"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
