import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { AuthKanbanApp } from "@/components/AuthKanbanApp";

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
        2,
        "/api/auth/logout",
        expect.objectContaining({ method: "POST" })
      );
    });
  });
});
