'use client';

import React, { useState, useEffect } from 'react';
import { api, ContractItem, ClauseInfo } from '../../lib/api';

interface ClauseViewProps {
  contracts: ContractItem[];
  selectedContractId: string;
  onOpenEvidence: (evidence: any) => void;
  onSelectContract: (contractId: string) => void;
}

export const ClauseView: React.FC<ClauseViewProps> = ({
  contracts,
  selectedContractId,
  onOpenEvidence,
  onSelectContract,
}) => {
  const [contractIdFilter, setContractIdFilter] = useState<string>(selectedContractId || '');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  
  const [clauses, setClauses] = useState<ClauseInfo[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [extracting, setExtracting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const clauseCategories = [
    'Termination',
    'Limitation of Liability',
    'Indemnification',
    'Confidentiality',
    'Payment Terms',
    'Intellectual Property',
    'Non-Compete',
    'Governing Law',
    'Dispute Resolution',
    'Renewal',
    'Data Protection',
    'Warranty',
    'Force Majeure',
    'Assignment',
  ];

  const fetchAllClauses = async () => {
    setLoading(true);
    setError(null);
    try {
      if (contractIdFilter) {
        const data = await api.getClauses(contractIdFilter);
        setClauses(data);
      } else {
        // Aggregate across all contracts
        const all: ClauseInfo[] = [];
        for (const c of contracts) {
          if (c.clauses && c.clauses.length > 0) {
            all.push(...c.clauses);
          } else {
            try {
              const res = await api.getClauses(c.id);
              all.push(...res);
            } catch {}
          }
        }
        setClauses(all);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch contract clauses.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllClauses();
  }, [contractIdFilter, contracts]);

  const handleTriggerExtraction = async () => {
    if (!contractIdFilter) {
      alert('Please select a specific contract to trigger clause extraction.');
      return;
    }

    setExtracting(true);
    try {
      const result = await api.extractClauses(contractIdFilter);
      setClauses(result);
    } catch (err: any) {
      alert(`Clause extraction failed: ${err.message}`);
    } finally {
      setExtracting(false);
    }
  };

  // Filter clauses by category
  const filteredClauses = clauses.filter((c) => {
    if (!categoryFilter) return true;
    const cType = c.clause_type.toLowerCase();
    const fType = categoryFilter.toLowerCase();
    return cType === fType || cType.includes(fType) || fType.includes(cType);
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      
      {/* Header Banner */}
      <div className="card-glass card-gold-border" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 className="serif-title" style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '0.25rem' }}>
            Clause Taxonomy & Intelligence
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Extracted and classified contract provisions categorized across standard legal taxonomies.
          </p>
        </div>

        {contractIdFilter && (
          <button className="btn-gold" onClick={handleTriggerExtraction} disabled={extracting}>
            {extracting ? 'Extracting...' : '⚡ Trigger Clause Classifier'}
          </button>
        )}
      </div>

      {/* Filter Toolbar */}
      <div className="card-glass" style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center' }}>
        <div style={{ flex: 1, minWidth: '220px' }}>
          <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', display: 'block', marginBottom: '0.35rem' }}>
            Filter Contract
          </label>
          <select
            className="input-legal"
            value={contractIdFilter}
            onChange={(e) => setContractIdFilter(e.target.value)}
          >
            <option value="">All Repository Contracts ({contracts.length})</option>
            {contracts.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        <div style={{ flex: 1, minWidth: '220px' }}>
          <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', display: 'block', marginBottom: '0.35rem' }}>
            Clause Category
          </label>
          <select
            className="input-legal"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <option value="">All Clause Categories ({clauses.length})</option>
            {clauseCategories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div style={{ background: 'var(--accent-rose-bg)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#f87171', padding: '1rem', borderRadius: '0.5rem', fontSize: '0.9rem' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Clauses Cards List */}
      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card-glass skeleton" style={{ height: '140px' }} />
          <div className="card-glass skeleton" style={{ height: '140px' }} />
        </div>
      ) : filteredClauses.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📜</div>
          <h4 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>No Classified Clauses Found</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', maxWidth: '440px', margin: '0 auto 1.5rem' }}>
            {categoryFilter
              ? `No clauses found matching category "${categoryFilter}".`
              : 'Clauses have not been extracted for the selected scope yet. Select a contract and trigger the clause classifier.'}
          </p>
          {contractIdFilter && (
            <button className="btn-gold" onClick={handleTriggerExtraction} disabled={extracting}>
              ⚡ Trigger Clause Classifier Now
            </button>
          )}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {filteredClauses.map((clause) => {
            const parentContract = contracts.find((c) => c.id === clause.contract_id);
            const confPct = Math.round(clause.confidence * 100);

            return (
              <div key={clause.id} className="card-glass" style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <span className="badge badge-gold">{clause.clause_type}</span>
                    {parentContract && (
                      <span
                        onClick={() => onSelectContract(parentContract.id)}
                        style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', cursor: 'pointer' }}
                      >
                        {parentContract.name}
                      </span>
                    )}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span className="badge badge-info">
                      Page {clause.page_number}
                    </span>
                    <span className={`badge ${confPct >= 80 ? 'badge-success' : 'badge-warning'}`}>
                      {confPct}% Confidence
                    </span>
                  </div>
                </div>

                {/* Clause Verbatim Text */}
                <div style={{
                  background: 'rgba(7, 9, 14, 0.8)',
                  padding: '1.25rem',
                  borderRadius: '0.5rem',
                  fontSize: '0.9rem',
                  lineHeight: 1.6,
                  color: '#e2e8f0',
                  fontFamily: 'Consolas, monospace',
                  border: '1px solid var(--border-color)',
                }}>
                  {clause.text}
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <button
                    className="btn-secondary"
                    style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem' }}
                    onClick={() => onOpenEvidence({
                      contractName: parentContract?.name,
                      section: clause.clause_type,
                      pageStart: clause.page_number,
                      text: clause.text,
                      similarityScore: clause.confidence,
                    })}
                  >
                    🔬 Inspect Source Evidence
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

    </div>
  );
};
