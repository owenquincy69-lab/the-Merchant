
import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "merchant.db"


@contextmanager
def get_db():
    connection = sqlite3.connect(DB_PATH, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'customer',
            referral_code TEXT NOT NULL UNIQUE,
            referred_by INTEGER REFERENCES users(id),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL DEFAULT 'General',
            price REAL NOT NULL CHECK(price >= 0),
            image_url TEXT NOT NULL DEFAULT '',
            stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            total REAL NOT NULL CHECK(total >= 0),
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL REFERENCES orders(id),
            product_id INTEGER NOT NULL REFERENCES products(id),
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            unit_price REAL NOT NULL CHECK(unit_price >= 0)
        );

        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER NOT NULL REFERENCES users(id),
            referred_user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
            status TEXT NOT NULL DEFAULT 'Registered',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)

        count = db.execute(
            "SELECT COUNT(*) AS total FROM products"
        ).fetchone()["total"]

        if count == 0:
            products = [
                (
                    "Everyday Classic Sneakers",
                    "Versatile everyday footwear.",
                    "Fashion",
                    2499,
                    "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=85",
                    20,
                ),
                (
                    "Minimalist Wristwatch",
                    "A clean, timeless everyday accessory.",
                    "Accessories",
                    3499,
                    "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=85",
                    15,
                ),
                (
                    "Wireless Headphones",
                    "Wireless listening for everyday use.",
                    "Electronics",
                    4299,
                    "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=85",
                    12,
                ),
                (
                    "Everyday Backpack",
                    "A practical bag for work and travel.",
                    "Lifestyle",
                    2899,
                    "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=900&q=85",
                    18,
                ),
                (
                    "Classic Sunglasses",
                    "A simple finishing touch for your outfit.",
                    "Accessories",
                    1499,
                    "https://images.unsplash.com/photo-1511499767150-a48a237f0083?auto=format&fit=crop&w=900&q=85",
                    25,
                ),
                (
                    "Modern Desk Lamp",
                    "Minimal lighting for your workspace.",
                    "Home",
                    2199,
                    "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=900&q=85",
                    10,
                ),
            ]

            db.executemany("""
                INSERT INTO products
                (name, description, category, price, image_url, stock)
                VALUES (?, ?, ?, ?, ?, ?)
            """, products)
