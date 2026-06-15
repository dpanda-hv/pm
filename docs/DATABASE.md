# Database model (Part 5)

## Scope

This document defines the MVP database model for the Kanban board.

MVP constraints:

- One JSON board blob per user in SQLite.
- One board per user.
- Board schema optimized for simple read/replace updates in Part 6.
- Explicit card ordering is preserved through `cardIds` arrays in each column.

Future phase:

- Migrate to normalized tables for cards/columns/history after MVP.

## SQLite location and lifecycle

- DB engine: SQLite.
- DB file path (proposed): `backend/data/pm.db`.
- On backend startup, create database and tables if missing.

## SQLite schema

```sql
CREATE TABLE IF NOT EXISTS user_boards (
  user_id TEXT PRIMARY KEY,
  board_json TEXT NOT NULL,
  board_version INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_user_boards_updated_at ON user_boards(updated_at);
```

### Notes

- `user_id` supports multi-user data separation even in MVP.
- `board_json` stores the complete board payload for that user.
- `board_version` is reserved for optimistic update checks and schema evolution.
- `updated_at` supports ordering/inspection and debugging.

## Board JSON contract (MVP)

Stored in `user_boards.board_json` as serialized JSON.

```json
{
  "schemaVersion": 1,
  "columns": [
    {
      "id": "col-todo",
      "title": "To Do",
      "cardIds": ["card-1", "card-2"]
    },
    {
      "id": "col-in-progress",
      "title": "In Progress",
      "cardIds": ["card-3"]
    },
    {
      "id": "col-blocked",
      "title": "Blocked",
      "cardIds": []
    },
    {
      "id": "col-in-review",
      "title": "In Review",
      "cardIds": []
    },
    {
      "id": "col-done",
      "title": "Done",
      "cardIds": ["card-4"]
    }
  ],
  "cards": {
    "card-1": {
      "id": "card-1",
      "title": "Plan milestone",
      "details": "Define sprint objective"
    },
    "card-2": {
      "id": "card-2",
      "title": "Gather requirements",
      "details": "Talk to stakeholders"
    },
    "card-3": {
      "id": "card-3",
      "title": "Implement endpoint",
      "details": "Add read API"
    },
    "card-4": {
      "id": "card-4",
      "title": "Ship demo",
      "details": "Verify acceptance criteria"
    }
  }
}
```

### Contract rules

- `schemaVersion` must be integer `1` for MVP.
- `columns` must contain exactly 5 entries by default for first-time users:
  - `To Do`
  - `In Progress`
  - `Blocked`
  - `In Review`
  - `Done`
- Column titles can be renamed by user after initialization.
- Each `cardIds` array defines stable, explicit ordering in that column.
- Every card id referenced in `cardIds` must exist in `cards`.
- A card id must appear in exactly one column.

## Default board for new user

When `user_id` has no row, backend should create and persist a default board blob with:

- The five default columns listed above.
- Empty or seed card set (implementation decision in Part 6; empty board is acceptable).
- `schemaVersion: 1`.

## Backend persistence operations (Part 6 target)

### Read board

```sql
SELECT board_json, board_version FROM user_boards WHERE user_id = ?;
```

If missing:

- Insert default board row.
- Return default board.

### Upsert board

Simple replace-update (MVP):

```sql
INSERT INTO user_boards (user_id, board_json, board_version, updated_at)
VALUES (?, ?, 1, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
ON CONFLICT(user_id) DO UPDATE SET
  board_json = excluded.board_json,
  board_version = user_boards.board_version + 1,
  updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now');
```

## Validation checklist before write

Backend must validate incoming board payload before persisting:

- Required top-level keys: `schemaVersion`, `columns`, `cards`.
- `columns` item shape: `id`, `title`, `cardIds`.
- `cards` value shape: `id`, `title`, `details`.
- `schemaVersion == 1`.
- No duplicate column ids.
- No duplicate card ids across columns.
- All `cardIds` exist in `cards` map.

## Test plan for Part 6 implementation

These tests are defined now and should be implemented with the backend API in Part 6.

1. Schema lifecycle
- Creates table automatically when DB file does not exist.
- Inserts default board for first read of unseen user.
- Reads back persisted board for existing user.

2. Serialization/deserialization
- Round-trip board JSON without mutation.
- Rejects malformed JSON payloads.
- Rejects payloads violating ordering/reference invariants.

3. Defaults and ordering
- New board contains default columns in expected order.
- Reordered cards remain in submitted order after save/read.

4. Multi-user isolation
- User A updates do not affect User B board row.

## Tradeoffs

Pros of JSON blob MVP:

- Very simple to implement and reason about.
- Fast for whole-board read/write flows.
- Minimal SQL complexity for MVP timeline.

Cons:

- Harder to query individual cards/columns in SQL.
- Higher write amplification for small edits.
- Concurrency and partial updates are less granular.

## Normalized-schema migration (next phase)

Proposed future tables:

- `boards (id, user_id, name, updated_at)`
- `columns (id, board_id, title, position)`
- `cards (id, board_id, title, details, updated_at)`
- `column_cards (column_id, card_id, position)`
- optional `chat_messages` and `audit_events`

Migration strategy:

1. Add normalized tables alongside JSON blob table.
2. Backfill from `user_boards.board_json` to normalized records.
3. Run dual-write for one release window.
4. Switch reads to normalized source.
5. Remove JSON blob write path when stable.
