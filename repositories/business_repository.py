import os
import json
import datetime
import logging
from abc import ABC, abstractmethod
from utils.config import DATA_DIR
from utils.supabase_client import get_supabase_client, is_supabase_available
from repositories.supabase_repository import SupabaseBusinessRepository

logger = logging.getLogger("VAULTY.BusinessRepository")

class AbstractBusinessRepository(ABC):
    @abstractmethod
    def get_all_cases(self) -> list:
        pass

    @abstractmethod
    def get_all_vendors(self) -> list:
        pass

    @abstractmethod
    def get_all_invoices(self) -> list:
        pass

    @abstractmethod
    def get_all_purchase_orders(self) -> list:
        pass

    @abstractmethod
    def get_case(self, case_id: str) -> dict:
        pass

    @abstractmethod
    def get_cases_by_status(self, status: str) -> list:
        pass

    @abstractmethod
    def get_cases_by_vendor(self, vendor_id: str) -> list:
        pass

    @abstractmethod
    def get_cases_by_discrepancy_type(self, discrepancy_type: str) -> list:
        pass

    @abstractmethod
    def get_invoice(self, invoice_id: str) -> dict:
        pass

    @abstractmethod
    def get_vendor(self, vendor_id: str) -> dict:
        pass

    @abstractmethod
    def get_purchase_order(self, po_id: str) -> dict:
        pass

    @abstractmethod
    def get_receipt(self, po_id: str) -> dict:
        pass

    @abstractmethod
    def get_contract(self, vendor_id: str) -> dict:
        pass

    @abstractmethod
    def get_amendments(self, vendor_id: str) -> list:
        pass

    @abstractmethod
    def get_vendor_history(self, vendor_id: str) -> dict:
        pass

    @abstractmethod
    def get_case_events(self, case_id: str = None) -> list:
        pass

    @abstractmethod
    def update_case(self, case_id: str, status: str, notes: str) -> dict:
        pass

    @abstractmethod
    def update_approval_status(self, case_id: str, approval_status: str, notes: str, actor: str = "Finance Manager") -> dict:
        pass

    @abstractmethod
    def create_case_event(self, case_id: str, agent: str, action: str, details: dict) -> dict:
        pass

    @abstractmethod
    def get_audit_logs(self, case_id: str = None) -> list:
        pass

    @abstractmethod
    def create_simulated_case(self, **kwargs) -> dict:
        pass

    @abstractmethod
    def get_data_mode(self) -> str:
        pass


class LocalJsonBusinessRepository(AbstractBusinessRepository):
    """Local JSON backing store for offline / fallback operations."""
    
    def _load_data(self, filename: str) -> list:
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            return []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return []

    def _save_data(self, filename: str, data: list):
        filepath = os.path.join(DATA_DIR, filename)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving {filename}: {e}")

    def get_all_cases(self) -> list:
        cases = self._load_data("cases.json")
        invoices = self._load_data("invoices.json")
        inv_map = {inv.get("invoice_id"): inv for inv in invoices if isinstance(inv, dict)}
        for c in cases:
            if isinstance(c, dict) and ("po_id" not in c or not c["po_id"]):
                inv = inv_map.get(c.get("invoice_id"))
                if inv and isinstance(inv, dict) and "po_id" in inv:
                    c["po_id"] = inv["po_id"]
        return cases

    def get_all_vendors(self) -> list:
        return self._load_data("vendors.json")

    def get_all_invoices(self) -> list:
        return self._load_data("invoices.json")

    def get_all_purchase_orders(self) -> list:
        return self._load_data("purchase_orders.json")

    def get_case(self, case_id: str) -> dict:
        cases = self.get_all_cases()
        for c in cases:
            if c.get("case_id") == case_id or c.get("invoice_id") == case_id:
                return c
        return {"error": f"Case {case_id} not found"}

    def get_cases_by_status(self, status: str) -> list:
        return [c for c in self.get_all_cases() if c.get("status") == status]

    def get_cases_by_vendor(self, vendor_id: str) -> list:
        return [c for c in self.get_all_cases() if c.get("vendor_id") == vendor_id or c.get("vendor_name") == vendor_id]

    def get_cases_by_discrepancy_type(self, discrepancy_type: str) -> list:
        return [c for c in self.get_all_cases() if c.get("discrepancy_type") == discrepancy_type]

    def get_invoice(self, invoice_id: str) -> dict:
        invoices = self.get_all_invoices()
        for inv in invoices:
            if inv.get("invoice_id") == invoice_id:
                return inv
        return {"error": f"Invoice {invoice_id} not found"}

    def get_vendor(self, vendor_id: str) -> dict:
        vendors = self.get_all_vendors()
        for v in vendors:
            if v.get("vendor_id") == vendor_id or v.get("vendor_name") == vendor_id:
                return v
        return {"error": f"Vendor {vendor_id} not found"}

    def get_purchase_order(self, po_id: str) -> dict:
        if not po_id:
            return {"error": "No PO reference provided"}
        pos = self.get_all_purchase_orders()
        for po in pos:
            if po.get("po_id") == po_id:
                return po
        return {"error": f"Purchase Order {po_id} not found"}

    def get_receipt(self, po_id: str) -> dict:
        if not po_id:
            return {"error": "No PO reference provided"}
        receipts = self._load_data("receipts.json")
        found = [r for r in receipts if r.get("po_id") == po_id]
        if found:
            return found[0]
        return {"error": f"Receipt for PO {po_id} not found"}

    def get_contract(self, vendor_id: str) -> dict:
        contracts = self._load_data("contracts.json")
        for ctr in contracts:
            if ctr.get("vendor_id") == vendor_id:
                return ctr
        return {"error": f"Contract for vendor {vendor_id} not found"}

    def get_amendments(self, vendor_id: str) -> list:
        amendments = self._load_data("amendments.json")
        return [a for a in amendments if a.get("vendor_id") == vendor_id]

    def get_vendor_history(self, vendor_id: str) -> dict:
        return self.get_vendor(vendor_id)

    def get_case_events(self, case_id: str = None) -> list:
        logs = self._load_data("audit_log.json")
        if case_id:
            return [l for l in logs if l.get("case_id") == case_id]
        return logs

    def get_audit_logs(self, case_id: str = None) -> list:
        return self.get_case_events(case_id)

    def update_case(self, case_id: str, status: str, notes: str) -> dict:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cases = self.get_all_cases()
        updated = False
        target_case = None
        for c in cases:
            if c.get("case_id") == case_id or c.get("invoice_id") == case_id:
                c["status"] = status
                c["last_action"] = notes
                c["updated_at"] = now_str
                updated = True
                target_case = c
                break
        if updated:
            self._save_data("cases.json", cases)
        return target_case or {"case_id": case_id, "status": status, "last_action": notes}

    def update_approval_status(self, case_id: str, approval_status: str, notes: str, actor: str = "Finance Manager") -> dict:
        res = self.update_case(case_id, approval_status, notes)
        self.create_case_event(case_id, actor, f"APPROVAL_STATUS_{approval_status}", {"notes": notes})
        return res

    def create_case_event(self, case_id: str, agent: str, action: str, details: dict) -> dict:
        event = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "case_id": case_id,
            "agent": agent,
            "action": action,
            "details": details
        }
        logs = self._load_data("audit_log.json")
        logs.insert(0, event)
        self._save_data("audit_log.json", logs)
        return event

    def create_simulated_case(
        self,
        vendor_id: str,
        vendor_name: str,
        invoice_id: str,
        po_id: str,
        amount: float,
        discrepancy_type: str,
        invoice_date: str,
        po_amount: float,
        receipt_qty: int,
        invoice_qty: int,
        unit_price: float,
        bank_account: str,
        is_recent_bank_update: bool = False
    ) -> dict:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        inv_data = {
            "invoice_id": invoice_id,
            "vendor_id": vendor_id,
            "vendor_name": vendor_name,
            "po_id": po_id,
            "invoice_date": invoice_date,
            "currency": "INR",
            "total_amount": amount,
            "line_items": [{
                "item_id": "ITM-CUST",
                "description": f"Supplies for {discrepancy_type}",
                "quantity": invoice_qty,
                "unit_price": unit_price,
                "total": amount
            }],
            "bank_account": bank_account,
            "notes": f"Simulated billing for {discrepancy_type}"
        }

        po_data = {
            "po_id": po_id,
            "vendor_id": vendor_id,
            "vendor_name": vendor_name,
            "po_date": invoice_date,
            "currency": "INR",
            "total_amount": po_amount,
            "line_items": [{
                "item_id": "ITM-CUST",
                "description": f"Supplies for {discrepancy_type}",
                "ordered_quantity": invoice_qty,
                "unit_price": po_amount / invoice_qty if invoice_qty > 0 else unit_price,
                "total": po_amount
            }],
            "status": "APPROVED",
            "approved_by": "Simulation Manager"
        }

        rec_data = {
            "receipt_id": f"REC-{invoice_id}",
            "po_id": po_id,
            "received_date": invoice_date,
            "received_by": "Warehouse Main Bay",
            "line_items": [{
                "item_id": "ITM-CUST",
                "description": f"Supplies for {discrepancy_type}",
                "received_quantity": receipt_qty,
                "accepted_quantity": receipt_qty,
                "rejected_quantity": 0
            }],
            "status": "FULL_DELIVERY" if receipt_qty >= invoice_qty else "PARTIAL_DELIVERY"
        }

        bank_update_date = "2026-09-27" if is_recent_bank_update else "2024-01-15"
        vendor_data = {
            "vendor_id": vendor_id,
            "vendor_name": vendor_name,
            "contract_id": f"CTR-{vendor_id}",
            "bank_account": bank_account,
            "banking_details_updated_at": bank_update_date,
            "risk_rating": "HIGH" if is_recent_bank_update else "MEDIUM",
            "status": "ACTIVE",
            "total_invoices_processed": 5
        }

        case_data = {
            "case_id": f"VX-SIM-{invoice_id}",
            "invoice_id": invoice_id,
            "vendor_id": vendor_id,
            "vendor_name": vendor_name,
            "amount": amount,
            "discrepancy_type": discrepancy_type,
            "status": "UNPROCESSED",
            "risk_level": "High" if is_recent_bank_update or "Mismatch" in discrepancy_type else "Medium",
            "last_action": "Simulated invoice received",
            "created_at": now_str,
            "updated_at": now_str
        }

        for fname, data_obj, key_name in [
            ("invoices.json", inv_data, "invoice_id"),
            ("purchase_orders.json", po_data, "po_id"),
            ("receipts.json", rec_data, "receipt_id"),
            ("vendors.json", vendor_data, "vendor_id"),
            ("cases.json", case_data, "case_id")
        ]:
            existing = self._load_data(fname)
            updated = False
            for idx, item in enumerate(existing):
                if item.get(key_name) == data_obj.get(key_name):
                    existing[idx] = data_obj
                    updated = True
                    break
            if not updated:
                existing.insert(0, data_obj)
            self._save_data(fname, existing)

        return case_data

    def get_data_mode(self) -> str:
        return "Local mode"


def get_business_repository() -> AbstractBusinessRepository:
    """
    Selects the active BusinessRepository implementation based on configuration & availability.
    Behavior:
    - If valid Supabase configuration exists and connection succeeds -> Supabase Business Repository ("Supabase")
    - If credentials missing or Supabase unreachable -> Local JSON Business Repository ("Local mode")
    """
    local_repo = LocalJsonBusinessRepository()
    if is_supabase_available():
        return SupabaseBusinessRepository(fallback_repo=local_repo)
    return local_repo
