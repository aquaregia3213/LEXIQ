'use client';

import { useEffect, useState } from 'react';
import { api, ContractItem, HealthStatus } from '../lib/api';
import { Sidebar, ViewType } from '../components/Sidebar';
import { Header } from '../components/Header';
import { EvidenceModal, EvidenceData } from '../components/EvidenceModal';

// Views
import { DashboardView } from '../components/views/DashboardView';
import { ContractUploadView } from '../components/views/ContractUploadView';
import { ContractListView } from '../components/views/ContractListView';
import { ContractDetailsView } from '../components/views/ContractDetailsView';
import { SemanticSearchView } from '../components/views/SemanticSearchView';
import { RAGQuestionView } from '../components/views/RAGQuestionView';
import { ClauseView } from '../components/views/ClauseView';
import { EntityView } from '../components/views/EntityView';
import { RiskAnalysisView } from '../components/views/RiskAnalysisView';
import { SourceEvidenceView } from '../components/views/SourceEvidenceView';
import { AgentView } from '../components/views/AgentView';
import { ECourtsView } from '../components/views/ECourtsView';

export default function Home() {
  const [currentView, setCurrentView] = useState<ViewType>('dashboard');
  const [selectedContractId, setSelectedContractId] = useState<string>('');
  
  const [contracts, setContracts] = useState<ContractItem[]>([]);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  
  const [loading, setLoading] = useState<boolean>(true);
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);
  const [modalEvidence, setModalEvidence] = useState<EvidenceData | null>(null);

  // Light / Dark Theme State
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  // Initialize theme from localStorage or system preference
  useEffect(() => {
    const savedTheme = localStorage.getItem('juriscope_theme') as 'dark' | 'light' | null;
    if (savedTheme) {
      setTheme(savedTheme);
      document.documentElement.setAttribute('data-theme', savedTheme);
    } else {
      document.documentElement.setAttribute('data-theme', 'dark');
    }
  }, []);

  const handleToggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    localStorage.setItem('juriscope_theme', nextTheme);
    document.documentElement.setAttribute('data-theme', nextTheme);
  };

  // Fetch backend status & contract list
  const loadData = async () => {
    setLoading(true);
    try {
      const healthData = await api.getHealth();
      setHealth(healthData);
      setIsBackendConnected(true);
    } catch {
      setIsBackendConnected(false);
    }

    try {
      const contractsList = await api.listContracts();
      setContracts(contractsList);
    } catch (err) {
      console.error('Error fetching contracts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();

    // Poll health check every 15 seconds
    const interval = setInterval(async () => {
      try {
        const h = await api.getHealth();
        setHealth(h);
        setIsBackendConnected(true);
      } catch {
        setIsBackendConnected(false);
      }
    }, 15000);

    return () => clearInterval(interval);
  }, []);

  const handleNavigate = (view: ViewType) => {
    setCurrentView(view);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSelectContractDetails = (contractId: string) => {
    setSelectedContractId(contractId);
    setCurrentView('details');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const getViewTitle = (): { title: string; subtitle: string } => {
    switch (currentView) {
      case 'dashboard':
        return { title: 'Executive Legal Dashboard', subtitle: 'Platform overview, 3D metrics, and backend health' };
      case 'upload':
        return { title: 'Ingest & Parse Contract', subtitle: 'Upload PDF/DOCX files into 3D vector storage' };
      case 'contracts':
        return { title: 'Contract Repository', subtitle: 'Search and inspect all ingested contracts' };
      case 'details':
        return { title: 'Contract Workspace & Intelligence', subtitle: 'Deep dive into clauses, entities, risks, and 3D knowledge graph' };
      case 'agent':
        return { title: 'Autonomous Legal AI Analyst', subtitle: 'Multi-step contract investigation, clause reasoning, and verifiable evidence auditing' };
      case 'search':
        return { title: 'Semantic Vector Search', subtitle: 'Conceptual vector similarity retrieval across chunks' };
      case 'rag':
        return { title: 'Grounded RAG AI Assistant', subtitle: 'Ask legal questions with verifiable document citations' };
      case 'clauses':
        return { title: 'Clause Taxonomy & Classification', subtitle: 'Categorized legal provisions across categories' };
      case 'entities':
        return { title: 'Named Entity Extraction', subtitle: 'Recognized corporate entities, signatories, and dates' };
      case 'risks':
        return { title: 'Risk Intelligence & Flags', subtitle: 'Automated contract risk detection and evidence' };
      case 'evidence':
        return { title: 'Source & Evidence Inspector', subtitle: 'Inspect raw chunk text and page grounding offsets' };
      case 'ecourts':
        return { title: 'Indian eCourts Case Intelligence', subtitle: 'CNR validation, official portal search coordinates, and AI procedural risk analysis' };
      default:
        return { title: 'Legal Intelligence Platform', subtitle: 'Autonomous contract and court intelligence platform' };
    }
  };

  const { title, subtitle } = getViewTitle();

  return (
    <div className="app-container">
      {/* Persistent Left Navigation Sidebar */}
      <Sidebar
        currentView={currentView}
        onNavigate={handleNavigate}
        isBackendConnected={isBackendConnected}
        totalContractsCount={contracts.length}
        theme={theme}
        onToggleTheme={handleToggleTheme}
      />

      {/* Main Content Area */}
      <div className="main-content">
        {/* Top Header Bar */}
        <Header
          title={title}
          subtitle={subtitle}
          contracts={contracts}
          selectedContractId={selectedContractId}
          onSelectContract={(id) => {
            setSelectedContractId(id);
            if (id && currentView !== 'details') {
              setCurrentView('details');
            }
          }}
          onQuickUpload={() => handleNavigate('upload')}
          isBackendConnected={isBackendConnected}
          theme={theme}
          onToggleTheme={handleToggleTheme}
        />

        {/* View Switcher Container */}
        <main className="page-wrapper">
          
          {/* Screen 1: Dashboard */}
          {currentView === 'dashboard' && (
            <DashboardView
              contracts={contracts}
              health={health}
              loading={loading}
              onNavigate={handleNavigate}
              onSelectContract={handleSelectContractDetails}
            />
          )}

          {/* Screen 2: Contract Upload */}
          {currentView === 'upload' && (
            <ContractUploadView
              onUploadSuccess={(newId) => {
                loadData();
                setSelectedContractId(newId);
              }}
              onNavigateToDetails={handleSelectContractDetails}
            />
          )}

          {/* Screen 3: Contract List */}
          {currentView === 'contracts' && (
            <ContractListView
              contracts={contracts}
              loading={loading}
              onSelectContract={handleSelectContractDetails}
              onNavigateToUpload={() => handleNavigate('upload')}
              onRefreshContracts={loadData}
            />
          )}

          {/* Screen 4: Contract Details */}
          {currentView === 'details' && selectedContractId && (
            <ContractDetailsView
              contractId={selectedContractId}
              onNavigateToAsk={(cId) => {
                setSelectedContractId(cId);
                handleNavigate('rag');
              }}
              onNavigateToSearch={(cId) => {
                setSelectedContractId(cId);
                handleNavigate('search');
              }}
              onNavigateToAgent={(cId) => {
                setSelectedContractId(cId);
                handleNavigate('agent');
              }}
              onOpenEvidence={(data) => setModalEvidence(data)}
            />
          )}

          {/* Screen: Autonomous Legal Agent */}
          {currentView === 'agent' && (
            <AgentView
              contracts={contracts}
              selectedContractId={selectedContractId}
              onSelectContract={(id) => setSelectedContractId(id)}
              onOpenEvidence={(data) => setModalEvidence(data)}
            />
          )}

          {/* Screen: Indian eCourts Intelligence */}
          {currentView === 'ecourts' && (
            <ECourtsView />
          )}

          {/* Screen 5: Semantic Search */}
          {currentView === 'search' && (
            <SemanticSearchView
              contracts={contracts}
              selectedContractId={selectedContractId}
              onOpenEvidence={(data) => setModalEvidence(data)}
              onSelectContract={handleSelectContractDetails}
            />
          )}

          {/* Screen 6: RAG Question Interface */}
          {currentView === 'rag' && (
            <RAGQuestionView
              contracts={contracts}
              selectedContractId={selectedContractId}
              onOpenEvidence={(data) => setModalEvidence(data)}
            />
          )}

          {/* Screen 7: Clause View */}
          {currentView === 'clauses' && (
            <ClauseView
              contracts={contracts}
              selectedContractId={selectedContractId}
              onOpenEvidence={(data) => setModalEvidence(data)}
              onSelectContract={handleSelectContractDetails}
            />
          )}

          {/* Screen 8: Entity View */}
          {currentView === 'entities' && (
            <EntityView
              contracts={contracts}
              selectedContractId={selectedContractId}
              onSelectContract={handleSelectContractDetails}
            />
          )}

          {/* Screen 9: Risk Analysis View */}
          {currentView === 'risks' && (
            <RiskAnalysisView
              contracts={contracts}
              selectedContractId={selectedContractId}
              onOpenEvidence={(data) => setModalEvidence(data)}
              onSelectContract={handleSelectContractDetails}
            />
          )}

          {/* Screen 10: Source / Evidence View */}
          {currentView === 'evidence' && (
            <SourceEvidenceView
              contracts={contracts}
              selectedContractId={selectedContractId}
              onOpenEvidence={(data) => setModalEvidence(data)}
              onSelectContract={handleSelectContractDetails}
            />
          )}

        </main>
      </div>

      {/* Global Source / Evidence Inspection Modal */}
      <EvidenceModal
        evidence={modalEvidence}
        onClose={() => setModalEvidence(null)}
      />
    </div>
  );
}
