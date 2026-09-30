'use client';

import React, { useState, useEffect } from 'react';
import { api, ContractItem, ChunkInfo, ClauseInfo } from '../../lib/api';

interface SourceEvidenceViewProps {
  contracts: ContractItem[];
  selectedContractId: string;
  onOpenEvidence: (evidence: any) => void;
  onSelectContract: (contractId: string) => void;
}

export const SourceEvidenceView: React.FC<SourceEvidenceViewProps> = ({
  contracts,
  selectedContractId,
  onOpenEvidence,
  onSelectContract,
}) => {
  const [targetId, setTargetId] = useState<string>(selectedContractId || (contracts[0]?.id || ''));
  const [activeTab, setActiveTab] = useState<'chunks' | 'clauses'>('chunks');
  const [chunks, setChunks] = useState<ChunkInfo[]>([]);
  const [clauses, setClauses] = useState<ClauseInfo[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const selectedContract = contracts.find((c) => c.id === targetId);

  useEffect(() => {
    if (!targetId) return;

    let isMounted = true;
    const loadEvidence = async () => {
      setLoading(true);
      setError(null);
      try {
        const [chunksData, clausesData] = await Promise.all([
          api.getContractChunks(targetId).catch(() => []),
          api.getClauses(targetId).catch(() => []),
        ]);
        if (isMounted) {
          setChunks(chunksData);
          setClauses(clausesData);
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || 'Failed to load document evidence data.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadEvidence();

    return () => {
      isMounted = false;
    };
  }, [targetId]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      
      {/* Header Banner */}
      <div className="card-glass card-gold-border">
        <h2 className="serif-title" style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          Document Source & Evidence Inspector
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Inspect raw parsed document text, chunk page offsets, and verification evidence for grounding AI responses.
        </p>
      </div>

      {/* Contract Selector Controls */}
      <div className="card-glass" style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: '240px' }}>
          <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', display: 'block', marginBottom: '0.35rem' }}>
            Select Contract Document
          </label>
          <select
            className="input-legal"
            value={targetId}
            onChange={(e) => {
              setTargetId(e.target.value);
              onSelectContract(e.target.value);
            }}
          >
            <option value="">Select Contract...</option>
            {contracts.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.contract_type || 'Contract'})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Selected Contract Evidence Workspace */}
      {!selectedContract ? (
        <div className="empty-state">
          <div className="empty-state-icon">🔬</div>
          <h4 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Select a Contract Document</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Choose a contract from the dropdown above to inspect source text chunks and document metadata.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* Document Overview Metadata */}
          <div className="card-glass" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.25rem' }}>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase' }}>Document Name</div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-gold)', marginTop: '0.25rem' }}>
                {selectedContract.name}
              </div>
            </div>

            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase' }}>Contract Category</div>
              <div style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-primary)', marginTop: '0.25rem' }}>
                {selectedContract.contract_type || 'General Contract'}
              </div>
            </div>

            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase' }}>Ingestion Status</div>
              <div style={{ marginTop: '0.25rem' }}>
                <span className="badge badge-success">
                  <span className="status-dot" /> {selectedContract.status}
                </span>
              </div>
            </div>

            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase' }}>Document ID</div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.25rem', fontFamily: 'monospace' }}>
                {selectedContract.id}
              </div>
            </div>
          </div>

          {/* Tab Selector */}
          <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
            <button
              className={activeTab === 'chunks' ? 'btn-gold' : 'btn-secondary'}
              style={{ padding: '0.5rem 1.25rem', fontSize: '0.85rem' }}
              onClick={() => setActiveTab('chunks')}
            >
              📄 Raw Document Chunks ({chunks.length})
            </button>
            <button
              className={activeTab === 'clauses' ? 'btn-gold' : 'btn-secondary'}
              style={{ padding: '0.5rem 1.25rem', fontSize: '0.85rem' }}
              onClick={() => setActiveTab('clauses')}
            >
              📑 Extracted Clauses ({clauses.length})
            </button>
          </div>

          {error && (
            <div style={{ background: 'var(--accent-rose-bg)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#f87171', padding: '1rem', borderRadius: '0.5rem', fontSize: '0.9rem' }}>
              ⚠️ {error}
            </div>
          )}

          {loading ? (
            <div className="card-glass skeleton" style={{ height: '200px' }} />
          ) : activeTab === 'chunks' ? (
            /* Raw Chunks Tab */
            <div className="card-glass">
              <h4 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '1.25rem' }}>
                Parsed Vector Chunks ({chunks.length})
              </h4>

              {chunks.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', padding: '2rem 1rem' }}>
                  No vector chunks found for this contract.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {chunks.map((chk, idx) => (
                    <div key={chk.id || chk.chunk_id || idx} style={{
                      background: 'rgba(7, 9, 14, 0.8)',
                      border: '1px solid var(--border-color)',
                      borderRadius: '0.6rem',
                      padding: '1.25rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.75rem'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span className="badge badge-gold">
                          Chunk #{chk.chunk_index !== undefined ? chk.chunk_index : idx + 1}
                        </span>
                        <span className="badge badge-info">
                          Page {chk.page_start} {chk.page_end !== chk.page_start ? `- ${chk.page_end}` : ''}
                        </span>
                        {chk.section && chk.section !== 'General' && (
                          <span className="badge badge-purple">{chk.section}</span>
                        )}
                      </div>

                      <div style={{
                        fontSize: '0.9rem',
                        lineHeight: 1.6,
                        color: '#e2e8f0',
                        fontFamily: 'Consolas, monospace',
                        maxHeight: '160px',
                        overflowY: 'auto',
                        whiteSpace: 'pre-wrap',
                      }}>
                        {chk.text}
                      </div>

                      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                        <button
                          className="btn-secondary"
                          style={{ fontSize: '0.75rem', padding: '0.3rem 0.65rem' }}
                          onClick={() => onOpenEvidence({
                            contractName: selectedContract.name,
                            section: chk.section || 'General',
                            pageStart: chk.page_start,
                            pageEnd: chk.page_end,
                            text: chk.text,
                            chunkId: chk.id || chk.chunk_id,
                          })}
                        >
                          🔬 Launch Evidence Inspector Modal
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            /* Extracted Clauses Tab */
            <div className="card-glass">
              <h4 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '1.25rem' }}>
                Extracted Contractual Provisions & Evidence ({clauses.length})
              </h4>

              {clauses.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', padding: '2rem 1rem' }}>
                  No clause evidence extracted for this contract yet. Navigate to Clause Taxonomy or Contract Details to extract clauses.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {clauses.map((clause) => (
                    <div key={clause.id} style={{
                      background: 'rgba(7, 9, 14, 0.8)',
                      border: '1px solid var(--border-color)',
                      borderRadius: '0.6rem',
                      padding: '1.25rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.75rem'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span className="badge badge-gold">{clause.clause_type}</span>
                        <span className="badge badge-info">Page {clause.page_number}</span>
                        {clause.confidence && (
                          <span className="badge badge-success">
                            {Math.round(clause.confidence * 100)}% Confidence
                          </span>
                        )}
                      </div>

                      <div style={{
                        fontSize: '0.9rem',
                        lineHeight: 1.6,
                        color: '#e2e8f0',
                        fontFamily: 'Consolas, monospace',
                      }}>
                        {clause.text}
                      </div>

                      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                        <button
                          className="btn-secondary"
                          style={{ fontSize: '0.75rem', padding: '0.3rem 0.65rem' }}
                          onClick={() => onOpenEvidence({
                            contractName: selectedContract.name,
                            section: clause.clause_type,
                            pageStart: clause.page_number,
                            text: clause.text,
                            similarityScore: clause.confidence,
                          })}
                        >
                          🔬 Launch Evidence Inspector Modal
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

        </div>
      )}

    </div>
  );
};
