import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from repositories.business_repository import (
    get_business_repository, LocalJsonBusinessRepository, SupabaseBusinessRepository
)
from repositories.memory_repository import (
    get_memory_repository, LocalMemoryRepository, HindsightMemoryRepository
)
from services.data_normalization import (
    normalize_discrepancy_type,
    calculate_difference,
    classify_approval_status
)
from services.analytics_service import get_analytics_service
from agents.pipeline import InvestigationPipeline


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


def test_analytics_service_home_and_extra_amount():
    """Verify Home metrics and positive overbilling extra amount calculations."""
    analytics = get_analytics_service()
    metrics = analytics.get_home_metrics()

    assert "cases_needing_approval_count" in metrics
    assert "needs_investigation_count" in metrics
    assert "resolved_discrepancies_count" in metrics
    assert "extra_amount_identified" in metrics

    extra_amt = analytics.get_extra_amount_identified()
    assert extra_amt >= 0.0


def test_analytics_approval_summary_and_history():
    """Verify Approvals page summary and persistent event history timeline."""
    analytics = get_analytics_service()
    summary = analytics.get_approval_summary()

    assert "needs_approval" in summary
    assert "approved" in summary
    assert "total_discrepancies" in summary

    history = analytics.get_approval_history()
    assert isinstance(history, list)


def test_recurring_vendor_issue_detection():
    """Verify detection of repeated vendor issues (same vendor + same normalized discrepancy type >= 2 cases)."""
    analytics = get_analytics_service()
    recurring = analytics.find_recurring_vendor_issues()

    assert isinstance(recurring, list)
    # ACME Corp has 2 price mismatch cases (VX-2001, VX-2002)
    acme_recurring = [r for r in recurring if r["vendor_name"] == "ACME Corp"]
    assert len(acme_recurring) > 0
    assert acme_recurring[0]["issue"] == "Price Mismatch"
    assert acme_recurring[0]["occurrences"] >= 2


def test_vendor_quality_metrics_and_reports():
    """Verify vendor quality metrics and report aggregations."""
    analytics = get_analytics_service()
    quality = analytics.get_vendor_quality_metrics()
    assert len(quality) > 0

    breakdown = analytics.get_discrepancy_breakdown()
    assert len(breakdown) > 0


def test_pipeline_start_investigation_by_id():
    """Verify execution of InvestigationPipeline by Invoice / Case ID."""
    pipeline = InvestigationPipeline()
    res = pipeline.run_pipeline("INV-2001", "VX-2001")

    assert res["invoice_id"] == "INV-2001"
    assert res["stage_2_triage"]["decision"] == "INVESTIGATE"
    assert res["stage_5_investigation"]["recommended_action"] == "APPLY_AMENDMENT"
    assert res["stage_7_human_gate"]["requires_human_payment_approval"] is True


def test_all_5_demo_scenarios():
    """Verify all 5 seeded demo scenarios run and return clean structured results."""
    pipeline = InvestigationPipeline()

    # Scenario 1: Clean invoice
    s1 = pipeline.run_pipeline("INV-1001", "VX-1001")
    assert s1["stage_5_investigation"]["recommended_action"] == "CLEAR"

    # Scenario 2: ACME Amendment confirmed
    s2 = pipeline.run_pipeline("INV-2001", "VX-2001")
    assert s2["stage_5_investigation"]["recommended_action"] == "APPLY_AMENDMENT"
    assert s2["stage_5_investigation"]["memory_verdict"] == "CONFIRMED"

    # Scenario 3: ACME Contradicted memory
    s3 = pipeline.run_pipeline("INV-2002", "VX-2002")
    assert s3["stage_5_investigation"]["recommended_action"] == "DRAFT_VENDOR_QUERY"
    assert s3["stage_5_investigation"]["memory_verdict"] == "CONTRADICTED"

    # Scenario 4: Human Correction applied
    s4 = pipeline.run_pipeline("INV-2044", "VX-2044")
    assert s4["stage_5_investigation"]["recommended_action"] == "REQUEST_CORRECTION"

    # Scenario 5: Fraud Signal
    s5 = pipeline.run_pipeline("INV-3005", "VX-3005")
    assert s5["stage_5_investigation"]["recommended_action"] == "FLAG_FRAUD"
    assert s5["stage_7_human_gate"]["requires_human_fraud_review"] is True


def test_human_feedback_reflection_and_future_recall():
    """Verify human supervisor feedback creates retained case experience that is recalled in future investigations."""
    pipeline = InvestigationPipeline()
    mem_repo = get_memory_repository()

    # Process a human correction on a case
    ref_res = pipeline.process_human_decision(
        case_id="VX-TEST-999",
        vendor_id="VND-002",
        vendor_name="ACME Corp",
        discrepancy_type="Price mismatch",
        agent_recommendation="APPLY_AMENDMENT",
        human_outcome="CORRECTED",
        human_notes="Supervisor correction: Verify amendment effective date before auto-releasing payment."
    )

    assert ref_res["human_outcome"] == "CORRECTED"
    assert "saved_memory" in ref_res

    # Recall memories for ACME Corp and verify the newly stored human correction lesson is present
    recalled = mem_repo.recall(query="amendment effective date", vendor_id="VND-002")
    assert len(recalled) > 0
    assert any("Supervisor correction" in m.get("lesson", "") or "effective date" in m.get("lesson", "").lower() for m in recalled)


if __name__ == "__main__":
    pytest.main([__file__])

