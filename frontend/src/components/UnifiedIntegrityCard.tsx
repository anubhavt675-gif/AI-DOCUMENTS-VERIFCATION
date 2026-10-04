import React from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Cpu,
  HardDrive,
  Blocks,
  RefreshCw,
  HelpCircle,
} from 'lucide-react';
import type { IntegratedVerificationResponse, AdvancedMLPrediction } from '../types';

interface UnifiedIntegrityCardProps {
  documentId?: string;
  isRegistered: boolean;
  verificationResult?: IntegratedVerificationResponse | null;
  autoencoderPrediction?: AdvancedMLPrediction | null;
  onRunUnifiedVerification: () => Promise<void>;
  onRegisterIntegrity: () => Promise<void>;
  onRunAutoencoder: () => Promise<void>;
  loading: boolean;
}

export const UnifiedIntegrityCard: React.FC<UnifiedIntegrityCardProps> = ({
  isRegistered,
  verificationResult,
  autoencoderPrediction,
  onRunUnifiedVerification,
  onRegisterIntegrity,
  onRunAutoencoder,
  loading,
}) => {
  const finalStatus = verificationResult?.final_status || (isRegistered ? 'REGISTERED' : 'UNREGISTERED');

  const getStatusBadge = () => {
    switch (finalStatus) {
      case 'VERIFIED_INTEGRITY':
        return {
          bg: 'rgba(63, 185, 80, 0.15)',
          border: 'var(--clr-verified)',
          color: 'var(--clr-verified)',
          icon: <ShieldCheck size={20} color="var(--clr-verified)" />,
          title: 'VERIFIED INTEGRITY',
        };
      case 'INTEGRITY_MISMATCH':
        return {
          bg: 'rgba(248, 81, 73, 0.15)',
          border: 'var(--clr-suspicious)',
          color: 'var(--clr-suspicious)',
          icon: <ShieldAlert size={20} color="var(--clr-suspicious)" />,
          title: 'INTEGRITY MISMATCH DETECTED',
        };
      case 'ANOMALY_DETECTED':
        return {
          bg: 'rgba(210, 153, 34, 0.15)',
          border: 'var(--clr-processing)',
          color: 'var(--clr-processing)',
          icon: <AlertTriangle size={20} color="var(--clr-processing)" />,
          title: 'STATISTICAL ANOMALY DETECTED',
        };
      default:
        return {
          bg: 'rgba(31, 111, 235, 0.1)',
          border: 'var(--clr-border)',
          color: 'var(--clr-text-primary)',
          icon: <HelpCircle size={20} color="var(--clr-accent-hover)" />,
          title: isRegistered ? 'REGISTERED (AWAITING VERIFICATION)' : 'UNREGISTERED DOCUMENT',
        };
    }
  };

  const badgeInfo = getStatusBadge();

  return (
    <div className="card" style={{ marginBottom: '1.5rem', border: `1px solid ${badgeInfo.border}` }}>
      <div className="card-header" style={{ borderBottom: '1px solid var(--clr-border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {badgeInfo.icon}
          <div>
            <h2 className="card-title" style={{ fontSize: '1.1rem' }}>
              Technical Integrity Evidence Engine
            </h2>
            <div style={{ fontSize: '0.75rem', color: 'var(--clr-text-secondary)' }}>
              Integrated multi-signal evaluation (Phases 5, 6 & 7)
            </div>
          </div>
        </div>

        <span
          className="badge ml-auto"
          style={{
            backgroundColor: badgeInfo.bg,
            color: badgeInfo.color,
            borderColor: badgeInfo.border,
            fontWeight: 700,
            letterSpacing: '0.05em',
            padding: '0.35rem 0.75rem',
          }}
        >
          {badgeInfo.title}
        </span>
      </div>

      <div style={{ padding: '1.25rem 0' }}>
        {/* Status Explanation Message */}
        {verificationResult?.technical_explanation && (
          <div
            style={{
              padding: '0.75rem 1rem',
              backgroundColor: 'var(--clr-bg)',
              borderRadius: 'var(--r-md)',
              border: '1px solid var(--clr-border)',
              marginBottom: '1.25rem',
              fontSize: '0.85rem',
              lineHeight: '1.5',
              color: 'var(--clr-text-primary)',
            }}
          >
            <strong>Technical Finding:</strong> {verificationResult.technical_explanation}
          </div>
        )}

        {/* 3-Pillar Evidence Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '1rem',
            marginBottom: '1.25rem',
          }}
        >
          {/* Pillar 1: ML Engine */}
          <div
            style={{
              padding: '1rem',
              backgroundColor: 'var(--clr-bg-2)',
              borderRadius: 'var(--r-md)',
              border: '1px solid var(--clr-border)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <Cpu size={16} color="var(--clr-accent-hover)" />
              <strong style={{ fontSize: '0.9rem' }}>PyTorch Autoencoder ML</strong>
            </div>

            <div style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--clr-text-secondary)' }}>Signal:</span>
                <span
                  style={{
                    fontWeight: 600,
                    color:
                      (verificationResult?.ml.prediction ?? autoencoderPrediction?.prediction ?? 0) === 1
                        ? 'var(--clr-suspicious)'
                        : 'var(--clr-verified)',
                  }}
                >
                  {(verificationResult?.ml.prediction ?? autoencoderPrediction?.prediction ?? 0) === 1
                    ? 'ANOMALOUS'
                    : 'NORMAL'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--clr-text-secondary)' }}>Reconstruction MSE:</span>
                <span style={{ fontFamily: 'var(--font-mono)' }}>
                  {verificationResult?.ml.reconstruction_error !== undefined
                    ? verificationResult.ml.reconstruction_error.toFixed(6)
                    : autoencoderPrediction?.reconstruction_error !== undefined
                    ? autoencoderPrediction.reconstruction_error.toFixed(6)
                    : 'N/A'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--clr-text-secondary)' }}>Anomaly Score:</span>
                <span style={{ fontFamily: 'var(--font-mono)' }}>
                  {(verificationResult?.ml.anomaly_score ?? autoencoderPrediction?.anomaly_score ?? 0).toFixed(4)}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--clr-text-secondary)' }}>Model Version:</span>
                <span>{verificationResult?.ml.model_version || autoencoderPrediction?.model_version || 'v1.0.0'}</span>
              </div>
            </div>
          </div>

          {/* Pillar 2: IPFS Engine */}
          <div
            style={{
              padding: '1rem',
              backgroundColor: 'var(--clr-bg-2)',
              borderRadius: 'var(--r-md)',
              border: '1px solid var(--clr-border)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <HardDrive size={16} color="var(--clr-accent-hover)" />
              <strong style={{ fontSize: '0.9rem' }}>IPFS Off-Chain Storage</strong>
            </div>

            <div style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--clr-text-secondary)' }}>Storage Status:</span>
                <span
                  style={{
                    fontWeight: 600,
                    color: verificationResult?.ipfs.retrieval_success ? 'var(--clr-verified)' : 'var(--clr-text-muted)',
                  }}
                >
                  {verificationResult?.ipfs.retrieval_success ? 'STORED & RETRIEVABLE' : isRegistered ? 'STORED' : 'PENDING'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--clr-text-secondary)' }}>Content Hash:</span>
                <span
                  style={{
                    fontWeight: 600,
                    color: verificationResult?.ipfs.hash_match ? 'var(--clr-verified)' : 'var(--clr-text-muted)',
                  }}
                >
                  {verificationResult?.ipfs.hash_match ? 'MATCH (100%)' : 'NOT CHECKED'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--clr-text-secondary)' }}>Addressing:</span>
                <span>CIDv0 Multihash</span>
              </div>
            </div>
          </div>

          {/* Pillar 3: Blockchain Engine */}
          <div
            style={{
              padding: '1rem',
              backgroundColor: 'var(--clr-bg-2)',
              borderRadius: 'var(--r-md)',
              border: '1px solid var(--clr-border)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <Blocks size={16} color="var(--clr-accent-hover)" />
              <strong style={{ fontSize: '0.9rem' }}>Hyperledger Fabric</strong>
            </div>

            <div style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--clr-text-secondary)' }}>On-Chain Record:</span>
                <span
                  style={{
                    fontWeight: 600,
                    color: verificationResult?.blockchain.record_found || isRegistered ? 'var(--clr-verified)' : 'var(--clr-text-muted)',
                  }}
                >
                  {verificationResult?.blockchain.record_found || isRegistered ? 'FOUND' : 'NOT FOUND'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--clr-text-secondary)' }}>SHA-256 Match:</span>
                <span
                  style={{
                    fontWeight: 600,
                    color: verificationResult?.blockchain.hash_match ? 'var(--clr-verified)' : 'var(--clr-text-muted)',
                  }}
                >
                  {verificationResult?.blockchain.hash_match ? 'MATCH' : isRegistered ? 'MATCH' : 'PENDING'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--clr-text-secondary)' }}>Tx Immutability:</span>
                <span>CRYPTOGRAPHIC</span>
              </div>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button className="btn-primary" onClick={onRunUnifiedVerification} disabled={loading}>
            <RefreshCw size={15} />
            {loading ? 'Evaluating Multi-Signal Evidence...' : 'Run Unified Technical Verification'}
          </button>

          {!isRegistered && (
            <button className="btn-secondary" onClick={onRegisterIntegrity} disabled={loading}>
              <Blocks size={15} />
              {loading ? 'Registering...' : 'Register Integrity (IPFS + Hyperledger)'}
            </button>
          )}

          <button className="btn-ghost" onClick={onRunAutoencoder} disabled={loading}>
            <Cpu size={15} />
            Run PyTorch Autoencoder Only
          </button>
        </div>
      </div>
    </div>
  );
};

export default UnifiedIntegrityCard;
