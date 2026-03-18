-- ============================================================
-- SQL ETL PIPELINE (SQLite) — INIT
-- Creates curated tables/views from the raw Superstore dataset.
--
-- Assumptions:
-- - Table `superstore_raw` exists (loaded from data/raw/superstore.csv)
-- ============================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

