import logging
import datetime
from utils.supabase_client import get_supabase_client, is_supabase_available

logger = logging.getLogger("VAULTY.SupabaseRepository")

class SupabaseBusinessRepository:
    """
    Supabase operational system-of-record implementation.
    Reads/writes vendors, invoices, purchase_orders, receipts, contracts,
    amendments, cases, case_events, approval_events from Supabase.
    """

    def __init__(self, fallback_repo=None):
        self.fallback = fallback_repo

    def _get_client(self):
        client = get_supabase_client()
        if client and is_supabase_available():
            return client
        return None

    def get_all_cases(self) -> list:
        client = self._get_client()
        if client:
            try:
                res = client.table("cases").select("*").execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase get_all_cases failed: {e}. Using fallback.")
        return self.fallback.get_all_cases() if self.fallback else []

    def get_all_vendors(self) -> list:
        client = self._get_client()
        if client:
            try:
                res = client.table("vendors").select("*").execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase get_all_vendors failed: {e}. Using fallback.")
        return self.fallback.get_all_vendors() if self.fallback else []

    def get_all_invoices(self) -> list:
        client = self._get_client()
        if client:
            try:
                res = client.table("invoices").select("*").execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase get_all_invoices failed: {e}. Using fallback.")
        return self.fallback.get_all_invoices() if self.fallback else []

    def get_all_purchase_orders(self) -> list:
        client = self._get_client()
        if client:
            try:
                res = client.table("purchase_orders").select("*").execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase get_all_purchase_orders failed: {e}. Using fallback.")
        return self.fallback.get_all_purchase_orders() if self.fallback else []

    def get_case(self, case_id: str) -> dict:
        client = self._get_client()
        if client:
            try:
                res = client.table("cases").select("*").eq("case_id", case_id).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"Supabase get_case failed: {e}. Using fallback.")
        return self.fallback.get_case(case_id) if self.fallback else {"error": f"Case {case_id} not found"}

    def get_cases_by_status(self, status: str) -> list:
        client = self._get_client()
        if client:
            try:
                res = client.table("cases").select("*").eq("status", status).execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase get_cases_by_status failed: {e}")
        return [c for c in self.get_all_cases() if c.get("status") == status]

    def get_cases_by_vendor(self, vendor_id: str) -> list:
        client = self._get_client()
        if client:
            try:
                res = client.table("cases").select("*").eq("vendor_id", vendor_id).execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase get_cases_by_vendor failed: {e}")
        return [c for c in self.get_all_cases() if c.get("vendor_id") == vendor_id]

    def get_cases_by_discrepancy_type(self, discrepancy_type: str) -> list:
        client = self._get_client()
        if client:
            try:
                res = client.table("cases").select("*").eq("discrepancy_type", discrepancy_type).execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase get_cases_by_discrepancy_type failed: {e}")
        return [c for c in self.get_all_cases() if c.get("discrepancy_type") == discrepancy_type]

    def get_invoice(self, invoice_id: str) -> dict:
        client = self._get_client()
        if client:
            try:
                res = client.table("invoices").select("*").eq("invoice_id", invoice_id).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"Supabase get_invoice failed: {e}. Using fallback.")
        return self.fallback.get_invoice(invoice_id) if self.fallback else {"error": f"Invoice {invoice_id} not found"}

    def get_vendor(self, vendor_id: str) -> dict:
        client = self._get_client()
        if client:
            try:
                res = client.table("vendors").select("*").eq("vendor_id", vendor_id).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"Supabase get_vendor failed: {e}. Using fallback.")
        return self.fallback.get_vendor(vendor_id) if self.fallback else {"error": f"Vendor {vendor_id} not found"}

    def get_purchase_order(self, po_id: str) -> dict:
        client = self._get_client()
        if client:
            try:
                res = client.table("purchase_orders").select("*").eq("po_id", po_id).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"Supabase get_purchase_order failed: {e}. Using fallback.")
        return self.fallback.get_purchase_order(po_id) if self.fallback else {"error": f"PO {po_id} not found"}

    def get_receipt(self, po_id: str) -> dict:
        client = self._get_client()
        if client:
            try:
                res = client.table("receipts").select("*").eq("po_id", po_id).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"Supabase get_receipt failed: {e}. Using fallback.")
        return self.fallback.get_receipt(po_id) if self.fallback else {"error": f"Receipt {po_id} not found"}

    def get_contract(self, vendor_id: str) -> dict:
        client = self._get_client()
        if client:
            try:
                res = client.table("contracts").select("*").eq("vendor_id", vendor_id).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"Supabase get_contract failed: {e}. Using fallback.")
        return self.fallback.get_contract(vendor_id) if self.fallback else {"error": f"Contract for {vendor_id} not found"}

    def get_amendments(self, vendor_id: str) -> list:
        client = self._get_client()
        if client:
            try:
                res = client.table("amendments").select("*").eq("vendor_id", vendor_id).execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase get_amendments failed: {e}. Using fallback.")
        return self.fallback.get_amendments(vendor_id) if self.fallback else []

    def get_vendor_history(self, vendor_id: str) -> dict:
        return self.get_vendor(vendor_id)

    def get_case_events(self, case_id: str) -> list:
        client = self._get_client()
        if client:
            try:
                res = client.table("case_events").select("*").eq("case_id", case_id).order("timestamp", desc=True).execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"Supabase get_case_events failed: {e}")
        return self.fallback.get_case_events(case_id) if self.fallback else []

    def get_audit_logs(self, case_id: str = None) -> list:
        return self.get_case_events(case_id)

    def update_case(self, case_id: str, status: str, notes: str) -> dict:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        client = self._get_client()
        if client:
            try:
                client.table("cases").update({
                    "status": status,
                    "last_action": notes,
                    "updated_at": now_str
                }).eq("case_id", case_id).execute()
            except Exception as e:
                logger.warning(f"Supabase update_case failed: {e}")
        return self.fallback.update_case(case_id, status, notes) if self.fallback else {"case_id": case_id, "status": status, "last_action": notes}

    def update_approval_status(self, case_id: str, approval_status: str, notes: str, actor: str = "Finance Manager") -> dict:
        return self.update_case(case_id, approval_status, notes)

    def create_case_event(self, case_id: str, agent: str, action: str, details: dict) -> dict:
        client = self._get_client()
        event_data = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "case_id": case_id,
            "agent": agent,
            "action": action,
            "details": details
        }
        if client:
            try:
                client.table("case_events").insert([event_data]).execute()
            except Exception as e:
                logger.warning(f"Supabase create_case_event failed: {e}")
        return self.fallback.create_case_event(case_id, agent, action, details) if self.fallback else event_data

    def create_simulated_case(self, **kwargs) -> dict:
        client = self._get_client()
        if client:
            try:
                inv_data = {
                    "invoice_id": kwargs["invoice_id"],
                    "vendor_id": kwargs["vendor_id"],
                    "vendor_name": kwargs["vendor_name"],
                    "po_id": kwargs["po_id"],
                    "invoice_date": kwargs["invoice_date"],
                    "currency": "INR",
                    "total_amount": kwargs["amount"],
                    "bank_account": kwargs["bank_account"]
                }
                client.table("invoices").upsert([inv_data], on_conflict="invoice_id").execute()
            except Exception as e:
                logger.warning(f"Supabase create_simulated_case failed: {e}")
        return self.fallback.create_simulated_case(**kwargs) if self.fallback else {}

    def get_data_mode(self) -> str:
        client = self._get_client()
        return "Supabase" if client else "Local mode"
