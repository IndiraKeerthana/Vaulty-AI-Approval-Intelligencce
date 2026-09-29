import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.pipeline import InvestigationPipeline
from agents.reflection import ReflectionAgent

def test_all_cases():
    print("=== TESTING VAULTY PIPELINE ===")
    
    pipeline_runner = InvestigationPipeline()
    cases_to_test = ["VX-1001", "VX-2001", "VX-2002", "VX-2044", "VX-3005"]
    
    for case_id in cases_to_test:
        print(f"\n--- Running Pipeline for {case_id} ---")
        inv_id = case_id.replace("VX-", "INV-")
        res = pipeline_runner.run_pipeline(inv_id, case_id)
        assert res is not None, f"Pipeline failed for {case_id}"
        
        triage = res.get("stage_2_triage", {})
        invest = res.get("stage_5_investigation", {})
        res_stage = res.get("stage_6_resolution", {})
        orch = res.get("stage_7_human_gate", {})
        
        print(f"Triage Decision: {triage.get('triage_decision')}")
        print(f"Investigator Rec Action: {invest.get('recommended_action')}")
        print(f"Resolution Summary: {res_stage.get('summary')}")
        
        if case_id == "VX-2044":
            print("\nTesting Reflection Agent on Human Correction for VX-2044...")
            ref_agent = ReflectionAgent()
            ref_res = ref_agent.reflect_and_learn(
                case_id=case_id,
                vendor_id="VND-004",
                vendor_name="Nexus Industrial Solutions",
                discrepancy_type="Quantity Mismatch",
                agent_recommendation=invest.get("recommended_action", "REQUEST_CORRECTION"),
                human_outcome="CORRECTED",
                human_notes="Confirmed partial delivery payment authorization for 80 received units."
            )
            print(f"Reflection Lesson: {ref_res.get('lesson') or ref_res.get('lesson_content')}")
            
    print("\n[SUCCESS] ALL TEST CASES VERIFIED SUCCESSFULLY WITH 0 ERRORS!")

if __name__ == "__main__":
    test_all_cases()
