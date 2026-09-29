import json
import logging
import datetime
from repositories.business_repository import get_business_repository
from repositories.memory_repository import get_memory_repository
from services.data_normalization import normalize_discrepancy_type
from utils.llm_client import LLMClient
from utils.logging_utils import log_audit_event

logger = logging.getLogger("VAULTY.ReflectionAgent")

class ReflectionAgent:
    def __init__(self):
        self.llm_client = LLMClient()

    def reflect_and_learn(
        self,
        case_id: str,
        vendor_id: str,
        vendor_name: str,
        discrepancy_type: str,
        agent_recommendation: str,
        human_outcome: str,  # "APPROVED", "ON_HOLD", "CORRECTED", "ESCALATED"
        human_notes: str = "",
        investigation_result: dict = None
    ) -> dict:
        """
        Runs after human decision.
        Synthesizes a complete business experience narrative and retains it into Hindsight memory
        with stable document_id (vaulty-case-{case_id}) and canonical tags.
        """
        log_audit_event(case_id, "ReflectionAgent", "START_REFLECTION", {
            "human_outcome": human_outcome,
            "human_notes": human_notes
        })
        biz_repo = get_business_repository()
        mem_repo = get_memory_repository()

        # Gather operational records for complete narrative synthesis
        case = biz_repo.get_case(case_id) or {}
        inv_id = case.get("invoice_id") or ""
        inv = biz_repo.get_invoice(inv_id) if inv_id else {}
        po_id = inv.get("po_id") or case.get("po_id") or ""
        po = biz_repo.get_purchase_order(po_id) if po_id else {}
        receipt = biz_repo.get_receipt(po_id) if po_id else {}
        contract = biz_repo.get_contract(vendor_id) if vendor_id else {}
        amendments = biz_repo.get_amendments(vendor_id) if vendor_id else []

        inv_amt = inv.get("total_amount") or case.get("amount") or 0.0
        po_amt = po.get("total_amount", 0.0)
        po_item = po.get("line_items", [{}])[0] if po.get("line_items") else {}
        po_unit_price = po_item.get("unit_price")

        # Summarize amendments
        matching_amd = None
        for a in amendments:
            if a.get("po_id") == po_id and a.get("status") == "APPROVED":
                matching_amd = a
                break

        if matching_amd:
            amd_summary = f"Approved amendment {matching_amd.get('amendment_id')} existed revising unit rate to ₹{matching_amd.get('amended_unit_price', 0):,.2f}."
        else:
            amd_summary = f"No approved amendment existed for PO {po_id}."

        # Receipt summary
        if receipt.get("status") == "PARTIAL_DELIVERY":
            rec_summary = f"Goods receipt {receipt.get('receipt_id')} recorded partial delivery."
        elif receipt.get("receipt_id"):
            rec_summary = f"Goods receipt {receipt.get('receipt_id')} confirmed full physical delivery."
        else:
            rec_summary = "No warehouse goods receipt recorded."

        # Investigation verdict
        inv_res = investigation_result or {}
        mem_verdict = inv_res.get("memory_verdict") or ("CONFIRMED" if matching_amd else "CONTRADICTED")
        findings = inv_res.get("findings") or inv_res.get("reasoning_summary") or f"Discrepancy analyzed against {po_id} and amendments."

        # Final outcome description
        if human_outcome == "APPROVED":
            final_outcome = "Payment release approved by authorized human reviewer."
            derived_learning = f"When {vendor_name} price or terms are backed by verified approved amendments, payment release is appropriate."
            feedback_type = "HUMAN_APPROVAL"
        elif human_outcome in ("CORRECTED", "ON_HOLD", "HELD"):
            final_outcome = f"Invoice placed on hold / correction requested: '{human_notes}'."
            derived_learning = f"When variance lacks an approved amendment or verified goods receipt for {vendor_name}, hold payment and verify before approval."
            feedback_type = "HUMAN_CORRECTION"
        else:
            final_outcome = f"Case escalated for managerial review: '{human_notes}'."
            derived_learning = f"Complex exception pattern for {vendor_name} requires cross-departmental verification."
            feedback_type = "POLICY_UPDATE"

        # Generate structured business narrative
        narrative = (
            f"Vaulty investigated case {case_id} for vendor {vendor_name} ({vendor_id}). "
            f"Invoice {inv_id} billed ₹{inv_amt:,.2f} with discrepancy: {discrepancy_type}. "
            f"Purchase order {po_id} authorized ₹{po_amt:,.2f} (unit price ₹{po_unit_price}). "
            f"{rec_summary} "
            f"{amd_summary} "
            f"Findings: {findings}. "
            f"Memory verdict was {mem_verdict}. "
            f"Vaulty recommended {agent_recommendation}. "
            f"Human reviewer decided: {human_outcome} (Reason: '{human_notes or final_outcome}'). "
            f"Final outcome: {final_outcome} "
            f"Learning: {derived_learning}"
        )

        doc_id = f"vaulty-case-{case_id}"
        norm_disc = normalize_discrepancy_type(discrepancy_type).lower().replace(" ", "_")
        tags = [
            "source:vaulty",
            "type:ap_exception",
            f"vendor:{vendor_id}",
            f"discrepancy:{norm_disc}"
        ]

        metadata = {
            "case_id": case_id,
            "vendor_id": vendor_id,
            "vendor_name": vendor_name,
            "invoice_id": inv_id,
            "discrepancy_type": discrepancy_type,
            "invoice_amount": inv_amt,
            "po_id": po_id,
            "po_amount": po_amt,
            "receipt_summary": rec_summary,
            "amendment_summary": amd_summary,
            "investigation_findings": findings,
            "memory_verdict": mem_verdict,
            "recommended_resolution": agent_recommendation,
            "human_decision": human_outcome,
            "human_reason": human_notes,
            "final_outcome": final_outcome,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Retain into Memory Repository
        saved = mem_repo.remember(
            lesson_content=narrative,
            vendor_id=vendor_id,
            vendor_name=vendor_name,
            topic=f"AP Experience on {vendor_name} ({discrepancy_type})",
            source_case_id=case_id,
            human_feedback_type=feedback_type,
            metadata=metadata,
            document_id=doc_id,
            tags=tags
        )

        log_audit_event(case_id, "ReflectionAgent", "REFLECTION_STORED", saved)
        return {
            "case_id": case_id,
            "human_outcome": human_outcome,
            "topic": f"AP Experience on {vendor_name} ({discrepancy_type})",
            "lesson": narrative,
            "reflection_text": narrative,
            "document_id": doc_id,
            "tags": tags,
            "saved_memory": saved,
            "memory_mode": mem_repo.get_memory_mode()
        }
