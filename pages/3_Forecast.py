import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

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
from utils.database import load_transactions
from utils.forecasting import sarimax_forecast

st.set_page_config(
    page_title="Financial Forecast",
    page_icon="📈",
    layout="wide"
)

# Header
st.markdown(
    """
    <h1 style="margin-bottom: 0.25rem;">📈 Financial Forecast</h1>
    <p style="color: #6b7280; margin-bottom: 1.5rem;">
        Predict future balances using time-series forecasting and scenario analysis.
    </p>
    """,
    unsafe_allow_html=True
)

df = load_transactions(st.session_state.user_id)

# Safety check
if "category" not in df.columns:
    df["category"] = "Other"

if df.empty:
    st.warning("No transaction data available. Upload transactions first.")
    st.stop()

# Prepare Monthly Balance
df["date"] = pd.to_datetime(df["date"])
monthly_balance = (
    df.groupby(pd.Grouper(key="date", freq="M"))["amount"]
    .sum()
    .cumsum()
)

st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("SARIMAX Balance Forecast (Next 6 Months)")

# SARIMAX Forecast with Fallback
try:
    mean_fc, ci = sarimax_forecast(monthly_balance, steps=6)

    forecast_df = pd.DataFrame({
        "Month": mean_fc.index.astype(str),
        "Forecast Balance": mean_fc.values,
        "Lower CI": ci.iloc[:, 0].values,
        "Upper CI": ci.iloc[:, 1].values
    })

    fig = px.line(
        forecast_df,
        x="Month",
        y="Forecast Balance",
        markers=True,
        labels={"Forecast Balance": "Balance (£)"}
    )

    st.plotly_chart(fig, use_container_width=True)
    st.success("SARIMAX forecasting active.")

except Exception as e:
    st.warning(
        "Not enough historical data for SARIMAX yet. "
        "Showing baseline trend projection instead."
    )

    baseline = monthly_balance.iloc[-1] + np.arange(1, 7) * monthly_balance.diff().mean()
    st.line_chart(baseline)

st.markdown('</div>', unsafe_allow_html=True)

# What-if Simulation
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("What-If Spending Simulation")

categories = df[df["amount"] < 0].groupby("category")["amount"].mean().abs()
adjustments = {}

for cat, avg in categories.items():
    adjustments[cat] = st.slider(
        f"{cat} (£ / month)",
        min_value=0,
        max_value=int(avg * 2),
        value=int(avg),
        step=10
    )

delta = sum(adjustments.values()) - categories.sum()
simulated = baseline - np.arange(1, 7) * delta

st.line_chart(simulated)
st.markdown('</div>', unsafe_allow_html=True)
