import { useState } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import clsx from "clsx";
import type { Card } from "@/lib/kanban";

type KanbanCardProps = {
  card: Card;
  onDelete: (cardId: number) => void;
  onUpdate: (cardId: number, title: string, details: string) => void;
};

export const KanbanCard = ({ card, onDelete, onUpdate }: KanbanCardProps) => {
  const { attributes, listeners, setNodeRef, setActivatorNodeRef, transform, transition, isDragging } =
    useSortable({ id: card.id });
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(card.title);
  const [editDetails, setEditDetails] = useState(card.details);

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const handleSave = () => {
    const trimmed = editTitle.trim();
    if (trimmed) {
      onUpdate(card.id, trimmed, editDetails);
    }
    setEditing(false);
  };

  const handleCancel = () => {
    setEditTitle(card.title);
    setEditDetails(card.details);
    setEditing(false);
  };

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
              setEditing(true);
            }}
          >
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
