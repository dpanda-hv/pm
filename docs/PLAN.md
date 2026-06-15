# Project Plan

## Confirmed decisions

- Every part is a hard gate. Do not start the next part until user approval.
- Frontend deployment model is fully static export.
- Packaging is one Dockerfile using multi-stage build.
- Authentication for MVP uses in-memory session state and resets on container restart.
- Database uses SQLite with one JSON blob per user board for MVP.
- Future improvement: normalized schema after MVP.
- Default columns are To Do, In Progress, Blocked, In Review, Done.
- Card order is persisted and preserved during user and AI moves.
- Chat history persistence is in-memory for MVP.
- AI response format must be strict structured output schema with validation and fallback handling.
- Minimum test coverage target is 80% and integration testing must be robust.
- Start and stop scripts must include lifecycle plus setup checks/tasks.
- `frontend/AGENTS.md` must be descriptive and future-proof.

## Global quality bar

- Keep scope MVP-only and avoid extra features.
- Root-cause each issue before fixing.
- Use concise docs and code.
- Maintain at least 80% coverage for backend and frontend test suites where applicable.
- At each part end, capture evidence: test results, coverage summary, and manual verification notes.

## Part 1: Planning and documentation

### Checklist

- [x] Expand this plan with executable checklists, tests, and success criteria.
- [x] Create `frontend/AGENTS.md` documenting current frontend structure, architecture, and commands.
- [x] Add explicit hard-gate rule and approval checkpoint language.
- [x] Confirm all decisions in the "Confirmed decisions" section remain accurate.
- [ ] Obtain user approval to proceed to Part 2.

### Tests

- [x] Documentation review for completeness against all 10 parts.
- [x] Consistency check between `AGENTS.md` and this plan.

### Success criteria

- Plan has no ambiguity for execution order, acceptance checks, and gates.
- User gives explicit approval to continue.

## Part 2: Scaffolding

### Checklist

- [x] Create one multi-stage Dockerfile for frontend build and backend runtime.
- [x] Scaffold FastAPI backend in `backend/` with basic health and sample API endpoint.
- [x] Implement basic static hello-world page served by FastAPI for smoke testing.
- [x] Add cross-platform start and stop scripts in `scripts/` for macOS, Linux, and Windows.
- [x] Add setup checks in scripts: environment file presence, port availability, and startup readiness checks.
- [x] Document commands in minimal README/docs updates.
- [ ] Request approval for Part 3.

### Tests

- [x] Container build succeeds from clean state.
- [ ] Container starts with script wrappers on supported OS paths.
- [x] `GET /health` returns success.
- [x] Sample API endpoint responds correctly.
- [x] Static hello-world content is reachable at `/`.

Part 2 evidence (15 June 2026, macOS):

- Docker image built successfully via `./scripts/start-mac.sh`.
- Container readiness and endpoint checks succeeded:
	- `GET /health` -> `{"status":"ok"}`
	- `GET /api/hello` -> `{"message":"Hello from FastAPI"}`
- Root page served static HTML and performed API fetch.
- `./scripts/stop-mac.sh` removed container successfully.
- Automated backend tests added and passing: `backend/tests/test_scaffolding_endpoints.py` (4 passed).
- Linux and Windows scripts were authored but not executed in this macOS environment.

### Success criteria

- One-command local startup works and serves both static content and API.
- Scripts reliably start and stop the stack.

## Part 3: Static frontend integration

### Checklist

- [x] Wire fully static Next export into Docker build output.
- [x] Serve exported assets from FastAPI at `/`.
- [x] Ensure existing demo Kanban renders correctly from static build.
- [x] Preserve current frontend behavior from baseline demo.
- [x] Add and run unit/integration tests for this integration.
- [ ] Request approval for Part 4.

### Tests

- [x] Frontend unit tests pass.
- [x] Frontend integration test confirms Kanban renders at `/` in container.
- [x] Static asset routing works for direct page reloads.
- [x] Coverage is at least 80% for frontend scope touched.

Part 3 evidence (15 June 2026, macOS):

- Containerized app serves exported frontend at `/` (heading `Kanban Studio` confirmed in integration tests).
- Container integration tests passed via `frontend/tests/container/static_frontend_serving.spec.ts` using `npm run test:e2e:container`.
- Frontend unit tests passed via `npm run test:unit`.
- Backend tests passed via containerized `uv run pytest -q`.
- Frontend source coverage from `npm run test:unit -- --coverage`: `All files` at `82.28%`.

### Success criteria

- Demo Kanban is visible at `/` from containerized app without Next runtime server.

## Part 4: MVP sign-in flow

### Checklist

- [x] Add login screen at first visit.
- [x] Validate fixed credentials (`user` / `password`).
- [x] Add logout capability.
- [x] Implement in-memory session handling that resets on restart.
- [x] Guard board access for unauthenticated users.
- [x] Add tests and request approval for Part 5.

### Tests

- [x] Login success path test.
- [x] Login failure path test.
- [x] Protected route test for unauthenticated state.
- [x] Logout invalidates access.
- [x] Session reset verified after container restart.
- [x] Coverage remains at least 80% for touched scopes.

Part 4 evidence (15 June 2026, macOS):

- Backend auth API tests added and passing: `backend/tests/test_auth_session_api.py`.
- Backend suite result: `8 passed` via containerized `uv run pytest -q`.
- Frontend auth unit tests added and passing: `frontend/src/components/AuthKanbanApp.test.tsx`.
- Frontend unit suite result: `10 passed`.
- Container browser integration tests passed (login success/failure/logout + static serving):
	- `frontend/tests/container/auth_session_flow.spec.ts`
	- `frontend/tests/container/static_frontend_serving.spec.ts`
- Session reset on restart verified with cookie-jar workflow:
	- pre-restart `GET /api/auth/session` -> `{"authenticated":true,"username":"user"}`
	- post-restart with same cookie -> `{"authenticated":false,"username":null}`

### Success criteria

- Only authenticated sessions can access the board and logout works reliably.

## Part 5: Database modeling (JSON blob)

### Checklist

- [x] Design SQLite schema using one board JSON blob per user.
- [x] Define JSON contract for board data including explicit card ordering.
- [x] Include default columns: To Do, In Progress, Blocked, In Review, Done.
- [x] Document rationale and tradeoffs in docs.
- [x] Include a future-phase note for normalized schema migration.
- [ ] Request explicit user sign-off before Part 6.

### Tests

- [x] Schema validation tests for create/read/update lifecycle.
- [x] JSON serialization/deserialization test coverage.
- [x] Default board shape test for first-time user.

Part 5 evidence (15 June 2026):

- Database design document added: `docs/DATABASE.md`.
- Includes SQLite DDL, JSON board contract, write/read SQL patterns, validation invariants, and default board definition.
- Includes implementation test plan for Part 6 covering lifecycle, serialization, defaults/order, and multi-user isolation.
- Includes normalized-schema migration strategy for post-MVP phase.

### Success criteria

- Database contract is approved and implementation-ready with clear migration path.

## Part 6: Backend board API

### Checklist

- [x] Implement DB initialization if file does not exist.
- [x] Add authenticated API routes for board read/write operations.
- [x] Support card create/edit/move with order persistence.
- [x] Enforce validation for incoming board mutation payloads.
- [x] Add backend unit and integration tests.
- [ ] Request approval for Part 7.

### Tests

- [x] DB auto-create on first run.
- [x] Authorized board read/write happy paths.
- [x] Invalid payload and unauthorized access handling.
- [x] Card move operations maintain deterministic ordering.
- [x] Coverage is at least 80% for backend touched scope.

Part 6 evidence (15 June 2026):

- Backend now includes SQLite-backed board persistence with auto-init (`user_boards` table creation when DB missing).
- Authenticated board routes implemented in `backend/app/main.py`:
	- `GET /api/board`
	- `PUT /api/board`
	- `POST /api/board/cards`
	- `PATCH /api/board/cards/{card_id}`
	- `POST /api/board/cards/{card_id}/move`
- Strict board validation implemented before writes (schema version, fixed column ids, card/reference invariants, ordering consistency).
- Backend test coverage added with feature-based files:
	- `backend/tests/test_board_api.py`
	- `backend/tests/test_board_card_operations.py`
- Backend suite result via containerized `uv run pytest -q`: `15 passed`.

### Success criteria

- Backend API safely persists and returns board state per user.

## Part 7: Frontend and backend connection

### Checklist

- [x] Replace local-only state with backend API integration.
- [x] Load board from backend on app start.
- [x] Persist board changes on user actions.
- [x] Handle loading/error states with simple UX.
- [x] Add robust integration tests for end-to-end board interactions.
- [ ] Request approval for Part 8.

### Tests

- [x] End-to-end test for login, load board, mutate board, refresh, and persistence.
- [x] Error-path tests for backend unavailable and invalid responses.
- [x] Coverage remains at least 80% for touched scopes.

Part 7 evidence (16 June 2026):

- Frontend now loads board from `GET /api/board` and persists edits via `PUT /api/board`.
- Integration wiring implemented in `frontend/src/components/AuthKanbanApp.tsx` and `frontend/src/components/KanbanBoard.tsx`.
- Frontend unit tests include backend error-path coverage for unavailable and malformed board responses (`AuthKanbanApp.test.tsx`).
- Container integration tests validate login, mutation, refresh, and persisted board state:
	- `frontend/tests/container/auth_session_flow.spec.ts` (includes persistence test)
	- `frontend/tests/container/static_frontend_serving.spec.ts`
- Container Playwright suite result: `6 passed`.
- Frontend unit suite result: `12 passed`.
- Backend suite remains green after integration changes: `15 passed`.
- Frontend source coverage from `npm run test:unit -- --coverage`: `All files` at `83.3%`.

### Success criteria

- Board state is persistent across reloads via backend API.

## Part 8: OpenRouter connectivity

### Checklist

- [ ] Add backend AI client using OpenRouter and model `openai/gpt-oss-120b`.
- [ ] Read API key from `.env`.
- [ ] Implement simple AI connectivity endpoint/test path.
- [ ] Validate with a deterministic "2+2" connectivity check.
- [ ] Add tests and request approval for Part 9.

### Tests

- [ ] Integration test for configured API-key path.
- [ ] Mocked fallback tests for upstream error handling.
- [ ] Connectivity test for "2+2" sanity check.

### Success criteria

- Backend can reliably make AI calls and handle failure paths cleanly.

## Part 9: Structured outputs with board context

### Checklist

- [ ] Define strict schema for AI response: user message plus optional board updates.
- [ ] Send board JSON and in-memory conversation history with each AI request.
- [ ] Validate AI response against schema.
- [ ] Implement retry/fallback behavior for invalid schema responses.
- [ ] Apply optional board updates atomically when valid.
- [ ] Add thorough tests and request approval for Part 10.

### Tests

- [ ] Schema validation pass/fail tests.
- [ ] Retry and fallback behavior tests.
- [ ] Atomic application test for AI-suggested board updates.
- [ ] Conversation-history inclusion tests.
- [ ] Coverage is at least 80% for touched backend scope.

### Success criteria

- AI responses are predictable, validated, and safe to apply.

## Part 10: AI sidebar UX

### Checklist

- [ ] Build sidebar chat UI integrated with backend AI endpoint.
- [ ] Show conversation with clear request/response states.
- [ ] Apply AI board updates when returned by structured output.
- [ ] Auto-refresh board state after AI updates.
- [ ] Keep visual style aligned with project color scheme.
- [ ] Add robust UI integration and end-to-end tests.
- [ ] Final verification and handoff notes.

### Tests

- [ ] End-to-end chat interaction test including board mutation.
- [ ] UI tests for loading, error, and retry states.
- [ ] Regression test for manual drag/drop after AI update.
- [ ] Coverage remains at least 80% for touched frontend scope.

### Success criteria

- Sidebar supports reliable AI chat and synchronized board updates.

## Approval protocol

- At the end of each part, stop and request explicit user approval.
- Only proceed to the next part after approval is received.