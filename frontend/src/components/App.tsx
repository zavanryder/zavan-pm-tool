"use client";

import { useCallback, useEffect, useState } from "react";
import { LoginForm } from "@/components/LoginForm";
import { BoardSelector } from "@/components/BoardSelector";
import { KanbanBoard } from "@/components/KanbanBoard";
import { apiFetch, login as apiLogin, register as apiRegister, getToken, setToken, setAuthErrorHandler } from "@/lib/api";

export function App() {
  const [user, setUser] = useState<{ username: string; userId: number } | null>(null);
  const [selectedBoardId, setSelectedBoardId] = useState<number | null>(null);
  const [restoring, setRestoring] = useState(true);

  const handleLogout = useCallback(() => {
    setToken(null);
    setUser(null);
    setSelectedBoardId(null);
  }, []);

  useEffect(() => {
    setAuthErrorHandler(handleLogout);
  }, [handleLogout]);

  useEffect(() => {
    const saved = getToken();
    if (saved) {
      apiFetch("/auth/me")
        .then((data) => setUser({ username: data.username, userId: data.user_id }))
        .catch(() => setToken(null))
        .finally(() => setRestoring(false));
    } else {
      setRestoring(false);
    }
  }, []);

  const handleLogin = async (username: string, password: string) => {
    const data = await apiLogin(username, password);
    setUser({ username: data.username, userId: data.user_id });
  };

  const handleRegister = async (username: string, password: string, displayName: string) => {
    const data = await apiRegister(username, password, displayName);
    setUser({ username: data.username, userId: data.user_id });
  };

  if (restoring) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-[var(--gray-text)]">Loading...</p>
      </div>
    );
  }

  if (!user) {
    return <LoginForm onLogin={handleLogin} onRegister={handleRegister} />;
  }

  if (!selectedBoardId) {
    return (
      <BoardSelector
        username={user.username}
        onSelect={setSelectedBoardId}
        onLogout={handleLogout}
      />
    );
  }

  return (
    <KanbanBoard
      username={user.username}
      boardId={selectedBoardId}
      onLogout={handleLogout}
      onBack={() => setSelectedBoardId(null)}
    />
  );
}
