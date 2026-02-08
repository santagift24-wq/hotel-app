
import sqlite3
import os

def get_db_path():
    if os.path.exists('/data'):
        return '/data/restaurant.db'
    elif os.path.exists('/persistent'):
        return '/persistent/restaurant.db'
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'restaurant.db')

DB_PATH = get_db_path()

def add_currency_column():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("PRAGMA table_info(settings)")
    columns = [row[1] for row in c.fetchall()]
    if 'currency' not in columns:
        c.execute("ALTER TABLE settings ADD COLUMN currency TEXT DEFAULT 'INR'")
        print("Added 'currency' column to settings table.")
    else:
        print("'currency' column already exists.")
    conn.commit()
    conn.close()

if __name__ == '__main__':
    print(f"Using DB: {DB_PATH}")
    add_currency_column()
