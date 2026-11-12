"""
Modul Pelatihan, Tuning, & Evaluasi 4 Algoritma Regresi Machine Learning
Membaca data langsung dari Data Warehouse SQLite (tobakost_warehouse.db)
"""
import os
import json
import pickle
import sqlite3
import tempfile
import pandas as pd
import numpy as np
import sklearn

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

if __package__:
    from .features import FEATURE_COLS, add_model_features, build_feature_frame
else:
    from features import FEATURE_COLS, add_model_features, build_feature_frame

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "tobakost_warehouse.db")
MODEL_DIR = os.path.join(BASE_DIR, "models")
REGISTRY_DIR = os.path.join(MODEL_DIR, "registry")

def load_data_from_dw():
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM vw_mart_kos_lengkap", conn)
    return add_model_features(df)

def evaluate_predictions(y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100.0
    r2 = r2_score(y_true, y_pred)
    return {"MAE": round(float(mae), 0), "RMSE": round(float(rmse), 0), "MAPE": round(float(mape), 2), "R2": round(float(r2), 4)}

def train_and_save():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"SQLite Data Warehouse tidak ditemukan: {DB_PATH}")
    df = load_data_from_dw()
    X = build_feature_frame(df)
    y = df["harga_bulanan_norm"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

    models = {
        "Linear Regression (Baseline)": LinearRegression(),
        "Ridge Regression (L2 Tuned)": Ridge(alpha=2.0),
        "Random Forest Regressor (Tuned)": RandomForestRegressor(
            n_estimators=150, max_depth=6, min_samples_split=8, random_state=42
        ),
        "Gradient Boosting / XGBoost (Tuned)": GradientBoostingRegressor(
            n_estimators=120, learning_rate=0.06, max_depth=3, random_state=42
        )
    }

    results = {}
    trained_objects = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        preds_test = model.predict(X_test)
        results[name] = evaluate_predictions(y_test, preds_test)
        trained_objects[name] = model
        print(f"{name:38s} -> Test R2: {results[name]['R2']:.4f} | MAE: Rp {results[name]['MAE']:,.0f}")

    best_algorithm = min(results, key=lambda name: results[name]["MAE"])
    bundle = {
        "format_version": 2,
        "sklearn_version": sklearn.__version__,
        "best_algorithm": best_algorithm,
        "model": trained_objects["Random Forest Regressor (Tuned)"],
        "all_models": trained_objects,
        "features": FEATURE_COLS,
        "metrics": results
    }

    os.makedirs(MODEL_DIR, exist_ok=True)
    outputs = [
        (os.path.join(MODEL_DIR, "best_rf_model.pkl"), "wb", lambda stream: pickle.dump(bundle, stream)),
        (os.path.join(MODEL_DIR, "metrics_summary.json"), "w", lambda stream: json.dump(results, stream, indent=2)),
    ]
    manifest = {
        "format_version": bundle["format_version"],
        "model_artifact": "models/best_rf_model.pkl",
        "metrics_artifact": "models/metrics_summary.json",
        "dataset_source": os.path.relpath(DB_PATH, BASE_DIR),
        "features": FEATURE_COLS,
        "best_algorithm": best_algorithm,
        "sklearn_version": sklearn.__version__,
    }
    os.makedirs(REGISTRY_DIR, exist_ok=True)
    outputs.append(
        (
            os.path.join(REGISTRY_DIR, "model_manifest.json"),
            "w",
            lambda stream: json.dump(manifest, stream, indent=2),
        )
    )
    for path, mode, writer in outputs:
        fd, temp_path = tempfile.mkstemp(prefix=".model-", suffix=".tmp", dir=MODEL_DIR)
        try:
            stream_context = os.fdopen(fd, mode) if "b" in mode else os.fdopen(fd, mode, encoding="utf-8")
            with stream_context as stream:
                writer(stream)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_path, path)
        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

    print(f"Model terbaik berdasarkan MAE test set: {best_algorithm}")
    print(f"Bundle model berhasil disimpan dengan scikit-learn {sklearn.__version__}.")

if __name__ == "__main__":
    train_and_save()
