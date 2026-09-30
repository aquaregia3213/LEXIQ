from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.models.models import Contract, Entity, Clause, Obligation, RiskFlag
from backend.app.services.extractor import normalize_entity_name


class BaseGraphProvider(ABC):
    """Abstract base interface for Knowledge Graph providers."""

    @abstractmethod
    def sync_contract_nodes(
        self,
        contract: Dict[str, Any],
        companies: List[Dict[str, Any]],
        persons: List[Dict[str, Any]],
        clauses: List[Dict[str, Any]],
        obligations: List[Dict[str, Any]],
        jurisdictions: List[Dict[str, Any]],
        risks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create/merge nodes and relationships for a contract."""
        pass

    @abstractmethod
    def query_contracts_by_company(self, company_name: str) -> List[Dict[str, Any]]:
        """1. Find contracts involving a company."""
        pass

    @abstractmethod
    def query_clauses_by_contract(self, contract_id: str) -> List[Dict[str, Any]]:
        """2. Find clauses inside a contract."""
        pass

    @abstractmethod
    def query_obligations_by_contract(self, contract_id: str) -> List[Dict[str, Any]]:
        """3. Find obligations belonging to a contract."""
        pass

    @abstractmethod
    def query_contracts_by_jurisdiction(self, jurisdiction_name: str) -> List[Dict[str, Any]]:
        """4. Find contracts governed by a jurisdiction."""
        pass

    @abstractmethod
    def get_contract_subgraph(self, contract_id: str) -> Dict[str, Any]:
        """Return nodes and edges subgraph for a contract."""
        pass

    @abstractmethod
    def delete_contract_nodes(self, contract_id: str) -> None:
        """Purge all nodes and edges belonging to a contract from the knowledge graph."""
        pass


class InMemoryGraphProvider(BaseGraphProvider):
    """
    In-Memory Knowledge Graph provider implementation for local testing and demonstration.
    Stores nodes and directed edge relationships in Python memory structures.
    """

    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []

    def sync_contract_nodes(
        self,
        contract: Dict[str, Any],
        companies: List[Dict[str, Any]],
        persons: List[Dict[str, Any]],
        clauses: List[Dict[str, Any]],
        obligations: List[Dict[str, Any]],
        jurisdictions: List[Dict[str, Any]],
        risks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        contract_id = contract["id"]
        c_node_key = f"Contract:{contract_id}"

        # Add/update Contract node
        self.nodes[c_node_key] = {
            "id": contract_id,
            "label": "Contract",
            "name": contract["name"],
            "type": contract.get("contract_type", "General"),
            "date": contract.get("created_at", "")
        }

        # Clear existing edges for this contract to maintain idempotency
        self.edges = [e for e in self.edges if e["source"] != c_node_key and e["target"] != c_node_key]

        # 1. Company nodes & relationships
        for comp in companies:
            norm_name = comp.get("normalized_name") or comp["name"]
            comp_key = f"Company:{norm_name.lower()}"
            self.nodes[comp_key] = {
                "id": comp_key,
                "label": "Company",
                "name": comp["name"],
                "normalized_name": norm_name
            }
            # Add edges (Company)-[:PARTY_TO]->(Contract) and (Company)-[:SIGNED]->(Contract)
            self.edges.append({"source": comp_key, "target": c_node_key, "type": "PARTY_TO"})
            self.edges.append({"source": comp_key, "target": c_node_key, "type": "SIGNED"})

        # 2. Person nodes & relationships
        for p in persons:
            p_name = p["name"]
            p_key = f"Person:{p_name.lower()}"
            self.nodes[p_key] = {
                "id": p_key,
                "label": "Person",
                "name": p_name
            }
            # Edge (Contract)-[:INVOLVES]->(Person)
            self.edges.append({"source": c_node_key, "target": p_key, "type": "INVOLVES"})

        # 3. Clause nodes & relationships
        for cl in clauses:
            cl_id = cl["id"]
            cl_key = f"Clause:{cl_id}"
            self.nodes[cl_key] = {
                "id": cl_id,
                "label": "Clause",
                "type": cl["clause_type"],
                "text": cl["text"]
            }
            # Edge (Contract)-[:CONTAINS]->(Clause)
            self.edges.append({"source": c_node_key, "target": cl_key, "type": "CONTAINS"})

        # 4. Obligation nodes & relationships
        for ob in obligations:
            ob_id = ob["id"]
            ob_key = f"Obligation:{ob_id}"
            self.nodes[ob_key] = {
                "id": ob_id,
                "label": "Obligation",
                "description": ob["description"],
                "deadline": ob.get("deadline", "N/A")
            }
            # Edge (Contract)-[:HAS_OBLIGATION]->(Obligation)
            self.edges.append({"source": c_node_key, "target": ob_key, "type": "HAS_OBLIGATION"})

        # 5. Jurisdiction nodes & relationships
        for j in jurisdictions:
            j_name = j["name"]
            j_key = f"Jurisdiction:{j_name.lower()}"
            self.nodes[j_key] = {
                "id": j_key,
                "label": "Jurisdiction",
                "name": j_name
            }
            # Edge (Contract)-[:GOVERNED_BY]->(Jurisdiction)
            self.edges.append({"source": c_node_key, "target": j_key, "type": "GOVERNED_BY"})

        # 6. Risk nodes & relationships
        for r in risks:
            r_id = r["id"]
            r_key = f"Risk:{r_id}"
            self.nodes[r_key] = {
                "id": r_id,
                "label": "Risk",
                "type": r["risk_type"],
                "severity": r.get("severity", "MEDIUM")
            }
            # Edge (Contract)-[:HAS_RISK]->(Risk)
            self.edges.append({"source": c_node_key, "target": r_key, "type": "HAS_RISK"})

        return self.get_contract_subgraph(contract_id)

    def query_contracts_by_company(self, company_name: str) -> List[Dict[str, Any]]:
        """1. Find contracts involving a company."""
        clean_name = company_name.lower().strip()
        matching_contracts = []

        for e in self.edges:
            if e["type"] in ("PARTY_TO", "SIGNED"):
                comp_key = e["source"]
                comp_node = self.nodes.get(comp_key)
                if comp_node:
                    c_name = comp_node.get("name", "").lower()
                    norm_name = comp_node.get("normalized_name", "").lower()
                    if clean_name in c_name or clean_name in norm_name:
                        c_node_key = e["target"]
                        c_node = self.nodes.get(c_node_key)
                        if c_node and c_node not in matching_contracts:
                            matching_contracts.append(c_node)

        return matching_contracts

    def query_clauses_by_contract(self, contract_id: str) -> List[Dict[str, Any]]:
        """2. Find clauses inside a contract."""
        c_node_key = f"Contract:{contract_id}"
        clauses = []
        for e in self.edges:
            if e["source"] == c_node_key and e["type"] == "CONTAINS":
                cl_key = e["target"]
                cl_node = self.nodes.get(cl_key)
                if cl_node:
                    clauses.append(cl_node)
        return clauses

    def query_obligations_by_contract(self, contract_id: str) -> List[Dict[str, Any]]:
        """3. Find obligations belonging to a contract."""
        c_node_key = f"Contract:{contract_id}"
        obligations = []
        for e in self.edges:
            if e["source"] == c_node_key and e["type"] == "HAS_OBLIGATION":
                ob_key = e["target"]
                ob_node = self.nodes.get(ob_key)
                if ob_node:
                    obligations.append(ob_node)
        return obligations

    def query_contracts_by_jurisdiction(self, jurisdiction_name: str) -> List[Dict[str, Any]]:
        """4. Find contracts governed by a jurisdiction."""
        clean_j = jurisdiction_name.lower().strip()
        matching_contracts = []

        for e in self.edges:
            if e["type"] == "GOVERNED_BY":
                j_key = e["target"]
                j_node = self.nodes.get(j_key)
                if j_node and clean_j in j_node.get("name", "").lower():
                    c_node_key = e["source"]
                    c_node = self.nodes.get(c_node_key)
                    if c_node and c_node not in matching_contracts:
                        matching_contracts.append(c_node)

        return matching_contracts

    def get_contract_subgraph(self, contract_id: str) -> Dict[str, Any]:
        """Return nodes and edges subgraph for a contract."""
        c_node_key = f"Contract:{contract_id}"
        rel_nodes = []
        rel_edges = []

        c_node = self.nodes.get(c_node_key)
        if c_node:
            rel_nodes.append(c_node)

        for e in self.edges:
            if e["source"] == c_node_key or e["target"] == c_node_key:
                rel_edges.append(e)

                s_node = self.nodes.get(e["source"])
                if s_node and s_node not in rel_nodes:
                    rel_nodes.append(s_node)

                t_node = self.nodes.get(e["target"])
                if t_node and t_node not in rel_nodes:
                    rel_nodes.append(t_node)

        return {
            "contract_id": contract_id,
            "node_count": len(rel_nodes),
            "edge_count": len(rel_edges),
            "nodes": rel_nodes,
            "edges": rel_edges
        }

    def delete_contract_nodes(self, contract_id: str) -> None:
        """Purge contract node, its child nodes, and connected edges."""
        c_node_key = f"Contract:{contract_id}"
        if c_node_key in self.nodes:
            del self.nodes[c_node_key]

        # Purge connected edges
        self.edges = [e for e in self.edges if e["source"] != c_node_key and e["target"] != c_node_key]


class GraphService:
    """Service orchestrating relational data sync into Knowledge Graph nodes and edges."""

    def __init__(self, provider: Optional[BaseGraphProvider] = None):
        self.provider = provider or InMemoryGraphProvider()

    def sync_contract_to_graph(self, db: Session, contract_id: str) -> Dict[str, Any]:
        """
        Extract contract, entities, clauses, obligations, and risk records from PostgreSQL/SQLite,
        normalize entities, and populate Knowledge Graph nodes and edges.
        """
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValueError(f"Contract with id '{contract_id}' not found.")

        # Query entities
        entities = db.query(Entity).filter(Entity.contract_id == contract_id).all()
        if not entities:
            from backend.app.services.extractor import get_entity_extractor
            try:
                entities = get_entity_extractor().extract_and_store_entities(db=db, contract_id=contract_id)
            except Exception:
                entities = []
        companies = [{"name": e.name, "normalized_name": e.normalized_name} for e in entities if e.entity_type == "COMPANY"]
        persons = [{"name": e.name} for e in entities if e.entity_type == "PERSON"]
        jurisdictions = [{"name": e.normalized_name or e.name} for e in entities if e.entity_type == "JURISDICTION"]

        # Query clauses
        clauses = db.query(Clause).filter(Clause.contract_id == contract_id).all()
        if not clauses:
            from backend.app.services.clause_classifier import get_clause_classifier
            try:
                clauses = get_clause_classifier().extract_and_store_clauses(db=db, contract_id=contract_id)
            except Exception:
                clauses = []
        clause_list = [{"id": c.id, "clause_type": c.clause_type, "text": c.text} for c in clauses]

        # Query obligations
        obligations = db.query(Obligation).filter(Obligation.contract_id == contract_id).all()
        if not obligations:
            from backend.app.services.obligation_extractor import get_obligation_extractor
            try:
                obligations = get_obligation_extractor().extract_and_store_obligations(db=db, contract_id=contract_id)
            except Exception:
                obligations = []
        obligation_list = [{"id": o.id, "description": o.description, "deadline": o.deadline or "N/A"} for o in obligations]

        # Query risk flags
        risks = db.query(RiskFlag).filter(RiskFlag.contract_id == contract_id).all()
        if not risks:
            from backend.app.services.risk_analyzer import get_risk_analyzer
            try:
                risks = get_risk_analyzer().analyze_and_store_contract_risks(db=db, contract_id=contract_id)
            except Exception:
                risks = []
        risk_list = [{"id": r.id, "risk_type": r.risk_type, "severity": r.severity} for r in risks]

        c_dict = {
            "id": contract.id,
            "name": contract.name,
            "contract_type": contract.contract_type or "General Contract",
            "created_at": str(contract.created_at)
        }

        return self.provider.sync_contract_nodes(
            contract=c_dict,
            companies=companies,
            persons=persons,
            clauses=clause_list,
            obligations=obligation_list,
            jurisdictions=jurisdictions,
            risks=risk_list
        )

    def query_contracts_by_company(self, company_name: str) -> List[Dict[str, Any]]:
        return self.provider.query_contracts_by_company(company_name)

    def query_clauses_by_contract(self, contract_id: str) -> List[Dict[str, Any]]:
        return self.provider.query_clauses_by_contract(contract_id)

    def query_obligations_by_contract(self, contract_id: str) -> List[Dict[str, Any]]:
        return self.provider.query_obligations_by_contract(contract_id)

    def query_contracts_by_jurisdiction(self, jurisdiction_name: str) -> List[Dict[str, Any]]:
        return self.provider.query_contracts_by_jurisdiction(jurisdiction_name)

    def get_contract_graph(self, contract_id: str) -> Dict[str, Any]:
        return self.provider.get_contract_subgraph(contract_id)

    def delete_contract_from_graph(self, contract_id: str) -> None:
        """Remove contract and related relationships from the knowledge graph."""
        self.provider.delete_contract_nodes(contract_id)


# Default singleton instance
_graph_service = GraphService()


def get_graph_service() -> GraphService:
    """Return default GraphService instance."""
    return _graph_service
