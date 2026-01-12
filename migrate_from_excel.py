#!/usr/bin/env python3
"""
Excel Data Migration Script for Sorting Management System

This script imports data from an Excel file into the sorting management database.

Expected Excel file structure:
- Sheet 1: "Dzialy" (Categories) - columns: opis_kategorii
- Sheet 2: "Operatorzy" (Operators) - columns: nr_operatora, imie_nazwisko, dzial
- Sheet 3: "Raporty" (Reports) - columns: nr_raportu, operator_nr, nr_niezgodnosci,
           nr_instrukcji, selekcja_na_biezaco, ilosc_detali_sprawdzonych,
           zalecana_wydajnosc, czas_pracy, uwagi, uwagi_do_wydajnosci, data_selekcji
- Sheet 4: "Defekty" (Defects) - columns: nr_raportu, defekt, ilosc

Usage:
    python migrate_from_excel.py <path_to_excel_file>

Example:
    python migrate_from_excel.py data.xlsx
"""

import sys
import os
from datetime import datetime
import pandas as pd
from sqlalchemy.exc import IntegrityError

# Add the parent directory to the path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import KategoriaZrodlaDanych, Operator, DaneRaportu, BrakiDefektyRaportu


def parse_date(date_value):
    """Parse date from various formats."""
    if pd.isna(date_value):
        return None

    if isinstance(date_value, datetime):
        return date_value.date()

    # Try parsing string dates
    if isinstance(date_value, str):
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d.%m.%Y', '%m/%d/%Y']:
            try:
                return datetime.strptime(date_value, fmt).date()
            except ValueError:
                continue

    return None


def parse_boolean(value):
    """Parse boolean from various formats."""
    if pd.isna(value):
        return False

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        value = value.lower().strip()
        return value in ['true', 'tak', 'yes', '1', 'prawda']

    return bool(value)


def import_categories(df, app):
    """Import categories/departments from DataFrame."""
    print("\n" + "="*60)
    print("IMPORTING CATEGORIES (DZIALY)")
    print("="*60)

    if df is None or df.empty:
        print("⚠ No categories data found or sheet is empty")
        return {}

    # Clean column names
    df.columns = df.columns.str.strip()

    # Check required columns
    if 'opis_kategorii' not in df.columns:
        print("❌ ERROR: Required column 'opis_kategorii' not found")
        print(f"Available columns: {', '.join(df.columns)}")
        return {}

    category_map = {}
    imported = 0
    skipped = 0

    with app.app_context():
        for idx, row in df.iterrows():
            opis = str(row['opis_kategorii']).strip()

            if not opis or opis == 'nan':
                skipped += 1
                continue

            # Check if category already exists
            existing = KategoriaZrodlaDanych.query.filter_by(opis_kategorii=opis).first()
            if existing:
                print(f"⚠ Category '{opis}' already exists (ID: {existing.id}), skipping...")
                category_map[opis] = existing.id
                skipped += 1
                continue

            # Create new category
            category = KategoriaZrodlaDanych(opis_kategorii=opis)

            try:
                db.session.add(category)
                db.session.commit()
                category_map[opis] = category.id
                print(f"✓ Imported category: {opis} (ID: {category.id})")
                imported += 1
            except IntegrityError as e:
                db.session.rollback()
                print(f"❌ Error importing category '{opis}': {e}")
                skipped += 1

    print(f"\n📊 Categories Summary: {imported} imported, {skipped} skipped")
    return category_map


def import_operators(df, category_map, app):
    """Import operators from DataFrame."""
    print("\n" + "="*60)
    print("IMPORTING OPERATORS (OPERATORZY)")
    print("="*60)

    if df is None or df.empty:
        print("⚠ No operators data found or sheet is empty")
        return {}

    # Clean column names
    df.columns = df.columns.str.strip()

    # Check required columns
    required_cols = ['nr_operatora', 'imie_nazwisko', 'dzial']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"❌ ERROR: Required columns missing: {', '.join(missing_cols)}")
        print(f"Available columns: {', '.join(df.columns)}")
        return {}

    operator_map = {}
    imported = 0
    skipped = 0

    with app.app_context():
        for idx, row in df.iterrows():
            try:
                nr_operatora = int(row['nr_operatora'])
                imie_nazwisko = str(row['imie_nazwisko']).strip()
                dzial_name = str(row['dzial']).strip()

                if not imie_nazwisko or imie_nazwisko == 'nan':
                    print(f"⚠ Row {idx + 2}: Missing operator name, skipping...")
                    skipped += 1
                    continue

                # Get category ID
                dzial_id = category_map.get(dzial_name)
                if not dzial_id:
                    # Try to find in database
                    category = KategoriaZrodlaDanych.query.filter_by(opis_kategorii=dzial_name).first()
                    if category:
                        dzial_id = category.id
                    else:
                        print(f"⚠ Row {idx + 2}: Category '{dzial_name}' not found, skipping operator {nr_operatora}...")
                        skipped += 1
                        continue

                # Check if operator already exists
                existing = Operator.query.filter_by(nr_operatora=nr_operatora).first()
                if existing:
                    print(f"⚠ Operator #{nr_operatora} already exists (ID: {existing.id}), skipping...")
                    operator_map[nr_operatora] = existing.id
                    skipped += 1
                    continue

                # Create new operator
                operator = Operator(
                    nr_operatora=nr_operatora,
                    imie_nazwisko=imie_nazwisko,
                    dzial_id=dzial_id
                )

                db.session.add(operator)
                db.session.commit()
                operator_map[nr_operatora] = operator.id
                print(f"✓ Imported operator: #{nr_operatora} - {imie_nazwisko} ({dzial_name})")
                imported += 1

            except (ValueError, KeyError) as e:
                print(f"❌ Row {idx + 2}: Error parsing data - {e}")
                skipped += 1
            except IntegrityError as e:
                db.session.rollback()
                print(f"❌ Row {idx + 2}: Database error - {e}")
                skipped += 1

    print(f"\n📊 Operators Summary: {imported} imported, {skipped} skipped")
    return operator_map


def import_reports(df, operator_map, app):
    """Import reports from DataFrame."""
    print("\n" + "="*60)
    print("IMPORTING REPORTS (RAPORTY)")
    print("="*60)

    if df is None or df.empty:
        print("⚠ No reports data found or sheet is empty")
        return {}

    # Clean column names
    df.columns = df.columns.str.strip()

    # Check required columns
    required_cols = ['nr_raportu', 'operator_nr', 'ilosc_detali_sprawdzonych', 'czas_pracy', 'data_selekcji']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"❌ ERROR: Required columns missing: {', '.join(missing_cols)}")
        print(f"Available columns: {', '.join(df.columns)}")
        return {}

    report_map = {}
    imported = 0
    skipped = 0

    with app.app_context():
        for idx, row in df.iterrows():
            try:
                nr_raportu = str(row['nr_raportu']).strip()
                operator_nr = int(row['operator_nr'])

                # Get operator ID
                operator_id = operator_map.get(operator_nr)
                if not operator_id:
                    # Try to find in database
                    operator = Operator.query.filter_by(nr_operatora=operator_nr).first()
                    if operator:
                        operator_id = operator.id
                    else:
                        print(f"⚠ Row {idx + 2}: Operator #{operator_nr} not found, skipping report {nr_raportu}...")
                        skipped += 1
                        continue

                # Check if report already exists
                existing = DaneRaportu.query.filter_by(nr_raportu=nr_raportu).first()
                if existing:
                    print(f"⚠ Report '{nr_raportu}' already exists (ID: {existing.id}), skipping...")
                    report_map[nr_raportu] = existing.id
                    skipped += 1
                    continue

                # Parse data
                data_selekcji = parse_date(row['data_selekcji'])
                if not data_selekcji:
                    print(f"⚠ Row {idx + 2}: Invalid date format for report {nr_raportu}, skipping...")
                    skipped += 1
                    continue

                # Create new report
                report = DaneRaportu(
                    nr_raportu=nr_raportu,
                    operator_id=operator_id,
                    nr_niezgodnosci=str(row.get('nr_niezgodnosci', '')).strip() or None,
                    nr_instrukcji=str(row.get('nr_instrukcji', '')).strip() or None,
                    selekcja_na_biezaco=parse_boolean(row.get('selekcja_na_biezaco', False)),
                    ilosc_detali_sprawdzonych=int(row['ilosc_detali_sprawdzonych']),
                    zalecana_wydajnosc=float(row['zalecana_wydajnosc']) if pd.notna(row.get('zalecana_wydajnosc')) else None,
                    czas_pracy=float(row['czas_pracy']),
                    uwagi=str(row.get('uwagi', '')).strip() if pd.notna(row.get('uwagi')) else None,
                    uwagi_do_wydajnosci=str(row.get('uwagi_do_wydajnosci', '')).strip() if pd.notna(row.get('uwagi_do_wydajnosci')) else None,
                    data_selekcji=data_selekcji
                )

                db.session.add(report)
                db.session.commit()
                report_map[nr_raportu] = report.id
                print(f"✓ Imported report: {nr_raportu} (Date: {data_selekcji})")
                imported += 1

            except (ValueError, KeyError) as e:
                print(f"❌ Row {idx + 2}: Error parsing data - {e}")
                skipped += 1
            except IntegrityError as e:
                db.session.rollback()
                print(f"❌ Row {idx + 2}: Database error - {e}")
                skipped += 1

    print(f"\n📊 Reports Summary: {imported} imported, {skipped} skipped")
    return report_map


def import_defects(df, report_map, app):
    """Import defects from DataFrame."""
    print("\n" + "="*60)
    print("IMPORTING DEFECTS (DEFEKTY)")
    print("="*60)

    if df is None or df.empty:
        print("⚠ No defects data found or sheet is empty")
        return

    # Clean column names
    df.columns = df.columns.str.strip()

    # Check required columns
    required_cols = ['nr_raportu', 'defekt', 'ilosc']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"❌ ERROR: Required columns missing: {', '.join(missing_cols)}")
        print(f"Available columns: {', '.join(df.columns)}")
        return

    imported = 0
    skipped = 0

    with app.app_context():
        for idx, row in df.iterrows():
            try:
                nr_raportu = str(row['nr_raportu']).strip()
                defekt = str(row['defekt']).strip()
                ilosc = int(row['ilosc'])

                if not defekt or defekt == 'nan':
                    print(f"⚠ Row {idx + 2}: Missing defect name, skipping...")
                    skipped += 1
                    continue

                # Get report ID
                raport_id = report_map.get(nr_raportu)
                if not raport_id:
                    # Try to find in database
                    raport = DaneRaportu.query.filter_by(nr_raportu=nr_raportu).first()
                    if raport:
                        raport_id = raport.id
                    else:
                        print(f"⚠ Row {idx + 2}: Report '{nr_raportu}' not found, skipping defect...")
                        skipped += 1
                        continue

                # Create new defect
                defect = BrakiDefektyRaportu(
                    raport_id=raport_id,
                    defekt=defekt,
                    ilosc=ilosc
                )

                db.session.add(defect)
                db.session.commit()
                print(f"✓ Imported defect: {defekt} ({ilosc} pcs) for report {nr_raportu}")
                imported += 1

            except (ValueError, KeyError) as e:
                print(f"❌ Row {idx + 2}: Error parsing data - {e}")
                skipped += 1
            except IntegrityError as e:
                db.session.rollback()
                print(f"❌ Row {idx + 2}: Database error - {e}")
                skipped += 1

    print(f"\n📊 Defects Summary: {imported} imported, {skipped} skipped")


def main():
    """Main migration function."""
    if len(sys.argv) < 2:
        print("Usage: python migrate_from_excel.py <path_to_excel_file>")
        print("\nExample: python migrate_from_excel.py data.xlsx")
        sys.exit(1)

    excel_file = sys.argv[1]

    if not os.path.exists(excel_file):
        print(f"❌ ERROR: File '{excel_file}' not found")
        sys.exit(1)

    print("\n" + "="*60)
    print("EXCEL DATA MIGRATION SCRIPT")
    print("="*60)
    print(f"Source file: {excel_file}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Create Flask app context
    app = create_app()

    try:
        # Read Excel file
        print("\n📖 Reading Excel file...")
        excel_data = pd.read_excel(excel_file, sheet_name=None)  # Read all sheets

        print(f"✓ Found {len(excel_data)} sheet(s): {', '.join(excel_data.keys())}")

        # Import data in order (respecting foreign key relationships)
        category_map = {}
        operator_map = {}
        report_map = {}

        # 1. Import categories
        if 'Dzialy' in excel_data:
            category_map = import_categories(excel_data['Dzialy'], app)
        else:
            print("\n⚠ WARNING: 'Dzialy' sheet not found in Excel file")

        # 2. Import operators
        if 'Operatorzy' in excel_data:
            operator_map = import_operators(excel_data['Operatorzy'], category_map, app)
        else:
            print("\n⚠ WARNING: 'Operatorzy' sheet not found in Excel file")

        # 3. Import reports
        if 'Raporty' in excel_data:
            report_map = import_reports(excel_data['Raporty'], operator_map, app)
        else:
            print("\n⚠ WARNING: 'Raporty' sheet not found in Excel file")

        # 4. Import defects
        if 'Defekty' in excel_data:
            import_defects(excel_data['Defekty'], report_map, app)
        else:
            print("\n⚠ WARNING: 'Defekty' sheet not found in Excel file")

        print("\n" + "="*60)
        print("✓ MIGRATION COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print("\n" + "="*60)
        print("❌ MIGRATION FAILED")
        print("="*60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
