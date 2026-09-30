'use client';

import React, { useState, useEffect } from 'react';
import { api, ContractItem, AgentQueryResponse, AgentFinding, AgentSourceCitation } from '../../lib/api';

interface AgentViewProps {
  contracts: ContractItem[];
  selectedContractId?: string;
  onSelectContract?: (contractId: string) => void;
  onOpenEvidence: (evidence: any) => void;
}

const SUGGESTED_QUESTIONS = [
  'What are the biggest risks in this contract?',
  'What are the termination conditions and notice periods?',
  'What obligations does the vendor have?',
  'Are there unusual or uncapped liability clauses?',
  'What happens if the contract automatically renews?',
  'Summarize the confidentiality and non-disclosure obligations.',
];

const LOADING_STATUS_STEPS = [
  'Analyzing legal query intent...',
  'Selecting contract analysis tools...',
  'Searching clauses and document chunks...',
  'Analyzing risk flags and obligations...',
  'Verifying source evidence and citations...',
  'Synthesizing grounded legal answer...',
];

export const AgentView: React.FC<AgentViewProps> = ({
  contracts,
  selectedContractId,
  onSelectContract,
  onOpenEvidence,
}) => {
  const [targetContractId, setTargetContractId] = useState<string>(selectedContractId || '');
  const [question, setQuestion] = useState<string>('');
  
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingStepIndex, setLoadingStepIndex] = useState<number>(0);
  const [response, setResponse] = useState<AgentQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Sync selected contract from props
  useEffect(() => {
    if (selectedContractId) {
      setTargetContractId(selectedContractId);
    }
  }, [selectedContractId]);

  // Rotate high-level safe activity status messages during loading
  useEffect(() => {
    if (!loading) {
      setLoadingStepIndex(0);
      return;
    }
    const interval = setInterval(() => {
      setLoadingStepIndex((prev) => (prev + 1) % LOADING_STATUS_STEPS.length);
    }, 1800);
    return () => clearInterval(interval);
  }, [loading]);

  const handleRunAgent = async (overrideQuestion?: string) => {
    const q = (overrideQuestion || question).trim();
    if (!q) {
      setError('Please enter a question or legal inquiry.');
      return;
    }

    setLoading(true);
    setError(null);
    if (overrideQuestion) {
      setQuestion(overrideQuestion);
    }

    try {
      const result = await api.queryAgent({
        question: q,
        contract_id: targetContractId || null,
        max_steps: 5,
      });
      setResponse(result);
    } catch (err: any) {
      console.error('Agent query failed:', err);
      setError(
        err.message ||
        'The Autonomous Legal Agent was unable to complete the analysis. Please verify backend connection and try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const mapToolLabel = (toolName: string): { label: string; icon: string } => {
    switch (toolName) {
      case 'search_contract':
        return { label: 'Semantic Vector Search', icon: '🔍' };
      case 'get_contract':
        return { label: 'Contract Metadata', icon: '📁' };
      case 'get_clauses':
        return { label: 'Clause Intelligence', icon: '📜' };
      case 'get_entities':
        return { label: 'Entity Extraction', icon: '🏢' };
      case 'get_obligations':
        return { label: 'Obligation Tracking', icon: '⚖️' };
      case 'get_risks':
      case 'analyze_risk':
        return { label: 'Risk Analysis', icon: '🛡️' };
      case 'query_knowledge_graph':
        return { label: 'Knowledge Graph', icon: '🌐' };
      case 'retrieve_source':
        return { label: 'Source Verification', icon: '🔬' };
      case 'compare_contracts':
        return { label: 'Clause Comparison', icon: '⚖️' };
      default:
        return { label: toolName.replace(/_/g, ' '), icon: '⚡' };
    }
  };

  const getConfidenceBadge = (confidence: string) => {
    const c = confidence.toUpperCase();
    if (c === 'HIGH') {
      return <span className="badge badge-success">Confidence: High</span>;
    } else if (c === 'MEDIUM') {
      return <span className="badge badge-gold">Confidence: Medium</span>;
    } else {
      return <span className="badge badge-danger">Confidence: Low / Insufficient Evidence</span>;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      
      {/* Hero Banner */}
      <div className="card-glass card-gold-border" style={{ position: 'relative', overflow: 'hidden' }}>
        <div style={{
          position: 'absolute',
          top: '-30px',
          right: '-30px',
          fontSize: '7rem',
          opacity: 0.04,
          pointerEvents: 'none'
        }}>
          🤖
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.5rem' }}>
          <span className="badge badge-gold">LEXIQ Autonomous Agent</span>
          <span className="badge badge-blue">ReAct Reasoning Engine</span>
        </div>

        <h2 className="serif-title" style={{ fontSize: '1.85rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          Autonomous Legal Contract Analyst
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: '750px', lineHeight: 1.5 }}>
          Ask complex multi-hop legal questions. The agent dynamically decides which contract tools to call, 
          inspects clauses, obligations, and risks, verifies grounded page evidence, and produces auditable findings.
        </p>

        {/* Input Bar & Controls */}
        <div style={{
          marginTop: '1.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
          background: 'rgba(0, 0, 0, 0.25)',
          padding: '1.25rem',
          borderRadius: '0.75rem',
          border: '1px solid var(--border-color)'
        }}>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            
            {/* Scope / Contract Selector */}
            <div style={{ minWidth: '240px', flex: '1' }}>
              <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.35rem', textTransform: 'uppercase', fontWeight: 600 }}>
                Target Contract Scope
              </label>
              <select
                value={targetContractId}
                onChange={(e) => {
                  setTargetContractId(e.target.value);
                  if (onSelectContract && e.target.value) {
                    onSelectContract(e.target.value);
                  }
                }}
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '0.65rem 0.85rem',
                  borderRadius: '0.5rem',
                  background: 'var(--bg-secondary)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-color)',
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  outline: 'none'
                }}
              >
                <option value="">🌐 All Contracts (Repository-Wide)</option>
                {contracts.map((c) => (
                  <option key={c.id} value={c.id}>
                    📄 {c.name} ({c.contract_type || 'Contract'})
                  </option>
                ))}
              </select>
            </div>

            {/* Max Steps Config */}
            <div style={{ width: '130px' }}>
              <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.35rem', textTransform: 'uppercase', fontWeight: 600 }}>
                Tool Budget
              </label>
              <div style={{
                padding: '0.65rem 0.85rem',
                borderRadius: '0.5rem',
                background: 'var(--bg-secondary)',
                color: 'var(--text-muted)',
                border: '1px solid var(--border-color)',
                fontSize: '0.85rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <span>Up to 5 steps</span>
                <span>⚡</span>
              </div>
            </div>
          </div>

          {/* Natural Language Question Input */}
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.35rem', textTransform: 'uppercase', fontWeight: 600 }}>
              Legal Question or Analysis Objective
            </label>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <input
                type="text"
                placeholder="e.g., What are the biggest risks in this agreement and what notice is required for termination?"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !loading) {
                    handleRunAgent();
                  }
                }}
                disabled={loading}
                style={{
                  flex: 1,
                  padding: '0.75rem 1rem',
                  borderRadius: '0.5rem',
                  background: 'var(--bg-secondary)',
                  color: 'var(--text-primary)',
                  border: '1px solid var(--border-color)',
                  fontSize: '0.95rem',
                  outline: 'none'
                }}
              />
              <button
                className="btn-gold"
                disabled={loading || !question.trim()}
                onClick={() => handleRunAgent()}
                style={{
                  padding: '0.75rem 1.75rem',
                  fontSize: '0.9rem',
                  fontWeight: 600,
                  whiteSpace: 'nowrap',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}
              >
                {loading ? 'Analyzing...' : '🚀 Investigate'}
              </button>
            </div>
          </div>

          {/* Clickable Suggested Inquiries */}
          <div style={{ marginTop: '0.25rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.4rem', fontWeight: 600 }}>
              Suggested Contract Queries:
            </span>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.45rem' }}>
              {SUGGESTED_QUESTIONS.map((sq, i) => (
                <button
                  key={i}
                  disabled={loading}
                  onClick={() => handleRunAgent(sq)}
                  style={{
                    padding: '0.35rem 0.75rem',
                    borderRadius: '1rem',
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid var(--border-color)',
                    color: 'var(--text-secondary)',
                    fontSize: '0.78rem',
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.background = 'var(--accent-gold-bg)';
                    e.currentTarget.style.borderColor = 'var(--border-gold)';
                    e.currentTarget.style.color = 'var(--text-gold)';
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                    e.currentTarget.style.borderColor = 'var(--border-color)';
                    e.currentTarget.style.color = 'var(--text-secondary)';
                  }}
                >
                  💡 {sq}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Loading & Agent Activity State (No Chain-of-Thought, Safe High-Level Status Only) */}
      {loading && (
        <div className="card-glass" style={{
          padding: '2.5rem 2rem',
          textAlign: 'center',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '1rem'
        }}>
          <div style={{
            width: '56px',
            height: '56px',
            borderRadius: '50%',
            border: '3px solid var(--border-gold)',
            borderTopColor: 'var(--accent-gold)',
            animation: 'spin 1s linear infinite'
          }} />

          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-gold)' }}>
              {LOADING_STATUS_STEPS[loadingStepIndex]}
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
              Autonomous tool loop executing. Auditing contract evidence without fabricating answers.
            </p>
          </div>

          <style jsx>{`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}</style>
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div style={{
          padding: '1rem 1.25rem',
          borderRadius: '0.5rem',
          background: 'var(--accent-rose-bg)',
          border: '1px solid var(--accent-rose)',
          color: '#fecdd3',
          fontSize: '0.9rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem'
        }}>
          <span style={{ fontSize: '1.25rem' }}>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {/* Agent Response Results */}
      {response && !loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* Main Answer Card */}
          <div className="card-glass card-gold-border" style={{ padding: '1.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '1.2rem' }}>⚖️</span>
                <h3 className="serif-title" style={{ fontSize: '1.35rem', fontWeight: 700 }}>
                  Agent Analysis
                </h3>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                {getConfidenceBadge(response.confidence)}
              </div>
            </div>

            {/* Executive Summary */}
            {response.summary && (
              <div style={{
                padding: '0.85rem 1.15rem',
                borderRadius: '0.5rem',
                background: 'rgba(212, 175, 55, 0.08)',
                borderLeft: '4px solid var(--accent-gold)',
                color: 'var(--text-primary)',
                fontSize: '0.92rem',
                fontWeight: 500,
                lineHeight: 1.5,
                marginBottom: '1.25rem'
              }}>
                <strong>Executive Summary:</strong> {response.summary}
              </div>
            )}

            {/* Answer Body */}
            <div style={{
              color: 'var(--text-primary)',
              fontSize: '0.95rem',
              lineHeight: 1.7,
              whiteSpace: 'pre-wrap',
              borderBottom: '1px solid var(--border-color)',
              paddingBottom: '1.25rem',
              marginBottom: '1.25rem'
            }}>
              {response.answer}
            </div>

            {/* Tools Invoked Bar */}
            {response.tools_used && response.tools_used.length > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                  Tools Executed:
                </span>
                {response.tools_used.map((t, idx) => {
                  const info = mapToolLabel(t);
                  return (
                    <span
                      key={idx}
                      style={{
                        fontSize: '0.75rem',
                        padding: '0.25rem 0.65rem',
                        borderRadius: '0.4rem',
                        background: 'rgba(255, 255, 255, 0.06)',
                        border: '1px solid var(--border-color)',
                        color: 'var(--text-secondary)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.35rem'
                      }}
                    >
                      <span>{info.icon}</span>
                      <span>{info.label}</span>
                    </span>
                  );
                })}
              </div>
            )}
          </div>

          {/* Key Findings Grid */}
          {response.findings && response.findings.length > 0 && (
            <div className="card-glass" style={{ padding: '1.5rem' }}>
              <h3 className="serif-title" style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span>📌</span> Key Structured Findings ({response.findings.length})
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1rem' }}>
                {response.findings.map((f, i) => (
                  <div
                    key={i}
                    style={{
                      padding: '1rem',
                      borderRadius: '0.5rem',
                      background: 'rgba(0, 0, 0, 0.2)',
                      border: '1px solid var(--border-color)',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between'
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <span className="badge badge-gold" style={{ fontSize: '0.7rem' }}>
                          {f.category.toUpperCase()}
                        </span>
                        {f.page_number && (
                          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                            Page {f.page_number}
                          </span>
                        )}
                      </div>
                      <p style={{ fontSize: '0.88rem', color: 'var(--text-primary)', lineHeight: 1.5 }}>
                        {f.fact}
                      </p>
                    </div>
                    {f.source_reference && (
                      <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.75rem', fontStyle: 'italic' }}>
                        Reference: {f.source_reference}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Verified Source Citations & Evidence Inspector */}
          {response.sources && response.sources.length > 0 && (
            <div className="card-glass" style={{ padding: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 className="serif-title" style={{ fontSize: '1.15rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span>🔬</span> Grounded Source Evidence ({response.sources.length})
                </h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  All citations backed by verified contract page text
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {response.sources.map((src, i) => (
                  <div
                    key={i}
                    style={{
                      padding: '1rem',
                      borderRadius: '0.5rem',
                      background: 'rgba(255, 255, 255, 0.02)',
                      border: '1px solid var(--border-color)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.5rem'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-gold)' }}>
                          {src.contract_name || 'Contract Document'}
                        </span>
                        <span className="badge badge-secondary" style={{ fontSize: '0.7rem' }}>
                          {src.source_location || `Page ${src.page_number || 1}`}
                        </span>
                      </div>

                      {/* Evidence Modal Launcher */}
                      <button
                        className="btn-secondary"
                        style={{ fontSize: '0.75rem', padding: '0.3rem 0.75rem' }}
                        onClick={() => {
                          onOpenEvidence({
                            contract_name: src.contract_name,
                            page_number: src.page_number || 1,
                            section: src.section || 'General',
                            source_location: src.source_location,
                            text: src.snippet || '',
                          });
                        }}
                      >
                        Inspect Full Excerpt ↗
                      </button>
                    </div>

                    <div style={{
                      fontSize: '0.84rem',
                      color: 'var(--text-secondary)',
                      fontFamily: 'monospace',
                      background: 'rgba(0, 0, 0, 0.3)',
                      padding: '0.65rem 0.85rem',
                      borderRadius: '0.35rem',
                      lineHeight: 1.5,
                      borderLeft: '3px solid var(--border-gold)'
                    }}>
                      "{src.snippet}"
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Limitations & Caveats */}
          {response.limitations && response.limitations.length > 0 && (
            <div style={{
              padding: '1rem 1.25rem',
              borderRadius: '0.5rem',
              background: 'var(--accent-amber-bg)',
              border: '1px solid var(--accent-amber)',
              color: '#fde68a',
              fontSize: '0.85rem'
            }}>
              <strong style={{ display: 'block', marginBottom: '0.35rem', fontSize: '0.9rem' }}>
                ⚠️ Disclosures & Evidence Boundaries:
              </strong>
              <ul style={{ margin: 0, paddingLeft: '1.25rem', lineHeight: 1.5 }}>
                {response.limitations.map((lim, idx) => (
                  <li key={idx}>{lim}</li>
                ))}
              </ul>
            </div>
          )}

        </div>
      )}

    </div>
  );
};
