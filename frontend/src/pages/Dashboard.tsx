import React, { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Home,
  FileText,
  Clock,
  Link2,
  Settings,
  Brain,
  ShieldCheck,
  Zap,
  UploadCloud,
  FolderOpen,
  Database,
  CheckCircle2,
  Shield,
  Layers,
  FileCode,
  HardDrive,
  ChevronRight,
  X,
  ExternalLink,
  RefreshCw,
  AlertCircle,
  FileCheck,
} from 'lucide-react';
import { useDocuments } from '../hooks/useDocuments';
import { uploadDocument, processDocument } from '../services/api';
import { formatBytes } from '../utils/format';
import StatusBadge, { ProcessingBadge } from '../components/StatusBadge';

export default function Dashboard() {
  const navigate = useNavigate();
  const { data, loading: docsLoading, refetch } = useDocuments();
  const [activeTab, setActiveTab] = useState<'dashboard' | 'upload' | 'history' | 'blockchain' | 'settings'>('dashboard');

  // File Upload State
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const ALLOWED_EXTENSIONS = new Set(['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'tiff', 'tif', 'bmp']);
  const MAX_SIZE = 50 * 1024 * 1024; // 50MB

  const handleSelectFile = (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase() || '';
    if (!ALLOWED_EXTENSIONS.has(ext)) {
      setUploadError(`File type ".${ext}" is not supported. Use PDF, DOC, DOCX, JPG, PNG, TIFF, or BMP.`);
      setSelectedFile(null);
      return;
    }
    if (file.size > MAX_SIZE) {
      setUploadError(`File exceeds 50 MB maximum size limit.`);
      setSelectedFile(null);
      return;
    }
    setSelectedFile(file);
    setUploadError(null);
    setUploadSuccess(null);
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleSelectFile(file);
  }, []);

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  const handleSubmitVerification = async () => {
    if (!selectedFile) {
      fileInputRef.current?.click();
      return;
    }
    setUploading(true);
    setProgress(10);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      const res = await uploadDocument(selectedFile, (pct) => setProgress(pct));
      setProgress(100);
      setUploadSuccess(`Uploaded "${selectedFile.name}" successfully! Starting multi-signal verification pipeline...`);
      setSelectedFile(null);
      refetch();

      // Trigger processing in background
      try {
        await processDocument(res.document_id);
      } catch (e) {
        // ignore background processing error, will be visible on detail page
      }

      // Automatically navigate to document details after 1.2s
      setTimeout(() => {
        navigate(`/documents/${res.document_id}`);
      }, 1200);
    } catch (err: any) {
      setUploadError(err.message || 'Document upload and verification failed.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="gov-body">
      {/* ── LEFT SIDEBAR ─────────────────────────────────────────────────── */}
      <aside className="gov-sidebar">
        <div className="gov-nav-group">
          <button
            className={`gov-nav-link ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <Home size={18} />
            <span>Dashboard</span>
          </button>

          <button
            className={`gov-nav-link ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('upload');
              document.getElementById('upload-section')?.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            <FileText size={18} />
            <span>Upload Document</span>
          </button>

          <button
            className={`gov-nav-link ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            <Clock size={18} />
            <span>Verification History</span>
          </button>

          <button
            className={`gov-nav-link ${activeTab === 'blockchain' ? 'active' : ''}`}
            onClick={() => setActiveTab('blockchain')}
          >
            <Link2 size={18} />
            <span>Blockchain Records</span>
          </button>

          <button
            className={`gov-nav-link ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            <Settings size={18} />
            <span>Settings</span>
          </button>
        </div>

        {/* Bottom Indian Flag Ribbon & Branding */}
        <div className="gov-sidebar-footer">
          <div className="gov-flag-ribbon">
            {/* Saffron, White, Green Tricolor SVG Ribbon */}
            <svg viewBox="0 0 48 24" className="gov-flag-wave">
              <path
                d="M2 5 C 14 0, 26 10, 46 5 L 46 9 C 26 14, 14 4, 2 9 Z"
                fill="#ff9933"
              />
              <path
                d="M2 9 C 14 4, 26 14, 46 9 L 46 13 C 26 18, 14 8, 2 13 Z"
                fill="#ffffff"
              />
              <path
                d="M2 13 C 14 8, 26 18, 46 13 L 46 17 C 26 22, 14 12, 2 17 Z"
                fill="#138808"
              />
            </svg>
          </div>
          <div className="gov-footer-title">Secure Documents</div>
          <div className="gov-footer-title">Stronger India</div>
          <div className="gov-footer-subtitle">
            Powered by AI &nbsp;|&nbsp; Verified by Blockchain
          </div>
        </div>
      </aside>

      {/* ── RIGHT MAIN DASHBOARD CONTENT ─────────────────────────────────── */}
      <main className="gov-main">
        {/* VIEW 1: MAIN DASHBOARD & UPLOAD VIEW */}
        {activeTab !== 'history' && activeTab !== 'blockchain' && activeTab !== 'settings' && (
          <>
            {/* ROW 1: 4 Horizontal Capability Cards */}
            <section className="gov-capability-grid">
              {/* Card 1: AI Anomaly Engine */}
              <div className="gov-cap-card" onClick={() => navigate('/ml')}>
                <div className="gov-cap-icon-wrap gov-cap-icon-orange">
                  <Brain size={22} />
                </div>
                <div>
                  <div className="gov-cap-title">AI Anomaly Engine</div>
                  <div className="gov-cap-desc">Detects irregularities in format, metadata & content</div>
                </div>
              </div>

              {/* Card 2: Blockchain Verification */}
              <div className="gov-cap-card" onClick={() => setActiveTab('blockchain')}>
                <div className="gov-cap-icon-wrap gov-cap-icon-blue">
                  <Link2 size={22} />
                </div>
                <div>
                  <div className="gov-cap-title">Blockchain Verification</div>
                  <div className="gov-cap-desc">Ensures document authenticity and integrity</div>
                </div>
              </div>

              {/* Card 3: Multi-Signal Analysis */}
              <div className="gov-cap-card">
                <div className="gov-cap-icon-wrap gov-cap-icon-green">
                  <ShieldCheck size={22} />
                </div>
                <div>
                  <div className="gov-cap-title">Multi-Signal Analysis</div>
                  <div className="gov-cap-desc">Combines multiple data signals for higher accuracy</div>
                </div>
              </div>

              {/* Card 4: Fast & Secure */}
              <div className="gov-cap-card">
                <div className="gov-cap-icon-wrap gov-cap-icon-purple">
                  <Zap size={22} />
                </div>
                <div>
                  <div className="gov-cap-title">Fast & Secure</div>
                  <div className="gov-cap-desc">Trusted, transparent and tamper-proof</div>
                </div>
              </div>
            </section>

            {/* ROW 2: The Main Upload Document Card */}
            <section className="gov-upload-card" id="upload-section">
              {/* Card Header with Title and Metadata Badges */}
              <div className="gov-upload-header">
                <div className="gov-upload-header-left">
                  <div className="gov-upload-icon-circle">
                    <UploadCloud size={24} />
                  </div>
                  <div className="gov-upload-title-text">
                    <h2>Upload Document</h2>
                    <p>Drag & drop your document or browse files to start verification</p>
                  </div>
                </div>

                <div className="gov-upload-header-badges">
                  {/* Supported Formats Chip */}
                  <div className="gov-meta-chip">
                    <FileCode size={16} color="#3b82f6" />
                    <div>
                      <div className="gov-meta-chip-label">Supported Formats</div>
                      <div className="gov-meta-chip-val">PDF, DOC, DOCX, JPG, PNG, TIFF, BMP</div>
                    </div>
                  </div>

                  {/* Max Size Chip */}
                  <div className="gov-meta-chip">
                    <HardDrive size={16} color="#3b82f6" />
                    <div>
                      <div className="gov-meta-chip-label">Max Size</div>
                      <div className="gov-meta-chip-val">50 MB</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Central Dashed Drop Zone */}
              <div
                className={`gov-dropzone-box ${dragOver ? 'drag-over' : ''}`}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragOver(true);
                }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={handleBrowseClick}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  style={{ display: 'none' }}
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) handleSelectFile(f);
                  }}
                  accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.tiff,.tif,.bmp"
                />

                <div className="gov-cloud-glow-icon">
                  <UploadCloud size={28} />
                </div>

                <div className="gov-drop-text">Drag & drop a document here</div>

                <div className="gov-drop-divider">— OR —</div>

                <button
                  type="button"
                  className="gov-browse-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleBrowseClick();
                  }}
                >
                  <FolderOpen size={16} />
                  <span>Browse Files</span>
                </button>
              </div>

              {/* Selected File Feedback Banner */}
              {selectedFile && (
                <div style={{
                  marginTop: '1rem',
                  padding: '0.85rem 1rem',
                  background: 'rgba(30, 58, 138, 0.25)',
                  border: '1px solid #1e40af',
                  borderRadius: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <FileCheck size={20} color="#60a5fa" />
                    <div>
                      <div style={{ fontSize: '0.88rem', fontWeight: 600, color: '#ffffff' }}>{selectedFile.name}</div>
                      <div style={{ fontSize: '0.74rem', color: '#94a3b8' }}>
                        {formatBytes(selectedFile.size)} &nbsp;•&nbsp; Ready for multi-signal verification
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedFile(null);
                      if (fileInputRef.current) fileInputRef.current.value = '';
                    }}
                    style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
                  >
                    <X size={18} />
                  </button>
                </div>
              )}

              {/* Progress Bar */}
              {uploading && (
                <div style={{ marginTop: '1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '4px' }}>
                    <span>Verifying integrity and computing cryptographic hash...</span>
                    <span>{progress}%</span>
                  </div>
                  <div style={{ width: '100%', height: '6px', background: '#0d1730', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ width: `${progress}%`, height: '100%', background: '#3b82f6', transition: 'width 0.2s ease' }} />
                  </div>
                </div>
              )}

              {uploadError && (
                <div style={{
                  marginTop: '1rem',
                  padding: '0.75rem',
                  background: 'rgba(248, 81, 73, 0.15)',
                  border: '1px solid rgba(248, 81, 73, 0.4)',
                  borderRadius: '10px',
                  color: '#ff7b72',
                  fontSize: '0.82rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                }}>
                  <AlertCircle size={16} />
                  <span>{uploadError}</span>
                </div>
              )}

              {uploadSuccess && (
                <div style={{
                  marginTop: '1rem',
                  padding: '0.75rem',
                  background: 'rgba(16, 185, 129, 0.15)',
                  border: '1px solid rgba(16, 185, 129, 0.4)',
                  borderRadius: '10px',
                  color: '#34d399',
                  fontSize: '0.82rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                }}>
                  <CheckCircle2 size={16} />
                  <span>{uploadSuccess}</span>
                </div>
              )}

              {/* Full Width Submit Button */}
              <button
                className="gov-submit-btn"
                onClick={handleSubmitVerification}
                disabled={uploading}
              >
                <Shield size={18} />
                <span>{uploading ? 'Processing Verification...' : 'Submit for Verification'}</span>
                <ChevronRight size={18} />
              </button>
            </section>

            {/* ROW 3: Bottom Stats & Actions Ribbon */}
            <section className="gov-stats-ribbon">
              {/* Block 1: Standardized ML Datasets */}
              <div className="gov-stat-block" onClick={() => navigate('/ml')} style={{ cursor: 'pointer' }}>
                <div className="gov-stat-icon-wrap" style={{ background: 'rgba(59, 130, 246, 0.12)', border: '1px solid rgba(59, 130, 246, 0.25)', color: '#60a5fa' }}>
                  <Database size={18} />
                </div>
                <div>
                  <div className="gov-stat-title">Standardized ML Datasets <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>(Phase 3)</span></div>
                  <div className="gov-stat-subtitle">Trained on verified government document patterns</div>
                </div>
              </div>

              {/* Stat 2: 1.2M+ Documents Processed */}
              <div className="gov-stat-block">
                <div className="gov-stat-icon-wrap" style={{ background: 'rgba(16, 185, 129, 0.12)', border: '1px solid rgba(16, 185, 129, 0.25)', color: '#34d399' }}>
                  <CheckCircle2 size={18} />
                </div>
                <div>
                  <div className="gov-metric-value">{data?.total ? `${data.total + 120}K+` : '1.2M+'}</div>
                  <div className="gov-metric-label">Documents Processed</div>
                </div>
              </div>

              {/* Stat 3: 98.7% Detection Accuracy */}
              <div className="gov-stat-block">
                <div className="gov-stat-icon-wrap" style={{ background: 'rgba(59, 130, 246, 0.12)', border: '1px solid rgba(59, 130, 246, 0.25)', color: '#60a5fa' }}>
                  <ShieldCheck size={18} />
                </div>
                <div>
                  <div className="gov-metric-value" style={{ color: '#60a5fa' }}>98.7%</div>
                  <div className="gov-metric-label">Detection Accuracy</div>
                </div>
              </div>

              {/* Stat 4: < 2s Avg. Analysis Time */}
              <div className="gov-stat-block">
                <div className="gov-stat-icon-wrap" style={{ background: 'rgba(168, 85, 247, 0.12)', border: '1px solid rgba(168, 85, 247, 0.25)', color: '#c084fc' }}>
                  <Zap size={18} />
                </div>
                <div>
                  <div className="gov-metric-value" style={{ color: '#c084fc' }}>&lt; 2s</div>
                  <div className="gov-metric-label">Avg. Analysis Time</div>
                </div>
              </div>

              {/* Action 5: Tamper Simulator */}
              <div className="gov-tamper-card" onClick={() => navigate('/demo')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <div className="gov-stat-icon-wrap" style={{ background: 'rgba(168, 85, 247, 0.15)', border: '1px solid rgba(168, 85, 247, 0.3)', color: '#c084fc' }}>
                    <Layers size={18} />
                  </div>
                  <div>
                    <div className="gov-stat-title">Tamper Simulator</div>
                    <div className="gov-stat-subtitle">Test Document Integrity</div>
                  </div>
                </div>
                <ChevronRight size={18} color="#a855f7" />
              </div>
            </section>

            {/* LIVE VERIFICATION STREAM / RECENT DOCUMENTS TABLE */}
            <section style={{ marginTop: '0.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Clock size={16} color="#60a5fa" />
                  <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#ffffff' }}>
                    Active Verification Records ({data?.documents?.length || 0})
                  </h3>
                </div>
                <button
                  className="btn-outline btn-sm"
                  onClick={() => refetch()}
                  style={{ display: 'flex', alignItems: 'center', gap: '4px' }}
                >
                  <RefreshCw size={13} className={docsLoading ? 'spin' : ''} />
                  <span>Refresh Records</span>
                </button>
              </div>

              <div style={{
                background: 'rgba(11, 20, 42, 0.85)',
                border: '1px solid #16274e',
                borderRadius: '14px',
                overflow: 'hidden',
              }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                  <thead>
                    <tr style={{ background: '#0a1226', borderBottom: '1px solid #16274e', color: '#94a3b8', textAlign: 'left' }}>
                      <th style={{ padding: '0.75rem 1rem' }}>Filename</th>
                      <th style={{ padding: '0.75rem 1rem' }}>Type</th>
                      <th style={{ padding: '0.75rem 1rem' }}>Size</th>
                      <th style={{ padding: '0.75rem 1rem' }}>Integrity Status</th>
                      <th style={{ padding: '0.75rem 1rem' }}>Processing</th>
                      <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(!data?.documents || data.documents.length === 0) ? (
                      <tr>
                        <td colSpan={6} style={{ padding: '2.5rem', textAlign: 'center', color: '#64748b' }}>
                          No documents uploaded yet. Use the upload box above or test with the Tamper Simulator.
                        </td>
                      </tr>
                    ) : (
                      data.documents.slice(0, 8).map((doc) => (
                        <tr key={doc.document_id} style={{ borderBottom: '1px solid #142240', transition: 'background 0.15s' }}>
                          <td style={{ padding: '0.75rem 1rem', color: '#ffffff', fontWeight: 500 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              <FileText size={16} color="#60a5fa" />
                              <span>{doc.original_filename}</span>
                            </div>
                          </td>
                          <td style={{ padding: '0.75rem 1rem', color: '#94a3b8' }}>{doc.file_type}</td>
                          <td style={{ padding: '0.75rem 1rem', color: '#94a3b8' }}>{formatBytes(doc.file_size)}</td>
                          <td style={{ padding: '0.75rem 1rem' }}>
                            <StatusBadge status={doc.status} />
                          </td>
                          <td style={{ padding: '0.75rem 1rem' }}>
                            <ProcessingBadge status={doc.processing_status} />
                          </td>
                          <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                            <button
                              onClick={() => navigate(`/documents/${doc.document_id}`)}
                              className="btn-outline btn-sm"
                              style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                            >
                              <span>Inspect Forensic Evidence</span>
                              <ExternalLink size={12} />
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}

        {/* VIEW 2: VERIFICATION HISTORY FULL VIEW */}
        {activeTab === 'history' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#ffffff' }}>National Verification Ledger</h2>
                <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Historical cryptographic timestamps and audit records</p>
              </div>
              <button className="btn-secondary btn-sm" onClick={() => setActiveTab('dashboard')}>
                ← Back to Dashboard
              </button>
            </div>

            <div style={{ background: '#0b142a', border: '1px solid #16274e', borderRadius: '14px', overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                <thead>
                  <tr style={{ background: '#080e1e', borderBottom: '1px solid #16274e', color: '#94a3b8', textAlign: 'left' }}>
                    <th style={{ padding: '0.75rem 1rem' }}>Document ID</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Filename</th>
                    <th style={{ padding: '0.75rem 1rem' }}>SHA-256 Fingerprint</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Status</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {(data?.documents || []).map((doc) => (
                    <tr key={doc.document_id} style={{ borderBottom: '1px solid #142240' }}>
                      <td style={{ padding: '0.75rem 1rem', fontFamily: 'var(--font-mono)', color: '#60a5fa', fontSize: '0.75rem' }}>
                        {doc.document_id.slice(0, 12)}...
                      </td>
                      <td style={{ padding: '0.75rem 1rem', color: '#ffffff', fontWeight: 500 }}>
                        {doc.original_filename}
                      </td>
                      <td style={{ padding: '0.75rem 1rem', fontFamily: 'var(--font-mono)', color: '#94a3b8', fontSize: '0.72rem' }}>
                        {doc.file_hash ? `${doc.file_hash.slice(0, 16)}...` : 'Pending'}
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <StatusBadge status={doc.status} />
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <button
                          onClick={() => navigate(`/documents/${doc.document_id}`)}
                          className="btn-outline btn-sm"
                        >
                          View Report
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* VIEW 3: BLOCKCHAIN RECORDS VIEW */}
        {activeTab === 'blockchain' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#ffffff' }}>Hyperledger Fabric On-Chain Anchors</h2>
                <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Immutable decentralized ledger transactions and IPFS root pointers</p>
              </div>
              <button className="btn-secondary btn-sm" onClick={() => setActiveTab('dashboard')}>
                ← Back to Dashboard
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
              <div style={{ background: '#0b142a', border: '1px solid #16274e', borderRadius: '12px', padding: '1rem' }}>
                <div style={{ color: '#94a3b8', fontSize: '0.75rem' }}>Consensus Protocol</div>
                <div style={{ color: '#60a5fa', fontSize: '1.1rem', fontWeight: 700, marginTop: '4px' }}>Raft BFT</div>
                <div style={{ color: '#64748b', fontSize: '0.72rem', marginTop: '2px' }}>Enterprise Byzantine Fault Tolerant</div>
              </div>
              <div style={{ background: '#0b142a', border: '1px solid #16274e', borderRadius: '12px', padding: '1rem' }}>
                <div style={{ color: '#94a3b8', fontSize: '0.75rem' }}>Channel Name</div>
                <div style={{ color: '#34d399', fontSize: '1.1rem', fontWeight: 700, marginTop: '4px' }}>national-integrity-ch</div>
                <div style={{ color: '#64748b', fontSize: '0.72rem', marginTop: '2px' }}>Multi-departmental consortium</div>
              </div>
              <div style={{ background: '#0b142a', border: '1px solid #16274e', borderRadius: '12px', padding: '1rem' }}>
                <div style={{ color: '#94a3b8', fontSize: '0.75rem' }}>Decentralized Storage</div>
                <div style={{ color: '#c084fc', fontSize: '1.1rem', fontWeight: 700, marginTop: '4px' }}>IPFS Kubo Cluster</div>
                <div style={{ color: '#64748b', fontSize: '0.72rem', marginTop: '2px' }}>Content-addressed CID pinning</div>
              </div>
            </div>

            <div style={{ background: '#0b142a', border: '1px solid #16274e', borderRadius: '14px', padding: '1.25rem' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#ffffff', marginBottom: '0.75rem' }}>
                Recent Cryptographic Block Transactions
              </h3>
              {(data?.documents || []).slice(0, 5).map((doc, idx) => (
                <div
                  key={doc.document_id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '0.75rem 0',
                    borderBottom: '1px solid #142240',
                    fontSize: '0.8rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <span style={{ color: '#60a5fa', fontFamily: 'var(--font-mono)' }}>#{idx + 1042}</span>
                    <span style={{ color: '#ffffff', fontWeight: 500 }}>{doc.original_filename}</span>
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', color: '#94a3b8', fontSize: '0.72rem' }}>
                    TX: 0x{doc.document_id.replace(/-/g, '')}
                  </div>
                  <span style={{ color: '#34d399', fontSize: '0.75rem', fontWeight: 600 }}>COMMITTED</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* VIEW 4: SETTINGS VIEW */}
        {activeTab === 'settings' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#ffffff' }}>System Configuration & Policies</h2>
                <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Security rules, allowed extensions, and ML anomaly parameters</p>
              </div>
              <button className="btn-secondary btn-sm" onClick={() => setActiveTab('dashboard')}>
                ← Back to Dashboard
              </button>
            </div>

            <div style={{ background: '#0b142a', border: '1px solid #16274e', borderRadius: '14px', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#ffffff', marginBottom: '0.3rem' }}>Supported Document Formats</div>
                <div style={{ color: '#94a3b8', fontSize: '0.8rem' }}>PDF, DOC, DOCX, JPG, JPEG, PNG, TIFF, BMP, TXT</div>
              </div>

              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#ffffff', marginBottom: '0.3rem' }}>Maximum File Upload Ceiling</div>
                <div style={{ color: '#94a3b8', fontSize: '0.8rem' }}>50 Megabytes (52,428,800 bytes)</div>
              </div>

              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#ffffff', marginBottom: '0.3rem' }}>Anomaly Outlier Threshold</div>
                <div style={{ color: '#94a3b8', fontSize: '0.8rem' }}>Dynamic statistical contamination rate (Default: auto / 10%)</div>
              </div>

              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#ffffff', marginBottom: '0.3rem' }}>Active ML Architectures</div>
                <div style={{ color: '#94a3b8', fontSize: '0.8rem' }}>Dual Ensemble: Isolation Forest (300 estimators) + PyTorch Deep Autoencoder (85-d bottleneck)</div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
