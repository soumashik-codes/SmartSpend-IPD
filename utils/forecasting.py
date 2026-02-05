import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

def sarimax_forecast(monthly_series: pd.Series, steps: int = 6):
    """
    monthly_series: indexed by month datetime-like, values are net monthly change or balance.
    Returns forecast mean and confidence intervals.
    """
    s = monthly_series.dropna()
    if len(s) < 6:
        raise ValueError("Not enough monthly data for SARIMAX (need at least 6 months).")

    model = SARIMAX(
        s,
        order=(1, 1, 1),
        seasonal_order=(1, 1, 1, 12),
        enforce_stationarity=False,
        enforce_invertibility=False
    )
    res = model.fit(disp=False)
    fc = res.get_forecast(steps=steps)
    mean = fc.predicted_mean
    ci = fc.conf_int()
    return mean, ci
