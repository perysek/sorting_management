#!/usr/bin/env python3
"""
Create a sample Excel template file for data migration.

This script generates an Excel file with the correct structure and sample data
that can be used as a template for importing data into the sorting management system.

Usage:
    python create_excel_template.py [output_filename]

Default output: data_template.xlsx
"""

import sys
import pandas as pd
from datetime import date


def create_template(output_file='data_template.xlsx'):
    """Create an Excel template with sample data."""

    # Sample Categories (Dzialy)
    dzialy_data = {
        'opis_kategorii': [
            'Jakość',
            'Produkcja',
            'Kontrola',
            'Magazyn'
        ]
    }

    # Sample Operators (Operatorzy)
    operatorzy_data = {
        'nr_operatora': [9012, 9013, 9014, 9015],
        'imie_nazwisko': [
            'Piotr Peresiak',
            'Jan Kowalski',
            'Anna Nowak',
            'Marek Wiśniewski'
        ],
        'dzial': ['Jakość', 'Produkcja', 'Jakość', 'Kontrola']
    }

    # Sample Reports (Raporty)
    raporty_data = {
        'nr_raportu': ['RPT001', 'RPT002', 'RPT003'],
        'operator_nr': [9012, 9013, 9012],
        'nr_niezgodnosci': ['NCR2025001', 'NCR2025002', 'NCR2025003'],
        'nr_instrukcji': ['INS-001', 'INS-002', 'INS-003'],
        'selekcja_na_biezaco': [True, False, True],
        'ilosc_detali_sprawdzonych': [5000, 8000, 6500],
        'zalecana_wydajnosc': [900.0, 1000.0, 850.0],
        'czas_pracy': [6.5, 8.0, 7.5],
        'uwagi': [
            'Partia wymaga dodatkowej kontroli',
            'Standardowa procedura',
            'Zauważono niewielkie odchylenia'
        ],
        'uwagi_do_wydajnosci': [
            'W normie',
            'Powyżej normy',
            'Zgodnie z oczekiwaniami'
        ],
        'data_selekcji': [
            '2025-01-10',
            '2025-01-11',
            '2025-01-12'
        ]
    }

    # Sample Defects (Defekty)
    defekty_data = {
        'nr_raportu': ['RPT001', 'RPT001', 'RPT002', 'RPT002', 'RPT003'],
        'defekt': [
            'niedolanie',
            'wypływka',
            'zarysowania',
            'pęknięcia',
            'niedolanie'
        ],
        'ilosc': [23, 12, 15, 8, 18]
    }

    # Create DataFrames
    df_dzialy = pd.DataFrame(dzialy_data)
    df_operatorzy = pd.DataFrame(operatorzy_data)
    df_raporty = pd.DataFrame(raporty_data)
    df_defekty = pd.DataFrame(defekty_data)

    # Write to Excel with multiple sheets
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df_dzialy.to_excel(writer, sheet_name='Dzialy', index=False)
        df_operatorzy.to_excel(writer, sheet_name='Operatorzy', index=False)
        df_raporty.to_excel(writer, sheet_name='Raporty', index=False)
        df_defekty.to_excel(writer, sheet_name='Defekty', index=False)

    print(f"✓ Excel template created: {output_file}")
    print("\nTemplate structure:")
    print(f"  - Sheet 'Dzialy': {len(df_dzialy)} sample categories")
    print(f"  - Sheet 'Operatorzy': {len(df_operatorzy)} sample operators")
    print(f"  - Sheet 'Raporty': {len(df_raporty)} sample reports")
    print(f"  - Sheet 'Defekty': {len(df_defekty)} sample defects")
    print("\nYou can now edit this file with your actual data and use it with:")
    print(f"  python migrate_from_excel.py {output_file}")


if __name__ == '__main__':
    output_file = sys.argv[1] if len(sys.argv) > 1 else 'data_template.xlsx'
    create_template(output_file)
