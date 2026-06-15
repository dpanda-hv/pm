"use client";

import { FormEvent, useEffect, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";

type SessionResponse = {
  authenticated: boolean;
  username: string | null;
};

export const AuthKanbanApp = () => {
  const [isLoadingSession, setIsLoadingSession] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState<string | null>(null);
  const [inputUsername, setInputUsername] = useState("user");
  const [inputPassword, setInputPassword] = useState("password");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

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
      setIsSubmitting(false);
    }
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
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
            Signed in as {username}
          </p>
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
      <KanbanBoard />
    </>
  );
};
