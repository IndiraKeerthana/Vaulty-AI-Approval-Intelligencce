import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from repositories.business_repository import get_business_repository
from repositories.memory_repository import get_memory_repository
from services.analytics_service import get_analytics_service
from services.data_normalization import (
    normalize_discrepancy_type,
    calculate_difference,
    classify_approval_status
)
from agents.pipeline import InvestigationPipeline
from ui.components import (
    render_stat_tile,
    render_status_pill,
    render_formatted_card,
    render_evidence_comparison_table,
    render_verification_path,
    render_signature_memory_panel,
    render_error_card,
    render_empty_state,
    mask_bank_account
)

biz_repo = get_business_repository()
mem_repo = get_memory_repository()
analytics = get_analytics_service()
pipeline = InvestigationPipeline()


# --- TECHNICAL EVENT FILTERING & TRANSLATION HELPERS ---

def is_business_event(event: dict) -> bool:
    """Filters out internal technical log events from business UI."""
    if not isinstance(event, dict):
        return False
    act = str(event.get("action", "")).upper()
    agent = str(event.get("agent", "")).upper()

    # Strictly exclude technical stage execution logs
    if any(tech in act for tech in ("ORCHESTR", "TRIAGE", "REFLECT", "STAGE_", "MEMORY", "START_", "AGENT", "TOOL", "LLM", "PROMPT")):
        return False
    if any(tech in agent for tech in ("ORCHESTR", "TRIAGE", "REFLECT", "SYSTEM", "PIPELINE")):
        return False
    return True


def format_business_event_desc(event: dict) -> str:
    """Formats an audit event into plain business language."""
    act = str(event.get("action", "")).upper()
    cid = event.get("case_id", "Case")

    if "RESOLV" in act or "APPROVED" in act or "RELEASE" in act:
        return f"Payment approval recorded for case {cid}."
    elif "CORRECT" in act or "SENT_BACK" in act:
        return f"Correction requested for case {cid}."
    elif "QUERY" in act or "VENDOR" in act:
        return f"Vendor confirmation requested for case {cid}."
    elif "HOLD" in act or "PROCURE" in act or "ESCALAT" in act:
        return f"Invoice placed on hold ({cid})."
    elif "FRAUD" in act:
        return f"Case flagged for fraud review ({cid})."
    elif "PIPELINE" in act or "INVESTIGAT" in act:
        return f"Investigation completed for case {cid}."
    elif "CREATE" in act or "INGEST" in act:
        return f"Invoice received into operational queue ({cid})."

    clean_act = act.replace("APPROVAL_STATUS_", "").replace("_", " ").title()
    return f"{clean_act} recorded for case {cid}."


def format_clean_vendor_lesson(les: dict) -> dict:
    """Transforms raw memory strings into clean business-readable lessons."""
    raw_topic = les.get("topic") or "Supplier Experience"
    raw_lesson = les.get("lesson") or les.get("lesson_content") or ""

    clean_topic = raw_topic
    if "Lesson on" in clean_topic:
        if "Price" in clean_topic or "rate" in clean_topic.lower():
            clean_topic = "Price Adjustment Verification"
        elif "Quantity" in clean_topic or "Partial" in clean_topic.lower():
            clean_topic = "Partial Delivery Hold Terms"
        elif "Matching" in clean_topic or "Clean" in clean_topic.lower():
            clean_topic = "Line-Item Verification"
        else:
            clean_topic = "Supplier Exception Insight"

    clean_lesson = raw_lesson
    if "CONFIRMED RESOLUTION LESSON for" in clean_lesson:
        clean_lesson = clean_lesson.split(": ", 1)[-1]
        clean_lesson = clean_lesson.replace("confirmed that ", "").replace("Retain this evidence-checking pattern.", "")
    elif "HUMAN CORRECTION LESSON for" in clean_lesson:
        if "notes: '" in clean_lesson:
            notes = clean_lesson.split("notes: '")[1].split("'")[0]
            clean_lesson = f"Supervisor instruction: {notes} Physical goods receipts and approval must be confirmed prior to payment."
        else:
            clean_lesson = clean_lesson.split(":", 1)[-1].strip()

    clean_lesson = clean_lesson.replace("APPLY_AMENDMENT", "amendment application")
    clean_lesson = clean_lesson.replace("REQUEST_CORRECTION", "correction request")

    return {"topic": clean_topic, "lesson": clean_lesson}


# --- PLOTLY CHART HELPERS FOR REPORTS PAGE ---

def render_plotly_horizontal_bar(categories, values, title="", color="#2563eb", is_currency=False, height=240):
    """Renders clean, publication-grade horizontal bar charts without label truncation or rotation."""
    if not categories or not values or len(categories) == 0:
        render_empty_state("No chart data available.", "No Chart Data")
        return

    text_labels = [f"₹{v:,.0f}" if is_currency else str(v) for v in values]

    fig = go.Figure(go.Bar(
        x=values,
        y=categories,
        orientation='h',
        text=text_labels,
        textposition='auto',
        marker=dict(color=color, cornerradius=4),
        hovertemplate="%{y}: " + ("₹%{x:,.2f}" if is_currency else "%{x}") + "<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color="#0f172a", family="Plus Jakarta Sans, sans-serif")) if title else None,
        margin=dict(l=20, r=20, t=30 if title else 10, b=20),
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#0f172a"),
        xaxis=dict(showgrid=True, gridcolor="#f1f5f9", tickfont=dict(color="#64748b", size=11), zeroline=False),
        yaxis=dict(showgrid=False, tickfont=dict(color="#0f172a", size=12), autorange="reversed")
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


# --- PAGE 1: HOME ---

def render_home_page():
    # 1. Branding Header
    st.markdown("""
    <div style="margin-bottom: 14px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 26px; font-weight: 800; color: #0f172a; letter-spacing: 0.02em;">VAULTY</div>
            <span style="background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.05em;">AI Exception Intelligence</span>
        </div>
        <div style="font-size: 13px; font-style: italic; color: #64748b; margin-top: 2px;">Investigate. Resolve. Remember.</div>
    </div>
    """, unsafe_allow_html=True)

    metrics = analytics.get_home_metrics()

    # 2. Dynamic Contextual Headline (Calculated from Real Data)
    needing_app_cnt = metrics.get("cases_needing_approval_count", 0)
    needs_inv_cnt = metrics.get("needs_investigation_count", 0)

    if needing_app_cnt > 0:
        headline = f"You have {needing_app_cnt} invoice{'s' if needing_app_cnt > 1 else ''} waiting on your decision."
    elif needs_inv_cnt > 0:
        headline = f"You have {needs_inv_cnt} invoice exception{'s' if needs_inv_cnt > 1 else ''} being checked."
    else:
        headline = "You're all caught up."

    st.markdown(f'<div style="font-size: 15px; font-weight: 700; color: #0f172a; margin-bottom: 16px;">{headline}</div>', unsafe_allow_html=True)

    # 3. Clean Summary Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_stat_tile("Needs your approval", str(needing_app_cnt), "Awaiting payment signoff", "#d97706")
    with c2:
        render_stat_tile("Being checked", str(needs_inv_cnt), "Unresolved exceptions", "#2563eb")
    with c3:
        render_stat_tile("Resolved discrepancies", str(metrics.get("resolved_discrepancies_count", 0)), "Verified and closed", "#16a34a")
    with c4:
        extra_amt = metrics.get("extra_amount_identified", 0.0)
        render_stat_tile("Extra amount identified", f"₹{extra_amt:,.0f}", "Total monetary overbilling", "#7c3aed")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 4. Primary CTA: Start Investigation
    st.markdown("""
    <div class="vaulty-card" style="border-left: 4px solid #2563eb; margin-bottom: 18px; padding: 16px 20px;">
        <div style="font-size: 15px; font-weight: 800; color: #0f172a; margin-bottom: 2px;">+ Start investigation</div>
        <div style="font-size: 12.5px; color: #64748b; margin-bottom: 12px;">
            Enter an Invoice ID or Case ID to review evidence against purchase orders, receipts, contract terms, and organizational experience.
        </div>
    """, unsafe_allow_html=True)

    col_inp, col_run = st.columns([4, 1])
    with col_inp:
        inv_input = st.text_input("Invoice ID or Case ID", "", placeholder="e.g. INV-1001, INV-2001, or CASE-101", key="home_inv_input", label_visibility="collapsed")
    with col_run:
        if st.button("Start investigation", type="primary", use_container_width=True, key="home_start_inv"):
            if not inv_input:
                st.warning("Please enter an Invoice ID or Case ID.")
            else:
                target_case = biz_repo.get_case(inv_input.strip())
                target_inv = biz_repo.get_invoice(inv_input.strip()) if "error" in target_case else target_case

                if "error" in target_case and "error" in target_inv:
                    render_error_card(f"Invoice or Case ID '{inv_input}' was not found in operational records.", title="Record Not Found")
                else:
                    target_cid = target_case.get("case_id", f"VX-{inv_input}") if "error" not in target_case else f"VX-{inv_input}"
                    st.session_state["selected_case_id"] = target_cid
                    st.session_state["previous_nav"] = "Home"
                    st.session_state["view_mode"] = "detail"
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1])

    # 5. RECENT ACTIVITY (FILTERED FOR PLAIN BUSINESS EVENTS ONLY - NO TECHNICAL LOGS)
    with col_left:
        st.markdown('<div class="vaulty-card" style="height: 100%;">', unsafe_allow_html=True)
        st.markdown("<div style='font-size: 14.5px; font-weight: 700; color: #0f172a; margin-bottom: 2px;'>Recent Activity</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 12px; color: #64748b; margin-bottom: 12px;'>Recent business events across invoice exceptions.</div>", unsafe_allow_html=True)

        logs = biz_repo.get_audit_logs()
        biz_logs = [l for l in logs if is_business_event(l)] if logs and isinstance(logs, list) else []

        if biz_logs:
            for item in biz_logs[:5]:
                dt = item.get("date") or item.get("timestamp", "Today")[:10]
                desc = format_business_event_desc(item)

                st.markdown(f"""
                <div style="background: #f8fafc; border: 1px solid #f1f5f9; border-left: 3px solid #2563eb; padding: 8px 12px; margin-bottom: 6px; border-radius: 6px;">
                    <div style="font-size: 10.5px; font-weight: 700; color: #64748b;">{dt}</div>
                    <div style="font-size: 12.5px; font-weight: 600; color: #0f172a; margin-top: 2px;">{desc}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            render_empty_state("No recent activity.", "No Activity")
        st.markdown("</div>", unsafe_allow_html=True)

    # 6. RECENT INVESTIGATIONS (Real Cases Table)
    with col_right:
        st.markdown('<div class="vaulty-card" style="height: 100%;">', unsafe_allow_html=True)
        st.markdown("<div style='font-size: 14.5px; font-weight: 700; color: #0f172a; margin-bottom: 2px;'>Recent Investigations</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 12px; color: #64748b; margin-bottom: 12px;'>Active exception cases in the operational queue.</div>", unsafe_allow_html=True)

        all_cases = biz_repo.get_all_cases()
        if all_cases and isinstance(all_cases, list):
            for c in all_cases[:4]:
                cid = c.get("case_id")
                inv_id = c.get("invoice_id")
                vname = c.get("vendor_name")
                issue = normalize_discrepancy_type(c.get("discrepancy_type", ""))
                amt = c.get("amount", 0.0)
                status = c.get("status")

                pill_html = render_status_pill(status)

                c_info, c_btn = st.columns([4, 1])
                with c_info:
                    st.markdown(f"""
                    <div style="border-bottom: 1px solid #f1f5f9; padding-bottom: 6px; margin-bottom: 6px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13px; font-weight: 700; color: #0f172a;">{vname} ({inv_id})</span>
                            {pill_html}
                        </div>
                        <div style="font-size: 11.5px; color: #475569; margin-top: 2px;">
                            <strong>Issue:</strong> {issue} &nbsp;|&nbsp; <strong>Amount:</strong> ₹{amt:,.2f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with c_btn:
                    if st.button("Review", key=f"home_case_btn_{cid}"):
                        st.session_state["selected_case_id"] = cid
                        st.session_state["previous_nav"] = "Home"
                        st.session_state["view_mode"] = "detail"
                        st.rerun()
        else:
            render_empty_state("No exception cases currently in queue.", "No Investigations")
        st.markdown("</div>", unsafe_allow_html=True)


# --- PAGE 2: APPROVALS ---

def render_approvals_page():
    st.markdown('<div class="page-title">Approvals</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Review invoices that need your decision.</div>', unsafe_allow_html=True)

    cases = biz_repo.get_all_cases()
    summary = analytics.get_approval_summary()

    # Summary Tiles
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_stat_tile("Ready for approval", str(summary.get("needs_approval", 0)), "Awaiting signoff", "#d97706")
    with c2:
        render_stat_tile("Resolved", str(summary.get("approved", 0)), "Payment released", "#16a34a")
    with c3:
        render_stat_tile("On hold / Query", str(summary.get("on_hold", 0) + summary.get("vendor_query", 0)), "Pending response", "#2563eb")
    with c4:
        render_stat_tile("Discrepancies", str(summary.get("total_discrepancies", 0)), "Total exception cases", "#7c3aed")
    with c5:
        render_stat_tile("Under review", f"₹{summary.get('total_amount_under_review', 0.0):,.0f}", "Open case value", "#dc2626")

    st.markdown("<br/>", unsafe_allow_html=True)

    # Search & Simple Filter Bar
    c_search, c_vendor, c_status = st.columns([2, 1, 1])
    with c_search:
        search_q = st.text_input("Search queue...", "", placeholder="Search vendor, invoice, case...", key="app_search")
    with c_vendor:
        all_vnames = list(set([c.get("vendor_name", "") for c in cases if c.get("vendor_name")]))
        selected_v = st.selectbox("Vendor Filter", ["All Vendors"] + all_vnames, key="app_vendor")
    with c_status:
        default_filter = st.session_state.get("approval_filter", "ALL")
        status_opts = ["ALL", "Ready for your approval", "Being checked", "Waiting on vendor", "On hold", "Needs urgent review", "Resolved"]
        idx = status_opts.index(default_filter) if default_filter in status_opts else 0
        selected_s = st.selectbox("Status Filter", status_opts, index=idx, key="app_status")

    # Filter Logic
    filtered = cases
    if search_q:
        q = search_q.lower()
        filtered = [c for c in filtered if q in c.get("vendor_name", "").lower() or q in c.get("case_id", "").lower() or q in c.get("invoice_id", "").lower()]
    if selected_v != "All Vendors":
        filtered = [c for c in filtered if c.get("vendor_name") == selected_v]

    if selected_s == "Ready for your approval":
        filtered = [c for c in filtered if c.get("status") == "AWAITING_HUMAN_PAYMENT_RELEASE"]
    elif selected_s == "Being checked":
        filtered = [c for c in filtered if c.get("status") in ("UNPROCESSED", "INVESTIGATING")]
    elif selected_s == "Waiting on vendor":
        filtered = [c for c in filtered if c.get("status") in ("PENDING VENDOR RESPONSE", "CORRECTION REQUESTED")]
    elif selected_s == "On hold":
        filtered = [c for c in filtered if c.get("status") == "ESCALATED TO PROCUREMENT"]
    elif selected_s == "Needs urgent review":
        filtered = [c for c in filtered if c.get("status") == "FRAUD REVIEW"]
    elif selected_s == "Resolved":
        filtered = [c for c in filtered if c.get("status") == "RESOLVED"]

    st.markdown("---")

    # Main Operational Queue
    st.markdown("### Operational Exception Queue")

    if not filtered:
        render_empty_state("No invoices require your attention matching the selected filter criteria.", "No Invoices Found")
    else:
        for c in filtered:
            cid = c.get("case_id")
            vname = c.get("vendor_name")
            inv_id = c.get("invoice_id")
            inv_amt = c.get("amount", 0.0)
            status = c.get("status")
            risk = c.get("risk_level", "Medium")
            last_action = c.get("last_action", "Pending inspection")
            updated = c.get("updated_at", c.get("created_at", "Today"))[:10]

            inv = biz_repo.get_invoice(inv_id) if inv_id else {}
            po_id = c.get("po_id") or (inv.get("po_id") if isinstance(inv, dict) and "error" not in inv else None)
            po = biz_repo.get_purchase_order(po_id) if po_id else {}
            rec = biz_repo.get_receipt(po_id) if po_id else {}

            po_available = isinstance(po, dict) and "error" not in po and po
            po_amt = po.get("total_amount", 0.0) if po_available else None

            diff = calculate_difference(inv, po, rec)
            if diff == 0.0 and po_amt is not None and inv_amt > po_amt and po_amt > 0:
                diff = inv_amt - po_amt

            norm_discrepancy = normalize_discrepancy_type(c.get("discrepancy_type", ""))
            pill_html = render_status_pill(status)

            col_info, col_btn = st.columns([5, 1])
            with col_info:
                if not po_available:
                    diff_str_html = '<span style="color: #d97706; font-weight: 700;">Purchase order not available</span>'
                    po_amt_str = "Not available"
                else:
                    po_amt_str = f"₹{po_amt:,.2f}"
                    diff_str_html = f'<span style="color: {"#dc2626" if diff > 0 else "#16a34a"}; font-weight: 700;">₹{diff:,.2f}</span>'

                st.markdown(f"""
                <div class="vaulty-card" style="margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-size: 15px; font-weight: 800; color: #0f172a;">{vname}</span>
                            <span style="font-size: 13px; color: #64748b; margin-left: 10px;">Invoice: {inv_id} | PO: {po_id or 'Not available'}</span>
                        </div>
                        <div>
                            {pill_html}
                            <span style="font-size: 11px; font-weight: 700; color: #475569; margin-left: 10px;">Priority: {risk}</span>
                        </div>
                    </div>
                    <div style="margin-top: 8px; font-size: 13px; color: #334155;">
                        <strong>Issue:</strong> {norm_discrepancy} &nbsp;|&nbsp; 
                        <strong>Invoice Amt:</strong> ₹{inv_amt:,.2f} &nbsp;|&nbsp; 
                        <strong>PO Amt:</strong> {po_amt_str} &nbsp;|&nbsp; 
                        <strong>Difference:</strong> {diff_str_html}
                    </div>
                    <div style="margin-top: 4px; font-size: 12px; color: #64748b;">
                        <strong>Last Action:</strong> {last_action} &nbsp;|&nbsp; <strong>Date:</strong> {updated}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_btn:
                if st.button("Inspect Case", key=f"app_btn_{cid}"):
                    st.session_state["selected_case_id"] = cid
                    st.session_state["previous_nav"] = "Approvals"
                    st.session_state["view_mode"] = "detail"
                    st.rerun()

    # Payment Approval History Section
    st.markdown("---")
    st.markdown("### Payment Approval History")
    st.caption("Complete operational history of payment approvals, vendor queries, and human decisions.")

    history = analytics.get_approval_history()
    if history and isinstance(history, list):
        df_hist = pd.DataFrame(history)
        cols = ["decision_date", "invoice_id", "vendor_name", "amount", "decision", "actor", "discrepancy_status", "final_outcome"]
        df_display = df_hist[[c for c in cols if c in df_hist.columns]].copy()
        df_display.columns = ["Date", "Invoice ID", "Vendor", "Amount (₹)", "Decision", "Actor", "Issue", "Outcome"]
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        render_empty_state("No approval history recorded yet.", "No History")


# --- PAGE 3: CASE VIEW (THE CENTERPIECE) ---

def render_case_detail_view(case_id: str):
    case_data = biz_repo.get_case(case_id)
    if not case_data or "error" in case_data:
        render_error_card(f"Case or Invoice '{case_id}' could not be located in operational records.", title="Record Not Found")
        prev = st.session_state.get("previous_nav", "Approvals")
        if st.button(f"← Back to {prev}"):
            st.session_state["view_mode"] = "list"
            st.rerun()
        return

    inv_id = case_data.get("invoice_id")
    vendor_id = case_data.get("vendor_id")
    vname = case_data.get("vendor_name")
    issue = case_data.get("discrepancy_type", "Invoice Exception")
    amount = case_data.get("amount", 0.0)
    status = case_data.get("status", "UNPROCESSED")

    inv_doc = biz_repo.get_invoice(inv_id) if inv_id else {}
    po_id = case_data.get("po_id") or (inv_doc.get("po_id") if isinstance(inv_doc, dict) and "error" not in inv_doc else None)
    po_doc = biz_repo.get_purchase_order(po_id) if po_id else {}
    rec_doc = biz_repo.get_receipt(po_id) if po_id else {}
    contract_doc = biz_repo.get_contract(vendor_id) if vendor_id else {}

    prev_nav = st.session_state.get("previous_nav", "Approvals")
    if st.button(f"← Back to {prev_nav}"):
        st.session_state["view_mode"] = "list"
        st.rerun()

    st.markdown("<br/>", unsafe_allow_html=True)

    # --------------------------------------------------
    # CASE HEADER
    # --------------------------------------------------
    pill_html = render_status_pill(status)
    po_available = isinstance(po_doc, dict) and "error" not in po_doc and po_doc
    po_amt = po_doc.get("total_amount", 0.0) if po_available else None

    # Dynamic concise description generated from actual case data
    if po_amt is not None and po_amt > 0 and amount > po_amt:
        desc_line = f"Invoice amount (₹{amount:,.2f}) differs from purchase order amount (₹{po_amt:,.2f})."
    elif not po_available:
        desc_line = f"Direct invoice billing submitted without purchase order authorization."
    elif "Quantity" in issue or "Partial" in issue:
        desc_line = f"Invoiced quantity differs from confirmed delivery receipt."
    elif "Bank" in issue or "Fraud" in issue:
        desc_line = f"Invoice bank account details were updated recently and require verification."
    else:
        desc_line = f"Invoice exception requiring evidence verification."

    st.markdown(f"""
    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px 24px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(16,24,40,0.04);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 22px; font-weight: 800; color: #0f172a;">{vname}</span>
                <span style="font-size: 13px; color: #64748b; margin-left: 12px;">Invoice: {inv_id} | Case: {case_id}</span>
            </div>
            <div>
                {pill_html}
            </div>
        </div>
        <div style="margin-top: 10px; font-size: 14.5px; font-weight: 600; color: #334155;">
            Issue: {normalize_discrepancy_type(issue)}
        </div>
        <div style="margin-top: 4px; font-size: 18px; font-weight: 800; color: #059669;">
            Amount: ₹{amount:,.2f}
        </div>
        <div style="margin-top: 8px; font-size: 13px; color: #64748b; font-style: italic;">
            {desc_line}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Visual Verification Path Bar
    render_verification_path()

    # --------------------------------------------------
    # SECTION 1 — CURRENT EVIDENCE
    # --------------------------------------------------
    st.markdown("### CURRENT EVIDENCE")
    st.caption("Side-by-side comparison of operational records available for this case.")

    render_evidence_comparison_table(inv_doc, po_doc, rec_doc, contract_doc)

    diff = calculate_difference(inv_doc, po_doc, rec_doc, contract_doc)
    if diff == 0.0 and po_amt is not None and amount > po_amt and po_amt > 0:
        diff = amount - po_amt

    if not po_available:
        diff_display_html = '<div style="font-size: 14px; font-weight: 700; color: #d97706;">Difference calculation: Purchase order not available</div>'
    elif diff > 0:
        diff_display_html = f'<div style="font-family: \'Plus Jakarta Sans\', sans-serif; font-size: 18px; font-weight: 800; color: #dc2626;">Difference: ₹{diff:,.2f}</div><div style="font-size: 12.5px; color: #475569; margin-top: 2px;">Exceeds authorized purchase order value.</div>'
    else:
        diff_display_html = '<div style="font-family: \'Plus Jakarta Sans\', sans-serif; font-size: 16px; font-weight: 700; color: #16a34a;">Difference: ₹0.00</div><div style="font-size: 12.5px; color: #475569; margin-top: 2px;">Matching consistency confirmed across available documents.</div>'

    st.markdown(f"""
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid {'#d97706' if not po_available else ('#dc2626' if diff > 0 else '#16a34a')}; border-radius: 6px; padding: 12px 16px; margin-top: 12px; margin-bottom: 20px;">
        {diff_display_html}
    </div>
    """, unsafe_allow_html=True)

    # TRIGGER INVESTIGATION PIPELINE (Clean Integration Button)
    if st.button("RUN INVESTIGATION PIPELINE", type="primary", use_container_width=True, key=f"run_inv_{case_id}"):
        with st.spinner("Reviewing current evidence, contract terms, and past organizational experience..."):
            pipeline_res = pipeline.run_pipeline(inv_id, case_id)
            st.session_state[f"pipeline_res_{case_id}"] = pipeline_res
            st.success("Investigation completed!")
            st.rerun()

    pipe_res = st.session_state.get(f"pipeline_res_{case_id}")

    # --------------------------------------------------
    # SECTION 2 — WHAT VAULTY FOUND
    # --------------------------------------------------
    st.markdown("---")
    st.markdown("### WHAT VAULTY FOUND")

    if pipe_res and isinstance(pipe_res, dict):
        inv_res = pipe_res.get("stage_5_investigation", {})
        res_res = pipe_res.get("stage_6_resolution", {})
        orch_res = pipe_res.get("stage_7_human_gate", {})
        mem_analysis = inv_res.get("memory_influence_analysis", {})
        findings_summary = inv_res.get("reasoning_summary") or "Investigation completed. Evidence reviewed against PO and contract terms."

        st.markdown(f"""
        <div class="vaulty-card">
            <div style="font-size: 14px; font-weight: 700; color: #0f172a; margin-bottom: 6px;">Evidence Findings</div>
            <div style="font-size: 13.5px; color: #334155; line-height: 1.5;">{findings_summary}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        render_empty_state("This case has not been investigated yet.", "Not Investigated Yet")
        inv_res = {}
        res_res = {}
        orch_res = {}
        mem_analysis = {}

    # --------------------------------------------------
    # SECTION 3 — VAULTY REMEMBERED (SIGNATURE VIOLET PANEL)
    # --------------------------------------------------
    render_signature_memory_panel(mem_analysis)

    # --------------------------------------------------
    # SECTION 4 — WHAT THIS MEANS
    # --------------------------------------------------
    st.markdown("### WHAT THIS MEANS")

    if pipe_res:
        means_conclusion = res_res.get("summary") or "Evidence verification completed."
        st.markdown(f"""
        <div class="vaulty-card" style="border-left: 4px solid #2563eb;">
            <div style="font-size: 14px; font-weight: 700; color: #0f172a;">Factual Conclusion</div>
            <div style="font-size: 13.5px; color: #334155; margin-top: 4px; line-height: 1.5;">{means_conclusion}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="vaulty-card" style="border-left: 4px solid #cbd5e1;">
            <div style="font-size: 13.5px; color: #64748b;">Vaulty has not completed an investigation for this case yet.</div>
        </div>
        """, unsafe_allow_html=True)

    # --------------------------------------------------
    # SECTION 5 — RECOMMENDED ACTION
    # --------------------------------------------------
    st.markdown("### RECOMMENDED ACTION")

    if pipe_res and inv_res.get("recommended_action"):
        rec_act = inv_res.get("recommended_action")
        st.markdown(f"""
        <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-left: 4px solid #16a34a; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
            <div style="font-size: 11px; font-weight: 700; color: #166534; text-transform: uppercase;">Recommended Action</div>
            <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 16px; font-weight: 800; color: #14532d; margin-top: 2px;">
                {rec_act.replace('_', ' ').title()}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Recommendation will be generated upon running the investigation pipeline.")

    # --------------------------------------------------
    # SECTION 6 — THIS NEEDS YOUR INPUT
    # --------------------------------------------------
    st.markdown("---")
    st.markdown("### THIS NEEDS YOUR INPUT")

    if status in ("AWAITING_HUMAN_PAYMENT_RELEASE", "UNPROCESSED") or orch_res.get("requires_human_payment_approval"):
        st.markdown("""
        <div style="background: #fffbeb; border: 1px solid #fde68a; border-left: 4px solid #d97706; border-radius: 8px; padding: 18px 20px; margin-bottom: 16px;">
            <div style="font-size: 15px; font-weight: 800; color: #92400e;">
                HUMAN SIGN-OFF REQUIRED FOR PAYMENT RELEASE
            </div>
            <div style="font-size: 13px; color: #78350f; margin-top: 4px;">
                Vaulty has reviewed current evidence and past experience. No payment is released automatically.<br/>
                <strong>Your explicit human approval or decision is required to proceed.</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_app, col_rej = st.columns(2)
        with col_app:
            if st.button("APPROVE PAYMENT RELEASE", type="primary", use_container_width=True, key=f"app_{case_id}"):
                biz_repo.update_approval_status(case_id, "RESOLVED", "Payment release approved by Finance Manager.")
                ref_res = pipeline.process_human_decision(
                    case_id=case_id,
                    vendor_id=vendor_id,
                    vendor_name=vname,
                    discrepancy_type=issue,
                    agent_recommendation=inv_res.get("recommended_action", "APPROVE"),
                    human_outcome="APPROVED",
                    human_notes="Payment release authorized after evidence verification."
                )
                st.session_state[f"lesson_saved_{case_id}"] = ref_res
                st.success("Payment Approved! Lesson saved to organizational memory.")
                st.rerun()

        with col_rej:
            notes_input = st.text_input("Correction Notes", "Verify receipt before releasing payment.", key=f"corr_{case_id}")
            if st.button("REQUEST CORRECTION / HOLD", use_container_width=True, key=f"rej_{case_id}"):
                biz_repo.update_approval_status(case_id, "PENDING VENDOR RESPONSE", f"Payment held: {notes_input}")
                ref_res = pipeline.process_human_decision(
                    case_id=case_id,
                    vendor_id=vendor_id,
                    vendor_name=vname,
                    discrepancy_type=issue,
                    agent_recommendation=inv_res.get("recommended_action", "APPROVE"),
                    human_outcome="CORRECTED",
                    human_notes=notes_input
                )
                st.session_state[f"lesson_saved_{case_id}"] = ref_res
                st.warning("Action saved! Vaulty learned from your feedback for future investigations.")
                st.rerun()

    elif status == "FRAUD REVIEW" or orch_res.get("requires_human_fraud_review"):
        st.error("THIS CASE IS PLACED ON FRAUD REVIEW. ROUTED TO FRAUD AUDIT TEAM.")
    else:
        st.success("This case has been resolved.")

    # --------------------------------------------------
    # SECTION 7 — VAULTY LEARNED FROM THIS CASE
    # --------------------------------------------------
    lesson_saved = st.session_state.get(f"lesson_saved_{case_id}")
    if lesson_saved and isinstance(lesson_saved, dict):
        st.markdown("---")
        st.markdown("### VAULTY LEARNED FROM THIS CASE")
        les_text = lesson_saved.get("reflection_text") or lesson_saved.get("lesson") or "Human resolution produced reusable organizational experience."
        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-card-title">Organizational Lesson Learned</div>
            <div class="insight-card-body">"{les_text}"</div>
        </div>
        """, unsafe_allow_html=True)

    # --------------------------------------------------
    # SECTION 8 — CASE HISTORY (FILTERED FOR BUSINESS EVENTS ONLY)
    # --------------------------------------------------
    st.markdown("---")
    with st.expander("CASE HISTORY", expanded=False):
        history_logs = biz_repo.get_case_events(case_id)
        biz_history = [l for l in history_logs if is_business_event(l)] if history_logs and isinstance(history_logs, list) else []

        if biz_history:
            for log in biz_history:
                dt = log.get("timestamp") or log.get("date")
                act_desc = format_business_event_desc(log)
                st.markdown(f"""
                <div style="background: #ffffff; border: 1px solid #e2e8f0; padding: 10px 14px; margin-bottom: 6px; border-radius: 6px; font-size: 12.5px;">
                    <strong>{dt}</strong> — {act_desc}
                </div>
                """, unsafe_allow_html=True)
        else:
            render_empty_state("No recorded business history events for this case yet.", "No Case History")


# --- PAGE 4: VENDORS ---

def render_vendors_page():
    st.markdown('<div class="page-title">Vendors</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Review supplier activity, payment terms, exceptions, and accumulated experience.</div>', unsafe_allow_html=True)

    vendors = biz_repo.get_all_vendors()
    if not vendors:
        render_empty_state("No suppliers found in repository records.", "No Vendors")
        return

    all_cases = biz_repo.get_all_cases()
    all_invoices = biz_repo.get_all_invoices()

    # Supplier Directory Table
    st.markdown("### Supplier Directory")
    directory_data = []
    for v in vendors:
        vid = v.get("vendor_id")
        vname = v.get("vendor_name")
        v_cases = [c for c in all_cases if c.get("vendor_id") == vid or c.get("vendor_name") == vname]
        v_invs = [i for i in all_invoices if i.get("vendor_id") == vid or i.get("vendor_name") == vname]

        inv_cnt = max(len(v_invs), v.get("total_invoices_processed", len(v_cases)))
        exc_cnt = len(v_cases)
        under_rev = sum([c.get("amount", 0.0) for c in v_cases if c.get("status") != "RESOLVED"])

        contract = biz_repo.get_contract(vid)
        p_terms = contract.get("payment_terms", v.get("payment_terms", "Net 30")) if isinstance(contract, dict) and "error" not in contract else v.get("payment_terms", "Net 30")

        directory_data.append({
            "Supplier Code": vid,
            "Vendor": vname,
            "Category": v.get("category", "Supplies & Services"),
            "Status": v.get("status", "Active"),
            "Payment Terms": p_terms,
            "Total Invoices": inv_cnt,
            "Exceptions": exc_cnt,
            "Under Review (₹)": f"₹{under_rev:,.2f}",
            "Last Activity": "Today"
        })

    df_dir = pd.DataFrame(directory_data)
    st.dataframe(df_dir, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Supplier Detail Inspector
    st.markdown("### Supplier Detail Inspector")
    vnames = [v.get("vendor_name") for v in vendors]
    c_search, c_select = st.columns([2, 2])
    with c_search:
        search_v = st.text_input("Search supplier profile...", "", key="v_search_input", placeholder="Type vendor name...")
    with c_select:
        filtered_vnames = [vn for vn in vnames if search_v.lower() in vn.lower()] if search_v else vnames
        selected_vname = st.selectbox("Select supplier profile", filtered_vnames if filtered_vnames else vnames, key="v_select_box")

    selected_vendor = [v for v in vendors if v.get("vendor_name") == selected_vname][0]
    vid = selected_vendor.get("vendor_id")

    vendor_cases = [c for c in all_cases if c.get("vendor_id") == vid or c.get("vendor_name") == selected_vname]
    vendor_invoices = [inv for inv in all_invoices if inv.get("vendor_id") == vid or inv.get("vendor_name") == selected_vname]

    inv_count = len(vendor_invoices) if vendor_invoices else (selected_vendor.get("total_invoices_processed", 18))
    exc_count = len(vendor_cases)
    under_review_amount = sum([c.get("amount", 0.0) for c in vendor_cases if c.get("status") != "RESOLVED"])

    category = selected_vendor.get("category", "Supplies & Services")

    st.markdown("<br/>", unsafe_allow_html=True)

    # Vendor Summary Card
    st.markdown(f"""
    <div class="vendor-summary-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 22px; font-weight: 800; color: #0f172a;">{selected_vname}</span>
                <span style="font-size: 13px; color: #64748b; margin-left: 12px;">{category} (Code: {vid})</span>
            </div>
            <div>
                <span class="status-pill status-clear">Active supplier</span>
            </div>
        </div>
        <div class="vendor-summary-grid">
            <div>
                <div class="vendor-summary-metric-label">Invoices</div>
                <div class="vendor-summary-metric-val">{inv_count}</div>
            </div>
            <div>
                <div class="vendor-summary-metric-label">Exceptions</div>
                <div class="vendor-summary-metric-val">{exc_count}</div>
            </div>
            <div>
                <div class="vendor-summary-metric-label">Under review</div>
                <div class="vendor-summary-metric-val">₹{under_review_amount:,.0f}</div>
            </div>
            <div>
                <div class="vendor-summary-metric-label">Payment account</div>
                <div class="vendor-summary-metric-val" style="font-size: 15px;">{mask_bank_account(selected_vendor.get('bank_account'))}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_main, col_side = st.columns([7, 3])

    with col_main:
        # Active Contract Information
        st.markdown("### Active Contract")
        contract = biz_repo.get_contract(vid)

        if isinstance(contract, dict) and "error" not in contract:
            c_title = contract.get("title", "Master Supply Agreement")
            end_d = contract.get("end_date", "Not available")
            std_rate = contract.get("standard_rate")
            std_rate_str = f"₹{std_rate:,.2f}" if isinstance(std_rate, (int, float)) else "Not available"
            p_terms = contract.get("payment_terms", "Not available")
            clause = contract.get("price_adjustment_clause", "Not available")

            st.markdown(f"""
            <div class="vaulty-card" style="margin-bottom: 20px;">
                <div style="font-size: 15px; font-weight: 700; color: #0f172a; margin-bottom: 12px;">
                    {c_title}
                </div>
                <div class="data-grid-two-col">
                    <div class="data-item">
                        <div class="data-label">Valid through</div>
                        <div class="data-value">{end_d}</div>
                    </div>
                    <div class="data-item">
                        <div class="data-label">Standard rate</div>
                        <div class="data-value">{std_rate_str}</div>
                    </div>
                    <div class="data-item">
                        <div class="data-label">Payment terms</div>
                        <div class="data-value">{p_terms}</div>
                    </div>
                    <div class="data-item">
                        <div class="data-label">Price adjustment terms</div>
                        <div class="data-value">{clause}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            render_empty_state("No active contract on file for this supplier.", "No Contract Record")

        # Recent Exceptions
        st.markdown("### Recent Exceptions")
        if not vendor_cases:
            render_empty_state("No recorded exceptions for this supplier.", "No Exceptions")
        else:
            for vc in vendor_cases:
                v_cid = vc.get("case_id")
                v_inv = vc.get("invoice_id")
                v_issue = normalize_discrepancy_type(vc.get("discrepancy_type", ""))
                v_amt = vc.get("amount", 0.0)
                v_status = vc.get("status")
                v_date = vc.get("created_at", "Today")[:10]

                outcome = "Resolved" if v_status == "RESOLVED" else "Under review"

                col_row, col_nav = st.columns([6, 1])
                with col_row:
                    st.markdown(f"""
                    <div class="vaulty-card" style="margin-bottom: 6px; padding: 12px 16px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; font-size: 13px;">
                            <span style="color: #64748b; font-weight: 600;">{v_date}</span>
                            <span style="font-weight: 700; color: #0f172a;">{v_inv}</span>
                            <span style="color: #334155;">{v_issue}</span>
                            <span style="font-weight: 700; color: #059669;">₹{v_amt:,.2f}</span>
                            <span class="status-pill status-investigating">{outcome}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_nav:
                    if st.button("Inspect", key=f"v_case_btn_{v_cid}"):
                        st.session_state["selected_case_id"] = v_cid
                        st.session_state["previous_nav"] = "Vendors"
                        st.session_state["view_mode"] = "detail"
                        st.rerun()

        # Recurring Vendor Issues
        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown("### Recurring Vendor Issues")
        recurring = analytics.find_recurring_vendor_issues()
        v_recurring = [r for r in recurring if r["vendor_id"] == vid or r["vendor_name"] == selected_vname]
        if v_recurring:
            for r in v_recurring:
                st.markdown(f"""
                <div class="vaulty-card" style="border-left: 4px solid #dc2626; margin-bottom: 8px;">
                    <div style="font-size: 14px; font-weight: 700; color: #991b1b;">
                        Recurring {r['issue']} ({r['occurrences']} occurrences detected)
                    </div>
                    <div style="font-size: 13px; color: #334155; margin-top: 4px;">
                        Total Monetary Difference: <strong>₹{r['total_difference']:,.2f}</strong> &nbsp;|&nbsp; 
                        Open: <strong>{r['open_cases']}</strong> &nbsp;|&nbsp; 
                        Resolved: <strong>{r['resolved_cases']}</strong> &nbsp;|&nbsp;
                        Last Occurrence: <strong>{r['last_occurrence']}</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            render_empty_state("No recurring discrepancy issues identified for this supplier.", "No Recurring Patterns")

    with col_side:
        # WHAT VAULTY HAS LEARNED (CLEAN BUSINESS-READY LESSONS)
        st.markdown("### WHAT VAULTY HAS LEARNED")
        st.markdown('<div style="font-size: 12.5px; color: #64748b; margin-bottom: 12px;">Accumulated organizational experience for this supplier.</div>', unsafe_allow_html=True)

        raw_lessons = mem_repo.get_vendor_memory(vid)

        # Clean and deduplicate lessons
        deduped_lessons = []
        seen_texts = set()

        if raw_lessons and isinstance(raw_lessons, list):
            for les in raw_lessons:
                cleaned = format_clean_vendor_lesson(les)
                normalized_text = cleaned["lesson"].strip().lower()
                if normalized_text and normalized_text not in seen_texts:
                    seen_texts.add(normalized_text)
                    deduped_lessons.append(cleaned)

        if deduped_lessons:
            for les in deduped_lessons:
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-card-title">{les['topic']}</div>
                    <div class="insight-card-body">"{les['lesson']}"</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            render_empty_state("No prior lessons stored for this supplier.", "No Lessons Stored")


# --- PAGE 5: REPORTS ---

def render_reports_page():
    st.markdown('<div class="page-title">Reports</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Understand invoice quality, discrepancy patterns, and supplier performance.</div>', unsafe_allow_html=True)

    cases = biz_repo.get_all_cases()
    invoices = biz_repo.get_all_invoices()
    total_invoices = max(len(invoices), len(cases))

    discrepant_cases = [c for c in cases if normalize_discrepancy_type(c.get("discrepancy_type", "")) != "Matching Consistency (Clean)"]
    discrepant_count = len(discrepant_cases)
    seamless_count = max(0, total_invoices - discrepant_count)
    seamless_pct = (seamless_count / total_invoices) * 100 if total_invoices > 0 else 100.0

    # Section 1: Summary Metrics
    st.markdown("### Processing Overview")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_stat_tile("Total Invoices Processed", str(total_invoices), "All processed invoices", "#2563eb")
    with c2:
        render_stat_tile("Clean / Legitimate Invoices", str(seamless_count), "Passed matching cleanly", "#16a34a")
    with c3:
        render_stat_tile("Discrepancy Invoices", str(discrepant_count), "Identified exceptions", "#d97706")
    with c4:
        render_stat_tile("Seamless Processing Rate", f"{seamless_pct:.1f}%", "Zero-discrepancy ratio", "#7c3aed")

    st.markdown("---")

    # Section 2: Discrepancy Overview
    st.markdown("### Discrepancy Overview")
    disc_summary = analytics.get_discrepancy_summary()
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        render_stat_tile("Total Discrepancy Cases", str(disc_summary.get("total_discrepancy_cases", 0)), "Total exceptions", "#2563eb")
    with d2:
        render_stat_tile("Total Financial Impact", f"₹{disc_summary.get('extra_amount_identified', 0.0):,.0f}", "Overbilling difference", "#dc2626")
    with d3:
        render_stat_tile("Open Discrepancies", str(disc_summary.get("open_discrepancies_count", 0)), "Awaiting resolution", "#d97706")
    with d4:
        render_stat_tile("Resolved Discrepancies", str(disc_summary.get("resolved_discrepancies_count", 0)), "Verified and closed", "#16a34a")

    st.markdown("<br/>", unsafe_allow_html=True)

    # Discrepancy Scenarios Table & Charts (NO "undefined" OR BLANK CONTAINERS)
    breakdown = analytics.get_discrepancy_breakdown()
    if breakdown and isinstance(breakdown, list) and len(breakdown) > 0:
        df_bd = pd.DataFrame(breakdown)
        cols = ["discrepancy_type", "case_count", "total_difference", "open_count", "resolved_count", "average_difference"]
        df_display = df_bd[[c for c in cols if c in df_bd.columns]].copy()
        df_display.columns = ["Discrepancy Type", "Case Count", "Total Difference (₹)", "Open", "Resolved", "Avg Difference (₹)"]
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        st.markdown("<br/>", unsafe_allow_html=True)
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown('<div class="vaulty-card">', unsafe_allow_html=True)
            st.markdown("<div style='font-size: 14px; font-weight: 700; color: #0f172a; margin-bottom: 10px;'>Case Count by Exception Type</div>", unsafe_allow_html=True)
            cats = [b["discrepancy_type"] for b in breakdown if b.get("discrepancy_type")]
            vals = [b["case_count"] for b in breakdown if b.get("discrepancy_type")]
            if cats and vals:
                render_plotly_horizontal_bar(cats, vals, color="#2563eb", height=240)
            else:
                render_empty_state("No exception case breakdown data available.", "No Chart Data")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_c2:
            st.markdown('<div class="vaulty-card">', unsafe_allow_html=True)
            st.markdown("<div style='font-size: 14px; font-weight: 700; color: #0f172a; margin-bottom: 10px;'>Financial Overbilling Impact (₹)</div>", unsafe_allow_html=True)
            cats = [b["discrepancy_type"] for b in breakdown if b.get("discrepancy_type")]
            vals = [b["total_difference"] for b in breakdown if b.get("discrepancy_type")]
            if cats and vals:
                render_plotly_horizontal_bar(cats, vals, color="#dc2626", is_currency=True, height=240)
            else:
                render_empty_state("No financial impact breakdown data available.", "No Chart Data")
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        render_empty_state("No discrepancy scenarios recorded.", "No Breakdown Data")

    st.markdown("---")

    # Section 3: Operational Drivers
    st.markdown("### Why Are Discrepancies Happening?")
    st.markdown("""
    <div class="data-grid-two-col">
        <div class="vaulty-card">
            <div style="font-weight: 700; color: #0f172a;">PO & Unit Price Mismatches</div>
            <div style="font-size: 13px; color: #475569; margin-top: 4px;">Invoiced rate exceeds purchase order authorization without signed contract amendment backing.</div>
        </div>
        <div class="vaulty-card">
            <div style="font-weight: 700; color: #0f172a;">Quantity & Partial Deliveries</div>
            <div style="font-size: 13px; color: #475569; margin-top: 4px;">Full order billed before goods receipt is confirmed at warehouse main bay.</div>
        </div>
        <div class="vaulty-card">
            <div style="font-weight: 700; color: #0f172a;">Missing Documentation</div>
            <div style="font-size: 13px; color: #475569; margin-top: 4px;">Direct billing submitted without valid Purchase Order reference.</div>
        </div>
        <div class="vaulty-card">
            <div style="font-weight: 700; color: #0f172a;">Banking Detail Modifications</div>
            <div style="font-size: 13px; color: #475569; margin-top: 4px;">Unverified bank account updates executed shortly before invoice submission.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Section 4: Recurring Vendor Issues
    st.markdown("### Recurring Vendor Issues")
    recurring = analytics.find_recurring_vendor_issues()
    if recurring and isinstance(recurring, list) and len(recurring) > 0:
        df_rec = pd.DataFrame(recurring)
        cols = ["vendor_name", "issue", "occurrences", "total_difference", "open_cases", "resolved_cases", "last_occurrence"]
        df_display = df_rec[[c for c in cols if c in df_rec.columns]].copy()
        df_display.columns = ["Supplier", "Recurring Issue", "Occurrences", "Total Difference (₹)", "Open", "Resolved", "Last Occurrence"]
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        render_empty_state("No recurring vendor issue patterns detected in operational history.", "No Recurring Issues")

    st.markdown("---")

    # Section 5: Vendor Invoice Quality
    st.markdown("### Vendor Invoice Quality")
    quality_metrics = analytics.get_vendor_quality_metrics()
    if quality_metrics and isinstance(quality_metrics, list) and len(quality_metrics) > 0:
        df_qual = pd.DataFrame(quality_metrics)
        cols = ["vendor_name", "total_invoices", "clean_invoices", "discrepant_invoices", "discrepancy_rate_pct", "total_difference", "most_common_issue"]
        df_display = df_qual[[c for c in cols if c in df_qual.columns]].copy()
        df_display.columns = ["Supplier", "Total Invoices", "Clean", "Discrepant", "Discrepancy Rate (%)", "Total Difference (₹)", "Most Common Issue"]
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        render_empty_state("No supplier quality data available.", "No Supplier Metrics")
