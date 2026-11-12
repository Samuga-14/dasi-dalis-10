# TobaKost Analytics & ML — Arsitektur Paket A (Ringan & Cepat)

Proyek Terintegrasi **Data Analitik & Data Science** — Institut Teknologi Del.  
Judul: **Analisis Faktor Penentu Tarif dan Prediksi Harga Sewa Kos Menggunakan Algoritma Machine Learning Berdasarkan Spesifikasi Fasilitas dan Aksesibilitas Lokasi di Kabupaten Toba**

## Struktur Folder Proyek (Paket A Modular — Tanpa Streamlit)

```text
tobakost_paket_a_project/
├── server.py                              # Launcher kompatibilitas
├── backend/
│   ├── main.py                             # Entrypoint backend berlapis
│   ├── api/http.py                         # HTTP adapter dan REST handler
│   ├── api/routes.py                       # Katalog route publik/admin
│   ├── core/config.py                      # Konfigurasi backend
│   ├── db/warehouse.py                     # Boundary akses warehouse
│   └── services/analytics.py               # Boundary service analytics
├── services/                               # Implementasi service yang dipakai backend
├── run_paket_a.bat                        # Klik 2x di Windows untuk langsung menjalankan server & membuka browser
├── requirements.txt                       # Library Python ringan (pandas, numpy, scikit-learn)
├── frontend/
│   ├── index.html                          # Markup dashboard
│   ├── css/app.css                         # Styling dashboard
│   └── js/app.js                           # Orkestrasi UI dan visualisasi
├── data/
│   ├── raw/                                # Sumber data asli, tidak ditimpa ETL
│   ├── staging/                            # Area transformasi/validasi sementara
│   ├── warehouse/                          # Lokasi warehouse untuk deployment berikutnya
│   ├── dummy_data_gform_kos_toba_600.csv  # Dataset survei Google Form 600 responden (36 kolom)
│   └── tobakost_warehouse.db              # Database SQLite Star Schema (1 Tabel Fakta + 4 Tabel Dimensi + View)
├── etl/
│   └── run_etl_star_schema.py             # Pipeline ETL otomatis (CSV Google Form -> SQLite Star Schema)
└── models/
    ├── artifacts/                          # Artifact model hasil training
    └── registry/                           # Manifest versi model dan dataset
    ├── train_models.py                    # Skrip pelatihan & evaluasi 4 algoritma regresi Machine Learning
    ├── best_rf_model.pkl                  # File model pre-trained siap pakai untuk inferensi cepat (<2 ms)
    └── metrics_summary.json               # Ringkasan metrik R2, MAE, RMSE, dan MAPE pada Test Set
```

## Cara Menjalankan Aplikasi di Windows

### Opsi A — melalui terminal VS Code

Buka terminal PowerShell, lalu jalankan perintah berikut satu per satu:

```powershell
cd "D:\DASI DALIS\dasi-dalis-10\tobakost_paket_a_project"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python server.py
```

Jika PowerShell menolak aktivasi virtual environment, jalankan sekali:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Setelah server berjalan, buka:

- Dashboard: **http://localhost:8000**
- Health check: **http://localhost:8000/api/health**

Jangan menutup terminal selama aplikasi digunakan. Tekan `Ctrl+C` untuk menghentikan server.

### Opsi B — klik file `.bat`

Klik dua kali [run_paket_a.bat](./run_paket_a.bat). File tersebut otomatis masuk ke folder
proyek lalu menjalankan `server.py`.

Opsi ini tetap membutuhkan dependency yang sudah terpasang. Jika belum, jalankan perintah
instalasi berikut terlebih dahulu dari folder proyek:

```powershell
python -m pip install -r requirements.txt
```

### Opsi C — menjalankan dari VS Code

1. Buka folder `tobakost_paket_a_project` di VS Code.
2. Pilih interpreter Python dari `.venv`.
3. Buka [server.py](./server.py).
4. Klik **Run Python File**.
5. Buka **http://localhost:8000** di browser.

### Jika model tidak kompatibel

Jalankan pelatihan ulang dari folder proyek:

```powershell
python models/train_models.py
python server.py
```

Server tidak melatih ulang model secara diam-diam saat startup.

## Pembagian 5 section visualisasi

Lima section visualisasi berdiri sendiri dan tidak digabung. Section ML serta ETL/admin tetap
menjadi halaman terpisah setelah lima visualisasi tersebut:

| Section | Cakupan | Fokus |
|---|---|---|
| 1. Ringkasan tarif & hunian | `tab1` | Statistik tarif, hunian, dan KPI utama |
| 2. Distribusi harga sewa | `tab2` | Distribusi, hierarki, dan perbandingan harga |
| 3. Fasilitas & keamanan | `tab3` | Fasilitas kamar, air, keamanan, dan aturan |
| 4. Peta & aksesibilitas | `tab4` | Pemetaan spasial, jarak, dan aksesibilitas |
| 5. Pencarian kos | `tab5` | Finder interaktif dan perbandingan unit |

Halaman tambahan tetap terpisah:

- `tab6`: insight dan rekomendasi.
- `tab7`–`tab9`: machine learning.
- `tab10`: ETL, warehouse, dan operasi admin.

Dengan pembagian ini, lima anggota tim dapat mengembangkan masing-masing visualisasi tanpa
menggabungkan beberapa visualisasi ke dalam satu halaman besar.

## Pembagian service dan alur FE–BE

Frontend memanggil backend melalui REST API JSON, bukan membaca SQLite secara langsung:

| Service | Endpoint | Tanggung jawab |
|---|---|---|
| Analytics | `GET /api/data` | Dataset dashboard, metrik, peta, korelasi, dan ringkasan visualisasi |
| Machine Learning | `POST /api/predict` | Prediksi harga dengan model Linear, Ridge, Random Forest, dan Gradient Boosting |
| Warehouse | `GET /api/warehouse?table=...` | Preview tabel star schema yang sudah di-whitelist |
| Capabilities | `GET /api/capabilities` | Menentukan role user/admin dan izin UI |
| Data ingestion | `POST /api/kos`, `POST /api/run-etl` | Operasi tulis dan refresh ETL/model, khusus admin |
| Health | `GET /api/health` | Status database, jumlah record, dan kompatibilitas model |

`frontend/index.html` hanya berisi markup. CSS dan JavaScript dipisah sebagai aset statis sehingga
visualisasi dapat dikembangkan per domain tanpa menaruh seluruh aplikasi dalam satu file HTML.

## Keamanan database dummy

Database saat ini adalah **SQLite warehouse berbasis data dummy**, bukan database produksi dan bukan
data real-time. SQLite tetap memiliki integrity check, foreign key enforcement, parameterized query,
dan whitelist nama tabel. Server default hanya bind ke `127.0.0.1`, sehingga tidak terbuka ke jaringan.
Untuk lingkungan selain lokal, set `TOBAKOST_HOST`, gunakan reverse proxy/HTTPS, dan set
`TOBAKOST_ADMIN_API_KEY`; key tersebut dikirim melalui header `X-API-Key` untuk endpoint tulis dan ETL.
Jangan menaruh key di source code atau repository.

## Role user dan admin

Role tidak dikunci berdasarkan jumlah pengguna. Semua user dapat membaca visualisasi, mencari kos,
dan menggunakan prediksi. Operasi perubahan warehouse dan refresh pipeline hanya tersedia untuk
admin melalui `X-API-Key`. Jika `TOBAKOST_ADMIN_API_KEY` belum diatur, operasi tulis sengaja
dinonaktifkan, bukan dibuka tanpa perlindungan.

## Saat mengganti dummy data dengan data riil

Letakkan file sumber di `data/raw/` atau set path eksplisit:

```powershell
$env:TOBAKOST_SOURCE_CSV = "D:\data-riil\survey-kos.csv"
python etl/run_etl_star_schema.py
python models/train_models.py
python server.py
```

ETL tidak mengubah file raw. Sebelum memakai data riil, tambahkan validasi skema, data kosong,
duplikasi, outlier, dan masking data sensitif. Setiap training menghasilkan
`models/registry/model_manifest.json` yang mencatat fitur, sumber dataset, algoritma terbaik, dan
versi scikit-learn. Perubahan kolom ETL harus diikuti perubahan `models/features.py`, retraining,
dan pengujian endpoint prediksi.

Model `.pkl` terikat pada versi scikit-learn yang membuatnya. Jika health check melaporkan model tidak tersedia atau tidak kompatibel, jalankan pelatihan ulang secara eksplisit dari folder proyek:

```bash
python models/train_models.py
```

Server tidak melatih ulang model diam-diam saat startup. Endpoint prediksi menggunakan semua model yang benar-benar tersimpan dalam bundle dan memilih model terbaik berdasarkan MAE pada test set.
