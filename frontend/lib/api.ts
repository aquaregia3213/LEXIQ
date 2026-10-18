/**
 * LEXIQ Legal AI Contract Intelligence Platform
 * Centralized API Client Layer
 */

const RAW_API_URL = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const API_BASE_URL = RAW_API_URL.replace(/\/+$/, '');
export const API_V1 = `${API_BASE_URL}/api/v1`;

// =========================================================================
// Type Definitions
// =========================================================================

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  environment: string;
  timestamp?: string;
  database?: {
    status: string;
    dialect?: string;
    database?: string;
    message?: string;
  };
}

export interface DocumentItem {
  id: string;
  contract_id: string;
  file_name: string;
  file_type: string;
  page_count: number;
  processing_status: string;
  error_message?: string | null;
  created_at?: string;
}

export interface ClauseInfo {
  id: string;
  clause_id?: string;
  contract_id: string;
  document_id?: string;
  clause_type: string;
  text: string;
  confidence: number;
  page_number: number;
  source_location?: string;
  created_at?: string;
}

export interface EntityInfo {
  id: string;
  entity_id?: string;
  contract_id: string;
  entity_type: string;
  text: string;
  name: string;
  normalized_value?: string;
  normalized_name?: string;
  confidence: number;
  source_location?: string;
  created_at?: string;
}

export interface ObligationInfo {
  id: string;
  obligation_id?: string;
  contract_id: string;
  obligation: string;
  description: string;
  responsible_party?: string;
  party?: string;
  deadline?: string | null;
  confidence: number;
  source_location?: string;
  created_at?: string;
}

export interface RiskFlagInfo {
  id: string;
  risk_id?: string;
  contract_id: string;
  clause_id?: string;
  risk_type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;
  confidence: number;
  explanation?: string;
  description: string;
  evidence?: string;
  source_location?: string;
  created_at?: string;
}

export interface RiskAnalysisResponse {
  contract_id: string;
  risk_count: number;
  disclaimer: string;
  risks: RiskFlagInfo[];
}

export interface GraphNode {
  id: string;
  label: string;
  name?: string;
  type?: string;
  [key: string]: any;
}

export interface GraphRelationship {
  source: string;
  target: string;
  type: string;
  [key: string]: any;
}

export interface SubgraphResponse {
  contract_id: string;
  node_count: number;
  relationship_count: number;
  nodes: GraphNode[];
  relationships: GraphRelationship[];
  edges?: GraphRelationship[];
}

export interface SourceCitation {
  chunk_id?: string;
  contract_id?: string;
  contract_name?: string;
  file_name?: string;
  page_start: number;
  page_end: number;
  page_number?: number;
  section: string;
  source_location?: string;
  text?: string;
}

export interface AskResponse {
  question: string;
  answer: string;
  sources: SourceCitation[];
  has_sufficient_evidence: boolean;
  confidence_notes?: string | null;
}

export interface SearchResultItem {
  chunk_id: string;
  contract_id: string;
  contract_name: string;
  contract_type?: string;
  document_id: string;
  file_name: string;
  chunk_index: number;
  text: string;
  page_start: number;
  page_end: number;
  page_number?: number;
  section: string;
  source_location?: string;
  similarity_score: number;
  metadata?: any;
}

export interface SearchResponse {
  query: string;
  result_count: number;
  top_k: number;
  results: SearchResultItem[];
}

export interface ChunkInfo {
  chunk_id: string;
  id: string;
  contract_id: string;
  document_id: string;
  chunk_index: number;
  text: string;
  page_start: number;
  page_end: number;
  section: string;
  source_location: string;
  metadata?: any;
  created_at?: string;
}

export interface ContractItem {
  id: string;
  name: string;
  contract_type?: string;
  status: string;
  file_path?: string;
  uploaded_by?: string;
  page_count?: number;
  chunk_count?: number;
  created_at: string;
  updated_at: string;
  documents?: DocumentItem[];
  clauses?: ClauseInfo[];
  entities?: EntityInfo[];
  obligations?: ObligationInfo[];
  risk_flags?: RiskFlagInfo[];
}

export interface ContractUploadResult {
  contract_id: string;
  filename: string;
  processing_status: string;
  document_id?: string;
  contract_name?: string;
  file_type?: string;
  page_count?: number;
  chunk_count?: number;
  message?: string;
}

// =========================================================================
// Fetch Helper
// =========================================================================

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorMessage = `HTTP Error ${res.status}: ${res.statusText}`;
    try {
      const errorJson = await res.json();
      if (errorJson.error?.message) {
        errorMessage = errorJson.error.message;
      } else if (typeof errorJson.detail === 'string') {
        errorMessage = errorJson.detail;
      } else if (errorJson.detail?.message) {
        errorMessage = errorJson.detail.message;
      }
    } catch {
      // Fall back to HTTP status message if JSON parsing fails
    }
    throw new Error(errorMessage);
  }
  return res.json();
}

// =========================================================================
// API Methods Object
// =========================================================================

export const api = {
  /**
   * Check backend service health and connectivity.
   */
  async getHealth(): Promise<HealthStatus> {
    const res = await fetch(`${API_V1}/health`, {
      headers: { Accept: 'application/json' },
    });
    return handleResponse<HealthStatus>(res);
  },

  /**
   * List all ingested contracts in reverse chronological order.
   */
  async listContracts(): Promise<ContractItem[]> {
    const res = await fetch(`${API_V1}/contracts`, {
      headers: { Accept: 'application/json' },
      cache: 'no-store',
    });
    return handleResponse<ContractItem[]>(res);
  },

  /**
   * Retrieve single contract details and associated relations.
   */
  async getContract(contractId: string): Promise<ContractItem> {
    const res = await fetch(`${API_V1}/contracts/${encodeURIComponent(contractId)}`, {
      headers: { Accept: 'application/json' },
    });
    return handleResponse<ContractItem>(res);
  },

  /**
   * Retrieve contract document chunks with page offsets.
   */
  async getContractChunks(contractId: string): Promise<ChunkInfo[]> {
    const res = await fetch(`${API_V1}/contracts/${encodeURIComponent(contractId)}/chunks`, {
      headers: { Accept: 'application/json' },
    });
    return handleResponse<ChunkInfo[]>(res);
  },

  /**
   * Delete contract and cascade-delete all associated database records and disk file.
   */
  async deleteContract(contractId: string): Promise<{ message: string }> {
    const res = await fetch(`${API_V1}/contracts/${encodeURIComponent(contractId)}`, {
      method: 'DELETE',
      headers: { Accept: 'application/json' },
    });
    return handleResponse<{ message: string }>(res);
  },

  /**
   * Upload a PDF or DOCX contract document.
   */
  async uploadContract(
    file: File,
    contractName?: string,
    contractType?: string
  ): Promise<ContractUploadResult> {
    const formData = new FormData();
    formData.append('file', file);
    if (contractName) formData.append('contract_name', contractName);
    if (contractType) formData.append('contract_type', contractType);

    const res = await fetch(`${API_V1}/contracts/upload`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<ContractUploadResult>(res);
  },

  /**
   * Retrieve extracted and classified clauses for a contract.
   */
  async getClauses(contractId: string): Promise<ClauseInfo[]> {
    const res = await fetch(`${API_V1}/contracts/${encodeURIComponent(contractId)}/clauses`, {
      headers: { Accept: 'application/json' },
    });
    return handleResponse<ClauseInfo[]>(res);
  },

  /**
   * Trigger clause extraction and classification pipeline on contract text.
   */
  async extractClauses(contractId: string): Promise<ClauseInfo[]> {
    const res = await fetch(`${API_V1}/contracts/${encodeURIComponent(contractId)}/extract-clauses`, {
      method: 'POST',
      headers: { Accept: 'application/json' },
    });
    return handleResponse<ClauseInfo[]>(res);
  },

  /**
   * Retrieve extracted named entities for a contract.
   */
  async getEntities(contractId: string): Promise<EntityInfo[]> {
    const res = await fetch(`${API_V1}/contracts/${encodeURIComponent(contractId)}/entities`, {
      headers: { Accept: 'application/json' },
    });
    return handleResponse<EntityInfo[]>(res);
  },

  /**
   * Trigger named entity extraction pipeline.
   */
  async extractEntities(contractId: string): Promise<EntityInfo[]> {
    const res = await fetch(`${API_V1}/contracts/${encodeURIComponent(contractId)}/extract-entities`, {
      method: 'POST',
      headers: { Accept: 'application/json' },
    });
    return handleResponse<EntityInfo[]>(res);
  },

  /**
   * Retrieve extracted obligations for a contract.
   */
  async getObligations(contractId: string): Promise<ObligationInfo[]> {
    const res = await fetch(`${API_V1}/contracts/${encodeURIComponent(contractId)}/obligations`, {
      headers: { Accept: 'application/json' },
    });
    return handleResponse<ObligationInfo[]>(res);
  },

  /**
   * Trigger contractual obligation extraction pipeline.
   */
  async extractObligations(contractId: string): Promise<ObligationInfo[]> {
    const res = await fetch(`${API_V1}/contracts/${encodeURIComponent(contractId)}/extract-obligations`, {
      method: 'POST',
      headers: { Accept: 'application/json' },
    });
    return handleResponse<ObligationInfo[]>(res);
  },

  /**
   * Retrieve identified risk flags with legal safety disclaimer.
   */
  async getRisks(contractId: string): Promise<RiskAnalysisResponse> {
    const res = await fetch(`${API_V1}/contracts/${encodeURIComponent(contractId)}/risks`, {
      headers: { Accept: 'application/json' },
    });
    return handleResponse<RiskAnalysisResponse>(res);
  },

  /**
   * Trigger risk analysis pipeline across contract clauses.
   */
  async analyzeRisks(contractId: string): Promise<RiskAnalysisResponse> {
    const res = await fetch(`${API_V1}/contracts/${encodeURIComponent(contractId)}/analyze-risks`, {
      method: 'POST',
      headers: { Accept: 'application/json' },
    });
    return handleResponse<RiskAnalysisResponse>(res);
  },

  /**
   * Retrieve Knowledge Graph subgraph (nodes & relationships) for a contract.
   */
  async getGraph(contractId: string): Promise<SubgraphResponse> {
    const res = await fetch(`${API_V1}/contracts/${encodeURIComponent(contractId)}/graph`, {
      headers: { Accept: 'application/json' },
    });
    return handleResponse<SubgraphResponse>(res);
  },

  /**
   * Synchronize contract relational data into Knowledge Graph.
   */
  async syncGraph(contractId: string): Promise<SubgraphResponse> {
    const res = await fetch(`${API_V1}/contracts/${encodeURIComponent(contractId)}/sync-graph`, {
      method: 'POST',
      headers: { Accept: 'application/json' },
    });
    return handleResponse<SubgraphResponse>(res);
  },

  /**
   * Find contracts involving a company.
   */
  async queryContractsByCompany(companyName: string): Promise<any[]> {
    const res = await fetch(`${API_V1}/graph/contracts-by-company?company_name=${encodeURIComponent(companyName)}`, {
      headers: { Accept: 'application/json' },
    });
    return handleResponse<any[]>(res);
  },

  /**
   * Find contracts governed by a jurisdiction.
   */
  async queryContractsByJurisdiction(jurisdictionName: string): Promise<any[]> {
    const res = await fetch(`${API_V1}/graph/contracts-by-jurisdiction?jurisdiction_name=${encodeURIComponent(jurisdictionName)}`, {
      headers: { Accept: 'application/json' },
    });
    return handleResponse<any[]>(res);
  },

  /**
   * Perform semantic vector search across contract chunks.
   */
  async performSearch(params: {
    query: string;
    contract_id?: string;
    contract_type?: string;
    section?: string;
    filters?: any;
    top_k?: number;
    min_score?: number;
  }): Promise<SearchResponse> {
    const res = await fetch(`${API_V1}/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(params),
    });
    return handleResponse<SearchResponse>(res);
  },

  /**
   * Ask legal question using grounded RAG pipeline.
   */
  async askQuestion(
    question: string,
    contractId?: string,
    topK: number = 5
  ): Promise<AskResponse> {
    const res = await fetch(`${API_V1}/rag/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        question,
        contract_id: contractId || undefined,
        top_k: topK,
      }),
    });
    return handleResponse<AskResponse>(res);
  },

  /**
   * Query LEXIQ Autonomous Legal AI Agent.
   * Performs multi-step tool selection, evidence verification, and grounded analysis.
   */
  async queryAgent(request: AgentQueryRequest): Promise<AgentQueryResponse> {
    const res = await fetch(`${API_V1}/agent/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(request),
    });
    return handleResponse<AgentQueryResponse>(res);
  },

  /**
   * Retrieve list of authorized Agent tools.
   */
  async getAgentTools(): Promise<AgentToolInfo[]> {
    const res = await fetch(`${API_V1}/agent/tools`, {
      headers: { Accept: 'application/json' },
    });
    return handleResponse<AgentToolInfo[]>(res);
  },

  /**
   * Lookup Indian eCourts case status or generate authorized portal deep links.
   */
  async lookupECourts(request: ECourtsSearchRequest): Promise<ECourtsLookupResponse> {
    const res = await fetch(`${API_V1}/ecourts/lookup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(request),
    });
    return handleResponse<ECourtsLookupResponse>(res);
  },

  /**
   * Ingest and normalize lawfully obtained eCourts record text.
   */
  async ingestECourtsRecord(request: ECourtsIngestRequest): Promise<ECourtsCaseResult> {
    const res = await fetch(`${API_V1}/ecourts/ingest`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(request),
    });
    return handleResponse<ECourtsCaseResult>(res);
  },

  /**
   * AI procedural risk and milestone analysis of eCourts case data.
   */
  async analyzeECourtsCase(request: ECourtsAnalysisRequest): Promise<ECourtsAnalysisResponse> {
    const res = await fetch(`${API_V1}/ecourts/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(request),
    });
    return handleResponse<ECourtsAnalysisResponse>(res);
  },

  /**
   * Get operational status of eCourts integration.
   */
  async getECourtsStatus(): Promise<ECourtsStatusResponse> {
    const res = await fetch(`${API_V1}/ecourts/status`, {
      headers: { Accept: 'application/json' },
    });
    return handleResponse<ECourtsStatusResponse>(res);
  },
};

// =========================================================================
// Agentic AI Type Definitions
// =========================================================================

export interface AgentQueryRequest {
  question: string;
  contract_id?: string | null;
  contract_ids?: string[];
  conversation_id?: string | null;
  max_steps?: number;
}

export interface AgentFinding {
  category: string;
  fact: string;
  contract_id?: string;
  contract_name?: string;
  page_number?: number;
  source_reference?: string;
}

export interface AgentSourceCitation {
  contract_id?: string;
  contract_name?: string;
  document_id?: string;
  chunk_id?: string;
  page_number?: number;
  section?: string;
  source_location?: string;
  snippet?: string;
  relevance_score?: number;
}

export interface AgentQueryResponse {
  answer: string;
  summary: string;
  findings: AgentFinding[];
  sources: AgentSourceCitation[];
  tools_used: string[];
  confidence: 'HIGH' | 'MEDIUM' | 'LOW' | string;
  limitations: string[];
}

export interface AgentToolInfo {
  name: string;
  description: string;
  parameters: any;
}

// =========================================================================
// Indian eCourts Intelligence Type Definitions
// =========================================================================

export type ECourtsIntegrationStatus =
  | 'Official portal link available'
  | 'Manual lookup required'
  | 'Authorized API configured'
  | 'Automated lookup verified';

export interface HearingRecord {
  hearing_date?: string;
  business_recorded?: string;
  next_date?: string;
  purpose?: string;
}

export interface OrderRecord {
  order_date?: string;
  order_number?: string;
  judge_name?: string;
  order_link?: string;
  summary?: string;
}

export interface ECourtsCaseResult {
  cnr_number?: string;
  case_type?: string;
  case_number?: string;
  filing_year?: number;
  filing_date?: string;
  registration_date?: string;
  court_name?: string;
  jurisdiction?: string;
  status: string;
  stage_of_case?: string;
  next_hearing_date?: string;
  purpose_of_hearing?: string;
  petitioner?: string;
  petitioner_advocate?: string;
  respondent?: string;
  respondent_advocate?: string;
  history: HearingRecord[];
  orders: OrderRecord[];
  portal_search_url: string;
  source_url: string;
  retrieved_at: string;
  integration_status: ECourtsIntegrationStatus;
  is_verified_automated: boolean;
  disclaimer: string;
}

export interface ECourtsSearchRequest {
  cnr_number?: string;
  state?: string;
  district?: string;
  court_complex?: string;
  case_type?: string;
  case_number?: string;
  year?: number;
  party_name?: string;
}

export interface ECourtsLookupResponse {
  success: boolean;
  integration_status: ECourtsIntegrationStatus;
  portal_search_url: string;
  message: string;
  case_data?: ECourtsCaseResult;
  suggested_actions: string[];
}

export interface ECourtsIngestRequest {
  raw_text: string;
  source_url?: string;
  cnr_number?: string;
  case_title?: string;
  document_type?: string;
}

export interface ECourtsAnalysisRequest {
  case_data?: ECourtsCaseResult;
  raw_text?: string;
  question?: string;
}

export interface ECourtsAnalysisResponse {
  official_case_facts: Record<string, any>;
  ai_summary: string;
  legal_risk_level: 'HIGH' | 'MEDIUM' | 'LOW' | string;
  key_milestones: string[];
  next_steps: string[];
  limitations: string[];
  source_citation: string;
}

export interface ECourtsStatusResponse {
  integration_mode: string;
  status_label: string;
  official_portal_url: string;
  captcha_protection_active: boolean;
  automated_scraping_permitted: boolean;
  authorized_api_configured: boolean;
  notes: string;
}
