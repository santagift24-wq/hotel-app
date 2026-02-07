import sqlite3

conn = sqlite3.connect('restaurant.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Check all tables
c.execute('SELECT COUNT(*) as cnt FROM restaurant_tables')
count = c.fetchone()['cnt']
print(f'Total tables in DB: {count}')

if count > 0:
    c.execute('SELECT * FROM restaurant_tables LIMIT 5')
    print('\nExisting tables:')
    for row in c.fetchall():
        print(f'  - Hotel {row["hotel_id"]}: Table {row["table_number"]} (QR: {row["qr_code"]})')

# Check hotels/settings
c.execute('SELECT id, hotel_name FROM settings')
print('\nHotels configured:')
for row in c.fetchall():
    print(f'  - {row["hotel_name"]} (ID: {row["id"]})')
    c.execute('SELECT COUNT(*) as cnt FROM restaurant_tables WHERE hotel_id = ?', (row['id'],))
    tbl_count = c.fetchone()['cnt']
    print(f'    Tables: {tbl_count}')

conn.close()
