"use client";

import { useState, useRef, useEffect } from "react";
import { sendMessage, fetchStreamResponse, getModels } from "@/lib/api";
import type { Message } from "@/lib/types";

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [model, setModel] = useState("gpt-4.1");
  const [providers, setProviders] = useState<Record<string, string[]>>({});
  const [streaming, setStreaming] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getModels()
      .then((data) => {
        setProviders(data.providers);
        const all = Object.values(data.providers).flat();
        if (all.length > 0 && !all.includes("gpt-4.1")) {
          setModel(all[0] as string);
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const allModels = Object.entries(providers).flatMap(([, models]) => models);

  const addMessage = (role: "user" | "assistant", content: string) => {
    const msg: Message = {
      id: crypto.randomUUID(),
      conversation_id: conversationId || "",
      role,
      content,
      token_count: 0,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, msg]);
    return msg;
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    addMessage("user", text);
    setLoading(true);

    try {
      if (streaming) {
        // SSE streaming
        const res = await fetchStreamResponse(text, conversationId || undefined, model);
        if (!res.body) throw new Error("No response body");

        const assistantId = crypto.randomUUID();
        setMessages((prev) => [
          ...prev,
          {
            id: assistantId,
            conversation_id: conversationId || "",
            role: "assistant",
            content: "",
            token_count: 0,
            created_at: new Date().toISOString(),
          },
        ]);

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6);
              if (data === "[DONE]") {
                // Extract conversation_id from first response if needed
                continue;
              }
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? { ...m, content: m.content + data }
                    : m
                )
              );
            }
          }
        }
      } else {
        // Regular request
        const res = await sendMessage(text, conversationId || undefined, model);
        if (!conversationId) setConversationId(res.conversation_id);
        addMessage("assistant", res.content);
      }
    } catch (err: any) {
      addMessage("assistant", `⚠️ Error: ${err.message}`);
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

  const handleNewChat = () => {
    setMessages([]);
    setConversationId(null);
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>💬 Chat</h1>
        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <select
            className="model-select"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            id="model-selector"
          >
            {allModels.length > 0 ? (
              allModels.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))
            ) : (
              <option value="gpt-4.1">gpt-4.1</option>
            )}
          </select>
          <label
            style={{ fontSize: "12px", color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: "4px" }}
          >
            <input
              type="checkbox"
              checked={streaming}
              onChange={(e) => setStreaming(e.target.checked)}
            />
            Stream
          </label>
          <button className="btn btn-outline btn-sm" onClick={handleNewChat} id="new-chat-btn">
            + New
          </button>
        </div>
      </div>

      <div className="messages-area" id="messages-area">
        {messages.length === 0 && (
          <div className="empty-state">
            <div className="empty-state-icon">💬</div>
            <h3>Start a Conversation</h3>
            <p>Send a message to begin chatting with the AI. Your conversations and inference logs are automatically captured.</p>
          </div>
        )}
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.role}`}>
            <div className="message-avatar">
              {msg.role === "user" ? "U" : "AI"}
            </div>
            <div>
              <div className="message-bubble">{msg.content}</div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <div className="message-avatar">AI</div>
            <div className="message-bubble">
              <div className="loading-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <div className="chat-input-wrapper">
          <textarea
            className="chat-input"
            placeholder="Type a message..."
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
            id="chat-input"
          />
          <button
            className="send-btn"
            onClick={handleSend}
            disabled={loading || !input.trim()}
            id="send-btn"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
