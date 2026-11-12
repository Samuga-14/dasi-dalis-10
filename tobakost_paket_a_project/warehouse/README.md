# Warehouse

Folder ini menjadi sumber kebenaran untuk DDL star schema dan ERD.

- `ddl/star_schema.sql`: kontrak tabel fakta, dimensi, key, dan view mart.
- `erd/star_schema.mmd`: diagram hubungan tabel.

Database hasil ETL boleh berbeda untuk development dan production, tetapi struktur analitik
harus mengikuti DDL yang didokumentasikan di sini.
