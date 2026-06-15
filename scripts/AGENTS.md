# Scripts agent guide

## Purpose

This folder contains start/stop scripts for macOS, Linux, and Windows to manage the local Dockerized app lifecycle.

## Scripts

- `start-mac.sh`
- `stop-mac.sh`
- `start-linux.sh`
- `stop-linux.sh`
- `start-windows.ps1`
- `stop-windows.ps1`

## Start script responsibilities

- Verify `.env` exists at repository root.
- Verify Docker CLI and daemon availability.
- Verify target port is free.
- Build image and run container.
- Wait for readiness via `GET /health`.
- Perform API smoke call via `GET /api/hello`.

## Stop script responsibilities

- Stop and remove `pm-mvp` container if present.
- Exit cleanly if container is not running.