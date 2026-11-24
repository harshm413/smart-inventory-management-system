"""
Shared PostgreSQL connection helpers.

Keeping database settings in one file avoids repeating the same connection
code in every pipeline script.
"""

from __future__ import annotations

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = PROJECT_ROOT / "sql"

load_dotenv(PROJECT_ROOT / ".env")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "inventory_reorder_system")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_MAINTENANCE_DB = os.getenv("DB_MAINTENANCE_DB", "postgres")


def connection_params(database: str | None = None) -> dict[str, str]:
    """Build connection parameters from environment variables."""
    params = {
        "host": DB_HOST,
        "port": DB_PORT,
        "dbname": database or DB_NAME,
        "user": DB_USER,
    }
    if DB_PASSWORD:
        params["password"] = DB_PASSWORD
    return params


def connect(database: str | None = None):
    """Open a PostgreSQL connection."""
    return psycopg2.connect(**connection_params(database))


def run_sql_file(conn, filename: str) -> None:
    """Run a SQL file from the sql folder."""
    path = SQL_DIR / filename
    sql_text = path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql_text)
    conn.commit()
    print(f"Ran {path.relative_to(PROJECT_ROOT)}")
