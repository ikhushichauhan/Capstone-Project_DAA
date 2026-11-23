"""SQLite storage for products and saved comparison runs."""
import os
import sqlite3
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("KNAPSACK_DB", os.path.join(BASE_DIR, "inventory.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    category   TEXT    NOT NULL DEFAULT 'General',
    weight     INTEGER NOT NULL CHECK (weight > 0),
    profit     REAL    NOT NULL CHECK (profit > 0),
    created_at TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS runs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at          TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    capacity            INTEGER NOT NULL,
    n_items             INTEGER NOT NULL,
    fractional_profit   REAL,
    greedy_whole_profit REAL,
    dp_profit           REAL,
    fractional_ms       REAL,
    greedy_whole_ms     REAL,
    dp_ms               REAL
);
"""

# (name, category, weight in kg, profit). Chosen so that greedy-whole and DP
# give different answers at capacity 50 - a good demo of why DP is needed.
SAMPLE_PRODUCTS = [
    ("Smartphone Boxes", "Electronics", 5, 150),
    ("LED Monitors", "Electronics", 15, 210),
    ("Headphone Packs", "Electronics", 4, 80),
    ("Office Chairs", "Furniture", 25, 250),
    ("Basmati Rice Sacks", "Grocery", 20, 100),
    ("Cooking Oil Crates", "Grocery", 18, 126),
    ("Medicine Cartons", "Pharma", 8, 200),
    ("Winter Jackets", "Apparel", 12, 96),
    ("Toy Sets", "Toys", 7, 49),
    ("Water Purifiers", "Appliances", 30, 270),
]


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create tables. A brand-new database is filled with sample products."""
    is_new = not os.path.exists(DB_PATH)
    with connect() as conn:
        conn.executescript(SCHEMA)
        if is_new:
            conn.executemany(
                "INSERT INTO products (name, category, weight, profit) VALUES (?, ?, ?, ?)",
                SAMPLE_PRODUCTS,
            )


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------
def clean_product(data):
    """Validate and normalise product input. Raises ValueError with a clear message."""
    name = str(data.get("name", "")).strip()
    category = str(data.get("category", "")).strip() or "General"

    if not name:
        raise ValueError("Product name is required.")
    if len(name) > 60:
        raise ValueError("Product name must be 60 characters or fewer.")
    if len(category) > 30:
        raise ValueError("Category must be 30 characters or fewer.")

    try:
        weight = float(data.get("weight"))
    except (TypeError, ValueError):
        raise ValueError("Weight must be a number.")
    if not weight.is_integer() or weight <= 0:
        raise ValueError("Weight must be a positive whole number of kg "
                         "(the DP table needs integer weights).")
    if weight > 100_000:
        raise ValueError("Weight must not exceed 100,000 kg.")

    try:
        profit = float(data.get("profit"))
    except (TypeError, ValueError):
        raise ValueError("Profit must be a number.")
    if not (0 < profit <= 1_000_000_000):
        raise ValueError("Profit must be greater than 0.")

    return name, category, int(weight), round(profit, 2)


# --------------------------------------------------------------------------
# Products
# --------------------------------------------------------------------------
def list_products():
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, name, category, weight, profit FROM products ORDER BY id"
        ).fetchall()
    return [dict(r) for r in rows]


def get_product(pid):
    with connect() as conn:
        row = conn.execute(
            "SELECT id, name, category, weight, profit FROM products WHERE id = ?", (pid,)
        ).fetchone()
    return dict(row) if row else None


def add_product(data):
    name, category, weight, profit = clean_product(data)
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO products (name, category, weight, profit) VALUES (?, ?, ?, ?)",
            (name, category, weight, profit),
        )
        pid = cur.lastrowid
    return get_product(pid)


def update_product(pid, data):
    name, category, weight, profit = clean_product(data)
    with connect() as conn:
        cur = conn.execute(
            "UPDATE products SET name=?, category=?, weight=?, profit=? WHERE id=?",
            (name, category, weight, profit, pid),
        )
        if cur.rowcount == 0:
            return None
    return get_product(pid)


def delete_product(pid):
    with connect() as conn:
        return conn.execute("DELETE FROM products WHERE id = ?", (pid,)).rowcount > 0


def clear_products():
    with connect() as conn:
        conn.execute("DELETE FROM products")


def load_samples():
    """Replace all products with the sample data set."""
    with connect() as conn:
        conn.execute("DELETE FROM products")
        conn.executemany(
            "INSERT INTO products (name, category, weight, profit) VALUES (?, ?, ?, ?)",
            SAMPLE_PRODUCTS,
        )


# --------------------------------------------------------------------------
# Saved comparison runs
# --------------------------------------------------------------------------
def save_run(capacity, n_items, results):
    with connect() as conn:
        conn.execute(
            """INSERT INTO runs (capacity, n_items,
                   fractional_profit, greedy_whole_profit, dp_profit,
                   fractional_ms, greedy_whole_ms, dp_ms)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                capacity, n_items,
                results["fractional"]["total_profit"],
                results["greedy_whole"]["total_profit"],
                results["dp"]["total_profit"],
                results["fractional"]["time_ms"],
                results["greedy_whole"]["time_ms"],
                results["dp"]["time_ms"],
            ),
        )


def list_runs(limit=50):
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def clear_runs():
    with connect() as conn:
        conn.execute("DELETE FROM runs")
