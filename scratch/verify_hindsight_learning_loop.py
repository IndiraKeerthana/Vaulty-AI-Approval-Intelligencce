import sys
import os
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.pipeline import InvestigationPipeline
from repositories.memory_repository import get_memory_repository
from repositories.business_repository import get_business_repository

def main():
    print("=" * 60)
    print("VAULTY HINDSIGHT LEARNING LOOP VERIFICATION")
    print("=" * 60)

    pipeline = InvestigationPipeline()
    mem_repo = get_memory_repository()
    biz_repo = get_business_repository()

    print(f"\n1. Memory Provider Mode: {mem_repo.get_memory_mode()}")

    # --- STEP 1: CASE A ---
    print("\n[STEP 1: CASE A] First Investigation on ACME Price Discrepancy (PO-2001)")
    res_a = pipeline.run_pipeline("INV-2001", "VX-2001")
    inv_a = res_a["stage_5_investigation"]
    print(f"  - Case ID: {res_a['case_id']}")
    print(f"  - Exception: {inv_a['discrepancy_type']}")
    print(f"  - Memory Verdict: {inv_a['memory_verdict']}")
    print(f"  - Recommended Action: {inv_a['recommended_action']}")

    # Human supervisor approves payment release
    print("\n  -> Simulating Human Approval Decision...")
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
    print("  - Retained Document ID:", ref_res_a.get("document_id"))
    print("  - Tags:", ref_res_a.get("tags"))
    print("  - Retained Narrative Snippet:\n   ", ref_res_a.get("lesson", "")[:180] + "...")

    # --- STEP 2: CASE B ---
    print("\n[STEP 2: CASE B] Second Investigation on Similar Case with Approved Amendment")
    res_b = pipeline.run_pipeline("INV-2001", "VX-2001")
    inv_b = res_b["stage_5_investigation"]
    mi_b = inv_b["memory_influence"]

    print("  - Recalled Memories Count:", len(res_b.get("memory_recall", [])))
    print("  - Current Amendment Verified:", inv_b.get("verified_amendment_id"))
    print("  - Memory Verdict:", inv_b["memory_verdict"])
    print("  - Memory Influence Status:", mi_b.get("status"))
    print("  - Why (Reason):", mi_b.get("reason"))
    print("  - Adapted Decision:", mi_b.get("adapted_decision"))
    assert inv_b["memory_verdict"] == "CONFIRMED", "Case B verdict must be CONFIRMED"

    # --- STEP 3: CASE C ---
    print("\n[STEP 3: CASE C] Third Investigation on Similar Case WITHOUT Approved Amendment (PO-2002)")
    res_c = pipeline.run_pipeline("INV-2002", "VX-2002")
    inv_c = res_c["stage_5_investigation"]
    mi_c = inv_c["memory_influence"]

    print("  - Recalled Memories Count:", len(res_c.get("memory_recall", [])))
    print("  - Current Amendment Verified:", inv_c.get("verified_amendment_id"))
    print("  - Memory Verdict:", inv_c["memory_verdict"])
    print("  - Memory Influence Status:", mi_c.get("status"))
    print("  - Why (Reason):", mi_c.get("reason"))
    print("  - Adapted Decision:", mi_c.get("adapted_decision"))
    print("  - Recommended Action:", inv_c.get("recommended_action"))

    assert inv_c["memory_verdict"] == "CONTRADICTED", "Case C verdict must be CONTRADICTED"
    assert "evidence overrides memory" in mi_c.get("reason", "").lower() or "evidence overrides memory" in mi_c.get("adapted_decision", "").lower(), "Must state evidence overrides memory"
    assert inv_c["recommended_action"] == "DRAFT_VENDOR_QUERY", "Action must adapt to DRAFT_VENDOR_QUERY"

    print("\n" + "=" * 60)
    print("ALL LEARNING LOOP CHECKS PASSED PERFECTLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()
