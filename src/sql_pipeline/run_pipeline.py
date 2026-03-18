"""
End-to-end runner for the SQL-first pipeline (SQLite):
1) Load raw CSV into SQLite raw table
2) Execute `sql/etl/*.sql` in lexical order
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.sql_pipeline.load_raw import load_csv_to_sqlite, DEFAULT_RAW_CSV_PATH
from src.sql_pipeline.run_etl import run_sql_etl, DEFAULT_SQL_DIR, DEFAULT_DB_PATH


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full SQL-first pipeline (SQLite).")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="Path to SQLite DB file.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_RAW_CSV_PATH, help="Path to raw superstore.csv.")
    parser.add_argument("--sql-dir", type=Path, default=DEFAULT_SQL_DIR, help="Directory containing ETL SQL scripts.")
    parser.add_argument("--encoding", default="latin-1", help="CSV encoding (default: latin-1).")
    args = parser.parse_args()

    load_csv_to_sqlite(db_path=args.db, csv_path=args.csv, table="superstore_raw", encoding=args.encoding)
    run_sql_etl(args.db, args.sql_dir)
    print("SQL-first pipeline complete.")


if __name__ == "__main__":
    main()

