# Aturan Kontribusi Kelompok

## Alur perubahan

1. Buat issue untuk setiap tugas.
2. Buat branch dari `main`, misalnya `feat/visualisasi-harga`.
3. Gunakan Conventional Commit dan cantumkan nomor issue:
   `feat: tambah visualisasi distribusi harga (#12)`.
4. Buka Pull Request yang menautkan issue.
5. Minta minimal satu review anggota lain.
6. Merge hanya setelah checks dan approval selesai.

Jangan push langsung ke `main`. Setiap anggota memakai akun GitHub sendiri agar kontribusi
tercatat pada Contributors.

## Area kerja

| Area | Folder utama |
|---|---|
| Data dan ETL | `data/`, `etl/` |
| Warehouse dan ERD | `warehouse/` |
| EDA dan eksperimen | `notebooks/`, `models/` |
| Frontend dan visualisasi | `app/frontend/`, `frontend/` |
| Backend dan integrasi | `app/api/`, `app/services/`, `backend/` |
| Paper dan laporan | `paper/`, `reports/`, `docs/` |

Perubahan lintas area harus dijelaskan pada Pull Request.
