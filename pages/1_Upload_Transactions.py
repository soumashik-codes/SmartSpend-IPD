import streamlit as st
import pandas as pd

# Styling
from utils.style import apply_global_style
apply_global_style()

# Auth
from utils.auth import require_login, logout_user
require_login()

with st.sidebar:
    st.markdown(f"👤 **{st.session_state.first_name} {st.session_state.last_name}**")
    if st.button("🚪 Log out"):
        logout_user()
        st.switch_page("pages/0_Login.py")

st.set_page_config(
    page_title="Upload Transactions",
    page_icon="📤",
    layout="wide"
)

# Data
from utils.database import (
    write_transactions,
    load_transactions,
    normalise_bank_csv
)
from utils.data_processing import categorise

# Header
st.markdown(
    """
    <h1 style="margin-bottom: 0.25rem;">📤 Upload and Analyse Transactions</h1>
    <p style="color: #6b7280; margin-bottom: 1.5rem;">
        Upload a bank statement CSV. The system automatically detects and standardises
        different formats.
    </p>
    """,
    unsafe_allow_html=True
)

left, right = st.columns([2.2, 1])

# Upload section
with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Upload CSV File")

    uploaded = st.file_uploader(
        "Select a CSV file",
        type=["csv"],
        label_visibility="collapsed"
    )
    
    st.caption(
    "Tip: Most UK banks (e.g. Monzo, Santander, Lloyds) allow you to export "
    "transaction history as a CSV file directly from their mobile or web apps."
    )

    st.markdown('</div>', unsafe_allow_html=True)

# Info
with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Supported Formats")
    st.markdown(
        """
        This page supports:
        - Standard CSVs (`date, description, amount`)
        - Bank statements with **Debit / Credit**
        - Statements with different column names
        """
    )
    st.markdown(
        "<small><b>Note:</b> Expenses are stored as negative values.</small>",
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

# Process uploaded file
if uploaded is not None:
    try:
        raw = pd.read_csv(uploaded)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Raw CSV Preview")
        st.caption("Showing first 10 transactions from uploaded file")
        st.dataframe(raw.head(10), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Normalise bank CSV
        cleaned = normalise_bank_csv(raw)

        # Categorise transactions
        cleaned["category"] = cleaned.apply(
            lambda r: categorise(str(r["description"]), float(r["amount"])),
            axis=1
        )

        # Add month (required by dashboard & forecasting)
        cleaned["month"] = cleaned["date"].dt.to_period("M").astype(str)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Standardised & Categorised Transactions")
        st.caption("Unified format with categories applied")
        st.dataframe(cleaned.head(15), use_container_width=True)

        if st.button("💾 Save and Analyse", type="primary"):
            write_transactions(
                cleaned,
                st.session_state.user_id,
                replace_existing=True
                )
            st.success(
                "Transactions saved successfully. You can now explore the Dashboard, Forecast, and Advisor."
            )

        st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Upload failed: {e}")

# Stored transactions
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("Current Stored Transactions")

df = load_transactions(st.session_state.user_id)

if df.empty:
    st.warning("No transactions stored yet.")
else:
    st.dataframe(
        df.sort_values("date", ascending=False),
        use_container_width=True
    )

st.markdown('</div>', unsafe_allow_html=True)

