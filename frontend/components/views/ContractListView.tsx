'use client';

import React, { useState } from 'react';
import { ContractItem, api } from '../../lib/api';

interface ContractListViewProps {
  contracts: ContractItem[];
  loading: boolean;
  onSelectContract: (contractId: string) => void;
  onNavigateToUpload: () => void;
  onRefreshContracts: () => void;
}

export const ContractListView: React.FC<ContractListViewProps> = ({
  contracts,
  loading,
  onSelectContract,
  onNavigateToUpload,
  onRefreshContracts,
}) => {
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Filtered contracts
  const filteredContracts = contracts.filter((c) => {
    const matchesSearch = c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (c.contract_type && c.contract_type.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesType = typeFilter === '' || c.contract_type === typeFilter;
    return matchesSearch && matchesType;
  });

  const handleDelete = async (contractId: string, contractName: string) => {
    if (!confirm(`Are you sure you want to delete contract "${contractName}"? This will purge document chunks and extracted entities.`)) {
      return;
    }
    setDeletingId(contractId);
    try {
      await api.deleteContract(contractId);
      onRefreshContracts();
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      
      {/* Header & Controls Bar */}
      <div className="card-glass" style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
        <div>
          <h2 className="serif-title" style={{ fontSize: '1.6rem', fontWeight: 700 }}>
            Contract Repository ({contracts.length})
          </h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Search, manage, extract clauses/entities, and run risk evaluations across ingested contracts.
          </p>
        </div>

        <button className="btn-gold" onClick={onNavigateToUpload}>
          + Upload New Contract
        </button>
      </div>

      {/* Search & Filter Controls */}
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: '260px' }}>
          <input
            type="text"
            className="input-legal"
            placeholder="🔍 Search contracts by title or type..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <select
          className="input-legal"
          style={{ width: 'auto', minWidth: '200px' }}
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
        >
          <option value="">All Contract Types</option>
          <option value="Non-Disclosure Agreement (NDA)">NDAs</option>
          <option value="Master Services Agreement (MSA)">MSAs</option>
          <option value="Service Level Agreement (SLA)">SLAs</option>
          <option value="Employment Agreement">Employment</option>
          <option value="Lease & Real Estate Agreement">Lease</option>
          <option value="Software License Agreement">Software License</option>
        </select>
      </div>

      {/* Contract Data Table */}
      {loading ? (
        <div className="card-glass" style={{ padding: '2rem' }}>
          <div className="skeleton" style={{ height: '40px', marginBottom: '1rem' }} />
          <div className="skeleton" style={{ height: '40px', marginBottom: '1rem' }} />
          <div className="skeleton" style={{ height: '40px' }} />
        </div>
      ) : filteredContracts.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📁</div>
          <h4 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>No Contracts Found</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '420px', margin: '0 auto 1.5rem' }}>
            {searchTerm || typeFilter
              ? 'No contracts match your search filter criteria. Try resetting search filters.'
              : 'Your contract repository is currently empty. Ingest your first PDF/DOCX contract to get started.'}
          </p>
          <button className="btn-gold" onClick={onNavigateToUpload}>
            + Upload First Contract
          </button>
        </div>
      ) : (
        <div className="table-container">
          <table className="legal-table">
            <thead>
              <tr>
                <th>Contract Name</th>
                <th>Category</th>
                <th>Status</th>
                <th>Uploaded Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredContracts.map((c) => (
                <tr key={c.id}>
                  <td>
                    <div
                      onClick={() => onSelectContract(c.id)}
                      style={{ fontWeight: 600, color: 'var(--text-gold)', cursor: 'pointer' }}
                    >
                      {c.name}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      ID: {c.id.substring(0, 8)}...
                    </div>
                  </td>
                  <td>
                    <span className="badge badge-info" style={{ fontSize: '0.75rem' }}>
                      {c.contract_type || 'General'}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${c.status === 'COMPLETED' ? 'badge-success' : c.status === 'FAILED' ? 'badge-danger' : 'badge-warning'}`}>
                      <span className="status-dot" /> {c.status}
                    </span>
                  </td>
                  <td style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                    {new Date(c.created_at).toLocaleDateString()}
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button
                        className="btn-secondary"
                        style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem' }}
                        onClick={() => onSelectContract(c.id)}
                      >
                        Inspect Details
                      </button>
                      <button
                        className="btn-secondary"
                        style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem', color: '#f87171', borderColor: 'rgba(244,63,94,0.3)' }}
                        disabled={deletingId === c.id}
                        onClick={() => handleDelete(c.id, c.name)}
                      >
                        {deletingId === c.id ? 'Deleting...' : 'Delete'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

    </div>
  );
};
