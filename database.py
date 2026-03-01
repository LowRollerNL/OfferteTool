import os
import sys
import sqlite3
from datetime import datetime

# ==========================
# Database pad (exe-proof)
# ==========================
def get_db_path():
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "offerte.db")

def get_connection():
    db_path = get_db_path()
    return sqlite3.connect(db_path)


# ==========================
# INIT DATABASE + MIGRATIONS
# ==========================
def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # ======================
    # db_version tabel
    # ======================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS db_version (
        version INTEGER PRIMARY KEY,
        applied_at TEXT
    )
    """)

    # Huidige versie checken
    cursor.execute("SELECT MAX(version) FROM db_version")
    row = cursor.fetchone()
    current_version = row[0] if row[0] is not None else 0

    # ======================
    # MIGRATIONS
    # ======================
    migrations = [
        # versie 1: basis tabellen
        (1, """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                address TEXT
            );
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                number TEXT,
                date TEXT,
                customer_id INTEGER,
                total_excl REAL,
                total_btw REAL,
                total_incl REAL
            );
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                btw_percent REAL NOT NULL
            );
        """),

        # versie 2: extra kolommen customers
        (2, """
            ALTER TABLE customers ADD COLUMN postal TEXT;
            ALTER TABLE customers ADD COLUMN city TEXT;
            ALTER TABLE customers ADD COLUMN kvk TEXT;
            ALTER TABLE customers ADD COLUMN btw TEXT;
            ALTER TABLE customers ADD COLUMN email TEXT;
        """),

        # versie 3: extra kolommen documents
        (3, """
            ALTER TABLE documents ADD COLUMN due_date TEXT;
            ALTER TABLE documents ADD COLUMN status TEXT;
            ALTER TABLE documents ADD COLUMN is_invoiced INTEGER DEFAULT 0;
            ALTER TABLE documents ADD COLUMN is_paid INTEGER DEFAULT 0;
            ALTER TABLE documents ADD COLUMN payment_id TEXT;
            ALTER TABLE documents ADD COLUMN payment_url TEXT;
            ALTER TABLE documents ADD COLUMN payment_status TEXT DEFAULT 'open';
            ALTER TABLE documents ADD COLUMN is_sent INTEGER DEFAULT 0;
        """),

        # versie 4: document_lines tabel
        (4, """
            CREATE TABLE IF NOT EXISTS document_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                description TEXT,
                quantity REAL,
                purchase_price REAL,
                sale_price REAL,
                profit_percent REAL,
                btw_percent REAL,
                total REAL
            );
        """)
    ]

    # Voer migraties uit die nog niet gedaan zijn
    for version, sql in migrations:
        if version > current_version:
            try:
                cursor.executescript(sql)
                cursor.execute("INSERT INTO db_version (version, applied_at) VALUES (?, ?)", 
                               (version, datetime.now().isoformat()))
                print(f"DB migratie versie {version} toegepast.")
            except sqlite3.OperationalError as e:
                print(f"Let op: migratie versie {version} gaf fout (kan al bestaan): {e}")

    conn.commit()
    conn.close()