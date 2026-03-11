"use client";

import { useState } from "react";

interface LoginFormProps {
  onLogin: (username: string, password: string) => Promise<void>;
  onRegister: (username: string, password: string, displayName: string) => Promise<void>;
}

export function LoginForm({ onLogin, onRegister }: LoginFormProps) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "login") {
        await onLogin(username, password);
      } else {
        await onRegister(username, password, displayName);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--surface)]">
      <div className="relative w-full max-w-md">
        <div className="pointer-events-none absolute -left-32 -top-32 h-[320px] w-[320px] rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.2)_0%,_transparent_70%)]" />
        <div className="pointer-events-none absolute -bottom-24 -right-24 h-[280px] w-[280px] rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.15)_0%,_transparent_70%)]" />

        <form
          onSubmit={handleSubmit}
          className="relative rounded-[32px] border border-[var(--stroke)] bg-white/90 p-10 shadow-[var(--shadow)] backdrop-blur"
          data-testid="login-form"
        >
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
            Project Management
          </p>
          <h1 className="mt-3 font-display text-3xl font-semibold text-[var(--navy-dark)]">
            Kanban Studio
          </h1>
          <p className="mt-2 text-sm text-[var(--gray-text)]">
            {mode === "login" ? "Sign in to your account" : "Create a new account"}
          </p>

          <div className="mt-8 flex gap-2">
            <button
              type="button"
              onClick={() => { setMode("login"); setError(""); }}
              className={`flex-1 rounded-xl px-4 py-2 text-sm font-semibold transition ${
                mode === "login"
                  ? "bg-[var(--navy-dark)] text-white"
                  : "bg-[var(--surface)] text-[var(--gray-text)]"
              }`}
              data-testid="mode-login"
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => { setMode("register"); setError(""); }}
              className={`flex-1 rounded-xl px-4 py-2 text-sm font-semibold transition ${
                mode === "register"
                  ? "bg-[var(--navy-dark)] text-white"
                  : "bg-[var(--surface)] text-[var(--gray-text)]"
              }`}
              data-testid="mode-register"
            >
              Register
            </button>
          </div>

          <div className="mt-6 flex flex-col gap-4">
            <div>
              <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[var(--stroke)] px-4 py-3 text-sm outline-none transition focus:border-[var(--primary-blue)]"
                required
                autoFocus
                data-testid="username-input"
              />
            </div>
            <div>
              <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[var(--stroke)] px-4 py-3 text-sm outline-none transition focus:border-[var(--primary-blue)]"
                required
                data-testid="password-input"
              />
            </div>
            {mode === "register" && (
              <div>
                <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
                  Display Name
                </label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="Optional"
                  className="mt-1 w-full rounded-xl border border-[var(--stroke)] px-4 py-3 text-sm outline-none transition focus:border-[var(--primary-blue)]"
                  data-testid="display-name-input"
                />
              </div>
            )}
          </div>

          {error && (
            <p className="mt-4 text-sm text-red-600" data-testid="login-error">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading || !username || !password}
            className="mt-6 w-full rounded-xl bg-[var(--secondary-purple)] px-6 py-3 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
            data-testid="submit-button"
          >
            {loading ? "Please wait..." : mode === "login" ? "Sign In" : "Create Account"}
          </button>
        </form>
      </div>
    </div>
  );
}
