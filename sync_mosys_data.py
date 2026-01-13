"""
Sync script to populate MOSYS data columns in local database.
Fetches data_niezgodnosci, nr_zamowienia, and kod_detalu from MOSYS/STAAMP database.
"""
import sqlite3
import sys
sys.path.insert(0, '.')

from MOSYS_data_functions import get_batch_niezgodnosc_details


def sync_mosys_data():
    """Sync MOSYS data to local database for all reports missing this data."""
    
    conn = sqlite3.connect('scrap_data.db')
    cursor = conn.cursor()
    
    # Get all unique nr_niezgodnosci that need MOSYS data
    cursor.execute('''
        SELECT DISTINCT nr_niezgodnosci 
        FROM dane_z_raportow 
        WHERE nr_niezgodnosci IS NOT NULL 
        AND nr_niezgodnosci != ''
        AND (data_niezgodnosci IS NULL OR nr_zamowienia IS NULL OR kod_detalu IS NULL)
    ''')
    
    rows = cursor.fetchall()
    nr_list = [row[0] for row in rows]
    
    if not nr_list:
        print("No records need MOSYS data sync.")
        conn.close()
        return
    
    print(f"Found {len(nr_list)} unique nr_niezgodnosci to sync...")
    
    # Fetch data from MOSYS in batch
    try:
        mosys_data = get_batch_niezgodnosc_details(nr_list)
        print(f"Fetched data for {len(mosys_data)} records from MOSYS")
    except Exception as e:
        print(f"Error fetching MOSYS data: {e}")
        conn.close()
        return
    
    # Update local database
    updated = 0
    for nr_niezgodnosci, data in mosys_data.items():
        cursor.execute('''
            UPDATE dane_z_raportow
            SET data_niezgodnosci = ?,
                nr_zamowienia = ?,
                kod_detalu = ?
            WHERE nr_niezgodnosci = ?
        ''', (
            data.get('data_niezgodnosci'),
            data.get('nr_zamowienia'),
            data.get('kod_detalu'),
            nr_niezgodnosci
        ))
        updated += cursor.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"Updated {updated} records in local database.")
    print("Sync complete!")


if __name__ == '__main__':
    sync_mosys_data()
