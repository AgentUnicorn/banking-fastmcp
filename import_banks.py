import csv
import sqlite3
from datetime import datetime

DB_PATH = "banking.db"  # path to your SQLite file
CSV_PATH = "data/banks.csv"  # path to your CSV file


def import_banks():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        count = 0

        for row in reader:
            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO banks (id, name, code, bin, short_name, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        int(row["id"]),
                        row["name"].strip(),
                        row["code"].strip(),
                        row["bin"].strip(),
                        row["shortName"].strip(),
                        datetime.now(),
                        datetime.now(),
                    ),
                )
                if cursor.rowcount > 0:
                    count += 1
            except Exception as e:
                print(f"⚠️ Error inserting row {row}: {e}")

    conn.commit()
    conn.close()
    print(f"✅ Imported {count} new banks successfully.")


if __name__ == "__main__":
    import_banks()
