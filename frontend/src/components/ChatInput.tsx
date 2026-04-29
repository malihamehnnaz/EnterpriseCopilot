import { useState, useRef, type FormEvent, type KeyboardEvent } from 'react';
import { Send, HelpCircle, AlignLeft, Mail, BarChart2 } from 'lucide-react';
import type { TaskType } from '../types';

type Props = {
  onSubmit: (message: string, taskType: TaskType) => Promise<void>;
  disabled: boolean;
};

const TASKS: { type: TaskType; label: string; icon: React.ReactNode; placeholder: string }[] = [
  {
    type: 'qa',
    label: 'Q&A',
    icon: <HelpCircle size={13} />,
    placeholder: 'Ask a grounded question about your uploaded documents…',
  },
  {
    type: 'summarize',
    label: 'Summarize',
    icon: <AlignLeft size={13} />,
    placeholder: 'Summarize the uploaded document and highlight key points…',
  },
  {
    type: 'email',
    label: 'Draft Email',
    icon: <Mail size={13} />,
    placeholder: 'Draft a professional internal email based on the document…',
  },
  {
    type: 'report',
    label: 'Report',
    icon: <BarChart2 size={13} />,
    placeholder: 'Generate an executive summary or structured report…',
  },
];

const MAX_CHARS = 2000;

export function ChatInput({ onSubmit, disabled }: Props) {
  const [message, setMessage] = useState('');
  const [taskType, setTaskType] = useState<TaskType>('qa');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const currentTask = TASKS.find((t) => t.type === taskType)!;

  const handleSubmit = async (e?: FormEvent) => {
    e?.preventDefault();
    const trimmed = message.trim();
    if (!trimmed || disabled) return;
    setMessage('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    await onSubmit(trimmed, taskType);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = 'auto';
      el.style.height = Math.min(el.scrollHeight, 200) + 'px';
    }
  };

  const remaining = MAX_CHARS - message.length;

  return (
    <div className="chat-input-panel">
      {/* Task selector */}
      <div className="task-selector">
        {TASKS.map((t) => (
          <button
            key={t.type}
            type="button"
            className={`task-btn${taskType === t.type ? ' active' : ''}`}
            onClick={() => setTaskType(t.type)}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>

      {/* Textarea */}
      <div className="chat-textarea-wrapper">
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          value={message}
          onChange={(e) => setMessage(e.target.value.slice(0, MAX_CHARS))}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder={currentTask.placeholder}
          rows={3}
          disabled={disabled}
        />
        {message.length > MAX_CHARS * 0.85 && (
          <span className="char-count" style={{ color: remaining < 50 ? 'var(--error)' : undefined }}>
            {remaining}
          </span>
        )}
      </div>

      {/* Footer */}
      <div className="chat-input-footer">
        <span className="input-hint">
          <kbd>Ctrl</kbd>+<kbd>Enter</kbd> to send
        </span>
        <button
          className="btn-send"
          onClick={() => handleSubmit()}
          disabled={disabled || !message.trim()}
          aria-label="Send message"
        >
          <Send size={15} />
          Send
        </button>
      </div>
    </div>
  );
}
