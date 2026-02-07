#!/usr/bin/env python3
"""
Add sample tables to table_details for testing.
Run this once to populate the Table Management page with test data.
"""
import sqlite3
import os

def add_sample_tables():
    """Add sample tables to the database"""
    # Determine database location (same logic as app.py)
    if os.path.exists('/data'):
        db_path = '/data/restaurant.db'
    elif os.path.exists('/persistent'):
        db_path = '/persistent/restaurant.db'
    else:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'restaurant.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Get the first admin user (represents a hotel/restaurant)
        c.execute('SELECT id FROM admin_users LIMIT 1')
        admin = c.fetchone()
        
        if not admin:
            print("Error: No admin users found in database. Register an admin first.")
            conn.close()
            return False
        
        hotel_id = admin[0]
        print(f"Adding sample tables to hotel_id: {hotel_id}")
        
        # Sample tables data
        sample_tables = [
            (hotel_id, 1, 'Main Hall', 4, 'available', '', 'Standard seating'),
            (hotel_id, 2, 'Main Hall', 4, 'available', '', 'Standard seating'),
            (hotel_id, 3, 'Main Hall', 4, 'available', '', 'Standard seating'),
            (hotel_id, 4, 'Main Hall', 2, 'available', '', 'Corner table'),
            (hotel_id, 5, 'Main Hall', 6, 'available', '', 'Large table'),
            (hotel_id, 6, 'Patio', 4, 'reserved', '', 'Outdoor seating'),
            (hotel_id, 7, 'Patio', 2, 'available', '', 'Outdoor seating'),
            (hotel_id, 8, 'Private Room', 8, 'occupied', 'John', 'Private event'),
        ]
        
        # Insert sample tables
        for table_data in sample_tables:
            c.execute('''INSERT INTO table_details 
                        (hotel_id, table_number, table_section, capacity, 
                         table_status, assigned_waiter, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''', table_data)
        
        conn.commit()
        print(f"✓ Successfully added {len(sample_tables)} sample tables!")
        print("\nTables added:")
        for i, table in enumerate(sample_tables, 1):
            print(f"  {i}. Table {table[1]} in {table[2]} (Capacity: {table[3]}, Status: {table[4]})")
        
        conn.close()
        return True
    
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == '__main__':
    add_sample_tables()
