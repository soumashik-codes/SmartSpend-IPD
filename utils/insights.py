import pandas as pd
from sklearn.ensemble import IsolationForest

def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flags unusual transactions using IsolationForest.
    Features: amount magnitude + day-of-month (simple, stable for IPD).
    """
    if df.empty:
        return df

    d = df.copy()
    d["date"] = pd.to_datetime(d["date"])
    d["abs_amount"] = d["amount"].abs()
    d["day"] = d["date"].dt.day

    X = d[["abs_amount", "day"]].fillna(0)

    model = IsolationForest(
        n_estimators=200,
        contamination=0.05,
        random_state=42
    )
    preds = model.fit_predict(X) 
    d["is_anomaly"] = (preds == -1)
    return d
