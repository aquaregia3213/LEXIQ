'use client';

import React from 'react';
import { ContractItem } from '../lib/api';

interface HeaderProps {
  title: string;
  subtitle?: string;
  contracts: ContractItem[];
  selectedContractId: string;
  onSelectContract: (contractId: string) => void;
  onQuickUpload: () => void;
  isBackendConnected: boolean;
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  contracts,
  selectedContractId,
  onSelectContract,
  onQuickUpload,
  isBackendConnected,
  theme,
  onToggleTheme,
}) => {
  return (
    <header style={{
      padding: '1.25rem 2.5rem',
      background: 'var(--bg-card-glass)',
      backdropFilter: 'blur(16px)',
      borderBottom: '1px solid var(--border-color)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 40,
    }}>
      {/* Title & Subtitle */}
      <div>
        <h2 style={{
          fontSize: '1.5rem',
          fontWeight: 700,
          color: 'var(--text-primary)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
        }}>
          {title}
        </h2>
        {subtitle && (
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
            {subtitle}
          </p>
        )}
      </div>

      {/* Header Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        
        {/* Theme Toggle Button */}
        <button
          onClick={onToggleTheme}
          className="theme-toggle-btn"
          title="Toggle Light/Dark Theme"
        >
          {theme === 'dark' ? '☀️ Light' : '🌙 Dark'}
        </button>

        {/* Global Contract Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>
            Scope:
          </span>
          <select
            value={selectedContractId}
            onChange={(e) => onSelectContract(e.target.value)}
            className="input-legal"
            style={{
              padding: '0.45rem 0.85rem',
              fontSize: '0.85rem',
              width: 'auto',
              maxWidth: '220px',
            }}
          >
            <option value="">All Repository Contracts</option>
            {contracts.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.contract_type || 'Contract'})
              </option>
            ))}
          </select>
        </div>

        {/* Backend Connectivity Status */}
        <div className={`badge ${isBackendConnected ? 'badge-success' : 'badge-danger'}`}>
          <span className="status-dot" />
          {isBackendConnected ? 'API Connected' : 'Server Offline'}
        </div>

        {/* Quick Upload CTA */}
        <button className="btn-gold" onClick={onQuickUpload}>
          <span>+ Upload Contract</span>
        </button>
      </div>
    </header>
  );
};
