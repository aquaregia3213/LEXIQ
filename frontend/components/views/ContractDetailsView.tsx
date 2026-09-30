'use client';

import React, { useState, useEffect } from 'react';
import { ContractItem, ClauseInfo, EntityInfo, RiskAnalysisResponse, SubgraphResponse, api } from '../../lib/api';
import { KnowledgeGraphViewer } from '../KnowledgeGraphViewer';

interface ContractDetailsViewProps {
  contractId: string;
  onNavigateToAsk: (contractId: string) => void;
  onNavigateToSearch: (contractId: string) => void;
  onNavigateToAgent: (contractId: string) => void;
  onOpenEvidence: (evidence: any) => void;
}

export const ContractDetailsView: React.FC<ContractDetailsViewProps> = ({
  contractId,
  onNavigateToAsk,
  onNavigateToSearch,
  onNavigateToAgent,
  onOpenEvidence,
}) => {
  const [contract, setContract] = useState<ContractItem | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'clauses' | 'entities' | 'risks' | 'graph'>('overview');
  
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Tab Data States
  const [clauses, setClauses] = useState<ClauseInfo[]>([]);
  const [entities, setEntities] = useState<EntityInfo[]>([]);
  const [risksData, setRisksData] = useState<RiskAnalysisResponse | null>(null);
  const [graphData, setGraphData] = useState<SubgraphResponse | null>(null);

  const fetchContractDetails = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getContract(contractId);
      setContract(data);
      setClauses(data.clauses || []);
      setEntities(data.entities || []);
      
      // Fetch risk & graph if available
      try {
        const rData = await api.getRisks(contractId);
        setRisksData(rData);
      } catch {}

      try {
        const gData = await api.getGraph(contractId);
        setGraphData(gData);
      } catch {}
    } catch (err: any) {
      setError(err.message || `Failed to load details for contract ID ${contractId}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (contractId) {
      fetchContractDetails();
    }
  }, [contractId]);

  // Action Triggers
  const handleExtractClauses = async () => {
    setActionLoading('Extracting Clauses...');
    try {
      const updatedClauses = await api.extractClauses(contractId);
      setClauses(updatedClauses);
      setActiveTab('clauses');
    } catch (err: any) {
      alert(`Clause extraction failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleExtractEntities = async () => {
    setActionLoading('Extracting Entities...');
    try {
      const updatedEntities = await api.extractEntities(contractId);
      setEntities(updatedEntities);
      setActiveTab('entities');
    } catch (err: any) {
      alert(`Entity extraction failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleAnalyzeRisks = async () => {
    setActionLoading('Analyzing Contract Risks...');
    try {
      const updatedRisks = await api.analyzeRisks(contractId);
      setRisksData(updatedRisks);
      setActiveTab('risks');
    } catch (err: any) {
      alert(`Risk analysis failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleSyncGraph = async () => {
    setActionLoading('Syncing Knowledge Graph...');
    try {
      const updatedGraph = await api.syncGraph(contractId);
      setGraphData(updatedGraph);
      setActiveTab('graph');
    } catch (err: any) {
      alert(`Graph sync failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="card-glass" style={{ padding: '3rem' }}>
        <div className="skeleton" style={{ height: '30px', width: '40%', marginBottom: '1rem' }} />
        <div className="skeleton" style={{ height: '150px', width: '100%', marginBottom: '1.5rem' }} />
        <div className="skeleton" style={{ height: '200px', width: '100%' }} />
      </div>
    );
  }

  if (error || !contract) {
    return (
      <div className="card-glass" style={{ textAlign: 'center', padding: '3rem 2rem' }}>
        <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>⚠️</div>
        <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem', color: '#f87171' }}>
          Contract Not Found
        </h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
          {error || 'Unable to retrieve contract record from backend.'}
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      
      {/* Contract Header Banner */}
      <div className="card-glass card-gold-border">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <span className="badge badge-gold">{contract.contract_type || 'Contract'}</span>
              <span className="badge badge-success"><span className="status-dot" /> {contract.status}</span>
            </div>
            <h2 className="serif-title" style={{ fontSize: '2rem', fontWeight: 700 }}>
              {contract.name}
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              Contract ID: {contract.id} • Uploaded: {new Date(contract.created_at).toLocaleString()}
            </p>
          </div>

          {/* Quick AI Trigger Buttons */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            <button className="btn-gold" style={{ fontSize: '0.8rem', fontWeight: 600 }} onClick={() => onNavigateToAgent(contract.id)}>
              🤖 AI Analyst
            </button>
            <button className="btn-secondary" style={{ fontSize: '0.8rem' }} onClick={() => onNavigateToAsk(contract.id)}>
              💬 Ask RAG AI
            </button>
            <button className="btn-secondary" style={{ fontSize: '0.8rem' }} onClick={() => onNavigateToSearch(contract.id)}>
              🔍 Search Chunks
            </button>
          </div>
        </div>

        {/* Action Pipeline Toolbar */}
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '0.75rem',
          marginTop: '1.5rem',
          paddingTop: '1.25rem',
          borderTop: '1px solid var(--border-color)'
        }}>
          <button className="btn-gold" style={{ fontSize: '0.85rem' }} disabled={!!actionLoading} onClick={handleExtractClauses}>
            {actionLoading === 'Extracting Clauses...' ? 'Extracting...' : '📜 Extract Clauses'}
          </button>
          <button className="btn-gold" style={{ fontSize: '0.85rem' }} disabled={!!actionLoading} onClick={handleExtractEntities}>
            {actionLoading === 'Extracting Entities...' ? 'Extracting...' : '🏢 Extract Entities'}
          </button>

          <button className="btn-gold" style={{ fontSize: '0.85rem' }} disabled={!!actionLoading} onClick={handleAnalyzeRisks}>
            {actionLoading === 'Analyzing Contract Risks...' ? 'Analyzing...' : '🛡️ Analyze Contract Risks'}
          </button>

          <button className="btn-secondary" style={{ fontSize: '0.85rem' }} disabled={!!actionLoading} onClick={handleSyncGraph}>
            {actionLoading === 'Syncing Knowledge Graph...' ? 'Syncing...' : '🌐 Sync Knowledge Graph'}
          </button>
        </div>
      </div>

      {/* Sub-Tab Navigation Bar */}
      <div style={{
        display: 'flex',
        gap: '0.5rem',
        borderBottom: '1px solid var(--border-color)',
        paddingBottom: '0.5rem',
        overflowX: 'auto'
      }}>
        {[
          { id: 'overview', label: 'Overview & Files', count: contract.documents?.length },
          { id: 'clauses', label: 'Clauses', count: clauses.length },
          { id: 'entities', label: 'Entities', count: entities.length },
          { id: 'risks', label: 'Risk Analysis', count: risksData?.risk_count },
          { id: 'graph', label: 'Knowledge Graph', count: graphData?.nodes?.length },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            style={{
              padding: '0.6rem 1.25rem',
              borderRadius: '0.5rem',
              border: 'none',
              background: activeTab === tab.id ? 'var(--accent-gold-bg)' : 'transparent',
              color: activeTab === tab.id ? 'var(--text-gold)' : 'var(--text-secondary)',
              fontWeight: activeTab === tab.id ? 700 : 500,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              transition: 'all 0.2s ease',
            }}
          >
            <span>{tab.label}</span>
            {tab.count !== undefined && (
              <span className="badge badge-info" style={{ padding: '0.1rem 0.4rem', fontSize: '0.7rem' }}>
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content Panels */}
      
      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
          <div className="card-glass">
            <h4 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>Document Properties</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.9rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Original File</span>
                <span style={{ fontWeight: 600 }}>{contract.documents?.[0]?.file_name || contract.name}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>Page Count</span>
                <span style={{ fontWeight: 600 }}>{contract.documents?.[0]?.page_count || 1} Pages</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>File Format</span>
                <span style={{ fontWeight: 600, textTransform: 'uppercase' }}>{contract.documents?.[0]?.file_type || 'PDF'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Parsing Status</span>
                <span style={{ color: '#34d399', fontWeight: 600 }}>{contract.status}</span>
              </div>
            </div>
          </div>

          <div className="card-glass">
            <h4 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>Extraction Overview</h4>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.9rem' }}>
              <li style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>📜 Extracted Clauses</span>
                <span className="badge badge-gold">{clauses.length} Clauses</span>
              </li>
              <li style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>🏢 Recognized Entities</span>
                <span className="badge badge-info">{entities.length} Entities</span>
              </li>
              <li style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>🛡️ Identified Risk Flags</span>
                <span className="badge badge-danger">{risksData?.risk_count || 0} Risks</span>
              </li>
            </ul>
          </div>
        </div>
      )}

      {/* Clauses Tab */}
      {activeTab === 'clauses' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {clauses.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📜</div>
              <h4>No Extracted Clauses</h4>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1rem' }}>
                Trigger the clause classification pipeline to extract contract provisions.
              </p>
              <button className="btn-gold" onClick={handleExtractClauses}>
                ⚡ Extract Clauses Now
              </button>
            </div>
          ) : (
            clauses.map((clause) => (
              <div key={clause.id} className="card-glass" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span className="badge badge-gold">{clause.clause_type}</span>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Page {clause.page_number} • Confidence: {(clause.confidence * 100).toFixed(0)}%
                  </div>
                </div>
                <div style={{
                  background: 'rgba(7, 9, 14, 0.8)',
                  padding: '1rem',
                  borderRadius: '0.5rem',
                  fontSize: '0.9rem',
                  lineHeight: 1.6,
                  fontFamily: 'Consolas, monospace',
                  border: '1px solid var(--border-color)',
                }}>
                  {clause.text}
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <button
                    className="btn-secondary"
                    style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
                    onClick={() => onOpenEvidence({
                      contractName: contract.name,
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
            ))
          )}
        </div>
      )}

      {/* Entities Tab */}
      {activeTab === 'entities' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {entities.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">🏢</div>
              <h4>No Extracted Entities</h4>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1rem' }}>
                Trigger entity extraction to identify companies, dates, monetary values, and jurisdictions.
              </p>
              <button className="btn-gold" onClick={handleExtractEntities}>
                ⚡ Extract Entities Now
              </button>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
              {entities.map((ent) => (
                <div key={ent.id} className="card-glass">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span className="badge badge-purple">{ent.entity_type}</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{(ent.confidence * 100).toFixed(0)}%</span>
                  </div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>{ent.name}</div>
                  {ent.normalized_name && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-gold)', marginTop: '0.2rem' }}>
                      Norm: {ent.normalized_name}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Risks Tab */}
      {activeTab === 'risks' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {!risksData || risksData.risks.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">🛡️</div>
              <h4>No Risk Flags Analyzed</h4>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1rem' }}>
                Run automated risk analysis to flag unusual liabilities or automatic renewals.
              </p>
              <button className="btn-gold" onClick={handleAnalyzeRisks}>
                ⚡ Analyze Contract Risks
              </button>
            </div>
          ) : (
            risksData.risks.map((risk) => (
              <div key={risk.id} className="card-glass" style={{ borderLeft: '4px solid #f87171' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <span className="badge badge-danger">{risk.risk_type}</span>
                  <span className="badge badge-warning">{risk.severity} SEVERITY</span>
                </div>
                <div style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                  {risk.description}
                </div>
                {risk.evidence && (
                  <div style={{ background: 'rgba(7, 9, 14, 0.8)', padding: '0.85rem', borderRadius: '0.4rem', fontSize: '0.85rem', fontFamily: 'Consolas, monospace', color: '#fca5a5' }}>
                    "{risk.evidence}"
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Knowledge Graph Tab */}
      {activeTab === 'graph' && (
        <KnowledgeGraphViewer
          graphData={graphData}
          loading={loading}
          onSyncGraph={handleSyncGraph}
        />
      )}

    </div>
  );
};
