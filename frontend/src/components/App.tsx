"use client";

import { useState } from "react";
import { LoginForm } from "@/components/LoginForm";
import { KanbanBoard } from "@/components/KanbanBoard";
import { login as apiLogin, setToken } from "@/lib/api";

export function App() {
  const [username, setUsername] = useState<string | null>(null);

  const handleLogin = async (user: string, password: string) => {
    const data = await apiLogin(user, password);
    setUsername(data.username);
  };

  const handleLogout = () => {
    setToken(null);
    setUsername(null);
  };

  if (!username) {
    return <LoginForm onLogin={handleLogin} />;
  }

  return <KanbanBoard username={username} onLogout={handleLogout} />;
}
