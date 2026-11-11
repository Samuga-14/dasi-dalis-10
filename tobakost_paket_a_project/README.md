# TobaKost Analytics & ML — Arsitektur Paket A (Ringan & Cepat)

Proyek Terintegrasi **Data Analitik & Data Science** — Institut Teknologi Del.  
Judul: **Analisis Faktor Penentu Tarif dan Prediksi Harga Sewa Kos Menggunakan Algoritma Machine Learning Berdasarkan Spesifikasi Fasilitas dan Aksesibilitas Lokasi di Kabupaten Toba**

## Struktur Folder Proyek (Murni Arsitektur Paket A — Tanpa Streamlit)

```text
tobakost_paket_a_project/
├── server.py                              # Backend Python REST API (menghubungkan Frontend HTML ke SQLite & ML)
├── run_paket_a.bat                        # Klik 2x di Windows untuk langsung menjalankan server & membuka browser
├── requirements.txt                       # Library Python ringan (pandas, numpy, scikit-learn)
├── frontend/
│   └── index.html                         # Frontend HTML5 + Plotly.js + Leaflet.js
├── data/
│   ├── dummy_data_gform_kos_toba_600.csv  # Dataset survei Google Form 600 responden (36 kolom)
│   └── tobakost_warehouse.db              # Database SQLite Star Schema (1 Tabel Fakta + 4 Tabel Dimensi + View)
├── etl/
│   └── run_etl_star_schema.py             # Pipeline ETL otomatis (CSV Google Form -> SQLite Star Schema)
└── models/
    ├── train_models.py                    # Skrip pelatihan & evaluasi 4 algoritma regresi Machine Learning
    ├── best_rf_model.pkl                  # File model pre-trained siap pakai untuk inferensi cepat (<2 ms)
    └── metrics_summary.json               # Ringkasan metrik R2, MAE, RMSE, dan MAPE pada Test Set
```

## Cara Menjalankan Aplikasi

1. Pastikan `pandas`, `numpy`, dan `scikit-learn` sudah terinstal:
   ```bash
   pip install -r requirements.txt
   ```
2. Jalankan server Paket A:
   ```bash
   python server.py
   ```
   *(Atau cukup klik tombol **Run Python File** pada `server.py` di VS Code, atau klik 2x file `run_paket_a.bat`).*
3. Aplikasi otomatis terbuka di browser pada alamat **`http://localhost:8000`**.
4. Periksa kesiapan SQLite dan model melalui **`http://localhost:8000/api/health`**.

Model `.pkl` terikat pada versi scikit-learn yang membuatnya. Jika health check melaporkan model tidak tersedia atau tidak kompatibel, jalankan pelatihan ulang secara eksplisit dari folder proyek:

```bash
python models/train_models.py
```

Server tidak melatih ulang model diam-diam saat startup. Endpoint prediksi menggunakan semua model yang benar-benar tersimpan dalam bundle dan memilih model terbaik berdasarkan MAE pada test set.
