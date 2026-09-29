import logging
from repositories.business_repository import get_business_repository
from repositories.memory_repository import get_memory_repository
from agents.triage import TriageAgent
from agents.investigator import InvestigatorAgent
from agents.resolution import ResolutionAgent
from agents.orchestrator import OrchestratorAgent
from agents.reflection import ReflectionAgent
from utils.logging_utils import log_audit_event

logger = logging.getLogger("VAULTY.InvestigationPipeline")

class InvestigationPipeline:
    """
    Unified end-to-end exception processing pipeline.
    Stages:
    1. Invoice (Fetch document)
    2. Exception Understanding (Triage)
    3. Evidence Collection (PO, Receipt, Contract, Vendor History, Amendments)
    4. Memory Recall (Hindsight / Local)
    5. Investigation (Memory vs Current Evidence Verification)
    6. Resolution Proposal (Structured Action Proposal)
    7. Safety / Human Gate (Orchestrator Review & Gate)
    8. Execution (Execute Resolution Action)
    9. Reflection (Learn from Human Outcome)
    """

    def __init__(self):
        self.biz_repo = get_business_repository()
        self.mem_repo = get_memory_repository()
        self.triage_agent = TriageAgent()
        self.investigator_agent = InvestigatorAgent()
        self.resolution_agent = ResolutionAgent()
        self.orchestrator_agent = OrchestratorAgent()
        self.reflection_agent = ReflectionAgent()

    def run_pipeline(self, invoice_id: str, case_id: str = None) -> dict:
        cid = case_id or invoice_id
        log_audit_event(cid, "Pipeline", "START_PIPELINE", {"invoice_id": invoice_id})

        # Stage 1: Invoice
        invoice = self.biz_repo.get_invoice(invoice_id)
        if "error" in invoice:
            return {"status": "ERROR", "message": f"Invoice {invoice_id} not found."}

        vendor_id = invoice.get("vendor_id", "")
        po_id = invoice.get("po_id", "")

        # Stage 3: Evidence Collection
        po = self.biz_repo.get_purchase_order(po_id) if po_id else {}
        receipt = self.biz_repo.get_receipt(po_id) if po_id else {}
        contract = self.biz_repo.get_contract(vendor_id) if vendor_id else {}
        vendor_hist = self.biz_repo.get_vendor_history(vendor_id) if vendor_id else {}
        amendments = self.biz_repo.get_amendments(vendor_id) if vendor_id else []

        # Stage 2: Exception Understanding (Triage)
        triage_result = self.triage_agent.evaluate(invoice, po, receipt)

        # Stage 4 & 5: Memory Recall & Investigation
        investigation_result = self.investigator_agent.investigate(invoice_id, cid)

        # Stage 6 & 8: Resolution Proposal & Execution
        resolution_result = self.resolution_agent.execute_resolution(invoice_id, investigation_result, cid)

        # Stage 7: Safety / Human Gate
        orchestrator_result = self.orchestrator_agent.review_and_gate(
            triage_res=triage_result,
            inv_res=investigation_result,
            res_res=resolution_result,
            case_id=cid
        )

        return {
            "invoice_id": invoice_id,
            "case_id": cid,
            "stage_1_invoice": invoice,
            "stage_2_triage": triage_result,
            "stage_3_evidence": {
                "po": po,
                "receipt": receipt,
                "contract": contract,
                "vendor_history": vendor_hist,
                "amendments": amendments
            },
            "memory_recall": investigation_result.get("memory_recall", []),
            "memory_reflection": investigation_result.get("memory_reflection", {}),
            "memory_influence": investigation_result.get("memory_influence", {}),
            "stage_5_investigation": investigation_result,
            "stage_6_resolution": resolution_result,
            "stage_7_human_gate": orchestrator_result
        }

    def process_human_decision(
        self,
        case_id: str,
        vendor_id: str,
        vendor_name: str,
        discrepancy_type: str,
        agent_recommendation: str,
        human_outcome: str,
        human_notes: str = "",
        investigation_result: dict = None
    ) -> dict:
        """Stage 9: Reflection from human decision"""
        return self.reflection_agent.reflect_and_learn(
            case_id=case_id,
            vendor_id=vendor_id,
            vendor_name=vendor_name,
            discrepancy_type=discrepancy_type,
            agent_recommendation=agent_recommendation,
            human_outcome=human_outcome,
            human_notes=human_notes,
            investigation_result=investigation_result
        )
