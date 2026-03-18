"""
Run the SQL-first ETL pipeline (SQLite).

This runner executes SQL scripts in `sql/etl/` in lexical order against a SQLite DB.
It assumes the raw load step has created table:
- superstore_raw
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "superstore.sqlite"
DEFAULT_SQL_DIR = PROJECT_ROOT / "sql" / "etl"


def _read_sql(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def run_sql_etl(db_path: Path, sql_dir: Path) -> None:
    sql_files = sorted(p for p in sql_dir.glob("*.sql") if p.is_file())
    if not sql_files:
        raise FileNotFoundError(f"No .sql files found in {sql_dir}")

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        for sql_file in sql_files:
            sql = _read_sql(sql_file).strip()
            if not sql:
                continue
            conn.executescript(sql + "\n")
        conn.commit()
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SQL ETL pipeline (SQLite).")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="Path to SQLite DB file.")
    parser.add_argument("--sql-dir", type=Path, default=DEFAULT_SQL_DIR, help="Directory containing ETL SQL scripts.")
    args = parser.parse_args()

    args.db.parent.mkdir(parents=True, exist_ok=True)
    run_sql_etl(args.db, args.sql_dir)
    print(f"SQL ETL complete. DB at {args.db}")


if __name__ == "__main__":
    main()

