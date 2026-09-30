'use client';

import React, { useState, useRef } from 'react';
import { api, ContractItem } from '../../lib/api';

interface ContractUploadViewProps {
  onUploadSuccess: (newContractId: string) => void;
  onNavigateToDetails: (contractId: string) => void;
}

export const ContractUploadView: React.FC<ContractUploadViewProps> = ({
  onUploadSuccess,
  onNavigateToDetails,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [contractName, setContractName] = useState<string>('');
  const [contractType, setContractType] = useState<string>('Master Services Agreement');
  
  const [uploading, setUploading] = useState<boolean>(false);
  const [activeStep, setActiveStep] = useState<number>(0);
  const [uploadResult, setUploadResult] = useState<any | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const contractTypes = [
    'Non-Disclosure Agreement (NDA)',
    'Master Services Agreement (MSA)',
    'Service Level Agreement (SLA)',
    'Employment Agreement',
    'Lease & Real Estate Agreement',
    'Software License Agreement',
    'Vendor & Procurement Contract',
    'Corporate Bylaws & Governance',
    'General Commercial Contract',
  ];

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const selected = e.dataTransfer.files[0];
      validateAndSetFile(selected);
    }
  };

  const validateAndSetFile = (selected: File) => {
    const ext = selected.name.split('.').pop()?.toLowerCase();
    if (ext !== 'pdf' && ext !== 'docx') {
      setErrorMsg('Unsupported file format. Please upload a PDF (.pdf) or DOCX (.docx) document.');
      return;
    }
    setFile(selected);
    if (!contractName) {
      // Auto-populate name without extension
      const baseName = selected.name.replace(/\.[^/.]+$/, '');
      setContractName(baseName.replace(/[-_]/g, ' '));
    }
    setErrorMsg(null);
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setErrorMsg('Please select a PDF or DOCX contract file to upload.');
      return;
    }

    setUploading(true);
    setErrorMsg(null);
    setUploadResult(null);
    setActiveStep(1);

    try {
      // Step 1: Uploading & File Ingestion
      setTimeout(() => setActiveStep(2), 600); // Visual progress update
      
      // Step 2 & 3: Trigger real backend ingestion
      const result = await api.uploadContract(file, contractName || file.name, contractType);
      
      setActiveStep(3);
      setTimeout(() => setActiveStep(4), 500);

      setUploadResult(result);
      if (result.contract_id) {
        onUploadSuccess(result.contract_id);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to parse and upload contract.');
      setActiveStep(0);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      
      {/* Header Banner */}
      <div className="card-glass card-gold-border">
        <h2 className="serif-title" style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          Contract Ingestion & Pipeline Parser
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Upload PDF or DOCX legal documents. The pipeline automatically extracts raw text, tracks page layouts, chunks provisions, generates vector embeddings, and stores records in PostgreSQL/pgvector.
        </p>
      </div>

      {/* Upload Form Card */}
      <div className="card-glass">
        <form onSubmit={handleUploadSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* File Dropzone */}
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleFileDrop}
            onClick={() => fileInputRef.current?.click()}
            style={{
              border: file ? '2px solid var(--accent-gold)' : '2px dashed var(--border-color)',
              borderRadius: '0.75rem',
              padding: '2.5rem 1.5rem',
              textAlign: 'center',
              background: file ? 'rgba(212, 175, 55, 0.05)' : 'rgba(13, 17, 26, 0.6)',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            <input
              type="file"
              ref={fileInputRef}
              accept=".pdf,.docx"
              onChange={(e) => e.target.files?.[0] && validateAndSetFile(e.target.files[0])}
              style={{ display: 'none' }}
            />
            <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>
              {file ? '📄' : '📁'}
            </div>
            {file ? (
              <div>
                <div style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--text-gold)', marginBottom: '0.25rem' }}>
                  {file.name}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {(file.size / 1024).toFixed(1)} KB • Click or drop to replace file
                </div>
              </div>
            ) : (
              <div>
                <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                  Drag & Drop PDF or DOCX contract here
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  or click to select file from your machine
                </div>
              </div>
            )}
          </div>

          {/* Contract Metadata Inputs */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '0.5rem', textTransform: 'uppercase' }}>
                Contract Title / Name
              </label>
              <input
                type="text"
                className="input-legal"
                placeholder="e.g. Acme Corp Services Agreement 2026"
                value={contractName}
                onChange={(e) => setContractName(e.target.value)}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '0.5rem', textTransform: 'uppercase' }}>
                Contract Category / Type
              </label>
              <select
                className="input-legal"
                value={contractType}
                onChange={(e) => setContractType(e.target.value)}
              >
                {contractTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Error Message Box */}
          {errorMsg && (
            <div style={{
              background: 'var(--accent-rose-bg)',
              border: '1px solid rgba(244, 63, 94, 0.3)',
              color: '#f87171',
              padding: '1rem',
              borderRadius: '0.5rem',
              fontSize: '0.9rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem'
            }}>
              <span>⚠️</span>
              <div>{errorMsg}</div>
            </div>
          )}

          {/* Action Button */}
          <button
            type="submit"
            className="btn-gold"
            disabled={uploading || !file}
            style={{ width: '100%', justifyContent: 'center', padding: '0.85rem' }}
          >
            {uploading ? 'Processing Contract Pipeline...' : '⚡ Process & Upload Contract'}
          </button>
        </form>
      </div>

      {/* Interactive Processing Pipeline Stepper */}
      {(uploading || uploadResult) && (
        <div className="card-glass">
          <h4 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1.25rem' }}>
            Ingestion Pipeline Execution Status
          </h4>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            
            {/* Step 1 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', opacity: activeStep >= 1 ? 1 : 0.4 }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: activeStep >= 1 ? 'var(--accent-gold)' : 'var(--bg-secondary)', color: '#000', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.85rem' }}>
                1
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>File Transfer & Structure Validation</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Validating PDF/DOCX byte stream and extracting document properties</div>
              </div>
            </div>

            {/* Step 2 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', opacity: activeStep >= 2 ? 1 : 0.4 }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: activeStep >= 2 ? 'var(--accent-gold)' : 'var(--bg-secondary)', color: '#000', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.85rem' }}>
                2
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>PyMuPDF Text & Page Information Extraction</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Extracting clean layout text, headings, and precise page numbers</div>
              </div>
            </div>

            {/* Step 3 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', opacity: activeStep >= 3 ? 1 : 0.4 }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: activeStep >= 3 ? 'var(--accent-gold)' : 'var(--bg-secondary)', color: '#000', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.85rem' }}>
                3
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>Semantic Chunking & Embedding Generation</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Generating dense vector embeddings for chunked provisions</div>
              </div>
            </div>

            {/* Step 4 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', opacity: activeStep >= 4 ? 1 : 0.4 }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: activeStep >= 4 ? 'var(--accent-emerald)' : 'var(--bg-secondary)', color: '#fff', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.85rem' }}>
                ✓
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: '0.9rem', color: activeStep >= 4 ? '#34d399' : 'inherit' }}>
                  PostgreSQL & pgvector Ingestion Completed
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Contract indexed and ready for semantic search & RAG Q&A</div>
              </div>
            </div>

          </div>

          {/* Success Summary Banner */}
          {uploadResult && (
            <div style={{
              marginTop: '1.5rem',
              padding: '1.25rem',
              background: 'var(--accent-emerald-bg)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              borderRadius: '0.6rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}>
              <div>
                <div style={{ fontWeight: 700, color: '#34d399', fontSize: '1rem', marginBottom: '0.2rem' }}>
                  🎉 Ingestion Complete!
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  Processed {uploadResult.page_count || 1} pages and generated {uploadResult.chunk_count || 'all'} vector chunks.
                </div>
              </div>

              {uploadResult.contract_id && (
                <button
                  className="btn-gold"
                  style={{ fontSize: '0.85rem', padding: '0.5rem 1rem' }}
                  onClick={() => onNavigateToDetails(uploadResult.contract_id)}
                >
                  View Contract Details →
                </button>
              )}
            </div>
          )}
        </div>
      )}

    </div>
  );
};
