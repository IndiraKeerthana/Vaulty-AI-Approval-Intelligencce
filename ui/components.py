import streamlit as st

def format_label(key: str) -> str:
    """Converts database keys to clean Title Case business labels."""
    mapping = {
        "po_id": "Purchase Order",
        "vendor_id": "Supplier Code",
        "contract_id": "Contract Ref",
        "invoice_id": "Invoice ID",
        "receipt_id": "Goods Receipt",
        "po_date": "PO Date",
        "invoice_date": "Invoice Date",
        "received_date": "Delivery Date",
        "start_date": "Effective Start",
        "end_date": "Effective End",
        "standard_rate": "Standard Unit Rate",
        "payment_terms": "Payment Terms",
        "price_adjustment_clause": "Price Adjustment Terms",
        "bank_account": "Payment Account",
        "banking_details_updated_at": "Bank Details Updated",
        "risk_rating": "Risk Rating",
        "total_amount": "Total Value",
        "approved_by": "Approved By",
        "received_by": "Received By",
        "doc_ref": "Document Reference",
        "amended_unit_price": "Amended Rate",
        "original_unit_price": "Original Rate",
        "effective_date": "Amendment Date"
    }
    if key in mapping:
        return mapping[key]
    return key.replace("_", " ").title()


def mask_bank_account(acc: str) -> str:
    """Masks raw banking numbers for security."""
    if not acc or acc == "N/A":
        return "Not available"
    acc_str = str(acc)
    if len(acc_str) > 4:
        return f"•••• {acc_str[-4:]}"
    return acc_str


def render_sidebar_header(data_mode: str, memory_mode: str):
    """Clean enterprise sidebar header with quiet system status badges."""
    data_text = "Connected (Supabase)" if data_mode == "Supabase" else "Local mode"
    mem_text = "Connected (Hindsight)" if memory_mode == "Hindsight" else "Local mode"

    data_class = "status-value-connected" if data_mode == "Supabase" else "status-value-local"
    mem_class = "status-value-connected" if memory_mode == "Hindsight" else "status-value-local"

    html = f"""
    <div class="sidebar-brand">
        <div class="brand-title-text">
            <span class="brand-logo-badge">V</span> VAULTY
        </div>
        <div class="brand-subtitle">AI Exception Intelligence</div>
        <div class="brand-tagline">Investigate. Resolve. Remember.</div>
        <div class="system-status-container">
            <div class="status-row">
                <span class="status-label">Data</span>
                <span class="{data_class}">{data_text}</span>
            </div>
            <div class="status-row">
                <span class="status-label">Memory</span>
                <span class="{mem_class}">{mem_text}</span>
            </div>
        </div>
    </div>
    """
    st.sidebar.markdown(html, unsafe_allow_html=True)


def render_status_pill(status: str) -> str:
    """Renders compact, restrained status pills in plain business language."""
    if not status:
        return '<span class="status-pill status-pending">Pending</span>'

    s = str(status).upper()
    if "AWAITING_HUMAN" in s or "AWAITING PAYMENT" in s or "READY_FOR_APPROVAL" in s:
        label = "Ready for your approval"
        cls = "status-pending"
    elif "INVESTIGAT" in s or "CHECKING" in s or "UNPROCESSED" in s:
        label = "Being checked"
        cls = "status-investigating"
    elif "VENDOR" in s or "PENDING VENDOR" in s:
        label = "Waiting on vendor"
        cls = "status-on-hold"
    elif "PROCUREMENT" in s or "HOLD" in s or "ESCALAT" in s:
        label = "On hold"
        cls = "status-on-hold"
    elif "FRAUD" in s or "CRITICAL" in s or "URGENT" in s:
        label = "Needs urgent review"
        cls = "status-fraud"
    elif "RESOLVED" in s or "APPROVED" in s or "CLOSED" in s:
        label = "Resolved"
        cls = "status-clear"
    elif "CORRECTION" in s or "SENT_BACK" in s:
        label = "Correction requested"
        cls = "status-on-hold"
    else:
        label = status.replace("_", " ").title()
        cls = "status-pending"

    return f'<span class="status-pill {cls}">{label}</span>'


def render_stat_tile(title: str, value: str, subtitle: str = "", color: str = "#2563eb"):
    """Renders top executive summary card."""
    html = f"""
    <div class="vaulty-metric-card" style="border-top: 3px solid {color};">
        <div>
            <div class="vaulty-metric-label">{title}</div>
            <div class="vaulty-metric-value">{value}</div>
        </div>
        <div class="vaulty-metric-sub">{subtitle}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_formatted_card(data: dict, title: str = None):
    """Renders structured business objects as clean key-value cards."""
    if not isinstance(data, dict) or not data or "error" in data:
        st.info(f"{title or 'Record'} not available.")
        return

    if title:
        st.markdown(f"#### {title}")

    hidden_keys = {"vendor_id", "contract_id", "confidence_score", "lesson_id", "source_case_id", "human_feedback_type", "error"}
    line_items = data.get("line_items", [])
    main_fields = {k: v for k, v in data.items() if k != "line_items" and k not in hidden_keys}

    grid_items_html = ""
    for k, v in main_fields.items():
        label = format_label(k)
        if v is None or v == "":
            val_str = '<span style="color:#94a3b8; font-style:italic;">Not available</span>'
        elif "bank_account" in k:
            val_str = mask_bank_account(v)
        elif isinstance(v, (int, float)) and ("amount" in k or "rate" in k or "price" in k or "total" in k):
            val_str = f"₹{v:,.2f}"
        else:
            val_str = str(v)

        grid_items_html += f"""
        <div class="data-item">
            <div class="data-label">{label}</div>
            <div class="data-value">{val_str}</div>
        </div>
        """

    st.markdown(f'<div class="data-grid-two-col">{grid_items_html}</div>', unsafe_allow_html=True)

    if line_items and isinstance(line_items, list):
        st.markdown("**Line Items**")
        table_rows = ""
        keys = list(line_items[0].keys()) if line_items and isinstance(line_items[0], dict) else []
        headers_html = "".join([f"<th>{format_label(k)}</th>" for k in keys if k not in hidden_keys])

        for item in line_items:
            if isinstance(item, dict):
                row_cells = ""
                for k in keys:
                    if k in hidden_keys:
                        continue
                    v = item.get(k)
                    if v is None or v == "":
                        cell_str = '<span style="color:#94a3b8; font-style:italic;">Not available</span>'
                    elif isinstance(v, (int, float)) and ("price" in k or "total" in k):
                        cell_str = f"₹{v:,.2f}"
                    else:
                        cell_str = str(v)
                    row_cells += f"<td>{cell_str}</td>"
                table_rows += f"<tr>{row_cells}</tr>"

        table_html = f"""
        <table class="formatted-table">
            <thead><tr>{headers_html}</tr></thead>
            <tbody>{table_rows}</tbody>
        </table>
        """
        st.markdown(table_html, unsafe_allow_html=True)


def render_evidence_comparison_table(inv: dict, po: dict, rec: dict = None, contract: dict = None):
    """
    Renders Section 1 Current Evidence side-by-side comparison table.
    Shows PO vs Invoice vs Delivery vs Contract terms cleanly.
    Enforces the financial rule: never display ₹0.00 for missing fields.
    """
    po_available = isinstance(po, dict) and "error" not in po and po
    inv_available = isinstance(inv, dict) and "error" not in inv and inv
    rec_available = isinstance(rec, dict) and "error" not in rec and rec
    contract_available = isinstance(contract, dict) and "error" not in contract and contract

    inv_amt = inv.get("total_amount") if inv_available else None
    po_amt = po.get("total_amount") if po_available else None

    inv_items = inv.get("line_items", [{}]) if inv_available else [{}]
    po_items = po.get("line_items", [{}]) if po_available else [{}]
    rec_items = rec.get("line_items", [{}]) if rec_available else [{}]

    inv_qty = inv_items[0].get("quantity") if inv_items else None
    po_qty = (po_items[0].get("ordered_quantity") or po_items[0].get("quantity")) if po_items else None
    rec_qty = rec_items[0].get("received_quantity") if rec_items else None

    inv_price = inv_items[0].get("unit_price") if inv_items else None
    po_price = po_items[0].get("unit_price") if po_items else None
    std_rate = contract.get("standard_rate") if contract_available else None

    def fmt_cell(val, is_curr=False, missing_msg="Not available"):
        if val is None or val == "" or val == "error":
            return f'<span style="color:#94a3b8; font-style:italic;">{missing_msg}</span>'
        if is_curr and isinstance(val, (int, float)):
            return f"₹{val:,.2f}"
        return str(val)

    po_amt_cell = fmt_cell(po_amt, is_curr=True, missing_msg="Purchase order not available")
    po_qty_cell = fmt_cell(po_qty, missing_msg="Purchase order not available")
    po_price_cell = fmt_cell(po_price, is_curr=True, missing_msg="Purchase order not available")
    po_terms_cell = fmt_cell(po.get('payment_terms') if po_available else None, missing_msg="Purchase order not available")

    html = f"""
    <table class="formatted-table" style="margin-top:12px;">
        <thead>
            <tr>
                <th style="width: 25%;">Field</th>
                <th style="width: 25%;">Purchase Order</th>
                <th style="width: 25%;">Invoice</th>
                <th style="width: 25%;">Delivery / Contract</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>Total Value</strong></td>
                <td>{po_amt_cell}</td>
                <td><strong>{fmt_cell(inv_amt, is_curr=True)}</strong></td>
                <td>-</td>
            </tr>
            <tr>
                <td><strong>Quantity</strong></td>
                <td>{po_qty_cell}</td>
                <td><strong>{fmt_cell(inv_qty)}</strong></td>
                <td>Receipt: {fmt_cell(rec_qty, missing_msg="Receipt not available")}</td>
            </tr>
            <tr>
                <td><strong>Unit Price / Rate</strong></td>
                <td>{po_price_cell}</td>
                <td><strong>{fmt_cell(inv_price, is_curr=True)}</strong></td>
                <td>Contract Rate: {fmt_cell(std_rate, is_curr=True, missing_msg="Contract not available")}</td>
            </tr>
            <tr>
                <td><strong>Payment Terms</strong></td>
                <td>{po_terms_cell}</td>
                <td>{fmt_cell(inv.get('payment_terms') if inv_available else None)}</td>
                <td>Contract Terms: {fmt_cell(contract.get('payment_terms') if contract_available else None, missing_msg="Contract not available")}</td>
            </tr>
        </tbody>
    </table>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_verification_path():
    """Renders visual verification sequence."""
    html = """
    <div class="verification-path-container">
        <div class="verification-step"><span class="verification-step-icon">✓</span> Invoice Received</div>
        <span class="verification-arrow">→</span>
        <div class="verification-step"><span class="verification-step-icon">✓</span> Purchase Order</div>
        <span class="verification-arrow">→</span>
        <div class="verification-step"><span class="verification-step-icon">✓</span> Goods Delivery</div>
        <span class="verification-arrow">→</span>
        <div class="verification-step"><span class="verification-step-icon">✓</span> Contract Terms</div>
        <span class="verification-arrow">→</span>
        <div class="verification-step"><span class="verification-step-icon">✓</span> Past Experience</div>
        <span class="verification-arrow">→</span>
        <div class="verification-step"><span class="verification-step-icon">✓</span> Final Verification</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_signature_memory_panel(analysis: dict, memory_influence: dict = None, human_outcome: str = None):
    """
    SECTION 3 — VAULTY REMEMBERED (SIGNATURE MEMORY PANEL)
    Dedicated Vaulty violet accent treatment (#7c3aed).
    Communicates memory is EXPERIENCE, not proof.
    Displays:
    - Past experience
    - Current evidence
    - Memory verdict (✓ CONFIRMED, ⚠ CONTRADICTED BY CURRENT EVIDENCE, — INSUFFICIENT)
    - WHY (explanation)
    - ADAPTED DECISION
    - If CONTRADICTED: "Evidence overrides memory."
    - Visible Learning Loop: RECALLED → VERIFIED → LEARNED
    """
    data = memory_influence or analysis or {}
    if not data or not isinstance(data, dict) or not any(data.values()):
        html = (
            '<div class="vaulty-signature-memory-panel">'
            '<div class="memory-header-title">'
            '<span>VAULTY REMEMBERED</span>'
            '<span class="memory-verdict-tag verdict-new">— INSUFFICIENT</span>'
            '</div>'
            '<div style="margin-top: 6px; font-size: 11.5px; font-weight: 700; color: #6d28d9; letter-spacing: 0.02em;">'
            'Memory status: RECALLED: No prior experience → Human approves → LEARNED'
            '</div>'
            '<div style="margin-top: 10px; font-size: 13.5px; color: #475569;">'
            'No relevant past experience found. Investigation is decided solely on primary records.'
            '</div>'
            '</div>'
        )
        st.markdown(html, unsafe_allow_html=True)
        return

    verdict_raw = str(data.get("status") or data.get("confirmation_or_contradiction") or "INSUFFICIENT").upper()

    if "CONTRADICT" in verdict_raw:
        verdict_tag = '<span class="memory-verdict-tag verdict-mismatch">⚠ CONTRADICTED BY CURRENT EVIDENCE</span>'
        verdict_key = "CONTRADICTED"
    elif "CONFIRM" in verdict_raw:
        verdict_tag = '<span class="memory-verdict-tag verdict-match">✓ CONFIRMED</span>'
        verdict_key = "CONFIRMED"
    else:
        verdict_tag = '<span class="memory-verdict-tag verdict-new">— INSUFFICIENT</span>'
        verdict_key = "INSUFFICIENT"

    past_exp = data.get("past_experience") or data.get("memory_recalled") or "No prior exception resolutions found."
    curr_evid = data.get("current_evidence") or "Verified current invoice line items against PO, Delivery Receipt, and Contract Amendment log."
    why_reason = data.get("reason") or data.get("memory_explanation") or "Current evidence checked against recalled patterns."
    adapted_decision = data.get("adapted_decision") or data.get("final_adaptation") or "Proceeding based on verified current evidence."

    # Construct dynamic visible learning loop status indicator
    if verdict_key == "CONFIRMED":
        if human_outcome == "APPROVED":
            loop_text = "RECALLED: Relevant prior resolution retrieved → Current amendment verified → MEMORY CONFIRMED → Human approved → LEARNED"
        else:
            loop_text = "RECALLED: Relevant prior resolution retrieved → Current amendment verified → MEMORY CONFIRMED"
    elif verdict_key == "CONTRADICTED":
        if human_outcome in ("CORRECTED", "ON_HOLD", "HELD"):
            loop_text = "RECALLED: Prior resolution retrieved → Current evidence conflicts → MEMORY CONTRADICTED → EVIDENCE OVERRIDES MEMORY → Human held → LEARNED"
        else:
            loop_text = "RECALLED: Prior resolution retrieved → Current evidence conflicts → MEMORY CONTRADICTED → EVIDENCE OVERRIDES MEMORY"
    else:
        if human_outcome:
            loop_text = f"RECALLED: No prior experience → Primary evidence decided → Human decision ({human_outcome}) → LEARNED"
        else:
            loop_text = "RECALLED: No relevant prior experience → Primary evidence decides → LEARNED UPON DECISION"

    override_banner = ""
    if verdict_key == "CONTRADICTED":
        override_banner = (
            '<div style="margin-top: 14px; padding: 12px 16px; background: #fef2f2; '
            'border: 1px solid #fecaca; border-left: 4px solid #dc2626; border-radius: 6px; '
            'color: #991b1b; font-weight: 800; font-size: 13.5px; display: flex; align-items: center; gap: 8px;">'
            '<span style="font-size: 16px;">⚠</span>'
            '<span>Evidence overrides memory.</span>'
            '</div>'
        )

    html = (
        f'<div class="vaulty-signature-memory-panel">'
        f'<div class="memory-header-title">'
        f'<span>VAULTY REMEMBERED</span>'
        f'{verdict_tag}'
        f'</div>'
        f'<div style="margin-top: 6px; font-size: 11.5px; font-weight: 700; color: #6d28d9; letter-spacing: 0.02em;">'
        f'Memory status: {loop_text}'
        f'</div>'
        f'<div class="memory-stage-grid">'
        f'<div class="memory-stage-box">'
        f'<div class="memory-stage-title">Past Experience</div>'
        f'<div class="memory-stage-content">{past_exp}</div>'
        f'</div>'
        f'<div class="memory-stage-box">'
        f'<div class="memory-stage-title">Current Evidence</div>'
        f'<div class="memory-stage-content">{curr_evid}</div>'
        f'</div>'
        f'<div class="memory-stage-box" style="background: #fdf4ff; border-color: #f0abfc;">'
        f'<div class="memory-stage-title" style="color: #86198f;">Why</div>'
        f'<div class="memory-stage-content" style="color: #701a75;">{why_reason}</div>'
        f'</div>'
        f'</div>'
        f'<div style="margin-top: 12px; background: #ffffff; border: 1px solid #ddd6fe; border-radius: 6px; padding: 12px 14px;">'
        f'<div style="font-size: 11px; font-weight: 700; color: #6d28d9; text-transform: uppercase;">Adapted Decision</div>'
        f'<div style="font-size: 13.5px; color: #334155; margin-top: 4px; font-weight: 600;">{adapted_decision}</div>'
        f'</div>'
        f'{override_banner}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_error_card(message: str, title: str = "Vaulty couldn't complete this check"):
    """Clean business error display without raw tracebacks."""
    html = f"""
    <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
        <div style="font-size: 14px; font-weight: 700; color: #991b1b;">{title}</div>
        <div style="font-size: 13px; color: #7f1d1d; margin-top: 4px;">
            {message}<br/>
            <strong>Your invoice records have not been changed.</strong>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_empty_state(message: str, title: str = "No records found"):
    """Polished empty state card."""
    html = f"""
    <div class="empty-state-card">
        <div class="empty-state-title">{title}</div>
        <div class="empty-state-body">{message}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
