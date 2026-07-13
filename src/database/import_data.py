import sqlite3
import pandas as pd
from pathlib import Path

# Project root folder
BASE_DIR = Path(__file__).resolve().parents[2]

# Database path
db_path = BASE_DIR / "database" / "retail.db"

# CSV file path
csv_path = BASE_DIR / "data" / "processed" / "processed_superstore.csv"

# Read CSV
df = pd.read_csv(csv_path)

# Connect to SQLite
conn = sqlite3.connect(db_path)

# Remove old table if it exists
conn.execute("DROP TABLE IF EXISTS Superstore")

# Import CSV as a new table
df.to_sql("Superstore", conn, index=False)

conn.commit()

# Verify row count
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM Superstore")
count = cursor.fetchone()[0]

print("✅ Data imported successfully!")
print(f"Total Records: {count}")

conn.close()