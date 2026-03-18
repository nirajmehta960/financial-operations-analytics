"""
Load raw Superstore CSV into SQLite for the SQL-first ETL pipeline.

Creates/overwrites the raw table expected by `sql/etl/*.sql`:
- superstore_raw
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "superstore.sqlite"
DEFAULT_RAW_CSV_PATH = PROJECT_ROOT / "data" / "raw" / "superstore.csv"


def _quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _create_table_from_csv_header(conn: sqlite3.Connection, *, table: str, header: list[str]) -> None:
    cols = ", ".join(f"{_quote_ident(c)} TEXT" for c in header)
    conn.execute(f"DROP TABLE IF EXISTS {_quote_ident(table)};")
    conn.execute(f"CREATE TABLE {_quote_ident(table)} ({cols});")


def _insert_csv_rows(
    conn: sqlite3.Connection,
    *,
    table: str,
    header: list[str],
    rows: list[list[str]],
) -> None:
    placeholders = ", ".join(["?"] * len(header))
    col_list = ", ".join(_quote_ident(c) for c in header)
    conn.executemany(
        f"INSERT INTO {_quote_ident(table)} ({col_list}) VALUES ({placeholders});",
        rows,
    )


def load_csv_to_sqlite(
    *,
    db_path: Path,
    csv_path: Path,
    table: str = "superstore_raw",
    encoding: str = "latin-1",
    chunk_size: int = 5000,
) -> None:
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing raw file: {csv_path}")

    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys = ON;")

        with csv_path.open("r", encoding=encoding, newline="") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                raise ValueError(f"Empty CSV file: {csv_path}")

            _create_table_from_csv_header(conn, table=table, header=header)

            batch: list[list[str]] = []
            for row in reader:
                if len(row) != len(header):
                    if len(row) < len(header):
                        row = row + ([""] * (len(header) - len(row)))
                    else:
                        row = row[: len(header)]
                batch.append(row)
                if len(batch) >= chunk_size:
                    _insert_csv_rows(conn, table=table, header=header, rows=batch)
                    batch.clear()

            if batch:
                _insert_csv_rows(conn, table=table, header=header, rows=batch)

        conn.commit()
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Load raw Superstore CSV into SQLite.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="Path to SQLite DB file.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_RAW_CSV_PATH, help="Path to raw superstore.csv.")
    parser.add_argument("--table", default="superstore_raw", help="Destination raw table name.")
    parser.add_argument("--encoding", default="latin-1", help="CSV encoding (default: latin-1).")
    args = parser.parse_args()

    load_csv_to_sqlite(db_path=args.db, csv_path=args.csv, table=args.table, encoding=args.encoding)
    print(f"Raw load complete. DB at {args.db}")


if __name__ == "__main__":
    main()

