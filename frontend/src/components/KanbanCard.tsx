import { useState } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import clsx from "clsx";
import type { Card } from "@/lib/kanban";
import { LABEL_COLORS } from "@/lib/kanban";

type KanbanCardProps = {
  card: Card;
  onDelete: (cardId: number) => void;
  onUpdate: (cardId: number, title: string, details: string, label?: string, dueDate?: string | null) => void;
};

const LABELS = ["", "bug", "feature", "improvement", "task", "docs"];

export const KanbanCard = ({ card, onDelete, onUpdate }: KanbanCardProps) => {
  const { attributes, listeners, setNodeRef, setActivatorNodeRef, transform, transition, isDragging } =
    useSortable({ id: card.id });
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(card.title);
  const [editDetails, setEditDetails] = useState(card.details);
  const [editLabel, setEditLabel] = useState(card.label);
  const [editDueDate, setEditDueDate] = useState(card.due_date || "");

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const handleSave = () => {
    const trimmed = editTitle.trim();
    if (trimmed) {
      onUpdate(card.id, trimmed, editDetails, editLabel, editDueDate || null);
    }
    setEditing(false);
  };

  const handleCancel = () => {
    setEditTitle(card.title);
    setEditDetails(card.details);
    setEditLabel(card.label);
    setEditDueDate(card.due_date || "");
    setEditing(false);
  };

  const isOverdue = card.due_date && new Date(card.due_date) < new Date(new Date().toISOString().split("T")[0]);

  return (
    <article
      ref={setNodeRef}
      style={style}
      className={clsx(
        "rounded-2xl border border-transparent bg-white px-4 py-4 shadow-[0_12px_24px_rgba(3,33,71,0.08)]",
        "transition-all duration-150",
        isDragging && "opacity-60 shadow-[0_18px_32px_rgba(3,33,71,0.16)]"
      )}
      {...attributes}
      data-testid={`card-${card.id}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div
          ref={setActivatorNodeRef}
          {...listeners}
          className="mt-1 cursor-grab text-[var(--gray-text)] hover:text-[var(--navy-dark)]"
          aria-label="Drag handle"
        >
          <svg width="12" height="16" viewBox="0 0 12 16" fill="currentColor">
            <circle cx="3" cy="2" r="1.5" />
            <circle cx="9" cy="2" r="1.5" />
            <circle cx="3" cy="8" r="1.5" />
            <circle cx="9" cy="8" r="1.5" />
            <circle cx="3" cy="14" r="1.5" />
            <circle cx="9" cy="14" r="1.5" />
          </svg>
        </div>
        {editing ? (
          <div className="flex-1">
            <input
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              className="w-full rounded border border-[var(--stroke)] px-2 py-1 text-sm font-semibold text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)]"
              aria-label="Edit card title"
              autoFocus
            />
            <textarea
              value={editDetails}
              onChange={(e) => setEditDetails(e.target.value)}
              className="mt-2 w-full resize-none rounded border border-[var(--stroke)] px-2 py-1 text-sm text-[var(--gray-text)] outline-none focus:border-[var(--primary-blue)]"
              rows={2}
              aria-label="Edit card details"
            />
            <div className="mt-2 flex gap-2">
              <select
                value={editLabel}
                onChange={(e) => setEditLabel(e.target.value)}
                className="rounded border border-[var(--stroke)] px-2 py-1 text-xs text-[var(--gray-text)] outline-none"
                aria-label="Card label"
              >
                {LABELS.map((l) => (
                  <option key={l} value={l}>{l || "No label"}</option>
                ))}
              </select>
              <input
                type="date"
                value={editDueDate}
                onChange={(e) => setEditDueDate(e.target.value)}
                className="rounded border border-[var(--stroke)] px-2 py-1 text-xs text-[var(--gray-text)] outline-none"
                aria-label="Due date"
              />
            </div>
            <div className="mt-2 flex gap-2">
              <button
                type="button"
                onClick={handleSave}
                className="rounded bg-[var(--secondary-purple)] px-3 py-1 text-xs font-semibold text-white"
              >
                Save
              </button>
              <button
                type="button"
                onClick={handleCancel}
                className="rounded border border-[var(--stroke)] px-3 py-1 text-xs font-semibold text-[var(--gray-text)]"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div
            className="flex-1 cursor-pointer"
            onClick={() => {
              setEditTitle(card.title);
              setEditDetails(card.details);
              setEditLabel(card.label);
              setEditDueDate(card.due_date || "");
              setEditing(true);
            }}
          >
            <div className="flex items-center gap-2">
              {card.label && (
                <span
                  className="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase text-white"
                  style={{ backgroundColor: LABEL_COLORS[card.label] || "#888888" }}
                  data-testid={`card-label-${card.id}`}
                >
                  {card.label}
                </span>
              )}
              {card.due_date && (
                <span
                  className={clsx(
                    "text-[10px] font-semibold",
                    isOverdue ? "text-red-600" : "text-[var(--gray-text)]"
                  )}
                  data-testid={`card-due-${card.id}`}
                >
                  {card.due_date}
                </span>
              )}
            </div>
            <h4 className="font-display text-base font-semibold text-[var(--navy-dark)]">
              {card.title}
            </h4>
            <p className="mt-2 text-sm leading-6 text-[var(--gray-text)]">
              {card.details}
            </p>
          </div>
        )}
        {!editing && (
          <button
            type="button"
            onClick={() => onDelete(card.id)}
            className="rounded-full border border-transparent px-2 py-1 text-xs font-semibold text-[var(--gray-text)] transition hover:border-[var(--stroke)] hover:text-[var(--navy-dark)]"
            aria-label={`Delete ${card.title}`}
          >
            Remove
          </button>
        )}
      </div>
    </article>
  );
};
