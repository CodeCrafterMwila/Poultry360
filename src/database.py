import sqlite3
import os

DB_PATH = "poultry360.db"  # (or whatever path your project uses)

def get_connection():
    # Adding timeout=10.0 allows SQLite to wait up to 10 seconds for locks to clear
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Batches table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_name TEXT UNIQUE NOT NULL,
        production_type TEXT CHECK(production_type IN ('Conventional', 'Organic')) NOT NULL,
        initial_population INTEGER NOT NULL,
        placement_date TEXT NOT NULL,
        breed TEXT,
        supplier TEXT,
        expected_harvest_date TEXT,
        status TEXT CHECK(status IN ('Active', 'Archived')) DEFAULT 'Active'
    )
    """)

    # Daily records table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id INTEGER,
        record_date TEXT NOT NULL,
        day_number INTEGER,
        week_number INTEGER,
        opening_population INTEGER,
        deaths INTEGER DEFAULT 0,
        culls INTEGER DEFAULT 0,
        closing_population INTEGER,
        feed_consumed_kg REAL DEFAULT 0.0,
        water_consumed_liters REAL DEFAULT 0.0,
        temperature REAL,
        observations TEXT,
        notes TEXT,
        FOREIGN KEY (batch_id) REFERENCES batches (id),
        UNIQUE(batch_id, record_date)
    )
    """)

    # Health & Vaccination table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS health_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id INTEGER,
        record_date TEXT,
        treatment_type TEXT CHECK(treatment_type IN ('Vitamin', 'Vaccine', 'Medication', 'Treatment')) NOT NULL,
        item_name TEXT NOT NULL,
        dosage TEXT,
        administration_method TEXT,
        status TEXT CHECK(status IN ('Done', 'Pending', 'Skipped')) DEFAULT 'Pending',
        notes TEXT,
        FOREIGN KEY (batch_id) REFERENCES batches (id)
    )
    """)

    # Expenses table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        expense_date TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        amount REAL NOT NULL,
        batch_id INTEGER,
        FOREIGN KEY (batch_id) REFERENCES batches (id)
    )
    """)

    # Sales table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_date TEXT NOT NULL,
        customer_name TEXT NOT NULL,
        batch_id INTEGER,
        quantity_sold INTEGER NOT NULL,
        price_per_bird REAL NOT NULL,
        total_amount REAL NOT NULL,
        amount_paid REAL NOT NULL,
        payment_status TEXT CHECK(payment_status IN ('Paid', 'Partial', 'Unpaid')) DEFAULT 'Unpaid',
        FOREIGN KEY (batch_id) REFERENCES batches (id)
    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)