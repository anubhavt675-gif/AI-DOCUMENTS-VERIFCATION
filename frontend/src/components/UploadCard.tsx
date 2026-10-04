import { useCallback, useRef, useState } from 'react';
import { UploadCloud, FileText, X, CheckCircle, AlertCircle } from 'lucide-react';
import { uploadDocument } from '../services/api';
import { formatBytes } from '../utils/format';

interface UploadCardProps {
  onUploadSuccess: () => void;
}

type UploadState = 'idle' | 'uploading' | 'success' | 'error';

const ACCEPTED_TYPES =
  '.pdf,.doc,.docx,.jpg,.jpeg,.png,.tiff,.tif,.bmp';

const MAX_SIZE_BYTES = 50 * 1024 * 1024; // 50 MB

export default function UploadCard({ onUploadSuccess }: UploadCardProps) {
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [state, setState] = useState<UploadState>('idle');
  const [message, setMessage] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const ALLOWED_EXTENSIONS = new Set([
    'pdf','doc','docx','jpg','jpeg','png','tiff','tif','bmp',
  ]);

  const validateFile = (file: File): string | null => {
    const ext = file.name.split('.').pop()?.toLowerCase() ?? '';
    if (!ALLOWED_EXTENSIONS.has(ext)) {
      return `File type ".${ext}" is not supported.`;
    }
    if (file.size > MAX_SIZE_BYTES) {
      return `File size ${formatBytes(file.size)} exceeds the 50 MB limit.`;
    }
    return null;
  };

  const selectFile = useCallback((file: File) => {
    const err = validateFile(file);
    if (err) {
      setState('error');
      setMessage(err);
      setSelectedFile(null);
      return;
    }
    setSelectedFile(file);
    setState('idle');
    setMessage('');
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) selectFile(file);
    },
    [selectFile]
  );

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) selectFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setState('uploading');
    setProgress(0);
    setMessage('');
    try {
      await uploadDocument(selectedFile, (pct) => setProgress(pct));
      setState('success');
      setMessage('Document uploaded successfully. Preprocessing pipeline initiated in background.');
      setSelectedFile(null);
      onUploadSuccess();
    } catch (e: unknown) {
      setState('error');
      setMessage(e instanceof Error ? e.message : 'Upload failed.');
    }
  };

  const reset = () => {
    setState('idle');
    setSelectedFile(null);
    setMessage('');
    setProgress(0);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <section className="card upload-card">
      <div className="card-header">
        <UploadCloud size={18} />
        <h2 className="card-title">Upload Document</h2>
      </div>

      {/* Drop zone */}
      <div
        className={`drop-zone ${dragOver ? 'drag-over' : ''} ${selectedFile ? 'has-file' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
        aria-label="Drop zone for document upload"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_TYPES}
          style={{ display: 'none' }}
          onChange={handleFileChange}
          id="file-input"
        />

        {selectedFile ? (
          <div className="file-selected">
            <FileText size={28} className="file-icon" />
            <div className="file-info">
              <span className="file-name">{selectedFile.name}</span>
              <span className="file-size">{formatBytes(selectedFile.size)}</span>
            </div>
            <button
              className="btn-icon"
              onClick={(e) => { e.stopPropagation(); reset(); }}
              aria-label="Remove file"
            >
              <X size={16} />
            </button>
          </div>
        ) : (
          <div className="drop-prompt">
            <UploadCloud size={36} className="drop-icon" />
            <p className="drop-text">Drag & drop a document here</p>
            <p className="drop-or">or</p>
            <span className="btn-outline">Browse Files</span>
          </div>
        )}
      </div>

      {/* Format info */}
      <p className="upload-meta">
        Accepted formats: PDF, DOC, DOCX, JPG, PNG, TIFF, BMP &nbsp;·&nbsp; Max 50 MB
      </p>

      {/* Progress bar */}
      {state === 'uploading' && (
        <div className="progress-wrap" role="progressbar" aria-valuenow={progress} aria-valuemax={100}>
          <div className="progress-bar" style={{ width: `${progress}%` }} />
          <span className="progress-label">{progress}%</span>
        </div>
      )}

      {/* Status message */}
      {state === 'success' && (
        <div className="alert alert-success">
          <CheckCircle size={16} />
          {message}
        </div>
      )}
      {state === 'error' && (
        <div className="alert alert-error">
          <AlertCircle size={16} />
          {message}
        </div>
      )}

      {/* Upload button */}
      <button
        className="btn-primary"
        disabled={!selectedFile || state === 'uploading'}
        onClick={handleUpload}
        id="upload-btn"
      >
        {state === 'uploading' ? 'Uploading…' : 'Submit for Verification'}
      </button>
    </section>
  );
}
