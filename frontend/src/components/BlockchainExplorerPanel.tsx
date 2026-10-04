import React, { useState } from 'react';
import { Blocks, Copy, Check, RefreshCw } from 'lucide-react';
import type { BlockchainVerifyResponse, BlockchainHistoryResponse } from '../types';

interface BlockchainExplorerPanelProps {
  documentId?: string;
  isRegistered: boolean;
  verifyData?: BlockchainVerifyResponse | null;
  historyData?: BlockchainHistoryResponse | null;
  onRegister: () => Promise<void>;
  onVerify: () => Promise<void>;
  loading: boolean;
}

export const BlockchainExplorerPanel: React.FC<BlockchainExplorerPanelProps> = ({
  isRegistered,
  verifyData,
  historyData,
  onRegister,
  onVerify,
  loading,
}) => {
  const [copiedTx, setCopiedTx] = useState(false);
  const [copiedHash, setCopiedHash] = useState(false);

  const txId = verifyData?.transaction_id || historyData?.history?.[0]?.transaction_id || null;
  const docHash = verifyData?.registered_hash || verifyData?.current_hash || null;
  const status = verifyData?.integrity_status || (isRegistered ? 'REGISTERED' : 'UNREGISTERED');

  const copyToClipboard = (text: string, type: 'tx' | 'hash') => {
    navigator.clipboard.writeText(text);
    if (type === 'tx') {
      setCopiedTx(true);
      setTimeout(() => setCopiedTx(false), 2000);
    } else {
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    }
  };

  return (
    <div className="card" style={{ marginBottom: '1.5rem' }}>
      <div className="card-header">
        <Blocks size={18} />
        <h2 className="card-title">Hyperledger Fabric Blockchain Ledger</h2>
        <span
          className={`badge ${
            status === 'MATCH' || status === 'REGISTERED'
              ? 'badge-verified'
              : status === 'HASH_MISMATCH' || status === 'INTEGRITY_MISMATCH'
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
            <div className="detail-label">Network Topology</div>
            <div className="detail-value">government-document-integrity-network</div>
          </div>
          <div className="detail-field">
            <div className="detail-label">Channel</div>
            <div className="detail-value">integritychannel</div>
          </div>
          <div className="detail-field">
            <div className="detail-label">Smart Contract (Chaincode)</div>
            <div className="detail-value">documentintegrity (v1.0 Go)</div>
          </div>
          <div className="detail-field">
            <div className="detail-label">Ledger State</div>
            <div className="detail-value">
              {isRegistered || txId ? (
                <span style={{ color: 'var(--clr-verified)', fontWeight: 600 }}>
                  ✓ Fingerprint Committed
                </span>
              ) : (
                <span style={{ color: 'var(--clr-text-muted)' }}>Unregistered on Ledger</span>
              )}
            </div>
          </div>
        </div>

        {txId && (
          <div style={{ marginTop: '1rem' }}>
            <div className="detail-label">Transaction ID (Fabric Cryptographic Hash)</div>
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
                  fontSize: '0.8rem',
                  wordBreak: 'break-all',
                  color: 'var(--clr-accent-hover)',
                  flex: 1,
                }}
              >
                {txId}
              </code>
              <button
                className="btn-ghost"
                onClick={() => copyToClipboard(txId, 'tx')}
                title="Copy Transaction ID"
                style={{ padding: '0.2rem 0.5rem' }}
              >
                {copiedTx ? <Check size={14} color="var(--clr-verified)" /> : <Copy size={14} />}
              </button>
            </div>
          </div>
        )}

        {docHash && (
          <div style={{ marginTop: '0.75rem' }}>
            <div className="detail-label">Committed SHA-256 Document Fingerprint</div>
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
                  fontSize: '0.8rem',
                  wordBreak: 'break-all',
                  color: 'var(--clr-text-primary)',
                  flex: 1,
                }}
              >
                {docHash}
              </code>
              <button
                className="btn-ghost"
                onClick={() => copyToClipboard(docHash, 'hash')}
                title="Copy Hash"
                style={{ padding: '0.2rem 0.5rem' }}
              >
                {copiedHash ? <Check size={14} color="var(--clr-verified)" /> : <Copy size={14} />}
              </button>
            </div>
          </div>
        )}

        {/* Audit History Log */}
        {historyData && historyData.history && historyData.history.length > 0 && (
          <div style={{ marginTop: '1.25rem' }}>
            <div className="detail-label" style={{ marginBottom: '0.4rem' }}>
              Immutable Transaction History ({historyData.total_events} events)
            </div>
            <div
              style={{
                overflowX: 'auto',
                border: '1px solid var(--clr-border)',
                borderRadius: 'var(--r-md)',
              }}
            >
              <table style={{ width: '100%', fontSize: '0.8rem', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: 'var(--clr-surface)', borderBottom: '1px solid var(--clr-border)' }}>
                    <th style={{ padding: '0.4rem 0.6rem', textAlign: 'left' }}>Event</th>
                    <th style={{ padding: '0.4rem 0.6rem', textAlign: 'left' }}>Block #</th>
                    <th style={{ padding: '0.4rem 0.6rem', textAlign: 'left' }}>Timestamp (UTC)</th>
                    <th style={{ padding: '0.4rem 0.6rem', textAlign: 'left' }}>Tx ID</th>
                  </tr>
                </thead>
                <tbody>
                  {historyData.history.map((entry, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid var(--clr-border-2)' }}>
                      <td style={{ padding: '0.4rem 0.6rem' }}>{entry.event_type}</td>
                      <td style={{ padding: '0.4rem 0.6rem' }}>#{entry.block_number ?? '1'}</td>
                      <td style={{ padding: '0.4rem 0.6rem' }}>
                        {new Date(entry.timestamp).toLocaleString()}
                      </td>
                      <td style={{ padding: '0.4rem 0.6rem', fontFamily: 'var(--font-mono)' }}>
                        {entry.transaction_id.slice(0, 16)}...
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Action Controls */}
        <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.25rem', flexWrap: 'wrap' }}>
          {!isRegistered && (
            <button className="btn-primary" onClick={onRegister} disabled={loading}>
              <Blocks size={15} />
              {loading ? 'Submitting Transaction...' : 'Register on Hyperledger Fabric'}
            </button>
          )}
          <button className="btn-secondary" onClick={onVerify} disabled={loading}>
            <RefreshCw size={15} />
            {loading ? 'Querying Ledger...' : 'Verify Technical Hash on Chain'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default BlockchainExplorerPanel;
