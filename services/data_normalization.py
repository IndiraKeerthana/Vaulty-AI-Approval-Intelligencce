def normalize_discrepancy_type(raw_type: str) -> str:
    """
    Normalizes raw discrepancy string into a canonical business category.
    """
    if not raw_type or "none" in raw_type.lower() or "matching" in raw_type.lower() or "clean" in raw_type.lower():
        return "Matching Consistency (Clean)"
    
    t = raw_type.lower()
    if "bank" in t or "fraud" in t or "anomaly" in t:
        return "Potential Fraud Signal"
    elif "duplicate" in t:
        return "Duplicate Invoice"
    elif "price" in t or "rate" in t:
        return "Price Mismatch"
    elif "quantity" in t or "partial" in t or "receipt" in t:
        return "Quantity Mismatch"
    elif "missing" in t or "no po" in t or "lacks" in t or "purchase order" in t:
        return "Missing Purchase Order"
    return "Other Discrepancy"


def calculate_difference(invoice: dict, po: dict, receipt: dict = None, contract: dict = None) -> float:
    """
    Calculates the actual positive monetary overbilling discrepancy.
    DOES NOT simply sum invoice totals.
    Calculates exact difference between Invoiced amount vs PO/Contract expected amount.
    """
    if not invoice or "total_amount" not in invoice:
        return 0.0

    inv_amount = float(invoice.get("total_amount", 0.0))
    po_amount = float(po.get("total_amount", 0.0)) if isinstance(po, dict) and "total_amount" in po else 0.0

    # 1. Price mismatch calculation
    if po_amount > 0 and inv_amount > po_amount:
        return round(inv_amount - po_amount, 2)

    # 2. Line item level unit price difference
    inv_items = invoice.get("line_items", [])
    po_items = po.get("line_items", []) if isinstance(po, dict) else []

    if inv_items and po_items:
        inv_unit_price = inv_items[0].get("unit_price", 0.0)
        po_unit_price = po_items[0].get("unit_price", 0.0)
        inv_qty = inv_items[0].get("quantity", 1)

        if inv_unit_price > po_unit_price:
            return round((inv_unit_price - po_unit_price) * inv_qty, 2)

    # 3. Quantity / Partial Delivery mismatch calculation
    if isinstance(receipt, dict) and "line_items" in receipt and receipt.get("status") == "PARTIAL_DELIVERY":
        rec_items = receipt.get("line_items", [])
        if rec_items and inv_items:
            rec_qty = rec_items[0].get("received_quantity", 0)
            inv_qty = inv_items[0].get("quantity", 0)
            unit_price = inv_items[0].get("unit_price", 0.0)
            if inv_qty > rec_qty:
                return round((inv_qty - rec_qty) * unit_price, 2)

    return 0.0


def classify_approval_status(case: dict) -> str:
    """
    Classifies a case into canonical approval status.
    """
    status = case.get("status", "UNPROCESSED")
    discrepancy = normalize_discrepancy_type(case.get("discrepancy_type", ""))

    if status == "RESOLVED":
        if discrepancy == "Matching Consistency (Clean)":
            return "Seamless / No Approval Required"
        return "Payment Approved"
    elif status == "AWAITING_HUMAN_PAYMENT_RELEASE":
        return "Needs Approval"
    elif status == "UNPROCESSED" and discrepancy != "Matching Consistency (Clean)":
        return "Needs Investigation"
    elif status == "PENDING VENDOR RESPONSE":
        return "Vendor Query Sent"
    elif status == "CORRECTION REQUESTED":
        return "Correction Requested"
    elif status == "FRAUD REVIEW":
        return "Fraud Review"
    elif status == "ESCALATED TO PROCUREMENT":
        return "On Hold / Escalated"

    return "Needs Investigation"
