"""Analytics transformations shared by dashboard endpoints."""

import numpy as np

from models.features import FEATURE_COLS


def enrich_price_analysis(df, models):
    """Add model predictions and pricing diagnostics to an analytics frame."""
    df = df.copy()
    df["pred_rf"] = np.round(
        models["Random Forest Regressor (Tuned)"].predict(df[FEATURE_COLS])
    ).astype(int)
    df["pred_ridge"] = np.round(
        models["Ridge Regression (L2 Tuned)"].predict(df[FEATURE_COLS])
    ).astype(int)
    df["pred_gb"] = np.round(
        models["Gradient Boosting / XGBoost (Tuned)"].predict(df[FEATURE_COLS])
    ).astype(int)
    df["pred_ols"] = np.round(
        models["Linear Regression (Baseline)"].predict(df[FEATURE_COLS])
    ).astype(int)
    df["selisih_rp"] = df["harga_bulanan_norm"] - df["pred_rf"]
    df["selisih_persen"] = ((df["selisih_rp"] / df["pred_rf"]) * 100.0).round(2)
    df["abs_error"] = df["selisih_rp"].abs()
    df["status_kewajaran"] = np.where(
        df["selisih_persen"] < -6.0,
        "Underpriced (Sangat Hemat)",
        np.where(
            df["selisih_persen"] > 6.0,
            "Overpriced (Kemahalan)",
            "Fair Price (Harga Wajar)",
        ),
    )
    return df


def feature_importance(model):
    """Return a stable, display-ready feature importance payload."""
    pairs = sorted(
        zip(FEATURE_COLS, model.feature_importances_),
        key=lambda item: item[1],
        reverse=True,
    )
    return [
        {"feature": name, "importance_pct": round(float(value) * 100.0, 2)}
        for name, value in pairs[:12]
    ]
