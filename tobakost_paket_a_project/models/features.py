"""Shared feature engineering for training and model inference."""

import pandas as pd


FEATURE_COLS = [
    "luas_kamar_m2", "jumlah_lantai", "km_dalam", "is_ac", "is_wifi",
    "ada_tv", "ada_meja_belajar", "parkir_mobil", "dapur_pribadi", "dapur_bersama",
    "keamanan_penjaga", "keamanan_cctv", "bebas_24jam", "listrik_termasuk",
    "jarak_ke_kampus_kantor_sekolah_terdekat_km", "jarak_ke_pasar_km",
    "jarak_krusial_km", "jarak_ke_jalan_raya_m", "is_tahunan",
    "skor_kelengkapan_fasilitas", "indeks_aksesibilitas_lokasi"
]


def add_model_features(df):
    """Apply the same binary and derived features used by the ETL pipeline."""
    df = df.copy()
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
    return add_derived_features(df)


def add_derived_features(df):
    """Calculate the shared facility score and location-accessibility index."""
    df = df.copy()
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
    return df


def build_feature_frame(df):
    """Return model input in the canonical training and inference column order."""
    missing = [column for column in FEATURE_COLS if column not in df.columns]
    if missing:
        raise ValueError(f"Fitur model tidak tersedia: {', '.join(missing)}")
    return df.loc[:, FEATURE_COLS]
