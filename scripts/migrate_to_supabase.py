import os
import json
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import DATA_DIR
from utils.supabase_client import get_supabase_client

TABLE_MAPPINGS = [
    ("vendors.json", "vendors", "vendor_id"),
    ("contracts.json", "contracts", "contract_id"),
    ("purchase_orders.json", "purchase_orders", "po_id"),
    ("invoices.json", "invoices", "invoice_id"),
    ("receipts.json", "receipts", "receipt_id"),
    ("amendments.json", "amendments", "amendment_id"),
    ("cases.json", "cases", "case_id"),
    ("audit_log.json", "case_events", None),
]

def migrate():
    print("==================================================")
    print("VAULTY SUPABASE ONE-TIME IDEMPOTENT MIGRATION")
    print("==================================================")

    client = get_supabase_client()
    if not client:
        print("[ERROR] Could not connect to Supabase. Check SUPABASE_URL and SUPABASE_ANON_KEY/SERVICE_ROLE_KEY in .env")
        return

    print("Connected to Supabase successfully. Starting migration...\n")

    for json_file, table_name, pk_col in TABLE_MAPPINGS:
        file_path = os.path.join(DATA_DIR, json_file)
        if not os.path.exists(file_path):
            print(f"[SKIP] File {json_file} not found.")
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            records = json.load(f)

        if not records:
            print(f"[SKIP] {json_file} is empty.")
            continue

        print(f"Migrating {len(records)} rows from {json_file} into '{table_name}' table...")

        try:
            if pk_col:
                client.table(table_name).upsert(records, on_conflict=pk_col).execute()
            else:
                client.table(table_name).insert(records).execute()
            print(f"  ✓ Successfully migrated {len(records)} rows into '{table_name}'.")
        except Exception as e:
            print(f"  ✗ [ERROR] Failed to migrate table '{table_name}': {e}")

    print("\n==================================================")
    print("MIGRATION COMPLETE!")
    print("Note: data/lessons.json was intentionally NOT migrated.")
    print("Hindsight memory layer remains separate from business data.")
    print("==================================================")

if __name__ == "__main__":
    migrate()
