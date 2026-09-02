"""
02_load_to_sqlite.py

Loads the clean, analysis-ready dataset into a SQLite database.
The database serves as the querying layer for the analytical work in Step 3.
"""

import pandas as pd
import sqlite3
import os

DATA = "data"
DB_PATH = "outputs/wso_conversion.db"

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

df = pd.read_csv(f"{DATA}/conversion_dataset.csv")

conn = sqlite3.connect(DB_PATH)
df.to_sql("users", conn, index=False, if_exists="replace")

cur = conn.cursor()
for col in ["profile_source", "school_tier", "class_year", "major_cat", "upgraded"]:
    cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{col} ON users({col});")
conn.commit()

n_rows = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
n_cols = len(cur.execute("PRAGMA table_info(users)").fetchall())
n_pos  = cur.execute("SELECT SUM(upgraded) FROM users").fetchone()[0]

print(f"Loaded 'users' table into {DB_PATH}")
print(f"  Rows:       {n_rows:,}")
print(f"  Columns:    {n_cols}")
print(f"  Upgraders:  {n_pos:,}  ({n_pos/n_rows*100:.1f}%)")
conn.close()
