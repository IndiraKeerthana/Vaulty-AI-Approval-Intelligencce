import json
import logging
from repositories.memory_repository import get_memory_repository
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
        human_outcome: str,  # "APPROVED", "REJECTED", "CORRECTED"
        human_notes: str = ""
    ) -> dict:
        """
        Runs after human decision or case outcome.
        Synthesizes an institutional lesson stored in memory so future behavior is altered.
        """
        log_audit_event(case_id, "ReflectionAgent", "START_REFLECTION", {
            "human_outcome": human_outcome,
            "human_notes": human_notes
        })
        mem_repo = get_memory_repository()

        prompt = f"""
You are the Reflection Agent for Vaulty (AI Exception Intelligence).
Synthesize an institutional lesson from this case outcome so memory alters future behavior.

Case ID: {case_id}
Vendor: {vendor_name} ({vendor_id})
Discrepancy: {discrepancy_type}
Agent Recommendation: {agent_recommendation}
Human Action Outcome: {human_outcome}
Human Supervisor Notes: {human_notes}

Return JSON:
- "topic": "Short topic header"
- "lesson": "2-3 sentence plain-English lesson stating what was learned and how future investigations should adapt."
- "feedback_type": "HUMAN_CORRECTION" / "HUMAN_APPROVAL" / "POLICY_UPDATE"
"""

        def fallback_reflection():
            res = mem_repo.reflect(
                case_id=case_id,
                human_outcome=human_outcome,
                vendor_id=vendor_id,
                vendor_name=vendor_name,
                discrepancy_type=discrepancy_type,
                agent_recommendation=agent_recommendation,
                human_notes=human_notes
            )
            return {
                "topic": res.get("topic", f"Lesson on {discrepancy_type}"),
                "lesson": res.get("lesson", ""),
                "feedback_type": "HUMAN_CORRECTION" if human_outcome == "CORRECTED" else "HUMAN_APPROVAL"
            }

        llm_res = self.llm_client.generate_json(prompt, fallback_fn=fallback_reflection)
        topic = llm_res.get("topic", f"Lesson on {discrepancy_type}")
        lesson_text = llm_res.get("lesson", "")
        feedback_type = llm_res.get("feedback_type", "HUMAN_CORRECTION" if human_outcome == "CORRECTED" else "HUMAN_APPROVAL")

        saved = mem_repo.remember(
            lesson_content=lesson_text,
            vendor_id=vendor_id,
            vendor_name=vendor_name,
            topic=topic,
            source_case_id=case_id,
            human_feedback_type=feedback_type
        )
        log_audit_event(case_id, "ReflectionAgent", "REFLECTION_STORED", saved)
        return {
            "case_id": case_id,
            "human_outcome": human_outcome,
            "topic": topic,
            "lesson": lesson_text,
            "saved_memory": saved,
            "memory_mode": mem_repo.get_memory_mode()
        }
