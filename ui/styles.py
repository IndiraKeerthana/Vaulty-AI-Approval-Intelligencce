import streamlit as st

def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    /* 1. UNIVERSAL LIGHT ENTERPRISE THEME */
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stMain"], main, section {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }

    /* Hide Streamlit Chrome & Headers */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header[data-testid="stHeader"] { display: none !important; }
    div[data-testid="stToolbar"] { display: none !important; }
    div[data-testid="stDecoration"] { display: none !important; }
    div[data-testid="stSidebarNav"] { display: none !important; }
    .stDeployButton { display: none !important; }

    /* Layout Max Width & Spacing */
    .main .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1360px !important;
        background-color: #f8fafc !important;
    }

    /* Headings Hierarchy */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #0f172a !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }

    .page-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 26px;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 2px;
        letter-spacing: -0.02em;
    }

    .page-subtitle {
        font-size: 13.5px;
        color: #64748b;
        margin-bottom: 20px;
        line-height: 1.45;
    }

    /* 2. SIDEBAR STYLING */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
    }

    section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        padding-top: 1.25rem;
    }

    .sidebar-brand {
        padding: 4px 4px 14px 4px;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 14px;
    }

    .brand-title-text {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 20px;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: 0.04em;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .brand-logo-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 26px;
        height: 26px;
        border-radius: 6px;
        background: #2563eb;
        color: #ffffff;
        font-size: 13px;
        font-weight: 800;
    }

    .brand-subtitle {
        font-size: 11px;
        font-weight: 700;
        color: #2563eb;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 4px;
    }

    .brand-tagline {
        font-size: 11.5px;
        font-style: italic;
        color: #64748b;
        margin-top: 2px;
    }

    .system-status-container {
        margin-top: 12px;
        padding-top: 10px;
        border-top: 1px solid #f1f5f9;
        display: flex;
        flex-direction: column;
        gap: 5px;
    }

    .status-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 11px;
    }

    .status-label {
        font-weight: 600;
        color: #64748b;
    }

    .status-value-connected {
        font-weight: 600;
        color: #15803d;
        background: #f0fdf4;
        padding: 2px 7px;
        border-radius: 4px;
        border: 1px solid #bbf7d0;
    }

    .status-value-local {
        font-weight: 600;
        color: #475569;
        background: #f8fafc;
        padding: 2px 7px;
        border-radius: 4px;
        border: 1px solid #e2e8f0;
    }

    /* RESTYLE STREAMLIT RADIO NAVIGATION INTO ENTERPRISE TABS */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] > div {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] label {
        background-color: #ffffff;
        border: 1px solid transparent;
        border-radius: 6px;
        padding: 8px 12px !important;
        cursor: pointer;
        transition: all 0.15s ease;
        display: flex;
        align-items: center;
        margin: 0 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {
        background-color: #f8fafc;
        border-color: #e2e8f0;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] label > div:first-child {
        display: none !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] label p {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        color: #334155 !important;
        margin: 0 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] label[aria-checked="true"],
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) {
        background-color: #eff6ff !important;
        border: 1px solid #bfdbfe !important;
        border-left: 4px solid #2563eb !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] label[aria-checked="true"] p,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label:has(input:checked) p {
        color: #1e40af !important;
        font-weight: 700 !important;
    }

    /* 3. CARDS & CONTAINERS */
    .vaulty-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 18px 22px;
        margin-bottom: 14px;
        box-shadow: 0 1px 3px rgba(16, 24, 40, 0.04);
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }

    .vaulty-card:hover {
        border-color: #cbd5e1;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }

    .vaulty-metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px 18px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 1px 3px rgba(16, 24, 40, 0.04);
    }

    .vaulty-metric-label {
        font-size: 11px;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .vaulty-metric-value {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 26px;
        font-weight: 800;
        color: #0f172a;
        margin-top: 4px;
        margin-bottom: 2px;
        line-height: 1.1;
    }

    .vaulty-metric-sub {
        font-size: 11.5px;
        color: #94a3b8;
    }

    /* STATUS PILLS */
    .status-pill {
        font-size: 11.5px;
        font-weight: 600;
        padding: 3px 9px;
        border-radius: 6px;
        display: inline-block;
        letter-spacing: 0.01em;
    }

    .status-clear {
        background-color: #f0fdf4;
        color: #166534;
        border: 1px solid #bbf7d0;
    }

    .status-investigating {
        background-color: #eff6ff;
        color: #1e40af;
        border: 1px solid #bfdbfe;
    }

    .status-pending {
        background-color: #fffbeb;
        color: #92400e;
        border: 1px solid #fde68a;
    }

    .status-on-hold {
        background-color: #f8fafc;
        color: #475569;
        border: 1px solid #cbd5e1;
    }

    .status-fraud {
        background-color: #fef2f2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }

    /* GRIDS */
    .data-grid-two-col {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-bottom: 12px;
    }

    .data-grid-four-col {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 14px;
    }

    .data-item {
        background: #f8fafc;
        border: 1px solid #f1f5f9;
        border-radius: 6px;
        padding: 10px 12px;
    }

    .data-label {
        font-size: 11px;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .data-value {
        font-size: 13.5px;
        font-weight: 600;
        color: #0f172a;
        margin-top: 2px;
    }

    /* TABLES */
    .formatted-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 8px;
        font-size: 13px;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        overflow: hidden;
    }

    .formatted-table th {
        background: #f8fafc;
        color: #475569;
        font-weight: 700;
        text-align: left;
        padding: 10px 14px;
        border-bottom: 1px solid #e2e8f0;
    }

    .formatted-table td {
        padding: 10px 14px;
        border-bottom: 1px solid #f1f5f9;
        color: #1e293b;
    }

    .formatted-table tr:hover {
        background: #f8fafc;
    }

    /* SIGNATURE VAULTY MEMORY PANEL (VIOLET ACCENT) */
    .vaulty-signature-memory-panel {
        background: #fcfaff;
        border: 1px solid #ddd6fe;
        border-left: 4px solid #7c3aed;
        border-radius: 8px;
        padding: 18px 20px;
        margin: 18px 0;
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.04);
    }

    .memory-header-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 15px;
        font-weight: 800;
        color: #5b21b6;
        letter-spacing: 0.02em;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .memory-verdict-tag {
        font-size: 11px;
        font-weight: 700;
        padding: 3px 9px;
        border-radius: 12px;
        letter-spacing: 0.02em;
    }

    .verdict-match {
        background-color: #f0fdf4;
        color: #15803d;
        border: 1px solid #bbf7d0;
    }

    .verdict-mismatch {
        background-color: #fef2f2;
        color: #b91c1c;
        border: 1px solid #fecaca;
    }

    .verdict-new {
        background-color: #f8fafc;
        color: #475569;
        border: 1px solid #cbd5e1;
    }

    .memory-stage-grid {
        margin-top: 14px;
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 12px;
    }

    .memory-stage-box {
        background: #ffffff;
        border: 1px solid #ede9fe;
        border-radius: 6px;
        padding: 12px 14px;
    }

    .memory-stage-title {
        font-size: 11px;
        font-weight: 700;
        color: #7c3aed;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }

    .memory-stage-content {
        font-size: 12.5px;
        color: #1e293b;
        line-height: 1.45;
    }

    /* VERIFICATION PATH CONTAINER */
    .verification-path-container {
        display: flex;
        align-items: center;
        gap: 8px;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 10px 16px;
        margin-bottom: 16px;
        overflow-x: auto;
    }

    .verification-step {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        font-weight: 600;
        color: #0f172a;
        white-space: nowrap;
    }

    .verification-step-icon {
        width: 18px;
        height: 18px;
        border-radius: 50%;
        background: #16a34a;
        color: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 10px;
        font-weight: 800;
    }

    .verification-arrow {
        color: #94a3b8;
        font-size: 12px;
    }

    /* VENDOR SUMMARY CARD */
    .vendor-summary-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(16, 24, 40, 0.04);
    }

    .vendor-summary-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid #f1f5f9;
    }

    .vendor-summary-metric-label {
        font-size: 11px;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .vendor-summary-metric-val {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 18px;
        font-weight: 800;
        color: #0f172a;
        margin-top: 2px;
    }

    /* INSIGHT CARD STYLING */
    .insight-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 3px solid #7c3aed;
        border-radius: 6px;
        padding: 12px 14px;
        margin-bottom: 8px;
    }

    .insight-card-title {
        font-size: 12.5px;
        font-weight: 700;
        color: #6d28d9;
    }

    .insight-card-body {
        font-size: 12.5px;
        color: #334155;
        margin-top: 3px;
        line-height: 1.45;
    }

    /* EMPTY STATE CARD */
    .empty-state-card {
        background: #ffffff;
        border: 1px dashed #cbd5e1;
        border-radius: 8px;
        padding: 24px;
        text-align: center;
        margin: 16px 0;
    }

    .empty-state-title {
        font-size: 14px;
        font-weight: 700;
        color: #475569;
    }

    .empty-state-body {
        font-size: 12.5px;
        color: #94a3b8;
        margin-top: 4px;
    }

    /* STREAMLIT FORM CONTROLS */
    .stTextInput input, .stSelectbox [data-baseweb="select"], .stNumberInput input {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border-color: #cbd5e1 !important;
        border-radius: 6px !important;
    }

    /* BUTTONS */
    div.stButton > button {
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        transition: all 0.15s ease !important;
    }

    div.stButton > button[kind="secondary"] {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border: 1px solid #cbd5e1 !important;
    }

    div.stButton > button[kind="secondary"]:hover {
        background-color: #f8fafc !important;
        border-color: #94a3b8 !important;
    }

    div.stButton > button[kind="primary"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: 1px solid #2563eb !important;
    }

    div.stButton > button[kind="primary"]:hover {
        background-color: #1d4ed8 !important;
        border-color: #1d4ed8 !important;
    }
    </style>
    """, unsafe_allow_html=True)
