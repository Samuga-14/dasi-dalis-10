"""
TobaKost Analytics & ML — Backend Server (Arsitektur Paket A)
Stack: Python built-in HTTP REST API + SQLite Star Schema Data Warehouse + Pre-trained ML Models (.pkl)
Frontend: HTML5 + Tailwind CSS + Chart.js + Leaflet.js (frontend/index.html)

Cara Menjalankan:
1. Klik tombol Run Python File di VS Code, ATAU
2. Ketik di terminal: python server.py
Server akan otomatis berjalan di http://localhost:8000 dan membuka browser.
"""
import os
import sys
import json
import logging
import math
import pickle
import sqlite3
import subprocess
import webbrowser
from http import HTTPStatus
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import numpy as np
import pandas as pd
import sklearn

from models.features import FEATURE_COLS, add_derived_features, add_model_features, build_feature_frame

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "tobakost_warehouse.db")
MODEL_PKL_PATH = os.path.join(BASE_DIR, "models", "best_rf_model.pkl")
FRONTEND_HTML_PATH = os.path.join(BASE_DIR, "frontend", "index.html")
ETL_SCRIPT_PATH = os.path.join(BASE_DIR, "etl", "run_etl_star_schema.py")
TRAIN_SCRIPT_PATH = os.path.join(BASE_DIR, "models", "train_models.py")
LOGGER = logging.getLogger("tobakost")
MODEL_BUNDLE = None


class RequestValidationError(ValueError):
    """Raised when an API request contains invalid user input."""


class ModelUnavailableError(RuntimeError):
    """Raised when the model artifact cannot be loaded safely."""


def ensure_database():
    """Ensure the SQLite warehouse exists without retraining models implicitly."""
    if not os.path.exists(DB_PATH):
        print("[INIT] Membangun SQLite Star Schema Data Warehouse...")
        subprocess.run([sys.executable, ETL_SCRIPT_PATH], check=True, cwd=BASE_DIR)


def load_model_bundle():
    global MODEL_BUNDLE
    ensure_database()
    if MODEL_BUNDLE is not None:
        return MODEL_BUNDLE
    if not os.path.exists(MODEL_PKL_PATH):
        raise ModelUnavailableError(
            "File model tidak ditemukan. Jalankan `python models/train_models.py` dari folder proyek untuk melatih dan menyimpan model."
        )
    try:
        with open(MODEL_PKL_PATH, "rb") as f:
            bundle = pickle.load(f)
    except Exception as exc:
        LOGGER.exception("Gagal memuat bundle model dari %s", MODEL_PKL_PATH)
        raise ModelUnavailableError(
            "File model tidak kompatibel atau rusak. Jalankan `python models/train_models.py` dengan dependensi dari requirements.txt."
        ) from exc

    if not isinstance(bundle, dict):
        raise ModelUnavailableError("Format bundle model tidak valid; latih ulang dengan models/train_models.py.")
    artifact_version = bundle.get("sklearn_version")
    if artifact_version != sklearn.__version__:
        raise ModelUnavailableError(
            f"Model dibuat dengan scikit-learn {artifact_version or 'versi tidak tercatat'}, "
            f"tetapi runtime menggunakan {sklearn.__version__}. Jalankan `python models/train_models.py`."
        )
    if bundle.get("features") != FEATURE_COLS:
        raise ModelUnavailableError("Urutan fitur model tidak sesuai dengan fitur API; latih ulang model.")
    expected_models = {
        "Linear Regression (Baseline)",
        "Ridge Regression (L2 Tuned)",
        "Random Forest Regressor (Tuned)",
        "Gradient Boosting / XGBoost (Tuned)"
    }
    if set(bundle.get("all_models", {})) != expected_models:
        raise ModelUnavailableError("Bundle tidak memuat keempat model yang didukung.")
    if set(bundle.get("metrics", {})) != expected_models:
        raise ModelUnavailableError("Metrik model tidak lengkap atau tidak konsisten dengan bundle.")
    MODEL_BUNDLE = bundle
    return MODEL_BUNDLE


def _validate_database():
    ensure_database()
    required_objects = {
        "fact_sewa_kos", "dim_lokasi", "dim_spesifikasi_kamar",
        "dim_fasilitas_aturan", "dim_kontrak_sewa", "vw_mart_kos_lengkap"
    }
    with sqlite3.connect(DB_PATH) as conn:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise sqlite3.DatabaseError(f"SQLite integrity check gagal: {integrity}")
        objects = {
            row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
            )
        }
        missing = required_objects - objects
        if missing:
            raise sqlite3.DatabaseError(f"Objek Star Schema tidak ditemukan: {', '.join(sorted(missing))}")
        row_count = conn.execute("SELECT COUNT(*) FROM vw_mart_kos_lengkap").fetchone()[0]
    return int(row_count)


def _json_safe(value):
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def get_full_analytics_payload():
    """Mengambil seluruh data dari SQLite Star Schema + prediksi ML untuk Frontend."""
    bundle = load_model_bundle()
    all_models = bundle["all_models"]
    metrics = bundle["metrics"]

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM vw_mart_kos_lengkap", conn)

        tables_info = {}
        for tbl in ["fact_sewa_kos", "dim_lokasi", "dim_spesifikasi_kamar", "dim_fasilitas_aturan", "dim_kontrak_sewa"]:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            sample_df = pd.read_sql_query(f"SELECT * FROM {tbl} LIMIT 25", conn)
            tables_info[tbl] = {
                "count": int(cnt),
                "columns": list(sample_df.columns),
                "rows": sample_df.to_dict(orient="records")
            }

    df = add_model_features(df)
    X = build_feature_frame(df)
    df["pred_rf"] = np.round(all_models["Random Forest Regressor (Tuned)"].predict(X)).astype(int)
    df["pred_ridge"] = np.round(all_models["Ridge Regression (L2 Tuned)"].predict(X)).astype(int)
    df["pred_gb"] = np.round(all_models["Gradient Boosting / XGBoost (Tuned)"].predict(X)).astype(int)
    df["pred_ols"] = np.round(all_models["Linear Regression (Baseline)"].predict(X)).astype(int)

    df["selisih_rp"] = df["harga_bulanan_norm"] - df["pred_rf"]
    df["selisih_persen"] = ((df["selisih_rp"] / df["pred_rf"]) * 100.0).round(2)
    df["abs_error"] = df["selisih_rp"].abs()
    df["status_kewajaran"] = np.where(
        df["selisih_persen"] < -6.0, "Underpriced (Sangat Hemat)",
        np.where(df["selisih_persen"] > 6.0, "Overpriced (Kemahalan)", "Fair Price (Harga Wajar)")
    )

    # Feature importance dari Random Forest & Gradient Boosting
    rf_model = all_models["Random Forest Regressor (Tuned)"]
    fi_pairs = sorted(zip(FEATURE_COLS, rf_model.feature_importances_), key=lambda x: x[1], reverse=True)
    feature_importance = [{"feature": k, "importance_pct": round(float(v) * 100.0, 2)} for k, v in fi_pairs[:12]]

    return _json_safe({
        "status": "ok",
        "architecture": "Paket A: Python REST API + SQLite Star Schema DW + HTML5/Tailwind/Chart.js/Leaflet",
        "total_records": int(len(df)),
        "best_algorithm": bundle["best_algorithm"],
        "model_version": bundle["sklearn_version"],
        "metrics": metrics,
        "feature_importance": feature_importance,
        "star_schema": tables_info,
        "records": df.to_dict(orient="records")
    })


def _read_numeric(payload, name, default, *, integer=False, binary=False):
    value = payload[name] if name in payload else default
    if value is None or value == "" or isinstance(value, bool):
        raise RequestValidationError(f"Fitur '{name}' harus berupa angka yang valid.")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise RequestValidationError(f"Fitur '{name}' harus berupa angka yang valid.") from exc
    if not math.isfinite(numeric):
        raise RequestValidationError(f"Fitur '{name}' harus berupa angka finite.")
    if numeric < 0:
        raise RequestValidationError(f"Fitur '{name}' tidak boleh negatif.")
    if binary and numeric not in (0, 1):
        raise RequestValidationError(f"Fitur '{name}' hanya menerima nilai 0 atau 1.")
    if integer and not numeric.is_integer():
        raise RequestValidationError(f"Fitur '{name}' harus berupa bilangan bulat.")
    if name == "jumlah_lantai" and numeric < 1:
        raise RequestValidationError("Fitur 'jumlah_lantai' minimal bernilai 1.")
    if name == "luas_kamar_m2" and numeric == 0:
        raise RequestValidationError("Fitur 'luas_kamar_m2' harus lebih besar dari 0.")
    return int(numeric) if integer or binary else numeric


def predict_single_kos(payload):
    """Predict with each available model using the shared training feature order."""
    bundle = load_model_bundle()
    all_models = bundle["all_models"]
    metrics = bundle["metrics"]

    binary_defaults = {
        "km_dalam": 1, "is_ac": 0, "is_wifi": 1, "ada_tv": 0,
        "ada_meja_belajar": 1, "parkir_mobil": 0, "dapur_pribadi": 0,
        "dapur_bersama": 1, "keamanan_penjaga": 0, "keamanan_cctv": 1,
        "bebas_24jam": 1, "listrik_termasuk": 0, "is_tahunan": 0
    }
    values = {
        "luas_kamar_m2": _read_numeric(payload, "luas_kamar_m2", 12),
        "jumlah_lantai": _read_numeric(payload, "jumlah_lantai", 1, integer=True),
        **{
            name: _read_numeric(payload, name, default, binary=True)
            for name, default in binary_defaults.items()
        },
        "jarak_ke_kampus_kantor_sekolah_terdekat_km": _read_numeric(
            payload, "jarak_ke_kampus_kantor_sekolah_terdekat_km", 0.8
        ),
        "jarak_ke_pasar_km": _read_numeric(payload, "jarak_ke_pasar_km", 1.0),
        "jarak_krusial_km": _read_numeric(payload, "jarak_krusial_km", 1.5),
        "jarak_ke_jalan_raya_m": _read_numeric(payload, "jarak_ke_jalan_raya_m", 100)
    }

    row_df = add_derived_features(pd.DataFrame([values]))
    skor_fas = float(row_df.iloc[0]["skor_kelengkapan_fasilitas"])
    indeks_aks = float(row_df.iloc[0]["indeks_aksesibilitas_lokasi"])
    row_df = build_feature_frame(row_df)

    selected_algo = payload.get("algorithm", bundle["best_algorithm"])
    if not isinstance(selected_algo, str) or selected_algo not in all_models:
        raise RequestValidationError("Algoritma tidak dikenal. Pilih salah satu algoritma yang tersedia.")

    predictions = {}
    for name, model in all_models.items():
        try:
            output = np.asarray(model.predict(row_df)).reshape(-1)
            if output.size != 1 or not np.isfinite(output[0]):
                raise ValueError("Model tidak menghasilkan satu prediksi numerik finite.")
            predictions[name] = int(round(float(output[0])))
        except Exception as exc:
            LOGGER.exception("Prediksi model gagal: %s", name)
            predictions[name] = {"status": "error", "message": str(exc)}

    selected_result = predictions[selected_algo]
    if isinstance(selected_result, dict):
        return {
            "status": "partial",
            "selected_algorithm": selected_algo,
            "predicted_monthly_rp": None,
            "predicted_yearly_rp": None,
            "range_min_rp": None,
            "range_max_rp": None,
            "mae_rp": None,
            "skor_kelengkapan_fasilitas": skor_fas,
            "indeks_aksesibilitas_lokasi": indeks_aks,
            "best_algorithm": bundle["best_algorithm"],
            "all_predictions": predictions
        }

    mae_val = int(metrics[selected_algo]["MAE"])
    return {
        "status": "ok" if all(not isinstance(prediction, dict) for prediction in predictions.values()) else "partial",
        "selected_algorithm": selected_algo,
        "predicted_monthly_rp": selected_result,
        "predicted_yearly_rp": selected_result * 12,
        "range_min_rp": selected_result - mae_val,
        "range_max_rp": selected_result + mae_val,
        "mae_rp": mae_val,
        "skor_kelengkapan_fasilitas": skor_fas,
        "indeks_aksesibilitas_lokasi": indeks_aks,
        "best_algorithm": bundle["best_algorithm"],
        "all_predictions": predictions
    }


def insert_new_kos_to_dw(payload):
    """Menyimpan unit kos baru langsung ke tabel fact_sewa_kos di SQLite Data Warehouse."""
    ensure_database()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    total_now = cur.execute("SELECT COUNT(*) FROM fact_sewa_kos").fetchone()[0]
    new_id = f"TOBA_{total_now + 1:03d}"
    nama_kost = str(payload.get("nama_kost", f"Kost Baru Toba {total_now + 1}")).strip()
    kecamatan = str(payload.get("kecamatan", "Laguboti")).strip()
    desa = str(payload.get("desa_kelurahan", "Sitoluama")).strip()

    # Cari id_lokasi yang cocok di dim_lokasi atau ambil default
    lok_row = cur.execute(
        "SELECT id_lokasi FROM dim_lokasi WHERE kecamatan = ? LIMIT 1", (kecamatan,)
    ).fetchone()
    id_lokasi = lok_row[0] if lok_row else "LOK_001"

    tipe_km = "dalam" if int(payload.get("km_dalam", 1)) == 1 else "luar"
    ac_str = "ac" if int(payload.get("is_ac", 0)) == 1 else "non-ac"
    spk_row = cur.execute(
        "SELECT id_spesifikasi FROM dim_spesifikasi_kamar WHERE tipe_kamar_mandi = ? AND ac_non_ac = ? LIMIT 1",
        (tipe_km, ac_str)
    ).fetchone()
    id_spesifikasi = spk_row[0] if spk_row else "SPK_001"

    wifi_str = "wifi" if int(payload.get("is_wifi", 1)) == 1 else "non-wifi"
    atr_row = cur.execute(
        "SELECT id_aturan FROM dim_fasilitas_aturan WHERE wifi_non_wifi = ? LIMIT 1", (wifi_str,)
    ).fetchone()
    id_aturan = atr_row[0] if atr_row else "ATR_001"

    id_kontrak = "KTK_01"
    harga_bulanan = int(payload.get("harga_bulanan_norm", 700000))
    jarak_kampus = float(payload.get("jarak_ke_kampus_kantor_sekolah_terdekat_km", 0.8))
    jarak_pasar = float(payload.get("jarak_ke_pasar_km", 1.0))
    jarak_rs = float(payload.get("jarak_krusial_km", 1.5))
    jarak_jalan = int(payload.get("jarak_ke_jalan_raya_m", 100))

    skor_fas = round(int(payload.get("km_dalam", 1)) * 2.5 + int(payload.get("is_ac", 0)) * 3.5 + int(payload.get("is_wifi", 1)) * 1.5 + 1.5, 1)
    indeks_aks = round((1.0 / (1.0 + jarak_kampus)) * 35 + (1.0 / (1.0 + jarak_pasar)) * 25 + 30.0, 1)

    cur.execute("""
        INSERT INTO fact_sewa_kos (
            id_kost, kode_unit_kos, nama_kost, id_lokasi, id_spesifikasi, id_aturan, id_kontrak,
            harga_sewa, harga_bulanan_norm,
            jarak_ke_kampus_kantor_sekolah_terdekat_km, jarak_ke_pasar_km,
            jarak_krusial_km, jarak_laundry_m, jarak_ibadah_m, jarak_pusat_kota_m, jarak_ke_jalan_raya_m,
            skor_kelengkapan_fasilitas, indeks_aksesibilitas_lokasi,
            latitude, longitude, source_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        new_id, f"KOS_NEW_{total_now+1}", f"{nama_kost} ({desa})",
        id_lokasi, id_spesifikasi, id_aturan, id_kontrak,
        harga_bulanan, harga_bulanan,
        jarak_kampus, jarak_pasar, jarak_rs, 250, 400, 1500, jarak_jalan,
        skor_fas, indeks_aks, 2.3855, 99.1482, "Input Web Paket A"
    ))
    conn.commit()
    conn.close()
    return {"status": "ok", "new_id_kost": new_id, "message": f"Unit {new_id} ({nama_kost}) berhasil disimpan ke SQLite Star Schema Data Warehouse."}


class PaketARequestHandler(SimpleHTTPRequestHandler):
    """HTTP Handler ringan yang melayani Frontend HTML5 dan REST API SQLite + ML."""

    def _send_json(self, data, status=200):
        raw = json.dumps(_json_safe(data), ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Vary", "Origin")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _read_json_body(self):
        length_text = self.headers.get("Content-Length", "0")
        try:
            length = int(length_text)
        except ValueError as exc:
            raise RequestValidationError("Content-Length tidak valid.") from exc
        if length < 0 or length > 1024 * 1024:
            raise RequestValidationError("Ukuran request harus kurang dari 1 MB.")
        if length == 0:
            return {}
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RequestValidationError("Body harus berisi JSON UTF-8 yang valid.") from exc
        if not isinstance(payload, dict):
            raise RequestValidationError("Body JSON harus berupa object.")
        return payload

    def _send_api_exception(self, exc):
        if isinstance(exc, RequestValidationError):
            self._send_json({"status": "error", "message": str(exc)}, HTTPStatus.BAD_REQUEST)
        elif isinstance(exc, ModelUnavailableError):
            LOGGER.exception("Model tidak tersedia untuk request %s", self.path)
            self._send_json({"status": "error", "message": str(exc)}, HTTPStatus.SERVICE_UNAVAILABLE)
        else:
            LOGGER.exception("API gagal memproses request %s", self.path)
            self._send_json(
                {"status": "error", "message": "Terjadi kesalahan internal. Periksa log server untuk traceback."},
                HTTPStatus.INTERNAL_SERVER_ERROR
            )

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Vary", "Origin")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/health":
            database_status = "connected"
            model_status = "loaded"
            result = {"status": "ok", "database": database_status, "model": model_status}
            try:
                result["database_records"] = _validate_database()
            except Exception as exc:
                LOGGER.exception("Health check gagal memeriksa SQLite Data Warehouse")
                result["database"] = "error"
                result["database_error"] = str(exc)
            try:
                bundle = load_model_bundle()
                result["model_version"] = bundle["sklearn_version"]
                result["best_algorithm"] = bundle["best_algorithm"]
            except Exception as exc:
                LOGGER.exception("Health check gagal memuat model")
                result["model"] = "error"
                result["model_error"] = str(exc)
            if result["database"] != "connected" or result["model"] != "loaded":
                result["status"] = "degraded"
            self._send_json(result)
            return

        if path in ("/", "/index.html"):
            if os.path.exists(FRONTEND_HTML_PATH):
                try:
                    with open(FRONTEND_HTML_PATH, "rb") as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                except OSError as exc:
                    LOGGER.exception("Gagal menyajikan frontend")
                    self._send_json({"status": "error", "message": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            self._send_json({"error": "frontend/index.html tidak ditemukan"}, 404)
            return

        if path == "/api/data":
            try:
                self._send_json(get_full_analytics_payload())
            except Exception as exc:
                self._send_api_exception(exc)
            return

        if path == "/api/warehouse":
            qs = parse_qs(parsed.query)
            table_name = qs.get("table", ["fact_sewa_kos"])[0]
            allowed = {"fact_sewa_kos", "dim_lokasi", "dim_spesifikasi_kamar", "dim_fasilitas_aturan", "dim_kontrak_sewa", "vw_mart_kos_lengkap"}
            if table_name not in allowed:
                self._send_json({"status": "error", "message": "Nama tabel tidak diizinkan."}, HTTPStatus.BAD_REQUEST)
                return
            try:
                with sqlite3.connect(DB_PATH) as conn:
                    df_t = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 100", conn)
                    total_c = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                self._send_json({
                    "status": "ok",
                    "table": table_name,
                    "total_rows": int(total_c),
                    "columns": list(df_t.columns),
                    "rows": df_t.to_dict(orient="records")
                })
            except Exception as exc:
                self._send_api_exception(exc)
            return

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path not in {"/api/predict", "/api/kos", "/api/run-etl"}:
            self._send_json({"status": "error", "message": "Endpoint tidak ditemukan"}, HTTPStatus.NOT_FOUND)
            return
        try:
            body = self._read_json_body()
        except RequestValidationError as exc:
            self._send_api_exception(exc)
            return

        if parsed.path == "/api/predict":
            try:
                self._send_json(predict_single_kos(body))
            except Exception as exc:
                self._send_api_exception(exc)
            return

        if parsed.path == "/api/kos":
            try:
                self._send_json(insert_new_kos_to_dw(body))
            except Exception as exc:
                self._send_api_exception(exc)
            return

        if parsed.path == "/api/run-etl":
            try:
                subprocess.run([sys.executable, ETL_SCRIPT_PATH], check=True, cwd=BASE_DIR)
                subprocess.run([sys.executable, TRAIN_SCRIPT_PATH], check=True, cwd=BASE_DIR)
                global MODEL_BUNDLE
                MODEL_BUNDLE = None
                load_model_bundle()
                self._send_json({"status": "ok", "message": "Pipeline ETL & Pelatihan 4 Model Regresi berhasil dijalankan ulang."})
            except Exception as exc:
                self._send_api_exception(exc)
            return


def run_server(port=8000):
    ensure_database()
    url = f"http://localhost:{port}"
    print("=" * 72)
    print(" TOBAKOST ANALYTICS & ML — ARSITEKTUR PAKET A SIAP!")
    print(f" Database Star Schema : {DB_PATH}")
    print(f" Model Regresi ML     : {MODEL_PKL_PATH}")
    print(f" Frontend HTML5/JS    : {FRONTEND_HTML_PATH}")
    print(f" Buka di Browser      : {url}")
    print("=" * 72)
    try:
        webbrowser.open(url)
    except Exception:
        LOGGER.warning("Browser tidak dapat dibuka otomatis; kunjungi %s", url, exc_info=True)
    server = HTTPServer(("0.0.0.0", port), PaketARequestHandler)
    try:
        print(f" Health Check         : {url}/api/health")
        print(" Model akan divalidasi saat health check atau saat digunakan.")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer dihentikan.")
        server.server_close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    run_server(8000)
