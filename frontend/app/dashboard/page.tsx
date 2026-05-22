"use client";

import { useState, useEffect } from "react";
import {
  getMetrics,
  getTimeseries,
  getRecentLogs,
  getProviderBreakdown,
} from "@/lib/api";
import type {
  Metrics,
  TimeseriesPoint,
  InferenceLog,
  ProviderBreakdown,
} from "@/lib/types";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

const COLORS = ["#6c63ff", "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];

const tooltipStyle = {
  backgroundColor: "#1a1a2e",
  border: "1px solid #2a2a4a",
  borderRadius: "8px",
  fontSize: "12px",
};

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [latency, setLatency] = useState<TimeseriesPoint[]>([]);
  const [throughput, setThroughput] = useState<TimeseriesPoint[]>([]);
  const [errors, setErrors] = useState<TimeseriesPoint[]>([]);
  const [logs, setLogs] = useState<InferenceLog[]>([]);
  const [providers, setProviders] = useState<ProviderBreakdown[]>([]);
  const [hours, setHours] = useState(24);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [m, ts, l, p] = await Promise.all([
        getMetrics(hours),
        getTimeseries(hours, 15),
        getRecentLogs(0, 50),
        getProviderBreakdown(hours),
      ]);
      setMetrics(m);
      setLatency(ts.latency_series);
      setThroughput(ts.throughput_series);
      setErrors(ts.error_series);
      setLogs(l);
      setProviders(p);
    } catch {
      /* empty */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, [hours]);

  const errorRate =
    metrics && metrics.total_requests > 0
      ? ((metrics.error_count / metrics.total_requests) * 100).toFixed(1)
      : "0.0";

  const formatDate = (d: string) =>
    new Date(d).toLocaleString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });

  const pieData = providers.map((p) => ({ name: p.provider, value: p.count }));

  if (loading && !metrics) {
    return (
      <div className="page-container">
        <div className="empty-state">
          <div className="loading-dots"><span></span><span></span><span></span></div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>📊 Dashboard</h1>
        <select
          className="model-select"
          value={hours}
          onChange={(e) => setHours(Number(e.target.value))}
          id="time-range-select"
        >
          <option value={1}>Last 1 hour</option>
          <option value={6}>Last 6 hours</option>
          <option value={24}>Last 24 hours</option>
          <option value={168}>Last 7 days</option>
        </select>
      </div>

      {/* Stat Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Requests</div>
          <div className="stat-value">{metrics?.total_requests ?? 0}</div>
          <div className="stat-sub">
            {metrics?.success_count ?? 0} successful
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Avg Latency</div>
          <div className="stat-value">{metrics?.avg_latency_ms?.toFixed(0) ?? 0}ms</div>
          <div className="stat-sub">across all providers</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Error Rate</div>
          <div className="stat-value">{errorRate}%</div>
          <div className="stat-sub">{metrics?.error_count ?? 0} errors</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Tokens</div>
          <div className="stat-value">
            {((metrics?.total_tokens ?? 0) / 1000).toFixed(1)}k
          </div>
          <div className="stat-sub">input + output</div>
        </div>
      </div>

      {/* Charts */}
      <div className="charts-grid">
        <div className="chart-card">
          <h3>Latency (ms)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={latency}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a4a" />
              <XAxis dataKey="timestamp" tick={{ fill: "#555577", fontSize: 10 }} />
              <YAxis tick={{ fill: "#555577", fontSize: 10 }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#6c63ff"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: "#6c63ff" }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Throughput (requests)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={throughput}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a4a" />
              <XAxis dataKey="timestamp" tick={{ fill: "#555577", fontSize: 10 }} />
              <YAxis tick={{ fill: "#555577", fontSize: 10 }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Errors</h3>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={errors}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a4a" />
              <XAxis dataKey="timestamp" tick={{ fill: "#555577", fontSize: 10 }} />
              <YAxis tick={{ fill: "#555577", fontSize: 10 }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#ef4444"
                fill="#ef444422"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Requests by Provider</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                dataKey="value"
                label={({ name, percent }) =>
                  `${name} ${(percent * 100).toFixed(0)}%`
                }
                labelLine={false}
              >
                {pieData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Logs Table */}
      <h2 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "16px" }}>
        Recent Inference Logs
      </h2>
      <div className="table-card">
        <table className="table" id="logs-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Model</th>
              <th>Provider</th>
              <th>Status</th>
              <th>Latency</th>
              <th>Tokens</th>
              <th>Preview</th>
            </tr>
          </thead>
          <tbody>
            {logs.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: "center", color: "var(--text-muted)", padding: "32px" }}>
                  No inference logs yet. Start chatting to generate data.
                </td>
              </tr>
            ) : (
              logs.map((log) => (
                <tr key={log.id}>
                  <td style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
                    {formatDate(log.created_at)}
                  </td>
                  <td style={{ fontSize: "13px" }}>{log.model}</td>
                  <td style={{ fontSize: "13px" }}>{log.provider}</td>
                  <td>
                    <span className={`badge badge-${log.status}`}>
                      {log.status === "success" ? "✓" : "✕"} {log.status}
                    </span>
                  </td>
                  <td style={{ fontSize: "13px" }}>{log.latency_ms.toFixed(0)}ms</td>
                  <td style={{ fontSize: "13px" }}>
                    {log.input_tokens + log.output_tokens}
                  </td>
                  <td
                    style={{
                      fontSize: "12px",
                      color: "var(--text-secondary)",
                      maxWidth: "200px",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                    title={log.output_preview}
                  >
                    {log.output_preview || "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
