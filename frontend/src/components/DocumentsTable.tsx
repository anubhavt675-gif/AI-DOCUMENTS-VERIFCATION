import { useNavigate } from 'react-router-dom';
import { FileText, FolderOpen, RefreshCw } from 'lucide-react';
import { format } from 'date-fns';
import type { Document } from '../types';
import { ProcessingBadge, ReadinessBadge } from './StatusBadge';
import { formatBytes, mimeLabel, shortId } from '../utils/format';

interface DocumentsTableProps {
  documents: Document[];
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}

export default function DocumentsTable({
  documents,
  loading,
  error,
  onRefresh,
}: DocumentsTableProps) {
  const navigate = useNavigate();

  if (loading) {
    return (
      <section className="card">
        <div className="card-header">
          <FileText size={18} />
          <h2 className="card-title">Documents</h2>
        </div>
        <div className="loading-rows">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="skeleton-row" />
          ))}
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="card">
        <div className="card-header">
          <FileText size={18} />
          <h2 className="card-title">Documents</h2>
        </div>
        <div className="alert alert-error" style={{ margin: '1rem 0' }}>
          {error}
          <button className="btn-ghost" onClick={onRefresh}>Retry</button>
        </div>
      </section>
    );
  }

  return (
    <section className="card">
      <div className="card-header">
        <FileText size={18} />
        <h2 className="card-title">
          Documents
          {documents.length > 0 && (
            <span className="count-chip">{documents.length}</span>
          )}
        </h2>
        <button
          className="btn-icon ml-auto"
          onClick={onRefresh}
          title="Refresh"
          aria-label="Refresh document list"
        >
          <RefreshCw size={15} />
        </button>
      </div>

      {documents.length === 0 ? (
        <div className="empty-state">
          <FolderOpen size={48} className="empty-icon" />
          <p className="empty-title">No documents yet</p>
          <p className="empty-sub">
            Upload a document above to begin the verification process.
          </p>
        </div>
      ) : (
        <div className="table-wrap">
          <table className="doc-table" role="table">
            <thead>
              <tr>
                <th>Document ID</th>
                <th>Filename</th>
                <th>Type</th>
                <th>Size</th>
                <th>Uploaded</th>
                <th>Processing</th>
                <th>Verification Readiness</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.document_id} className="doc-row">
                  <td>
                    <code className="doc-id">{shortId(doc.document_id)}</code>
                  </td>
                  <td className="filename-cell" title={doc.original_filename}>
                    {doc.original_filename}
                  </td>
                  <td>
                    <span className="type-chip">{mimeLabel(doc.file_type)}</span>
                  </td>
                  <td>{formatBytes(doc.file_size)}</td>
                  <td>
                    {format(new Date(doc.upload_timestamp), 'dd MMM yyyy, HH:mm')}
                  </td>
                  <td>
                    <ProcessingBadge status={doc.processing_status} />
                  </td>
                  <td>
                    <ReadinessBadge processingStatus={doc.processing_status} />
                  </td>
                  <td>
                    <button
                      className="btn-view"
                      onClick={() => navigate(`/documents/${doc.document_id}`)}
                      aria-label={`View document ${doc.original_filename}`}
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
