import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
db_path = BASE_DIR / "database" / "retail.db"
csv_path = BASE_DIR / "data" / "processed" / "processed_superstore.csv"
sql_dir = BASE_DIR / "sql"

if not csv_path.exists():
    raise FileNotFoundError(
        f"{csv_path} not found. Run notebooks 01 and 03 first to create it."
    )

df = pd.read_csv(csv_path)

with sqlite3.connect(db_path) as conn:
    conn.execute("DROP TABLE IF EXISTS Superstore")
    df.to_sql("Superstore", conn, index=False)

    # Dropping the table also drops its trigger, so rebuild the audit
    # table, views, trigger and indexes from the sql/ folder.
    for name in ["02_create_tables.sql", "07_views.sql",
                 "08_triggers.sql", "09_indexes.sql"]:
        conn.executescript((sql_dir / name).read_text(encoding="utf-8"))

    count = conn.execute("SELECT COUNT(*) FROM Superstore").fetchone()[0]

print("✅ Data imported successfully!")
print(f"Total Records: {count}")