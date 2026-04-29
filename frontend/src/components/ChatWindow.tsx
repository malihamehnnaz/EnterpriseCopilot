import { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, Bot, Zap, Brain, Trash2 } from 'lucide-react';
import type { ChatMessage, FeedbackState } from '../types';
import { SourceList } from './SourceList';
import { FeedbackButtons } from './FeedbackButtons';
import { ThinkingIndicator } from './ThinkingIndicator';

type Props = {
  messages: ChatMessage[];
  loading: boolean;
  onFeedback: (messageId: string, helpful: boolean) => void;
  onClear: () => void;
};

function formatTime(ts?: number): string {
  if (!ts) return '';
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export function ChatWindow({ messages, loading, onFeedback, onClear }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const hasMessages = messages.length > 0;

  return (
    <div className="panel chat-panel">
      {/* Header */}
      <div className="chat-panel-header">
        <div className="chat-panel-title">
          <span className="status-dot" />
          <div>
            <h2>Enterprise Copilot</h2>
            <p className="chat-panel-meta">Grounded answers · Role-aware retrieval · Auditable</p>
          </div>
        </div>
        <div className="chat-panel-actions">
          {hasMessages && (
            <button className="btn-icon" onClick={onClear} title="Clear conversation">
              <Trash2 size={15} />
            </button>
          )}
        </div>
      </div>

      {/* Message list */}
      <div className="message-list">
        {!hasMessages && (
          <div className="welcome-state">
            <div className="welcome-icon">
              <Bot size={28} />
            </div>
            <p className="welcome-title">Ready to assist</p>
            <p className="welcome-body">
              Upload a document using the sidebar, then ask questions, request summaries,
              draft emails, or generate reports — all grounded in your enterprise knowledge base.
            </p>
            <div className="suggestion-chips">
              <span className="suggestion-chip">Summarize the document</span>
              <span className="suggestion-chip">What are the key risks?</span>
              <span className="suggestion-chip">Draft an executive summary</span>
              <span className="suggestion-chip">List action items</span>
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.role}`}>
            {/* Avatar */}
            <div className={`avatar ${msg.role === 'user' ? 'user-avatar' : 'assistant-avatar'}`}>
              {msg.role === 'user' ? <User size={16} color="white" /> : <Bot size={16} color="var(--accent)" />}
            </div>

            {/* Body */}
            <div className="message-body">
              <div className="message-header">
                <span className="message-role">{msg.role === 'user' ? 'You' : 'Copilot'}</span>
                {msg.timestamp && <span className="message-time">{formatTime(msg.timestamp)}</span>}
              </div>

              {/* Bubble */}
              <div className="bubble">
                {msg.role === 'assistant' ? (
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                ) : (
                  <p>{msg.content}</p>
                )}
                {msg.sources?.length ? <SourceList sources={msg.sources} /> : null}
              </div>

              {/* Meta chips (assistant only) */}
              {msg.role === 'assistant' && (msg.meta?.model || msg.meta?.cached || msg.meta?.memory_used) && (
                <div className="message-meta">
                  {msg.meta?.model && (
                    <span className="meta-chip">
                      <Zap size={10} />
                      {msg.meta.model}
                    </span>
                  )}
                  {msg.meta?.cached && (
                    <span className="meta-chip cached">Cached</span>
                  )}
                  {msg.meta?.memory_used && (
                    <span className="meta-chip memory">
                      <Brain size={10} />
                      Memory
                    </span>
                  )}
                </div>
              )}

              {/* Feedback (assistant only, non-empty) */}
              {msg.role === 'assistant' && msg.content && (
                <FeedbackButtons
                  state={(msg.feedback ?? 'none') as FeedbackState}
                  onFeedback={(helpful) => onFeedback(msg.id, helpful)}
                />
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message assistant">
            <div className="avatar assistant-avatar">
              <Bot size={16} color="var(--accent)" />
            </div>
            <div className="message-body">
              <div className="message-header">
                <span className="message-role">Copilot</span>
              </div>
              <ThinkingIndicator />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
