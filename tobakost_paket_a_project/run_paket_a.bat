@echo off
cd /d "%~dp0"
echo ===============================================================
echo   Menjalankan TobaKost Analytics & ML (Arsitektur Paket A)
echo   Backend: Python REST API + SQLite Star Schema Data Warehouse
echo   Frontend: HTML + CSS + JavaScript modular + Plotly.js + Leaflet.js
echo ===============================================================
python server.py
if errorlevel 1 (
  echo.
  echo Server gagal dijalankan. Pastikan dependency terpasang:
  echo python -m pip install -r requirements.txt
)
pause
