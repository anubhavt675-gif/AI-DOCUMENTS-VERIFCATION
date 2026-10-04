import { useState, useEffect } from 'react';
import { ShieldCheck, User, ChevronDown } from 'lucide-react';
import { checkHealth } from '../services/api';

export default function Header() {
  const [apiOnline, setApiOnline] = useState<boolean>(true);
  const [showAdminMenu, setShowAdminMenu] = useState<boolean>(false);

  useEffect(() => {
    let mounted = true;
    const testApi = async () => {
      try {
        await checkHealth();
        if (mounted) setApiOnline(true);
      } catch {
        if (mounted) setApiOnline(false);
      }
    };
    testApi();
    const interval = setInterval(testApi, 15000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="gov-header">
      {/* Left: Glowing Blue Shield & Titles */}
      <div className="gov-header-left">
        <div className="gov-shield-icon">
          <ShieldCheck size={26} strokeWidth={2.4} />
        </div>
        <div className="gov-title-block">
          <h1>Government Document Integrity Verification</h1>
          <p>Multi-Signal AI Anomaly Detection & Blockchain Verification</p>
        </div>
      </div>

      {/* Right: Status Pill, Phase Pill, Admin Dropdown */}
      <div className="gov-header-right">
        <div className="gov-status-badge">
          <span className="gov-pulse-dot" style={{ background: apiOnline ? '#10b981' : '#f85149', boxShadow: apiOnline ? '0 0 8px #10b981' : '0 0 8px #f85149' }} />
          <span>{apiOnline ? 'AI Online' : 'AI Offline'}</span>
        </div>

        <div className="gov-phase-pill">
          Phase 7 - Multi-Signal Integrity
        </div>

        <div className="gov-admin-pill" onClick={() => setShowAdminMenu(!showAdminMenu)} style={{ position: 'relative' }}>
          <div style={{
            width: '24px',
            height: '24px',
            borderRadius: '50%',
            background: 'rgba(255,255,255,0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <User size={14} color="#e2e8f0" />
          </div>
          <span style={{ fontWeight: 600 }}>Admin</span>
          <ChevronDown size={14} color="#94a3b8" />

          {showAdminMenu && (
            <div style={{
              position: 'absolute',
              top: '120%',
              right: 0,
              width: '180px',
              background: '#0d1730',
              border: '1px solid #1a2f5a',
              borderRadius: '10px',
              padding: '0.5rem',
              boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
              zIndex: 200,
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
            }}>
              <div style={{ padding: '0.4rem 0.6rem', fontSize: '0.72rem', color: '#64748b', borderBottom: '1px solid #142343' }}>
                Signed in as <strong>National Security Admin</strong>
              </div>
              <a href="/ml" style={{ padding: '0.4rem 0.6rem', fontSize: '0.78rem', color: '#cbd5e1', textDecoration: 'none', borderRadius: '6px' }}>
                🧠 ML Models Registry
              </a>
              <a href="/demo" style={{ padding: '0.4rem 0.6rem', fontSize: '0.78rem', color: '#cbd5e1', textDecoration: 'none', borderRadius: '6px' }}>
                🛡️ Tampering Sandbox
              </a>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
