# Aturan Kontribusi Kelompok

## Strategi branch

Kelompok boleh mengerjakan semua bagian proyek dari branch anggota masing-masing. Branch tidak
dibagi berdasarkan domain pekerjaan.

```text
main       # versi stabil dan checkpoint
└── develop       # integrasi seluruh pekerjaan tim
    ├── develop-1 # branch kerja anggota 1
    ├── develop-2 # branch kerja anggota 2
    ├── develop-3 # branch kerja anggota 3
    ├── develop-4 # branch kerja anggota 4
    └── develop-5 # branch kerja anggota 5
```

Alur perubahan:

1. Buat issue untuk setiap tugas.
2. Kerjakan tugas pada `develop-<nomor>`.
3. Gunakan Conventional Commit dan cantumkan nomor issue:
   `feat: tambah visualisasi distribusi harga (#12)`.
4. Buka Pull Request dari `develop-<nomor>` ke `develop`.
5. Minta minimal satu review anggota lain.
6. Setelah stabil, buka Pull Request dari `develop` ke `main` untuk checkpoint atau rilis.

Jangan push langsung ke `main` atau `develop`. Setiap anggota memakai akun GitHub sendiri agar
kontribusi tercatat pada Contributors. Branch kerja lama `team/*` sudah dihapus karena tidak
memiliki commit unik.

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
