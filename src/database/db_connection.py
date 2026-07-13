import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "database" / "retail.db"

def get_connection():
    return sqlite3.connect(DB_PATH)