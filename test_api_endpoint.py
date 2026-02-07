import sqlite3
from flask import Flask, session
import sys
sys.path.insert(0, '.')

# Simulate Flask request context
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test'

with app.test_request_context():
    session['admin_id'] = 1  # Royal Restaurant
    
    import app as app_module
    
    # Call the function directly
    hotel_id = app_module.get_current_hotel_id()
    print(f"Current Hotel ID: {hotel_id}")
    
    # Get tables
    conn = app_module.get_db()
    c = conn.cursor()
    
    c.execute('SELECT id, hotel_id, table_number, is_active FROM restaurant_tables WHERE hotel_id = ? ORDER BY table_number', 
             (hotel_id,))
    tables = c.fetchall()
    conn.close()
    
    print(f"\nTables from DB query: {len(tables)}")
    for table in tables:
        print(f"  - Table {table['table_number']} (ID: {table['id']}, Active: {table['is_active']})")
