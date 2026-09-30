'use client';

import React, { useState, useEffect } from 'react';
import { api, ContractItem, EntityInfo } from '../../lib/api';

interface EntityViewProps {
  contracts: ContractItem[];
  selectedContractId: string;
  onSelectContract: (contractId: string) => void;
}

export const EntityView: React.FC<EntityViewProps> = ({
  contracts,
  selectedContractId,
  onSelectContract,
}) => {
  const [contractIdFilter, setContractIdFilter] = useState<string>(selectedContractId || '');
  const [typeFilter, setTypeFilter] = useState<string>('');
  
  const [entities, setEntities] = useState<EntityInfo[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [extracting, setExtracting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAllEntities = async () => {
    setLoading(true);
    setError(null);
    try {
      if (contractIdFilter) {
        const data = await api.getEntities(contractIdFilter);
        setEntities(data);
      } else {
        // Aggregate entities across all contracts
        const all: EntityInfo[] = [];
        for (const c of contracts) {
          if (c.entities && c.entities.length > 0) {
            all.push(...c.entities);
          } else {
            try {
              const res = await api.getEntities(c.id);
              all.push(...res);
            } catch {}
          }
        }
        setEntities(all);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch contract entities.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllEntities();
  }, [contractIdFilter, contracts]);

  const handleTriggerExtraction = async () => {
    if (!contractIdFilter) {
      alert('Please select a specific contract to trigger entity extraction.');
      return;
    }

    setExtracting(true);
    try {
      const result = await api.extractEntities(contractIdFilter);
      setEntities(result);
    } catch (err: any) {
      alert(`Entity extraction failed: ${err.message}`);
    } finally {
      setExtracting(false);
    }
  };

  const filteredEntities = entities.filter((e) => {
    if (!typeFilter) return true;
    const eType = e.entity_type.toUpperCase();
    const fType = typeFilter.toUpperCase();
    if (fType === 'PARTY' || fType === 'COMPANY') {
      return eType === 'PARTY' || eType === 'COMPANY';
    }
    if (fType === 'MONETARY_VALUE' || fType === 'MONETARY_AMOUNT' || fType === 'AMOUNT') {
      return eType === 'MONETARY_VALUE' || eType === 'MONETARY_AMOUNT' || eType === 'AMOUNT';
    }
    return eType === fType;
  });

  const getEntityBadgeStyle = (type: string) => {
    switch (type.toUpperCase()) {
      case 'PARTY': case 'COMPANY': return 'badge-gold';
      case 'JURISDICTION': return 'badge-purple';
      case 'MONETARY_VALUE': case 'AMOUNT': return 'badge-success';
      case 'DATE': return 'badge-info';
      case 'PERSON': return 'badge-warning';
      default: return 'badge-info';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      
      {/* Header Banner */}
      <div className="card-glass card-gold-border" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 className="serif-title" style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '0.25rem' }}>
            Named Entity Recognition (NER)
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Extracted corporate entities, signatories, governing jurisdictions, execution dates, and monetary figures.
          </p>
        </div>

        {contractIdFilter && (
          <button className="btn-gold" onClick={handleTriggerExtraction} disabled={extracting}>
            {extracting ? 'Extracting...' : '⚡ Trigger Entity Extractor'}
          </button>
        )}
      </div>

      {/* Filter Controls */}
      <div className="card-glass" style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ flex: 1, minWidth: '220px' }}>
          <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', display: 'block', marginBottom: '0.35rem' }}>
            Filter Contract Scope
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
            Entity Category
          </label>
          <select
            className="input-legal"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="">All Entity Categories ({entities.length})</option>
            <option value="COMPANY">Parties & Companies</option>
            <option value="JURISDICTION">Jurisdictions</option>
            <option value="DATE">Dates & Deadlines</option>
            <option value="MONETARY_AMOUNT">Monetary Figures</option>
            <option value="PERSON">Signatories & People</option>
          </select>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div style={{ background: 'var(--accent-rose-bg)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#f87171', padding: '1rem', borderRadius: '0.5rem', fontSize: '0.9rem' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Entity Grid */}
      {loading ? (
        <div className="card-glass skeleton" style={{ height: '200px' }} />
      ) : filteredEntities.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🏢</div>
          <h4 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>No Extracted Entities Found</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', maxWidth: '440px', margin: '0 auto 1.5rem' }}>
            {typeFilter
              ? `No entities matching category "${typeFilter}".`
              : 'Entities have not been extracted for the selected contract scope. Trigger entity extraction to process.'}
          </p>
          {contractIdFilter && (
            <button className="btn-gold" onClick={handleTriggerExtraction} disabled={extracting}>
              ⚡ Trigger Entity Extractor Now
            </button>
          )}
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
          {filteredEntities.map((entity) => {
            const parentContract = contracts.find((c) => c.id === entity.contract_id);
            const confPct = Math.round(entity.confidence * 100);

            return (
              <div key={entity.id} className="card-glass" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                    <span className={`badge ${getEntityBadgeStyle(entity.entity_type)}`}>
                      {entity.entity_type}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {confPct}% Confidence
                    </span>
                  </div>

                  <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
                    {entity.name}
                  </div>

                  {entity.normalized_name && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-gold)' }}>
                      Normalized: {entity.normalized_name}
                    </div>
                  )}
                </div>

                {parentContract && (
                  <div style={{
                    marginTop: '1rem',
                    paddingTop: '0.75rem',
                    borderTop: '1px solid var(--border-color)',
                    fontSize: '0.8rem',
                    color: 'var(--text-muted)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '180px' }}>
                      {parentContract.name}
                    </span>
                    <button
                      className="btn-secondary"
                      style={{ fontSize: '0.7rem', padding: '0.2rem 0.5rem' }}
                      onClick={() => onSelectContract(parentContract.id)}
                    >
                      View →
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

    </div>
  );
};
