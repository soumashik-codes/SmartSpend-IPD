import streamlit as st
import pandas as pd
from PIL import Image

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


# Data
from utils.database import (
    load_transactions,
    insert_receipt,
    insert_receipt_items,
    get_receipts_for_transaction,
    get_items_for_receipt
)
from utils.ocr_utils import ocr_image, parse_receipt_items

st.set_page_config(
    page_title="Receipt Analysis",
    page_icon="🧾",
    layout="wide"
)

# Header
st.markdown(
    """
    <h1 style="margin-bottom: 0.25rem;">🧾 Receipt Analysis</h1>
    <p style="color: #6b7280; margin-bottom: 1.5rem;">
        Attach receipts to transactions and extract item-level details using OCR.
    </p>
    """,
    unsafe_allow_html=True
)

df = load_transactions(st.session_state.user_id)
if df.empty:
    st.warning("Upload transactions before adding receipts.")
    st.stop()

# Select Transaction
df["label"] = df["date"].astype(str) + " | " + df["description"] + " | £" + df["amount"].astype(str)
choice = st.selectbox("Select transaction", df["label"])
transaction_id = int(df.loc[df["label"] == choice, "id"].iloc[0])

uploaded = st.file_uploader("Upload receipt image (PNG/JPG)", type=["png", "jpg", "jpeg"])

if uploaded:
    img = Image.open(uploaded)
    st.image(img, use_container_width=True)

    if st.button("Run OCR & Save", type="primary"):
        text = ocr_image(img)
        items = parse_receipt_items(text)

        rid = insert_receipt(transaction_id, uploaded.name, text)
        insert_receipt_items(rid, items)

        st.success(f"Receipt saved. {len(items)} items extracted.")
        st.rerun()

# Show Linked Receipts
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("Linked Receipts")

receipts = get_receipts_for_transaction(transaction_id)
if receipts.empty:
    st.info("No receipts linked yet.")
else:
    st.dataframe(receipts[["id", "filename", "created_at"]], use_container_width=True)
    rid = st.selectbox("View receipt items", receipts["id"])
    items_df = get_items_for_receipt(int(rid))
    st.dataframe(items_df, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)
