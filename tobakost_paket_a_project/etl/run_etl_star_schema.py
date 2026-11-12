"""
Pipeline ETL Otomatis -> Data Warehouse Skema Bintang (SQLite / DuckDB)
Proyek Terintegrasi Data Analitik & Data Science - Institut Teknologi Del
Dataset: Survei Google Form 600 Responden Kos Kabupaten Toba (dummy_data_gform_kos_toba_600.csv)
"""
import os
import re
import shutil
import sqlite3
import tempfile
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
GFORM_CSV_PATH = os.getenv(
    "TOBAKOST_SOURCE_CSV",
    os.path.join(RAW_DATA_DIR, "kos_survey.csv"),
)
LEGACY_GFORM_CSV_PATH = os.path.join(BASE_DIR, "data", "dummy_data_gform_kos_toba_600.csv")
FALLBACK_CSV_PATH = os.path.join(BASE_DIR, "data", "dummy_data_kost_toba_600.csv")
DB_PATH = os.path.join(BASE_DIR, "data", "tobakost_warehouse.db")

def parse_tujuan_kampus(val):
    s = str(val).strip()
    m = re.match(r"^(.*?)\s+(\d+(?:\.\d+)?)$", s)
    if m:
        nama = m.group(1).strip()
        meter = float(m.group(2))
        return nama, round(meter / 1000.0, 2), int(meter)
    return s, 1.0, 1000

def run_etl():
    csv_path = GFORM_CSV_PATH
    if not os.path.exists(csv_path):
        csv_path = LEGACY_GFORM_CSV_PATH if os.path.exists(LEGACY_GFORM_CSV_PATH) else FALLBACK_CSV_PATH
    print("[1/4] EXTRACT: Membaca dataset Google Form dari:", csv_path)
    df_raw = pd.read_csv(csv_path)
    raw_count = len(df_raw)

    print("[2/4] TRANSFORM: Parsing 36 kolom kuesioner Google Form, ekstraksi multi-label, & normalisasi harga...")
    df = df_raw.copy()
    parsed_k = df["5. Perkiraan Jarak ke Kampus / Sekolah / Tempat Kerja Terdekat"].apply(parse_tujuan_kampus)

    df["nama_kost"] = df["1. Nama Kos"]
    df["kecamatan"] = df["2. Kecamatan Lokasi Kos"]
    df["desa_kelurahan"] = df["3. Desa / Kelurahan Lokasi Kos"]
    df["kategori_penghuni"] = df["4. Kategori Penghuni Kos"].str.lower()
    df["nama_tempat_krusial"] = [p[0] for p in parsed_k]
    df["jarak_ke_kampus_kantor_sekolah_terdekat_km"] = [p[1] for p in parsed_k]
    df["jarak_kampus_m"] = [p[2] for p in parsed_k]
    df["jarak_ke_pasar_km"] = (df["6. Perkiraan Jarak ke Pasar / Minimarket / Supermarket Terdekat"] / 1000.0).round(2)
    df["jarak_krusial_km"] = (df["7. Perkiraan Jarak ke RS / Puskesmas / Klinik Terdekat"] / 1000.0).round(2)
    df["jarak_laundry_m"] = df["8. Perkiraan Jarak ke Laundry Terdekat"].astype(int)
    df["jarak_ibadah_m"] = df["9. Perkiraan Jarak ke Tempat Ibadah Terdekat"].astype(int)
    df["jarak_pusat_kota_m"] = df["10. Perkiraan Jarak ke Pusat Kota"].astype(int)
    df["jarak_ke_jalan_raya_m"] = df["11. Perkiraan Jarak Masuk dari Jalan Raya Utama"].astype(int)
    df["area_tempat_makan"] = df["12. Apakah lokasi kos Anda dekat dengan area tempat makan?"]
    df["jumlah_lantai"] = df["13. Posisi Lantai Kamar"].astype(int)
    df["luas_kamar_m2"] = df["14. Luas Kamar (m2)"].astype(float)
    df["fasilitas_kamar_detail"] = df["15. Fasilitas didalam kamar kos yang tersedia"]

    # Ekstraksi biner dari checkbox fasilitas kamar (Pertanyaan 15)
    df["ada_dipan"] = df["fasilitas_kamar_detail"].str.contains("Dipan", case=False).astype(int)
    df["ada_kasur"] = df["fasilitas_kamar_detail"].str.contains("Kasur", case=False).astype(int)
    df["ada_lemari"] = df["fasilitas_kamar_detail"].str.contains("Lemari", case=False).astype(int)
    df["ada_meja_belajar"] = df["fasilitas_kamar_detail"].str.contains("Meja & Kursi", case=False).astype(int)
    df["ada_tv"] = df["fasilitas_kamar_detail"].str.contains("Televisi", case=False).astype(int)
    df["ada_cermin"] = df["fasilitas_kamar_detail"].str.contains("Cermin", case=False).astype(int)
    df["ada_kulkas_pribadi"] = df["fasilitas_kamar_detail"].str.contains("Kulkas mini", case=False).astype(int)

    def map_tier_furnitur(r):
        if r["ada_kulkas_pribadi"] == 1 or r["ada_tv"] == 1:
            return "Eksekutif (Lengkap + TV & Kulkas Mini)"
        elif r["ada_cermin"] == 1:
            return "Lengkap (Dipan, Kasur, Lemari, Meja, Cermin)"
        elif r["ada_meja_belajar"] == 1:
            return "Menengah (Dipan, Kasur, Lemari, Meja & Kursi)"
        elif r["ada_kasur"] == 1:
            return "Dasar (Kasur & Lemari)"
        return "Kamar Kosong (Tanpa Furnitur)"

    df["fasilitas"] = df.apply(map_tier_furnitur, axis=1)
    df["ac_non_ac"] = np.where(df["16. Ada Pendingin Ruangan (AC) di Kamar"] == "Ada", "ac", "non-ac")
    df["tipe_kamar_mandi"] = np.where(df["17. Tipe Kamar Mandi"].str.contains("dalam", case=False), "dalam", "luar")
    df["kelengkapan_kamar_mandi"] = df["18. Kelengkapan isi dalam kamar mandi"]
    df["kloset_duduk"] = df["kelengkapan_kamar_mandi"].str.contains("duduk", case=False).astype(int)
    df["ada_shower"] = df["kelengkapan_kamar_mandi"].str.contains("Shower", case=False).astype(int)
    df["ada_water_heater"] = df["kelengkapan_kamar_mandi"].str.contains("Water Heater", case=False).astype(int)

    df["sumber_air_utama"] = df["19. Sumber Air Utama di Kos"]
    df["wifi_non_wifi"] = np.where(df["20. Fasilitas Internet Wi-Fi Kos"] == "Ada", "wifi", "non-wifi")
    df["fasilitas_dapur_kulkas"] = df["21. Fasilitas Dapur & Kulkas di Kos"]
    df["dapur"] = np.where(
        df["fasilitas_dapur_kulkas"].str.contains("Pribadi", case=False), "pribadi",
        np.where(df["fasilitas_dapur_kulkas"].str.contains("Bersama", case=False), "bersama", "tidak ada")
    )
    df["fasilitas_cuci_jemur"] = df["22. Fasilitas Cuci Pakaian & Area Jemuran Kos"]
    df["keamanan_kos"] = df["23. Keamanan Kos"]
    df["lahan_parkir"] = np.where(
        df["24. Lahan Parkir"] == "Mobil & Motor", "mobil & motor",
        np.where(df["24. Lahan Parkir"] == "Motor Saja", "motor", "tidak ada")
    )
    df["aturan_jam_malam_masuk"] = np.where(df["25. Aturan Jam Malam"] == "Bebas 24 Jam", "Bebas 24 Jam", "Ada Batas Jam Malam")
    df["kapasitas_kamar"] = df["26. Berapa kapasitas penghuni dalam satu kamar?"]
    df["skema_biaya_listrik"] = np.where(df["27. Skema Biaya Listrik"].str.contains("termasuk", case=False), "termasuk sewa", "token sendiri")
    df["tahun_mulai_sewa"] = df["28. Tahun Mulai Menyewa"].astype(str)
    df["sewa_tahunan_bulanan"] = np.where(df["29. Periode Pembayaran Sewa"] == "Per Tahun", "tahunan", "bulanan")
    df["harga_sewa"] = df["30. Nominal Harga Sewa Kos"].astype(int)
    df["harga_bulanan_norm"] = df["harga_ekuivalen_bulanan_rp"].astype(int)
    df["source_url"] = "https://forms.gle/SurveiKosKabupatenTobaITDel"

    # Encoding biner untuk Feature Engineering
    df["km_dalam"] = (df["tipe_kamar_mandi"] == "dalam").astype(int)
    df["is_ac"] = (df["ac_non_ac"] == "ac").astype(int)
    df["is_wifi"] = (df["wifi_non_wifi"] == "wifi").astype(int)
    df["parkir_mobil"] = (df["lahan_parkir"] == "mobil & motor").astype(int)
    df["dapur_pribadi"] = (df["dapur"] == "pribadi").astype(int)
    df["dapur_bersama"] = (df["dapur"] == "bersama").astype(int)
    df["keamanan_penjaga"] = (df["keamanan_kos"] == "Penjaga & CCTV").astype(int)
    df["keamanan_cctv"] = (df["keamanan_kos"] == "CCTV Saja").astype(int)
    df["bebas_24jam"] = (df["aturan_jam_malam_masuk"] == "Bebas 24 Jam").astype(int)
    df["listrik_termasuk"] = (df["skema_biaya_listrik"] == "termasuk sewa").astype(int)
    df["is_tahunan"] = (df["sewa_tahunan_bulanan"] == "tahunan").astype(int)

    # Feature Engineering (Komponen S2)
    df["skor_kelengkapan_fasilitas"] = (
        df["km_dalam"] * 2.5 +
        df["is_ac"] * 3.5 +
        df["is_wifi"] * 1.5 +
        df["ada_tv"] * 0.5 +
        df["ada_meja_belajar"] * 0.5 +
        df["parkir_mobil"] * 0.5 +
        df["dapur_pribadi"] * 0.5 +
        df["keamanan_penjaga"] * 0.5
    ).round(1)

    df["indeks_aksesibilitas_lokasi"] = (
        (1.0 / (1.0 + df["jarak_ke_kampus_kantor_sekolah_terdekat_km"])) * 35 +
        (1.0 / (1.0 + df["jarak_ke_pasar_km"])) * 25 +
        (1.0 / (1.0 + df["jarak_krusial_km"])) * 20 +
        (1.0 / (1.0 + df["jarak_ke_jalan_raya_m"] / 100.0)) * 20
    ).round(1)

    print("[3/4] BUILD STAR SCHEMA: Menyusun 4 Tabel Dimensi dan 1 Tabel Fakta...")
    # Dimensi 1: dim_lokasi
    lok_cols = ["kecamatan", "desa_kelurahan", "nama_tempat_krusial", "area_tempat_makan"]
    dim_lokasi = df[lok_cols].drop_duplicates().reset_index(drop=True)
    dim_lokasi["id_lokasi"] = [f"LOK_{i+1:03d}" for i in range(len(dim_lokasi))]
    dim_lokasi = dim_lokasi[["id_lokasi"] + lok_cols]

    # Dimensi 2: dim_spesifikasi_kamar
    spek_cols = [
        "luas_kamar_m2", "jumlah_lantai", "tipe_kamar_mandi", "kelengkapan_kamar_mandi",
        "ac_non_ac", "fasilitas", "fasilitas_kamar_detail",
        "ada_lemari", "ada_kasur", "ada_tv", "ada_meja_belajar", "kloset_duduk", "ada_shower", "ada_water_heater"
    ]
    dim_spesifikasi = df[spek_cols].drop_duplicates().reset_index(drop=True)
    dim_spesifikasi["id_spesifikasi"] = [f"SPK_{i+1:03d}" for i in range(len(dim_spesifikasi))]
    dim_spesifikasi = dim_spesifikasi[["id_spesifikasi"] + spek_cols]

    # Dimensi 3: dim_fasilitas_aturan
    aturan_cols = [
        "kategori_penghuni", "sumber_air_utama", "wifi_non_wifi", "fasilitas_dapur_kulkas",
        "dapur", "fasilitas_cuci_jemur", "lahan_parkir", "keamanan_kos",
        "aturan_jam_malam_masuk", "kapasitas_kamar", "skema_biaya_listrik"
    ]
    dim_aturan = df[aturan_cols].drop_duplicates().reset_index(drop=True)
    dim_aturan["id_aturan"] = [f"ATR_{i+1:03d}" for i in range(len(dim_aturan))]
    dim_aturan = dim_aturan[["id_aturan"] + aturan_cols]

    # Dimensi 4: dim_kontrak_sewa
    kontrak_cols = ["sewa_tahunan_bulanan", "is_tahunan", "tahun_mulai_sewa"]
    dim_kontrak = df[kontrak_cols].drop_duplicates().reset_index(drop=True)
    dim_kontrak["id_kontrak"] = [f"KTK_{i+1:02d}" for i in range(len(dim_kontrak))]
    dim_kontrak["faktor_konversi_bulanan"] = np.where(dim_kontrak["is_tahunan"] == 1, 12, 1)
    dim_kontrak = dim_kontrak[["id_kontrak", "sewa_tahunan_bulanan", "is_tahunan", "tahun_mulai_sewa", "faktor_konversi_bulanan"]]

    # Join Foreign Keys ke Tabel Fakta
    fact = df.merge(dim_lokasi, on=lok_cols, how="left")
    fact = fact.merge(dim_spesifikasi, on=spek_cols, how="left")
    fact = fact.merge(dim_aturan, on=aturan_cols, how="left")
    fact = fact.merge(dim_kontrak, on=kontrak_cols, how="left")

    fact_sewa_kos = fact[[
        "id_kost", "kode_unit_kos", "nama_kost", "id_lokasi", "id_spesifikasi", "id_aturan", "id_kontrak",
        "harga_sewa", "harga_bulanan_norm",
        "jarak_ke_kampus_kantor_sekolah_terdekat_km", "jarak_ke_pasar_km",
        "jarak_krusial_km", "jarak_laundry_m", "jarak_ibadah_m", "jarak_pusat_kota_m", "jarak_ke_jalan_raya_m",
        "skor_kelengkapan_fasilitas", "indeks_aksesibilitas_lokasi",
        "latitude", "longitude", "source_url"
    ]]

    print("[4/4] LOAD TO SQLITE DATA WAREHOUSE:", DB_PATH)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    tmp_db = os.path.join(tempfile.gettempdir(), "tobakost_warehouse_build.db")
    if os.path.exists(tmp_db):
        os.remove(tmp_db)
    conn = sqlite3.connect(tmp_db)
    dim_lokasi.to_sql("dim_lokasi", conn, index=False, if_exists="replace")
    dim_spesifikasi.to_sql("dim_spesifikasi_kamar", conn, index=False, if_exists="replace")
    dim_aturan.to_sql("dim_fasilitas_aturan", conn, index=False, if_exists="replace")
    dim_kontrak.to_sql("dim_kontrak_sewa", conn, index=False, if_exists="replace")
    fact_sewa_kos.to_sql("fact_sewa_kos", conn, index=False, if_exists="replace")

    conn.execute("""
    CREATE VIEW vw_mart_kos_lengkap AS
    SELECT
        f.id_kost,
        f.kode_unit_kos,
        f.nama_kost,
        l.id_lokasi,
        l.kecamatan,
        l.desa_kelurahan,
        l.nama_tempat_krusial,
        l.area_tempat_makan,
        s.id_spesifikasi,
        s.luas_kamar_m2,
        s.jumlah_lantai,
        s.tipe_kamar_mandi,
        s.kelengkapan_kamar_mandi,
        s.ac_non_ac,
        s.fasilitas,
        s.fasilitas_kamar_detail,
        s.ada_lemari,
        s.ada_kasur,
        s.ada_tv,
        s.ada_meja_belajar,
        s.kloset_duduk,
        s.ada_shower,
        s.ada_water_heater,
        a.id_aturan,
        a.kategori_penghuni,
        a.sumber_air_utama,
        a.wifi_non_wifi,
        a.fasilitas_dapur_kulkas,
        a.dapur,
        a.fasilitas_cuci_jemur,
        a.lahan_parkir,
        a.keamanan_kos,
        a.aturan_jam_malam_masuk,
        a.kapasitas_kamar,
        a.skema_biaya_listrik,
        k.id_kontrak,
        k.sewa_tahunan_bulanan,
        k.is_tahunan,
        k.tahun_mulai_sewa,
        f.harga_sewa,
        f.harga_bulanan_norm,
        f.jarak_ke_kampus_kantor_sekolah_terdekat_km,
        f.jarak_ke_pasar_km,
        f.jarak_krusial_km,
        f.jarak_laundry_m,
        f.jarak_ibadah_m,
        f.jarak_pusat_kota_m,
        f.jarak_ke_jalan_raya_m,
        f.skor_kelengkapan_fasilitas,
        f.indeks_aksesibilitas_lokasi,
        f.latitude,
        f.longitude,
        f.source_url
    FROM fact_sewa_kos f
    JOIN dim_lokasi l ON f.id_lokasi = l.id_lokasi
    JOIN dim_spesifikasi_kamar s ON f.id_spesifikasi = s.id_spesifikasi
    JOIN dim_fasilitas_aturan a ON f.id_aturan = a.id_aturan
    JOIN dim_kontrak_sewa k ON f.id_kontrak = k.id_kontrak;
    """)
    conn.commit()
    conn.close()
    shutil.copy2(tmp_db, DB_PATH)
    print(f"ETL Selesai! {raw_count} baris Google Form berhasil dimuat ke Star Schema Data Warehouse.")

if __name__ == "__main__":
    run_etl()
