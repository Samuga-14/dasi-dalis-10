"""Safe access helpers for the SQLite star-schema warehouse."""

import sqlite3
from contextlib import contextmanager

from server_config import DB_PATH


REQUIRED_OBJECTS = {
    "fact_sewa_kos",
    "dim_lokasi",
    "dim_spesifikasi_kamar",
    "dim_fasilitas_aturan",
    "dim_kontrak_sewa",
    "vw_mart_kos_lengkap",
}

READABLE_OBJECTS = REQUIRED_OBJECTS


@contextmanager
def connection():
    """Open a short-lived connection with foreign keys and a busy timeout."""
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    try:
        yield conn
    finally:
        conn.close()


def connect():
    """Return a configured connection for transactions owned by a caller."""
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def validate() -> int:
    """Verify SQLite integrity and required star-schema objects."""
    with connection() as conn:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise sqlite3.DatabaseError(f"SQLite integrity check gagal: {integrity}")
        objects = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
            )
        }
        missing = REQUIRED_OBJECTS - objects
        if missing:
            raise sqlite3.DatabaseError(
                f"Objek Star Schema tidak ditemukan: {', '.join(sorted(missing))}"
            )
        return int(conn.execute("SELECT COUNT(*) FROM vw_mart_kos_lengkap").fetchone()[0])


def ensure_readable_object(name: str) -> str:
    """Allow only known table/view names before interpolating SQL identifiers."""
    if name not in READABLE_OBJECTS:
        raise ValueError("Nama tabel tidak diizinkan.")
    return name
