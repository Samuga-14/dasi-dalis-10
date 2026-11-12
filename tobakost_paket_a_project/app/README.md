# Application Boundary

Struktur final dosen menempatkan dashboard dan modul prediksi di `app/`.

Untuk prototype saat ini:

- Frontend aktif berada di `frontend/`.
- Backend aktif berada di `backend/` dan dapat dijalankan melalui `server.py`.
- API client frontend berada di `frontend/js/services/api.js`.

Migrasi fisik ke `app/` dilakukan setelah kontrak API FastAPI disepakati agar tidak merusak
dashboard yang sedang dikerjakan anggota frontend.
