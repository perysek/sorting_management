"""
Migration script to add MOSYS data columns to dane_z_raportow table.
Run with Flask server stopped.
"""
import sqlite3

def migrate():
    conn = sqlite3.connect('scrap_data.db')
    cursor = conn.cursor()
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(dane_z_raportow)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'data_niezgodnosci' not in columns:
        cursor.execute('ALTER TABLE dane_z_raportow ADD COLUMN data_niezgodnosci DATE')
        print('Added data_niezgodnosci column')
    else:
        print('data_niezgodnosci column already exists')
    
    if 'nr_zamowienia' not in columns:
        cursor.execute('ALTER TABLE dane_z_raportow ADD COLUMN nr_zamowienia TEXT')
        print('Added nr_zamowienia column')
    else:
        print('nr_zamowienia column already exists')
    
    if 'kod_detalu' not in columns:
        cursor.execute('ALTER TABLE dane_z_raportow ADD COLUMN kod_detalu TEXT')
        print('Added kod_detalu column')
    else:
        print('kod_detalu column already exists')
    
    conn.commit()
    conn.close()
    print('Migration complete!')

if __name__ == '__main__':
    migrate()
