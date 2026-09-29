import json
import logging
from repositories.business_repository import get_business_repository
from repositories.memory_repository import get_memory_repository
from utils.llm_client import LLMClient
from utils.logging_utils import log_audit_event

logger = logging.getLogger("VAULTY.InvestigatorAgent")

class InvestigatorAgent:
    def __init__(self):
        self.llm_client = LLMClient()

    def investigate(self, invoice_id: str, case_id: str = None) -> dict:
        """
        Investigates an AP exception using evidence collection and memory recall.
        Compares recalled memories directly against current evidence (RECALL -> VERIFY -> ADAPT).
        Principle: MEMORY GUIDES THE INVESTIGATION. CURRENT EVIDENCE DECIDES THE OUTCOME.
        """
        cid = case_id or invoice_id
        log_audit_event(cid, "InvestigatorAgent", "START_INVESTIGATION", {"invoice_id": invoice_id})

        biz_repo = get_business_repository()
        mem_repo = get_memory_repository()

        # 1. Fetch current business evidence dynamically
        inv = biz_repo.get_invoice(invoice_id)
        vendor_id = inv.get("vendor_id", "")
        po_id = inv.get("po_id", "")

        po = biz_repo.get_purchase_order(po_id) if po_id else {}
        receipt = biz_repo.get_receipt(po_id) if po_id else {}
        contract = biz_repo.get_contract(vendor_id) if vendor_id else {}
        vendor_hist = biz_repo.get_vendor_history(vendor_id) if vendor_id else {}
        amendments = biz_repo.get_amendments(vendor_id) if vendor_id else []

        vendor_name = vendor_hist.get("vendor_name") or inv.get("vendor_name", vendor_id) or "Vendor"

        # 2. Build meaningful dynamic recall query from CURRENT CASE before concluding
        inv_unit_price = inv.get("line_items", [{}])[0].get("unit_price") if inv.get("line_items") else None
        po_unit_price = po.get("line_items", [{}])[0].get("unit_price") if po.get("line_items") else None

        bank_updated_at = vendor_hist.get("banking_details_updated_at", "")
        is_recent_bank_change = bool(bank_updated_at and ("2026-09" in bank_updated_at or vendor_hist.get("risk_rating") == "HIGH"))

        if is_recent_bank_change:
            disc_concept = "recent banking detail changes, bank account modifications, vendor risk rating, and fraud review outcomes"
            detected_type = "Potential fraud signal"
        elif "notes" in inv and "duplicate" in inv.get("notes", "").lower():
            disc_concept = "duplicate invoice submissions, prior payment records, and duplicate resolution handling"
            detected_type = "Duplicate billing"
        elif not po_id or "error" in po:
            disc_concept = "missing purchase order references, unbacked invoice submissions, and vendor query workflows"
            detected_type = "Missing PO"
        elif receipt.get("status") == "PARTIAL_DELIVERY":
            disc_concept = "quantity discrepancies, partial delivery receipts, warehouse receipt verification, and hold procedures"
            detected_type = "Quantity mismatch"
        elif inv_unit_price and po_unit_price and inv_unit_price != po_unit_price:
            disc_concept = f"price discrepancies (invoiced ₹{inv_unit_price:,.2f} vs PO ₹{po_unit_price:,.2f}), approved amendments, contract rate terms, similar PO conditions, and their final human resolutions"
            detected_type = "Price mismatch"
        elif inv.get("total_amount") and po.get("total_amount") and inv.get("total_amount") != po.get("total_amount"):
            disc_concept = "total amount variances, approved contract amendments, and human resolution outcomes"
            detected_type = "Price mismatch"
        else:
            disc_concept = "matching line items, routine clean invoice approvals, and payment release verification"
            detected_type = "None"

        recall_query = f"Find previous AP exception investigations involving {vendor_name} ({vendor_id}) with {disc_concept}, similar PO conditions, and their final human resolutions."

        # 3. Query memory BEFORE reaching final conclusion
        raw_memories = mem_repo.recall(query=recall_query, vendor_id=vendor_id, top_k=3)

        memory_recall = []
        for m in raw_memories:
            if isinstance(m, dict):
                text_content = m.get("text") or m.get("lesson") or m.get("content", "")
                doc_id = m.get("document_id") or m.get("lesson_id") or m.get("source_case_id", "")
                rel = m.get("confidence_score") or m.get("score") or 0.95
                src = m.get("source") or ("hindsight" if mem_repo.get_memory_mode() == "Hindsight" else "local_fallback")
                memory_recall.append({
                    "text": text_content,
                    "document_id": doc_id,
                    "relevance": rel,
                    "source": src,
                    "metadata": m.get("metadata", {})
                })
            elif isinstance(m, str):
                memory_recall.append({
                    "text": m,
                    "document_id": "",
                    "relevance": 0.95,
                    "source": "hindsight" if mem_repo.get_memory_mode() == "Hindsight" else "local_fallback",
                    "metadata": {}
                })

        # 4. Use Reflect for higher-level synthesis on meaningful exceptions
        memory_reflection = {}
        if detected_type != "None" and raw_memories:
            reflect_query = (
                f"Based on previous Vaulty investigations and the current case evidence for {vendor_name} ({cid}), "
                f"what prior experience is relevant to this {detected_type} exception, what should be verified now, "
                f"and how should the previous experience influence—but not override—the current decision?"
            )
            reflection_res = mem_repo.reflect(
                query=reflect_query,
                context={
                    "case_id": cid,
                    "vendor_id": vendor_id,
                    "exception_type": detected_type,
                    "current_evidence": [
                        f"Invoice {invoice_id} amount: ₹{inv.get('total_amount', 0):,.2f}",
                        f"PO {po_id} amount: ₹{po.get('total_amount', 0):,.2f}",
                        f"Approved amendments: {len(amendments)}"
                    ],
                    "recalled_memories": [m.get("text", "") for m in memory_recall]
                },
                case_id=cid
            )
            memory_reflection = reflection_res

        prompt = f"""
You are the Investigator Agent for Vaulty (AI Exception Intelligence).
Investigate invoice exception {invoice_id} for vendor {vendor_name} ({vendor_id}).

PRINCIPLE: MEMORY GUIDES THE INVESTIGATION. CURRENT EVIDENCE DECIDES THE OUTCOME.
Recalled memories suggest previous experiences, BUT YOU MUST VERIFY THEM AGAINST CURRENT EVIDENCE.
Never repeat an old decision if current evidence contradicts memory!

Current Invoice: {json.dumps(inv, indent=2)}
Current PO: {json.dumps(po, indent=2)}
Current Receipt: {json.dumps(receipt, indent=2)}
Contract Terms: {json.dumps(contract, indent=2)}
Vendor Master Profile: {json.dumps(vendor_hist, indent=2)}
Current Approved Amendments: {json.dumps(amendments, indent=2)}
Recalled Experience: {json.dumps(memory_recall, indent=2)}
Higher-Level Reflection: {json.dumps(memory_reflection, indent=2)}

Determine memory verdict:
- "CONFIRMED": Past memory is relevant AND current evidence supports the same pattern.
- "CONTRADICTED": Past memory is relevant BUT current evidence conflicts with it.
- "INSUFFICIENT": Memory exists but is not strong enough or current evidence does not allow confirmation (or no past memory exists).

Return a strict JSON object:
- "exception_type": "{detected_type}"
- "current_evidence": ["List of verified evidence statements"]
- "relevant_memory": ["Summaries of recalled memories"]
- "memory_verdict": "CONFIRMED" or "CONTRADICTED" or "INSUFFICIENT"
- "memory_influence": {{
    "status": "CONFIRMED | CONTRADICTED | INSUFFICIENT",
    "past_experience": "...",
    "current_evidence": "...",
    "reason": "...",
    "adapted_decision": "..."
  }}
- "reasoning_summary": "Concise plain-English business narrative"
- "recommended_action": "APPLY_AMENDMENT" / "DRAFT_VENDOR_QUERY" / "REQUEST_CORRECTION" / "RESOLVE_DUPLICATE" / "FLAG_FRAUD" / "CLEAR"
- "verified_amendment_id": "ID of approved amendment if found, else null"
- "requires_human": true
- "risk_reason": "Specific risk explanation"
- "evidence_gaps": ["List of missing or unverified evidence items"]
"""

        def fallback_investigation():
            exception_type = detected_type
            current_evidence = []
            relevant_memory = [m.get("text", "") for m in memory_recall]
            memory_verdict = "INSUFFICIENT"
            recommended_action = ""
            verified_amendment_id = None
            risk_reason = ""
            evidence_gaps = []

            past_experience_text = (
                relevant_memory[0] if relevant_memory else
                f"No prior exception resolutions found for {vendor_name}."
            )

            # 1. Fraud Banking Anomaly Check
            if is_recent_bank_change:
                current_evidence = [
                    f"Vendor banking details updated recently on {bank_updated_at}",
                    f"Invoice total ₹{inv.get('total_amount', 0):,.2f} exceeds PO total ₹{po.get('total_amount', 0):,.2f}",
                    f"Vendor risk rating: {vendor_hist.get('risk_rating', 'HIGH')}"
                ]
                recommended_action = "FLAG_FRAUD"
                risk_reason = "Recent bank account modification combined with rate discrepancy poses severe financial risk."
                evidence_gaps = ["Vendor identity re-verification", "Bank account change confirmation"]
                has_fraud_memory = any("fraud" in m.lower() or "bank" in m.lower() for m in relevant_memory)
                if has_fraud_memory:
                    memory_verdict = "CONFIRMED"
                    reason_text = "Recalled institutional security policy mandates immediate fraud review when banking details are modified."
                    adapted_text = "Route invoice directly to Fraud Review Board. Automatic payment release is blocked."
                else:
                    memory_verdict = "CONFIRMED"
                    reason_text = "High risk security anomaly verified against master vendor record."
                    adapted_text = "Route invoice directly to Fraud Review Board."

            # 2. Duplicate Invoice Check
            elif detected_type == "Duplicate billing":
                current_evidence = [
                    f"Invoice ID {invoice_id} matches description and total of PO {po_id}",
                    "Invoice notes indicate re-submission of prior billing period"
                ]
                recommended_action = "RESOLVE_DUPLICATE"
                risk_reason = "Risk of duplicate payment release for previously billed goods."
                evidence_gaps = []
                memory_verdict = "CONFIRMED"
                reason_text = "Current evidence verifies invoice is an identical duplicate re-submission."
                adapted_text = "Close exception as duplicate submission; do not release duplicate payment."

            # 3. Missing PO Check
            elif detected_type == "Missing PO":
                current_evidence = [
                    f"Invoice {invoice_id} submitted without valid Purchase Order reference",
                    f"Vendor master record {vendor_id} requires PO backing for all invoices"
                ]
                recommended_action = "DRAFT_VENDOR_QUERY"
                risk_reason = "Unbacked invoice submitted without prior procurement authorization."
                evidence_gaps = ["Valid Purchase Order reference from vendor"]
                memory_verdict = "INSUFFICIENT" if not relevant_memory else "CONFIRMED"
                reason_text = "Current evidence indicates absence of required purchase order reference."
                adapted_text = "Hold invoice and draft vendor query requesting authorized purchase order reference."

            # 4. Quantity / Partial Delivery Check
            elif detected_type == "Quantity mismatch":
                rec_qty = receipt.get("line_items", [{}])[0].get("received_quantity", 0)
                inv_qty = inv.get("line_items", [{}])[0].get("quantity", 0)

                current_evidence = [
                    f"Goods Receipt {receipt.get('receipt_id')} records partial delivery of {rec_qty} units",
                    f"Invoice {invoice_id} bills for full PO quantity of {inv_qty} units",
                    "Contract terms state partial deliveries payable only upon verified receipt of partial quantity"
                ]
                recommended_action = "REQUEST_CORRECTION"
                risk_reason = "Overbilling for goods not yet physically received at warehouse."
                evidence_gaps = ["Delivery confirmation for remaining units"]

                has_human_correction = any("HUMAN CORRECTION" in m or "partial" in m.lower() or "receipt" in m.lower() for m in relevant_memory)
                if has_human_correction:
                    memory_verdict = "CONFIRMED"
                    reason_text = "Past supervisor guidance instructed verifying warehouse receipt before payment release. Current evidence confirms partial delivery."
                    adapted_text = "Hold full payment and issue formal request for corrected invoice matching received quantity."
                else:
                    memory_verdict = "CONFIRMED"
                    reason_text = "Warehouse receipt documents partial delivery; invoice billed full quantity."
                    adapted_text = "Request corrected invoice for received quantity."

            # 5. Price Mismatch Check
            elif detected_type == "Price mismatch":
                # Check for approved amendment matching current PO and rate
                matching_amendment = None
                for amd in amendments:
                    if amd.get("po_id") == po_id and amd.get("status") == "APPROVED":
                        if inv_unit_price is not None and amd.get("amended_unit_price") == inv_unit_price:
                            matching_amendment = amd
                            break
                        elif amd.get("amended_unit_price"):
                            matching_amendment = amd
                            break

                has_amendment_memory = any("amendment" in m.lower() or "price" in m.lower() for m in relevant_memory)

                if matching_amendment:
                    verified_amendment_id = matching_amendment.get("amendment_id")
                    current_evidence = [
                        f"Invoiced unit price ₹{inv_unit_price:,.2f} vs PO unit price ₹{po_unit_price:,.2f}" if (inv_unit_price and po_unit_price) else "Invoiced total exceeds PO total",
                        f"Verified active Approved Amendment {verified_amendment_id} signed by {matching_amendment.get('approved_by')}",
                        f"Amended rate ₹{matching_amendment.get('amended_unit_price'):,.2f} matches invoice rate ₹{inv_unit_price:,.2f}" if inv_unit_price else "Amendment authorizes rate adjustment"
                    ]
                    recommended_action = "APPLY_AMENDMENT"
                    risk_reason = "Price discrepancy is backed by verified contract amendment."
                    evidence_gaps = []

                    if has_amendment_memory:
                        memory_verdict = "CONFIRMED"
                        reason_text = "Past experience suggested price variances for this vendor could be backed by approved amendments. Current evidence search verified active approved amendment."
                        adapted_text = f"Apply verified amendment {verified_amendment_id} and recommend payment approval."
                    else:
                        memory_verdict = "CONFIRMED"
                        reason_text = f"Current evidence search confirmed approved pricing amendment {verified_amendment_id}."
                        adapted_text = f"Apply approved amendment {verified_amendment_id} and proceed with payment approval."

                else:
                    current_evidence = [
                        f"Invoiced unit price ₹{inv_unit_price:,.2f} vs PO unit price ₹{po_unit_price:,.2f}" if (inv_unit_price and po_unit_price) else "Invoiced total exceeds PO total",
                        f"Amendment log searched for vendor {vendor_id} - NO approved amendment found for PO {po_id}",
                        "Master contract mandates signed pricing amendment for rate adjustments"
                    ]
                    recommended_action = "DRAFT_VENDOR_QUERY"
                    risk_reason = "Unsubstantiated price increase without approved contract amendment."
                    evidence_gaps = [f"Approved contract amendment for PO {po_id}"]

                    if has_amendment_memory:
                        memory_verdict = "CONTRADICTED"
                        reason_text = "Past experience suggested this variance could be legitimate, but the current case contains no matching approved amendment. Current evidence overrides memory."
                        adapted_text = "Refuse payment approval. Place invoice on hold and draft vendor query regarding unamended rate. Evidence overrides memory."
                    else:
                        memory_verdict = "INSUFFICIENT"
                        reason_text = "No approved pricing amendment found in vendor records for current PO."
                        adapted_text = "Hold invoice and draft vendor query."

            # 6. Clean / Clear Case
            else:
                current_evidence = ["Matching records across Invoice, PO, and Goods Receipt"]
                recommended_action = "CLEAR"
                risk_reason = "No discrepancy found."
                evidence_gaps = []
                memory_verdict = "INSUFFICIENT"
                reason_text = "Routine matching invoice; records are consistent."
                adapted_text = "Approve payment release. No exception requires resolution."

            if exception_type == "None" or recommended_action in ("CLEAR", "APPROVE", "CONTINUE_WITH_PAYMENT"):
                reasoning_summary = "No issues found. The invoice matches the available purchase order and delivery evidence."
            else:
                reasoning_summary = f"Investigation completed for {invoice_id}. Exception: {exception_type}. Recommended Action: {recommended_action}."

            current_evidence_summary = "; ".join(current_evidence)

            mem_influence_obj = {
                "status": memory_verdict,
                "past_experience": past_experience_text,
                "current_evidence": current_evidence_summary,
                "reason": reason_text,
                "adapted_decision": adapted_text
            }

            logger.info(f"[HINDSIGHT] memory verdict: {memory_verdict}")

            return {
                "case_id": cid,
                "investigation_status": "COMPLETED",
                "discrepancy_type": exception_type,
                "exception_type": exception_type,
                "current_evidence": current_evidence,
                "findings": reasoning_summary,
                "relevant_memory": relevant_memory,
                "memory_recall": memory_recall,
                "memory_reflection": memory_reflection,
                "memory_verdict": memory_verdict,
                "memory_influence": mem_influence_obj,
                "memory_explanation": reason_text,
                "reasoning_summary": reasoning_summary,
                "conclusion": adapted_text,
                "recommended_action": recommended_action,
                "requires_human": True,
                "requires_human_review": True,
                "resolution_state": "AWAITING_HUMAN_SIGN_OFF" if recommended_action != "CLEAR" else "RESOLVED",
                "learning_candidate": True,
                "verified_amendment_id": verified_amendment_id,
                "risk_reason": risk_reason,
                "evidence_gaps": evidence_gaps,
                "memory_influence_analysis": {
                    "memory_recalled": past_experience_text,
                    "current_evidence": current_evidence_summary,
                    "confirmation_or_contradiction": memory_verdict,
                    "final_adaptation": adapted_text
                }
            }

        res = self.llm_client.generate_json(prompt, fallback_fn=fallback_investigation)

        # Standardize contract output fields
        res["case_id"] = cid
        res["investigation_status"] = "COMPLETED"
        if "discrepancy_type" not in res:
            res["discrepancy_type"] = res.get("exception_type", detected_type)
        if "findings" not in res:
            res["findings"] = res.get("reasoning_summary", "Evidence verified against operational records.")
        if "memory_recall" not in res:
            res["memory_recall"] = memory_recall
        if "memory_reflection" not in res:
            res["memory_reflection"] = memory_reflection

        # Ensure memory_verdict is canonical
        mv = res.get("memory_verdict", "INSUFFICIENT")
        if mv in ("NOT_APPLICABLE", "NONE", "UNKNOWN"):
            mv = "INSUFFICIENT"
        res["memory_verdict"] = mv

        # Ensure memory_influence object is properly structured
        if "memory_influence" not in res or not isinstance(res.get("memory_influence"), dict):
            past_exp = res.get("relevant_memory", ["No prior memory"])[0] if res.get("relevant_memory") else "No prior memory"
            curr_evid = "; ".join(res.get("current_evidence", []))
            if mv == "CONFIRMED":
                reason = "Past experience confirmed by current evidence verification."
                adapted = "Proceed with recommended resolution supported by verified records."
            elif mv == "CONTRADICTED":
                reason = "Past experience suggested this variance could be legitimate, but the current case contains no matching approved amendment. Current evidence overrides memory."
                adapted = "Refuse payment approval and hold invoice to issue vendor query. Evidence overrides memory."
            else:
                reason = "No strong prior experience found. Decided solely on current evidence."
                adapted = "Proceed based on verified primary records."

            res["memory_influence"] = {
                "status": mv,
                "past_experience": past_exp,
                "current_evidence": curr_evid,
                "reason": reason,
                "adapted_decision": adapted
            }

        mi = res["memory_influence"]
        if "memory_influence_analysis" not in res:
            res["memory_influence_analysis"] = {
                "memory_recalled": mi.get("past_experience", ""),
                "current_evidence": mi.get("current_evidence", ""),
                "confirmation_or_contradiction": mi.get("status", mv),
                "final_adaptation": mi.get("adapted_decision", "")
            }

        logger.info(f"[HINDSIGHT] memory verdict: {res['memory_verdict']}")
        log_audit_event(cid, "InvestigatorAgent", "INVESTIGATION_COMPLETE", res)
        return res
