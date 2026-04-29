import { ThumbsUp, ThumbsDown } from 'lucide-react';
import type { FeedbackState } from '../types';

type Props = {
  state: FeedbackState;
  disabled?: boolean;
  onFeedback: (helpful: boolean) => void;
};

export function FeedbackButtons({ state, disabled, onFeedback }: Props) {
  return (
    <div className="feedback-bar">
      <span className="feedback-label">Was this helpful?</span>
      <button
        className={`btn-feedback${state === 'up' ? ' active-up' : ''}`}
        disabled={disabled || state !== 'none'}
        onClick={() => onFeedback(true)}
        aria-label="Thumbs up"
        title="Helpful"
      >
        <ThumbsUp size={13} />
        Yes
      </button>
      <button
        className={`btn-feedback${state === 'down' ? ' active-down' : ''}`}
        disabled={disabled || state !== 'none'}
        onClick={() => onFeedback(false)}
        aria-label="Thumbs down"
        title="Not helpful"
      >
        <ThumbsDown size={13} />
        No
      </button>
    </div>
  );
}
