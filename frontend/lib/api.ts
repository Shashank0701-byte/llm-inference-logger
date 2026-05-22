const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

// ── Chat ──────────────────────────────────────────────────

export async function sendMessage(
  message: string,
  conversationId?: string,
  model?: string
) {
  return request<import("./types").ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
      model: model || "",
    }),
  });
}

export function streamMessage(
  message: string,
  conversationId?: string,
  model?: string
): EventSource | { getReader: () => ReadableStreamDefaultReader } {
  // We use fetch for SSE since EventSource doesn't support POST
  const controller = new AbortController();
  const response = fetch(`${API_BASE}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
      model: model || "",
    }),
    signal: controller.signal,
  });
  return { response, controller } as any;
}

export async function fetchStreamResponse(
  message: string,
  conversationId?: string,
  model?: string
): Promise<Response> {
  return fetch(`${API_BASE}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
      model: model || "",
    }),
  });
}

export async function getModels() {
  return request<{ providers: Record<string, string[]> }>("/api/models");
}

// ── Conversations ─────────────────────────────────────────

export async function listConversations(skip = 0, limit = 50) {
  return request<import("./types").Conversation[]>(
    `/api/conversations?skip=${skip}&limit=${limit}`
  );
}

export async function getConversation(id: string) {
  return request<import("./types").Conversation>(`/api/conversations/${id}`);
}

export async function createConversation(title?: string, model?: string) {
  return request<import("./types").Conversation>("/api/conversations", {
    method: "POST",
    body: JSON.stringify({ title: title || "New Conversation", model: model || "" }),
  });
}

export async function updateConversation(id: string, status: string) {
  return request<import("./types").Conversation>(`/api/conversations/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

// ── Dashboard ─────────────────────────────────────────────

export async function getMetrics(hours = 24) {
  return request<import("./types").Metrics>(
    `/api/dashboard/metrics?hours=${hours}`
  );
}

export async function getTimeseries(hours = 24, bucketMinutes = 15) {
  return request<{
    latency_series: import("./types").TimeseriesPoint[];
    throughput_series: import("./types").TimeseriesPoint[];
    error_series: import("./types").TimeseriesPoint[];
  }>(`/api/dashboard/timeseries?hours=${hours}&bucket_minutes=${bucketMinutes}`);
}

export async function getRecentLogs(skip = 0, limit = 50) {
  return request<import("./types").InferenceLog[]>(
    `/api/dashboard/logs?skip=${skip}&limit=${limit}`
  );
}

export async function getProviderBreakdown(hours = 24) {
  return request<import("./types").ProviderBreakdown[]>(
    `/api/dashboard/providers?hours=${hours}`
  );
}
