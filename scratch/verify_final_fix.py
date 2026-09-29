import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from streamlit.testing.v1 import AppTest
from repositories.business_repository import get_business_repository

def run_verification():
    print("--- Starting Final Verification ---")

    # Reset test cases to initial state for testing
    biz_repo = get_business_repository()
    biz_repo.update_case("VX-1001", "UNPROCESSED", "Pending Triage")
    biz_repo.update_case("VX-2001", "UNPROCESSED", "Pending Triage")

    # 1. Clean case initial render (VX-1001)
    at = AppTest.from_file("app.py", default_timeout=15).run()
    at.session_state["selected_case_id"] = "VX-1001"
    at.session_state["previous_nav"] = "Home"
    at.session_state["view_mode"] = "detail"
    at = at.run()

    md_texts = [m.value for m in at.markdown]
    all_text = "\n".join(md_texts)

    assert "No issues found. The invoice matches the available purchase order and delivery evidence." in all_text, f"Clean case findings text missing. Found:\n{all_text}"
    assert "Everything looks good. You can continue with the payment." in all_text, "Clean case what this means text missing"
    assert "Continue with payment" in all_text, "Clean case recommended action text missing"
    assert "Payment is ready for your approval." in all_text, "Clean case human gate text missing"
    assert len(at.button) > 0, "Approval button should be visible"
    print("PASSED: Scenario 1 (Clean case language & initial state)")

    # 2. Approve action
    app_btn = [b for b in at.button if "APPROVE PAYMENT RELEASE" in b.label]
    assert len(app_btn) > 0, "Approve button not found"
    at = app_btn[0].click().run()

    md_texts_after_app = [m.value for m in at.markdown]
    all_text_app = "\n".join(md_texts_after_app)

    assert "PAYMENT APPROVED SUCCESSFULLY" in all_text_app, "PAYMENT APPROVED SUCCESSFULLY banner missing"
    assert "Payment release has been approved by the authorized reviewer." in all_text_app, "Approved subtitle missing"
    assert "THIS NEEDS YOUR INPUT" not in all_text_app, "THIS NEEDS YOUR INPUT should be removed"
    assert not any("APPROVE PAYMENT RELEASE" in b.label for b in at.button if hasattr(b, "label")), "Approve button should be gone"
    assert not any("REQUEST CORRECTION / HOLD" in b.label for b in at.button if hasattr(b, "label")), "Hold button should be gone"
    print("PASSED: Scenario 2 (Approve action & UI replacement)")

    # 4. Reopen decided case
    at2 = AppTest.from_file("app.py", default_timeout=15).run()
    at2.session_state["selected_case_id"] = "VX-1001"
    at2.session_state["previous_nav"] = "Home"
    at2.session_state["view_mode"] = "detail"
    at2 = at2.run()

    all_text_reopen = "\n".join([m.value for m in at2.markdown])
    assert "PAYMENT APPROVED SUCCESSFULLY" in all_text_reopen, "Reopened case should stay APPROVED"
    assert not any("APPROVE PAYMENT RELEASE" in b.label for b in at2.button if hasattr(b, "label")), "Approval buttons must NOT return"
    print("PASSED: Scenario 4 (Reopening approved case persists completed state)")

    # 3. Hold action (on another open case VX-2001)
    at3 = AppTest.from_file("app.py", default_timeout=15).run()
    at3.session_state["selected_case_id"] = "VX-2001"
    at3.session_state["previous_nav"] = "Approvals"
    at3.session_state["view_mode"] = "detail"
    at3 = at3.run()

    rej_btn = [b for b in at3.button if "REQUEST CORRECTION / HOLD" in b.label]
    assert len(rej_btn) > 0, "Hold button not found on VX-2001"
    at3 = rej_btn[0].click().run()

    all_text_hold = "\n".join([m.value for m in at3.markdown])
    assert "PAYMENT ON HOLD" in all_text_hold, "PAYMENT ON HOLD banner missing"
    assert "Payment release has been placed on hold pending further review." in all_text_hold, "Hold subtitle missing"
    assert "THIS NEEDS YOUR INPUT" not in all_text_hold, "THIS NEEDS YOUR INPUT should be removed"
    assert not any("APPROVE PAYMENT RELEASE" in b.label for b in at3.button if hasattr(b, "label")), "Approve button should be gone"
    print("PASSED: Scenario 3 (Hold action & UI replacement)")

    # Reopen held case
    at4 = AppTest.from_file("app.py", default_timeout=15).run()
    at4.session_state["selected_case_id"] = "VX-2001"
    at4.session_state["previous_nav"] = "Approvals"
    at4.session_state["view_mode"] = "detail"
    at4 = at4.run()

    all_text_reopen_hold = "\n".join([m.value for m in at4.markdown])
    assert "PAYMENT ON HOLD" in all_text_reopen_hold, "Reopened case should stay ON HOLD"
    assert not any("APPROVE PAYMENT RELEASE" in b.label for b in at4.button if hasattr(b, "label")), "Approval buttons must NOT return"
    print("PASSED: Scenario 4b (Reopening held case persists ON HOLD state)")

    # Reset test cases after verification
    biz_repo.update_case("VX-1001", "UNPROCESSED", "Pending Triage")
    biz_repo.update_case("VX-2001", "UNPROCESSED", "Pending Triage")

    print("\nALL VERIFICATION SCENARIOS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_verification()
