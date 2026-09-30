'use client';

import React from 'react';

export interface EvidenceData {
  contractName?: string;
  fileName?: string;
  pageStart?: number;
  pageEnd?: number;
  section?: string;
  text?: string;
  similarityScore?: number;
  chunkId?: string;
  metadata?: any;
}

interface EvidenceModalProps {
  evidence: EvidenceData | null;
  onClose: () => void;
}

export const EvidenceModal: React.FC<EvidenceModalProps> = ({ evidence, onClose }) => {
  if (!evidence) return null;

  const scorePct = evidence.similarityScore
    ? Math.round(evidence.similarityScore * 100)
    : null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(5, 7, 12, 0.88)',
        backdropFilter: 'blur(16px)',
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem',
        perspective: '1200px',
      }}
      onClick={onClose}
    >
      <div
        className="card-glass card-gold-border card-3d-elevated"
        style={{
          maxWidth: '780px',
          width: '100%',
          maxHeight: '90vh',
          overflowY: 'auto',
          padding: '2.25rem',
          transform: 'perspective(1000px) rotateX(1deg) translateZ(30px)',
          boxShadow: '0 35px 70px -15px rgba(0, 0, 0, 0.9), 0 0 45px rgba(212, 175, 55, 0.25)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
              <span className="badge badge-gold">
                🔬 3D Source & Evidence Inspector
              </span>
              {scorePct !== null && (
                <span className="badge badge-success">
                  {scorePct}% Grounding Match
                </span>
              )}
            </div>
            <h3 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {evidence.contractName || evidence.fileName || 'Contract Document Evidence'}
            </h3>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-muted)',
              fontSize: '1.2rem',
              cursor: 'pointer',
              lineHeight: 1,
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            ✕
          </button>
        </div>

        {/* Location & Metadata Bar */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
          gap: '1rem',
          padding: '1.1rem 1.25rem',
          background: 'rgba(13, 17, 26, 0.95)',
          borderRadius: '0.75rem',
          border: '1px solid var(--border-color)',
          marginBottom: '1.5rem',
          fontSize: '0.85rem',
          boxShadow: 'inset 0 2px 4px rgba(0, 0, 0, 0.5)',
        }}>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase' }}>DOCUMENT PAGE</div>
            <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.2rem' }}>
              Page {evidence.pageStart || 1} {evidence.pageEnd && evidence.pageEnd !== evidence.pageStart ? `- ${evidence.pageEnd}` : ''}
            </div>
          </div>

          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase' }}>SECTION / HEADING</div>
            <div style={{ fontWeight: 700, color: 'var(--text-gold)', marginTop: '0.2rem' }}>
              {evidence.section || 'General Content'}
            </div>
          </div>

          {evidence.fileName && (
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase' }}>SOURCE FILE</div>
              <div style={{ color: 'var(--text-secondary)', marginTop: '0.2rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {evidence.fileName}
              </div>
            </div>
          )}
        </div>

        {/* Evidence Text Box */}
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ fontSize: '0.75rem', color: 'var(--text-gold)', fontWeight: 700, display: 'block', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Extracted Document Chunk (Verbatim Source Text)
          </label>
          <div style={{
            background: 'rgba(7, 9, 14, 0.98)',
            border: '1.5px solid var(--border-gold)',
            borderRadius: '0.75rem',
            padding: '1.35rem',
            lineHeight: 1.6,
            color: '#e2e8f0',
            fontFamily: 'Consolas, Monaco, monospace',
            fontSize: '0.92rem',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            boxShadow: 'inset 0 2px 10px rgba(0, 0, 0, 0.8), 0 0 15px rgba(212, 175, 55, 0.1)',
          }}>
            {evidence.text || 'No text snippet available.'}
          </div>
        </div>

        {/* Action / Disclaimer Footer */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          paddingTop: '1.25rem',
          borderTop: '1px solid var(--border-color)',
          fontSize: '0.8rem',
          color: 'var(--text-muted)'
        }}>
          <div>
            Grounded in vector chunk index. Zero artificial text generation.
          </div>
          <button className="btn-secondary" onClick={onClose}>
            Close Evidence
          </button>
        </div>
      </div>
    </div>
  );
};
