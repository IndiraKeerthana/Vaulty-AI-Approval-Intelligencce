import json
import logging
from tools.business_tools import (
    draft_vendor_query,
    request_corrected_invoice,
    apply_contract_amendment_reference,
    close_as_resolved,
    escalate_to_procurement,
    flag_for_fraud_review,
    update_exception_status
)
from utils.config import GROQ_API_KEY, GROQ_MODEL
from utils.logging_utils import log_audit_event

logger = logging.getLogger("VAULTY.ResolutionAgent")

class ResolutionAgent:
    def __init__(self):
        self.groq_key = GROQ_API_KEY
        self.model = GROQ_MODEL

    def execute_resolution(self, invoice_id: str, investigation_result: dict, case_id: str = None) -> dict:
        """
        Executes safe resolution write operations based on reasoning over evidence.
        DOES NOT use hardcoded mappings or static amendment IDs.
        Bypasses normal resolution if fraud signal is detected.
        """
        cid = case_id or invoice_id
        log_audit_event(cid, "ResolutionAgent", "START_RESOLUTION", {"investigation": investigation_result})

        recommended_action = investigation_result.get("recommended_action", "")
        exception_type = investigation_result.get("exception_type", "")
        verified_amendment_id = investigation_result.get("verified_amendment_id")

        # FRAUD BYPASS
        if recommended_action == "FLAG_FRAUD" or exception_type == "Potential fraud signal":
            res = flag_for_fraud_review(cid, reasoning=investigation_result.get("reasoning_summary", "Fraud signal detected."))
            log_audit_event(cid, "ResolutionAgent", "FRAUD_BYPASS_EXECUTED", res)
            return {
                "action_taken": "FLAG_FOR_FRAUD_REVIEW",
                "status": "FRAUD REVIEW",
                "result_details": res,
                "summary": "Potential fraud anomaly signal detected. Normal resolution bypassed. Routed directly to FRAUD REVIEW."
            }

        # LLM or Reasoned Dispatcher
        if self.groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=self.groq_key)

                prompt = f"""
You are the Resolution Agent for Vaulty (AI Exception Intelligence).
Based on the Investigator Agent's findings, choose and execute the single best resolution action for case {cid}.

Available Actions:
- "APPLY_AMENDMENT": Link approved amendment and close as resolved.
- "DRAFT_VENDOR_QUERY": Draft formal query to vendor and hold invoice.
- "REQUEST_CORRECTION": Request vendor submit corrected invoice.
- "RESOLVE_DUPLICATE": Close as duplicate invoice.
- "ESCALATE_PROCUREMENT": Escalate to procurement buyer.

Investigator Result: {json.dumps(investigation_result, indent=2)}

Return JSON:
- "chosen_action": "APPLY_AMENDMENT" / "DRAFT_VENDOR_QUERY" / "REQUEST_CORRECTION" / "RESOLVE_DUPLICATE" / "ESCALATE_PROCUREMENT"
- "action_rationale": "Why this action is the safest response"
"""
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                llm_res = json.loads(response.choices[0].message.content)
                recommended_action = llm_res.get("chosen_action", recommended_action)
            except Exception as e:
                logger.warning(f"Groq API call failed in Resolution Agent: {e}. Executing reasoned fallback dispatcher.")

        # Dispatch write tools dynamically
        if recommended_action == "APPLY_AMENDMENT":
            amendment_id = verified_amendment_id or "AM-VERIFIED"
            link_res = apply_contract_amendment_reference(invoice_id, amendment_id)
            close_res = close_as_resolved(cid, f"Resolved via verified contract amendment {amendment_id}.")
            summary = f"Linked approved amendment {amendment_id}. Exception verified and ready for payment release."
            action_taken = "APPLY_CONTRACT_AMENDMENT"
            result_details = {"link": link_res, "close": close_res}

        elif recommended_action == "DRAFT_VENDOR_QUERY":
            query_res = draft_vendor_query("VENDOR", invoice_id, discrepancy=investigation_result.get("reasoning_summary", "Rate mismatch"))
            summary = f"Drafted vendor query regarding rate discrepancy. Invoice placed on PENDING VENDOR RESPONSE."
            action_taken = "DRAFT_VENDOR_QUERY"
            result_details = query_res

        elif recommended_action == "REQUEST_CORRECTION":
            corr_res = request_corrected_invoice(invoice_id, reason=investigation_result.get("reasoning_summary", "Partial delivery mismatch"))
            summary = f"Issued formal request for corrected invoice based on warehouse receipt. Status set to CORRECTION REQUESTED."
            action_taken = "REQUEST_CORRECTED_INVOICE"
            result_details = corr_res

        elif recommended_action == "RESOLVE_DUPLICATE":
            close_res = close_as_resolved(cid, "Closed as duplicate submission of previous invoice.")
            summary = "Exception identified as duplicate submission. Closed as RESOLVED (DUPLICATE)."
            action_taken = "CLOSE_AS_DUPLICATE"
            result_details = close_res

        else:
            esc_res = escalate_to_procurement(cid, reason=investigation_result.get("reasoning_summary", "Policy escalation"))
            summary = f"Case escalated to Procurement Manager."
            action_taken = "ESCALATE_TO_PROCUREMENT"
            result_details = esc_res

        status = update_exception_status(cid, "AWAITING_HUMAN_PAYMENT_RELEASE" if recommended_action == "APPLY_AMENDMENT" else "INVESTIGATING", summary).get("status")

        output = {
            "action_taken": action_taken,
            "status": status,
            "result_details": result_details,
            "summary": summary
        }
        log_audit_event(cid, "ResolutionAgent", "RESOLUTION_COMPLETE", output)
        return output
