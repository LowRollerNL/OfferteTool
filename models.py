import os
import sys
import sqlite3
from datetime import datetime

def resource_path(relative_path):
    """Geeft correct pad in PyInstaller exe"""
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)

DB_FILE = resource_path("database.db")  # vervang oude harde pad

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # ✅ zorgt voor dict-achtige rijen
    return conn

# ==========================
# Database initialisatie / upgrade
# ==========================
def init_db():
    conn = get_connection()
    cursor = conn.cursor()


    # =====================
    # Tabel customers
    # =====================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            address TEXT
        )
    """)

    cursor.execute("PRAGMA table_info(customers)")
    columns = [col[1] for col in cursor.fetchall()]

    if "postal" not in columns:
        cursor.execute("ALTER TABLE customers ADD COLUMN postal TEXT")
    if "city" not in columns:
        cursor.execute("ALTER TABLE customers ADD COLUMN city TEXT")

    # =====================
    # Tabel documents
    # =====================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            number TEXT,
            date TEXT,
            due_date TEXT,
            customer_id INTEGER,
            status TEXT,
            total_excl REAL,
            total_btw REAL,
            total_incl REAL,
            is_invoiced INTEGER DEFAULT 0,
            is_paid INTEGER DEFAULT 0,
            payment_id TEXT,
            payment_url TEXT,
            payment_status TEXT DEFAULT 'open'
        )
    """)

    # Check extra kolommen (upgrade bestaande DB)
    cursor.execute("PRAGMA table_info(documents)")
    columns = [col[1] for col in cursor.fetchall()]

    if "payment_id" not in columns:
        cursor.execute("ALTER TABLE documents ADD COLUMN payment_id TEXT")

    if "payment_url" not in columns:
        cursor.execute("ALTER TABLE documents ADD COLUMN payment_url TEXT")

    # =====================
    # Tabel document_lines
    # =====================
    cursor.execute("""
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
        )
    """)

    # =====================
    # Tabel items
    # =====================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            btw_percent REAL NOT NULL
        )
    """)

    # =====================
    # Tabel settings
    # =====================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            name TEXT,
            address TEXT,
            postal TEXT,
            city TEXT,
            phone TEXT,
            email TEXT,
            iban TEXT,
            bic TEXT,
            kvk TEXT,
            btw TEXT,
            logo_path TEXT,
            logo_width REAL DEFAULT 40,
            logo_height REAL DEFAULT 20
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO settings (id) VALUES (1)")

    # Voeg kolommen toe als ze nog niet bestaan (voor upgrade van oude DB)
    columns_needed = {
        "name": "TEXT",
        "address": "TEXT",
        "postal": "TEXT",
        "city": "TEXT",
        "phone": "TEXT",
        "email": "TEXT",
        "kvk": "TEXT",
        "btw": "TEXT",
        "logo_path": "TEXT",
        "logo_width": "REAL DEFAULT 40",
        "logo_height": "REAL DEFAULT 20"
}

    cursor.execute("PRAGMA table_info(settings)")
    existing_columns = [col[1] for col in cursor.fetchall()]

    for col_name, col_type in columns_needed.items():
        if col_name not in existing_columns:
            cursor.execute(f"ALTER TABLE settings ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()
    
# ==========================
# Customers
# ==========================
def create_customer(name, email, phone="", address="", postal="", city=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO customers (name, email, phone, address, postal, city) VALUES (?, ?, ?, ?, ?, ?)",
        (name, email, phone, address, postal, city)
    )
    conn.commit()
    customer_id = cursor.lastrowid
    conn.close()
    return customer_id

def get_customers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers")
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row   # <--- hier!
    return cursor.fetchall()
    return rows  # nu zijn rijen dict-achtig


def get_open_customers():
    """Return klanten die een open offerte hebben"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT c.id, c.name, c.email, c.phone, c.address
        FROM customers c
        JOIN documents d ON d.customer_id = c.id
        WHERE d.status='open'
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

# ==========================
# Documents
# ==========================
def create_document(doc):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO documents
        (type, number, date, due_date, customer_id, status,
         total_excl, total_btw, total_incl, is_invoiced)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        doc["type"],
        doc["number"],
        doc["date"],
        doc["due_date"],
        doc["customer_id"],
        doc["status"],
        doc["total_excl"],
        doc["total_btw"],
        doc["total_incl"],
        doc.get("is_invoiced", 0)  # ← ALTIJD 0 bij nieuwe offerte
    ))

    conn.commit()
    doc_id = cursor.lastrowid
    conn.close()
    return doc_id

def get_documents(doc_type):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM documents WHERE type = ?", (doc_type,))
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()

    conn.close()

    # 🔥 Elke rij omzetten naar dictionary
    return [dict(zip(columns, row)) for row in rows]

def delete_document(document_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM document_lines WHERE document_id=?", (document_id,))
    cursor.execute("DELETE FROM documents WHERE id=?", (document_id,))
    conn.commit()
    conn.close()

# ==========================
# Document lines
# ==========================
def add_document_line(document_id, line):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO document_lines
        (document_id, description, quantity, purchase_price, sale_price, profit_percent, btw_percent, total)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        document_id,
        line["description"],
        line["quantity"],
        line["purchase_price"],
        line["sale_price"],
        line["profit_percent"],
        line["btw_percent"],
        line["total"]
    ))
    conn.commit()
    conn.close()

def get_document_lines(document_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM document_lines WHERE document_id=?", (document_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_document(document_id, data):
    """Update kolommen van een document"""
    conn = get_connection()
    cursor = conn.cursor()
    fields = ", ".join([f"{k} = ?" for k in data.keys()])
    values = list(data.values())
    values.append(document_id)
    cursor.execute(f"UPDATE documents SET {fields} WHERE id = ?", values)
    conn.commit()
    conn.close()

def delete_document_lines(document_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM document_lines WHERE document_id = ?", (document_id,))
    conn.commit()
    conn.close()
    
def generate_document_number(doc_type):
    conn = get_connection()
    cursor = conn.cursor()

    year = datetime.now().year
    year_prefix = str(year)

    cursor.execute("""
        SELECT number FROM documents
        WHERE type = ? AND number LIKE ?
        ORDER BY number DESC LIMIT 1
    """, (doc_type, f"{year_prefix}%"))

    last = cursor.fetchone()
    conn.close()

    if last:
        last_number = int(last[0][-3:])  # laatste 3 cijfers
        new_number = last_number + 1
    else:
        new_number = 1

    return f"{year_prefix}{new_number:03d}"    
   
def get_paid_factures_total():
    """Return totaalbedrag van betaalde facturen"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(total_incl) FROM documents WHERE type='factuur' AND is_paid=1")
    total = cursor.fetchone()[0] or 0
    conn.close()
    return total
    
    # Artikelen CRUD
def get_items():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, btw_percent FROM items ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return rows

def create_item(name, price, btw_percent):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO items (name, price, btw_percent) VALUES (?, ?, ?)",
                   (name, price, btw_percent))
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return item_id
    
def update_item(item_id, name, price, btw_percent):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE items
        SET name=?, price=?, btw_percent=?
        WHERE id=?
    """, (name, price, btw_percent, item_id))
    conn.commit()
    conn.close()


def delete_item(item_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id=?", (item_id,))
    conn.commit()
    conn.close()      
    
# ==========================
# Bedrijfsinstellingen
# ==========================
def init_settings():
    """Zet standaard bedrijfsinstellingen in database als ze nog niet bestaan"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO settings 
        (id, name, address, postal, city, phone, email, kvk, btw, logo_path, logo_width, logo_height)
        VALUES (1, '', '', '', '', '', '', '', '', '', 40, 20)
    """)

    conn.commit()
    conn.close()


def migrate_settings_table():
    conn = get_connection()
    cursor = conn.cursor()

    columns_to_add = {
        "terms": "TEXT",
        "payment_term_days": "INTEGER DEFAULT 14",
        "mollie_api_key": "TEXT"
    }

    for column, definition in columns_to_add.items():
        try:
            cursor.execute(f"ALTER TABLE settings ADD COLUMN {column} {definition}")
        except:
            # Kolom bestaat al
            pass

    conn.commit()
    conn.close()

def get_settings():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, address, postal, city,
               phone, email, iban, bic, kvk, btw,
               logo_path, logo_width, logo_height, terms, payment_term_days, mollie_api_key
        FROM settings
        WHERE id=1
    """)
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "name": row[0],
            "address": row[1],
            "postal": row[2],
            "city": row[3],
            "phone": row[4],
            "email": row[5],
            "iban": row[6],
            "bic": row[7],
            "kvk": row[8],
            "btw": row[9],
            "logo_path": row[10],
            "logo_width": row[11],
            "logo_height": row[12],
            "terms": row[13],
            "payment_term_days": row[14],
            "mollie_api_key": row[15]


        }
    return {}

def save_settings(data):
    conn = conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE settings
        SET name=?, address=?, postal=?, city=?, phone=?, email=?, iban=?, bic=?, kvk=?, btw=?, logo_path=?, terms=?, payment_term_days=?, mollie_api_key=?
        WHERE id=1
    """, (
        data["name"],
        data["address"],
        data["postal"],
        data["city"],
        data["phone"],
        data["email"],
        data["iban"],
        data["bic"],
        data["kvk"], 
        data["btw"], 
        data["logo_path"], 
        data["terms"],
        data["payment_term_days"],
        data["mollie_api_key"]
    ))
    conn.commit()
    conn.close()    
    
def update_customer(customer_id, name=None, email=None, phone=None, address=None, postal=None, city=None):
    from models import get_connection
    conn = get_connection()
    c = conn.cursor()
    
    updates = []
    params = []

    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if email is not None:
        updates.append("email = ?")
        params.append(email)
    if phone is not None:
        updates.append("phone = ?")
        params.append(phone)
    if address is not None:
        updates.append("address = ?")
        params.append(address)
    if postal is not None:
        updates.append("postal = ?")
        params.append(postal)
    if city is not None:
        updates.append("city = ?")
        params.append(city)

    params.append(customer_id)

    if updates:
        c.execute(f"UPDATE customers SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()

    conn.close()
    
def delete_customer(customer_id):
    import sqlite3
    conn = sqlite3.connect("database.db")  # pas aan naar jouw DB pad
    c = conn.cursor()
    c.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    conn.commit()
    conn.close()    
    
    
