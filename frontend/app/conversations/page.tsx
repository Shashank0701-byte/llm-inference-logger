"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  listConversations,
  updateConversation,
  createConversation,
} from "@/lib/api";
import type { Conversation } from "@/lib/types";

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const load = async () => {
    setLoading(true);
    try {
      const data = await listConversations();
      setConversations(data);
    } catch {
      /* empty */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleCancel = async (id: string) => {
    await updateConversation(id, "cancelled");
    load();
  };

  const handleResume = async (id: string) => {
    await updateConversation(id, "active");
    router.push(`/chat?conversation=${id}`);
  };

  const handleNew = async () => {
    await createConversation();
    load();
  };

  const statusBadge = (status: string) => {
    const map: Record<string, { cls: string; icon: string }> = {
      active: { cls: "badge-active", icon: "●" },
      cancelled: { cls: "badge-cancelled", icon: "✕" },
      completed: { cls: "badge-completed", icon: "✓" },
    };
    const s = map[status] || map.active;
    return (
      <span className={`badge ${s.cls}`}>
        {s.icon} {status}
      </span>
    );
  };

  const formatDate = (d: string) =>
    new Date(d).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>📋 Conversations</h1>
        <button className="btn btn-primary" onClick={handleNew} id="new-conversation-btn">
          + New Conversation
        </button>
      </div>

      {loading ? (
        <div className="empty-state">
          <div className="loading-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      ) : conversations.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📋</div>
          <h3>No Conversations Yet</h3>
          <p>Start chatting to create your first conversation. All messages and inference logs are captured automatically.</p>
        </div>
      ) : (
        <div className="table-card">
          <table className="table" id="conversations-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Status</th>
                <th>Model</th>
                <th>Messages</th>
                <th>Created</th>
                <th>Updated</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {conversations.map((c) => (
                <tr key={c.id}>
                  <td style={{ fontWeight: 500 }}>{c.title}</td>
                  <td>{statusBadge(c.status)}</td>
                  <td>
                    <span style={{ color: "var(--text-secondary)", fontSize: "13px" }}>
                      {c.model || "—"}
                    </span>
                  </td>
                  <td>{c.message_count ?? 0}</td>
                  <td style={{ color: "var(--text-secondary)", fontSize: "13px" }}>
                    {formatDate(c.created_at)}
                  </td>
                  <td style={{ color: "var(--text-secondary)", fontSize: "13px" }}>
                    {formatDate(c.updated_at)}
                  </td>
                  <td>
                    <div style={{ display: "flex", gap: "6px" }}>
                      {c.status === "active" && (
                        <button
                          className="btn btn-outline btn-sm"
                          onClick={() => handleCancel(c.id)}
                        >
                          Cancel
                        </button>
                      )}
                      {c.status === "cancelled" && (
                        <button
                          className="btn btn-outline btn-sm"
                          onClick={() => handleResume(c.id)}
                        >
                          Resume
                        </button>
                      )}
                      {c.status !== "cancelled" && (
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => router.push(`/chat?conversation=${c.id}`)}
                        >
                          Open
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
