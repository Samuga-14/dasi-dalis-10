# Alur Pengerjaan TobaKost: Dummy Data sampai Data Riil

Dokumen ini menjadi panduan kerja tim dari awal pengembangan sampai aplikasi siap
digunakan dengan data riil. Prinsip utamanya:

1. Jangan langsung mengganti data dummy dengan data riil.
2. Simpan data asli di area `raw` dan jangan mengubahnya.
3. Setiap perubahan data, ETL, fitur, atau model harus memiliki versi dan catatan.
4. Jangan menggunakan model baru di aplikasi sebelum lolos validasi.

## Gambaran Besar

```text
FASE A — DATA DUMMY
Data dummy
   -> ETL awal
   -> Warehouse dummy
   -> EDA awal
   -> Training baseline
   -> API + dashboard prototype
   -> Pengujian end-to-end

FASE B — DATA RIIL
Data riil mentah
   -> Profiling dan data quality check
   -> Cleaning terdokumentasi
   -> EDA data riil
   -> ETL staging
   -> Warehouse versi baru
   -> Retraining dan evaluasi model
   -> UAT/API/dashboard
   -> Release data riil
```

## Tools yang Dipakai

| Kebutuhan | Tools | Lokasi/output |
|---|---|---|
| Menyimpan kode dan versi | Git + GitHub | Seluruh repository |
| Menjalankan Python | Virtual environment `.venv` | Environment lokal |
| Membaca dan membersihkan data | pandas + NumPy | `etl/`, notebook |
| EDA interaktif | Jupyter Notebook | `notebooks/01_eda.ipynb` |
| Grafik EDA | Plotly, Matplotlib, Seaborn | Notebook dan reports |
| Profiling otomatis opsional | ydata-profiling | Laporan profiling HTML |
| Validasi schema | Pandera atau validasi pandas | `etl/validate.py` |
| Database lokal | SQLite | Development/demo |
| Database production | PostgreSQL | Deployment data riil |
| DDL dan ERD | SQL + Mermaid/dbdiagram.io | `warehouse/` |
| Training model | scikit-learn | `notebooks/`, `models/` |
| Menyimpan model | joblib atau pickle | `models/artifacts/` |
| Menyajikan API | FastAPI + Uvicorn | `app/` |
| Pengujian API | pytest + HTTP client | `tests/` |
| Dashboard | HTML, JavaScript, Plotly.js, Leaflet.js | `app/frontend/` |

Tools tambahan seperti Seaborn, Matplotlib, Jupyter, Pandera, pytest, dan FastAPI perlu
ditambahkan ke `requirements.txt` ketika implementasi final mulai dipindahkan ke struktur
repository wajib.

## Fase 0 — Menyiapkan Repository dan Aturan Tim

Sebelum mengolah data:

1. Tentukan nama repository dan branch.
2. Buat struktur folder wajib:

```text
data/
etl/
warehouse/
notebooks/
models/
app/
paper/
reports/weekly/
docs/
```

3. Tentukan pemilik area kerja:
   - Data/ETL.
   - Warehouse/ERD.
   - EDA/ML.
   - Frontend/visualisasi.
   - Backend/API/integrasi.
4. Buat aturan penamaan dataset, notebook, model, dan laporan.
5. Tambahkan `.gitignore` untuk `.venv/`, cache Python, secret, database lokal yang besar,
   dan file hasil eksperimen sementara.
6. Jangan commit data pribadi, credential, atau file lebih besar dari batas GitHub.

Output:

- Struktur repository.
- Pembagian tugas.
- `README.md`.
- `docs/data-dictionary.md` versi awal.
- `reports/weekly/minggu-01.md`.

## Fase A — Pengembangan dengan Data Dummy

### A1. Memahami data dummy

Tools: pandas dan Jupyter Notebook.

Kerjakan:

1. Baca CSV dummy.
2. Catat jumlah baris dan kolom.
3. Catat tipe data setiap kolom.
4. Identifikasi kolom target harga.
5. Identifikasi kolom identifier, kategori, numerik, lokasi, dan fasilitas.
6. Catat nilai kosong, duplikasi, dan nilai yang tidak konsisten.
7. Buat data dictionary awal.

Notebook:

```text
notebooks/01_eda_dummy.ipynb
```

Output:

- Profil dataset dummy.
- Data dictionary.
- Daftar asumsi awal.
- Daftar masalah data dummy yang diketahui.

### A2. Membuat ETL dummy

Tools: Python, pandas, NumPy, dan SQLite.

Alur:

```text
CSV dummy
   -> extract
   -> transform nama dan tipe kolom
   -> validasi nilai
   -> feature engineering
   -> load ke warehouse
```

Pisahkan fungsi agar mudah diganti saat data riil masuk:

```text
etl/extract.py
etl/transform.py
etl/validate.py
etl/load.py
```

Jangan mencampur logika cleaning dengan training model. Cleaning dan feature engineering
yang digunakan model harus dapat dipanggil ulang oleh pipeline inference.

Output:

- Dataset hasil transformasi.
- Log jumlah baris masuk dan keluar.
- Laporan baris yang ditolak.
- Database warehouse dummy.

### A3. Membuat warehouse dan ERD

Tools: SQL, SQLite, PostgreSQL, Mermaid, atau dbdiagram.io.

Tentukan:

- Tabel fakta.
- Tabel dimensi.
- Primary key.
- Foreign key.
- Tipe data.
- View mart untuk dashboard dan model.

Simpan di:

```text
warehouse/ddl/
warehouse/erd/
```

Gate sebelum lanjut:

- Foreign key valid.
- Tidak ada duplicate primary key.
- Jumlah record fact sesuai hasil ETL.
- View mart dapat dibaca.

### A4. EDA dummy

Tools: Jupyter, pandas, Plotly, Matplotlib, dan Seaborn.

Analisis minimal:

- Distribusi harga.
- Harga berdasarkan kecamatan.
- Harga berdasarkan fasilitas.
- Hubungan harga dan jarak.
- Missing value.
- Outlier.
- Ketidakseimbangan kategori.
- Korelasi numerik.

EDA bukan sekadar membuat chart. Setiap chart harus memiliki kesimpulan dan batasan.

Output:

```text
notebooks/01_eda_dummy.ipynb
reports/eda-dummy.md
```

### A5. Baseline dan eksperimen model

Tools: scikit-learn dan Jupyter.

Urutan:

1. Tentukan target dan fitur.
2. Pisahkan train/test dengan random seed.
3. Buat baseline sederhana.
4. Latih beberapa kandidat model.
5. Bandingkan MAE, RMSE, MAPE, dan R².
6. Periksa residual dan error pada kelompok data penting.
7. Pilih model berdasarkan metrik dan kebutuhan bisnis, bukan hanya satu skor.

Notebook:

```text
notebooks/02_baseline.ipynb
notebooks/03_model_experiments.ipynb
```

Simpan:

```text
models/artifacts/model-v001.joblib
models/model_card.md
models/registry/model_manifest-v001.json
```

Model card minimal berisi dataset, fitur, target, algoritma, metrik, batasan, dan tanggal
training.

### A6. Membuat API dan dashboard prototype

Tools:

- Backend: FastAPI + Uvicorn.
- Schema: Pydantic.
- Frontend: HTML, JavaScript, Plotly.js, Leaflet.js.
- Database lokal: SQLite.

API minimal:

```text
GET  /api/health
GET  /api/analytics/summary
GET  /api/listings
POST /api/predictions
```

Dashboard harus memanggil API, bukan membaca SQLite langsung.

### A7. Pengujian dummy end-to-end

Sebelum data riil dikumpulkan, pastikan:

- ETL dapat dijalankan dari awal.
- Warehouse dapat dibuat ulang.
- Model dapat dilatih ulang.
- Model dapat dimuat API.
- Prediksi memiliki schema response yang konsisten.
- Lima visualisasi dapat mengambil data API.
- Error request ditampilkan dengan jelas.
- Tidak ada secret di repository.

## Fase B — Data Riil Masuk dalam Kondisi Kotor

### B1. Menyimpan data riil tanpa menyentuh raw

Buat versi data:

```text
data/
├── raw/
│   └── survey-kos-2026-11-12.csv
├── staging/
└── sample/
```

Aturan:

- Jangan edit file di `raw/`.
- Jangan menimpa file raw lama.
- Gunakan tanggal atau version identifier.
- Simpan sumber, waktu pengambilan, pemilik, dan izin penggunaan.
- Jika data sensitif, batasi akses dan lakukan masking.

Output:

```text
data/raw/README.md
docs/data-provenance.md
```

### B2. Profiling data riil sebelum cleaning

Jangan langsung menghapus baris atau mengganti nilai. Profiling dilakukan lebih dulu.

Tools:

- Jupyter + pandas untuk pemeriksaan terkontrol.
- ydata-profiling untuk ringkasan otomatis opsional.
- NumPy untuk pemeriksaan numerik.
- Pandera untuk aturan schema.

Periksa:

- Jumlah baris dan kolom.
- Nama kolom dan perubahan schema.
- Tipe data aktual.
- Missing value per kolom.
- Duplikasi identifier.
- Nilai kategori yang berbeda penulisan.
- Nilai negatif atau tidak masuk akal.
- Outlier.
- Data leakage.
- Data pribadi atau sensitif.
- Konsistensi satuan rupiah, meter, kilometer, dan tanggal.

Notebook:

```text
notebooks/04_data_profiling_riil.ipynb
```

Output:

```text
reports/data-quality-raw-v001.md
reports/data-profile-raw-v001.html
```

### B3. Menyusun aturan data quality

Sebelum cleaning, tulis aturan yang dapat diperiksa otomatis:

| Aturan | Contoh |
|---|---|
| Required column | `harga_bulanan_norm` harus ada |
| Tipe data | Harga harus numerik |
| Range | Luas kamar harus lebih besar dari 0 |
| Kategori | Nilai kecamatan harus ada di daftar referensi |
| Unik | ID unit tidak boleh duplikat |
| Relasi | ID dimensi harus dapat ditemukan |
| Konsistensi | Harga tahunan dapat dinormalisasi ke bulanan |
| Privacy | Nomor telepon/email tidak masuk ke fitur model |

Gunakan `etl/validate.py` dan hasilkan:

- `passed_rows`.
- `rejected_rows`.
- Alasan penolakan.
- Ringkasan per aturan.

Jangan hanya mencatat “data sudah bersih”; simpan bukti angka sebelum dan sesudah.

### B4. Cleaning dan standardisasi

Tools: Python, pandas, NumPy, dan aturan validasi.

Urutan yang disarankan:

1. Salin data raw ke staging.
2. Standarkan nama kolom.
3. Standarkan encoding dan whitespace.
4. Ubah tipe data.
5. Normalisasi kategori.
6. Ubah satuan secara eksplisit.
7. Tangani missing value sesuai aturan domain.
8. Deduplicate dengan kriteria yang disetujui.
9. Tandai outlier; jangan otomatis menghapus tanpa alasan.
10. Masking atau hapus data sensitif.
11. Simpan log setiap transformasi.

Contoh:

```text
data/raw/survey-kos-2026-11-12.csv
   -> data/staging/survey-kos-clean-v001.parquet
```

Parquet cocok untuk staging besar. CSV tetap boleh digunakan jika dataset kecil dan mudah
diaudit.

Output:

- Dataset staging bersih.
- Laporan before/after.
- Reject file.
- Script cleaning yang repeatable.

### B5. EDA ulang dengan data riil

EDA dummy tidak boleh dianggap berlaku otomatis untuk data riil.

Ulangi:

- Distribusi harga.
- Distribusi kecamatan.
- Fasilitas dan kategori.
- Missingness.
- Outlier.
- Korelasi.
- Perubahan pola dibanding dummy.
- Data representatif atau bias.

Bandingkan dummy dan riil:

```text
notebooks/05_eda_real.ipynb
reports/eda-real-v001.md
```

Keputusan penting:

- Apakah kolom dummy masih tersedia?
- Apakah target masih valid?
- Apakah feature engineering masih masuk akal?
- Apakah ada kategori baru?
- Apakah data riil cukup untuk training?
- Apakah model harus diganti atau hanya dilatih ulang?

### B6. ETL riil ke warehouse

Alur:

```text
raw
  -> profiling
  -> staging clean
  -> validate
  -> transform
  -> load dimensions
  -> load fact
  -> build mart/view
```

Jangan menghapus warehouse dummy sebelum warehouse riil lolos validasi. Buat database atau
schema terpisah, misalnya:

```text
tobakost_dummy
tobakost_real_v001
```

Atau gunakan schema PostgreSQL:

```text
staging
warehouse
mart
```

### B7. Retraining model dengan data riil

Model harus dilatih ulang jika:

- Target berubah.
- Kolom berubah.
- Kategori baru muncul.
- Distribusi data berubah jauh.
- Feature engineering berubah.
- Data dummy tidak representatif.

Urutan:

1. Freeze dataset training versi tertentu.
2. Freeze feature schema.
3. Split train/validation/test.
4. Train baseline.
5. Train kandidat model.
6. Evaluasi overall dan per subgroup.
7. Bandingkan dengan model dummy.
8. Buat model card baru.
9. Simpan artifact versi baru.
10. Daftarkan manifest model.

Contoh versi:

```text
dataset-real-v001
feature-schema-v002
model-v002
```

Jangan menimpa `model-v001`. Model lama diperlukan untuk rollback dan perbandingan.

### B8. Validasi API dan dashboard dengan data riil

Uji:

- `/api/health`.
- `/api/analytics/summary`.
- `/api/listings`.
- `/api/predictions`.
- Response untuk missing field.
- Response untuk kategori baru.
- Response untuk harga di luar range.
- Waktu response.
- Pagination jika data besar.
- Role user dan admin.

Dashboard diperiksa untuk:

- Label dan satuan.
- Nilai kosong.
- Peta dengan koordinat invalid.
- Chart tanpa data.
- Format rupiah.
- Filter kategori baru.
- Pesan error yang tidak membocorkan data sensitif.

### B9. User acceptance test dan release

Sebelum release:

1. Tim data menyetujui data quality report.
2. Tim warehouse menyetujui DDL dan jumlah baris.
3. Tim ML menyetujui model card dan metrik.
4. Tim frontend menyetujui lima section visualisasi.
5. Tim backend menyetujui API contract dan keamanan.
6. Dosen atau stakeholder mencoba alur pencarian kos.
7. Semua hasil dicatat di `reports/weekly/`.

Release harus menyebut:

- Dataset version.
- ETL version/commit.
- Warehouse version.
- Model version.
- API version.
- Tanggal release.
- Known limitations.

## Jika Terjadi Perubahan di Tengah Jalan

### Hanya nilai data yang berubah

- Jalankan profiling ulang.
- Jalankan cleaning dan validation.
- Retrain jika distribusi berubah.
- Tidak selalu perlu mengubah DDL.

### Kolom atau schema berubah

- Update data dictionary.
- Update ETL transform dan validation.
- Update DDL jika perlu.
- Update `models/features.py`.
- Buat feature schema version baru.
- Retrain dan uji API.

### Target harga berubah

- Ulangi definisi masalah.
- Ulangi EDA.
- Ulangi baseline.
- Evaluasi ulang semua model.
- Update model card dan paper.

### Sumber data baru ditambahkan

- Buat connector/extract terpisah.
- Jangan menimpa sumber lama.
- Dokumentasikan join key dan potensi bias.
- Validasi data sebelum digabung.

## Checklist Singkat per Fase

### Dummy selesai jika

- [ ] ETL dapat diulang.
- [ ] Warehouse dan ERD tersedia.
- [ ] EDA dan baseline terdokumentasi.
- [ ] Model card tersedia.
- [ ] API dan dashboard berjalan.
- [ ] Lima visualisasi berjalan.

### Data riil siap training jika

- [ ] Raw data tersimpan dan terlacak.
- [ ] Data dictionary diperbarui.
- [ ] Profiling selesai.
- [ ] Data quality rules disetujui.
- [ ] Cleaning repeatable.
- [ ] Reject rows terdokumentasi.
- [ ] EDA riil selesai.
- [ ] Tidak ada data leakage.

### Model riil siap aplikasi jika

- [ ] Metrik memenuhi target.
- [ ] Error subgroup diperiksa.
- [ ] Model card dan manifest tersedia.
- [ ] API prediction lolos test.
- [ ] Dashboard lolos UAT.
- [ ] Rollback ke model sebelumnya tersedia.

## Contoh Perintah Kerja

```powershell
# 1. Aktifkan environment
.\.venv\Scripts\Activate.ps1

# 2. Jalankan ETL dummy atau sumber yang dipilih
$env:TOBAKOST_SOURCE_CSV = "data\sample\kos_dummy.csv"
python etl\run_etl_star_schema.py

# 3. Training model
python models\train_models.py

# 4. Jalankan aplikasi lokal
python server.py

# 5. Saat data riil sudah siap, gunakan path baru dan versi baru
$env:TOBAKOST_SOURCE_CSV = "data\raw\survey-kos-2026-11-12.csv"
python etl\run_etl_star_schema.py
python models\train_models.py
python server.py
```

Perintah di atas adalah alur prototype saat ini. Pada struktur final dosen, perintah tersebut
dipindahkan ke modul `etl/` dan `app/main.py`, sementara notebook menjadi tempat eksplorasi dan
eksperimen yang dapat direproduksi.
