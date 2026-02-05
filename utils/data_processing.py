import pandas as pd
import re

# Category keywords (semantic + merchant-based)
CATEGORY_KEYWORDS = {
    "Groceries": [
        "tesco", "asda", "sainsbury", "aldi", "lidl",
        "supermarket", "costcutter", "food center", "food and wine",
        "pick n save"
    ],

    "Food": [
        "restaurant", "cafe", "coffee", "pizza", "kebab",
        "subway", "deliveroo", "uber eats", "biryani", "chicken",
        "peri peri", "greggs", "wetherspoon", "pub", "pret", "nando"
    ],

    "Transport": [
        "tfl", "train", "bus", "uber", "bolt",
        "tube", "journey", "trip", "transport"
    ],

    "Shopping": [
        "amazon", "asos", "zara", "store", "retail","laptop", 
        "computer", "electronics", "currys", "pc world"
    ],

    "Subscriptions": [
        "netflix", "spotify", "subscription"
    ],

    "Rent": [
        "rent", "landlord", "housing"
    ],

    "Cash": [
        "cash withdrawal", "atm"
    ],

    "Income": [
        "salary", "payroll", "income", "bonus",
        "bac", "deposit", "sent from", "transfer in", "received"
    ],
}


# Column normalisation

def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]

    rename_map = {
        "transaction date": "date",
        "posting date": "date",
        "value date": "date",
        "details": "description",
        "narrative": "description",
        "merchant": "description",
        "reference": "description",
        "value": "amount",
        "amount (£)": "amount",
        "transaction amount": "amount",
        "money in": "credit",
        "money out": "debit",
        "credit": "credit",
        "debit": "debit",
    }

    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    return df


# Text cleaning helper

def clean_description(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\d+", " ", text)
    text = re.sub(r"[^\w\s]", " ", text)
    return text

# Categorisation logic

def categorise(description: str, amount: float) -> str:
    desc = clean_description(description)

    if amount > 0:
        return "Income"

    for category, keywords in CATEGORY_KEYWORDS.items():
        if category == "Income":
            continue
        if any(k in desc for k in keywords):
            return category

    return "Other"

# Main cleaning pipeline

def clean_and_prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = normalise_columns(df)

    # Build amount column if missing
    if "amount" not in df.columns:
        if "credit" in df.columns or "debit" in df.columns:
            credit = pd.to_numeric(df.get("credit", 0), errors="coerce").fillna(0)
            debit = pd.to_numeric(df.get("debit", 0), errors="coerce").fillna(0)
            df["amount"] = credit - debit
        else:
            raise ValueError(
                "Unsupported bank statement format. "
                "CSV must contain either an amount column or debit/credit columns."
            )

    required = {"date", "description", "amount"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = df[["date", "description", "amount"]].copy()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    df = df.dropna(subset=["date", "amount"])

    df["category"] = df.apply(
           lambda row: categorise(row["description"], row["amount"]),
        axis=1
    )

    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    return df
