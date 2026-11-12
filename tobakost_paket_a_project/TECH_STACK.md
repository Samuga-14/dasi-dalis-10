# TobaKost Analytics & Machine Learning — Tech Stack

Dokumen ini menjelaskan teknologi, arsitektur, alur data, dan pembagian tanggung jawab
komponen pada proyek TobaKost.

## 1. Ringkasan Arsitektur

```text
Browser
  |
  | HTTP/JSON REST API
  v
Python Backend
  |
  +--> Analytics Service
  +--> Machine Learning Service
  +--> ETL Pipeline
  +--> SQLite Star Schema Warehouse
  |
  +--> Model Artifacts (.pkl + manifest)
```

Frontend tidak mengakses database secara langsung. Semua komunikasi data dilakukan melalui
REST API backend.

## 2. Frontend

| Komponen | Teknologi | Fungsi |
|---|---|---|
| Markup | HTML5 | Struktur halaman dashboard |
| Styling | CSS3 + Tailwind CSS CDN | Layout, responsive UI, dan komponen visual |
| Dashboard logic | JavaScript ES6+ | State, filter, event, dan orkestrasi UI |
| Chart visualization | Plotly.js | Bar chart, treemap, box plot, heatmap, scatter plot, dan model chart |
| Map visualization | Leaflet.js | Peta lokasi kos dan layer aksesibilitas |
| API client | `frontend/js/services/api.js` | Boundary komunikasi frontend ke REST API |
| Main UI controller | `frontend/js/app.js` | Rendering visualisasi, filter, tabel, dan interaksi |

### Lima section visualisasi

Lima section visualisasi utama berdiri sendiri:

1. Ringkasan tarif & hunian.
2. Distribusi harga sewa.
3. Fasilitas & keamanan.
4. Peta & aksesibilitas.
5. Pencarian kos.

Halaman tambahan untuk insight, machine learning, serta ETL/admin tetap terpisah dari lima
visualisasi utama.

## 3. Backend

| Komponen | Teknologi | Fungsi |
|---|---|---|
| Bahasa | Python 3 | Backend, ETL, dan machine learning |
| HTTP server | Python `http.server` | Menyajikan frontend dan REST API |
| Request format | JSON | Format request dan response API |
| Routing | Custom HTTP handler | Routing endpoint `/api/...` |
| Configuration | `server_config.py` dan environment variable | Host, port, path, dan admin key |
| Analytics boundary | `backend/services/analytics.py` | Akses terstandar ke service analitik |
| Database boundary | `backend/db/warehouse.py` | Akses terstandar ke warehouse |
| Entry point | `server.py` dan `backend/main.py` | Menjalankan aplikasi |

Backend saat ini sengaja ringan dan tidak menggunakan framework web besar. Untuk deployment
production, backend dapat dimigrasikan ke FastAPI atau Flask tanpa mengubah kontrak API secara
signifikan.

## 4. REST API

### Endpoint publik

| Method | Endpoint | Fungsi |
|---|---|---|
| `GET` | `/api/health` | Memeriksa status database dan model |
| `GET` | `/api/capabilities` | Mengembalikan role dan permission frontend |
| `GET` | `/api/data` | Mengambil data analitik, metrik, prediksi, dan feature importance |
| `GET` | `/api/warehouse?table=<name>` | Preview tabel warehouse yang diizinkan |
| `POST` | `/api/predict` | Prediksi harga dengan model machine learning |

### Endpoint admin

| Method | Endpoint | Fungsi |
|---|---|---|
| `POST` | `/api/kos` | Menambahkan data kos baru |
| `POST` | `/api/run-etl` | Menjalankan ulang ETL dan training model |

Endpoint admin membutuhkan header:

```http
X-API-Key: <TOBAKOST_ADMIN_API_KEY>
```

Jika `TOBAKOST_ADMIN_API_KEY` belum diatur, operasi tulis dinonaktifkan secara default.

## 5. Database dan Data Warehouse

### Database saat ini

- Database: SQLite.
- File: `data/tobakost_warehouse.db`.
- Model data: star schema.
- Tabel fakta: `fact_sewa_kos`.
- Tabel dimensi:
  - `dim_lokasi`.
  - `dim_spesifikasi_kamar`.
  - `dim_fasilitas_aturan`.
  - `dim_kontrak_sewa`.
- View analitik: `vw_mart_kos_lengkap`.

### Perlindungan database saat ini

- Foreign key SQLite diaktifkan.
- `PRAGMA integrity_check` dijalankan melalui health check.
- Nama tabel warehouse menggunakan whitelist.
- Query memakai parameterized query untuk nilai input.
- Server default hanya bind ke `127.0.0.1`.
- Endpoint perubahan data membutuhkan API key admin.

SQLite cocok untuk demo, pengembangan lokal, dan penggunaan single-user. Untuk production
multi-user, database utama sebaiknya dipindahkan ke PostgreSQL.

## 6. ETL dan Data Engineering

| Tahap | Lokasi | Fungsi |
|---|---|---|
| Raw data | `data/raw/` | Menyimpan data asli tanpa ditimpa |
| Staging | `data/staging/` | Area transformasi dan validasi sementara |
| Warehouse | `data/warehouse/` | Lokasi warehouse untuk pengembangan deployment |
| ETL script | `etl/run_etl_star_schema.py` | Extract, transform, dan load ke star schema |
| Data processing | pandas dan NumPy | Parsing, normalisasi, dan feature engineering |

Sumber CSV dapat ditentukan melalui:

```powershell
$env:TOBAKOST_SOURCE_CSV = "D:\data-riil\survey-kos.csv"
python etl/run_etl_star_schema.py
```

ETL memiliki fallback ke dataset dummy jika sumber utama belum tersedia.

## 7. Machine Learning

### Library

- pandas.
- NumPy.
- scikit-learn `1.9.1`.

### Model yang digunakan

- Linear Regression.
- Ridge Regression.
- Random Forest Regressor.
- Gradient Boosting Regressor.

### Feature engineering

Feature engineering terpusat di [models/features.py](./models/features.py), sehingga training
dan inference menggunakan urutan fitur yang sama.

### Model artifact

| Artifact | Fungsi |
|---|---|
| `models/best_rf_model.pkl` | Bundle model dan seluruh model terlatih |
| `models/metrics_summary.json` | Metrik evaluasi model |
| `models/registry/model_manifest.json` | Versi model, fitur, dataset, dan scikit-learn |
| `models/artifacts/` | Lokasi artifact model untuk pengembangan berikutnya |

Training ulang:

```powershell
python models/train_models.py
```

## 8. Role dan User

Sistem tidak mengasumsikan jumlah user tertentu.

### User

- Melihat dashboard.
- Mencari kos.
- Menggunakan prediksi harga.
- Membaca analitik dan rekomendasi.

### Admin

- Menambah data kos.
- Menjalankan ETL.
- Melakukan refresh model.
- Memeriksa warehouse.

Role admin saat ini menggunakan API key sederhana untuk development. Untuk production,
sebaiknya diganti dengan authentication dan authorization berbasis akun, session/JWT,
password hashing, serta role-based access control.

## 9. Dependency

Dependency Python didefinisikan di [requirements.txt](./requirements.txt):

- `pandas` untuk manipulasi data.
- `numpy` untuk komputasi numerik.
- `scikit-learn==1.9.1` untuk training dan inference machine learning.

Library frontend seperti Tailwind CSS, Plotly.js, dan Leaflet.js saat ini dimuat melalui CDN.
Untuk production, dependency frontend sebaiknya dipin versinya dan dikelola melalui npm atau
disimpan melalui asset bundler.

## 10. Konfigurasi Runtime

| Variable | Default | Fungsi |
|---|---|---|
| `TOBAKOST_HOST` | `127.0.0.1` | Host server |
| `TOBAKOST_PORT` | `8000` | Port server |
| `TOBAKOST_ADMIN_API_KEY` | kosong | Proteksi endpoint admin |
| `TOBAKOST_SOURCE_CSV` | CSV dummy | Sumber data ETL |

Contoh menjalankan:

```powershell
$env:TOBAKOST_ADMIN_API_KEY = "admin-key-lokal"
$env:TOBAKOST_SOURCE_CSV = "D:\data-riil\survey-kos.csv"
python server.py
```

## 11. Rekomendasi untuk Production

Jika proyek mulai memakai data riil atau diakses banyak pengguna, lakukan migrasi berikut:

1. Ganti SQLite dengan PostgreSQL.
2. Gunakan FastAPI atau Flask dengan WSGI/ASGI server.
3. Tambahkan authentication dan role-based authorization.
4. Gunakan HTTPS melalui reverse proxy.
5. Simpan credential di secret manager atau environment variable.
6. Tambahkan migration database menggunakan Alembic.
7. Tambahkan backup dan restore teruji.
8. Tambahkan audit log untuk perubahan data.
9. Validasi schema, missing value, duplikasi, outlier, dan data sensitif sebelum ETL.
10. Versioning dataset, ETL, feature schema, dan model.
11. Tambahkan automated tests dan CI/CD.
12. Jangan memuat seluruh dataset ke browser jika jumlah data sudah besar; gunakan pagination
    dan endpoint agregasi.

## 12. Cara Menjalankan

```powershell
cd "D:\DASI DALIS\dasi-dalis-10\tobakost_paket_a_project"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python server.py
```

Buka `http://localhost:8000` setelah server aktif.
