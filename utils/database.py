import sqlite3
from pathlib import Path
import pandas as pd


# Database configuration
DB_DIR = Path(__file__).resolve().parents[1] / "db"
DB_PATH = DB_DIR / "smartspend.db"


def get_conn():
    DB_DIR.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            password_hash BLOB NOT NULL
        )
    """)


    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            month TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL,
            filename TEXT,
            ocr_text TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(transaction_id) REFERENCES transactions(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS receipt_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_id INTEGER NOT NULL,
            item_name TEXT,
            qty REAL,
            unit_price REAL,
            total REAL,
            FOREIGN KEY(receipt_id) REFERENCES receipts(id)
        )
    """)

    conn.commit()
    conn.close()


# Bank CSV normalisation
COLUMN_MAP = {
    "date": [
        "date", "transaction date", "posted date",
        "posting date", "value date", "transaction_datetime"
    ],
    "description": [
        "description", "details", "narrative",
        "reference", "merchant", "name", "memo"
    ],
    "amount": [
        "amount", "transaction amount",
        "value", "amount (£)", "amount (gbp)"
    ],
    "debit": ["debit", "money out", "moneyout", "withdrawal", "paid out"],
    "credit": ["credit", "money in", "moneyin", "deposit", "paid in"],
}


def _clean_colname(c: str) -> str:
    return str(c).strip().lower().replace("\ufeff", "")


def _find_column(df: pd.DataFrame, options: list[str]) -> str | None:
    for opt in options:
        opt = opt.lower()
        for col in df.columns:
            if opt == col.lower() or opt in col.lower():
                return col
    return None


def normalise_bank_csv(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [_clean_colname(c) for c in df.columns]

    date_col = _find_column(df, COLUMN_MAP["date"])
    desc_col = _find_column(df, COLUMN_MAP["description"])
    amount_col = _find_column(df, COLUMN_MAP["amount"])
    debit_col = _find_column(df, COLUMN_MAP["debit"])
    credit_col = _find_column(df, COLUMN_MAP["credit"])

    if not date_col or not desc_col:
        raise ValueError("CSV must include a date and description column")

    if amount_col:
        df["amount"] = pd.to_numeric(df[amount_col], errors="coerce")
    elif debit_col or credit_col:
        debit = pd.to_numeric(df[debit_col], errors="coerce").fillna(0) if debit_col else 0
        credit = pd.to_numeric(df[credit_col], errors="coerce").fillna(0) if credit_col else 0
        df["amount"] = credit - debit
    else:
        raise ValueError("No usable amount column found")

    df["date"] = pd.to_datetime(df[date_col], errors="coerce")
    df["description"] = df[desc_col].astype(str).fillna("")

    out = df[["date", "description", "amount"]].copy()
    out = out.dropna(subset=["date", "amount"])

    return out


# Transaction persistence (user-scoped)
def write_transactions(df: pd.DataFrame, user_id: int, replace_existing: bool = True):
    init_db()

    df = df.copy()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["date", "amount"])

    if "category" not in df.columns:
        df["category"] = "Other"
    else:
        df["category"] = df["category"].fillna("Other").astype(str)

    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df["user_id"] = user_id

    df = df[["user_id", "date", "description", "amount", "category", "month"]]

    conn = get_conn()
    cur = conn.cursor()

    if replace_existing:
        cur.execute(
            "DELETE FROM transactions WHERE user_id = ?",
            (user_id,)
        )

    cur.executemany(
        """
        INSERT INTO transactions (user_id, date, description, amount, category, month)
        VALUES (?,?,?,?,?,?)
        """,
        df.values.tolist()
    )

    conn.commit()
    conn.close()


def load_transactions(user_id: int) -> pd.DataFrame:
    init_db()
    conn = get_conn()
    df = pd.read_sql_query(
        """
        SELECT id, date, description, amount, category, month
        FROM transactions
        WHERE user_id = ?
        ORDER BY date ASC, id ASC
        """,
        conn,
        params=(user_id,)
    )
    conn.close()
    return df


# Receipt handling
def insert_receipt(transaction_id: int, filename: str, ocr_text: str) -> int:
    init_db()
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO receipts(transaction_id, filename, ocr_text) VALUES (?,?,?)",
        (transaction_id, filename, ocr_text)
    )

    receipt_id = cur.lastrowid
    conn.commit()
    conn.close()
    return receipt_id


def insert_receipt_items(receipt_id: int, items: list[dict]):
    init_db()
    conn = get_conn()
    cur = conn.cursor()

    for it in items:
        cur.execute(
            """
            INSERT INTO receipt_items(receipt_id, item_name, qty, unit_price, total)
            VALUES (?,?,?,?,?)
            """,
            (
                receipt_id,
                it.get("item_name"),
                it.get("qty"),
                it.get("unit_price"),
                it.get("total"),
            )
        )

    conn.commit()
    conn.close()

def get_receipts_for_transaction(transaction_id: int) -> pd.DataFrame:
    init_db()
    conn = get_conn()
    df = pd.read_sql_query(
        """
        SELECT id, transaction_id, filename, ocr_text, created_at
        FROM receipts
        WHERE transaction_id = ?
        ORDER BY created_at DESC
        """,
        conn,
        params=(transaction_id,)
    )
    conn.close()
    return df


def get_items_for_receipt(receipt_id: int) -> pd.DataFrame:
    init_db()
    conn = get_conn()
    df = pd.read_sql_query(
        """
        SELECT item_name, qty, unit_price, total
        FROM receipt_items
        WHERE receipt_id = ?
        """,
        conn,
        params=(receipt_id,)
    )
    conn.close()
    return df
