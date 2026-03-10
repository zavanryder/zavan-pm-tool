"use client";

import { useCallback, useEffect, useState } from "react";
import { LoginForm } from "@/components/LoginForm";
import { KanbanBoard } from "@/components/KanbanBoard";
import { login as apiLogin, setToken, setAuthErrorHandler } from "@/lib/api";

export function App() {
  const [username, setUsername] = useState<string | null>(null);

  const handleLogout = useCallback(() => {
    setToken(null);
    setUsername(null);
  }, []);

  useEffect(() => {
    setAuthErrorHandler(handleLogout);
  }, [handleLogout]);

  const handleLogin = async (user: string, password: string) => {
    const data = await apiLogin(user, password);
    setUsername(data.username);
  };

  if (!username) {
    return <LoginForm onLogin={handleLogin} />;
  }

  return <KanbanBoard username={username} onLogout={handleLogout} />;
}
