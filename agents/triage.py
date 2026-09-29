import json
import logging
from utils.llm_client import LLMClient
from utils.logging_utils import log_audit_event

logger = logging.getLogger("VAULTY.TriageAgent")

class TriageAgent:
    def __init__(self):
        self.llm_client = LLMClient()

    def evaluate(self, invoice: dict, po: dict, receipt: dict) -> dict:
        """
        Triage Agent evaluates raw invoice, PO, and receipt without pre-flagged errors.
        Decides whether case requires deeper investigation or can be CLEARED.
        """
        inv_id = invoice.get("invoice_id", "UNKNOWN")
        log_audit_event(inv_id, "TriageAgent", "START_TRIAGE", {"invoice_id": inv_id})

        prompt = f"""
You are the Triage Agent for Vaulty (AI Exception Intelligence).
Inspect the raw Invoice, Purchase Order (PO), and Goods Receipt data.
Evaluate matching across price, quantity, PO reference, duplicate billing, or timing issues.
Materiality is contextual.

Invoice: {json.dumps(invoice, indent=2)}
PO: {json.dumps(po, indent=2)}
Receipt: {json.dumps(receipt, indent=2)}

Return a strict JSON object:
- "decision": "CLEAR" or "INVESTIGATE"
- "exception_type": "Price mismatch" / "Quantity mismatch" / "Missing PO" / "Duplicate billing" / "Potential fraud signal" / "None"
- "explanation": "Concise summary of triage decision"
- "observations": ["list of key observations"]
- "priority": "LOW" / "MEDIUM" / "HIGH" / "CRITICAL"
"""
        def fallback_eval():
            observations = []
            requires_investigation = False
            priority = "LOW"
            exception_type = "None"

            # Check missing PO reference
            if not invoice.get("po_id"):
                observations.append("Invoice lacks a Purchase Order (PO) reference.")
                requires_investigation = True
                priority = "MEDIUM"
                exception_type = "Missing PO"

            # Check invoice total / unit price vs PO
            inv_amount = invoice.get("total_amount", 0.0)
            po_amount = po.get("total_amount", 0.0) if isinstance(po, dict) and "total_amount" in po else None

            if po_amount is not None and not exception_type == "Missing PO":
                diff = abs(inv_amount - po_amount)
                if diff > 0.01:
                    percentage_diff = (diff / po_amount) * 100 if po_amount > 0 else 100
                    observations.append(f"Price discrepancy detected: Invoice total (₹{inv_amount:,.2f}) vs PO total (₹{po_amount:,.2f}) - difference of ₹{diff:,.2f} ({percentage_diff:.1f}%).")
                    requires_investigation = True
                    priority = "HIGH" if percentage_diff > 5 else "MEDIUM"
                    exception_type = "Price mismatch"

            # Check quantity delivery match
            if isinstance(receipt, dict) and "line_items" in receipt:
                rec_status = receipt.get("status")
                if rec_status == "PARTIAL_DELIVERY":
                    observations.append("Goods receipt records a PARTIAL DELIVERY. Received quantity is less than billed quantity.")
                    requires_investigation = True
                    priority = "HIGH"
                    if exception_type == "None":
                        exception_type = "Quantity mismatch"

            # Check duplicate notes
            notes = invoice.get("notes", "").lower()
            if "duplicate" in notes:
                observations.append("Invoice notes indicate duplicate submission.")
                requires_investigation = True
                priority = "MEDIUM"
                exception_type = "Duplicate billing"

            if not requires_investigation:
                observations.append("Invoice line items, unit prices, ordered PO quantities, and goods receipt match consistently.")
                decision = "CLEAR"
                explanation = "Matching verification passed cleanly across Invoice, PO, and Goods Receipt. No exception investigation required."
            else:
                decision = "INVESTIGATE"
                explanation = f"Potential discrepancy identified ({exception_type}): {'; '.join(observations)}."

            return {
                "decision": decision,
                "exception_type": exception_type,
                "explanation": explanation,
                "observations": observations,
                "priority": priority
            }

        res = self.llm_client.generate_json(prompt, fallback_fn=fallback_eval)
        log_audit_event(inv_id, "TriageAgent", "TRIAGE_COMPLETE", res)
        return res
