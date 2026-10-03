import sqlite3

def init_db():
    conn = sqlite3.connect("people.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS counts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            in_count INTEGER,
            out_count INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def insert_count(in_count, out_count):
    conn = sqlite3.connect("people.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO counts (in_count, out_count) VALUES (?, ?)",
        (in_count, out_count)
    )

    conn.commit()
    conn.close()