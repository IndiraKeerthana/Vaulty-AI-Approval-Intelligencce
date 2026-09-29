import logging
from repositories.business_repository import get_business_repository

logger = logging.getLogger("VAULTY.BusinessTools")

def repo():
    return get_business_repository()

def get_data_mode() -> str:
    return repo().get_data_mode()

def get_all_cases() -> list:
    return repo().get_all_cases()

def get_all_vendors() -> list:
    return repo().get_all_vendors()

def get_all_invoices() -> list:
    return repo().get_all_invoices()

def get_all_purchase_orders() -> list:
    return repo().get_all_purchase_orders()

def get_invoice(invoice_id: str) -> dict:
    return repo().get_invoice(invoice_id)

def get_po(po_id: str) -> dict:
    return repo().get_purchase_order(po_id)

def get_receipt(po_id: str) -> dict:
    return repo().get_receipt(po_id)

def get_contract(vendor_id: str) -> dict:
    return repo().get_contract(vendor_id)

def get_vendor_history(vendor_id: str) -> dict:
    return repo().get_vendor_history(vendor_id)

def get_amendment_log(vendor_id: str) -> list:
    return repo().get_amendments(vendor_id)

def update_exception_status(exception_id: str, status: str, notes: str) -> dict:
    return repo().update_case(exception_id, status, notes)

def draft_vendor_query(vendor_id: str, invoice_id: str, discrepancy: str) -> dict:
    repo().create_case_event(
        case_id=invoice_id,
        agent="ResolutionAgent",
        action="DRAFT_VENDOR_QUERY",
        details={"vendor_id": vendor_id, "discrepancy": discrepancy}
    )
    update_exception_status(invoice_id, "PENDING VENDOR RESPONSE", f"Query drafted for vendor {vendor_id}: {discrepancy}")
    return {
        "action": "draft_vendor_query",
        "status": "DRAFTED",
        "message": f"Official query drafted to vendor {vendor_id} regarding: {discrepancy}. Invoice placed on PENDING VENDOR RESPONSE."
    }

def request_corrected_invoice(invoice_id: str, reason: str) -> dict:
    repo().create_case_event(
        case_id=invoice_id,
        agent="ResolutionAgent",
        action="REQUEST_CORRECTED_INVOICE",
        details={"reason": reason}
    )
    update_exception_status(invoice_id, "CORRECTION REQUESTED", f"Corrected invoice requested: {reason}")
    return {
        "action": "request_corrected_invoice",
        "status": "REQUESTED",
        "message": f"Corrected invoice requested for {invoice_id}. Reason: {reason}."
    }

def apply_contract_amendment_reference(invoice_id: str, amendment_id: str) -> dict:
    repo().create_case_event(
        case_id=invoice_id,
        agent="ResolutionAgent",
        action="APPLY_CONTRACT_AMENDMENT",
        details={"amendment_id": amendment_id}
    )
    return {
        "action": "apply_contract_amendment_reference",
        "status": "LINKED",
        "amendment_id": amendment_id,
        "message": f"Successfully linked contract amendment {amendment_id} to invoice {invoice_id}."
    }

def close_as_resolved(exception_id: str, resolution_summary: str) -> dict:
    update_exception_status(exception_id, "RESOLVED", resolution_summary)
    repo().create_case_event(
        case_id=exception_id,
        agent="ResolutionAgent",
        action="CLOSE_AS_RESOLVED",
        details={"resolution_summary": resolution_summary}
    )
    return {
        "action": "close_as_resolved",
        "status": "RESOLVED",
        "summary": resolution_summary
    }

def escalate_to_procurement(case_id: str, reason: str) -> dict:
    update_exception_status(case_id, "ESCALATED TO PROCUREMENT", reason)
    repo().create_case_event(
        case_id=case_id,
        agent="ResolutionAgent",
        action="ESCALATE_TO_PROCUREMENT",
        details={"reason": reason}
    )
    return {
        "action": "escalate_to_procurement",
        "status": "ESCALATED",
        "message": f"Case {case_id} escalated to Procurement team. Reason: {reason}"
    }

def flag_for_fraud_review(case_id: str, reasoning: str) -> dict:
    update_exception_status(case_id, "FRAUD REVIEW", reasoning)
    repo().create_case_event(
        case_id=case_id,
        agent="ResolutionAgent",
        action="FLAG_FOR_FRAUD_REVIEW",
        details={"reasoning": reasoning}
    )
    return {
        "action": "flag_for_fraud_review",
        "status": "FRAUD_REVIEW",
        "message": f"Potential fraud signal detected on case {case_id}. Normal resolution bypassed. Routed directly to FRAUD REVIEW."
    }

def create_new_simulated_case(**kwargs) -> dict:
    return repo().create_simulated_case(**kwargs)
