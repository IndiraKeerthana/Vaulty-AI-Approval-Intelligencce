-- Vaulty Supabase Database Schema
-- Supports operational AP tables, case events, and approval events.

-- 1. Vendors Table
CREATE TABLE IF NOT EXISTS vendors (
    vendor_id TEXT PRIMARY KEY,
    vendor_name TEXT NOT NULL,
    contract_id TEXT,
    bank_account TEXT,
    banking_details_updated_at TEXT,
    risk_rating TEXT DEFAULT 'MEDIUM',
    status TEXT DEFAULT 'ACTIVE',
    total_invoices_processed INT DEFAULT 0
);
ALTER TABLE vendors ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Permissive policy for vendors" ON vendors FOR ALL USING (true);

-- 2. Purchase Orders Table
CREATE TABLE IF NOT EXISTS purchase_orders (
    po_id TEXT PRIMARY KEY,
    vendor_id TEXT REFERENCES vendors(vendor_id),
    vendor_name TEXT,
    po_date TEXT,
    currency TEXT DEFAULT 'INR',
    total_amount NUMERIC(15, 2),
    line_items JSONB DEFAULT '[]'::jsonb,
    status TEXT DEFAULT 'APPROVED',
    approved_by TEXT
);
ALTER TABLE purchase_orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Permissive policy for purchase_orders" ON purchase_orders FOR ALL USING (true);

-- 3. Invoices Table
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id TEXT PRIMARY KEY,
    vendor_id TEXT REFERENCES vendors(vendor_id),
    vendor_name TEXT,
    po_id TEXT,
    invoice_date TEXT,
    currency TEXT DEFAULT 'INR',
    total_amount NUMERIC(15, 2),
    line_items JSONB DEFAULT '[]'::jsonb,
    bank_account TEXT,
    notes TEXT
);
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Permissive policy for invoices" ON invoices FOR ALL USING (true);

-- 4. Receipts Table
CREATE TABLE IF NOT EXISTS receipts (
    receipt_id TEXT PRIMARY KEY,
    po_id TEXT,
    received_date TEXT,
    received_by TEXT,
    line_items JSONB DEFAULT '[]'::jsonb,
    status TEXT
);
ALTER TABLE receipts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Permissive policy for receipts" ON receipts FOR ALL USING (true);

-- 5. Contracts Table
CREATE TABLE IF NOT EXISTS contracts (
    contract_id TEXT PRIMARY KEY,
    vendor_id TEXT REFERENCES vendors(vendor_id),
    title TEXT,
    start_date TEXT,
    end_date TEXT,
    standard_rate NUMERIC(15, 2),
    payment_terms TEXT,
    price_adjustment_clause TEXT
);
ALTER TABLE contracts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Permissive policy for contracts" ON contracts FOR ALL USING (true);

-- 6. Amendments Table
CREATE TABLE IF NOT EXISTS amendments (
    amendment_id TEXT PRIMARY KEY,
    vendor_id TEXT REFERENCES vendors(vendor_id),
    po_id TEXT,
    effective_date TEXT,
    original_unit_price NUMERIC(15, 2),
    amended_unit_price NUMERIC(15, 2),
    reason TEXT,
    approved_by TEXT,
    status TEXT DEFAULT 'APPROVED',
    doc_ref TEXT
);
ALTER TABLE amendments ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Permissive policy for amendments" ON amendments FOR ALL USING (true);

-- 7. Cases Table
CREATE TABLE IF NOT EXISTS cases (
    case_id TEXT PRIMARY KEY,
    invoice_id TEXT,
    vendor_id TEXT,
    vendor_name TEXT,
    amount NUMERIC(15, 2),
    discrepancy_type TEXT,
    status TEXT DEFAULT 'UNPROCESSED',
    risk_level TEXT DEFAULT 'Medium',
    last_action TEXT,
    created_at TEXT,
    updated_at TEXT
);
ALTER TABLE cases ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Permissive policy for cases" ON cases FOR ALL USING (true);

-- 8. Case Events Table
CREATE TABLE IF NOT EXISTS case_events (
    event_id SERIAL PRIMARY KEY,
    case_id TEXT REFERENCES cases(case_id),
    timestamp TEXT,
    date TEXT,
    agent TEXT,
    action TEXT,
    details JSONB DEFAULT '{}'::jsonb
);
ALTER TABLE case_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Permissive policy for case_events" ON case_events FOR ALL USING (true);

-- 9. Approval Events Table
CREATE TABLE IF NOT EXISTS approval_events (
    approval_id SERIAL PRIMARY KEY,
    case_id TEXT REFERENCES cases(case_id),
    invoice_id TEXT,
    vendor_id TEXT,
    event_type TEXT,
    previous_status TEXT,
    new_status TEXT,
    amount NUMERIC(15, 2),
    actor TEXT,
    reason TEXT,
    created_at TEXT
);
ALTER TABLE approval_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Permissive policy for approval_events" ON approval_events FOR ALL USING (true);
