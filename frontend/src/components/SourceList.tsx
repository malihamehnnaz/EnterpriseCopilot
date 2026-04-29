import { useState } from 'react';
import { ChevronRight, FileText, Hash } from 'lucide-react';
import type { SourceItem } from '../types';

type Props = {
  sources: SourceItem[];
};

export function SourceList({ sources }: Props) {
  const [open, setOpen] = useState(false);

  if (!sources.length) return null;

  return (
    <div className="sources-section">
      <button
        className={`sources-toggle${open ? ' open' : ''}`}
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <ChevronRight size={13} />
        {sources.length} source{sources.length !== 1 ? 's' : ''} cited
      </button>

      {open && (
        <div className="source-cards">
          {sources.map((src) => (
            <div key={src.chunk_id} className="source-card">
              <div className="source-card-header">
                <FileText size={13} color="var(--accent)" style={{ flexShrink: 0 }} />
                <span className="source-filename" title={src.source}>
                  {src.source}
                </span>
                {src.page != null && (
                  <span className="source-page">p. {src.page}</span>
                )}
                {src.score != null && (
                  <span className="source-score">{(src.score * 100).toFixed(0)}%</span>
                )}
                {src.retrieval_method && (
                  <span className="source-method-badge">{src.retrieval_method}</span>
                )}
              </div>
              {src.chunk_id && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 4 }}>
                  <Hash size={10} color="var(--text-muted)" />
                  <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                    {src.chunk_id.slice(0, 16)}…
                  </span>
                </div>
              )}
              {src.excerpt && (
                <p className="source-excerpt">{src.excerpt}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

