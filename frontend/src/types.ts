export type SourceItem = {
  source: string;
  chunk_id: string;
  page?: number | null;
  score?: number | null;
  excerpt?: string | null;
  retrieval_method?: string | null;
};

export type MessageMeta = {
  model?: string;
  cached?: boolean;
  session_id?: string;
  memory_used?: boolean;
};

export type FeedbackState = 'none' | 'up' | 'down';

export type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceItem[];
  meta?: MessageMeta;
  feedback?: FeedbackState;
  timestamp?: number;
};

export type TaskType = 'qa' | 'summarize' | 'email' | 'report';

export type Toast = {
  id: string;
  type: 'success' | 'error' | 'info';
  message: string;
};

export type UploadStatus =
  | { state: 'idle' }
  | { state: 'uploading'; progress: number }
  | { state: 'success'; message: string }
  | { state: 'error'; message: string };
