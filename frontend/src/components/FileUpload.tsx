import { useState, useRef, type DragEvent, type ChangeEvent } from 'react';
import { UploadCloud, FileText, X, CheckCircle, AlertCircle, Loader } from 'lucide-react';
import { uploadDocument } from '../api/client';
import type { UploadStatus } from '../types';

const AVAILABLE_ROLES = ['viewer', 'analyst', 'manager', 'admin'];

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

type Props = {
  onUploaded?: (message: string) => void;
};

export function FileUpload({ onUploaded }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [allowedRoles, setAllowedRoles] = useState<string[]>(['viewer', 'analyst', 'manager', 'admin']);
  const [status, setStatus] = useState<UploadStatus>({ state: 'idle' });
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const pickFile = (f: File) => setFile(f);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) pickFile(f);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f) pickFile(f);
  };

  const toggleRole = (role: string) => {
    setAllowedRoles((prev) =>
      prev.includes(role) ? prev.filter((r) => r !== role) : [...prev, role],
    );
  };

  const handleUpload = async () => {
    if (!file) return;
    setStatus({ state: 'uploading', progress: 0 });
    try {
      const result = await uploadDocument(file, allowedRoles);
      const msg = `Indexed ${result.chunks_indexed} chunks from "${result.filename}".`;
      setStatus({ state: 'success', message: msg });
      setFile(null);
      if (inputRef.current) inputRef.current.value = '';
      onUploaded?.(msg);
    } catch (error) {
      setStatus({
        state: 'error',
        message: error instanceof Error ? error.message : 'Upload failed.',
      });
    }
  };

  return (
    <div className="panel upload-panel">
      <div className="panel-body">
        <div className="panel-heading">
          <div className="panel-heading-icon">
            <UploadCloud size={16} />
          </div>
          <div>
            <h3>Knowledge Ingestion</h3>
            <p>Upload documents to the secured vector store</p>
          </div>
        </div>

        {/* Drop zone */}
        <div
          className={`drop-zone${dragOver ? ' drag-over' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx,.txt,.md"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
          <div className="drop-zone-icon">
            <UploadCloud size={20} />
          </div>
          <p className="drop-zone-title">
            {dragOver ? 'Drop to upload' : 'Click or drag & drop'}
          </p>
          <p className="drop-zone-sub">PDF, DOCX, TXT, MD</p>
        </div>

        {/* Selected file chip */}
        {file && (
          <div className="selected-file">
            <FileText size={16} className="selected-file-icon" />
            <span className="selected-file-name">{file.name}</span>
            <span className="selected-file-size">{formatBytes(file.size)}</span>
            <button className="btn-icon" onClick={() => setFile(null)} aria-label="Remove file">
              <X size={13} />
            </button>
          </div>
        )}

        {/* Role access */}
        <div className="role-section">
          <p className="role-section-label">Access roles</p>
          <div className="role-grid">
            {AVAILABLE_ROLES.map((role) => (
              <label
                key={role}
                className={`role-chip${allowedRoles.includes(role) ? ' selected' : ''}`}
                onClick={() => toggleRole(role)}
              >
                <input type="checkbox" readOnly checked={allowedRoles.includes(role)} />
                <span className="role-chip-dot" />
                <span>{role}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Upload button */}
        <button
          className="btn-upload"
          onClick={handleUpload}
          disabled={!file || status.state === 'uploading'}
        >
          {status.state === 'uploading' ? (
            <>
              <Loader size={15} style={{ animation: 'spin 1s linear infinite' }} />
              Uploading…
            </>
          ) : (
            <>
              <UploadCloud size={15} />
              Upload Document
            </>
          )}
        </button>

        {/* Status message */}
        {status.state === 'success' && (
          <div className="upload-status success">
            <CheckCircle size={14} style={{ flexShrink: 0, marginTop: 1 }} />
            <span>{status.message}</span>
          </div>
        )}
        {status.state === 'error' && (
          <div className="upload-status error">
            <AlertCircle size={14} style={{ flexShrink: 0, marginTop: 1 }} />
            <span>{status.message}</span>
          </div>
        )}
      </div>
    </div>
  );
}
