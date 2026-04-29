import { useState, useCallback } from 'react';
import { Bot, RefreshCw, Copy, Check } from 'lucide-react';

import { streamChat, submitFeedback } from './api/client';
import { ChatInput } from './components/ChatInput';
import { ChatWindow } from './components/ChatWindow';
import { FileUpload } from './components/FileUpload';
import { ToastContainer } from './components/Toast';
import type { ChatMessage, FeedbackState, Toast, TaskType } from './types';

function generateSessionId(): string {
  return `sess_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

function createMessage(role: 'user' | 'assistant', content: string): ChatMessage {
  return { id: crypto.randomUUID(), role, content, timestamp: Date.now() };
}

export default function App() {
  const [sessionId, setSessionId] = useState(generateSessionId);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [copied, setCopied] = useState(false);

  /** Add a toast notification */
  const addToast = useCallback((type: Toast['type'], message: string) => {
    const id = crypto.randomUUID();
    setToasts((prev) => [...prev, { id, type, message }]);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  /** Start a new session */
  const newSession = () => {
    setSessionId(generateSessionId());
    setMessages([]);
    addToast('info', 'New session started. Context has been reset.');
  };

  /** Copy session ID */
  const copySession = async () => {
    await navigator.clipboard.writeText(sessionId).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  /** Clear chat messages */
  const clearMessages = () => {
    setMessages([]);
  };

  /** Handle feedback from a message */
  const handleFeedback = useCallback(
    async (messageId: string, helpful: boolean) => {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === messageId
            ? { ...m, feedback: (helpful ? 'up' : 'down') as FeedbackState }
            : m,
        ),
      );
      try {
        await submitFeedback({ session_id: sessionId, helpful, rating: helpful ? 5 : 1 });
        addToast('success', helpful ? 'Thanks for the positive feedback!' : 'Got it — we\'ll use this to improve.');
      } catch {
        addToast('error', 'Failed to submit feedback. Please try again.');
        // Revert
        setMessages((prev) =>
          prev.map((m) => (m.id === messageId ? { ...m, feedback: 'none' as FeedbackState } : m)),
        );
      }
    },
    [sessionId, addToast],
  );

  /** Send a chat message and handle the SSE stream */
  const handleSubmit = useCallback(
    async (message: string, taskType: TaskType) => {
      setLoading(true);
      const assistantId = crypto.randomUUID();

      setMessages((prev) => [
        ...prev,
        createMessage('user', message),
        { id: assistantId, role: 'assistant', content: '', timestamp: Date.now() },
      ]);

      try {
        await streamChat(message, taskType, sessionId, {
          onChunk: (chunk) =>
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, content: m.content + chunk } : m,
              ),
            ),
          onSources: (sources) =>
            setMessages((prev) =>
              prev.map((m) => (m.id === assistantId ? { ...m, sources } : m)),
            ),
          onMeta: (meta) =>
            setMessages((prev) =>
              prev.map((m) => (m.id === assistantId ? { ...m, meta } : m)),
            ),
          onDone: () => setLoading(false),
        });
      } catch (error) {
        const errMsg = error instanceof Error ? error.message : 'An unexpected error occurred.';
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: `⚠️ ${errMsg}` } : m,
          ),
        );
        addToast('error', errMsg);
        setLoading(false);
      }
    },
    [sessionId, addToast],
  );

  return (
    <>
      <main className="app-shell">
        {/* ── Left Sidebar ── */}
        <aside className="sidebar">
          {/* Brand */}
          <div className="brand-card">
            <div className="brand-logo">
              <div className="brand-icon">
                <Bot size={22} />
              </div>
              <div>
                <div className="brand-title">Enterprise Copilot</div>
                <div className="brand-sub">AI-Powered Assistant</div>
              </div>
            </div>
            <p className="brand-description">
              Secure internal assistant powered by hybrid RAG, LangGraph agents, and Azure OpenAI.
              All responses are grounded, role-aware, and auditable.
            </p>
            <div className="brand-badges">
              <span className="badge">Hybrid RAG</span>
              <span className="badge">LangGraph</span>
              <span className="badge">Memory</span>
              <span className="badge">Azure OpenAI</span>
            </div>
          </div>

          {/* Session */}
          <div className="panel session-card">
            <div className="session-header">
              <span className="session-label">
                <span
                  style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent)', display: 'inline-block' }}
                />
                Active Session
              </span>
              <div style={{ display: 'flex', gap: 4 }}>
                <button className="btn-icon" onClick={copySession} title="Copy session ID">
                  {copied ? <Check size={14} color="var(--success)" /> : <Copy size={14} />}
                </button>
                <button className="btn-icon" onClick={newSession} title="New session">
                  <RefreshCw size={14} />
                </button>
              </div>
            </div>
            <div className="session-id">{sessionId}</div>
            <button className="btn-new-session" onClick={newSession}>
              <RefreshCw size={13} />
              Start New Session
            </button>
          </div>

          {/* File Upload */}
          <FileUpload
            onUploaded={(msg) => addToast('success', msg)}
          />
        </aside>

        {/* ── Workspace ── */}
        <section className="workspace">
          <ChatWindow
            messages={messages}
            loading={loading}
            onFeedback={handleFeedback}
            onClear={clearMessages}
          />
          <ChatInput onSubmit={handleSubmit} disabled={loading} />
        </section>
      </main>

      {/* Toast notifications */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </>
  );
}
