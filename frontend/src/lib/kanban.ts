export type Card = {
  id: number;
  title: string;
  details: string;
  label: string;
  due_date: string | null;
};

export type Column = {
  id: number;
  title: string;
  position: number;
  cards: Card[];
};

export type Board = {
  id: number;
  name: string;
  columns: Column[];
};

export type BoardSummary = {
  id: number;
  name: string;
  created_at: string;
};

export function columnDndId(columnId: number): string {
  return `col-${columnId}`;
}

export function parseColumnDndId(dndId: string | number): number | null {
  if (typeof dndId === "string" && dndId.startsWith("col-")) {
    return Number(dndId.slice(4));
  }
  return null;
}

export function findColumnByCardId(columns: Column[], cardId: number): Column | undefined {
  return columns.find((col) => col.cards.some((c) => c.id === cardId));
}

export function findContainerId(columns: Column[], dndId: string | number): number | undefined {
  const colId = parseColumnDndId(dndId);
  if (colId !== null) return colId;
  return findColumnByCardId(columns, dndId as number)?.id;
}

export function reorderCards(
  columns: Column[],
  activeId: number,
  overId: string | number,
): { columns: Column[]; targetColumnId: number; position: number } | null {
  const activeColId = findContainerId(columns, activeId);
  const overColId = findContainerId(columns, overId);
  if (!activeColId || !overColId) return null;

  const activeCol = columns.find((c) => c.id === activeColId)!;
  const overCol = columns.find((c) => c.id === overColId)!;
  const isOverCol = parseColumnDndId(overId) !== null;

  if (activeColId === overColId) {
    const oldIdx = activeCol.cards.findIndex((c) => c.id === activeId);
    const card = activeCol.cards[oldIdx];
    let newIdx: number;
    if (isOverCol) {
      newIdx = activeCol.cards.length - 1;
    } else {
      newIdx = activeCol.cards.findIndex((c) => c.id === overId);
    }
    if (oldIdx === -1 || newIdx === -1 || oldIdx === newIdx) return null;

    const next = [...activeCol.cards];
    next.splice(oldIdx, 1);
    next.splice(newIdx, 0, card);
    const newColumns = columns.map((c) =>
      c.id === activeColId ? { ...c, cards: next } : c,
    );
    return { columns: newColumns, targetColumnId: activeColId, position: newIdx };
  }

  const activeIdx = activeCol.cards.findIndex((c) => c.id === activeId);
  if (activeIdx === -1) return null;
  const card = activeCol.cards[activeIdx];

  const nextActive = [...activeCol.cards];
  nextActive.splice(activeIdx, 1);

  const nextOver = [...overCol.cards];
  let insertIdx: number;
  if (isOverCol) {
    insertIdx = nextOver.length;
  } else {
    const overIdx = overCol.cards.findIndex((c) => c.id === overId);
    insertIdx = overIdx === -1 ? nextOver.length : overIdx;
  }
  nextOver.splice(insertIdx, 0, card);

  const newColumns = columns.map((c) => {
    if (c.id === activeColId) return { ...c, cards: nextActive };
    if (c.id === overColId) return { ...c, cards: nextOver };
    return c;
  });
  return { columns: newColumns, targetColumnId: overColId, position: insertIdx };
}

export const LABEL_COLORS: Record<string, string> = {
  bug: "#e74c3c",
  feature: "#209dd7",
  improvement: "#ecad0a",
  task: "#753991",
  docs: "#888888",
};
