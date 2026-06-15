#!/usr/bin/env bash

set -euo pipefail

CONTAINER_NAME="pm-mvp"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required but was not found in PATH."
  exit 1
fi

if docker ps -a --format '{{.Names}}' | grep -qx "${CONTAINER_NAME}"; then
  docker rm -f "${CONTAINER_NAME}" >/dev/null
  echo "Stopped and removed ${CONTAINER_NAME}."
else
  echo "Container ${CONTAINER_NAME} is not running."
fi
