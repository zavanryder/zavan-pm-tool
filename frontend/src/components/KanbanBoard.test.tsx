import { render, screen, within, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { KanbanBoard } from "@/components/KanbanBoard";

const mockBoard = {
  id: 1,
  name: "My Board",
  columns: [
    { id: 1, title: "Backlog", position: 0, cards: [
      { id: 1, title: "Card One", details: "Details one", label: "", due_date: null },
      { id: 2, title: "Card Two", details: "Details two", label: "bug", due_date: "2026-04-01" },
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
  createCard: vi.fn(() => Promise.resolve({ id: 99, title: "New", details: "", label: "", due_date: null })),
  deleteCard: vi.fn(() => Promise.resolve({ ok: true })),
  deleteColumn: vi.fn(() => Promise.resolve({ ok: true })),
  addColumn: vi.fn(() => Promise.resolve({ id: 6, title: "Extra", position: 5, cards: [] })),
  moveCard: vi.fn(() => Promise.resolve({ ok: true })),
  updateCard: vi.fn(() => Promise.resolve({ ok: true })),
  renameBoard: vi.fn(() => Promise.resolve({ ok: true })),
  setToken: vi.fn(),
  getToken: vi.fn(),
  setAuthErrorHandler: vi.fn(),
  aiChat: vi.fn(() => Promise.resolve({ message: "Done", board_updates: [] })),
}));

const getFirstColumn = () => screen.getAllByTestId(/^column-\d+$/)[0];

describe("KanbanBoard", () => {
  it("renders five columns after loading", async () => {
    render(<KanbanBoard username="user" boardId={1} onLogout={() => {}} onBack={() => {}} />);
    await waitFor(() => {
      expect(screen.getAllByTestId(/^column-\d+$/)).toHaveLength(5);
    });
  });

  it("shows board name", async () => {
    render(<KanbanBoard username="user" boardId={1} onLogout={() => {}} onBack={() => {}} />);
    await waitFor(() => {
      expect(screen.getByTestId("board-name")).toHaveTextContent("My Board");
    });
  });

  it("renders card labels", async () => {
    render(<KanbanBoard username="user" boardId={1} onLogout={() => {}} onBack={() => {}} />);
    await waitFor(() => {
      expect(screen.getByTestId("card-label-2")).toHaveTextContent("bug");
    });
  });

  it("renders card due dates", async () => {
    render(<KanbanBoard username="user" boardId={1} onLogout={() => {}} onBack={() => {}} />);
    await waitFor(() => {
      expect(screen.getByTestId("card-due-2")).toHaveTextContent("2026-04-01");
    });
  });

  it("has back button", async () => {
    render(<KanbanBoard username="user" boardId={1} onLogout={() => {}} onBack={() => {}} />);
    await waitFor(() => {
      expect(screen.getByTestId("back-button")).toBeInTheDocument();
    });
  });

  it("renames a column on blur", async () => {
    render(<KanbanBoard username="user" boardId={1} onLogout={() => {}} onBack={() => {}} />);
    await waitFor(() => screen.getAllByTestId(/^column-\d+$/));
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
            c.id === 1 ? { ...c, cards: [...c.cards, { id: 99, title: "New card", details: "Notes", label: "", due_date: null }] } : c
          ),
        });
      }
      return Promise.resolve(mockBoard);
    });

    render(<KanbanBoard username="user" boardId={1} onLogout={() => {}} onBack={() => {}} />);
    await waitFor(() => screen.getAllByTestId(/^column-\d+$/));
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
