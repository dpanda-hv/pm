import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { AuthKanbanApp } from "@/components/AuthKanbanApp";

const boardFixture = {
  schemaVersion: 1,
  columns: [
    { id: "col-todo", title: "To Do", cardIds: [] },
    { id: "col-in-progress", title: "In Progress", cardIds: [] },
    { id: "col-blocked", title: "Blocked", cardIds: [] },
    { id: "col-in-review", title: "In Review", cardIds: [] },
    { id: "col-done", title: "Done", cardIds: [] },
  ],
  cards: {},
};

describe("AuthKanbanApp", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows login when session is unauthenticated", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ authenticated: false, username: null }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );

    render(<AuthKanbanApp />);

    expect(await screen.findByRole("heading", { name: /sign in to kanban/i })).toBeInTheDocument();
  });

  it("logs in successfully and renders the board", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");
    fetchMock
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ authenticated: false, username: null }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ authenticated: true, username: "user" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(boardFixture), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      );

    render(<AuthKanbanApp />);

    await screen.findByRole("heading", { name: /sign in to kanban/i });
    await userEvent.click(screen.getByRole("button", { name: /^sign in$/i }));

    expect(await screen.findByRole("heading", { name: /kanban studio/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /log out/i })).toBeInTheDocument();

    await waitFor(() => {
      expect(fetchMock).toHaveBeenNthCalledWith(
        2,
        "/api/auth/login",
        expect.objectContaining({ method: "POST" })
      );
      expect(fetchMock).toHaveBeenNthCalledWith(
        3,
        "/api/board",
        expect.objectContaining({ method: "GET" })
      );
    });
  });

  it("shows an error for invalid credentials", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");
    fetchMock
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ authenticated: false, username: null }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "Invalid credentials" }), {
          status: 401,
          headers: { "Content-Type": "application/json" },
        })
      );

    render(<AuthKanbanApp />);

    await screen.findByRole("heading", { name: /sign in to kanban/i });
    await userEvent.click(screen.getByRole("button", { name: /^sign in$/i }));

    expect(await screen.findByText(/invalid credentials/i)).toBeInTheDocument();
  });

  it("logs out and returns to sign in", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");
    fetchMock
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ authenticated: true, username: "user" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(boardFixture), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ authenticated: false }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      );

    render(<AuthKanbanApp />);

    expect(await screen.findByRole("heading", { name: /kanban studio/i })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /log out/i }));

    expect(await screen.findByRole("heading", { name: /sign in to kanban/i })).toBeInTheDocument();

    await waitFor(() => {
      expect(fetchMock).toHaveBeenNthCalledWith(
        3,
        "/api/auth/logout",
        expect.objectContaining({ method: "POST" })
      );
    });
  });

  it("shows backend unavailable error when board load fails", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");
    fetchMock
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ authenticated: true, username: "user" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
      .mockRejectedValueOnce(new Error("network down"));

    render(<AuthKanbanApp />);

    expect(
      await screen.findByText(/unable to load board from backend/i)
    ).toBeInTheDocument();
  });

  it("shows backend invalid response error when board payload is malformed", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");
    fetchMock
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ authenticated: true, username: "user" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ bad: "payload" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      );

    render(<AuthKanbanApp />);

    expect(
      await screen.findByText(/unable to load board from backend/i)
    ).toBeInTheDocument();
  });
});
