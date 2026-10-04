import { useState, useEffect } from 'react';
import {
  ShieldAlert,
  AlertOctagon,
  FileWarning,
  Zap,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Database,
  Cpu,
  Layers,
  ExternalLink,
} from 'lucide-react';
import { listDocuments, simulateDocumentTampering, seedTrainingData, trainModel } from '../services/api';
import type { Document, TamperingSimulationResponse, SeedDataResponse } from '../types';

export default function DemoTamperPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>('');
  const [loadingDocs, setLoadingDocs] = useState<boolean>(false);

  // Tamper simulation state
  const [simulating, setSimulating] = useState<boolean>(false);
  const [simulationResult, setSimulationResult] = useState<TamperingSimulationResponse | null>(null);
  const [simError, setSimError] = useState<string | null>(null);

  // Seeding state
  const [seeding, setSeeding] = useState<boolean>(false);
  const [seedResult, setSeedResult] = useState<SeedDataResponse | null>(null);
  const [seedError, setSeedError] = useState<string | null>(null);

  // Model quick-train state
  const [training, setTraining] = useState<boolean>(false);
  const [trainResult, setTrainResult] = useState<string | null>(null);

  const fetchDocs = async () => {
    setLoadingDocs(true);
    try {
      const res = await listDocuments(0, 50);
      setDocuments(res.documents || []);
      if (res.documents && res.documents.length > 0 && !selectedDocId) {
        setSelectedDocId(res.documents[0].document_id);
      }
    } catch (err: any) {
      console.error('Failed to load documents:', err);
    } finally {
      setLoadingDocs(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleSimulateTamper = async () => {
    if (!selectedDocId) {
      setSimError('Please select a document first.');
      return;
    }
    setSimulating(true);
    setSimError(null);
    setSimulationResult(null);
    try {
      const res = await simulateDocumentTampering(selectedDocId);
      setSimulationResult(res);
    } catch (err: any) {
      setSimError(err.message || 'Tampering simulation failed.');
    } finally {
      setSimulating(false);
    }
  };

  const handleSeedData = async (normal = 20, anomalous = 5) => {
    setSeeding(true);
    setSeedError(null);
    setSeedResult(null);
    try {
      const res = await seedTrainingData(normal, anomalous);
      setSeedResult(res);
      await fetchDocs();
    } catch (err: any) {
      setSeedError(err.message || 'Failed to seed synthetic dataset.');
    } finally {
      setSeeding(false);
    }
  };

  const handleQuickTrain = async () => {
    setTraining(true);
    setTrainResult(null);
    try {
      const res = await trainModel({
        model_name: 'IsolationForest',
        model_version: `1.0.demo_${Date.now().toString().slice(-4)}`,
        n_estimators: 100,
        random_state: 42,
        set_active: true,
      });
      setTrainResult(`Successfully trained and activated Isolation Forest v${res.model_version}!`);
    } catch (err: any) {
      setTrainResult(`Training failed: ${err.message || 'Unknown error'}`);
    } finally {
      setTraining(false);
    }
  };

  const selectedDoc = documents.find((d) => d.document_id === selectedDocId);

  return (
    <main className="container page">
      {/* Page Title & Hero */}
      <div className="card" style={{ background: 'linear-gradient(135deg, rgba(22, 27, 34, 0.95), rgba(33, 38, 45, 0.95))', borderColor: 'rgba(248, 81, 73, 0.3)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.75rem' }}>
          <div style={{
            width: '44px',
            height: '44px',
            borderRadius: '10px',
            background: 'rgba(248, 81, 73, 0.15)',
            border: '1px solid rgba(248, 81, 73, 0.4)',
            color: 'var(--clr-suspicious)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <ShieldAlert size={26} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span className="phase-tag" style={{ background: 'rgba(248, 81, 73, 0.15)', borderColor: 'rgba(248, 81, 73, 0.3)', color: '#ff7b72' }}>
                Forensic Simulation Lab
              </span>
              <span style={{ fontSize: '0.75rem', color: 'var(--clr-text-muted)' }}>
                Multi-Signal Integrity Test Suite
              </span>
            </div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--clr-text-primary)', marginTop: '0.25rem' }}>
              Document Tampering & Forensic Anomaly Simulator
            </h1>
          </div>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--clr-text-secondary)', lineHeight: 1.5, maxWidth: '900px' }}>
          This interactive laboratory demonstrates how malicious document alteration is caught across multiple layers:
          <strong> SHA-256 cryptographic discrepancy</strong>, <strong>Hyperledger Fabric immutable on-chain record mismatch</strong>, and <strong>Machine Learning statistical deviation scoring</strong>.
        </p>
      </div>

      {/* Grid Layout: Simulation on Left, Data Seeding / Setup on Right */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.6fr) minmax(0, 1fr)', gap: '1.5rem', alignItems: 'start' }}>
        
        {/* LEFT COLUMN: Tampering Simulation */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div className="card">
            <div className="card-header" style={{ marginBottom: '1rem' }}>
              <FileWarning size={18} style={{ color: '#f0883e' }} />
              <h2 className="card-title">1. Select Target Document & Trigger Attack</h2>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--clr-text-secondary)', marginBottom: '0.4rem' }}>
                Select an uploaded government document:
              </label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <select
                  value={selectedDocId}
                  onChange={(e) => setSelectedDocId(e.target.value)}
                  style={{
                    flex: 1,
                    background: 'var(--clr-bg)',
                    border: '1px solid var(--clr-border)',
                    color: 'var(--clr-text-primary)',
                    borderRadius: 'var(--r-md)',
                    padding: '0.5rem 0.75rem',
                    fontSize: '0.85rem',
                  }}
                  disabled={loadingDocs || simulating}
                >
                  {documents.length === 0 && (
                    <option value="">No documents found. Seed training data or upload a file first.</option>
                  )}
                  {documents.map((doc) => (
                    <option key={doc.document_id} value={doc.document_id}>
                      {doc.original_filename} ({doc.file_type}) — Status: {doc.status}
                    </option>
                  ))}
                </select>
                <button
                  className="btn-outline btn-sm"
                  onClick={fetchDocs}
                  disabled={loadingDocs}
                  title="Reload documents list"
                >
                  <RefreshCw size={14} className={loadingDocs ? 'spin' : ''} />
                </button>
              </div>

              {selectedDoc && (
                <div style={{
                  marginTop: '0.75rem',
                  padding: '0.6rem 0.8rem',
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--clr-border)',
                  borderRadius: 'var(--r-md)',
                  fontSize: '0.78rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}>
                  <div>
                    <span style={{ color: 'var(--clr-text-muted)' }}>Registered Hash: </span>
                    <code style={{ color: '#79c0ff', fontFamily: 'var(--font-mono)' }}>
                      {selectedDoc.file_hash ? `${selectedDoc.file_hash.slice(0, 16)}...${selectedDoc.file_hash.slice(-8)}` : 'Hash Pending'}
                    </code>
                  </div>
                  <a
                    href={`/documents/${selectedDoc.document_id}`}
                    style={{ color: 'var(--clr-accent-hover)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '3px' }}
                  >
                    View Details <ExternalLink size={12} />
                  </a>
                </div>
              )}
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
              <button
                className="btn-primary"
                onClick={handleSimulateTamper}
                disabled={simulating || !selectedDocId}
                style={{
                  background: 'linear-gradient(135deg, #d23f31, #b22222)',
                  borderColor: '#f85149',
                  padding: '0.65rem 1.25rem',
                  fontWeight: 600,
                  fontSize: '0.88rem',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                }}
              >
                <Zap size={16} />
                {simulating ? 'Simulating Tamper Attack...' : '🚨 Simulate Content Tampering'}
              </button>
              <span style={{ fontSize: '0.75rem', color: 'var(--clr-text-muted)' }}>
                Safe sandbox simulation (does not overwrite physical file)
              </span>
            </div>

            {simError && (
              <div style={{
                marginTop: '1rem',
                padding: '0.75rem',
                background: 'rgba(248, 81, 73, 0.1)',
                border: '1px solid rgba(248, 81, 73, 0.3)',
                borderRadius: 'var(--r-md)',
                color: 'var(--clr-suspicious)',
                fontSize: '0.82rem',
              }}>
                {simError}
              </div>
            )}
          </div>

          {/* SIMULATION RESULTS */}
          {simulationResult && (
            <div className="card" style={{ borderLeft: '4px solid #f85149' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <AlertOctagon size={20} style={{ color: 'var(--clr-suspicious)' }} />
                    <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--clr-text-primary)' }}>
                      Tampering Attack Detection Report
                    </h3>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--clr-text-muted)', marginTop: '0.2rem' }}>
                    Document: {simulationResult.tampering_simulation.original_filename}
                  </div>
                </div>

                <span style={{
                  padding: '4px 12px',
                  borderRadius: '100px',
                  background: 'rgba(248, 81, 73, 0.15)',
                  border: '1px solid rgba(248, 81, 73, 0.4)',
                  color: '#ff7b72',
                  fontWeight: 700,
                  fontSize: '0.8rem',
                }}>
                  {simulationResult.anomaly_analysis.risk_level} RISK
                </span>
              </div>

              {/* Hash Mismatch Comparison Box */}
              <div style={{
                background: 'var(--clr-bg)',
                border: '1px solid var(--clr-border)',
                borderRadius: 'var(--r-md)',
                padding: '1rem',
                marginBottom: '1rem',
              }}>
                <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--clr-text-secondary)', marginBottom: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Cryptographic Signature Verification
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                    <span style={{ color: 'var(--clr-text-muted)' }}>Registered Authentic Hash:</span>
                    <code style={{ color: '#3fb950', fontFamily: 'var(--font-mono)', background: 'rgba(63, 185, 80, 0.1)', padding: '2px 6px', borderRadius: '4px' }}>
                      {simulationResult.tampering_simulation.original_hash}
                    </code>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                    <span style={{ color: 'var(--clr-text-muted)' }}>Tampered Document Hash:</span>
                    <code style={{ color: '#f85149', fontFamily: 'var(--font-mono)', background: 'rgba(248, 81, 73, 0.1)', padding: '2px 6px', borderRadius: '4px' }}>
                      {simulationResult.tampering_simulation.simulated_tampered_hash}
                    </code>
                  </div>
                </div>

                <div style={{
                  marginTop: '0.75rem',
                  paddingTop: '0.75rem',
                  borderTop: '1px solid var(--clr-border)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  color: 'var(--clr-suspicious)',
                  fontSize: '0.82rem',
                  fontWeight: 600,
                }}>
                  <XCircle size={16} />
                  <span>HASH MISMATCH CONFIRMED: Cryptographic payload altered!</span>
                </div>
              </div>

              {/* Multi-Layer Signals Breakdown */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem', marginBottom: '1rem' }}>
                <div style={{ background: 'var(--clr-bg)', border: '1px solid var(--clr-border)', borderRadius: 'var(--r-md)', padding: '0.75rem' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--clr-text-muted)', textTransform: 'uppercase' }}>
                    Blockchain Verification
                  </div>
                  <div style={{ fontSize: '1rem', fontWeight: 700, color: simulationResult.blockchain_check.hash_match ? '#3fb950' : '#f85149', marginTop: '0.2rem' }}>
                    {simulationResult.blockchain_check.status}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--clr-text-secondary)', marginTop: '0.2rem' }}>
                    {simulationResult.blockchain_check.registered ? 'Fabric record checked' : 'Unregistered draft'}
                  </div>
                </div>

                <div style={{ background: 'var(--clr-bg)', border: '1px solid var(--clr-border)', borderRadius: 'var(--r-md)', padding: '0.75rem' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--clr-text-muted)', textTransform: 'uppercase' }}>
                    ML Anomaly Score
                  </div>
                  <div style={{ fontSize: '1rem', fontWeight: 700, color: '#f85149', marginTop: '0.2rem' }}>
                    {simulationResult.anomaly_analysis.anomaly_score_0_to_100}% Outlier
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--clr-text-secondary)', marginTop: '0.2rem' }}>
                    Statistical divergence detected
                  </div>
                </div>
              </div>

              {/* Detected Forensic Red Flags */}
              <div>
                <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--clr-text-secondary)', marginBottom: '0.5rem' }}>
                  Triggered Forensic Red Flags:
                </div>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  {simulationResult.anomaly_analysis.detected_issues.map((issue, idx) => (
                    <li
                      key={idx}
                      style={{
                        fontSize: '0.8rem',
                        color: '#ff7b72',
                        background: 'rgba(248, 81, 73, 0.08)',
                        border: '1px solid rgba(248, 81, 73, 0.2)',
                        padding: '0.4rem 0.6rem',
                        borderRadius: 'var(--r-sm)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.4rem',
                      }}
                    >
                      <span>⚠️</span> {issue}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Final Verdict Banner */}
              <div style={{
                marginTop: '1rem',
                padding: '0.75rem',
                background: 'rgba(248, 81, 73, 0.15)',
                border: '1px solid rgba(248, 81, 73, 0.4)',
                borderRadius: 'var(--r-md)',
                color: '#fff',
                fontWeight: 700,
                fontSize: '0.9rem',
                textAlign: 'center',
              }}>
                {simulationResult.anomaly_analysis.final_verdict}
              </div>
            </div>
          )}
        </div>

        {/* RIGHT COLUMN: Quick Seed & Training Hub */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          
          {/* Seeding Box */}
          <div className="card">
            <div className="card-header" style={{ marginBottom: '0.75rem' }}>
              <Database size={18} style={{ color: '#1f6feb' }} />
              <h2 className="card-title">2. Synthetic Dataset Seeder</h2>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--clr-text-secondary)', marginBottom: '1rem', lineHeight: 1.4 }}>
              Populate the system with standardized 85-dimensional feature vectors representing authentic government records and tampering anomalies.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              <button
                className="btn-secondary"
                onClick={() => handleSeedData(20, 5)}
                disabled={seeding}
                style={{ width: '100%', justifyContent: 'center' }}
              >
                <Database size={15} />
                {seeding ? 'Generating Vectors...' : 'Seed 25 Synthetic Feature Vectors'}
              </button>
              <button
                className="btn-outline btn-sm"
                onClick={() => handleSeedData(50, 10)}
                disabled={seeding}
                style={{ width: '100%', justifyContent: 'center' }}
              >
                Seed 60 High-Density Records
              </button>
            </div>

            {seedResult && (
              <div style={{
                marginTop: '0.75rem',
                padding: '0.6rem',
                background: 'rgba(63, 185, 80, 0.1)',
                border: '1px solid rgba(63, 185, 80, 0.3)',
                borderRadius: 'var(--r-md)',
                fontSize: '0.78rem',
                color: '#3fb950',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
              }}>
                <CheckCircle2 size={16} />
                <span>{seedResult.message} ({seedResult.total_seeded} total records)</span>
              </div>
            )}

            {seedError && (
              <div style={{
                marginTop: '0.75rem',
                padding: '0.6rem',
                background: 'rgba(248, 81, 73, 0.1)',
                border: '1px solid rgba(248, 81, 73, 0.3)',
                borderRadius: 'var(--r-md)',
                fontSize: '0.78rem',
                color: 'var(--clr-suspicious)',
              }}>
                {seedError}
              </div>
            )}
          </div>

          {/* Quick Model Training */}
          <div className="card">
            <div className="card-header" style={{ marginBottom: '0.75rem' }}>
              <Cpu size={18} style={{ color: '#8957e5' }} />
              <h2 className="card-title">3. Model Quick-Training</h2>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--clr-text-secondary)', marginBottom: '1rem', lineHeight: 1.4 }}>
              Train an Isolation Forest detector on the populated baseline feature distributions.
            </p>

            <button
              className="btn-primary"
              onClick={handleQuickTrain}
              disabled={training}
              style={{
                width: '100%',
                justifyContent: 'center',
                background: 'linear-gradient(135deg, #1f6feb, #8957e5)',
              }}
            >
              <Cpu size={15} />
              {training ? 'Training Model...' : 'Train Isolation Forest Now'}
            </button>

            {trainResult && (
              <div style={{
                marginTop: '0.75rem',
                padding: '0.6rem',
                background: 'rgba(56, 139, 253, 0.1)',
                border: '1px solid rgba(56, 139, 253, 0.3)',
                borderRadius: 'var(--r-md)',
                fontSize: '0.78rem',
                color: '#79c0ff',
              }}>
                {trainResult}
              </div>
            )}
          </div>

          {/* Defense-in-Depth Architecture Card */}
          <div className="card" style={{ background: 'var(--clr-surface)' }}>
            <div className="card-header" style={{ marginBottom: '0.75rem' }}>
              <Layers size={18} style={{ color: '#58a6ff' }} />
              <h2 className="card-title" style={{ fontSize: '0.85rem' }}>Defense-in-Depth Pipeline</h2>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.78rem' }}>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
                <span style={{ fontWeight: 700, color: '#58a6ff', minWidth: '16px' }}>1.</span>
                <div>
                  <strong style={{ color: 'var(--clr-text-primary)' }}>Cryptographic Hashes:</strong>
                  <div style={{ color: 'var(--clr-text-secondary)' }}>SHA-256 binary validation on ingress and egress.</div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
                <span style={{ fontWeight: 700, color: '#3fb950', minWidth: '16px' }}>2.</span>
                <div>
                  <strong style={{ color: 'var(--clr-text-primary)' }}>Hyperledger Fabric Ledger:</strong>
                  <div style={{ color: 'var(--clr-text-secondary)' }}>Immutable timestamping and transaction audit trail.</div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
                <span style={{ fontWeight: 700, color: '#8957e5', minWidth: '16px' }}>3.</span>
                <div>
                  <strong style={{ color: 'var(--clr-text-primary)' }}>IPFS Content Addressing:</strong>
                  <div style={{ color: 'var(--clr-text-secondary)' }}>Decentralized CID-based content retrieval.</div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
                <span style={{ fontWeight: 700, color: '#f0883e', minWidth: '16px' }}>4.</span>
                <div>
                  <strong style={{ color: 'var(--clr-text-primary)' }}>Dual ML Anomaly Detection:</strong>
                  <div style={{ color: 'var(--clr-text-secondary)' }}>Isolation Forest + Deep Autoencoder scoring.</div>
                </div>
              </div>
            </div>
          </div>

        </div>

      </div>
    </main>
  );
}
