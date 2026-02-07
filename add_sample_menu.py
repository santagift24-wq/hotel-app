#!/usr/bin/env python3
"""
Add sample menu items to the database for testing.
Run this to populate the menu with test data.
"""
import sqlite3
import os

def add_sample_menu_items():
    """Add sample menu items to the database"""
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
        print(f"Adding sample menu items to hotel_id: {hotel_id}")

        # Sample menu items
        sample_menu = [
            (hotel_id, 'Margherita Pizza', 'Pizza', 12.99, 'Fresh tomato sauce, mozzarella cheese, basil', '/static/menu_images/pizza.jpg'),
            (hotel_id, 'Chicken Burger', 'Burgers', 8.99, 'Grilled chicken breast with lettuce, tomato, mayo', '/static/menu_images/burger.jpg'),
            (hotel_id, 'Caesar Salad', 'Salads', 7.99, 'Romaine lettuce, croutons, parmesan, caesar dressing', '/static/menu_images/salad.jpg'),
            (hotel_id, 'Pasta Carbonara', 'Pasta', 11.99, 'Creamy sauce with bacon, eggs, parmesan, black pepper', '/static/menu_images/pasta.jpg'),
            (hotel_id, 'Fish and Chips', 'Seafood', 13.99, 'Beer battered cod with fries and tartar sauce', '/static/menu_images/fish.jpg'),
            (hotel_id, 'Chocolate Cake', 'Desserts', 5.99, 'Rich chocolate cake with vanilla frosting', '/static/menu_images/cake.jpg'),
            (hotel_id, 'French Fries', 'Sides', 3.99, 'Crispy golden fries with ketchup', '/static/menu_images/fries.jpg'),
            (hotel_id, 'Coke', 'Beverages', 2.99, 'Classic cola drink', '/static/menu_images/coke.jpg'),
        ]

        # Insert sample menu items
        for item in sample_menu:
            c.execute('''
                INSERT INTO menu_items (hotel_id, name, category, price, description, image_path, is_available)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', item)

        conn.commit()
        print(f"Successfully added {len(sample_menu)} sample menu items")
        conn.close()
        return True

    except Exception as e:
        print(f"Error adding sample menu items: {e}")
        return False

if __name__ == '__main__':
    add_sample_menu_items()