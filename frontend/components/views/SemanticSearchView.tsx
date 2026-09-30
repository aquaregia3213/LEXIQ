'use client';

import React, { useState, useEffect } from 'react';
import { api, ContractItem, SearchResponse, SearchResultItem } from '../../lib/api';

interface SemanticSearchViewProps {
  contracts: ContractItem[];
  selectedContractId: string;
  onOpenEvidence: (evidence: any) => void;
  onSelectContract: (contractId: string) => void;
}

export const SemanticSearchView: React.FC<SemanticSearchViewProps> = ({
  contracts,
  selectedContractId,
  onOpenEvidence,
  onSelectContract,
}) => {
  const [query, setQuery] = useState<string>('automatic renewal provisions');
  const [contractIdFilter, setContractIdFilter] = useState<string>(selectedContractId || '');
  const [contractTypeFilter, setContractTypeFilter] = useState<string>('');
  const [sectionFilter, setSectionFilter] = useState<string>('');
  const [topK, setTopK] = useState<number>(5);
  const [minScore, setMinScore] = useState<number>(0.0);

  const [loading, setLoading] = useState<boolean>(false);
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const presetQueries = [
    'contracts with automatic renewal',
    'limitation of liability cap limits',
    'indemnification obligations and scope',
    'governing law and jurisdiction Delaware',
    'confidentiality term and return of data',
    'termination for convenience notice period',
  ];

  const handleExecuteSearch = async (searchQuery?: string) => {
    const q = searchQuery !== undefined ? searchQuery : query;
    if (!q.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const res = await api.performSearch({
        query: q,
        contract_id: contractIdFilter || undefined,
        contract_type: contractTypeFilter || undefined,
        section: sectionFilter || undefined,
        top_k: topK,
        min_score: minScore,
      });
      setSearchResponse(res);
    } catch (err: any) {
      setError(err.message || 'Semantic vector search failed.');
      setSearchResponse(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Perform initial search on mount
    handleExecuteSearch();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      
      {/* Header Card */}
      <div className="card-glass card-gold-border">
        <h2 className="serif-title" style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          pgvector Semantic Retrieval Engine
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Search contract repository using natural language conceptual queries rather than strict keyword matching. Returns dense vector matching chunks grounded in source contracts.
        </p>
      </div>

      {/* Search Input & Controls Bar */}
      <div className="card-glass" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleExecuteSearch();
          }}
          style={{ display: 'flex', gap: '0.75rem' }}
        >
          <div style={{ flex: 1 }}>
            <input
              type="text"
              className="input-legal"
              placeholder="Enter natural language query e.g. 'What is the liability cap limit?'..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              style={{ fontSize: '1.05rem', padding: '0.85rem 1.2rem' }}
            />
          </div>
          <button type="submit" className="btn-gold" disabled={loading || !query.trim()}>
            {loading ? 'Searching...' : '🔍 Search Vectors'}
          </button>
        </form>

        {/* Preset Query Chips */}
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.5rem' }}>
            Recommended Legal Queries
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {presetQueries.map((pq) => (
              <button
                key={pq}
                onClick={() => {
                  setQuery(pq);
                  handleExecuteSearch(pq);
                }}
                style={{
                  background: query === pq ? 'var(--accent-gold-bg)' : 'rgba(13, 17, 26, 0.8)',
                  border: query === pq ? '1px solid var(--border-gold)' : '1px solid var(--border-color)',
                  color: query === pq ? 'var(--text-gold)' : 'var(--text-secondary)',
                  padding: '0.35rem 0.75rem',
                  borderRadius: '999px',
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
              >
                {pq}
              </button>
            ))}
          </div>
        </div>

        {/* Advanced Filters Drawer */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1rem',
          paddingTop: '1rem',
          borderTop: '1px solid var(--border-color)',
        }}>
          <div>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', display: 'block', marginBottom: '0.35rem' }}>
              Scope Contract
            </label>
            <select
              className="input-legal"
              style={{ padding: '0.5rem', fontSize: '0.85rem' }}
              value={contractIdFilter}
              onChange={(e) => setContractIdFilter(e.target.value)}
            >
              <option value="">All Repository Contracts</option>
              {contracts.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', display: 'block', marginBottom: '0.35rem' }}>
              Top K Chunks: {topK}
            </label>
            <input
              type="range"
              min="1"
              max="20"
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--accent-gold)' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', display: 'block', marginBottom: '0.35rem' }}>
              Min Similarity: {(minScore * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="0"
              max="0.9"
              step="0.05"
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--accent-gold)' }}
            />
          </div>
        </div>

      </div>

      {/* Error Alert */}
      {error && (
        <div style={{ background: 'var(--accent-rose-bg)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#f87171', padding: '1rem', borderRadius: '0.5rem', fontSize: '0.9rem' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Search Results List */}
      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card-glass skeleton" style={{ height: '120px' }} />
          <div className="card-glass skeleton" style={{ height: '120px' }} />
        </div>
      ) : searchResponse && searchResponse.results.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🔍</div>
          <h4 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>No Vector Matches Found</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            No contract chunks matched query "{searchResponse.query}" above the similarity threshold of {(minScore * 100).toFixed(0)}%.
          </p>
        </div>
      ) : searchResponse ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Found <strong style={{ color: 'var(--text-gold)' }}>{searchResponse.result_count}</strong> matching vector chunks for query "{searchResponse.query}":
          </div>

          {searchResponse.results.map((item: SearchResultItem, index: number) => {
            const scorePct = Math.round(item.similarity_score * 100);
            return (
              <div key={item.chunk_id || index} className="card-glass" style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span
                      onClick={() => onSelectContract(item.contract_id)}
                      style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--text-gold)', cursor: 'pointer' }}
                    >
                      {item.contract_name || item.file_name}
                    </span>
                    {item.section && (
                      <span className="badge badge-info" style={{ fontSize: '0.75rem' }}>
                        {item.section}
                      </span>
                    )}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span className="badge badge-gold">
                      Page {item.page_start} {item.page_end !== item.page_start ? `- ${item.page_end}` : ''}
                    </span>
                    <span className={`badge ${scorePct >= 75 ? 'badge-success' : 'badge-warning'}`}>
                      {scorePct}% Similarity
                    </span>
                  </div>
                </div>

                <div style={{
                  background: 'rgba(7, 9, 14, 0.8)',
                  padding: '1rem',
                  borderRadius: '0.5rem',
                  fontSize: '0.9rem',
                  lineHeight: 1.6,
                  color: '#e2e8f0',
                  fontFamily: 'Consolas, monospace',
                  border: '1px solid var(--border-color)',
                }}>
                  {item.text}
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <button
                    className="btn-secondary"
                    style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem' }}
                    onClick={() => onOpenEvidence({
                      contractName: item.contract_name,
                      fileName: item.file_name,
                      pageStart: item.page_start,
                      pageEnd: item.page_end,
                      section: item.section,
                      text: item.text,
                      similarityScore: item.similarity_score,
                      chunkId: item.chunk_id,
                    })}
                  >
                    🔬 Inspect Source Evidence
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      ) : null}

    </div>
  );
};
