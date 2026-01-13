"""
Import data from Excel file into database tables.
Reads from dane.xlsx sheets:
- dane_z_raportow -> DaneRaportu table
- braki_defekty_raportow -> BrakiDefektyRaportu table
"""
import pandas as pd
import sqlite3
from datetime import datetime

# Connect to database
conn = sqlite3.connect('scrap_data.db')
cursor = conn.cursor()

# Read Excel file
xl = pd.ExcelFile('dane.xlsx')

print("=" * 60)
print("IMPORTING DATA FROM EXCEL TO DATABASE")
print("=" * 60)

# ===== Import dane_z_raportow =====
print("\n>>> Reading 'dane_z_raportow' sheet...")
df_raportow = pd.read_excel(xl, 'dane_z_raportow')
print(f"Found {len(df_raportow)} rows")
print(f"Columns: {list(df_raportow.columns)}")

# Clear existing data in related tables first (defects first due to FK)
print("\n>>> Clearing existing data from braki_defekty_raportow...")
cursor.execute("DELETE FROM braki_defekty_raportow")
print(">>> Clearing existing data from dane_z_raportow...")
cursor.execute("DELETE FROM dane_z_raportow")
conn.commit()

# Insert dane_z_raportow
print("\n>>> Inserting dane_z_raportow...")
for idx, row in df_raportow.iterrows():
    # Handle date parsing
    data_selekcji = row.get('data_selekcji')
    if pd.notna(data_selekcji):
        if isinstance(data_selekcji, datetime):
            data_selekcji = data_selekcji.strftime('%Y-%m-%d')
        else:
            data_selekcji = str(data_selekcji)
    else:
        data_selekcji = None
    
    # Handle boolean
    selekcja_na_biezaco = bool(row.get('selekcja_na_biezaco', False)) if pd.notna(row.get('selekcja_na_biezaco')) else False
    
    cursor.execute("""
        INSERT INTO dane_z_raportow (
            id, nr_raportu, operator_id, nr_niezgodnosci, nr_instrukcji,
            selekcja_na_biezaco, ilosc_detali_sprawdzonych, zalecana_wydajnosc,
            czas_pracy, uwagi, uwagi_do_wydajnosci, data_selekcji
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        int(row['id']) if pd.notna(row.get('id')) else None,
        str(row['nr_raportu']) if pd.notna(row.get('nr_raportu')) else None,
        int(row['operator_id']) if pd.notna(row.get('operator_id')) else None,
        str(row['nr_niezgodnosci']) if pd.notna(row.get('nr_niezgodnosci')) else None,
        str(row['nr_instrukcji']) if pd.notna(row.get('nr_instrukcji')) else None,
        selekcja_na_biezaco,
        int(row['ilosc_detali_sprawdzonych']) if pd.notna(row.get('ilosc_detali_sprawdzonych')) else None,
        float(row['zalecana wydajność']) if pd.notna(row.get('zalecana wydajność')) else None,
        float(row['czas_pracy']) if pd.notna(row.get('czas_pracy')) else None,
        str(row['uwagi']) if pd.notna(row.get('uwagi')) else None,
        str(row['uwagi_do_wydajnosci']) if pd.notna(row.get('uwagi_do_wydajnosci')) else None,
        data_selekcji
    ))

conn.commit()
print(f"Inserted {len(df_raportow)} rows into dane_z_raportow")

# ===== Import braki_defekty_raportow =====
print("\n>>> Reading 'braki_defekty_raportow' sheet...")
df_defekty = pd.read_excel(xl, 'braki_defekty_raportow')
print(f"Found {len(df_defekty)} rows")
print(f"Columns: {list(df_defekty.columns)}")

# Insert braki_defekty_raportow
print("\n>>> Inserting braki_defekty_raportow...")
for idx, row in df_defekty.iterrows():
    cursor.execute("""
        INSERT INTO braki_defekty_raportow (id, raport_id, defekt, ilosc)
        VALUES (?, ?, ?, ?)
    """, (
        int(row['id']) if pd.notna(row.get('id')) else None,
        int(row['raport_id']) if pd.notna(row.get('raport_id')) else None,
        str(row['defekt']) if pd.notna(row.get('defekt')) else None,
        int(row['ilosc']) if pd.notna(row.get('ilosc')) else None,
    ))

conn.commit()
print(f"Inserted {len(df_defekty)} rows into braki_defekty_raportow")

# ===== Verify data =====
print("\n" + "=" * 60)
print("VERIFICATION")
print("=" * 60)

cursor.execute("SELECT COUNT(*) FROM dane_z_raportow")
count_raportow = cursor.fetchone()[0]
print(f"dane_z_raportow: {count_raportow} rows")

cursor.execute("SELECT COUNT(*) FROM braki_defekty_raportow")
count_defekty = cursor.fetchone()[0]
print(f"braki_defekty_raportow: {count_defekty} rows")

print("\n>>> Sample data from dane_z_raportow:")
cursor.execute("SELECT * FROM dane_z_raportow LIMIT 3")
for row in cursor.fetchall():
    print(f"  {row}")

print("\n>>> Sample data from braki_defekty_raportow:")
cursor.execute("SELECT * FROM braki_defekty_raportow LIMIT 5")
for row in cursor.fetchall():
    print(f"  {row}")

conn.close()
print("\n" + "=" * 60)
print("IMPORT COMPLETED SUCCESSFULLY!")
print("=" * 60)
