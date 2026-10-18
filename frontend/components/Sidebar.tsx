'use client';

import React from 'react';

export type ViewType = 
  | 'dashboard'
  | 'upload'
  | 'contracts'
  | 'details'
  | 'agent'
  | 'ecourts'
  | 'search'
  | 'rag'
  | 'clauses'
  | 'entities'
  | 'risks'
  | 'evidence';

interface SidebarProps {
  currentView: ViewType;
  onNavigate: (view: ViewType) => void;
  isBackendConnected: boolean;
  totalContractsCount: number;
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentView,
  onNavigate,
  isBackendConnected,
  totalContractsCount,
  theme,
  onToggleTheme,
}) => {
  const navItems: { id: ViewType; label: string; icon: string; badge?: string }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: '⚡' },
    { id: 'agent', label: 'AI Analyst', icon: '🤖', badge: 'Agent' },
    { id: 'ecourts', label: 'eCourts India', icon: '⚖️', badge: 'Official' },
    { id: 'upload', label: 'Contract Upload', icon: '📤' },
    { id: 'contracts', label: 'Contract Repository', icon: '📁', badge: totalContractsCount > 0 ? String(totalContractsCount) : undefined },
    { id: 'search', label: 'Semantic Search', icon: '🔍' },
    { id: 'rag', label: 'Legal AI Assistant', icon: '💬', badge: 'RAG' },
    { id: 'clauses', label: 'Clause Intelligence', icon: '📜' },
    { id: 'entities', label: 'Entity Extraction', icon: '🏢' },
    { id: 'risks', label: 'Risk Analysis', icon: '⚠️' },
    { id: 'evidence', label: 'Source Evidence', icon: '🔬' },
  ];

  return (
    <aside style={{
      width: '260px',
      height: '100vh',
      position: 'fixed',
      top: 0,
      left: 0,
      background: 'var(--bg-secondary)',
      backdropFilter: 'blur(20px)',
      borderRight: '1px solid var(--border-color)',
      display: 'flex',
      flexDirection: 'column',
      zIndex: 50,
      transition: 'all 0.25s ease',
    }}>
      {/* Brand Header: JURISCOPE */}
      <div style={{
        padding: '1.75rem 1.5rem',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '0.75rem',
            background: 'var(--accent-gold-bg)',
            border: '1px solid var(--border-gold)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.4rem',
            boxShadow: '0 0 15px rgba(212, 175, 55, 0.2)'
          }}>
            ⚖️
          </div>
          <div>
            <h1 style={{
              fontSize: '1.25rem',
              fontWeight: 800,
              letterSpacing: '0.05em',
              fontFamily: 'Playfair Display, serif',
              background: 'var(--gradient-gold)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              JURISCOPE
            </h1>
            <p style={{ fontSize: '0.68rem', color: 'var(--text-muted)', letterSpacing: '0.03em', textTransform: 'uppercase', fontWeight: 700 }}>
              3D Legal AI Platform
            </p>
          </div>
        </div>
      </div>

      {/* Navigation List */}
      <nav style={{ flex: 1, padding: '1.25rem 1rem', overflowY: 'auto' }}>
        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 700, padding: '0 0.5rem 0.75rem 0.5rem' }}>
          Navigation Views
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
          {navItems.map((item) => {
            const isActive = currentView === item.id || (currentView === 'details' && item.id === 'contracts');
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  width: '100%',
                  padding: '0.75rem 1rem',
                  borderRadius: '0.6rem',
                  border: isActive ? '1px solid var(--border-gold)' : '1px solid transparent',
                  background: isActive ? 'var(--accent-gold-bg)' : 'transparent',
                  color: isActive ? 'var(--text-gold)' : 'var(--text-secondary)',
                  fontWeight: isActive ? 700 : 500,
                  fontSize: '0.9rem',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.2s ease',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span style={{ fontSize: '1.1rem' }}>{item.icon}</span>
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className={`badge ${isActive ? 'badge-gold' : 'badge-info'}`} style={{ padding: '0.15rem 0.5rem', fontSize: '0.7rem' }}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </nav>

      {/* Footer & Theme Switcher */}
      <div style={{
        padding: '1.25rem 1.5rem',
        borderTop: '1px solid var(--border-color)',
        background: 'var(--bg-card)',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.85rem'
      }}>
        {/* Light / Dark Mode Toggle Button */}
        <button
          onClick={onToggleTheme}
          className="theme-toggle-btn"
          style={{ width: '100%', justifyContent: 'center' }}
        >
          <span>{theme === 'dark' ? '☀️ Switch to Light Mode' : '🌙 Switch to Dark Mode'}</span>
        </button>

        {/* Backend Status */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>FastAPI Engine</span>
          {isBackendConnected ? (
            <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>
              <span className="status-dot" /> Online
            </span>
          ) : (
            <span className="badge badge-danger" style={{ fontSize: '0.7rem' }}>
              <span className="status-dot" /> Offline
            </span>
          )}
        </div>
      </div>
    </aside>
  );
};
