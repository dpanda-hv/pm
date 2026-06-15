# Frontend agent guide

## Purpose

The `frontend/` app is the current UI-only Kanban MVP built with Next.js App Router. It is the baseline UX and interaction model that later parts will connect to the FastAPI backend.

This document describes what exists today and how to evolve it safely in future phases.

## Tech stack

- Next.js 16 (App Router)
- React 19
- TypeScript 5
- Tailwind CSS 4
- dnd-kit for drag-and-drop
- Vitest + Testing Library for unit/component tests
- Playwright for end-to-end tests

## Current behavior

- The root page renders `KanbanBoard` from `src/components/KanbanBoard.tsx`.
- Board data is in-memory React state initialized from `src/lib/kanban.ts`.
- Users can:
  - Rename columns inline.
  - Add cards and remove cards.
  - Move cards within and across columns via drag-and-drop.
- No authentication or backend API is used yet.
- No persistence exists beyond current browser state.

## Data model (frontend local)

Defined in `src/lib/kanban.ts`:

- `Card`: `id`, `title`, `details`
- `Column`: `id`, `title`, `cardIds[]`
- `BoardData`: `columns[]`, `cards` dictionary

Helper functions:

- `moveCard(columns, activeId, overId)`: pure reorder/move utility.
- `createId(prefix)`: client-side ID generation for new cards.

## Styling and visual system

- Global styles are in `src/app/globals.css`.
- Color tokens align with project palette:
  - `--accent-yellow: #ecad0a`
  - `--primary-blue: #209dd7`
  - `--secondary-purple: #753991`
  - `--navy-dark: #032147`
  - `--gray-text: #888888`
- Typography uses `Space_Grotesk` (display) and `Manrope` (body) in `src/app/layout.tsx`.

## Key files

- `src/app/page.tsx`: page entry that mounts board component.
- `src/components/KanbanBoard.tsx`: board state and interaction orchestration.
- `src/components/KanbanColumn.tsx`: per-column UI and drop zone.
- `src/components/KanbanCard.tsx`: sortable card UI.
- `src/components/NewCardForm.tsx`: add-card input workflow.
- `src/lib/kanban.ts`: data types, seed data, and move logic.

## Test coverage map

- Unit logic: `src/lib/kanban.test.ts` validates move behavior.
- Component behavior: `src/components/KanbanBoard.test.tsx` validates render/rename/add/remove flows.
- End-to-end behavior: `tests/kanban.spec.ts` validates render, add card, and drag-drop.

## Commands

From `frontend/`:

- Install deps: `npm install`
- Run dev server: `npm run dev`
- Build: `npm run build`
- Lint: `npm run lint`
- Unit tests: `npm run test:unit`
- E2E tests: `npm run test:e2e`
- Full test suite: `npm run test:all`

## Constraints for upcoming phases

- Keep UI behavior backwards compatible while introducing backend persistence.
- Preserve drag/drop semantics and deterministic card ordering.
- Avoid introducing Next.js server-runtime dependencies that conflict with static export goals.
- Keep components simple; avoid over-engineering state management.

## Planned evolution notes

- Part 3 will shift this app to static export artifacts served by FastAPI.
- Part 4 will add login gating before board access.
- Part 7 will replace local state lifecycle with backend-synced board reads/writes.
- Part 10 will add AI sidebar chat and board refresh behavior.

## Agent workflow expectation

- Treat each plan part as a hard gate.
- At end of each part, stop and request explicit user approval.
- Do not begin the next part until approval is received.
