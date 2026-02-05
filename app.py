import streamlit as st
from utils.style import apply_global_style
from utils.auth import init_session
from utils.ui import top_right_auth

st.set_page_config(
    page_title="SmartSpend",
    page_icon="💳",
    layout="wide"
)

apply_global_style()
init_session()

# Top Navigation
nav_left, nav_right = st.columns([6, 2])

with nav_left:
    st.markdown(
        "<h2 style='margin:0;'>💳 SmartSpend</h2>",
        unsafe_allow_html=True
    )

with nav_right:
    if st.session_state.logged_in:
        top_right_auth()
    else:
        if st.button("Log In"):
            st.switch_page("pages/0_Login.py")

# Hero Section 
st.markdown(
    """
    <div class="card" style="
        background: linear-gradient(135deg, #0f172a, #1e293b);
        color: white;
        padding: 3rem;
        margin-top: 2rem;
    ">
        <h1 style="font-size: 3rem; margin-bottom: 1rem;">
            Master Your Money with SmartSpend
        </h1>
        <p style="font-size: 1.1rem; max-width: 700px;">
            Track expenses, gain intelligent insights, and forecast your financial future
            with confidence - all in one smart dashboard.
        </p>
        <br>
        <form method="get">
            <button name="get_started" value="1"
                style="
                    background-color: #3b82f6;
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    border-radius: 8px;
                    font-size: 1rem;
                    cursor: pointer;
                ">
                Get Started
            </button>
        </form>
    </div>
    """,
    unsafe_allow_html=True
)

# Handle Get Started Redirect
query_params = st.query_params

if "get_started" in query_params:
    if st.session_state.logged_in:
        st.switch_page("pages/2_Dashboard.py")
    else:
        st.switch_page("pages/0_Login.py")

# Features
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<h2>Smarter Tools for Your Finances</h2>", unsafe_allow_html=True)

f1, f2, f3 = st.columns(3)

def feature_card(title, text):
    st.markdown(
        f"""
        <div class="card">
            <h4>{title}</h4>
            <p style="color:#6b7280;">{text}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with f1:
    feature_card(
        "📊 Real-time Tracking",
        "Upload transactions and instantly see categorised spending insights."
    )

with f2:
    feature_card(
        "💡 SmartSpend Advisor",
        "Rule-based and anomaly-driven financial insights."
    )

with f3:
    feature_card(
        "📈 Future Forecasting",
        "Time-series forecasting using SARIMAX models."
    )

# Footer
st.markdown(
    """
    <div style="text-align:center; margin-top:4rem; color:#6b7280;">
        © 2026 SmartSpend — Final Year Project
    </div>
    """,
    unsafe_allow_html=True
)
