# TobaKost Analytics & Machine Learning — Tech Stack

Dokumen ini menjelaskan teknologi, arsitektur, alur data, dan pembagian tanggung jawab
komponen pada proyek TobaKost. Struktur repository mengikuti format akademik yang diwajibkan
dosen. Folder `app/` menjadi pusat aplikasi dashboard dan API, sedangkan ETL, warehouse,
notebook, model, paper, laporan mingguan, dan dokumentasi dipisahkan sesuai siklus kerja data
science.

## 0. Keputusan Tech Stack

| Lapisan | Pilihan | Alasan |
|---|---|---|
| Frontend | HTML5, CSS3, JavaScript ES6+ | Ringan, mudah dibagi per visualisasi, dan tidak menambah kompleksitas framework |
| Chart | Plotly.js | Mendukung chart interaktif untuk analitik eksploratif |
| Peta | Leaflet.js | Ringan dan sesuai untuk visualisasi lokasi kos |
| Backend/API | Python + FastAPI | REST API bertipe jelas, dokumentasi OpenAPI otomatis, dan cocok dengan ETL/ML Python |
| Validasi API | Pydantic | Memvalidasi request prediksi dan data listing sebelum diproses |
| Database development | SQLite | Mudah dijalankan lokal dan cocok untuk data dummy/single-user |
| Database production | PostgreSQL | Mendukung multi-user, transaksi, role, backup, dan deployment nyata |
| Warehouse model | Star schema | Memisahkan fact dan dimension untuk kebutuhan analitik |
| ETL | Python, pandas, NumPy | Konsisten dengan pipeline feature engineering dan model |
| Machine learning | scikit-learn | Model regresi, evaluasi, dan preprocessing berada dalam ekosistem Python |
| Notebook | Jupyter Notebook | EDA, baseline, dan eksperimen dapat direproduksi |
| Dokumentasi | Markdown | Mudah direview melalui GitHub |
| Version control | Git + GitHub | Kolaborasi, review, dan histori perubahan |

### Keputusan backend

Backend yang direkomendasikan untuk struktur final adalah **FastAPI**, bukan custom
`http.server`. Custom server yang ada tetap dapat dipakai sebagai prototype lokal, tetapi FastAPI
lebih tepat untuk koordinasi tim karena memiliki router, schema request/response, dependency
injection, validasi Pydantic, dan OpenAPI/Swagger.

Endpoint tetap dipisahkan berdasarkan domain:

- `/api/analytics` untuk data agregasi dan visualisasi.
- `/api/listings` untuk pencarian kos.
- `/api/predictions` untuk inferensi model.
- `/api/warehouse` untuk endpoint admin/inspeksi.
- `/api/health` untuk readiness check.

### Keputusan database

Gunakan **SQLite untuk development dan demo** karena database dummy saat ini berbentuk file
`data/tobakost_warehouse.db`. Gunakan **PostgreSQL untuk data riil atau multi-user**. Schema,
repository, dan API harus dirancang agar perpindahan database tidak mengubah frontend.

## 1. Struktur Repository Wajib

Target struktur repository:

```text
da-ds-2026-kelompok-XX/
├── README.md
├── data/
│   ├── sample/                         # Sampel kecil yang boleh di-commit
│   └── README.md                       # Tautan data lengkap dan instruksi akses
├── etl/                                # Extract-transform-load
│   ├── extract.py
│   ├── transform.py
│   ├── validate.py
│   └── load.py
├── warehouse/                          # DDL, seed, dan ERD
│   ├── ddl/
│   ├── seeds/
│   └── erd/
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_baseline.ipynb
│   └── 03_model_experiments.ipynb
├── models/
│   ├── artifacts/                      # .pkl/.joblib, jangan commit > 50 MB
│   ├── model_card.md
│   └── registry/
├── app/
│   ├── frontend/                       # HTML, CSS, JS, Plotly, Leaflet
│   ├── api/                            # FastAPI routers dan schemas
│   ├── services/                       # Analytics, prediction, recommendation
│   └── main.py
├── paper/
│   ├── naskah-jurnal/
│   └── jurnal-target.md
├── reports/weekly/
│   ├── minggu-01.md
│   └── minggu-14.md
└── docs/
    ├── proposal/
    ├── data-dictionary.md
    └── data-quality-report.md
```

File data lengkap, database binary besar, dan artifact model di atas batas repository tidak
boleh di-commit. Repository menyimpan sampel, schema, manifest, checksum, serta tautan sumber
data lengkap.

## 2. Ringkasan Arsitektur

```text
Browser (HTML + JavaScript + Plotly + Leaflet)
  |
  | HTTPS/JSON REST API
  v
FastAPI Backend
  |
  +--> Analytics service
  +--> Listing/search service
  +--> Prediction service
  +--> PostgreSQL/SQLite warehouse
  |
  +--> Versioned model artifacts

ETL scripts --> staging --> warehouse
Jupyter notebooks --> EDA/baseline/experiments --> models/registry
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
| HTTP server | FastAPI + Uvicorn | Menyajikan REST API dan OpenAPI |
| Request format | JSON | Format request dan response API |
| Routing | FastAPI APIRouter | Routing endpoint berdasarkan domain |
| Validation | Pydantic | Validasi payload dan response |
| Configuration | `server_config.py` dan environment variable | Host, port, path, dan admin key |
| Analytics boundary | `backend/services/analytics.py` | Akses terstandar ke service analitik |
| Database boundary | `backend/db/warehouse.py` | Akses terstandar ke warehouse |
| Entry point | `server.py` dan `backend/main.py` | Menjalankan aplikasi |

Backend prototype saat ini masih memiliki adapter custom. Target struktur final menggunakan
FastAPI agar kontrak API, validasi, dan pembagian router lebih mudah dikelola tim.

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

### Strategi migrasi database

1. DDL star schema ditulis di `warehouse/ddl/`.
2. ETL menulis ke staging terlebih dahulu.
3. Data quality check dijalankan sebelum load ke fact/dimension.
4. SQLite digunakan untuk test lokal.
5. PostgreSQL digunakan sebagai target deployment data riil.
6. API hanya berkomunikasi dengan repository/service, bukan SQL langsung dari frontend.

## 6. ETL dan Data Engineering

| Tahap | Lokasi | Fungsi |
|---|---|---|
| Raw data | `data/raw/` | Menyimpan data asli tanpa ditimpa |
| Staging | `data/staging/` | Area transformasi dan validasi sementara |
| Warehouse | `data/warehouse/` | Lokasi warehouse untuk pengembangan deployment |
| ETL script | `etl/` | Extract, transform, validate, dan load ke star schema |
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

## 8. Pembagian Kerja Lima Anggota

| Anggota | Area | Deliverable utama |
|---|---|---|
| Anggota 1 | Data/ETL | `data/`, `etl/`, data quality, data dictionary |
| Anggota 2 | Warehouse | `warehouse/`, DDL star schema, ERD, query mart |
| Anggota 3 | EDA/ML | `notebooks/`, eksperimen, baseline, model card |
| Anggota 4 | Visualisasi frontend | `app/frontend/`, lima section visualisasi, Leaflet/Plotly |
| Anggota 5 | Backend/API/integrasi | `app/api/`, prediction service, auth, integrasi FE–BE |

Pembagian ini tidak berarti setiap anggota hanya boleh menyentuh satu folder. Perubahan lintas
folder harus didokumentasikan di pull request dan diuji melalui API atau notebook terkait.

## 9. Role dan User

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

## 10. Dependency

Dependency Python didefinisikan di [requirements.txt](./requirements.txt):

- `pandas` untuk manipulasi data.
- `numpy` untuk komputasi numerik.
- `scikit-learn==1.9.1` untuk training dan inference machine learning.

Library frontend seperti Tailwind CSS, Plotly.js, dan Leaflet.js saat ini dimuat melalui CDN.
Untuk production, dependency frontend sebaiknya dipin versinya dan dikelola melalui npm atau
disimpan melalui asset bundler.

## 11. Konfigurasi Runtime

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

## 12. Rekomendasi untuk Production

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

## 13. Cara Menjalankan

```powershell
cd "D:\DASI DALIS\dasi-dalis-10\tobakost_paket_a_project"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python server.py
```

Buka `http://localhost:8000` setelah server aktif.

## 14. Jawaban singkat untuk koordinasi tim

Stack final yang dapat disampaikan ke tim:

> **Frontend:** HTML5, CSS3, JavaScript ES6+, Plotly.js, dan Leaflet.js.
> **Backend:** Python FastAPI dengan Uvicorn, Pydantic, dan REST API JSON.
> **ETL:** Python, pandas, dan NumPy.
> **Machine learning:** scikit-learn dengan notebook Jupyter untuk EDA, baseline, dan eksperimen.
> **Database development:** SQLite.
> **Database data riil/production:** PostgreSQL.
> **Warehouse:** star schema dengan fact dan dimension tables.
> **Dokumentasi/kolaborasi:** Markdown, Git, dan GitHub.
