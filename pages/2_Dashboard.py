import streamlit as st
import pandas as pd
import plotly.express as px

from utils.style import apply_global_style
apply_global_style()

from utils.auth import require_login, logout_user
require_login()

with st.sidebar:
    st.markdown(
        f"👤 **{st.session_state.first_name} {st.session_state.last_name}**"
    )
    if st.button("🚪 Log out"):
        logout_user()
        st.switch_page("pages/0_Login.py")

from utils.database import load_transactions
from utils.insights import detect_anomalies

st.set_page_config(
    page_title="Dashboard",
    page_icon="📊",
    layout="wide"
)

# Header
first_name = st.session_state.get("first_name", "")

st.markdown(
    f"""
    <h1 style="margin-bottom:0.25rem;">
        👋 Welcome back{',' if first_name else ''} {first_name}
    </h1>
    <p style="color:#6b7280; margin-bottom:1.5rem;">
        Here’s an overview of your recent financial activity.
    </p>
    """,
    unsafe_allow_html=True
)

# Load data
df = load_transactions(st.session_state.user_id)

# Data safety check
if df.empty:
    st.warning("No transactions available yet. Please upload a CSV file to get started.")
    st.stop()

if "category" not in df.columns:
    df["category"] = "Other"
else:
    df["category"] = df["category"].fillna("Other")

# Data prep
df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date", "amount"])
df["month"] = df["date"].dt.to_period("M").astype(str)

# Running balance over time
df = df.sort_values("date")
df["running_balance"] = df["amount"].cumsum()

# KPIs
total_income = df[df["amount"] > 0]["amount"].sum()
total_expenses = df[df["amount"] < 0]["amount"].sum()
net_change = total_income + total_expenses

k1, k2, k3 = st.columns(3)

def kpi_card(title, value, color):
    st.markdown(
        f"""
        <div class="card">
            <p style="color:#6b7280; margin-bottom:0.25rem;">{title}</p>
            <h2 style="color:{color}; margin:0;">£{value:,.2f}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

with k1:
    kpi_card("Net Balance Change (Period)", net_change, "#2563eb")

with k2:
    kpi_card("Total Income", total_income, "#16a34a")

with k3:
    kpi_card("Total Expenses", abs(total_expenses), "#dc2626")

# Charts
left, right = st.columns([2, 1])

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Net Balance Change (Monthly)")

    monthly = (
        df.groupby("month")["amount"]
        .sum()
        .reset_index()
        .sort_values("month")
    )
    

    fig_balance = px.line(
        monthly,
        x="month",
        y="amount",
        markers=True,
        labels={
            "amount": "Net Balance Change (Income − Expenses) (£)",
            "month": "Month (Aggregated)"
        }
    )

    st.plotly_chart(fig_balance, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("Running Balance Over Time")

fig_running = px.line(
    df,
    x="date",
    y="running_balance",
    labels={
        "running_balance": "Balance (£)",
        "date": "Date"
    }
)

st.plotly_chart(fig_running, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Spending by Category")

    spending = (
        df[df["amount"] < 0]
        .groupby("category")["amount"]
        .sum()
        .abs()
        .reset_index()
    )

    fig_cat = px.pie(
        spending,
        names="category",
        values="amount",
        hole=0.6
    )

    st.plotly_chart(fig_cat, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Unusual activity 
st.markdown('<div class="card">', unsafe_allow_html=True)

df_anom = detect_anomalies(df)

if "is_anomaly" not in df_anom.columns:
    df_anom["is_anomaly"] = False

anomalies = df_anom[df_anom["is_anomaly"] == True]

expense_anomalies = anomalies[anomalies["amount"] < 0]
income_anomalies = anomalies[anomalies["amount"] > 0]

if expense_anomalies.empty and income_anomalies.empty:
    st.success("No unusual patterns detected. Your activity looks consistent.")
else:
    if not expense_anomalies.empty:
        st.subheader("💸 Unusually High Spending")
        st.caption("These expenses are significantly higher than your typical spending.")
        st.dataframe(
            expense_anomalies[
                ["date", "description", "category", "amount"]
            ].sort_values("amount"),
            use_container_width=True
        )

    if not income_anomalies.empty:
        st.subheader("💰 Higher-than-Usual Income Received")
        st.caption("These income transactions are larger than your typical deposits.")
        st.dataframe(
            income_anomalies[
                ["date", "description", "category", "amount"]
            ].sort_values("amount", ascending=False),
            use_container_width=True
        )

st.markdown('</div>', unsafe_allow_html=True)

# Recent transactions
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("Recent Transactions")

st.dataframe(
    df.sort_values("date", ascending=False).head(10),
    use_container_width=True
)

st.markdown('</div>', unsafe_allow_html=True)
