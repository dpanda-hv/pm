#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="pm-mvp:dev"
CONTAINER_NAME="pm-mvp"
PORT="${PORT:-8000}"

if [[ ! -f "${ROOT_DIR}/.env" ]]; then
  echo "Missing .env at ${ROOT_DIR}/.env"
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required but was not found in PATH."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon is not running."
  exit 1
fi

if lsof -Pi :"${PORT}" -sTCP:LISTEN -t >/dev/null 2>&1; then
  echo "Port ${PORT} is already in use."
  exit 1
fi

echo "Building image ${IMAGE_NAME}..."
docker build -t "${IMAGE_NAME}" "${ROOT_DIR}"

docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true

echo "Starting container ${CONTAINER_NAME} on port ${PORT}..."
docker run -d \
  --name "${CONTAINER_NAME}" \
  --env-file "${ROOT_DIR}/.env" \
  -p "${PORT}:8000" \
  "${IMAGE_NAME}" >/dev/null

echo "Waiting for service readiness..."
for _ in {1..30}; do
  if curl -fsS "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -fsS "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
  echo "Service failed to become ready."
  docker logs "${CONTAINER_NAME}" || true
  exit 1
fi

echo "Container is ready."
echo "Health: $(curl -fsS "http://127.0.0.1:${PORT}/health")"
echo "API:    $(curl -fsS "http://127.0.0.1:${PORT}/api/hello")"
echo "Open http://127.0.0.1:${PORT}/"
