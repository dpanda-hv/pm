"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import type { BoardData } from "@/lib/kanban";

type SessionResponse = {
  authenticated: boolean;
  username: string | null;
};

type AIChatResponse = {
  ok: boolean;
  reply: string;
  boardUpdated: boolean;
  board: BoardData;
};

type AIChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export const AuthKanbanApp = () => {
  const [isLoadingSession, setIsLoadingSession] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState<string | null>(null);
  const [inputUsername, setInputUsername] = useState("user");
  const [inputPassword, setInputPassword] = useState("password");
  const [error, setError] = useState<string | null>(null);
  const [boardError, setBoardError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingBoard, setIsLoadingBoard] = useState(false);
  const [board, setBoard] = useState<BoardData | null>(null);
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<AIChatMessage[]>([]);
  const [chatError, setChatError] = useState<string | null>(null);
  const [isSendingChat, setIsSendingChat] = useState(false);

  const lastUserMessage = useMemo(
    () => [...chatMessages].reverse().find((message) => message.role === "user")?.content,
    [chatMessages]
  );

  useEffect(() => {
    let isMounted = true;

    const loadSession = async () => {
      try {
        const response = await fetch("/api/auth/session", {
          method: "GET",
          credentials: "same-origin",
        });
        const data = (await response.json()) as SessionResponse;
        if (!isMounted) {
          return;
        }
        setIsAuthenticated(data.authenticated);
        setUsername(data.username);
      } catch {
        if (!isMounted) {
          return;
        }
        setIsAuthenticated(false);
        setUsername(null);
      } finally {
        if (isMounted) {
          setIsLoadingSession(false);
        }
      }
    };

    void loadSession();

    return () => {
      isMounted = false;
    };
  }, []);

  const onLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: inputUsername,
          password: inputPassword,
        }),
      });

      if (!response.ok) {
        setError("Invalid credentials");
        return;
      }

      const data = (await response.json()) as SessionResponse;
      setIsAuthenticated(data.authenticated);
      setUsername(data.username);
    } catch {
      setError("Login failed. Try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const onLogout = async () => {
    setError(null);
    setIsSubmitting(true);

    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "same-origin",
      });
    } finally {
      setIsAuthenticated(false);
      setUsername(null);
      setBoard(null);
      setIsSubmitting(false);
    }
  };

  const loadBoard = useCallback(async () => {
    setIsLoadingBoard(true);
    setBoardError(null);

    try {
      const response = await fetch("/api/board", {
        method: "GET",
        credentials: "same-origin",
      });

      if (!response.ok) {
        throw new Error("board-load-failed");
      }

      const data = (await response.json()) as BoardData;
      if (!data.columns || !data.cards) {
        throw new Error("board-load-invalid");
      }

      setBoard(data);
    } catch {
      setBoardError("Unable to load board from backend.");
    } finally {
      setIsLoadingBoard(false);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }
    void loadBoard();
  }, [isAuthenticated, loadBoard]);

  const onBoardChange = (nextBoard: BoardData) => {
    setBoard(nextBoard);
    setBoardError(null);

    void (async () => {
      try {
        const response = await fetch("/api/board", {
          method: "PUT",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(nextBoard),
        });

        if (!response.ok) {
          throw new Error("board-save-failed");
        }
      } catch {
        setBoardError("Board changes could not be saved.");
      }
    })();
  };

  const runAIChat = async (message: string) => {
    if (!message.trim()) {
      return;
    }

    setChatError(null);
    setIsSendingChat(true);
    setChatMessages((previous) => [...previous, { role: "user", content: message }]);

    try {
      const response = await fetch("/api/ai/chat", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        throw new Error("ai-chat-failed");
      }

      const data = (await response.json()) as AIChatResponse;
      if (!data.reply || !data.board) {
        throw new Error("ai-chat-invalid");
      }

      setChatMessages((previous) => [
        ...previous,
        { role: "assistant", content: data.reply },
      ]);

      if (data.boardUpdated) {
        setBoard(data.board);
        await loadBoard();
      }
    } catch {
      setChatError("AI request failed. Try again.");
    } finally {
      setIsSendingChat(false);
    }
  };

  const onSubmitAIChat = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const message = chatInput.trim();
    if (!message) {
      return;
    }
    setChatInput("");
    void runAIChat(message);
  };

  const onRetryLastMessage = () => {
    if (!lastUserMessage || isSendingChat) {
      return;
    }
    void runAIChat(lastUserMessage);
  };

  if (isLoadingSession) {
    return (
      <main className="mx-auto flex min-h-screen max-w-[640px] items-center justify-center px-6">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
          Checking session...
        </p>
      </main>
    );
  }

  if (!isAuthenticated) {
    return (
      <main className="mx-auto flex min-h-screen max-w-[640px] items-center justify-center px-6">
        <section className="w-full rounded-3xl border border-[var(--stroke)] bg-white p-8 shadow-[var(--shadow)]">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
            Project Management MVP
          </p>
          <h1 className="mt-3 font-display text-3xl font-semibold text-[var(--navy-dark)]">
            Sign in to Kanban
          </h1>
          <p className="mt-3 text-sm text-[var(--gray-text)]">
            Use the MVP credentials to continue.
          </p>

          <form className="mt-8 space-y-4" onSubmit={onLogin}>
            <label className="block text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
              Username
              <input
                aria-label="Username"
                value={inputUsername}
                onChange={(event) => setInputUsername(event.target.value)}
                className="mt-2 w-full rounded-xl border border-[var(--stroke)] px-4 py-3 text-sm text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)]"
                autoComplete="username"
              />
            </label>

            <label className="block text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
              Password
              <input
                aria-label="Password"
                type="password"
                value={inputPassword}
                onChange={(event) => setInputPassword(event.target.value)}
                className="mt-2 w-full rounded-xl border border-[var(--stroke)] px-4 py-3 text-sm text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)]"
                autoComplete="current-password"
              />
            </label>

            {error ? (
              <p className="text-sm font-semibold text-[var(--secondary-purple)]">{error}</p>
            ) : null}

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full rounded-xl bg-[var(--secondary-purple)] px-4 py-3 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? "Signing in..." : "Sign in"}
            </button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <>
      <header className="sticky top-0 z-10 border-b border-[var(--stroke)] bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-[1500px] items-center justify-between px-6 py-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
              Signed in as {username}
            </p>
            {boardError ? (
              <p className="mt-1 text-xs font-semibold text-[var(--secondary-purple)]">
                {boardError}
              </p>
            ) : null}
          </div>
          <button
            type="button"
            onClick={onLogout}
            disabled={isSubmitting}
            className="rounded-lg border border-[var(--stroke)] px-3 py-2 text-xs font-semibold uppercase tracking-[0.15em] text-[var(--navy-dark)] transition hover:bg-[var(--surface)] disabled:cursor-not-allowed disabled:opacity-60"
          >
            Log out
          </button>
        </div>
      </header>
      {isLoadingBoard || !board ? (
        <main className="mx-auto flex min-h-screen max-w-[640px] items-center justify-center px-6">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
            Loading board...
          </p>
        </main>
      ) : (
        <div className="mx-auto grid min-h-[calc(100vh-72px)] w-full max-w-[1700px] gap-6 px-4 pb-8 pt-6 xl:grid-cols-[minmax(0,1fr)_360px]">
          <KanbanBoard board={board} onBoardChange={onBoardChange} />
          <aside className="flex h-[calc(100vh-112px)] flex-col rounded-3xl border border-[var(--stroke)] bg-[var(--surface-strong)] p-4 shadow-[var(--shadow)]">
            <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                AI Copilot
              </p>
              <h2 className="mt-2 font-display text-2xl font-semibold text-[var(--navy-dark)]">
                Board Assistant
              </h2>
              <p className="mt-2 text-sm leading-6 text-[var(--gray-text)]">
                Ask for card moves, edits, or summaries. Any valid board update is applied and refreshed.
              </p>
            </div>

            <div className="mt-4 flex-1 space-y-3 overflow-y-auto pr-1" aria-live="polite">
              {chatMessages.length === 0 ? (
                <p className="rounded-2xl border border-dashed border-[var(--stroke)] px-4 py-5 text-sm text-[var(--gray-text)]">
                  Try: "Move all blocked cards to In Review" or "Create a release checklist card in To Do".
                </p>
              ) : null}
              {chatMessages.map((message, index) => (
                <div
                  key={`${message.role}-${index}-${message.content}`}
                  className={
                    message.role === "user"
                      ? "ml-auto max-w-[92%] rounded-2xl bg-[var(--secondary-purple)] px-4 py-3 text-sm text-white"
                      : "mr-auto max-w-[92%] rounded-2xl border border-[var(--stroke)] bg-white px-4 py-3 text-sm text-[var(--navy-dark)]"
                  }
                >
                  {message.content}
                </div>
              ))}
              {isSendingChat ? (
                <p className="mr-auto inline-flex rounded-2xl border border-[var(--stroke)] bg-white px-4 py-3 text-sm font-semibold text-[var(--primary-blue)]">
                  Thinking...
                </p>
              ) : null}
            </div>

            {chatError ? (
              <div className="mt-3 rounded-xl border border-[var(--secondary-purple)]/30 bg-[var(--secondary-purple)]/10 p-3">
                <p className="text-sm font-semibold text-[var(--secondary-purple)]">{chatError}</p>
                <button
                  type="button"
                  onClick={onRetryLastMessage}
                  disabled={!lastUserMessage || isSendingChat}
                  className="mt-2 rounded-lg border border-[var(--secondary-purple)] px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-[var(--secondary-purple)] transition hover:bg-[var(--secondary-purple)] hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Retry last message
                </button>
              </div>
            ) : null}

            <form className="mt-4" onSubmit={onSubmitAIChat}>
              <label className="sr-only" htmlFor="ai-message-input">
                Chat message
              </label>
              <textarea
                id="ai-message-input"
                value={chatInput}
                onChange={(event) => setChatInput(event.target.value)}
                placeholder="Ask AI to update the board..."
                rows={3}
                className="w-full resize-none rounded-2xl border border-[var(--stroke)] px-4 py-3 text-sm text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)]"
              />
              <button
                type="submit"
                disabled={isSendingChat || !chatInput.trim()}
                className="mt-3 w-full rounded-xl bg-[var(--primary-blue)] px-4 py-3 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-55"
              >
                {isSendingChat ? "Sending..." : "Send to AI"}
              </button>
            </form>
          </aside>
        </div>
      )}
    </>
  );
};
