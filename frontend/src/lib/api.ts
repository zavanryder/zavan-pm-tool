const API_BASE = "/api";

let token: string | null = null;

export function setToken(t: string | null) {
  token = t;
}

export function getToken(): string | null {
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
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401) {
    token = null;
    onAuthError?.();
    throw new Error("Session expired");
  }
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  return res.json();
}

export async function login(username: string, password: string) {
  const data = await apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  token = data.token;
  return data;
}

export async function fetchBoard() {
  return apiFetch("/board");
}

export async function renameColumn(columnId: number, title: string) {
  return apiFetch(`/columns/${columnId}`, {
    method: "PUT",
    body: JSON.stringify({ title }),
  });
}

export async function createCard(columnId: number, title: string, details: string) {
  return apiFetch("/cards", {
    method: "POST",
    body: JSON.stringify({ column_id: columnId, title, details }),
  });
}

export async function updateCard(cardId: number, updates: { title?: string; details?: string }) {
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

export async function aiChat(message: string, conversationHistory: { role: string; content: string }[]) {
  return apiFetch("/ai/chat", {
    method: "POST",
    body: JSON.stringify({ message, conversation_history: conversationHistory }),
  });
}
