import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parents[2] / "data" / "chatbot_escolar.db"

con = sqlite3.connect(DB)
for (nombre,) in con.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
):
    print(f"\n{nombre}")
    for col in con.execute(f"PRAGMA table_info({nombre})"):
        print(f"  - {col[1]} ({col[2]})")
con.close()