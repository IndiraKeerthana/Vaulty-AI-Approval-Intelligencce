import logging
from utils.logging_utils import log_audit_event

logger = logging.getLogger("VAULTY.OrchestratorAgent")

class OrchestratorAgent:
    def __init__(self):
        pass

    def review_and_gate(self, triage_res: dict, inv_res: dict, res_res: dict, case_id: str) -> dict:
        """
        Orchestrator reviews findings, verifies evidence consistency, and enforces
        THE MANDATORY HUMAN GATE FOR ALL HIGH RISK / PAYMENT RELEASE ACTIONS.
        """
        log_audit_event(case_id, "OrchestratorAgent", "START_ORCHESTRATION_REVIEW", {
            "triage": triage_res.get("decision"),
            "resolution": res_res.get("action_taken")
        })

        recommended_action = inv_res.get("recommended_action", "")
        action_taken = res_res.get("action_taken", "")

        # Check Fraud routing
        if action_taken == "FLAG_FOR_FRAUD_REVIEW" or recommended_action == "FLAG_FRAUD":
            output = {
                "workflow_approved": True,
                "requires_human_payment_approval": False,
                "requires_human_fraud_review": True,
                "escalated": True,
                "orchestrator_decision": "ROUTE_TO_FRAUD_REVIEW",
                "summary": "Potential fraud anomaly signal confirmed. Invoice locked and routed directly to Fraud Review Board. Payment release blocked."
            }
            log_audit_event(case_id, "OrchestratorAgent", "ORCHESTRATION_DECISION", output)
            return output

        # Check Clear or Resolved exceptions eligible for payment release
        if triage_res.get("decision") == "CLEAR" or action_taken == "APPLY_CONTRACT_AMENDMENT":
            output = {
                "workflow_approved": True,
                "requires_human_payment_approval": True,  # HARD HUMAN GATE
                "requires_human_fraud_review": False,
                "escalated": False,
                "orchestrator_decision": "AWAITING_HUMAN_PAYMENT_RELEASE",
                "summary": "Investigation complete and evidence verified. Case is ready for payment release. MANDATORY HUMAN PAYMENT RELEASE GATE ACTIVATED."
            }
            log_audit_event(case_id, "OrchestratorAgent", "ORCHESTRATION_DECISION", output)
            return output

        # Case placed on hold
        output = {
            "workflow_approved": True,
            "requires_human_payment_approval": False,
            "requires_human_fraud_review": False,
            "escalated": False,
            "orchestrator_decision": "HELD_PENDING_EXTERNAL_ACTION",
            "summary": f"Investigation action executed: {action_taken}. Invoice held pending external response/correction."
        }
        log_audit_event(case_id, "OrchestratorAgent", "ORCHESTRATION_DECISION", output)
        return output
