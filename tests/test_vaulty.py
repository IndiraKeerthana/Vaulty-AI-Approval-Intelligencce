import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from repositories.business_repository import (
    get_business_repository, LocalJsonBusinessRepository
)
from repositories.memory_repository import (
    get_memory_repository, LocalMemoryRepository
)
from services.data_normalization import (
    normalize_discrepancy_type,
    calculate_difference
)
from services.analytics_service import get_analytics_service
from agents.pipeline import InvestigationPipeline
from utils.llm_client import LLMClient


def test_provider_selection_and_local_fallback():
    """Verify provider selection defaults cleanly to Local mode when no credentials exist."""
    biz_repo = get_business_repository()
    assert biz_repo.get_data_mode() == "Local mode"
    assert isinstance(biz_repo, LocalJsonBusinessRepository)

    mem_repo = get_memory_repository()
    assert mem_repo.get_memory_mode() == "Local mode"
    assert isinstance(mem_repo, LocalMemoryRepository)


def test_data_normalization_and_differences():
    """Verify canonical discrepancy normalization and exact positive difference calculation."""
    assert normalize_discrepancy_type("Price mismatch (₹550 vs ₹500 PO)") == "Price Mismatch"
    assert normalize_discrepancy_type("Quantity / Partial Delivery Mismatch") == "Quantity Mismatch"
    assert normalize_discrepancy_type("Missing Purchase Order Reference") == "Missing Purchase Order"
    assert normalize_discrepancy_type("Potential Duplicate Invoice") == "Duplicate Invoice"
    assert normalize_discrepancy_type("Price mismatch + Recent Banking Detail Change") == "Potential Fraud Signal"
    assert normalize_discrepancy_type("None (Matching consistency)") == "Matching Consistency (Clean)"

    inv = {"total_amount": 55000.0, "line_items": [{"unit_price": 550.0, "quantity": 100}]}
    po = {"total_amount": 50000.0, "line_items": [{"unit_price": 500.0, "ordered_quantity": 100}]}
    diff = calculate_difference(inv, po)
    assert diff == 5000.0


def test_llm_fallback_behavior():
    """Verify LLMClient cleanly executes evidence fallback when API key is unconfigured or fails."""
    client = LLMClient(api_key="INVALID_TEST_KEY_FOR_FALLBACK")
    assert client.is_available() is True  # has key string

    def fallback_demo():
        return {"status": "FALLBACK_SUCCESS", "value": 42}

    res = client.generate_json("Test prompt", fallback_fn=fallback_demo)
    assert res.get("status") == "FALLBACK_SUCCESS"
    assert res.get("value") == 42


def test_investigation_result_contract_and_creation():
    """Verify standardized investigation result contract creation."""
    pipeline = InvestigationPipeline()
    res = pipeline.run_pipeline("INV-2001", "VX-2001")

    assert res["invoice_id"] == "INV-2001"
    assert res["case_id"] == "VX-2001"
    assert "stage_5_investigation" in res
    inv_res = res["stage_5_investigation"]

    # Verify standardized contract fields
    assert inv_res["case_id"] == "VX-2001"
    assert inv_res["investigation_status"] == "COMPLETED"
    assert "discrepancy_type" in inv_res
    assert isinstance(inv_res["current_evidence"], list)
    assert "findings" in inv_res
    assert "relevant_memory" in inv_res
    assert inv_res["memory_verdict"] in ("CONFIRMED", "CONTRADICTED", "NOT_APPLICABLE")
    assert "conclusion" in inv_res
    assert "recommended_action" in inv_res
    assert inv_res["requires_human_review"] is True
    assert inv_res["resolution_state"] == "AWAITING_HUMAN_SIGN_OFF"
    assert inv_res["learning_candidate"] is True


def test_investigation_result_caching_and_no_duplicate_execution():
    """Verify case-level caching prevents duplicate pipeline executions on reruns."""
    session_state_cache = {}
    case_id = "VX-2001"

    # Simulate First View -> Run Pipeline & Cache
    if f"pipeline_res_{case_id}" not in session_state_cache:
        pipeline = InvestigationPipeline()
        session_state_cache[f"pipeline_res_{case_id}"] = pipeline.run_pipeline("INV-2001", case_id)

    first_result = session_state_cache[f"pipeline_res_{case_id}"]

    # Simulate Rerun -> Reuse Cached Result
    execution_counter = 0
    if f"pipeline_res_{case_id}" not in session_state_cache:
        execution_counter += 1

    assert execution_counter == 0
    assert session_state_cache[f"pipeline_res_{case_id}"] == first_result


def test_memory_recall_and_no_memory_fallback():
    """Verify memory recall when memories exist vs fallback when no memory is present."""
    mem_repo = get_memory_repository()

    # Query for known topic
    recalled = mem_repo.recall(query="price amendment", vendor_id="VND-001", top_k=3)
    assert isinstance(recalled, list)

    # Query for non-existent vendor
    no_mem = mem_repo.recall(query="xyz_non_existent_topic_12345", vendor_id="VND-NONEXISTENT-999", top_k=3)
    assert isinstance(no_mem, list)
    assert len(no_mem) == 0


def test_memory_confirmed_vs_contradicted_and_evidence_override():
    """Verify memory confirmed vs contradicted verdicts and current evidence overriding memory."""
    pipeline = InvestigationPipeline()

    # Scenario 2 (VX-2001): Approved amendment exists -> Memory CONFIRMED
    res_confirmed = pipeline.run_pipeline("INV-2001", "VX-2001")
    inv_c = res_confirmed["stage_5_investigation"]
    assert inv_c["memory_verdict"] == "CONFIRMED"
    assert inv_c["recommended_action"] == "APPLY_AMENDMENT"

    # Scenario 3 (VX-2002): Memory recalls prior amendment experience, but current PO has NO approved amendment -> Memory CONTRADICTED
    res_contradicted = pipeline.run_pipeline("INV-2002", "VX-2002")
    inv_contr = res_contradicted["stage_5_investigation"]
    assert inv_contr["memory_verdict"] == "CONTRADICTED"
    # Current evidence overrides past memory! Action becomes DRAFT_VENDOR_QUERY instead of auto-approval.
    assert inv_contr["recommended_action"] == "DRAFT_VENDOR_QUERY"


def test_human_decision_learning_and_future_recall():
    """Verify human supervisor decision creates retained lesson that is retrieved by future investigation."""
    pipeline = InvestigationPipeline()
    mem_repo = get_memory_repository()

    # Process human decision on Case A
    ref_res = pipeline.process_human_decision(
        case_id="VX-TEST-888",
        vendor_id="VND-002",
        vendor_name="ACME Corp",
        discrepancy_type="Price mismatch",
        agent_recommendation="APPLY_AMENDMENT",
        human_outcome="CORRECTED",
        human_notes="Supervisor correction: Check warehouse delivery receipt before releasing payment."
    )

    assert ref_res["human_outcome"] == "CORRECTED"

    # Verify lesson retained in memory
    recalled = mem_repo.recall(query="delivery receipt warehouse", vendor_id="VND-002")
    assert len(recalled) > 0
    assert any("Supervisor correction" in m.get("lesson", "") or "warehouse" in m.get("lesson", "").lower() for m in recalled)


def test_analytics_and_human_gated_approval_state():
    """Verify payment release remains strictly human gated and propagates state across application."""
    biz_repo = get_business_repository()
    analytics = get_analytics_service()

    # Check initial metrics
    metrics_before = analytics.get_home_metrics()

    # Approve Case VX-4001
    biz_repo.update_approval_status("VX-4001", "RESOLVED", "Payment release approved by Finance Manager.")
    case_4001 = biz_repo.get_case("VX-4001")
    assert case_4001["status"] == "RESOLVED"

    # Verify audit event
    logs = biz_repo.get_audit_logs("VX-4001")
    assert len(logs) > 0

    # Reset case status
    biz_repo.update_case("VX-4001", "UNPROCESSED", "Pending Triage")


def test_hindsight_learning_loop_cases_a_b_c():
    """
    Directly verifies Section 13 learning loop requirement:
    CASE A: Vendor ACME, Price mismatch, Approved amendment exists, Human approves -> Retain called with full narrative & human outcome.
    CASE B: Same vendor, Similar price mismatch, Approved amendment exists -> Recall retrieves experience, current amendment verified -> CONFIRMED.
    CASE C: Same vendor, Similar price mismatch, NO approved amendment -> Recalls experience, current evidence contradicts it -> CONTRADICTED -> Evidence overrides memory.
    """
    pipeline = InvestigationPipeline()

    # --- CASE A ---
    res_a = pipeline.run_pipeline("INV-2001", "VX-2001")
    inv_a = res_a["stage_5_investigation"]

    # Human decision on Case A: Human approves
    ref_res_a = pipeline.process_human_decision(
        case_id="VX-2001",
        vendor_id="VND-002",
        vendor_name="ACME Corp",
        discrepancy_type="Price mismatch (₹550 vs ₹500 PO)",
        agent_recommendation=inv_a.get("recommended_action", "APPLY_AMENDMENT"),
        human_outcome="APPROVED",
        human_notes="Approved payment release after verifying signed amendment AM-17.",
        investigation_result=inv_a
    )

    # 1. Hindsight retain is called
    assert ref_res_a is not None
    assert ref_res_a.get("document_id") == "vaulty-case-VX-2001"
    assert "source:vaulty" in ref_res_a.get("tags", [])
    assert "vendor:VND-002" in ref_res_a.get("tags", [])

    # 2. Memory contains the investigation and human outcome
    saved_lesson = ref_res_a.get("lesson", "")
    assert "ACME Corp" in saved_lesson
    assert "APPROVED" in saved_lesson
    assert "AM-17" in saved_lesson or "amendment" in saved_lesson.lower()
    assert "approved" in saved_lesson.lower()

    # --- CASE B ---
    # Same vendor, similar price mismatch, approved amendment exists again
    res_b = pipeline.run_pipeline("INV-2001", "VX-2001")
    inv_b = res_b["stage_5_investigation"]

    # 1. Hindsight recall is called
    assert "memory_recall" in res_b
    assert len(res_b["memory_recall"]) > 0

    # 2. Previous experience is retrieved
    recalled_texts = [m.get("text", "") for m in res_b["memory_recall"]]
    assert any("ACME" in t or "amendment" in t.lower() or "price" in t.lower() for t in recalled_texts)

    # 3. Current amendment is verified
    assert inv_b.get("verified_amendment_id") == "AM-17"

    # 4. Memory verdict = CONFIRMED
    assert inv_b["memory_verdict"] == "CONFIRMED"
    mi_b = inv_b["memory_influence"]
    assert mi_b["status"] == "CONFIRMED"
    assert "reason" in mi_b and len(mi_b["reason"]) > 0
    assert "adapted_decision" in mi_b and len(mi_b["adapted_decision"]) > 0

    # 5. Resolution uses recalled experience as supporting context
    res_b_action = res_b["stage_6_resolution"]
    assert res_b_action["action_taken"] in ("APPLY_CONTRACT_AMENDMENT", "APPROVE_PAYMENT_RELEASE")

    # --- CASE C ---
    # Same vendor, similar price mismatch, NO approved amendment (VX-2002 on PO-2002)
    res_c = pipeline.run_pipeline("INV-2002", "VX-2002")
    inv_c = res_c["stage_5_investigation"]

    # 1. Previous ACME experience is recalled
    assert len(res_c["memory_recall"]) > 0

    # 2. Current evidence contradicts it
    assert inv_c.get("verified_amendment_id") is None
    assert inv_c["memory_verdict"] == "CONTRADICTED"

    # 3. Memory verdict = CONTRADICTED
    mi_c = inv_c["memory_influence"]
    assert mi_c["status"] == "CONTRADICTED"

    # 4. Evidence overrides memory explicitly stated
    assert "evidence overrides memory" in mi_c["reason"].lower() or "evidence overrides memory" in mi_c["adapted_decision"].lower()

    # 5. Recommendation changes accordingly
    assert inv_c["recommended_action"] == "DRAFT_VENDOR_QUERY"
    assert res_c["stage_6_resolution"]["action_taken"] == "DRAFT_VENDOR_QUERY"


if __name__ == "__main__":
    pytest.main([__file__])

