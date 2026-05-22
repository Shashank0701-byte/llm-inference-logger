import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "LLM Inference Logger",
  description:
    "Lightweight inference logging and ingestion system for LLM applications",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="app-layout">
          <aside className="sidebar">
            <div className="sidebar-header">
              <div className="sidebar-logo">⚡ LLM Logger</div>
            </div>
            <nav className="sidebar-nav">
              <Link href="/chat" className="nav-link" id="nav-chat">
                💬 Chat
              </Link>
              <Link
                href="/conversations"
                className="nav-link"
                id="nav-conversations"
              >
                📋 Conversations
              </Link>
              <Link href="/dashboard" className="nav-link" id="nav-dashboard">
                📊 Dashboard
              </Link>
            </nav>
          </aside>
          <main className="main-content">{children}</main>
        </div>
      </body>
    </html>
  );
}
