"use client";

import { useCallback, useEffect, useState } from "react";
import * as api from "@/lib/api";
import type { BoardSummary } from "@/lib/kanban";

interface BoardSelectorProps {
  username: string;
  onSelect: (boardId: number) => void;
  onLogout: () => void;
}

export function BoardSelector({ username, onSelect, onLogout }: BoardSelectorProps) {
  const [boards, setBoards] = useState<BoardSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [error, setError] = useState<string | null>(null);

  const loadBoards = useCallback(async () => {
    try {
      const data = await api.listBoards();
      setBoards(data);
      setError(null);
    } catch {
      setError("Failed to load boards");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadBoards();
  }, [loadBoards]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const name = newName.trim();
    if (!name) return;
    try {
      const board = await api.createBoard(name);
      setNewName("");
      setCreating(false);
      onSelect(board.id);
    } catch {
      setError("Failed to create board");
    }
  };

  const handleDelete = async (boardId: number) => {
    try {
      await api.deleteBoard(boardId);
      setBoards((prev) => prev.filter((b) => b.id !== boardId));
    } catch {
      setError("Failed to delete board");
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-[var(--surface)]">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <div className="relative mx-auto max-w-3xl px-6 pb-16 pt-12">
        <header className="flex items-start justify-between rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
              Project Management
            </p>
            <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
              Your Boards
            </h1>
            <p className="mt-3 text-sm text-[var(--gray-text)]">
              Select a board to open, or create a new one.
            </p>
          </div>
          <div className="flex flex-col items-end gap-2 rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4">
            <p className="text-xs font-semibold text-[var(--gray-text)]">{username}</p>
            <button
              type="button"
              onClick={onLogout}
              className="text-xs font-semibold text-[var(--primary-blue)] transition hover:opacity-70"
              data-testid="logout-button"
            >
              Sign out
            </button>
          </div>
        </header>

        {error && (
          <div className="mt-4 flex items-center justify-between rounded-lg bg-red-50 px-4 py-2">
            <p className="text-sm text-red-600">{error}</p>
            <button
              type="button"
              onClick={() => setError(null)}
              className="text-xs font-semibold text-red-400 hover:text-red-600"
            >
              Dismiss
            </button>
          </div>
        )}

        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {loading && (
            <p className="col-span-full text-center text-sm text-[var(--gray-text)]">
              Loading...
            </p>
          )}

          {!loading && boards.map((board) => (
            <div
              key={board.id}
              className="group flex flex-col justify-between rounded-2xl border border-[var(--stroke)] bg-white p-6 shadow-[var(--shadow)] transition hover:border-[var(--primary-blue)]"
              data-testid={`board-${board.id}`}
            >
              <div>
                <h3 className="font-display text-lg font-semibold text-[var(--navy-dark)]">
                  {board.name}
                </h3>
                <p className="mt-1 text-xs text-[var(--gray-text)]">
                  Created {new Date(board.created_at).toLocaleDateString()}
                </p>
              </div>
              <div className="mt-4 flex gap-2">
                <button
                  type="button"
                  onClick={() => onSelect(board.id)}
                  className="flex-1 rounded-xl bg-[var(--secondary-purple)] px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90"
                  data-testid={`open-board-${board.id}`}
                >
                  Open
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(board.id)}
                  className="rounded-xl border border-[var(--stroke)] px-3 py-2 text-xs font-semibold text-[var(--gray-text)] transition hover:border-red-300 hover:text-red-600"
                  data-testid={`delete-board-${board.id}`}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}

          {!loading && !creating && (
            <button
              type="button"
              onClick={() => setCreating(true)}
              className="flex min-h-[140px] items-center justify-center rounded-2xl border-2 border-dashed border-[var(--stroke)] p-6 text-sm font-semibold text-[var(--gray-text)] transition hover:border-[var(--primary-blue)] hover:text-[var(--primary-blue)]"
              data-testid="new-board-button"
            >
              + New Board
            </button>
          )}

          {creating && (
            <form
              onSubmit={handleCreate}
              className="flex min-h-[140px] flex-col justify-center gap-3 rounded-2xl border border-[var(--stroke)] bg-white p-6 shadow-[var(--shadow)]"
              data-testid="new-board-form"
            >
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Board name"
                autoFocus
                className="rounded-xl border border-[var(--stroke)] px-3 py-2 text-sm outline-none transition focus:border-[var(--primary-blue)]"
                data-testid="new-board-name"
              />
              <div className="flex gap-2">
                <button
                  type="submit"
                  className="flex-1 rounded-xl bg-[var(--secondary-purple)] px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90"
                >
                  Create
                </button>
                <button
                  type="button"
                  onClick={() => { setCreating(false); setNewName(""); }}
                  className="rounded-xl border border-[var(--stroke)] px-3 py-2 text-xs font-semibold text-[var(--gray-text)]"
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
