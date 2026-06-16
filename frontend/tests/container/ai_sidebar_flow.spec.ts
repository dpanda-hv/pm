import { expect, test } from "@playwright/test";

type Card = {
  id: string;
  title: string;
  details: string;
};

type Column = {
  id: string;
  title: string;
  cardIds: string[];
};

type BoardState = {
  schemaVersion: number;
  columns: Column[];
  cards: Record<string, Card>;
};

const createBoardState = (): BoardState => ({
  schemaVersion: 1,
  columns: [
    { id: "col-todo", title: "To Do", cardIds: ["card-a"] },
    { id: "col-in-progress", title: "In Progress", cardIds: [] },
    { id: "col-blocked", title: "Blocked", cardIds: [] },
    { id: "col-in-review", title: "In Review", cardIds: [] },
    { id: "col-done", title: "Done", cardIds: [] },
  ],
  cards: {
    "card-a": {
      id: "card-a",
      title: "Release checklist",
      details: "Prepare launch tasks.",
    },
  },
});

test("AI sidebar chat applies board mutation and renders conversation", async ({ page }) => {
  let boardState = createBoardState();

  await page.route("**/api/auth/session", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ authenticated: true, username: "user" }),
    });
  });

  await page.route("**/api/board", async (route) => {
    const request = route.request();

    if (request.method() === "PUT") {
      const payload = request.postDataJSON() as BoardState;
      boardState = payload;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(boardState),
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(boardState),
    });
  });

  await page.route("**/api/ai/chat", async (route) => {
    boardState = {
      ...boardState,
      columns: boardState.columns.map((column) =>
        column.id === "col-todo" ? { ...column, title: "Planned" } : column
      ),
    };

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        ok: true,
        reply: "Renamed To Do to Planned.",
        boardUpdated: true,
        board: boardState,
      }),
    });
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: /kanban studio/i })).toBeVisible();

  await page.getByLabel("Chat message").fill("Rename To Do to Planned");
  await page.getByRole("button", { name: /send to ai/i }).click();

  await expect(page.getByText("Rename To Do to Planned")).toBeVisible();
  await expect(page.getByText("Renamed To Do to Planned.")).toBeVisible();
  await expect(page.locator('input[aria-label="Column title"][value="Planned"]')).toBeVisible();
});

test("manual drag and drop still works after AI board update", async ({ page }) => {
  let boardState = createBoardState();

  await page.route("**/api/auth/session", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ authenticated: true, username: "user" }),
    });
  });

  await page.route("**/api/board", async (route) => {
    const request = route.request();

    if (request.method() === "PUT") {
      const payload = request.postDataJSON() as BoardState;
      boardState = payload;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(boardState),
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(boardState),
    });
  });

  await page.route("**/api/ai/chat", async (route) => {
    boardState = {
      ...boardState,
      columns: boardState.columns.map((column) =>
        column.id === "col-in-progress" ? { ...column, title: "Active" } : column
      ),
    };

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        ok: true,
        reply: "Renamed In Progress to Active.",
        boardUpdated: true,
        board: boardState,
      }),
    });
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: /kanban studio/i })).toBeVisible();

  await page.getByLabel("Chat message").fill("Rename In Progress to Active");
  await page.getByRole("button", { name: /send to ai/i }).click();
  await expect(page.locator('input[aria-label="Column title"][value="Active"]')).toBeVisible();

  const card = page.getByTestId("card-card-a");
  const targetColumn = page.getByTestId("column-col-in-progress");

  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(cardBox.x + cardBox.width / 2, cardBox.y + cardBox.height / 2);
  await page.mouse.down();
  await page.mouse.move(columnBox.x + columnBox.width / 2, columnBox.y + 120, {
    steps: 12,
  });
  await page.mouse.up();

  await expect(targetColumn.getByTestId("card-card-a")).toBeVisible();
});
