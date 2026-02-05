import streamlit as st

from utils.style import apply_global_style
from utils.auth import (
    init_session,
    create_user,
    verify_user,
    login_user,
    logout_user
)
from utils.database import load_transactions

st.set_page_config(
    page_title="SmartSpend | Login",
    page_icon="🔐",
    layout="centered"
)

apply_global_style()
init_session()

st.markdown(
    """
    <h1 style="margin-bottom:0.25rem;">🔐 SmartSpend</h1>
    <p style="color:#6b7280;">
        Personal finance insights — private, local, and data-driven.
    </p>
    """,
    unsafe_allow_html=True
)

# Already logged in
if st.session_state.logged_in:
    st.success(f"Signed in as {st.session_state.first_name} {st.session_state.last_name}")

    if st.button("Log out"):
        logout_user()
        st.switch_page("app.py")

    st.stop()

# Tabs
tab_login, tab_register = st.tabs(["Login", "Create Account"])

# Login
with tab_login:
    st.subheader("Welcome to SmartSpend! 😃")

    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login", type="primary"):
        ok, msg, user_id, first_name, last_name = verify_user(
            username,
            password
        )

        if ok:
            login_user(username, user_id, first_name, last_name)
            st.success(msg)

            df = load_transactions(user_id)
            if df.empty:
                st.switch_page("pages/1_Upload_Transactions.py")
            else:
                st.switch_page("pages/2_Dashboard.py")
        else:
            st.error(msg)

# Create account
with tab_register:
    st.subheader("Create a new account 👇")

    first_name = st.text_input("First name", key="register_first_name")
    last_name = st.text_input("Last name", key="register_last_name")
    new_username = st.text_input("Username", key="register_username")
    new_password = st.text_input(
        "Password",
        type="password",
        key="register_password",
        help="Use a strong password you haven't used elsewhere."
    )

    if st.button("Create Account", type="primary"):
        if not all([first_name, last_name, new_username, new_password]):
            st.warning("Please complete all fields.")
        else:
            ok, msg = create_user(
                new_username,
                first_name,
                last_name,
                new_password
            )
            (st.success if ok else st.error)(msg)
