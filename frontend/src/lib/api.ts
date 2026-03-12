const API_BASE = "/api";

let token: string | null = null;

function loadStoredToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem("auth_token");
  }
  return null;
}

export function setToken(t: string | null) {
  token = t;
  if (typeof window !== "undefined") {
    if (t) localStorage.setItem("auth_token", t);
    else localStorage.removeItem("auth_token");
  }
}

export function getToken(): string | null {
  if (!token) token = loadStoredToken();
  return token;
}

let onAuthError: (() => void) | null = null;

export function setAuthErrorHandler(handler: () => void) {
  onAuthError = handler;
}

export async function apiFetch(path: string, options: RequestInit = {}) {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (options.body) {
    headers["Content-Type"] = "application/json";
  }
  const currentToken = getToken();
  if (currentToken) {
    headers["Authorization"] = `Bearer ${currentToken}`;
  }
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401) {
    setToken(null);
    onAuthError?.();
    throw new Error("Session expired");
  }
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `API error: ${res.status}`);
  }
  return res.json();
}

export async function login(username: string, password: string) {
  const data = await apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  setToken(data.token);
  return data;
}

export async function register(username: string, password: string, displayName: string = "") {
  const data = await apiFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, password, display_name: displayName }),
  });
  setToken(data.token);
  return data;
}

// Board CRUD
export async function listBoards() {
  return apiFetch("/boards");
}

export async function createBoard(name: string) {
  return apiFetch("/boards", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export async function fetchBoard(boardId?: number) {
  if (boardId !== undefined) {
    return apiFetch(`/boards/${boardId}`);
  }
  return apiFetch("/board");
}

export async function renameBoard(boardId: number, name: string) {
  return apiFetch(`/boards/${boardId}`, {
    method: "PUT",
    body: JSON.stringify({ name }),
  });
}

export async function deleteBoard(boardId: number) {
  return apiFetch(`/boards/${boardId}`, { method: "DELETE" });
}

// Column management
export async function renameColumn(columnId: number, title: string) {
  return apiFetch(`/columns/${columnId}`, {
    method: "PUT",
    body: JSON.stringify({ title }),
  });
}

export async function addColumn(boardId: number, title: string) {
  return apiFetch("/columns", {
    method: "POST",
    body: JSON.stringify({ board_id: boardId, title }),
  });
}

export async function deleteColumn(columnId: number) {
  return apiFetch(`/columns/${columnId}`, { method: "DELETE" });
}

// Card CRUD
export async function createCard(
  columnId: number,
  title: string,
  details: string,
  label: string = "",
  dueDate: string | null = null,
) {
  return apiFetch("/cards", {
    method: "POST",
    body: JSON.stringify({ column_id: columnId, title, details, label, due_date: dueDate }),
  });
}

export async function updateCard(
  cardId: number,
  updates: { title?: string; details?: string; label?: string; due_date?: string | null },
) {
  return apiFetch(`/cards/${cardId}`, {
    method: "PUT",
    body: JSON.stringify(updates),
  });
}

export async function deleteCard(cardId: number) {
  return apiFetch(`/cards/${cardId}`, { method: "DELETE" });
}

export async function moveCard(cardId: number, targetColumnId: number, position: number) {
  return apiFetch(`/cards/${cardId}/move`, {
    method: "PUT",
    body: JSON.stringify({ target_column_id: targetColumnId, position }),
  });
}

// Search
export async function searchCards(query: string, boardId?: number) {
  return apiFetch("/search", {
    method: "POST",
    body: JSON.stringify({ query, board_id: boardId }),
  });
}

// AI Chat
export async function aiChat(
  message: string,
  conversationHistory: { role: string; content: string }[],
  boardId?: number,
) {
  return apiFetch("/ai/chat", {
    method: "POST",
    body: JSON.stringify({ message, conversation_history: conversationHistory, board_id: boardId }),
  });
}

// Profile
export async function updateProfile(displayName: string) {
  return apiFetch("/profile", {
    method: "PUT",
    body: JSON.stringify({ display_name: displayName }),
  });
}

export async function changePassword(oldPassword: string, newPassword: string) {
  return apiFetch("/profile/password", {
    method: "PUT",
    body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
  });
}
