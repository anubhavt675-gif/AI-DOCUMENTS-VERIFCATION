import React from 'react';
import {
  UploadCloud,
  FileSearch,
  Binary,
  Cpu,
  HardDrive,
  Blocks,
  ShieldCheck,
  AlertCircle,
} from 'lucide-react';

interface VerificationTimelineProps {
  uploaded: boolean;
  preprocessed: boolean;
  featuresGenerated: boolean;
  mlAnalyzed: boolean;
  ipfsStored: boolean;
  blockchainRegistered: boolean;
  integrityVerified: boolean;
  finalStatus?: string | null;
}

export const VerificationTimeline: React.FC<VerificationTimelineProps> = ({
  uploaded,
  preprocessed,
  featuresGenerated,
  mlAnalyzed,
  ipfsStored,
  blockchainRegistered,
  integrityVerified,
  finalStatus,
}) => {
  const steps = [
    {
      id: 'upload',
      label: 'Document Uploaded',
      completed: uploaded,
      icon: <UploadCloud size={16} />,
      desc: 'Original file archived',
    },
    {
      id: 'preprocess',
      label: 'Preprocessed',
      completed: preprocessed,
      icon: <FileSearch size={16} />,
      desc: 'Text & metadata extracted',
    },
    {
      id: 'features',
      label: 'Features Generated',
      completed: featuresGenerated,
      icon: <Binary size={16} />,
      desc: 'Standardized ML vectors',
    },
    {
      id: 'ml',
      label: 'ML Analyzed',
      completed: mlAnalyzed,
      icon: <Cpu size={16} />,
      desc: 'Autoencoder & Isolation Forest',
    },
    {
      id: 'ipfs',
      label: 'IPFS Storage',
      completed: ipfsStored,
      icon: <HardDrive size={16} />,
      desc: 'Content-addressed CID',
    },
    {
      id: 'blockchain',
      label: 'Blockchain Registered',
      completed: blockchainRegistered,
      icon: <Blocks size={16} />,
      desc: 'Immutable Fabric fingerprint',
    },
    {
      id: 'verified',
      label: 'Integrity Verified',
      completed: integrityVerified,
      icon: finalStatus === 'INTEGRITY_MISMATCH' ? <AlertCircle size={16} /> : <ShieldCheck size={16} />,
      desc: finalStatus || 'Awaiting verification',
    },
  ];

  return (
    <div className="card" style={{ marginBottom: '1.5rem' }}>
      <div className="card-header">
        <Blocks size={18} />
        <h2 className="card-title">Verification Lifecycle Timeline</h2>
        {finalStatus && (
          <span
            className={`badge ${
              finalStatus === 'VERIFIED_INTEGRITY'
                ? 'badge-verified'
                : finalStatus === 'INTEGRITY_MISMATCH'
                ? 'badge-failed'
                : finalStatus === 'ANOMALY_DETECTED'
                ? 'badge-suspicious'
                : 'badge-uploaded'
            } ml-auto`}
          >
            {finalStatus.replace(/_/g, ' ')}
          </span>
        )}
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          gap: '1rem',
          padding: '1rem 0.5rem 0.5rem',
        }}
      >
        {steps.map((step, idx) => (
          <div
            key={step.id}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center',
              position: 'relative',
              opacity: step.completed ? 1 : 0.45,
            }}
          >
            <div
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: step.completed
                  ? step.id === 'verified' && finalStatus === 'INTEGRITY_MISMATCH'
                    ? 'rgba(248, 81, 73, 0.2)'
                    : 'rgba(63, 185, 80, 0.2)'
                  : 'var(--clr-surface)',
                border: `1px solid ${
                  step.completed
                    ? step.id === 'verified' && finalStatus === 'INTEGRITY_MISMATCH'
                      ? 'var(--clr-suspicious)'
                      : 'var(--clr-verified)'
                    : 'var(--clr-border)'
                }`,
                color: step.completed
                  ? step.id === 'verified' && finalStatus === 'INTEGRITY_MISMATCH'
                    ? 'var(--clr-suspicious)'
                    : 'var(--clr-verified)'
                  : 'var(--clr-text-muted)',
                marginBottom: '0.5rem',
              }}
            >
              {step.icon}
            </div>
            <div
              style={{
                fontSize: '0.8rem',
                fontWeight: 600,
                color: step.completed ? 'var(--clr-text-primary)' : 'var(--clr-text-muted)',
              }}
            >
              {idx + 1}. {step.label}
            </div>
            <div
              style={{
                fontSize: '0.72rem',
                color: 'var(--clr-text-secondary)',
                marginTop: '0.2rem',
              }}
            >
              {step.desc}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default VerificationTimeline;
