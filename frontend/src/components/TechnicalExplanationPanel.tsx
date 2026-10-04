import React from 'react';
import { Info, ShieldAlert } from 'lucide-react';

export const TechnicalExplanationPanel: React.FC = () => {
  return (
    <div className="card" style={{ marginBottom: '1.5rem', backgroundColor: 'var(--clr-bg-2)' }}>
      <div className="card-header">
        <Info size={18} color="var(--clr-accent-hover)" />
        <h2 className="card-title">How Document Technical Verification Works</h2>
      </div>

      <div style={{ padding: '0.75rem 0', fontSize: '0.85rem', lineHeight: '1.6' }}>
        <p style={{ color: 'var(--clr-text-secondary)', marginBottom: '1rem' }}>
          This system verifies technical file integrity and evaluates statistical anomaly signals using a three-tier architecture:
        </p>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '0.75rem',
            marginBottom: '1rem',
          }}
        >
          <div style={{ padding: '0.75rem', backgroundColor: 'var(--clr-bg)', borderRadius: 'var(--r-md)', border: '1px solid var(--clr-border)' }}>
            <strong style={{ color: 'var(--clr-text-primary)' }}>1. Cryptographic Fingerprint:</strong>
            <p style={{ color: 'var(--clr-text-secondary)', fontSize: '0.8rem', marginTop: '0.2rem' }}>
              The ingested document receives a SHA-256 hash fingerprint calculated directly from its byte stream.
            </p>
          </div>

          <div style={{ padding: '0.75rem', backgroundColor: 'var(--clr-bg)', borderRadius: 'var(--r-md)', border: '1px solid var(--clr-border)' }}>
            <strong style={{ color: 'var(--clr-text-primary)' }}>2. IPFS Storage & CID:</strong>
            <p style={{ color: 'var(--clr-text-secondary)', fontSize: '0.8rem', marginTop: '0.2rem' }}>
              The file is archived in decentralized, content-addressed IPFS storage, returning a reproducible Content Identifier (CID).
            </p>
          </div>

          <div style={{ padding: '0.75rem', backgroundColor: 'var(--clr-bg)', borderRadius: 'var(--r-md)', border: '1px solid var(--clr-border)' }}>
            <strong style={{ color: 'var(--clr-text-primary)' }}>3. Hyperledger Fabric Record:</strong>
            <p style={{ color: 'var(--clr-text-secondary)', fontSize: '0.8rem', marginTop: '0.2rem' }}>
              The document hash and IPFS CID are immutably recorded on-chain via smart contract. The full document is never stored on blockchain.
            </p>
          </div>

          <div style={{ padding: '0.75rem', backgroundColor: 'var(--clr-bg)', borderRadius: 'var(--r-md)', border: '1px solid var(--clr-border)' }}>
            <strong style={{ color: 'var(--clr-text-primary)' }}>4. Multi-Signal Verification:</strong>
            <p style={{ color: 'var(--clr-text-secondary)', fontSize: '0.8rem', marginTop: '0.2rem' }}>
              During verification, current file SHA-256 is matched against the on-chain ledger, IPFS content is validated, and PyTorch Autoencoder evaluates statistical deviations.
            </p>
          </div>
        </div>

        {/* Forensic & Legal Clarifications */}
        <div
          style={{
            padding: '0.75rem 1rem',
            backgroundColor: 'rgba(31, 111, 235, 0.08)',
            borderLeft: '3px solid var(--clr-accent)',
            borderRadius: 'var(--r-sm)',
            fontSize: '0.78rem',
            color: 'var(--clr-text-secondary)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem', color: 'var(--clr-accent-hover)', fontWeight: 600 }}>
            <ShieldAlert size={14} />
            Forensic & Technical Evidence Standards
          </div>
          <ul style={{ paddingLeft: '1.2rem', margin: 0 }}>
            <li>
              <strong>Cryptographic Integrity:</strong> A matching blockchain record confirms byte-level consistency since registration; it does <em>not</em> independently authenticate the real-world legitimacy of the original issuing authority.
            </li>
            <li>
              <strong>Machine Learning Signals:</strong> Anomaly scores from the PyTorch Autoencoder identify statistical deviations from baseline training distributions; an anomaly score alone does <em>not</em> prove fraudulent tampering.
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default TechnicalExplanationPanel;
