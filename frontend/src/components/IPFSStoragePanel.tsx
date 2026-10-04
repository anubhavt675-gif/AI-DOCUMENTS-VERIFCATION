import React, { useState } from 'react';
import { HardDrive, Copy, Check, Download, RefreshCw } from 'lucide-react';
import type { IPFSVerifyResponse } from '../types';
import { getIPFSContentUrl } from '../services/api';

interface IPFSStoragePanelProps {
  documentId: string;
  currentCid?: string | null;
  verifyData?: IPFSVerifyResponse | null;
  onUpload: () => Promise<void>;
  onVerify: () => Promise<void>;
  loading: boolean;
}

export const IPFSStoragePanel: React.FC<IPFSStoragePanelProps> = ({
  documentId,
  currentCid,
  verifyData,
  onUpload,
  onVerify,
  loading,
}) => {
  const [copiedCid, setCopiedCid] = useState(false);
  const cid = currentCid || verifyData?.ipfs_cid || null;
  const status = verifyData?.status || (cid ? 'STORED' : 'NOT_STORED');

  const copyCid = () => {
    if (cid) {
      navigator.clipboard.writeText(cid);
      setCopiedCid(true);
      setTimeout(() => setCopiedCid(false), 2000);
    }
  };

  return (
    <div className="card" style={{ marginBottom: '1.5rem' }}>
      <div className="card-header">
        <HardDrive size={18} />
        <h2 className="card-title">InterPlanetary File System (IPFS) Off-Chain Storage</h2>
        <span
          className={`badge ${
            status === 'VERIFIED' || status === 'STORED'
              ? 'badge-verified'
              : status === 'HASH_MISMATCH' || status === 'RETRIEVAL_FAILED'
              ? 'badge-failed'
              : 'badge-uploaded'
          } ml-auto`}
        >
          {status.replace(/_/g, ' ')}
        </span>
      </div>

      <div style={{ padding: '1rem 0' }}>
        <div className="detail-grid">
          <div className="detail-field">
            <div className="detail-label">Storage Architecture</div>
            <div className="detail-value">Decentralized Content-Addressed Storage (UnixFS)</div>
          </div>
          <div className="detail-field">
            <div className="detail-label">Addressing Standard</div>
            <div className="detail-value">CIDv0 (base58btc SHA2-256 multihash)</div>
          </div>
          <div className="detail-field">
            <div className="detail-label">Storage Status</div>
            <div className="detail-value">
              {cid ? (
                <span style={{ color: 'var(--clr-verified)', fontWeight: 600 }}>
                  ✓ Stored Off-Chain
                </span>
              ) : (
                <span style={{ color: 'var(--clr-text-muted)' }}>Not yet uploaded to IPFS</span>
              )}
            </div>
          </div>
          <div className="detail-field">
            <div className="detail-label">Content Verification</div>
            <div className="detail-value">
              {verifyData ? (
                verifyData.hash_match ? (
                  <span style={{ color: 'var(--clr-verified)', fontWeight: 600 }}>
                    ✓ Hash Verified (100% Match)
                  </span>
                ) : (
                  <span style={{ color: 'var(--clr-suspicious)', fontWeight: 600 }}>
                    ⚠ Hash Mismatch Detected
                  </span>
                )
              ) : (
                <span style={{ color: 'var(--clr-text-muted)' }}>Pending check</span>
              )}
            </div>
          </div>
        </div>

        {cid && (
          <div style={{ marginTop: '1rem' }}>
            <div className="detail-label">Content Identifier (CID)</div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                backgroundColor: 'var(--clr-bg)',
                padding: '0.5rem 0.75rem',
                borderRadius: 'var(--r-md)',
                marginTop: '0.3rem',
                border: '1px solid var(--clr-border)',
              }}
            >
              <code
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.85rem',
                  wordBreak: 'break-all',
                  color: 'var(--clr-verified)',
                  flex: 1,
                }}
              >
                {cid}
              </code>
              <button
                className="btn-ghost"
                onClick={copyCid}
                title="Copy IPFS CID"
                style={{ padding: '0.2rem 0.5rem' }}
              >
                {copiedCid ? <Check size={14} color="var(--clr-verified)" /> : <Copy size={14} />}
              </button>
              <a
                href={getIPFSContentUrl(documentId)}
                target="_blank"
                rel="noreferrer"
                className="btn-ghost"
                title="View document from IPFS"
                style={{ padding: '0.2rem 0.5rem', display: 'flex', alignItems: 'center' }}
              >
                <Download size={14} />
              </a>
            </div>
          </div>
        )}

        {/* Action Controls */}
        <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.25rem', flexWrap: 'wrap' }}>
          {!cid && (
            <button className="btn-primary" onClick={onUpload} disabled={loading}>
              <HardDrive size={15} />
              {loading ? 'Uploading...' : 'Persist File to IPFS'}
            </button>
          )}
          {cid && (
            <button className="btn-secondary" onClick={onVerify} disabled={loading}>
              <RefreshCw size={15} />
              {loading ? 'Verifying...' : 'Verify IPFS Content Hash'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default IPFSStoragePanel;
