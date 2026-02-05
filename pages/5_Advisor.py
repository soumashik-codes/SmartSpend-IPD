import streamlit as st
import pandas as pd

from utils.style import apply_global_style
apply_global_style()

from utils.auth import require_login, logout_user
require_login()

with st.sidebar:
    st.markdown(f"👤 **{st.session_state.first_name} {st.session_state.last_name}**")
    if st.button("🚪 Log out"):
        logout_user()
        st.switch_page("pages/0_Login.py")

from utils.database import load_transactions
from utils.insights import detect_anomalies

st.set_page_config(
    page_title="SmartSpend Advisor",
    page_icon="💡",
    layout="wide"
)

st.markdown(
    """
    <h1 style="margin-bottom: 0.25rem;">💡 SmartSpend Advisor</h1>
    <p style="color: #6b7280; margin-bottom: 1.5rem;">
        Explainable financial insights based on your spending behaviour.
    </p>
    """,
    unsafe_allow_html=True
)

# Load data
df = load_transactions(st.session_state.user_id)
if df.empty:
    st.warning("Upload transactions to generate insights.")
    st.stop()

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
df = df.dropna(subset=["date", "amount"]).copy()

if "category" not in df.columns:
    df["category"] = "Other"

df["category"] = df["category"].fillna("Other").astype(str)
df["description"] = df.get("description", "").astype(str)

# Helpers
def _money(x: float) -> str:
    return f"£{x:,.2f}"

def _safe_median(series: pd.Series) -> float | None:
    series = pd.to_numeric(series, errors="coerce").dropna()
    if series.empty:
        return None
    return float(series.median())

def _recent_baseline(series: pd.Series, k: int = 10) -> float | None:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return None
    return float(s.tail(k).median())

def _near_equal(a: float, b: float, pct: float = 0.05) -> bool:
    if b == 0:
        return abs(a) < 1e-9
    return abs(a - b) / abs(b) <= pct

def _merchant_hint(desc: str) -> str:
    d = (desc or "").strip()
    if not d:
        return "this transaction"
    short = d.replace(",", " ").replace("  ", " ").strip()
    return short[:45] + ("…" if len(short) > 45 else "")

# Detect anomalies (ML signal) + make unique
df_anom = detect_anomalies(df)
if "is_anomaly" not in df_anom.columns:
    df_anom["is_anomaly"] = False

anom_rows = (
    df_anom[df_anom["is_anomaly"] == True]
    .sort_values("date", ascending=False)
    .drop_duplicates(subset=["date", "description", "amount"])
    .head(6)
)

# Explain anomalies in a fintech-ish way
def explain_transaction(row: pd.Series, full_df: pd.DataFrame) -> dict | None:
    amount = float(row["amount"])
    category = str(row.get("category", "Other"))
    desc = str(row.get("description", ""))
    label = _merchant_hint(desc)

    # Income insight
    if amount > 0:
        incomes = full_df[full_df["amount"] > 0].sort_values("date")
        baseline = _recent_baseline(incomes["amount"], k=8)

        # If not enough income history, don’t overclaim
        if baseline is None or len(incomes) < 3:
            return {
                "type": "positive",
                "title": "Income received",
                "message": f"You received {_money(amount)} ({label}). Logged as income for your timeline."
            }

        if _near_equal(amount, baseline, pct=0.06):
            return None

        # Big income = positive, small income = heads-up
        if amount >= baseline * 1.35:
            return {
                "type": "positive",
                "title": "Higher-than-usual income",
                "message": f"You received {_money(amount)} ({label}), which is above your recent typical income (~{_money(baseline)})."
            }

        if amount <= baseline * 0.70:
            return {
                "type": "alert",
                "title": "Lower-than-usual income",
                "message": f"You received {_money(amount)} ({label}), which is below your recent typical income (~{_money(baseline)})."
            }

        return None

    # Expense insight
    spend = abs(amount)
    expenses = full_df[full_df["amount"] < 0].sort_values("date")

    cat_hist = expenses[expenses["category"] == category]["amount"].abs()
    cat_baseline = _recent_baseline(cat_hist, k=12)

    overall_baseline = _recent_baseline(expenses["amount"].abs(), k=20)

    baseline_used = None
    baseline_label = None

    if cat_baseline is not None and cat_hist.dropna().shape[0] >= 4:
        baseline_used = cat_baseline
        baseline_label = f"your typical {category} spend"
    elif overall_baseline is not None:
        baseline_used = overall_baseline
        baseline_label = "your typical spend"

    if baseline_used is None:
        return {
            "type": "alert",
            "title": "Unusual expense recorded",
            "message": f"You spent {_money(spend)} ({label}). Not enough history yet to compare against your normal spending."
        }

    # Skip near-equal comparisons
    if _near_equal(spend, baseline_used, pct=0.08):
        return None

    # Strong anomaly threshold (fintech style: don’t alert for small changes)
    if spend >= baseline_used * 2.5 and spend >= 25:
        return {
            "type": "alert",
            "title": "Unusually large expense",
            "message": f"You spent {_money(spend)} ({label}). That’s much higher than {baseline_label} (~{_money(baseline_used)})."
        }

    # Medium anomaly as a softer “Heads-up”
    if spend >= baseline_used * 1.8 and spend >= 15:
        return {
            "type": "alert",
            "title": "Higher-than-usual spend",
            "message": f"{_money(spend)} ({label}) is higher than {baseline_label} (~{_money(baseline_used)})."
        }

    return None

# Build insights
insights: list[dict] = []

for _, r in anom_rows.iterrows():
    item = explain_transaction(r, df_anom)
    if item:
        insights.append(item)

# Monthly trend insight (more “real app”)
df["month"] = df["date"].dt.to_period("M").astype(str)
monthly_spend = (
    df[df["amount"] < 0]
    .groupby("month")["amount"]
    .sum()
    .abs()
    .sort_index()
)

if len(monthly_spend) >= 2:
    last = float(monthly_spend.iloc[-1])
    prev = float(monthly_spend.iloc[-2])
    if prev > 0:
        change_pct = (last - prev) / prev
        if change_pct <= -0.10:
            insights.append({
                "type": "positive",
                "title": "Spending decreased this month",
                "message": f"Your spending is down {_money(prev - last)} (≈{abs(change_pct)*100:.0f}%) compared to last month."
            })
        elif change_pct >= 0.15:
            insights.append({
                "type": "alert",
                "title": "Spending increased this month",
                "message": f"Your spending is up {_money(last - prev)} (≈{abs(change_pct)*100:.0f}%) compared to last month."
            })

# Generic suggestion (kept, but less generic tone)
insights.append({
    "type": "suggestion",
    "title": "Keep an eye on top categories",
    "message": "Your biggest categories drive most of your month-to-month budget changes."
})

# Deduplicate + limit cards
seen = set()
clean_insights = []
for ins in insights:
    key = (ins["type"], ins["title"], ins["message"])
    if key not in seen:
        seen.add(key)
        clean_insights.append(ins)

# Order: alerts, positives, suggestions
priority = {"alert": 0, "positive": 1, "suggestion": 2}
clean_insights = sorted(clean_insights, key=lambda x: priority.get(x["type"], 9))[:6]

# Display
cols = st.columns(3)

for i, ins in enumerate(clean_insights):
    color = {
        "alert": "#dc2626",
        "positive": "#16a34a",
        "suggestion": "#2563eb"
    }[ins["type"]]

    with cols[i % 3]:
        st.markdown(
            f"""
            <div class="card">
                <p style="color:{color}; font-weight:600;">{ins['type'].capitalize()}</p>
                <p style="font-weight:600; margin-bottom:0.35rem;">{ins['title']}</p>
                <small style="color:#6b7280; line-height:1.4;">{ins['message']}</small>
            </div>
            """,
            unsafe_allow_html=True
        )
