import { describe, it, expect } from "vitest";
import { reorderCards, type Column } from "./kanban";

const makeColumns = (): Column[] => [
  { id: 1, title: "A", position: 0, cards: [
    { id: 10, title: "Card 1", details: "", label: "", due_date: null },
    { id: 11, title: "Card 2", details: "", label: "", due_date: null },
    { id: 12, title: "Card 3", details: "", label: "", due_date: null },
  ]},
  { id: 2, title: "B", position: 1, cards: [
    { id: 20, title: "Card 4", details: "", label: "", due_date: null },
  ]},
  { id: 3, title: "C", position: 2, cards: [] },
];

describe("reorderCards", () => {
  it("reorders within the same column", () => {
    const result = reorderCards(makeColumns(), 12, 10);
    expect(result).not.toBeNull();
    const col = result!.columns.find((c) => c.id === 1)!;
    expect(col.cards.map((c) => c.id)).toEqual([12, 10, 11]);
    expect(result!.targetColumnId).toBe(1);
    expect(result!.position).toBe(0);
  });

  it("moves a card to another column", () => {
    const result = reorderCards(makeColumns(), 10, 20);
    expect(result).not.toBeNull();
    const colA = result!.columns.find((c) => c.id === 1)!;
    const colB = result!.columns.find((c) => c.id === 2)!;
    expect(colA.cards.map((c) => c.id)).toEqual([11, 12]);
    expect(colB.cards.map((c) => c.id)).toEqual([10, 20]);
    expect(result!.targetColumnId).toBe(2);
  });

  it("drops to an empty column", () => {
    const result = reorderCards(makeColumns(), 10, 3);
    expect(result).not.toBeNull();
    const colA = result!.columns.find((c) => c.id === 1)!;
    const colC = result!.columns.find((c) => c.id === 3)!;
    expect(colA.cards.map((c) => c.id)).toEqual([11, 12]);
    expect(colC.cards.map((c) => c.id)).toEqual([10]);
    expect(result!.targetColumnId).toBe(3);
  });

  it("returns null for same position", () => {
    const result = reorderCards(makeColumns(), 10, 10);
    expect(result).toBeNull();
  });
});
