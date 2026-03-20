"""
CrewIQ — Module 2: Load CSVs into SQLite
=========================================
Loads all 4 CSV datasets into a local SQLite database (crewiq.db)
so we can run SQL analytics against them.

Run this ONCE before running any SQL scripts:
    python notebooks/02_load_to_sqlite.py
"""

import sqlite3
import pandas as pd
import os

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH  = os.path.join(BASE_DIR, 'crewiq.db')

# ── Load CSVs ────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("  CrewIQ — Module 2: Loading data into SQLite")
print("="*60)

conn = sqlite3.connect(DB_PATH)

datasets = {
    'crew_roster':     'crew_roster.csv',
    'flight_schedule': 'flight_schedule.csv',
    'disruptions':     'disruptions.csv',
    'fatigue_logs':    'fatigue_logs.csv',
}

for table_name, filename in datasets.items():
    path = os.path.join(DATA_DIR, filename)
    df   = pd.read_csv(path)
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    print(f"  ✓ {table_name:<20} {len(df):>6,} rows loaded")

conn.close()

print(f"\n  Database saved to: crewiq.db")
print("  Run SQL scripts with: sqlite3 crewiq.db < sql/filename.sql")
print("="*60 + "\n")
