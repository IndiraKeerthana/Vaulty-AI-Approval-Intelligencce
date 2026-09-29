import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from repositories.business_repository import get_business_repository
from services.analytics_service import get_analytics_service
from streamlit.testing.v1 import AppTest

def verify_kpis():
    print("--- Starting KPI Aggregation Verification ---")
    biz_repo = get_business_repository()
    analytics = get_analytics_service()

    # Initial state check
    cases = biz_repo.get_all_cases()
    persisted_resolved = len([c for c in cases if str(c.get("status", "")).upper() in ("RESOLVED", "APPROVED", "COMPLETED")])
    persisted_held = len([c for c in cases if str(c.get("status", "")).upper() in ("ON_HOLD", "HELD", "ON HOLD", "ESCALATED TO PROCUREMENT", "HOLD", "PENDING VENDOR RESPONSE", "QUERY", "VENDOR_QUERY")])

    home_metrics = analytics.get_home_metrics()
    app_summary = analytics.get_approval_summary()

    print(f"Persisted resolved count in repo: {persisted_resolved}")
    print(f"Home metrics resolved count: {home_metrics['resolved_count']}")
    assert home_metrics['resolved_count'] == persisted_resolved, "Home metrics resolved count does not match repo"
    assert home_metrics['resolved_count'] > 0, "Resolved count should be > 0"

    print(f"Persisted held count in repo: {persisted_held}")
    print(f"Approvals on_hold + query count: {app_summary['on_hold'] + app_summary['vendor_query']}")
    assert (app_summary['on_hold'] + app_summary['vendor_query']) == persisted_held, "Approvals summary on hold/query does not match repo"
    assert (app_summary['on_hold'] + app_summary['vendor_query']) > 0, "Held/query count should be > 0"

    # Test state transition: Approve an open case (e.g. VX-4001)
    case_to_test = "VX-4001"
    biz_repo.update_case(case_to_test, "UNPROCESSED", "Pending Triage")
    res_before = analytics.get_home_metrics()['resolved_count']
    
    # Approve case
    biz_repo.update_approval_status(case_to_test, "RESOLVED", "Payment release approved by Finance Manager.")
    res_after = analytics.get_home_metrics()['resolved_count']
    assert res_after == res_before + 1, f"Expected resolved count to increase by 1, was {res_before} -> {res_after}"
    print(f"PASSED: Approving a case increases Home RESOLVED KPI from {res_before} to {res_after}")

    # Test state transition: Put case on hold
    held_before = analytics.get_approval_summary()['on_hold'] + analytics.get_approval_summary()['vendor_query']
    biz_repo.update_approval_status(case_to_test, "ON_HOLD", "Payment held pending review.")
    held_after = analytics.get_approval_summary()['on_hold'] + analytics.get_approval_summary()['vendor_query']
    res_after_hold = analytics.get_home_metrics()['resolved_count']
    assert held_after == held_before + 1, f"Expected held count to increase by 1, was {held_before} -> {held_after}"
    assert res_after_hold == res_after - 1, f"Expected resolved count to decrease by 1, was {res_after} -> {res_after_hold}"
    print(f"PASSED: Putting case on hold increases ON HOLD / QUERY KPI from {held_before} to {held_after}")

    # Revert test case status
    biz_repo.update_case(case_to_test, "UNPROCESSED", "Pending Triage")

    # Verify via Streamlit AppTest for UI rendering of cards
    at = AppTest.from_file("app.py", default_timeout=15).run()
    # Check Home page rendering
    home_texts = "\n".join([m.value for m in at.markdown])
    assert "RESOLVED" in home_texts, "RESOLVED KPI label missing from Home UI"
    assert "Verified and closed" in home_texts, "Verified and closed subtitle missing from Home UI"
    print("PASSED: Home UI renders RESOLVED KPI tile")

    # Check Approvals page rendering
    at.session_state["current_nav"] = "Approvals"
    at.session_state["primary_nav_radio"] = "Approvals"
    at.session_state["view_mode"] = "list"
    at = at.run()
    app_texts = "\n".join([m.value for m in at.markdown])
    assert "On hold / Query" in app_texts, "On hold / Query KPI missing from Approvals UI"
    print("PASSED: Approvals UI renders On hold / Query KPI tile")

    print("\nALL KPI AGGREGATION VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    verify_kpis()
