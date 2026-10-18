# Langflow Integration Architecture & Operations Guide

## 1. Executive Overview

Langflow serves as the visual and autonomous agent workflow orchestration layer for **LEXIQ: Agentic AI-Powered Legal Contract Intelligence Platform**. 

This integration preserves FastAPI as the authoritative backend for:
- User authentication and authorization
- Input validation and sanitization
- Relational database and vector search access
- Contract file management and document parsing
- Tenant isolation and audit logging

Langflow **never directly accesses the PostgreSQL/pgvector database**. Instead, Langflow coordinates multi-step reasoning loops and invokes approved legal retrieval tools strictly through an authenticated FastAPI tool execution interface.

---

## 2. Target Architecture

```mermaid
graph TD
    User([Legal Analyst / User]) -->|HTTPS| Frontend[Next.js Frontend]
    Frontend -->|REST API| FastAPI[FastAPI Backend :8000]
    
    subgraph FastAPI Boundary [FastAPI Authoritative Services]
        FastAPI --> Auth[Auth & Tenant Isolation]
        FastAPI --> AgentRouter[/api/v1/agent/query]
        FastAPI --> ToolExec[/api/v1/agent/tools/execute]
        ToolExec --> ToolRegistry[Registered Legal Tools]
        ToolRegistry --> DB[(PostgreSQL + pgvector)]
        ToolRegistry --> KG[(Neo4j Knowledge Graph)]
    end

    subgraph Langflow Boundary [Secured Orchestration Layer]
        AgentRouter -->|Server-to-Server REST| LFClient[LangflowClientService]
        LFClient -->|HTTP POST /api/v1/run/{flow_id}| LangflowEngine[Langflow Workflow Engine :7860]
        
        LangflowEngine --> ChatInput[ChatInput Node]
        ChatInput --> PromptNode[Legal Synthesis Prompt]
        LangflowEngine --> ToolCaller[LEXIQ Tool Caller Component]
        ToolCaller -->|Authenticated HTTP with X-LEXIQ-API-KEY| ToolExec
        PromptNode --> GeminiNode[Google Gemini 2.5 Flash]
        GeminiNode --> StructuredOutput[ChatOutput Node]
    end

    FastAPI -.->|Automatic Failover if Langflow Offline| NativeOrch[Native AgentOrchestrator]
```

### Request Flow Sequence
1. **User Request**: The Next.js frontend sends a legal question to `POST /api/v1/agent/query`.
2. **Orchestrator Selection**: FastAPI checks `settings.AGENT_ORCHESTRATOR`:
   - If set to `"langflow"`, it delegates the query to `LangflowClientService`.
   - If set to `"native"` (default), it invokes the built-in `AgentOrchestrator`.
3. **Workflow Invocation**: `LangflowClientService` executes `POST {LANGFLOW_BASE_URL}/api/v1/run/{LANGFLOW_FLOW_ID}` with the user's question, contract parameters, and tenant context.
4. **Tool Execution over HTTP**: When Langflow requires contract data, the `LEXIQToolCaller` custom component sends an HTTP POST request to `POST /api/v1/agent/tools/execute` on FastAPI.
5. **Security & Tenant Validation**: FastAPI verifies the `x-lexiq-api-key` header and ensures the requesting user has authorization to access the target contract.
6. **Tool Processing**: The tool executes against PostgreSQL/pgvector and returns standardized evidence and summaries.
7. **Gemini Synthesis**: Langflow invokes Google Gemini (`gemini-2.5-flash`) to synthesize an evidence-grounded legal answer.
8. **Response Parsing & Validation**: `LangflowClientService` validates the structured response against `AgentQueryResponse` and delivers it to the frontend.
9. **Failover Protection**: If Langflow is unreachable or times out, FastAPI automatically fails over to the native orchestrator when `LANGFLOW_FALLBACK_TO_NATIVE=true`.

---

## 3. Service Boundaries & Responsibilities

| Responsibility | Handled By | Rationale |
| :--- | :--- | :--- |
| **User Authentication & RBAC** | FastAPI | Centralized session management and JWT/cookie validation. |
| **Tenant Contract Isolation** | FastAPI | Prevents unauthorized cross-tenant contract access. |
| **Database & Vector Operations** | FastAPI (`pgvector`) | Langflow remains a client; no raw SQL credentials in Langflow. |
| **Knowledge Graph Queries** | FastAPI (`neo4j`) | Managed connections and graph schema consistency. |
| **Legal Agent Workflow** | Langflow (or Native fallback) | Visual workflow editing, prompt iteration, and dynamic routing. |
| **LLM Reasoning & Synthesis** | Google Gemini (`gemini-2.5-flash`) | Multimodal legal reasoning with citation verification. |
| **Response Validation** | FastAPI (`pydantic`) | Guarantees strongly-typed outputs for Next.js frontend. |

---

## 4. Pinned Langflow Version & Deployment

### Recommended Version
- **Pinned Package**: `langflow>=1.2.0, <2.0.0`
- **Docker Image**: `langflowai/langflow:1.2.0`

### Why Docker or Dedicated Service?
Langflow contains heavy dependencies (e.g. data connectors, Celery, multiple vector stores). Running Langflow in a dedicated container or separate virtual environment preserves LEXIQ's lightweight FastAPI runtime and prevents library version conflicts.

```bash
# Run Langflow via Docker on port 7860
docker run -d \
  -p 7860:7860 \
  -v langflow-data:/app/data \
  --name lexiq-langflow \
  langflowai/langflow:latest
```

---

## 5. Flow Import & Setup Instructions

### Step 1: Open Langflow UI
Navigate to `http://localhost:7860` in your web browser.

### Step 2: Import the Flow
1. Click **My Collection** $\rightarrow$ **Upload**.
2. Select [`flows/lexiq_legal_agent_flow.json`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/flows/lexiq_legal_agent_flow.json).
3. The visual graph will load with:
   - **Contract Query Input** (`ChatInput`)
   - **LEXIQ Legal Tool Caller** (`CustomComponent`)
   - **Legal Synthesis Prompt** (`Prompt`)
   - **Google Gemini 2.5 Flash** (`GoogleGenerativeAIModel`)
   - **Structured Agent Output** (`ChatOutput`)

### Step 3: Install the Custom Tool Caller Component
In Langflow, custom components can be added directly:
- Open [`flows/custom_components/lexiq_tool_caller.py`](file:///c:/Users/Atharva%20Jadhav/OneDrive/Desktop/Clg%20stuff/Projects/SYMINIPROJECT/flows/custom_components/lexiq_tool_caller.py).
- Copy the Python code and paste it into a **Custom Component** node in Langflow.
- Configure `lexiq_api_url` to `http://localhost:8000` (or `http://host.docker.internal:8000` if running inside Docker).

### Step 4: Obtain Flow ID and API Key
1. In Langflow, click **API** in the upper right corner of your flow.
2. Copy the **Flow ID** (e.g. `c8e04b4d-17e9-4e78-8d2a-438992e16d2b`).
3. If API authentication is enabled in your Langflow instance, generate an **API Key** under Settings $\rightarrow$ API Keys.

---

## 6. Environment Configuration

Add the following variables to your `.env` file:

```env
# Agent Orchestration Configuration
# Set to 'langflow' to route queries through Langflow, or 'native' for built-in orchestrator
AGENT_ORCHESTRATOR=langflow

# Langflow Service Endpoint
LANGFLOW_BASE_URL=http://localhost:7860
LANGFLOW_FLOW_ID=your_imported_flow_id_here
LANGFLOW_API_KEY=your_langflow_api_key_if_enabled

# Operational Safeguards
LANGFLOW_TIMEOUT_SECONDS=30.0
LANGFLOW_FALLBACK_TO_NATIVE=true

# Server-to-Server Internal Security Key
LEXIQ_INTERNAL_API_KEY=lexiq_internal_secret_token
```

---

## 7. Security & Safeguards

### Authenticated Server-to-Server Tool Execution
All calls from Langflow to `POST /api/v1/agent/tools/execute` require the header:
```http
x-lexiq-api-key: lexiq_internal_secret_token
```
Requests without this header or with an invalid key are rejected with `HTTP 401 Unauthorized` using constant-time comparison (`secrets.compare_digest`).

### Multi-Tenant Isolation
When a tool request specifies `contract_id` and `user_id`:
1. FastAPI queries the contract in the database.
2. If `contract.uploaded_by != user_id`, FastAPI aborts the request immediately with `HTTP 403 Forbidden`.
3. Langflow cannot bypass this boundary.

### Loop Prevention & Timeouts
- **Request Timeout**: Configured via `LANGFLOW_TIMEOUT_SECONDS` (default: 30.0s).
- **Execution Safeguard**: Native fallback ensures client queries do not fail if Langflow takes too long or experiences an internal crash.
- **Tool Parameter Validation**: Every tool validates arguments against its JSON Schema before execution.
