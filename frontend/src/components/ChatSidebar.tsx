"use client";

import { useEffect, useRef, useState } from "react";
import * as api from "@/lib/api";

type Message = {
  role: "user" | "assistant";
  content: string;
};

interface ChatSidebarProps {
  open: boolean;
  onClose: () => void;
  onBoardUpdated: () => void;
  boardId?: number;
}

export function ChatSidebar({ open, onClose, onBoardUpdated, boardId }: ChatSidebarProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = { role: "user", content: text };
    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const data = await api.aiChat(text, history, boardId);
      const assistantMsg: Message = { role: "assistant", content: data.message };
      setMessages((prev) => [...prev, assistantMsg]);
      if (data.board_updates && data.board_updates.length > 0) {
        onBoardUpdated();
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Something went wrong. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!open) return null;

  return (
    <div className="fixed right-0 top-0 z-50 flex h-full w-[400px] flex-col border-l border-[var(--stroke)] bg-white shadow-[-8px_0_32px_rgba(3,33,71,0.08)]" data-testid="chat-sidebar">
      <div className="flex items-center justify-between border-b border-[var(--stroke)] px-6 py-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
            AI Assistant
          </p>
          <p className="mt-1 font-display text-lg font-semibold text-[var(--navy-dark)]">
            Chat
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-full border border-[var(--stroke)] px-3 py-1 text-xs font-semibold text-[var(--gray-text)] transition hover:text-[var(--navy-dark)]"
          data-testid="chat-close"
        >
          Close
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 && (
          <p className="text-center text-sm text-[var(--gray-text)]">
            Ask me to create, move, or update cards on your board.
          </p>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`mb-4 ${msg.role === "user" ? "text-right" : "text-left"}`}
          >
            <div
              className={`inline-block max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-6 ${
                msg.role === "user"
                  ? "bg-[var(--secondary-purple)] text-white"
                  : "bg-[var(--surface)] text-[var(--navy-dark)]"
              }`}
              data-testid={`chat-message-${msg.role}`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="mb-4 text-left">
            <div className="inline-block rounded-2xl bg-[var(--surface)] px-4 py-3 text-sm text-[var(--gray-text)]">
              Thinking...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-[var(--stroke)] px-6 py-4">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask the AI..."
            rows={2}
            className="flex-1 resize-none rounded-xl border border-[var(--stroke)] px-3 py-2 text-sm outline-none transition focus:border-[var(--primary-blue)]"
            data-testid="chat-input"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="self-end rounded-xl bg-[var(--secondary-purple)] px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
            data-testid="chat-send"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
