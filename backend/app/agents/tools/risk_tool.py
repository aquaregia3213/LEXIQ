from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.agents.tools.base import BaseTool, ToolResult
from backend.app.models.models import Contract, RiskFlag, Clause
from backend.app.services.risk_analyzer import get_risk_analyzer


class GetRisksTool(BaseTool):
    """Tool for retrieving identified risk flags (unlimited liability, automatic renewal, etc.)."""
    name = "get_risks"
    description = (
        "Retrieve identified contract risk flags including unlimited liability, automatic renewal, "
        "broad indemnification, restrictive termination, and unusual IP provisions. "
        "Can be filtered by severity ('HIGH', 'MEDIUM', 'LOW')."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "contract_id": {
                "type": "string",
                "description": "The UUID of the contract."
            },
            "severity": {
                "type": "string",
                "description": "Optional severity level filter ('HIGH', 'MEDIUM', 'LOW')."
            },
            "risk_type": {
                "type": "string",
                "description": "Optional specific risk category (e.g., 'unlimited_liability', 'automatic_renewal')."
            }
        },
        "required": ["contract_id"]
    }

    def execute(self, db: Session, **kwargs) -> ToolResult:
        try:
            self.validate_args(kwargs)
            contract_id = kwargs.get("contract_id")
            severity = kwargs.get("severity")
            risk_type = kwargs.get("risk_type")

            contract = db.query(Contract).filter(Contract.id == contract_id).first()
            if not contract:
                return ToolResult(
                    success=False,
                    data=[],
                    error=f"Contract with id '{contract_id}' not found.",
                    summary_for_agent=f"Contract '{contract_id}' not found."
                )

            risks = db.query(RiskFlag).filter(RiskFlag.contract_id == contract_id).all()
            if not risks:
                try:
                    analyzer = get_risk_analyzer()
                    risks = analyzer.analyze_and_store_contract_risks(db=db, contract_id=contract_id)
                except Exception:
                    risks = []

            if severity:
                clean_sev = severity.strip().upper()
                risks = [r for r in risks if r.severity.upper() == clean_sev]

            if risk_type:
                clean_rt = risk_type.strip().lower()
                risks = [r for r in risks if clean_rt in r.risk_type.lower()]

            if not risks:
                crit_msg = []
                if severity:
                    crit_msg.append(f"severity '{severity}'")
                if risk_type:
                    crit_msg.append(f"type '{risk_type}'")
                extra = f" matching {', '.join(crit_msg)}" if crit_msg else ""
                return ToolResult(
                    success=True,
                    data=[],
                    evidence=[],
                    summary_for_agent=f"No risk flags{extra} found in contract '{contract.name}'."
                )

            data = []
            evidence = []
            for r in risks:
                loc = "Contract Document Text"
                page_num = 1
                if r.clause_id:
                    clause = db.query(Clause).filter(Clause.id == r.clause_id).first()
                    if clause:
                        loc = f"Clause ({clause.clause_type}), Page {clause.page_number}"
                        page_num = clause.page_number

                item_dict = {
                    "risk_id": r.id,
                    "contract_id": r.contract_id,
                    "clause_id": r.clause_id,
                    "risk_type": r.risk_type,
                    "severity": r.severity,
                    "description": r.description,
                    "evidence": r.evidence,
                    "confidence": round(r.confidence, 4),
                    "source_location": loc
                }
                data.append(item_dict)

                evidence.append({
                    "contract_id": r.contract_id,
                    "contract_name": contract.name,
                    "clause_id": r.clause_id,
                    "page_number": page_num,
                    "section": r.risk_type,
                    "source_location": loc,
                    "snippet": f"[{r.severity} RISK - {r.risk_type}] {r.description} (Evidence: '{r.evidence}')",
                    "relevance_score": r.confidence
                })

            summary = f"Found {len(risks)} risk flag(s) in '{contract.name}': " + ", ".join(
                f"{r.risk_type} ({r.severity})" for r in risks[:4]
            )
            return ToolResult(
                success=True,
                data=data,
                evidence=evidence,
                summary_for_agent=summary
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=[],
                error=f"GetRisksTool failed: {str(e)}",
                summary_for_agent=f"Error retrieving risks: {str(e)}"
            )


class AnalyzeRiskTool(BaseTool):
    """Tool for analyzing a specific clause or raw text snippet for potential hazards."""
    name = "analyze_risk"
    description = (
        "Evaluate a specific clause text or paragraph for potential risks and liabilities, "
        "such as uncapped damages, automatic renewal traps, or broad indemnities."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The specific clause text or snippet to analyze."
            },
            "clause_type": {
                "type": "string",
                "description": "Optional category of clause (e.g., 'Liability', 'Renewal')."
            }
        },
        "required": ["text"]
    }

    def execute(self, db: Session, **kwargs) -> ToolResult:
        try:
            self.validate_args(kwargs)
            text = kwargs.get("text", "").strip()
            clause_type = kwargs.get("clause_type")

            analyzer = get_risk_analyzer()
            risks = analyzer.analyze_clause_text(clause_text=text, clause_type=clause_type)

            evidence = []
            for r in risks:
                evidence.append({
                    "source_location": "Snippet Analysis",
                    "snippet": f"Risk: {r['risk_type']} ({r['severity']}): {r['description']}",
                    "relevance_score": r.get("confidence", 0.88)
                })

            summary = f"Snippet analysis detected {len(risks)} risk(s)." if risks else "Snippet analysis detected no obvious high-risk patterns."
            return ToolResult(
                success=True,
                data=risks,
                evidence=evidence,
                summary_for_agent=summary
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=[],
                error=f"AnalyzeRiskTool failed: {str(e)}",
                summary_for_agent=f"Error analyzing risk in snippet: {str(e)}"
            )
