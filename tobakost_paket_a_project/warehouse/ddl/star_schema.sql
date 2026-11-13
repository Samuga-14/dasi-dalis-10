-- Contract DDL for the TobaKost star schema.
-- The current ETL creates equivalent SQLite tables from pandas dataframes.

CREATE TABLE dim_lokasi (
    id_lokasi TEXT PRIMARY KEY,
    kecamatan TEXT NOT NULL,
    desa_kelurahan TEXT NOT NULL,
    nama_tempat_krusial TEXT,
    area_tempat_makan TEXT
);

CREATE TABLE dim_spesifikasi_kamar (
    id_spesifikasi TEXT PRIMARY KEY,
    luas_kamar_m2 REAL,
    jumlah_lantai INTEGER,
    tipe_kamar_mandi TEXT,
    kelengkapan_kamar_mandi TEXT,
    ac_non_ac TEXT,
    fasilitas TEXT,
    fasilitas_kamar_detail TEXT,
    jenis_kos TEXT NOT NULL CHECK (jenis_kos IN ('ekonomi', 'eksekutif'))
);

CREATE TABLE dim_fasilitas_aturan (
    id_aturan TEXT PRIMARY KEY,
    kategori_penghuni TEXT,
    sumber_air_utama TEXT,
    wifi_non_wifi TEXT,
    fasilitas_dapur_kulkas TEXT,
    dapur TEXT,
    fasilitas_cuci_jemur TEXT,
    lahan_parkir TEXT,
    keamanan_kos TEXT,
    aturan_jam_malam_masuk TEXT,
    kapasitas_kamar TEXT,
    skema_biaya_listrik TEXT
);

CREATE TABLE dim_kontrak_sewa (
    id_kontrak TEXT PRIMARY KEY,
    sewa_tahunan_bulanan TEXT,
    is_tahunan INTEGER,
    tahun_mulai_sewa TEXT
);

CREATE TABLE fact_sewa_kos (
    id_kost TEXT PRIMARY KEY,
    kode_unit_kos TEXT,
    nama_kost TEXT,
    id_lokasi TEXT NOT NULL REFERENCES dim_lokasi(id_lokasi),
    id_spesifikasi TEXT NOT NULL REFERENCES dim_spesifikasi_kamar(id_spesifikasi),
    id_aturan TEXT NOT NULL REFERENCES dim_fasilitas_aturan(id_aturan),
    id_kontrak TEXT NOT NULL REFERENCES dim_kontrak_sewa(id_kontrak),
    harga_sewa INTEGER,
    harga_bulanan_norm INTEGER,
    jarak_ke_kampus_kantor_sekolah_terdekat_km REAL,
    jarak_ke_pasar_km REAL,
    jarak_krusial_km REAL,
    jarak_laundry_m INTEGER,
    jarak_ibadah_m INTEGER,
    jarak_pusat_kota_m INTEGER,
    jarak_ke_jalan_raya_m INTEGER,
    skor_kelengkapan_fasilitas REAL,
    indeks_aksesibilitas_lokasi REAL,
    latitude REAL,
    longitude REAL,
    source_url TEXT
);
