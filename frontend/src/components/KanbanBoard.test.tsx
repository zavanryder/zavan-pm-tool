import { render, screen, within, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { KanbanBoard } from "@/components/KanbanBoard";

const mockBoard = {
  id: 1,
  columns: [
    { id: 1, title: "Backlog", position: 0, cards: [
      { id: 1, title: "Card One", details: "Details one" },
      { id: 2, title: "Card Two", details: "Details two" },
    ]},
    { id: 2, title: "Discovery", position: 1, cards: [] },
    { id: 3, title: "In Progress", position: 2, cards: [] },
    { id: 4, title: "Review", position: 3, cards: [] },
    { id: 5, title: "Done", position: 4, cards: [] },
  ],
};

vi.mock("@/lib/api", () => ({
  fetchBoard: vi.fn(() => Promise.resolve(mockBoard)),
  renameColumn: vi.fn(() => Promise.resolve({ ok: true })),
  createCard: vi.fn(() => Promise.resolve({ id: 99, title: "New", details: "" })),
  deleteCard: vi.fn(() => Promise.resolve({ ok: true })),
  moveCard: vi.fn(() => Promise.resolve({ ok: true })),
  setToken: vi.fn(),
  getToken: vi.fn(),
}));

const getFirstColumn = () => screen.getAllByTestId(/column-/i)[0];

describe("KanbanBoard", () => {
  it("renders five columns after loading", async () => {
    render(<KanbanBoard username="user" onLogout={() => {}} />);
    await waitFor(() => {
      expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
    });
  });

  it("renames a column", async () => {
    render(<KanbanBoard username="user" onLogout={() => {}} />);
    await waitFor(() => screen.getAllByTestId(/column-/i));
    const column = getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    expect(input).toHaveValue("New Name");
  });

  it("adds a card", async () => {
    const { fetchBoard } = await import("@/lib/api");
    let callCount = 0;
    (fetchBoard as ReturnType<typeof vi.fn>).mockImplementation(() => {
      callCount++;
      if (callCount > 1) {
        return Promise.resolve({
          ...mockBoard,
          columns: mockBoard.columns.map((c) =>
            c.id === 1 ? { ...c, cards: [...c.cards, { id: 99, title: "New card", details: "Notes" }] } : c
          ),
        });
      }
      return Promise.resolve(mockBoard);
    });

    render(<KanbanBoard username="user" onLogout={() => {}} />);
    await waitFor(() => screen.getAllByTestId(/column-/i));
    const column = getFirstColumn();
    await userEvent.click(within(column).getByRole("button", { name: /add a card/i }));
    await userEvent.type(within(column).getByPlaceholderText(/card title/i), "New card");
    await userEvent.type(within(column).getByPlaceholderText(/details/i), "Notes");
    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    await waitFor(() => {
      expect(within(column).getByText("New card")).toBeInTheDocument();
    });
  });
});
