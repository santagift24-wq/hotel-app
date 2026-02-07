#!/usr/bin/env python3
"""
Initialize store profiles with defaults for all hotels.
Ensures every hotel has a store profile entry with proper default values.
"""
import sqlite3
import os
from datetime import datetime

def init_store_profiles():
    """Initialize store profiles for all hotels"""
    # Determine database location
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

        # Get all admin users
        c.execute('SELECT id FROM admin_users')
        admins = c.fetchall()

        if not admins:
            print("Error: No admin users found in database.")
            conn.close()
            return False

        added_count = 0
        for admin in admins:
            hotel_id = admin[0]
            
            # Check if store profile already exists
            c.execute('SELECT id FROM store_profiles WHERE hotel_id = ?', (hotel_id,))
            existing = c.fetchone()
            
            if existing:
                # Update with defaults if missing values
                c.execute('''
                    UPDATE store_profiles 
                    SET store_description = COALESCE(store_description, 'Premium dining experience'),
                        cuisine_type = COALESCE(cuisine_type, 'Multi-cuisine'),
                        rating = COALESCE(rating, 4.5),
                        review_count = COALESCE(review_count, 24)
                    WHERE hotel_id = ? AND 
                    (store_description IS NULL OR store_description = '' OR 
                     cuisine_type IS NULL OR cuisine_type = '')
                ''', (hotel_id,))
                if c.rowcount > 0:
                    added_count += 1
                    print(f"Updated hotel_id {hotel_id} with default values")
            else:
                # Create new store profile with defaults
                c.execute('''
                    INSERT INTO store_profiles 
                    (hotel_id, store_description, cuisine_type, rating, review_count, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (hotel_id, 'Premium dining experience', 'Multi-cuisine', 4.5, 24, datetime.now()))
                added_count += 1
                print(f"Created store profile for hotel_id {hotel_id}")

        conn.commit()
        print(f"\nSuccessfully initialized {added_count} store profile(s)")
        conn.close()
        return True

    except Exception as e:
        print(f"Error initializing store profiles: {e}")
        return False

if __name__ == '__main__':
    init_store_profiles()
