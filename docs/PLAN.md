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

- [ ] Wire fully static Next export into Docker build output.
- [ ] Serve exported assets from FastAPI at `/`.
- [ ] Ensure existing demo Kanban renders correctly from static build.
- [ ] Preserve current frontend behavior from baseline demo.
- [ ] Add and run unit/integration tests for this integration.
- [ ] Request approval for Part 4.

### Tests

- [ ] Frontend unit tests pass.
- [ ] Frontend integration test confirms Kanban renders at `/` in container.
- [ ] Static asset routing works for direct page reloads.
- [ ] Coverage is at least 80% for frontend scope touched.

### Success criteria

- Demo Kanban is visible at `/` from containerized app without Next runtime server.

## Part 4: MVP sign-in flow

### Checklist

- [ ] Add login screen at first visit.
- [ ] Validate fixed credentials (`user` / `password`).
- [ ] Add logout capability.
- [ ] Implement in-memory session handling that resets on restart.
- [ ] Guard board access for unauthenticated users.
- [ ] Add tests and request approval for Part 5.

### Tests

- [ ] Login success path test.
- [ ] Login failure path test.
- [ ] Protected route test for unauthenticated state.
- [ ] Logout invalidates access.
- [ ] Session reset verified after container restart.
- [ ] Coverage remains at least 80% for touched scopes.

### Success criteria

- Only authenticated sessions can access the board and logout works reliably.

## Part 5: Database modeling (JSON blob)

### Checklist

- [ ] Design SQLite schema using one board JSON blob per user.
- [ ] Define JSON contract for board data including explicit card ordering.
- [ ] Include default columns: To Do, In Progress, Blocked, In Review, Done.
- [ ] Document rationale and tradeoffs in docs.
- [ ] Include a future-phase note for normalized schema migration.
- [ ] Request explicit user sign-off before Part 6.

### Tests

- [ ] Schema validation tests for create/read/update lifecycle.
- [ ] JSON serialization/deserialization test coverage.
- [ ] Default board shape test for first-time user.

### Success criteria

- Database contract is approved and implementation-ready with clear migration path.

## Part 6: Backend board API

### Checklist

- [ ] Implement DB initialization if file does not exist.
- [ ] Add authenticated API routes for board read/write operations.
- [ ] Support card create/edit/move with order persistence.
- [ ] Enforce validation for incoming board mutation payloads.
- [ ] Add backend unit and integration tests.
- [ ] Request approval for Part 7.

### Tests

- [ ] DB auto-create on first run.
- [ ] Authorized board read/write happy paths.
- [ ] Invalid payload and unauthorized access handling.
- [ ] Card move operations maintain deterministic ordering.
- [ ] Coverage is at least 80% for backend touched scope.

### Success criteria

- Backend API safely persists and returns board state per user.

## Part 7: Frontend and backend connection

### Checklist

- [ ] Replace local-only state with backend API integration.
- [ ] Load board from backend on app start.
- [ ] Persist board changes on user actions.
- [ ] Handle loading/error states with simple UX.
- [ ] Add robust integration tests for end-to-end board interactions.
- [ ] Request approval for Part 8.

### Tests

- [ ] End-to-end test for login, load board, mutate board, refresh, and persistence.
- [ ] Error-path tests for backend unavailable and invalid responses.
- [ ] Coverage remains at least 80% for touched scopes.

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