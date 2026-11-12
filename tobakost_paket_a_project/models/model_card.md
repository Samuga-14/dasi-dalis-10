# Model Card

## Status

Model aktif saat ini masih model baseline berbasis data dummy. Jangan menganggap metriknya
sebagai performa pada data riil.

## Ringkasan

- Target: `harga_bulanan_norm`.
- Kandidat: Linear Regression, Ridge, Random Forest, dan Gradient Boosting.
- Artifact aktif: `models/best_rf_model.pkl`.
- Feature engineering: `models/features.py`.
- Metrik: `models/metrics_summary.json`.

## Batasan

- Model terikat pada versi scikit-learn yang tercatat di bundle.
- Data dummy tidak mewakili jaminan performa pada data riil.
- Prediksi adalah estimasi, bukan penetapan harga.
- Model riil harus dibuat sebagai versi baru dengan data quality report dan evaluasi subgroup.
