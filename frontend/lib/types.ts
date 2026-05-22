export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  token_count: number;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  status: "active" | "cancelled" | "completed";
  provider: string;
  model: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
  messages?: Message[];
}

export interface ChatResponse {
  content: string;
  conversation_id: string;
  model: string;
  provider: string;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
}

export interface InferenceLog {
  id: string;
  conversation_id: string | null;
  session_id: string;
  model: string;
  provider: string;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  status: string;
  error_message: string | null;
  input_preview: string;
  output_preview: string;
  created_at: string;
}

export interface Metrics {
  total_requests: number;
  success_count: number;
  error_count: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  total_tokens: number;
  requests_by_provider: Record<string, number>;
  requests_by_model: Record<string, number>;
}

export interface TimeseriesPoint {
  timestamp: string;
  value: number;
}

export interface ProviderBreakdown {
  provider: string;
  count: number;
  avg_latency_ms: number;
  total_tokens: number;
}
