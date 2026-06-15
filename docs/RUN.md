# Local run commands

## macOS

- Start: `./scripts/start-mac.sh`
- Stop: `./scripts/stop-mac.sh`

## Linux

- Start: `./scripts/start-linux.sh`
- Stop: `./scripts/stop-linux.sh`

## Windows (PowerShell)

- Start: `./scripts/start-windows.ps1`
- Stop: `./scripts/stop-windows.ps1`

## Notes

- Scripts expect `.env` at repository root.
- Default app URL is `http://127.0.0.1:8000`.
- Set `PORT` env var to override exposed local port.

## Container integration test (Part 3)

- Start container: `./scripts/start-mac.sh` (or Linux/Windows equivalent)
- Run test: from `frontend/`, `npm run test:e2e:container`
- Stop container: `./scripts/stop-mac.sh`
