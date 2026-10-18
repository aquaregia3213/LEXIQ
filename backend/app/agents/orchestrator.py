import time
import logging
import re
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.agents.schemas import (
    AgentQueryRequest,
    AgentQueryResponse,
    AgentFinding,
    AgentSourceCitation
)
from backend.app.agents.state import AgentState
from backend.app.agents.prompts import (
    AGENT_SYSTEM_PROMPT,
    INSUFFICIENT_EVIDENCE_MESSAGE,
    LEGAL_DISCLAIMER_TEXT
)
from backend.app.agents.tools import get_all_tools, BaseTool
from backend.app.models.models import Contract

logger = logging.getLogger("legal_ai.agent")


class AgentOrchestrator:
    """
    LEXIQ Agent Orchestrator.
    Controls the multi-step ReAct reasoning and execution loop, tool selection,
    evidence aggregation, and hallucination-resistant grounded response generation.
    """

    def __init__(self, tools: Optional[Dict[str, BaseTool]] = None):
        self.tools = tools or get_all_tools()

    def run(self, db: Session, request: AgentQueryRequest) -> AgentQueryResponse:
        """
        Execute the agent loop for a user legal query.
        """
        req_id = str(uuid.uuid4())
        exec_id = str(uuid.uuid4())
        start_time = time.time()

        # Initialize working state
        state = AgentState(
            request_id=req_id,
            execution_id=exec_id,
            question=request.question.strip(),
            contract_id=request.contract_id,
            contract_ids=request.contract_ids or [],
            conversation_id=request.conversation_id,
            max_steps=min(request.max_steps or 5, 10)
        )

        logger.info(
            f"Agent Execution Started [request_id={req_id}, execution_id={exec_id}]: "
            f"question='{state.question[:100]}', contract_id={state.contract_id}"
        )

        # Pre-resolve contract_id if not given or if multiple given
        self._resolve_target_contracts(db, state)

        # -------------------------------------------------------------
        # Controlled Agent Loop (Max Steps Safeguard)
        # -------------------------------------------------------------
        while state.current_step < state.max_steps:
            # 1. Decide next action/tool based on intent & current evidence
            tool_name, tool_args = self._select_next_tool(db, state)

            if not tool_name or tool_name == "FINISH":
                logger.info(f"Agent decided to finish at step {state.current_step}.")
                break

            tool = self.tools.get(tool_name)
            if not tool:
                logger.warning(f"Unknown tool '{tool_name}' selected. Ending tool loop.")
                break

            # 2. Execute Tool with timing and error trapping
            tool_start = time.time()
            try:
                result = tool.execute(db, **tool_args)
                duration_ms = (time.time() - tool_start) * 1000

                state.record_tool_call(
                    tool_name=tool_name,
                    arguments=tool_args,
                    observation=result.summary_for_agent,
                    duration_ms=duration_ms,
                    success=result.success,
                    evidence=result.evidence
                )

                logger.info(
                    f"Tool Executed [step={state.current_step}, tool={tool_name}, duration={duration_ms:.1f}ms, success={result.success}]: "
                    f"{result.summary_for_agent[:120]}"
                )

            except Exception as e:
                duration_ms = (time.time() - tool_start) * 1000
                err_msg = f"Tool execution error: {str(e)}"
                logger.error(f"Tool Failed [tool={tool_name}]: {err_msg}")
                state.record_tool_call(
                    tool_name=tool_name,
                    arguments=tool_args,
                    observation=err_msg,
                    duration_ms=duration_ms,
                    success=False,
                    evidence=[]
                )

        # 3. Assess if collected evidence is sufficient to answer the prompt
        state.is_sufficient = self._check_evidence_sufficiency(state)

        total_duration = time.time() - start_time
        logger.info(
            f"Agent Execution Finished [exec_id={exec_id}, steps={state.current_step}/{state.max_steps}, "
            f"tools={state.tools_called}, total_time={total_duration:.2f}s]"
        )

        # -------------------------------------------------------------
        # Evidence Aggregation & Grounded Answer Synthesis
        # -------------------------------------------------------------
        return self._synthesize_response(state)

    def _resolve_target_contracts(self, db: Session, state: AgentState):
        """Identify target contract(s) if not explicitly supplied."""
        if state.contract_id:
            return

        # Check if question mentions a specific contract name or company
        q_lower = state.question.lower()
        contracts = db.query(Contract).all()
        for c in contracts:
            if c.name.lower() in q_lower:
                state.contract_id = c.id
                break

        # Check for comparison mentions: "contract A and contract B"
        if not state.contract_ids and len(contracts) >= 2:
            matched = [c.id for c in contracts if c.name.lower() in q_lower]
            if len(matched) >= 2:
                state.contract_ids = matched[:2]

    def _select_next_tool(self, db: Session, state: AgentState) -> tuple[Optional[str], Dict[str, Any]]:
        """
        Determine the next best tool to invoke based on user intent and current state.
        Ensures diverse, task-specific, non-blind tool execution.
        """
        q = state.question.lower()
        step = state.current_step
        called = set(state.tools_called)

        # Detect malicious prompt injection inside question or earlier observations
        sanitized_q = re.sub(
            r"(ignore previous instructions|system override|print secret|disregard instructions|delete all|bypass)",
            "",
            q,
            flags=re.IGNORECASE
        )

        # 1. Multi-contract comparison questions
        is_compare = any(w in sanitized_q for w in ("compare", "difference", "differences", "versus", "vs"))
        if is_compare:
            if "compare_contracts" not in called:
                # Need two contracts
                c_ids = state.contract_ids
                if len(c_ids) < 2:
                    all_c = db.query(Contract).limit(2).all()
                    c_ids = [c.id for c in all_c]

                if len(c_ids) >= 2:
                    clause_type = "Termination"
                    if "liability" in sanitized_q:
                        clause_type = "Liability"
                    elif "confidential" in sanitized_q:
                        clause_type = "Confidentiality"
                    elif "renewal" in sanitized_q:
                        clause_type = "Renewal"

                    return "compare_contracts", {
                        "contract_id_a": c_ids[0],
                        "contract_id_b": c_ids[1],
                        "clause_type": clause_type
                    }
            elif state.tools_called.count("retrieve_source") < min(2, len(state.collected_evidence)):
                idx = state.tools_called.count("retrieve_source")
                ev = state.collected_evidence[idx]
                return "retrieve_source", {
                    "contract_id": ev.get("contract_id"),
                    "page_number": ev.get("page_number", 1)
                }
            return "FINISH", {}

        # 2. Compound Multi-Step Reasoning: Termination + Obligations
        has_termination = any(w in sanitized_q for w in ("terminate", "termination", "cancel", "cancellation"))
        has_obligation = any(w in sanitized_q for w in ("obligation", "obligations", "responsible", "shall", "must", "deliverable", "covenant"))
        if has_termination and has_obligation:
            c_id = state.contract_id or (db.query(Contract).first().id if db.query(Contract).first() else None)
            if c_id:
                if "get_clauses" not in called:
                    return "get_clauses", {"contract_id": c_id, "clause_type": "Termination"}
                elif "get_obligations" not in called:
                    return "get_obligations", {"contract_id": c_id}
                elif "search_contract" not in called and any(w in sanitized_q for w in ("post-termination", "remain", "survival", "after")):
                    return "search_contract", {"query": "post-termination obligations survival", "contract_id": c_id}
                elif "retrieve_source" not in called and state.collected_evidence:
                    ev = state.collected_evidence[0]
                    return "retrieve_source", {
                        "contract_id": ev.get("contract_id"),
                        "page_number": ev.get("page_number", 1)
                    }
                return "FINISH", {}

        # 3. Knowledge Graph & Party Responsibility questions
        is_party_query = "which party" in sanitized_q or "responsible party" in sanitized_q
        is_graph_query = is_party_query or any(w in sanitized_q for w in ("relationship", "relationships", "involving", "governed by", "party to", "jurisdiction", "companies", "graph"))
        if is_graph_query:
            c_id = state.contract_id or (db.query(Contract).first().id if db.query(Contract).first() else None)

            # If asking specifically which party is responsible, identify entities first
            if is_party_query and "get_entities" not in called and c_id:
                return "get_entities", {"contract_id": c_id}

            if "query_knowledge_graph" not in called:
                # Check for jurisdiction
                j_match = re.search(r"jurisdiction\s+of\s+([A-Za-z]+)|governed\s+by\s+([A-Za-z]+)", sanitized_q)
                if j_match:
                    target = (j_match.group(1) or j_match.group(2)).strip()
                    return "query_knowledge_graph", {"query_type": "by_jurisdiction", "target": target}

                # Check for company
                c_match = re.search(r"company\s+([A-Za-z0-9]+)|involving\s+([A-Za-z0-9]+)", sanitized_q)
                if c_match:
                    target = (c_match.group(1) or c_match.group(2)).strip()
                    return "query_knowledge_graph", {"query_type": "by_company", "target": target}

                # Default to contract subgraph
                if c_id:
                    return "query_knowledge_graph", {"query_type": "contract_subgraph", "target": c_id}

            if "get_entities" not in called and c_id:
                return "get_entities", {"contract_id": c_id}

            if "get_obligations" not in called and c_id and any(w in sanitized_q for w in ("obligation", "responsible", "duty", "duties")):
                return "get_obligations", {"contract_id": c_id}

            if "get_clauses" not in called and c_id:
                c_type = None
                for t in ["Data Protection", "Confidentiality", "Termination", "Liability", "Governing Law"]:
                    if t.lower() in sanitized_q:
                        c_type = t
                        break
                if c_type:
                    return "get_clauses", {"contract_id": c_id, "clause_type": c_type}

            if "retrieve_source" not in called and state.collected_evidence:
                ev = state.collected_evidence[0]
                return "retrieve_source", {
                    "contract_id": ev.get("contract_id"),
                    "page_number": ev.get("page_number", 1)
                }

            return "FINISH", {}

        # 4. Risk questions
        is_risk = any(w in sanitized_q for w in ("risk", "risks", "liability exposure", "liability cap", "uncapped", "dangerous", "unfavorable"))
        if is_risk:
            c_id = state.contract_id or (db.query(Contract).first().id if db.query(Contract).first() else None)
            if "get_risks" not in called and c_id:
                return "get_risks", {"contract_id": c_id}

            elif "get_clauses" not in called and c_id:
                c_type = "Liability" if "liability" in sanitized_q else "Termination"
                return "get_clauses", {"contract_id": c_id, "clause_type": c_type}

            elif "retrieve_source" not in called and state.collected_evidence:
                ev = state.collected_evidence[0]
                return "retrieve_source", {
                    "contract_id": ev.get("contract_id"),
                    "page_number": ev.get("page_number", 1)
                }
            return "FINISH", {}

        # 5. Obligation questions
        is_obligation = any(w in sanitized_q for w in ("obligation", "obligations", "shall", "must", "deliverable", "responsible party", "deadline", "covenant"))
        if is_obligation:
            c_id = state.contract_id or (db.query(Contract).first().id if db.query(Contract).first() else None)
            if "get_obligations" not in called and c_id:
                party = None
                if "vendor" in sanitized_q:
                    party = "Vendor"
                elif "customer" in sanitized_q:
                    party = "Customer"
                elif "client" in sanitized_q:
                    party = "Client"
                return "get_obligations", {"contract_id": c_id, "party": party}

            elif "search_contract" not in called and len(state.collected_evidence) == 0:
                # Fallback to semantic search if obligations empty
                return "search_contract", {"query": state.question, "contract_id": c_id}

            elif "retrieve_source" not in called and state.collected_evidence:
                ev = state.collected_evidence[0]
                return "retrieve_source", {
                    "contract_id": ev.get("contract_id"),
                    "page_number": ev.get("page_number", 1)
                }
            return "FINISH", {}

        # 6. Clause classification / Rights questions (Termination, Confidentiality, Governing Law, etc.)
        is_clause = any(w in sanitized_q for w in ("clause", "clauses", "termination", "confidentiality", "indemnification", "renewal", "ip rights", "governing law", "dispute", "law"))
        if is_clause:
            c_id = state.contract_id or (db.query(Contract).first().id if db.query(Contract).first() else None)
            if "get_clauses" not in called and c_id:
                c_type = None
                for t in ["Termination", "Liability", "Indemnification", "Confidentiality", "Payment", "Renewal", "Governing Law"]:
                    if t.lower() in sanitized_q:
                        c_type = t
                        break
                return "get_clauses", {"contract_id": c_id, "clause_type": c_type}

            elif "retrieve_source" not in called and state.collected_evidence:
                ev = state.collected_evidence[0]
                return "retrieve_source", {
                    "contract_id": ev.get("contract_id"),
                    "page_number": ev.get("page_number", 1)
                }

            elif "search_contract" not in called and len(state.collected_evidence) == 0:
                return "search_contract", {"query": state.question, "contract_id": state.contract_id}

            return "FINISH", {}

        # 7. General / Semantic Search Questions
        if "search_contract" not in called:
            return "search_contract", {
                "query": state.question,
                "contract_id": state.contract_id,
                "top_k": 4
            }
        elif "get_contract" not in called and state.contract_id:
            return "get_contract", {"contract_id": state.contract_id}
        elif "retrieve_source" not in called and state.collected_evidence:
            ev = state.collected_evidence[0]
            return "retrieve_source", {
                "contract_id": ev.get("contract_id"),
                "page_number": ev.get("page_number", 1)
            }

        return "FINISH", {}

    def _stem_word(self, w: str) -> str:
        """Simple morphological stemmer for English plurals and inflections."""
        w = w.lower()
        if w.endswith("ies") and len(w) > 4:
            return w[:-3] + "y"
        if w.endswith("es") and len(w) > 4:
            return w[:-2]
        if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
            return w[:-1]
        return w

    def _matches_query_terms(self, text: str, query_words: set[str]) -> bool:
        """Check if text contains any substantive query word or its morphological stem."""
        clean_text = text.lower()
        for w in query_words:
            if w in clean_text or self._stem_word(w) in clean_text:
                return True
        return False

    def _check_evidence_sufficiency(self, state: AgentState) -> bool:
        """Evaluate whether enough reliable evidence has been collected to formulate a complete answer."""
        if not state.collected_evidence:
            return False

        q_words = set(re.findall(r"\w+", state.question.lower())) - {
            "what", "which", "is", "are", "the", "a", "an", "in", "on", "of", "to", "for",
            "contract", "contracts", "agreement", "party", "parties", "does", "do", "has",
            "have", "contains", "state", "under", "say", "saying", "tell", "show", "give",
            "vendor", "customer", "if", "this", "that", "and", "or", "any", "all", "about",
            "how", "when", "where", "who", "why", "with", "from", "into", "their"
        }
        if not q_words:
            return len(state.collected_evidence) > 0

        # Check if collected evidence contains substantive terms from query
        matching_count = 0
        for ev in state.collected_evidence:
            snippet = (ev.get("snippet") or ev.get("text") or "").lower()
            loc = (ev.get("source_location") or "").lower()
            sec = (ev.get("section") or "").lower()
            combined = f"{snippet} {loc} {sec}"
            if self._matches_query_terms(combined, q_words):
                matching_count += 1

        return matching_count > 0

    def _synthesize_response(self, state: AgentState) -> AgentQueryResponse:
        """
        Aggregate verified evidence, sanitize against prompt injection, and assemble
        standardized AgentQueryResponse with citations, findings, confidence, and limitations.
        """
        # Security: sanitize question and untrusted contract content
        sanitized_q = re.sub(
            r"(ignore previous instructions|system override|print secret|disregard instructions)",
            "[redacted]",
            state.question,
            flags=re.IGNORECASE
        )

        q_words = set(re.findall(r"\w+", sanitized_q.lower())) - {
            "what", "which", "is", "are", "the", "a", "an", "in", "on", "of", "to", "for",
            "contract", "contracts", "agreement", "party", "parties", "does", "do", "has",
            "have", "contains", "state", "under", "say", "saying", "tell", "show", "give",
            "vendor", "customer", "if", "this", "that", "and", "or", "any", "all", "about",
            "how", "when", "where", "who", "why", "with", "from", "into", "their"
        }

        # Filter evidence to those with substantive relevance to question
        relevant_evidence = []
        for ev in state.collected_evidence:
            snippet = (ev.get("snippet") or ev.get("text") or "").lower()
            loc = (ev.get("source_location") or "").lower()
            sec = (ev.get("section") or "").lower()
            combined = f"{snippet} {loc} {sec}"
            if not q_words or self._matches_query_terms(combined, q_words):
                relevant_evidence.append(ev)

        # 1. Handle Insufficient Evidence Case
        if not relevant_evidence or not state.is_sufficient:
            return AgentQueryResponse(
                answer=INSUFFICIENT_EVIDENCE_MESSAGE,
                summary="Insufficient evidence found in the contract repository.",
                findings=[],
                sources=[],
                tools_used=state.tools_called,
                confidence="LOW",
                limitations=[
                    "The contract repository or specified contract document did not contain verifiable evidence addressing this query.",
                    "No factual claims could be substantiated."
                ]
            )

        # 2. Extract structured findings
        findings: List[AgentFinding] = []
        sources: List[AgentSourceCitation] = []
        seen_sources = set()

        for idx, ev in enumerate(relevant_evidence):
            snippet = ev.get("snippet") or ev.get("text") or ""
            # Sanitize snippet against prompt injection directives
            clean_snippet = re.sub(
                r"(ignore previous instructions|system override|print secret|disregard instructions)",
                "[redacted]",
                snippet,
                flags=re.IGNORECASE
            )

            p_num = ev.get("page_number") or ev.get("page_start", 1)
            c_id = ev.get("contract_id")
            c_name = ev.get("contract_name") or "Contract Document"
            loc = ev.get("source_location") or f"Page {p_num}"
            sec = ev.get("section") or "General"

            # Create finding
            findings.append(AgentFinding(
                category=sec.lower() if sec else "clause",
                fact=clean_snippet[:220].strip() + ("..." if len(clean_snippet) > 220 else ""),
                contract_id=c_id,
                contract_name=c_name,
                page_number=p_num,
                source_reference=loc
            ))

            # Deduplicate source citation
            s_key = (c_id, p_num, sec, clean_snippet[:50])
            if s_key not in seen_sources:
                seen_sources.add(s_key)
                sources.append(AgentSourceCitation(
                    contract_id=c_id,
                    contract_name=c_name,
                    document_id=ev.get("document_id"),
                    chunk_id=ev.get("chunk_id"),
                    page_number=p_num,
                    section=sec,
                    source_location=loc,
                    snippet=clean_snippet.strip(),
                    relevance_score=ev.get("relevance_score", 0.90)
                ))

        # 3. Synthesize comprehensive grounded answer
        from backend.app.config import settings
        from backend.app.services.llm import get_llm_service

        final_answer = None
        if settings.active_ai_provider == "gemini" and settings.GEMINI_API_KEY:
            try:
                evidence_payload = [
                    {
                        "chunk_id": s.chunk_id or f"ev-{i}",
                        "contract_name": s.contract_name,
                        "section": s.section,
                        "page_start": s.page_number,
                        "page_end": s.page_number,
                        "text": s.snippet
                    }
                    for i, s in enumerate(sources)
                ]
                gemini_res = get_llm_service().generate_grounded_answer(
                    question=state.question,
                    evidence_chunks=evidence_payload
                )
                final_answer = gemini_res.get("answer")
            except Exception as e:
                logger.error(f"Gemini agent synthesis failed: {e}")
                raise

        if not final_answer:
            answer_parts = []
            for src in sources[:4]:
                answer_parts.append(
                    f"According to {src.contract_name} ({src.source_location}): \"{src.snippet}\""
                )

            final_answer = "\n\n".join(answer_parts)
            if not final_answer:
                final_answer = INSUFFICIENT_EVIDENCE_MESSAGE

            # Add mandatory legal safety disclaimer
            final_answer += f"\n\n---\n{LEGAL_DISCLAIMER_TEXT}"


        # 4. Synthesize summary
        primary_source = sources[0] if sources else None
        summary = (
            f"Analysis of '{primary_source.contract_name if primary_source else 'contracts'}' identified "
            f"{len(findings)} relevant provision(s) across {len(sources)} source location(s)."
        )

        # 5. Determine confidence
        confidence = "HIGH" if len(sources) >= 2 else "MEDIUM"

        limitations = [
            "Analysis is constrained strictly to the uploaded contract text and verified chunk references.",
            "AI-assisted output does not constitute formal legal counsel."
        ]
        if state.current_step >= state.max_steps:
            limitations.append("Maximum reasoning step budget reached; some secondary relations may require manual inspection.")

        return AgentQueryResponse(
            answer=final_answer,
            summary=summary,
            findings=findings,
            sources=sources,
            tools_used=state.tools_called,
            confidence=confidence,
            limitations=limitations
        )


_default_orchestrator = AgentOrchestrator()


def get_agent_orchestrator() -> AgentOrchestrator:
    """Return default singleton AgentOrchestrator instance."""
    return _default_orchestrator
