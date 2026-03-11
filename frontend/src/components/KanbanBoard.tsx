"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { ChatSidebar } from "@/components/ChatSidebar";
import { reorderCards, type Board, type Card } from "@/lib/kanban";
import * as api from "@/lib/api";

interface KanbanBoardProps {
  username: string;
  boardId: number;
  onLogout: () => void;
  onBack: () => void;
}

export const KanbanBoard = ({ username, boardId, onLogout, onBack }: KanbanBoardProps) => {
  const [board, setBoard] = useState<Board | null>(null);
  const [activeCardId, setActiveCardId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [editingName, setEditingName] = useState(false);
  const [boardName, setBoardName] = useState("");
  const [addingColumn, setAddingColumn] = useState(false);
  const [newColumnTitle, setNewColumnTitle] = useState("");

  const loadBoard = useCallback(async () => {
    try {
      const data = await api.fetchBoard(boardId);
      setBoard(data);
      setBoardName(data.name);
      setError(null);
    } catch {
      setError("Failed to load board");
    }
  }, [boardId]);

  useEffect(() => {
    loadBoard();
  }, [loadBoard]);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  const activeCard = useMemo(() => {
    if (!board || !activeCardId) return null;
    for (const col of board.columns) {
      const card = col.cards.find((c) => c.id === activeCardId);
      if (card) return card;
    }
    return null;
  }, [board, activeCardId]);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as number);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);
    if (!over || !board || active.id === over.id) return;

    const result = reorderCards(board.columns, active.id as number, over.id);
    if (!result) return;

    setBoard({ ...board, columns: result.columns });
    try {
      await api.moveCard(active.id as number, result.targetColumnId, result.position);
    } catch {
      setError("Failed to move card");
      loadBoard();
    }
  };

  const handleRenameColumn = async (columnId: number, title: string) => {
    if (!board) return;
    setBoard({
      ...board,
      columns: board.columns.map((col) =>
        col.id === columnId ? { ...col, title } : col
      ),
    });
    try {
      await api.renameColumn(columnId, title);
    } catch {
      setError("Failed to rename column");
      loadBoard();
    }
  };

  const handleDeleteColumn = async (columnId: number) => {
    if (!board) return;
    setBoard({
      ...board,
      columns: board.columns.filter((col) => col.id !== columnId),
    });
    try {
      await api.deleteColumn(columnId);
    } catch {
      setError("Failed to delete column");
      loadBoard();
    }
  };

  const handleAddColumn = async (e: React.FormEvent) => {
    e.preventDefault();
    const title = newColumnTitle.trim();
    if (!title || !board) return;
    try {
      await api.addColumn(boardId, title);
      setNewColumnTitle("");
      setAddingColumn(false);
      await loadBoard();
    } catch {
      setError("Failed to add column");
    }
  };

  const handleAddCard = async (columnId: number, title: string, details: string, label?: string, dueDate?: string | null) => {
    try {
      await api.createCard(columnId, title, details, label, dueDate);
      await loadBoard();
    } catch {
      setError("Failed to add card");
    }
  };

  const handleDeleteCard = async (columnId: number, cardId: number) => {
    if (!board) return;
    setBoard({
      ...board,
      columns: board.columns.map((col) =>
        col.id === columnId
          ? { ...col, cards: col.cards.filter((c) => c.id !== cardId) }
          : col
      ),
    });
    try {
      await api.deleteCard(cardId);
    } catch {
      setError("Failed to delete card");
      loadBoard();
    }
  };

  const handleUpdateCard = async (cardId: number, title: string, details: string, label?: string, dueDate?: string | null) => {
    if (!board) return;
    setBoard({
      ...board,
      columns: board.columns.map((col) => ({
        ...col,
        cards: col.cards.map((c) =>
          c.id === cardId ? { ...c, title, details, label: label ?? c.label, due_date: dueDate !== undefined ? dueDate : c.due_date } : c
        ),
      })),
    });
    try {
      await api.updateCard(cardId, { title, details, label, due_date: dueDate });
    } catch {
      setError("Failed to update card");
      loadBoard();
    }
  };

  const handleRenameBoardBlur = async () => {
    setEditingName(false);
    const name = boardName.trim();
    if (!name || !board || name === board.name) {
      setBoardName(board?.name || "");
      return;
    }
    try {
      await api.renameBoard(boardId, name);
      setBoard({ ...board, name });
    } catch {
      setError("Failed to rename board");
      setBoardName(board.name);
    }
  };

  if (!board) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-[var(--gray-text)]">
          {error || "Loading..."}
        </p>
      </div>
    );
  }

  const colCount = board.columns.length + (addingColumn ? 1 : 0);

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <div className={`flex transition-all ${chatOpen ? "pr-[400px]" : ""}`}>
        <main className="relative mx-auto flex min-h-screen max-w-[1500px] flex-1 flex-col gap-10 px-6 pb-16 pt-12">
          <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
            <div className="flex flex-wrap items-start justify-between gap-6">
              <div>
                <button
                  type="button"
                  onClick={onBack}
                  className="mb-2 text-xs font-semibold text-[var(--primary-blue)] transition hover:opacity-70"
                  data-testid="back-button"
                >
                  &larr; All Boards
                </button>
                <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                  Kanban Board
                </p>
                {editingName ? (
                  <input
                    value={boardName}
                    onChange={(e) => setBoardName(e.target.value)}
                    onBlur={handleRenameBoardBlur}
                    onKeyDown={(e) => e.key === "Enter" && (e.target as HTMLInputElement).blur()}
                    className="mt-3 w-full bg-transparent font-display text-4xl font-semibold text-[var(--navy-dark)] outline-none"
                    autoFocus
                    data-testid="board-name-input"
                  />
                ) : (
                  <h1
                    className="mt-3 cursor-pointer font-display text-4xl font-semibold text-[var(--navy-dark)]"
                    onClick={() => setEditingName(true)}
                    data-testid="board-name"
                  >
                    {board.name}
                  </h1>
                )}
              </div>
              <div className="flex items-start gap-4">
                <button
                  type="button"
                  onClick={() => setChatOpen(true)}
                  className="rounded-2xl border border-[var(--stroke)] bg-[var(--secondary-purple)] px-5 py-4 text-sm font-semibold text-white transition hover:opacity-90"
                  data-testid="chat-toggle"
                >
                  AI Chat
                </button>
                <div className="flex flex-col items-end gap-2 rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4">
                  <p className="text-xs font-semibold text-[var(--gray-text)]">
                    {username}
                  </p>
                  <button
                    type="button"
                    onClick={onLogout}
                    className="text-xs font-semibold text-[var(--primary-blue)] transition hover:opacity-70"
                    data-testid="logout-button"
                  >
                    Sign out
                  </button>
                </div>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-4">
              {board.columns.map((column) => (
                <div
                  key={column.id}
                  className="flex items-center gap-2 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]"
                >
                  <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
                  {column.title}
                </div>
              ))}
              {!addingColumn && (
                <button
                  type="button"
                  onClick={() => setAddingColumn(true)}
                  className="rounded-full border border-dashed border-[var(--stroke)] px-4 py-2 text-xs font-semibold text-[var(--gray-text)] transition hover:border-[var(--primary-blue)] hover:text-[var(--primary-blue)]"
                  data-testid="add-column-button"
                >
                  + Column
                </button>
              )}
            </div>
            {error && (
              <div className="flex items-center justify-between rounded-lg bg-red-50 px-4 py-2">
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
          </header>

          <DndContext
            sensors={sensors}
            collisionDetection={closestCorners}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
          >
            <section
              className="grid gap-6"
              style={{ gridTemplateColumns: `repeat(${colCount}, minmax(0, 1fr))` }}
            >
              {board.columns.map((column) => (
                <KanbanColumn
                  key={column.id}
                  column={column}
                  onRename={handleRenameColumn}
                  onAddCard={handleAddCard}
                  onDeleteCard={handleDeleteCard}
                  onUpdateCard={handleUpdateCard}
                  onDeleteColumn={handleDeleteColumn}
                />
              ))}
              {addingColumn && (
                <form
                  onSubmit={handleAddColumn}
                  className="flex min-h-[520px] flex-col items-center justify-center gap-3 rounded-3xl border-2 border-dashed border-[var(--stroke)] p-4"
                  data-testid="add-column-form"
                >
                  <input
                    type="text"
                    value={newColumnTitle}
                    onChange={(e) => setNewColumnTitle(e.target.value)}
                    placeholder="Column title"
                    autoFocus
                    className="w-full rounded-xl border border-[var(--stroke)] px-3 py-2 text-sm outline-none focus:border-[var(--primary-blue)]"
                    data-testid="new-column-title"
                  />
                  <div className="flex gap-2">
                    <button
                      type="submit"
                      className="rounded-xl bg-[var(--secondary-purple)] px-4 py-2 text-sm font-semibold text-white"
                    >
                      Add
                    </button>
                    <button
                      type="button"
                      onClick={() => { setAddingColumn(false); setNewColumnTitle(""); }}
                      className="rounded-xl border border-[var(--stroke)] px-3 py-2 text-xs font-semibold text-[var(--gray-text)]"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              )}
            </section>
            <DragOverlay>
              {activeCard ? (
                <div className="w-[260px]">
                  <KanbanCardPreview card={activeCard} />
                </div>
              ) : null}
            </DragOverlay>
          </DndContext>
        </main>
      </div>
      <ChatSidebar
        open={chatOpen}
        onClose={() => setChatOpen(false)}
        onBoardUpdated={loadBoard}
        boardId={boardId}
      />
    </div>
  );
};
