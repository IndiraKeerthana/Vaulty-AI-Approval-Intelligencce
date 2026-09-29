import streamlit as st
import datetime
from repositories.business_repository import get_business_repository
from repositories.memory_repository import get_memory_repository
from agents.pipeline import InvestigationPipeline
from ui.styles import inject_custom_css
from ui.components import render_sidebar_header
from ui.pages import (
    render_home_page,
    render_approvals_page,
    render_case_detail_view,
    render_vendors_page,
    render_reports_page
)

st.set_page_config(
    page_title="Vaulty — AI Exception Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_custom_css()

biz_repo = get_business_repository()
mem_repo = get_memory_repository()
pipeline = InvestigationPipeline()

data_mode = biz_repo.get_data_mode()
memory_mode = mem_repo.get_memory_mode()

# 1. Sidebar Brand & System Status Header
render_sidebar_header(data_mode=data_mode, memory_mode=memory_mode)

st.sidebar.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

def on_nav_change():
    st.session_state["current_nav"] = st.session_state.get("primary_nav_radio", "Home")
    st.session_state["view_mode"] = "list"
    st.session_state["selected_case_id"] = None

if "current_nav" in st.session_state:
    st.session_state["primary_nav_radio"] = st.session_state["current_nav"]

current_nav = st.session_state.get("current_nav", "Home")
nav_options = ["Home", "Approvals", "Vendors", "Reports"]
nav_index = nav_options.index(current_nav) if current_nav in nav_options else 0

selected_nav = st.sidebar.radio(
    "",
    nav_options,
    index=nav_index,
    key="primary_nav_radio",
    label_visibility="collapsed",
    on_change=on_nav_change
)

if selected_nav != current_nav:
    st.session_state["current_nav"] = selected_nav
    st.session_state["view_mode"] = "list"
    st.session_state["selected_case_id"] = None
    st.rerun()

st.sidebar.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# 3. Dynamic Invoice Ingestion Utility (Quiet Sidebar Utility)
with st.sidebar.expander("Ingest Invoice ▾", expanded=False):
    st.caption("Receive a new invoice into the operational pipeline.")
    sim_vendor_name = st.text_input("Supplier Name", "Orion Tech", key="sim_vname")
    sim_inv_id = st.text_input("Invoice ID", f"INV-{int(datetime.datetime.now().timestamp()) % 10000}", key="sim_invid")
    sim_po_id = st.text_input("PO ID", f"PO-{int(datetime.datetime.now().timestamp()) % 10000}", key="sim_poid")
    sim_disc_type = st.selectbox("Discrepancy Type", [
        "Price Mismatch",
        "Quantity / Partial Delivery Mismatch",
        "Recent Banking Detail Change",
        "Matching Consistency (Clean)"
    ], key="sim_disctype")
    sim_inv_qty = st.number_input("Invoiced Qty", value=100, key="sim_invqty")
    sim_rec_qty = st.number_input("Received Qty", value=80 if "Quantity" in sim_disc_type else 100, key="sim_recqty")
    sim_inv_amount = st.number_input("Invoiced Amount (₹)", value=60000.0, key="sim_invamt")
    sim_po_amount = st.number_input("PO Amount (₹)", value=50000.0 if "Price" in sim_disc_type else 60000.0, key="sim_poamt")
    sim_bank_flag = st.checkbox("Simulate Bank Detail Update", value=("Banking" in sim_disc_type), key="sim_bankflag")

    if st.button("Ingest Invoice", type="primary", use_container_width=True, key="sim_submit"):
        vendor_id = f"VND-{sim_vendor_name.replace(' ', '').upper()[:5]}"
        new_case = biz_repo.create_simulated_case(
            vendor_id=vendor_id,
            vendor_name=sim_vendor_name,
            invoice_id=sim_inv_id,
            po_id=sim_po_id,
            amount=sim_inv_amount,
            discrepancy_type=sim_disc_type,
            invoice_date=datetime.datetime.now().strftime("%Y-%m-%d"),
            po_amount=sim_po_amount,
            receipt_qty=int(sim_rec_qty),
            invoice_qty=int(sim_inv_qty),
            unit_price=sim_inv_amount / sim_inv_qty if sim_inv_qty > 0 else sim_inv_amount,
            bank_account=f"IN{int(datetime.datetime.now().timestamp())}",
            is_recent_bank_update=sim_bank_flag
        )
        cid = new_case["case_id"]
        pipeline_res = pipeline.run_pipeline(sim_inv_id, cid)
        st.session_state[f"pipeline_res_{cid}"] = pipeline_res
        st.session_state["selected_case_id"] = cid
        st.session_state["previous_nav"] = st.session_state.get("current_nav", "Approvals")
        st.session_state["view_mode"] = "detail"
        st.sidebar.success(f"Invoice {sim_inv_id} ingested!")
        st.rerun()

# 4. Render Active View Destination
view_mode = st.session_state.get("view_mode", "list")
selected_cid = st.session_state.get("selected_case_id")

if view_mode == "detail" and selected_cid:
    render_case_detail_view(selected_cid)
else:
    active_page = st.session_state.get("current_nav", "Home")
    if active_page == "Home":
        render_home_page()
    elif active_page == "Approvals":
        render_approvals_page()
    elif active_page == "Vendors":
        render_vendors_page()
    elif active_page == "Reports":
        render_reports_page()
