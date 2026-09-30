'use client';

import React from 'react';
import { ContractItem, HealthStatus } from '../../lib/api';
import { ViewType } from '../Sidebar';

interface DashboardViewProps {
  contracts: ContractItem[];
  health: HealthStatus | null;
  loading: boolean;
  onNavigate: (view: ViewType) => void;
  onSelectContract: (contractId: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  contracts,
  health,
  loading,
  onNavigate,
  onSelectContract,
}) => {
  // Aggregate stats across contracts
  const totalContracts = contracts.length;
  const totalClauses = contracts.reduce((acc, c) => acc + (c.clauses?.length || 0), 0);
  const totalEntities = contracts.reduce((acc, c) => acc + (c.entities?.length || 0), 0);
  const totalRisks = contracts.reduce((acc, c) => acc + (c.risk_flags?.length || 0), 0);

  // Severe risk count
  const criticalRisks = contracts.reduce((acc, c) => {
    return acc + (c.risk_flags?.filter((r) => r.severity === 'HIGH' || r.severity === 'CRITICAL').length || 0);
  }, 0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2.25rem' }}>
      
      {/* 3D Elevated Hero Banner: JURISCOPE — 3D Legal Intelligence Engine */}
      <div className="card-glass card-gold-border card-3d-elevated" style={{ padding: '2.75rem 2.25rem', position: 'relative' }}>
        <div style={{ maxWidth: '780px' }}>
          <div style={{ marginBottom: '0.85rem' }}>
            <span className="badge badge-gold">
              <span className="status-dot" /> JURISCOPE — 3D Legal Intelligence Engine
            </span>
          </div>
          <h1 className="serif-title" style={{ fontSize: '2.4rem', fontWeight: 700, lineHeight: 1.2, marginBottom: '0.85rem' }}>
            JURISCOPE Legal Intelligence & Risk Assurance
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.02rem', lineHeight: 1.6 }}>
            Automated contract parsing, pgvector semantic retrieval, grounded RAG Q&A, 3D clause taxonomy, and automated risk analysis for modern legal practices.
          </p>
        </div>
      </div>

      {/* 3D KPI Metrics Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem' }}>
        
        {/* Total Contracts */}
        <div className="card-glass" style={{ cursor: 'pointer' }} onClick={() => onNavigate('contracts')}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-gold)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              INGESTED CONTRACTS
            </span>
            <div className="icon-3d" style={{ width: '42px', height: '42px', background: 'var(--accent-gold-bg)', border: '1px solid var(--border-gold)', color: 'var(--text-gold)', fontSize: '1.3rem' }}>
              📁
            </div>
          </div>
          <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--text-primary)', textShadow: '0 4px 10px rgba(0,0,0,0.3)' }}>
            {loading ? <span className="skeleton" style={{ display: 'inline-block', width: '60px', height: '36px' }} /> : totalContracts}
          </div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
            Active documents in repository
          </div>
        </div>

        {/* Total Clauses */}
        <div className="card-glass" style={{ cursor: 'pointer' }} onClick={() => onNavigate('clauses')}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--accent-blue)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              EXTRACTED CLAUSES
            </span>
            <div className="icon-3d" style={{ width: '42px', height: '42px', background: 'var(--accent-blue-bg)', border: '1px solid rgba(59, 130, 246, 0.3)', color: 'var(--accent-blue)', fontSize: '1.3rem' }}>
              📜
            </div>
          </div>
          <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--text-primary)', textShadow: '0 4px 10px rgba(0,0,0,0.3)' }}>
            {loading ? <span className="skeleton" style={{ display: 'inline-block', width: '60px', height: '36px' }} /> : totalClauses}
          </div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
            Categorized clause provisions
          </div>
        </div>

        {/* Total Entities */}
        <div className="card-glass" style={{ cursor: 'pointer' }} onClick={() => onNavigate('entities')}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--accent-purple)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              IDENTIFIED ENTITIES
            </span>
            <div className="icon-3d" style={{ width: '42px', height: '42px', background: 'var(--accent-purple-bg)', border: '1px solid rgba(139, 92, 246, 0.3)', color: 'var(--accent-purple)', fontSize: '1.3rem' }}>
              🏢
            </div>
          </div>
          <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--text-primary)', textShadow: '0 4px 10px rgba(0,0,0,0.3)' }}>
            {loading ? <span className="skeleton" style={{ display: 'inline-block', width: '60px', height: '36px' }} /> : totalEntities}
          </div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
            Parties, dates & monetary values
          </div>
        </div>

        {/* Risk Flags */}
        <div className="card-glass" style={{ cursor: 'pointer' }} onClick={() => onNavigate('risks')}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--accent-rose)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              RISK FLAGS
            </span>
            <div className="icon-3d" style={{ width: '42px', height: '42px', background: 'var(--accent-rose-bg)', border: '1px solid rgba(244, 63, 94, 0.3)', color: 'var(--accent-rose)', fontSize: '1.3rem' }}>
              ⚠️
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
            <span style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--text-primary)', textShadow: '0 4px 10px rgba(0,0,0,0.3)' }}>
              {loading ? <span className="skeleton" style={{ display: 'inline-block', width: '60px', height: '36px' }} /> : totalRisks}
            </span>
            {criticalRisks > 0 && (
              <span style={{ fontSize: '0.85rem', color: 'var(--accent-rose)', fontWeight: 700 }}>
                ({criticalRisks} High/Critical)
              </span>
            )}
          </div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
            Flagged contractual concerns
          </div>
        </div>

      </div>

      {/* 3D Interactive Workflow Shortcuts */}
      <div>
        <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--text-primary)' }}>
          3D Interactive Workflows & Actions
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.25rem' }}>
          
          <button className="card-glass" onClick={() => onNavigate('upload')} style={{ textAlign: 'left', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '1.1rem' }}>
            <div className="icon-3d" style={{ fontSize: '1.8rem', background: 'var(--accent-gold-bg)', padding: '0.85rem', border: '1px solid var(--border-gold)' }}>📤</div>
            <div>
              <div style={{ fontWeight: 700, color: 'var(--text-gold)', marginBottom: '0.2rem', fontSize: '1rem' }}>Upload Contract</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Parse PDF or DOCX file into repository</div>
            </div>
          </button>

          <button className="card-glass" onClick={() => onNavigate('rag')} style={{ textAlign: 'left', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '1.1rem' }}>
            <div className="icon-3d" style={{ fontSize: '1.8rem', background: 'var(--accent-blue-bg)', padding: '0.85rem', border: '1px solid rgba(59, 130, 246, 0.3)' }}>💬</div>
            <div>
              <div style={{ fontWeight: 700, color: 'var(--accent-blue)', marginBottom: '0.2rem', fontSize: '1rem' }}>Ask Legal AI</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Grounded natural language Q&A</div>
            </div>
          </button>

          <button className="card-glass" onClick={() => onNavigate('search')} style={{ textAlign: 'left', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '1.1rem' }}>
            <div className="icon-3d" style={{ fontSize: '1.8rem', background: 'var(--accent-purple-bg)', padding: '0.85rem', border: '1px solid rgba(139, 92, 246, 0.3)' }}>🔍</div>
            <div>
              <div style={{ fontWeight: 700, color: 'var(--accent-purple)', marginBottom: '0.2rem', fontSize: '1rem' }}>Semantic Search</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Vector similarity chunk discovery</div>
            </div>
          </button>

          <button className="card-glass" onClick={() => onNavigate('risks')} style={{ textAlign: 'left', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '1.1rem' }}>
            <div className="icon-3d" style={{ fontSize: '1.8rem', background: 'var(--accent-rose-bg)', padding: '0.85rem', border: '1px solid rgba(244, 63, 94, 0.3)' }}>🛡️</div>
            <div>
              <div style={{ fontWeight: 700, color: 'var(--accent-rose)', marginBottom: '0.2rem', fontSize: '1rem' }}>Risk Center</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Review flagged contract liabilities</div>
            </div>
          </button>

        </div>
      </div>

      {/* System Health & Recent Contracts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.5rem' }}>
        
        {/* Backend & DB Health Card */}
        <div className="card-glass">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>FastAPI & Database Engine</h3>
            {health ? (
              <span className="badge badge-success">
                <span className="status-dot" /> Online
              </span>
            ) : (
              <span className="badge badge-danger">
                <span className="status-dot" /> Offline
              </span>
            )}
          </div>

          {health ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', fontSize: '0.9rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.6rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Backend Version</span>
                <span style={{ fontWeight: 600 }}>v{health.version}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.6rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Service Engine</span>
                <span style={{ fontWeight: 600 }}>{health.service}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.6rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Database Status</span>
                <span style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>{health.database?.status || 'CONNECTED'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Vector Store</span>
                <span style={{ color: 'var(--text-gold)', fontWeight: 600 }}>pgvector</span>
              </div>
            </div>
          ) : (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Attempting connection to backend service at http://127.0.0.1:8000...
            </p>
          )}
        </div>

        {/* Recent Contracts Card */}
        <div className="card-glass">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Recent Uploads</h3>
            <button className="btn-secondary" style={{ fontSize: '0.75rem', padding: '0.35rem 0.85rem' }} onClick={() => onNavigate('contracts')}>
              View All
            </button>
          </div>

          {contracts.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              No contracts ingested yet. Upload your first PDF/DOCX contract to begin.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {contracts.slice(0, 4).map((c) => (
                <div
                  key={c.id}
                  onClick={() => onSelectContract(c.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.85rem 1rem',
                    borderRadius: '0.6rem',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    cursor: 'pointer',
                    transition: 'all 0.25s ease',
                    boxShadow: '0 4px 15px rgba(0,0,0,0.1)',
                  }}
                >
                  <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '220px' }}>
                    <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-gold)' }}>{c.name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{c.contract_type || 'Contract'}</div>
                  </div>
                  <span className={`badge ${c.status === 'COMPLETED' ? 'badge-success' : c.status === 'FAILED' ? 'badge-danger' : 'badge-warning'}`} style={{ fontSize: '0.7rem' }}>
                    {c.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );
};
