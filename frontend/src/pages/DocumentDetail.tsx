import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  FileText,
  Calendar,
  HardDrive,
  Tag,
  Clock,
  Info,
  Hash,
  Copy,
  Check,
  RefreshCw,
  Layers,
  Database,
  Eye,
  AlertTriangle,
  Scan,
  Cpu,
  BarChart3,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { format } from 'date-fns';
import {
  useDocument,
  useDocumentAnalysis,
  useDocumentFeatures,
  useDocumentPredictions,
} from '../hooks/useDocuments';
import StatusBadge, { ProcessingBadge, ReadinessBadge } from '../components/StatusBadge';
import { formatBytes, mimeLabel } from '../utils/format';
import VerificationTimeline from '../components/VerificationTimeline';
import UnifiedIntegrityCard from '../components/UnifiedIntegrityCard';
import BlockchainExplorerPanel from '../components/BlockchainExplorerPanel';
import IPFSStoragePanel from '../components/IPFSStoragePanel';
import TechnicalExplanationPanel from '../components/TechnicalExplanationPanel';
import {
  predictAdvancedAutoencoder,
  uploadToIPFS,
  verifyIPFSContent,
  registerOnBlockchain,
  verifyOnBlockchain,
  getBlockchainHistory,
  registerDocumentIntegrity,
  verifyDocumentIntegrity,
} from '../services/api';
import type {
  AdvancedMLPrediction,
  BlockchainVerifyResponse,
  BlockchainHistoryResponse,
  IPFSVerifyResponse,
  IntegratedVerificationResponse,
} from '../types';

export default function DocumentDetail() {
  const { documentId } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const { document, loading: docLoading, error: docError } = useDocument(documentId);
  const {
    analysis,
    loading: analysisLoading,
    processing: isReprocessing,
    error: analysisError,
    reprocess,
  } = useDocumentAnalysis(documentId);
  const {
    features,
    generating: isGeneratingFeatures,
    error: featuresError,
    extract: generateFeatures,
  } = useDocumentFeatures(documentId);
  const {
    latestPrediction,
    predicting: isPredictingAnomaly,
    error: predictionError,
    predict: runAnomalyDetection,
  } = useDocumentPredictions(documentId);

  const [copiedHash, setCopiedHash] = useState(false);
  const [copiedFeatures, setCopiedFeatures] = useState(false);
  const [textMode, setTextMode] = useState<'preview' | 'full' | 'raw'>('preview');
  const [featureCategory, setFeatureCategory] = useState<string>('all');
  const [featureSearch, setFeatureSearch] = useState<string>('');

  // ── Phase 5-7 States ─────────────────────────────────────────
  const [autoencoderPrediction, setAutoencoderPrediction] = useState<AdvancedMLPrediction | null>(null);
  const [verificationResult, setVerificationResult] = useState<IntegratedVerificationResponse | null>(null);
  const [blockchainVerify, setBlockchainVerify] = useState<BlockchainVerifyResponse | null>(null);
  const [blockchainHistory, setBlockchainHistory] = useState<BlockchainHistoryResponse | null>(null);
  const [ipfsVerify, setIpfsVerify] = useState<IPFSVerifyResponse | null>(null);
  const [ipfsCid, setIpfsCid] = useState<string | null>(document?.current_ipfs_cid || null);
  const [isBlockchainRegistered, setIsBlockchainRegistered] = useState<boolean>(
    document?.integrity_status === 'REGISTERED' || document?.integrity_status === 'VERIFIED_INTEGRITY'
  );
  const [integrityLoading, setIntegrityLoading] = useState(false);
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);
  const [actionErrorMsg, setActionErrorMsg] = useState<string | null>(null);

  const showNotification = (success?: string, error?: string) => {
    if (success) {
      setActionSuccessMsg(success);
      setTimeout(() => setActionSuccessMsg(null), 4000);
    }
    if (error) {
      setActionErrorMsg(error);
      setTimeout(() => setActionErrorMsg(null), 5000);
    }
  };

  const handleRunAutoencoder = async () => {
    if (!documentId) return;
    setIntegrityLoading(true);
    try {
      const res = await predictAdvancedAutoencoder(documentId);
      setAutoencoderPrediction(res);
      showNotification(`PyTorch Autoencoder: prediction = ${res.prediction === 1 ? 'ANOMALOUS' : 'NORMAL'} (MSE: ${res.reconstruction_error.toFixed(5)})`);
    } catch (err: any) {
      showNotification(undefined, err.message || 'Autoencoder scoring failed.');
    } finally {
      setIntegrityLoading(false);
    }
  };

  const handleUploadIPFS = async () => {
    if (!documentId) return;
    setIntegrityLoading(true);
    try {
      const res = await uploadToIPFS(documentId);
      setIpfsCid(res.ipfs_cid);
      showNotification(`Stored on IPFS successfully with CID: ${res.ipfs_cid}`);
    } catch (err: any) {
      showNotification(undefined, err.message || 'IPFS upload failed.');
    } finally {
      setIntegrityLoading(false);
    }
  };

  const handleVerifyIPFS = async () => {
    if (!documentId) return;
    setIntegrityLoading(true);
    try {
      const res = await verifyIPFSContent(documentId);
      setIpfsVerify(res);
      showNotification(`IPFS Content Check: ${res.status} (Hash Match: ${res.hash_match ? 'Yes' : 'No'})`);
    } catch (err: any) {
      showNotification(undefined, err.message || 'IPFS verification failed.');
    } finally {
      setIntegrityLoading(false);
    }
  };

  const handleRegisterBlockchain = async () => {
    if (!documentId) return;
    setIntegrityLoading(true);
    try {
      const res = await registerOnBlockchain(documentId);
      setIsBlockchainRegistered(true);
      showNotification(`Registered on Hyperledger Fabric. Tx ID: ${res.transaction_id.slice(0, 16)}...`);
    } catch (err: any) {
      showNotification(undefined, err.message || 'Blockchain registration failed.');
    } finally {
      setIntegrityLoading(false);
    }
  };

  const handleVerifyBlockchain = async () => {
    if (!documentId) return;
    setIntegrityLoading(true);
    try {
      const res = await verifyOnBlockchain(documentId);
      setBlockchainVerify(res);
      if (res.blockchain_record_found) {
        setIsBlockchainRegistered(true);
      }
      try {
        const hist = await getBlockchainHistory(documentId);
        setBlockchainHistory(hist);
      } catch (e) {
        // history query optional
      }
      showNotification(`Blockchain Fingerprint Check: ${res.integrity_status}`);
    } catch (err: any) {
      showNotification(undefined, err.message || 'Blockchain query failed.');
    } finally {
      setIntegrityLoading(false);
    }
  };

  const handleRegisterIntegrity = async () => {
    if (!documentId) return;
    setIntegrityLoading(true);
    try {
      const res = await registerDocumentIntegrity(documentId);
      setIpfsCid(res.ipfs_cid);
      setIsBlockchainRegistered(true);
      showNotification(`End-to-End Registration Complete. IPFS CID & Fabric Tx registered!`);
    } catch (err: any) {
      showNotification(undefined, err.message || 'Unified registration failed.');
    } finally {
      setIntegrityLoading(false);
    }
  };

  const handleRunUnifiedVerification = async () => {
    if (!documentId) return;
    setIntegrityLoading(true);
    try {
      const res = await verifyDocumentIntegrity(documentId);
      setVerificationResult(res);
      if (res.ipfs.cid) setIpfsCid(res.ipfs.cid);
      if (res.blockchain.record_found) setIsBlockchainRegistered(true);
      showNotification(`Unified Evidence Status: ${res.final_status}`);
    } catch (err: any) {
      showNotification(undefined, err.message || 'Integrity verification failed.');
    } finally {
      setIntegrityLoading(false);
    }
  };

  const loading = docLoading || (analysisLoading && !analysis);

  if (loading) {
    return (
      <main className="container page">
        <div className="skeleton-detail" />
      </main>
    );
  }

  if (docError || !document) {
    return (
      <main className="container page">
        <div className="alert alert-error">
          {docError ?? 'Document not found.'}
          <button className="btn-ghost" onClick={() => navigate('/')}>
            Back to Dashboard
          </button>
        </div>
      </main>
    );
  }

  const fileHash = analysis?.file?.hash || document.file_hash || 'Pending generation';
  const hashAlgorithm = analysis?.file?.hash_algorithm || document.hash_algorithm || 'SHA-256';

  const copyHashToClipboard = () => {
    if (fileHash && fileHash !== 'Pending generation') {
      navigator.clipboard.writeText(fileHash);
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    }
  };

  const copyFeaturesToClipboard = () => {
    if (features) {
      navigator.clipboard.writeText(JSON.stringify(features, null, 2));
      setCopiedFeatures(true);
      setTimeout(() => setCopiedFeatures(false), 2000);
    }
  };

  const basicFields = [
    { icon: <Tag size={15} />, label: 'Document ID', value: document.document_id },
    { icon: <FileText size={15} />, label: 'Filename', value: document.original_filename },
    { icon: <Info size={15} />, label: 'File Type', value: mimeLabel(document.file_type) },
    { icon: <HardDrive size={15} />, label: 'File Size', value: formatBytes(document.file_size) },
    {
      icon: <Calendar size={15} />,
      label: 'Uploaded',
      value: format(new Date(document.upload_timestamp), 'dd MMM yyyy, HH:mm:ss'),
    },
    {
      icon: <Clock size={15} />,
      label: 'Last Updated',
      value: format(new Date(document.updated_at), 'dd MMM yyyy, HH:mm:ss'),
    },
  ];

  const meta = analysis?.metadata || {};
  const structure = analysis?.structure || {};
  const ocr = analysis?.ocr;

  const rawText = analysis?.text?.raw_text || '';
  const cleanedText = analysis?.text?.cleaned_text || '';
  const previewText = cleanedText.length > 500 ? cleanedText.slice(0, 500) + '...' : cleanedText;

  let displayedText = previewText;
  if (textMode === 'full') displayedText = cleanedText;
  if (textMode === 'raw') displayedText = rawText;

  // Grouped Feature Views
  const featMap = features?.features || {};
  const isPreprocessed = (analysis?.processing_status || document.processing_status) === 'completed';

  // Filter features for registry inspector
  const featureEntries = Object.entries(featMap).filter(([key]) => {
    const matchesSearch = key.toLowerCase().includes(featureSearch.toLowerCase());
    if (!matchesSearch) return false;
    if (featureCategory === 'all') return true;
    if (featureCategory === 'file') return key.startsWith('file_') || key.startsWith('filename_');
    if (featureCategory === 'text') return key.includes('word') || key.includes('sentence') || key.includes('ratio') || key.includes('token') || key.includes('character');
    if (featureCategory === 'metadata') return key.startsWith('has_') || key.startsWith('metadata_') || key.includes('length');
    if (featureCategory === 'structural') return key.includes('page') || key.includes('font') || key.includes('table') || key.includes('paragraph') || key.includes('image_');
    if (featureCategory === 'integrity') return key.includes('hash') || key.includes('sha256') || key.includes('present') || key.includes('missing');
    return true;
  });

  return (
    <main className="container page">
      {/* Top action row */}
      <div className="detail-top-nav">
        <button className="btn-back" onClick={() => navigate('/')}>
          <ArrowLeft size={15} /> Back to Dashboard
        </button>
        <div className="detail-actions">
          <button
            className="btn-outline btn-sm"
            onClick={reprocess}
            disabled={isReprocessing}
            title="Re-run document preprocessing pipeline"
          >
            <RefreshCw size={14} className={isReprocessing ? 'spin' : ''} />
            {isReprocessing ? 'Processing…' : 'Reprocess Document'}
          </button>
          {isPreprocessed && (
            <button
              className="btn-primary btn-sm"
              onClick={generateFeatures}
              disabled={isGeneratingFeatures}
              title="Extract standardized ML feature vector"
            >
              <Cpu size={14} className={isGeneratingFeatures ? 'spin' : ''} />
              {isGeneratingFeatures ? 'Extracting Features…' : features ? 'Regenerate ML Features' : 'Extract ML Features'}
            </button>
          )}
        </div>
      </div>

      {/* Basic Information Card */}
      <div className="card">
        <div className="card-header">
          <FileText size={18} />
          <h2 className="card-title">Document Information</h2>
          <div className="badge-group ml-auto">
            <StatusBadge status={document.status} />
            <ProcessingBadge status={analysis?.processing_status || document.processing_status} />
            <ReadinessBadge processingStatus={analysis?.processing_status || document.processing_status} />
          </div>
        </div>

        {analysisError && (
          <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
            <AlertTriangle size={15} />
            <span>{analysisError}</span>
          </div>
        )}

        <div className="detail-grid">
          {basicFields.map((f) => (
            <div className="detail-field" key={f.label}>
              <div className="detail-label">
                {f.icon}
                {f.label}
              </div>
              <div className="detail-value">{f.value}</div>
            </div>
          ))}
        </div>

        {/* SHA-256 Cryptographic Fingerprint */}
        <div className="fingerprint-box">
          <div className="fingerprint-header">
            <span className="fingerprint-label">
              <Hash size={14} /> Cryptographic Document Fingerprint ({hashAlgorithm})
            </span>
            {fileHash && fileHash !== 'Pending generation' && (
              <button
                className="btn-copy"
                onClick={copyHashToClipboard}
                title="Copy SHA-256 hash"
                aria-label="Copy hash"
              >
                {copiedHash ? (
                  <>
                    <Check size={13} color="var(--clr-verified)" /> Copied
                  </>
                ) : (
                  <>
                    <Copy size={13} /> Copy Hash
                  </>
                )}
              </button>
            )}
          </div>
          <code className="fingerprint-hash">{fileHash}</code>
          <p className="fingerprint-hint">
            Calculated directly from the original unmodified file bytes for future blockchain integrity verification.
          </p>
        </div>

        {analysis?.processing_error && (
          <div className="alert alert-error" style={{ marginTop: '1rem' }}>
            <AlertTriangle size={16} />
            <div>
              <strong>Preprocessing Notice:</strong> {analysis.processing_error}
            </div>
          </div>
        )}
      </div>

      {/* Notifications */}
      {actionSuccessMsg && (
        <div className="alert alert-success" style={{ marginBottom: '1rem' }}>
          <Check size={16} />
          <span>{actionSuccessMsg}</span>
        </div>
      )}
      {actionErrorMsg && (
        <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
          <AlertTriangle size={16} />
          <span>{actionErrorMsg}</span>
        </div>
      )}

      {/* ── PHASE 5, 6, 7: INTEGRATED TECHNICAL INTEGRITY WORKFLOW ─── */}
      <VerificationTimeline
        uploaded={true}
        preprocessed={document.processing_status === 'completed'}
        featuresGenerated={!!features}
        mlAnalyzed={!!latestPrediction || !!autoencoderPrediction || !!verificationResult?.ml}
        ipfsStored={!!ipfsCid}
        blockchainRegistered={isBlockchainRegistered}
        integrityVerified={!!verificationResult}
        finalStatus={verificationResult?.final_status || document.integrity_status}
      />

      <UnifiedIntegrityCard
        documentId={document.document_id}
        isRegistered={isBlockchainRegistered}
        verificationResult={verificationResult}
        autoencoderPrediction={autoencoderPrediction}
        onRunUnifiedVerification={handleRunUnifiedVerification}
        onRegisterIntegrity={handleRegisterIntegrity}
        onRunAutoencoder={handleRunAutoencoder}
        loading={integrityLoading}
      />

      <IPFSStoragePanel
        documentId={document.document_id}
        currentCid={ipfsCid}
        verifyData={ipfsVerify}
        onUpload={handleUploadIPFS}
        onVerify={handleVerifyIPFS}
        loading={integrityLoading}
      />

      <BlockchainExplorerPanel
        documentId={document.document_id}
        isRegistered={isBlockchainRegistered}
        verifyData={blockchainVerify}
        historyData={blockchainHistory}
        onRegister={handleRegisterBlockchain}
        onVerify={handleVerifyBlockchain}
        loading={integrityLoading}
      />

      <TechnicalExplanationPanel />

      {/* ── PHASE 4 & 5: MACHINE LEARNING ANOMALY DETECTION SECTION ─────────── */}
      <div className="card ml-anomaly-card">
        <div className="card-header">
          <Cpu size={18} color="var(--clr-accent)" />
          <h2 className="card-title">Machine Learning Anomaly Detection</h2>
          <div className="badge-group ml-auto">
            <span className="type-chip">Model: Isolation Forest</span>
            {latestPrediction && (
              <span className="type-chip">Model Ver: {latestPrediction.model_version}</span>
            )}
            <span className="type-chip">Features Ver: 1.0</span>
          </div>
        </div>

        {predictionError && (
          <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
            <AlertTriangle size={15} />
            <span>{predictionError}</span>
          </div>
        )}

        {/* Forensic & Legal Disclaimer */}
        <div className="anomaly-forensic-disclaimer">
          <Info size={14} className="disclaimer-icon" />
          <span>
            <strong>Forensic Notice:</strong> The ML anomaly score reflects statistical divergence
            from learned document distributions and does not constitute conclusive or legal proof of
            forgery or tampering.
          </span>
        </div>

        {!latestPrediction ? (
          <div className="empty-features-prompt">
            <Sparkles size={32} color="var(--clr-accent)" />
            <p className="empty-prompt-title">Anomaly Detection Not Yet Evaluated</p>
            <p className="empty-prompt-sub">
              {features
                ? 'Standardized Phase 3 feature vectors are available. Run Isolation Forest anomaly detection to identify statistical pattern divergence.'
                : 'Extract Document Features (Phase 3) below before running machine learning anomaly detection.'}
            </p>
            {features && (
              <button
                className="btn-primary"
                onClick={() => runAnomalyDetection()}
                disabled={isPredictingAnomaly}
              >
                <Cpu size={15} className={isPredictingAnomaly ? 'spin' : ''} />
                {isPredictingAnomaly ? 'Evaluating Anomaly Score…' : 'Run Isolation Forest Detection'}
              </button>
            )}
          </div>
        ) : (
          <div className="ml-prediction-results space-y-4">
            {/* Status Verdict Banner */}
            <div
              className={`prediction-status-banner ${
                latestPrediction.prediction === 0 ? 'status-normal' : 'status-anomalous'
              }`}
            >
              <div className="status-banner-header">
                <div className="status-pill">
                  {latestPrediction.prediction === 0
                    ? 'NORMAL (BASELINE ALIGNED)'
                    : 'STATISTICAL ANOMALY DETECTED'}
                </div>
                <button
                  className="btn-secondary btn-sm ml-auto"
                  onClick={() => runAnomalyDetection()}
                  disabled={isPredictingAnomaly}
                >
                  <RefreshCw size={13} className={isPredictingAnomaly ? 'spin' : ''} />
                  {isPredictingAnomaly ? 'Re-evaluating…' : 'Re-run Detection'}
                </button>
              </div>
              <p className="status-banner-desc">
                {latestPrediction.prediction === 0
                  ? 'No statistical anomaly detected by the current model. The document aligns with the learned baseline distribution.'
                  : "The document shows statistical patterns that differ from the model's learned baseline. Further verification is required."}
              </p>
            </div>

            {/* Score & Metrics Summary Grid */}
            <div className="detail-grid">
              <div className="detail-field">
                <div className="detail-label">Normalized Anomaly Score</div>
                <div className="detail-value text-lg font-bold">
                  {(latestPrediction.anomaly_score * 100).toFixed(1)}%
                  <span className="text-xs text-muted" style={{ marginLeft: '6px' }}>
                    ({latestPrediction.anomaly_score.toFixed(4)})
                  </span>
                </div>
                {/* Visual Gauge Bar */}
                <div className="anomaly-meter-track">
                  <div
                    className="anomaly-meter-fill"
                    style={{
                      width: `${Math.min(100, Math.max(0, latestPrediction.anomaly_score * 100))}%`,
                      backgroundColor:
                        latestPrediction.anomaly_score >= latestPrediction.threshold
                          ? 'var(--clr-suspicious)'
                          : 'var(--clr-verified)',
                    }}
                  />
                  <div
                    className="anomaly-threshold-marker"
                    style={{ left: `${latestPrediction.threshold * 100}%` }}
                    title={`Decision Threshold: ${latestPrediction.threshold}`}
                  />
                </div>
                <div className="meter-labels">
                  <span>0.0 (Normal)</span>
                  <span>Threshold ({latestPrediction.threshold.toFixed(2)})</span>
                  <span>1.0 (Outlier)</span>
                </div>
              </div>

              <div className="detail-field">
                <div className="detail-label">Raw Decision Score</div>
                <div className="detail-value font-mono">
                  {latestPrediction.raw_score > 0
                    ? `+${latestPrediction.raw_score.toFixed(4)}`
                    : latestPrediction.raw_score.toFixed(4)}
                </div>
                <div className="text-xs text-muted" style={{ fontSize: '0.75rem', color: 'var(--clr-text-muted)' }}>
                  {latestPrediction.raw_score >= 0 ? 'Inlier region (>= 0.0)' : 'Outlier region (< 0.0)'}
                </div>
              </div>

              <div className="detail-field">
                <div className="detail-label">Model Architecture & Version</div>
                <div className="detail-value">
                  {latestPrediction.model_name}
                  <span className="type-chip" style={{ marginLeft: '6px' }}>
                    v{latestPrediction.model_version}
                  </span>
                </div>
                <div className="text-xs text-muted" style={{ fontSize: '0.75rem', color: 'var(--clr-text-muted)' }}>
                  Evaluated: {new Date(latestPrediction.prediction_timestamp).toLocaleString()}
                </div>
              </div>
            </div>

            {/* Explainable Feature Contributions (Difference from Baseline) */}
            {latestPrediction.contributing_features &&
              latestPrediction.contributing_features.length > 0 && (
                <div className="contributing-features-block">
                  <div className="subblock-title flex items-center justify-between" style={{ marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>
                      Features Differing from Training Distribution:
                    </span>
                    <span className="text-xs text-muted font-normal" style={{ fontSize: '0.75rem', color: 'var(--clr-text-muted)' }}>
                      Ranked by deviation from baseline distribution (does not prove tampering)
                    </span>
                  </div>
                  <div className="feature-table-wrap">
                    <table className="feature-vector-table">
                      <thead>
                        <tr>
                          <th>Feature Identifier</th>
                          <th>Document Value</th>
                          <th>Baseline Mean ± Std</th>
                          <th>Deviation (Z-Score)</th>
                          <th>Description</th>
                        </tr>
                      </thead>
                      <tbody>
                        {latestPrediction.contributing_features.map((cf) => (
                          <tr key={cf.feature_name}>
                            <td className="name-cell font-mono text-xs">
                              <code>{cf.feature_name}</code>
                            </td>
                            <td className="val-cell font-mono font-semibold">
                              {cf.document_value}
                            </td>
                            <td className="val-cell font-mono text-xs" style={{ color: 'var(--clr-text-muted)' }}>
                              {cf.baseline_mean.toFixed(2)} ± {cf.baseline_std.toFixed(2)}
                            </td>
                            <td className="val-cell">
                              <span className="deviation-chip">
                                {cf.deviation_score.toFixed(2)}σ
                              </span>
                            </td>
                            <td className="text-xs" style={{ color: 'var(--clr-text-muted)' }}>
                              {cf.description || 'Registered feature definition'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
          </div>
        )}
      </div>

      {/* ── PHASE 3: DOCUMENT FEATURES SECTION ───────────────────────────── */}
      <div className="card feature-section-card">
        <div className="card-header">
          <Cpu size={18} color="var(--clr-accent)" />
          <h2 className="card-title">Document Features (ML-Ready Representation)</h2>
          <div className="badge-group ml-auto">
            <span className="type-chip">Feature Version: 1.0</span>
            <span className="type-chip">Pipeline: 1.0.0</span>
            {features && (
              <span className="badge badge-verified">
                {features.feature_count} Features Extracted
              </span>
            )}
          </div>
        </div>

        {featuresError && (
          <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
            <AlertTriangle size={15} />
            <span>{featuresError}</span>
          </div>
        )}

        {!features ? (
          <div className="empty-features-prompt">
            <Sparkles size={32} color="var(--clr-accent)" />
            <p className="empty-prompt-title">Standardized Features Not Yet Extracted</p>
            <p className="empty-prompt-sub">
              {isPreprocessed
                ? 'Document preprocessing is complete. Click below to engineer the deterministic feature vector for downstream machine learning.'
                : 'Complete document preprocessing before engineering features.'}
            </p>
            {isPreprocessed && (
              <button
                className="btn-primary"
                onClick={generateFeatures}
                disabled={isGeneratingFeatures}
              >
                <Cpu size={15} className={isGeneratingFeatures ? 'spin' : ''} />
                {isGeneratingFeatures ? 'Generating Features…' : 'Generate ML Feature Vector'}
              </button>
            )}
          </div>
        ) : (
          <div className="feature-content-wrapper">
            {/* Grouped Feature Overview Cards */}
            <div className="feature-category-grid">
              {/* 1. File Features */}
              <div className="feature-category-card">
                <div className="category-header">
                  <HardDrive size={15} />
                  <span>File-Level Features</span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">Size (Bytes / KB):</span>
                  <span className="metric-val">{featMap['file_size_bytes']} B ({featMap['file_size_kb']} KB)</span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">Extension Code:</span>
                  <span className="metric-val">{featMap['file_extension_code']}</span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">MIME Code:</span>
                  <span className="metric-val">{featMap['mime_type_code']}</span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">Filename Length / Digits:</span>
                  <span className="metric-val">{featMap['filename_length']} chars / {featMap['filename_digit_count']} digits</span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">UUID Pattern in Filename:</span>
                  <span className="metric-val">{featMap['filename_has_uuid_pattern'] ? 'Yes' : 'No'}</span>
                </div>
              </div>

              {/* 2. Text Features */}
              <div className="feature-category-card">
                <div className="category-header">
                  <FileText size={15} />
                  <span>Text & Lexical Features</span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">Words / Characters:</span>
                  <span className="metric-val">{featMap['word_count']} / {featMap['character_count']}</span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">Sentences / Paragraphs:</span>
                  <span className="metric-val">{featMap['sentence_count']} / {featMap['paragraph_count']}</span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">Vocabulary Richness:</span>
                  <span className="metric-val">{featMap['vocabulary_richness']}</span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">Avg Word / Sentence Length:</span>
                  <span className="metric-val">{featMap['average_word_length']} / {featMap['average_sentence_length']}</span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">Numeric Ratio / Tokens:</span>
                  <span className="metric-val">{featMap['numeric_ratio']} ({featMap['numeric_token_count']})</span>
                </div>
              </div>

              {/* 3. Metadata Features */}
              <div className="feature-category-card">
                <div className="category-header">
                  <Database size={15} />
                  <span>Metadata Characteristics</span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">Completeness Ratio:</span>
                  <span className="metric-val">{featMap['metadata_completeness_ratio']} ({featMap['metadata_field_count']}/9)</span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">Author / Title Present:</span>
                  <span className="metric-val">
                    {featMap['has_author'] ? '✓' : '✗'} / {featMap['has_title'] ? '✓' : '✗'}
                  </span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">Creator / Producer Present:</span>
                  <span className="metric-val">
                    {featMap['has_creator'] ? '✓' : '✗'} / {featMap['has_producer'] ? '✓' : '✗'}
                  </span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">Author == Last Modified:</span>
                  <span className="metric-val">{featMap['author_equals_last_modified_by'] ? 'Yes' : 'No'}</span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">Modified After Created:</span>
                  <span className="metric-val">{featMap['metadata_modified_after_created'] ? 'Yes' : 'No'}</span>
                </div>
              </div>

              {/* 4. Structural Features */}
              <div className="feature-category-card">
                <div className="category-header">
                  <Layers size={15} />
                  <span>Structural Forensics</span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">Pages / Images / Links:</span>
                  <span className="metric-val">{featMap['page_count']} / {featMap['image_count']} / {featMap['link_count']}</span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">Unique Fonts / Name Count:</span>
                  <span className="metric-val">{featMap['unique_font_count']} / {featMap['font_name_count']}</span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">Font Sizes (Min / Max / Avg):</span>
                  <span className="metric-val">{featMap['minimum_font_size']} / {featMap['maximum_font_size']} / {featMap['average_font_size']} pt</span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">Text Page Ratio:</span>
                  <span className="metric-val">{featMap['text_page_ratio']}</span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">Dimension Consistency:</span>
                  <span className="metric-val">{featMap['page_dimension_consistency_ratio']}</span>
                </div>
              </div>

              {/* 5. Integrity & Missingness */}
              <div className="feature-category-card">
                <div className="category-header">
                  <ShieldCheck size={15} />
                  <span>Integrity & Quality Signals</span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">SHA-256 Present:</span>
                  <span className="metric-val">{featMap['sha256_present'] ? 'Yes (Verified)' : 'No'}</span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">Hash Algorithm Code:</span>
                  <span className="metric-val">{featMap['hash_algorithm_code']}</span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">Hash Length:</span>
                  <span className="metric-val">{featMap['hash_length']} chars</span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">Cross-Source Consistency:</span>
                  <span className="metric-val">Par: {featMap['paragraph_count_consistency']} | Date: {featMap['metadata_date_consistency'] ? 'Yes' : 'No'}</span>
                </div>
                <div className="category-metric-row">
                  <span className="metric-label">Missingness Flags:</span>
                  <span className="metric-val">Text: {featMap['text_missing'] ? '1' : '0'} | Meta: {featMap['metadata_missing'] ? '1' : '0'}</span>
                </div>
              </div>
            </div>

            {/* Feature Vector Inspector Table */}
            <div className="vector-inspector">
              <div className="inspector-toolbar">
                <div className="inspector-title">
                  <BarChart3 size={15} />
                  <span>Ordered Feature Vector Catalog ({featureEntries.length} items)</span>
                </div>
                <div className="inspector-actions ml-auto">
                  <input
                    type="text"
                    placeholder="Search feature name…"
                    className="feature-search-input"
                    value={featureSearch}
                    onChange={(e) => setFeatureSearch(e.target.value)}
                  />
                  <button
                    className="btn-copy"
                    onClick={copyFeaturesToClipboard}
                    title="Copy complete feature vector as JSON"
                  >
                    {copiedFeatures ? (
                      <>
                        <Check size={13} color="var(--clr-verified)" /> Copied
                      </>
                    ) : (
                      <>
                        <Copy size={13} /> Copy JSON
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Category Filter Pills */}
              <div className="text-mode-pills" style={{ marginBottom: '0.75rem' }}>
                {['all', 'file', 'text', 'metadata', 'structural', 'integrity'].map((cat) => (
                  <button
                    key={cat}
                    className={`pill-btn ${featureCategory === cat ? 'active' : ''}`}
                    onClick={() => setFeatureCategory(cat)}
                  >
                    {cat.charAt(0).toUpperCase() + cat.slice(1)}
                  </button>
                ))}
              </div>

              {/* Table */}
              <div className="feature-table-wrap">
                <table className="feature-vector-table">
                  <thead>
                    <tr>
                      <th style={{ width: '45px' }}>#</th>
                      <th>Feature Identifier</th>
                      <th>Value</th>
                      <th>Type</th>
                    </tr>
                  </thead>
                  <tbody>
                    {featureEntries.map(([fKey, fVal], idx) => (
                      <tr key={fKey}>
                        <td className="idx-cell">{idx + 1}</td>
                        <td className="name-cell">
                          <code>{fKey}</code>
                        </td>
                        <td className="val-cell">
                          <span className={typeof fVal === 'boolean' ? (fVal ? 'bool-true' : 'bool-false') : 'num-val'}>
                            {fVal === true ? 'true' : fVal === false ? 'false' : String(fVal)}
                          </span>
                        </td>
                        <td className="type-cell">
                          <span className="type-chip">{typeof fVal}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Extracted Text & Normalization Section */}
      <div className="card">
        <div className="card-header">
          <Eye size={18} />
          <h2 className="card-title">Extracted & Standardized Text</h2>
          <div className="text-mode-pills ml-auto">
            <button
              className={`pill-btn ${textMode === 'preview' ? 'active' : ''}`}
              onClick={() => setTextMode('preview')}
            >
              Preview
            </button>
            <button
              className={`pill-btn ${textMode === 'full' ? 'active' : ''}`}
              onClick={() => setTextMode('full')}
            >
              Full Cleaned
            </button>
            <button
              className={`pill-btn ${textMode === 'raw' ? 'active' : ''}`}
              onClick={() => setTextMode('raw')}
            >
              Raw Extracted
            </button>
          </div>
        </div>

        {/* Statistics Bar */}
        <div className="text-stats-bar">
          <div className="stat-pill">
            <span className="stat-label">Words</span>
            <span className="stat-val">{analysis?.text?.word_count ?? 0}</span>
          </div>
          <div className="stat-pill">
            <span className="stat-label">Characters</span>
            <span className="stat-val">{analysis?.text?.character_count ?? 0}</span>
          </div>
          <div className="stat-pill">
            <span className="stat-label">Paragraphs</span>
            <span className="stat-val">{analysis?.text?.paragraph_count ?? 0}</span>
          </div>
          <div className="stat-pill">
            <span className="stat-label">Cleaning Status</span>
            <span className="stat-val stat-val-ok">Normalized (NFKC)</span>
          </div>
        </div>

        {/* Text Container */}
        <div className="text-display-box">
          {displayedText ? (
            <pre className="text-content">{displayedText}</pre>
          ) : (
            <p className="text-empty-hint">
              No textual content extracted from this document or file contains only non-OCR graphics.
            </p>
          )}
        </div>
      </div>

      {/* Metadata Section */}
      <div className="card">
        <div className="card-header">
          <Database size={18} />
          <h2 className="card-title">Standardized Document Metadata</h2>
        </div>

        <div className="metadata-table-wrap">
          <table className="metadata-table">
            <tbody>
              <tr>
                <td className="meta-key">Title</td>
                <td className="meta-val">{meta.title || <span className="muted">Not specified</span>}</td>
              </tr>
              <tr>
                <td className="meta-key">Author / Signatory</td>
                <td className="meta-val">{meta.author || <span className="muted">Not specified</span>}</td>
              </tr>
              <tr>
                <td className="meta-key">Subject / Topic</td>
                <td className="meta-val">{meta.subject || <span className="muted">Not specified</span>}</td>
              </tr>
              <tr>
                <td className="meta-key">Creator / Software</td>
                <td className="meta-val">{meta.creator || <span className="muted">Not specified</span>}</td>
              </tr>
              <tr>
                <td className="meta-key">Producer</td>
                <td className="meta-val">{meta.producer || <span className="muted">Not specified</span>}</td>
              </tr>
              <tr>
                <td className="meta-key">Keywords</td>
                <td className="meta-val">{meta.keywords || <span className="muted">Not specified</span>}</td>
              </tr>
              <tr>
                <td className="meta-key">Creation Date</td>
                <td className="meta-val">
                  {meta.created_at ? format(new Date(meta.created_at), 'dd MMM yyyy, HH:mm:ss (x)') : <span className="muted">Not specified</span>}
                </td>
              </tr>
              <tr>
                <td className="meta-key">Modification Date</td>
                <td className="meta-val">
                  {meta.modified_at ? format(new Date(meta.modified_at), 'dd MMM yyyy, HH:mm:ss (x)') : <span className="muted">Not specified</span>}
                </td>
              </tr>
              {meta.last_modified_by && (
                <tr>
                  <td className="meta-key">Last Modified By</td>
                  <td className="meta-val">{meta.last_modified_by}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Structural Analysis Section */}
      <div className="card">
        <div className="card-header">
          <Layers size={18} />
          <h2 className="card-title">Structural & Forensic Analysis</h2>
          {structure.format && <span className="type-chip ml-auto">{structure.format}</span>}
        </div>

        <div className="detail-grid">
          {structure.page_count !== undefined && (
            <div className="detail-field">
              <div className="detail-label">Page Count</div>
              <div className="detail-value">{structure.page_count}</div>
            </div>
          )}
          {structure.paragraph_count !== undefined && (
            <div className="detail-field">
              <div className="detail-label">Paragraph Count</div>
              <div className="detail-value">{structure.paragraph_count}</div>
            </div>
          )}
          {structure.table_count !== undefined && (
            <div className="detail-field">
              <div className="detail-label">Table Count</div>
              <div className="detail-value">{structure.table_count}</div>
            </div>
          )}
          {structure.total_images !== undefined && (
            <div className="detail-field">
              <div className="detail-label">Embedded Images</div>
              <div className="detail-value">{structure.total_images}</div>
            </div>
          )}
          {structure.image_count !== undefined && structure.total_images === undefined && (
            <div className="detail-field">
              <div className="detail-label">Image Count</div>
              <div className="detail-value">{structure.image_count}</div>
            </div>
          )}
          {structure.total_links !== undefined && (
            <div className="detail-field">
              <div className="detail-label">Embedded Links</div>
              <div className="detail-value">{structure.total_links}</div>
            </div>
          )}
          {structure.font_count !== undefined && (
            <div className="detail-field">
              <div className="detail-label">Fonts Detected</div>
              <div className="detail-value">{structure.font_count}</div>
            </div>
          )}
          {structure.width !== undefined && (
            <div className="detail-field">
              <div className="detail-label">Image Resolution</div>
              <div className="detail-value">{structure.width} × {structure.height} px (Ratio: {structure.aspect_ratio})</div>
            </div>
          )}
          {structure.color_mode && (
            <div className="detail-field">
              <div className="detail-label">Color Space</div>
              <div className="detail-value">{structure.color_mode}</div>
            </div>
          )}
          {structure.has_exif !== undefined && (
            <div className="detail-field">
              <div className="detail-label">EXIF Metadata</div>
              <div className="detail-value">{structure.has_exif ? 'Present' : 'None detected'}</div>
            </div>
          )}
        </div>

        {/* Font List if detected */}
        {structure.font_names && structure.font_names.length > 0 && (
          <div className="structure-subblock">
            <span className="subblock-title">Identified Font Families:</span>
            <div className="tag-list">
              {structure.font_names.map((font: string) => (
                <span className="tag-chip" key={font}>
                  {font}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Headings if DOCX */}
        {structure.headings && structure.headings.length > 0 && (
          <div className="structure-subblock">
            <span className="subblock-title">Document Headings Outline:</span>
            <ul className="outline-list">
              {structure.headings.map((h: string, idx: number) => (
                <li key={idx}>{h}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Structural anomalies like image-only pages or unusually low text */}
        {((structure.pages_with_low_text?.length ?? 0) > 0 || (structure.pages_with_only_images?.length ?? 0) > 0) && (
          <div className="anomaly-notice-box">
            <AlertTriangle size={15} color="var(--clr-processing)" />
            <div>
              {(structure.pages_with_low_text?.length ?? 0) > 0 && (
                <p>
                  <strong>Notice:</strong> Pages with sparse text detected:{' '}
                  {structure.pages_with_low_text?.join(', ')}.
                </p>
              )}
              {(structure.pages_with_only_images?.length ?? 0) > 0 && (
                <p>
                  <strong>Notice:</strong> Pages containing image-only content (no vector text):{' '}
                  {structure.pages_with_only_images?.join(', ')}.
                </p>
              )}
            </div>
          </div>
        )}
      </div>

      {/* OCR Status Section */}
      <div className="card">
        <div className="card-header">
          <Scan size={18} />
          <h2 className="card-title">Optical Character Recognition (OCR)</h2>
          <span className={`badge ${ocr?.used ? 'badge-verified' : 'badge-uploaded'} ml-auto`}>
            {ocr?.status ? ocr.status.toUpperCase() : 'NOT REQUIRED'}
          </span>
        </div>

        <div className="ocr-details">
          <div className="detail-grid">
            <div className="detail-field">
              <div className="detail-label">OCR Applied</div>
              <div className="detail-value">{ocr?.used ? 'Yes' : 'No'}</div>
            </div>
            <div className="detail-field">
              <div className="detail-label">OCR Status</div>
              <div className="detail-value">{ocr?.status || 'not_required'}</div>
            </div>
          </div>

          {ocr?.error_message && (
            <div className="alert alert-info" style={{ marginTop: '0.75rem' }}>
              <Info size={15} />
              <span>{ocr.error_message}</span>
            </div>
          )}

          {!ocr?.used && !ocr?.error_message && (
            <p className="ocr-hint">
              OCR is automatically invoked for scanned and bitmap image documents when Tesseract engine is present.
            </p>
          )}
        </div>
      </div>
    </main>
  );
}
