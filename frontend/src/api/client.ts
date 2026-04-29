import type { SourceItem, TaskType } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

function buildHeaders(sessionId?: string): Record<string, string> {
  const headers: Record<string, string> = {
    'x-user-id': 'frontend.user',
    'x-user-role': 'analyst',
  };
  if (sessionId) {
    headers['x-session-id'] = sessionId;
  }
  return headers;
}

export async function uploadDocument(file: File, allowedRoles: string[]) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('allowed_roles', allowedRoles.join(','));

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    headers: buildHeaders(),
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Upload failed (${response.status})`);
  }

  return response.json();
}

export async function submitFeedback(payload: {
  session_id?: string;
  helpful: boolean;
  rating: number;
  feedback_text?: string;
}): Promise<{ feedback_id: string; status: string }> {
  const response = await fetch(`${API_BASE_URL}/feedback`, {
    method: 'POST',
    headers: { ...buildHeaders(payload.session_id), 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error('Failed to submit feedback');
  }

  return response.json();
}

export async function streamChat(
  message: string,
  taskType: TaskType,
  sessionId: string,
  handlers: {
    onChunk: (chunk: string) => void;
    onSources: (sources: SourceItem[]) => void;
    onMeta: (meta: { model?: string; cached?: boolean; session_id?: string; memory_used?: boolean }) => void;
    onDone: () => void;
  },
) {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: { ...buildHeaders(sessionId), 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, task_type: taskType, stream: true, session_id: sessionId }),
  });

  if (!response.ok || !response.body) {
    const text = await response.text().catch(() => '');
    throw new Error(text || `Request failed (${response.status})`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split('\n\n');
    buffer = events.pop() ?? '';

    for (const event of events) {
      if (!event.startsWith('data: ')) continue;
      try {
        const payload = JSON.parse(event.slice(6));
        if (payload.type === 'chunk') handlers.onChunk(payload.content);
        if (payload.type === 'sources') handlers.onSources(payload.content);
        if (payload.type === 'meta') handlers.onMeta(payload.content);
        if (payload.type === 'done') handlers.onDone();
      } catch {
        // skip malformed events
      }
    }
  }
}
