'use client';

import React, { useState } from 'react';
import { SubgraphResponse } from '../lib/api';

interface KnowledgeGraphViewerProps {
  graphData: SubgraphResponse | null;
  loading: boolean;
  onSyncGraph?: () => void;
}

export const KnowledgeGraphViewer: React.FC<KnowledgeGraphViewerProps> = ({
  graphData,
  loading,
  onSyncGraph,
}) => {
  const [selectedNode, setSelectedNode] = useState<any | null>(null);

  if (loading) {
    return (
      <div className="card-glass" style={{ padding: '3rem', textAlign: 'center' }}>
        <div className="skeleton" style={{ height: '300px', width: '100%', marginBottom: '1rem' }} />
        <p style={{ color: 'var(--text-muted)' }}>Retrieving 3D Knowledge Graph relationships...</p>
      </div>
    );
  }

  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">🌐</div>
        <h4 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>No Knowledge Graph Data</h4>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '460px', margin: '0 auto 1.5rem' }}>
          This contract has not been synced to the Knowledge Graph yet. Syncing builds relational 3D entity nodes, clauses, obligations, and risk connections.
        </p>
        {onSyncGraph && (
          <button className="btn-gold" onClick={onSyncGraph}>
            ⚡ Sync Contract to 3D Knowledge Graph
          </button>
        )}
      </div>
    );
  }

  // Node color mapper
  const getNodeColor = (label: string) => {
    switch (label.toUpperCase()) {
      case 'CONTRACT': return '#d4af37';
      case 'COMPANY': case 'PARTY': return '#3b82f6';
      case 'CLAUSE': return '#10b981';
      case 'RISK': case 'RISKFLAG': return '#f43f5e';
      case 'JURISDICTION': return '#8b5cf6';
      default: return '#06b6d4';
    }
  };

  return (
    <div className="card-glass card-gold-border">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
            <span className="badge badge-gold">🌐 3D Knowledge Subgraph</span>
          </div>
          <h4 style={{ fontSize: '1.3rem', fontWeight: 700 }}>Interactive 3D Entity & Clause Graph</h4>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            {graphData.nodes.length} Connected 3D Spherical Nodes • {graphData.relationships.length} Relational Edges
          </p>
        </div>
        {onSyncGraph && (
          <button className="btn-secondary" onClick={onSyncGraph} style={{ fontSize: '0.8rem' }}>
            🔄 Re-sync 3D Graph
          </button>
        )}
      </div>

      {/* 3D Canvas Workspace Container */}
      <div style={{
        background: 'radial-gradient(circle at center, rgba(19, 25, 38, 0.95) 0%, rgba(7, 9, 14, 0.98) 100%)',
        border: '1px solid var(--border-color)',
        borderRadius: '0.85rem',
        padding: '1.75rem',
        minHeight: '420px',
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        gap: '1.75rem',
        boxShadow: 'inset 0 0 40px rgba(0, 0, 0, 0.8), 0 20px 40px rgba(0, 0, 0, 0.5)',
        perspective: '1000px',
      }}>
        
        {/* 3D Floating Node Spheres Grid */}
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-gold)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '1rem' }}>
            Extracted Entity & Provision Nodes (Click to inspect properties)
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.85rem' }}>
            {graphData.nodes.map((node) => {
              const color = getNodeColor(node.label);
              const isSelected = selectedNode?.id === node.id;

              return (
                <div
                  key={node.id}
                  onClick={() => setSelectedNode(node)}
                  style={{
                    background: isSelected ? 'rgba(212, 175, 55, 0.2)' : 'rgba(19, 25, 38, 0.9)',
                    border: `1.5px solid ${color}`,
                    borderRadius: '0.75rem',
                    padding: '0.65rem 1rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.6rem',
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                    transition: 'all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
                    transform: isSelected
                      ? 'perspective(500px) translateZ(25px) scale(1.1)'
                      : 'perspective(500px) translateZ(10px)',
                    boxShadow: isSelected
                      ? `0 15px 35px ${color}55, inset 0 1px 0 rgba(255,255,255,0.4)`
                      : `0 8px 20px rgba(0,0,0,0.5), 0 0 12px ${color}33`,
                  }}
                >
                  {/* 3D Sphere Bullet */}
                  <div
                    className="node-sphere-3d"
                    style={{
                      width: '16px',
                      height: '16px',
                      color: color,
                    }}
                  />
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                      {node.name || node.properties?.name || node.type || node.properties?.type || node.id}
                    </span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      {node.label}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Node Inspector Drawer */}
        {selectedNode && (
          <div style={{
            background: 'rgba(13, 17, 26, 0.95)',
            border: '1px solid var(--border-gold)',
            borderRadius: '0.6rem',
            padding: '1rem',
            transform: 'perspective(600px) translateZ(15px)',
            boxShadow: '0 10px 30px rgba(212, 175, 55, 0.15)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <div style={{ fontWeight: 700, color: 'var(--text-gold)', fontSize: '0.95rem' }}>
                Inspect Node Properties: {selectedNode.name || selectedNode.properties?.name || selectedNode.id}
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.1rem' }}
              >
                ✕
              </button>
            </div>
            <pre style={{ fontSize: '0.8rem', color: '#e2e8f0', fontFamily: 'Consolas, monospace', margin: 0, whiteSpace: 'pre-wrap' }}>
              {JSON.stringify(selectedNode.properties || selectedNode, null, 2)}
            </pre>
          </div>
        )}

        {/* Relational 3D Beams & Edges List */}
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-gold)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.75rem' }}>
            3D Knowledge Edges & Relational Links ({(graphData.relationships || graphData.edges || []).length})
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
            {(graphData.relationships || graphData.edges || []).map((edge, idx) => (
              <div
                key={idx}
                style={{
                  background: 'rgba(13, 17, 26, 0.85)',
                  padding: '0.75rem 1.25rem',
                  borderRadius: '0.5rem',
                  border: '1px solid var(--border-color)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '1rem',
                  fontSize: '0.85rem',
                  transition: 'transform 0.2s ease',
                  boxShadow: '0 4px 15px rgba(0, 0, 0, 0.4)',
                }}
              >
                <span style={{ fontWeight: 700, color: 'var(--text-gold)' }}>{edge.source}</span>
                <span style={{
                  color: '#60a5fa',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  background: 'var(--accent-blue-bg)',
                  border: '1px solid rgba(59, 130, 246, 0.3)',
                  padding: '0.2rem 0.6rem',
                  borderRadius: '999px',
                  boxShadow: '0 0 10px rgba(59, 130, 246, 0.2)',
                }}>
                  ⚡ ─── [{edge.type}] ───►
                </span>
                <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{edge.target}</span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};
