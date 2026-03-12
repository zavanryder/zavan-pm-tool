"use client";

import { useEffect, useState } from "react";
import clsx from "clsx";
import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import type { Column } from "@/lib/kanban";
import { columnDndId } from "@/lib/kanban";
import { KanbanCard } from "@/components/KanbanCard";
import { NewCardForm } from "@/components/NewCardForm";

type KanbanColumnProps = {
  column: Column;
  onRename: (columnId: number, title: string) => void;
  onAddCard: (columnId: number, title: string, details: string, label?: string, dueDate?: string | null) => void;
  onDeleteCard: (columnId: number, cardId: number) => void;
  onUpdateCard: (cardId: number, title: string, details: string, label?: string, dueDate?: string | null) => void;
  onDeleteColumn: (columnId: number) => void;
};

export function KanbanColumn({
  column,
  onRename,
  onAddCard,
  onDeleteCard,
  onUpdateCard,
  onDeleteColumn,
}: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id: columnDndId(column.id) });
  const [localTitle, setLocalTitle] = useState(column.title);

  useEffect(() => {
    setLocalTitle(column.title);
  }, [column.title]);

  const commitRename = () => {
    const trimmed = localTitle.trim();
    if (trimmed && trimmed !== column.title) {
      onRename(column.id, trimmed);
    } else {
      setLocalTitle(column.title);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      (e.target as HTMLInputElement).blur();
    }
  };

  return (
    <section
      ref={setNodeRef}
      className={clsx(
        "flex min-h-[520px] flex-col rounded-3xl border border-[var(--stroke)] bg-[var(--surface-strong)] p-4 shadow-[var(--shadow)] transition",
        isOver && "ring-2 ring-[var(--accent-yellow)]"
      )}
      data-testid={`column-${column.id}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="w-full">
          <div className="flex items-center gap-3">
            <div className="h-2 w-10 rounded-full bg-[var(--accent-yellow)]" />
            <span className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
              {column.cards.length} cards
            </span>
          </div>
          <input
            value={localTitle}
            onChange={(e) => setLocalTitle(e.target.value)}
            onBlur={commitRename}
            onKeyDown={handleKeyDown}
            className="mt-3 w-full bg-transparent font-display text-lg font-semibold text-[var(--navy-dark)] outline-none"
            aria-label="Column title"
          />
        </div>
        <button
          type="button"
          onClick={() => onDeleteColumn(column.id)}
          className="mt-1 rounded-full border border-transparent px-2 py-1 text-xs font-semibold text-[var(--gray-text)] transition hover:border-[var(--stroke)] hover:text-red-600"
          aria-label={`Delete column ${column.title}`}
          title="Delete column"
        >
          x
        </button>
      </div>
      <div className="mt-4 flex flex-1 flex-col gap-3">
        <SortableContext items={column.cards.map((c) => c.id)} strategy={verticalListSortingStrategy}>
          {column.cards.map((card) => (
            <KanbanCard
              key={card.id}
              card={card}
              onDelete={(cardId) => onDeleteCard(column.id, cardId)}
              onUpdate={onUpdateCard}
            />
          ))}
        </SortableContext>
        {column.cards.length === 0 && (
          <div className="flex flex-1 items-center justify-center rounded-2xl border border-dashed border-[var(--stroke)] px-3 py-6 text-center text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
            Drop a card here
          </div>
        )}
      </div>
      <NewCardForm
        onAdd={(title, details, label, dueDate) => onAddCard(column.id, title, details, label, dueDate)}
      />
    </section>
  );
}
