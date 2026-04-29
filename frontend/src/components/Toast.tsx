import { useEffect, useState } from 'react';
import { CheckCircle, XCircle, Info, X } from 'lucide-react';
import type { Toast as ToastType } from '../types';

type Props = {
  toasts: ToastType[];
  onRemove: (id: string) => void;
};

const ICONS = {
  success: <CheckCircle size={16} color="var(--success)" />,
  error:   <XCircle    size={16} color="var(--error)"   />,
  info:    <Info       size={16} color="var(--accent)"  />,
};

const TITLES = { success: 'Success', error: 'Error', info: 'Info' };

function ToastItem({ toast, onRemove }: { toast: ToastType; onRemove: (id: string) => void }) {
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setExiting(true);
      setTimeout(() => onRemove(toast.id), 220);
    }, 4000);
    return () => clearTimeout(timer);
  }, [toast.id, onRemove]);

  const handleClose = () => {
    setExiting(true);
    setTimeout(() => onRemove(toast.id), 220);
  };

  return (
    <div className={`toast ${toast.type}${exiting ? ' exiting' : ''}`}>
      <span className="toast-icon">{ICONS[toast.type]}</span>
      <div className="toast-content">
        <div className="toast-title">{TITLES[toast.type]}</div>
        <div className="toast-body">{toast.message}</div>
      </div>
      <button className="toast-close" onClick={handleClose} aria-label="Close">
        <X size={14} />
      </button>
    </div>
  );
}

export function ToastContainer({ toasts, onRemove }: Props) {
  if (!toasts.length) return null;
  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onRemove={onRemove} />
      ))}
    </div>
  );
}
