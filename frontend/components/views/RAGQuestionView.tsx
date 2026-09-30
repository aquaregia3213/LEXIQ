'use client';

import React, { useState } from 'react';
import { api, ContractItem, AskResponse, SourceCitation } from '../../lib/api';

interface RAGQuestionViewProps {
  contracts: ContractItem[];
  selectedContractId: string;
  onOpenEvidence: (evidence: any) => void;
}

export const RAGQuestionView: React.FC<RAGQuestionViewProps> = ({
  contracts,
  selectedContractId,
  onOpenEvidence,
}) => {
  const [question, setQuestion] = useState<string>('Which contracts contain automatic renewal provisions?');
  const [targetContractId, setTargetContractId] = useState<string>(selectedContractId || '');
  const [topK, setTopK] = useState<number>(5);

  const [loading, setLoading] = useState<boolean>(false);
  const [ragResponse, setRagResponse] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const presetQuestions = [
    'Which contracts contain automatic renewal provisions?',
    'What is the limitation of liability cap limit across agreements?',
    'Are there any strict non-compete or non-solicitation clauses?',
    'What is the governing law and jurisdiction specified?',
    'What are the confidentiality obligations and return of data rules?',
    'What are the termination for convenience terms and notice periods?',
  ];

  const handleAskQuestion = async (qText?: string) => {
    const q = qText !== undefined ? qText : question;
    if (!q.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const response = await api.askQuestion(q, targetContractId || undefined, topK);
      setRagResponse(response);
    } catch (err: any) {
      setError(err.message || 'Failed to generate grounded RAG answer.');
      setRagResponse(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      
      {/* Header Banner */}
      <div className="card-glass card-gold-border">
        <h2 className="serif-title" style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          Grounded RAG Legal AI Assistant
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Ask natural language legal questions. Answers are synthesized directly from retrieved contract chunks in pgvector, with verifiable source citations and evidence grounding checks.
        </p>
      </div>

      {/* Question Form & Preset Chips Card */}
      <div className="card-glass" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleAskQuestion();
          }}
          style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}
        >
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <div style={{ flex: 1 }}>
              <textarea
                className="input-legal"
                rows={2}
                placeholder="Ask a question about your contracts..."
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                style={{ fontSize: '1rem', padding: '0.85rem 1.2rem', resize: 'vertical' }}
              />
            </div>
            <button
              type="submit"
              className="btn-gold"
              disabled={loading || !question.trim()}
              style={{ alignSelf: 'flex-start', padding: '0.85rem 1.5rem' }}
            >
              {loading ? 'Synthesizing...' : '💬 Ask Assistant'}
            </button>
          </div>

          {/* Scope Selector Row */}
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                Target Scope:
              </span>
              <select
                className="input-legal"
                style={{ padding: '0.4rem 0.75rem', fontSize: '0.85rem', width: 'auto' }}
                value={targetContractId}
                onChange={(e) => setTargetContractId(e.target.value)}
              >
                <option value="">All Contracts in Repository</option>
                {contracts.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </form>

        {/* Preset Prompt Chips */}
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.5rem' }}>
            Frequent Legal Assistant Prompts
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {presetQuestions.map((pq) => (
              <button
                key={pq}
                onClick={() => {
                  setQuestion(pq);
                  handleAskQuestion(pq);
                }}
                style={{
                  background: question === pq ? 'var(--accent-gold-bg)' : 'rgba(13, 17, 26, 0.8)',
                  border: question === pq ? '1px solid var(--border-gold)' : '1px solid var(--border-color)',
                  color: question === pq ? 'var(--text-gold)' : 'var(--text-secondary)',
                  padding: '0.35rem 0.75rem',
                  borderRadius: '999px',
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  textAlign: 'left',
                }}
              >
                {pq}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div style={{ background: 'var(--accent-rose-bg)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#f87171', padding: '1rem', borderRadius: '0.5rem', fontSize: '0.9rem' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Loading Skeleton & Progress */}
      {loading && (
        <div className="card-glass" style={{ padding: '2rem', textAlign: 'center' }}>
          <div className="skeleton" style={{ height: '24px', width: '60%', margin: '0 auto 1rem' }} />
          <div className="skeleton" style={{ height: '100px', width: '100%', marginBottom: '1.5rem' }} />
          <p style={{ color: 'var(--text-gold)', fontSize: '0.9rem', fontWeight: 600 }}>
            ⚡ Retrieving vector chunks & synthesizing grounded legal answer...
          </p>
        </div>
      )}

      {/* Synthesized Answer Output */}
      {ragResponse && !loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* Grounded Answer Card */}
          <div className="card-glass card-gold-border" style={{ padding: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span className="badge badge-gold">
                  🤖 AI Synthesized Legal Answer
                </span>
                {ragResponse.has_sufficient_evidence ? (
                  <span className="badge badge-success">
                    <span className="status-dot" /> High Evidence Grounding
                  </span>
                ) : (
                  <span className="badge badge-warning">
                    ⚠️ Limited Document Evidence
                  </span>
                )}
              </div>
            </div>

            {/* Answer Content */}
            <div style={{
              fontSize: '1.05rem',
              lineHeight: 1.7,
              color: 'var(--text-primary)',
              whiteSpace: 'pre-wrap',
              marginBottom: '1.5rem',
              padding: '1.25rem',
              background: 'rgba(7, 9, 14, 0.6)',
              borderRadius: '0.75rem',
              border: '1px solid var(--border-color)',
            }}>
              {ragResponse.answer}
            </div>

            {/* Confidence Notes */}
            {ragResponse.confidence_notes && (
              <div style={{ fontSize: '0.85rem', color: 'var(--text-gold)', fontStyle: 'italic', marginBottom: '1rem' }}>
                Note: {ragResponse.confidence_notes}
              </div>
            )}

            {/* Legal Safety Disclaimer */}
            <div style={{
              background: 'rgba(212, 175, 55, 0.05)',
              border: '1px solid rgba(212, 175, 55, 0.2)',
              borderRadius: '0.5rem',
              padding: '0.75rem 1rem',
              fontSize: '0.8rem',
              color: 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}>
              <span>🛡️</span>
              <div>
                <strong>Legal Safety Disclaimer</strong>: Answers are AI-synthesized directly from uploaded contract documents for information purposes and do not constitute formal legal advice.
              </div>
            </div>
          </div>

          {/* Source Citations Section */}
          <div className="card-glass">
            <h4 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>
              Verifiable Source Citations ({ragResponse.sources.length})
            </h4>

            {ragResponse.sources.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                No direct citations attached to this answer.
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
                {ragResponse.sources.map((src: SourceCitation, index: number) => (
                  <div
                    key={src.chunk_id || index}
                    className="card-glass"
                    style={{ background: 'rgba(13, 17, 26, 0.8)', cursor: 'pointer' }}
                    onClick={() => onOpenEvidence({
                      contractName: src.contract_name,
                      fileName: src.file_name,
                      pageStart: src.page_start,
                      pageEnd: src.page_end,
                      section: src.section,
                      chunkId: src.chunk_id,
                      text: src.text,
                    })}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                      <span className="badge badge-gold">
                        Page {src.page_start} {src.page_end !== src.page_start ? `- ${src.page_end}` : ''}
                      </span>
                      <span className="badge badge-info" style={{ fontSize: '0.7rem' }}>
                        {src.section || 'General'}
                      </span>
                    </div>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                      {src.contract_name || src.file_name || 'Contract Chunk'}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-gold)', marginTop: '0.5rem' }}>
                      Inspect Verbatim Source Evidence →
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>
      )}

    </div>
  );
};
