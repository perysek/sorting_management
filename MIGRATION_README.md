# Excel Data Migration Guide

This guide explains how to import data from Excel files into the Sorting Management System database.

## Overview

The migration system consists of three components:

1. **migrate_from_excel.py** - Main migration script that imports data from Excel
2. **create_excel_template.py** - Helper script to generate a sample Excel template
3. **data_template.xlsx** - Sample Excel file with proper structure and example data

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all required packages including `pandas` and `openpyxl`.

### 2. Prepare Your Excel File

#### Option A: Use the Template Generator

Generate a sample template with example data:

```bash
python create_excel_template.py
```

This creates `data_template.xlsx` which you can edit with your actual data.

#### Option B: Create Your Own Excel File

Create an Excel file with 4 sheets following the structure below.

### 3. Run the Migration

```bash
python migrate_from_excel.py your_data.xlsx
```

The script will:
- Read all sheets from the Excel file
- Import data in the correct order (respecting foreign key relationships)
- Skip duplicate entries (based on unique constraints)
- Display detailed progress and summary statistics
- Handle errors gracefully with clear error messages

## Excel File Structure

Your Excel file must contain the following sheets with specific column names:

### Sheet 1: "Dzialy" (Categories/Departments)

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| opis_kategorii | Text | Yes | Category description (e.g., "Jakość", "Produkcja") |

**Example:**
```
opis_kategorii
Jakość
Produkcja
Kontrola
Magazyn
```

### Sheet 2: "Operatorzy" (Operators)

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| nr_operatora | Integer | Yes | Operator number (must be unique) |
| imie_nazwisko | Text | Yes | Full name of operator |
| dzial | Text | Yes | Department name (must match a category from Sheet 1) |

**Example:**
```
nr_operatora  imie_nazwisko       dzial
9012          Piotr Peresiak     Jakość
9013          Jan Kowalski       Produkcja
9014          Anna Nowak         Jakość
```

### Sheet 3: "Raporty" (Reports)

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| nr_raportu | Text | Yes | Report number/identifier |
| operator_nr | Integer | Yes | Operator number (must exist in Sheet 2) |
| nr_niezgodnosci | Text | No | Non-conformity report number |
| nr_instrukcji | Text | No | Instruction number |
| selekcja_na_biezaco | Boolean | No | Ongoing selection flag (TRUE/FALSE, tak/nie, yes/no, 1/0) |
| ilosc_detali_sprawdzonych | Integer | Yes | Number of parts checked |
| zalecana_wydajnosc | Float | No | Recommended productivity (parts per hour) |
| czas_pracy | Float | Yes | Work time in hours |
| uwagi | Text | No | General notes |
| uwagi_do_wydajnosci | Text | No | Performance notes |
| data_selekcji | Date | Yes | Selection date (formats: YYYY-MM-DD, DD/MM/YYYY, DD.MM.YYYY) |

**Example:**
```
nr_raportu  operator_nr  nr_niezgodnosci  nr_instrukcji  selekcja_na_biezaco  ilosc_detali_sprawdzonych  zalecana_wydajnosc  czas_pracy  uwagi                              uwagi_do_wydajnosci         data_selekcji
RPT001      9012         NCR2025001       INS-001        TRUE                 5000                       900.0               6.5         Partia wymaga dodatkowej kontroli  W normie                   2025-01-10
RPT002      9013         NCR2025002       INS-002        FALSE                8000                       1000.0              8.0         Standardowa procedura              Powyżej normy              2025-01-11
```

### Sheet 4: "Defekty" (Defects)

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| nr_raportu | Text | Yes | Report number (must exist in Sheet 3) |
| defekt | Text | Yes | Defect name/type |
| ilosc | Integer | Yes | Quantity of parts with this defect |

**Example:**
```
nr_raportu  defekt        ilosc
RPT001      niedolanie    23
RPT001      wypływka      12
RPT002      zarysowania   15
RPT002      pęknięcia     8
```

## Important Notes

### Data Validation

- **Unique Constraints**: The script checks for duplicates:
  - Categories: `opis_kategorii` must be unique
  - Operators: `nr_operatora` must be unique
  - Reports: `nr_raportu` must be unique per import session

- **Foreign Key Relationships**:
  - Operators must reference valid categories
  - Reports must reference valid operators
  - Defects must reference valid reports

- **Data Types**:
  - Dates: Accepted formats: YYYY-MM-DD, DD/MM/YYYY, DD.MM.YYYY, MM/DD/YYYY
  - Booleans: TRUE/FALSE, tak/nie, yes/no, 1/0 (case insensitive)
  - Numbers: Must be valid integers or floats

### Migration Order

The script imports data in this order to respect foreign key relationships:

1. Categories (dzialy)
2. Operators (operatorzy) - depends on categories
3. Reports (raporty) - depends on operators
4. Defects (defekty) - depends on reports

### Handling Existing Data

- **Duplicates**: If a record with the same unique identifier already exists in the database, it will be skipped with a warning message
- **Partial Import**: Even if some records fail, the script continues processing remaining records
- **Transactions**: Each record is committed individually to prevent data loss if errors occur

### Error Handling

The script provides clear feedback for common issues:

- Missing required columns
- Invalid data types
- Missing foreign key references
- Duplicate entries
- Invalid date formats
- Empty or missing values

## Example Output

```
============================================================
EXCEL DATA MIGRATION SCRIPT
============================================================
Source file: data.xlsx
Started at: 2025-01-12 10:30:00

📖 Reading Excel file...
✓ Found 4 sheet(s): Dzialy, Operatorzy, Raporty, Defekty

============================================================
IMPORTING CATEGORIES (DZIALY)
============================================================
✓ Imported category: Jakość (ID: 1)
✓ Imported category: Produkcja (ID: 2)
⚠ Category 'Kontrola' already exists (ID: 3), skipping...

📊 Categories Summary: 2 imported, 1 skipped

============================================================
IMPORTING OPERATORS (OPERATORZY)
============================================================
✓ Imported operator: #9012 - Piotr Peresiak (Jakość)
✓ Imported operator: #9013 - Jan Kowalski (Produkcja)

📊 Operators Summary: 2 imported, 0 skipped

============================================================
IMPORTING REPORTS (RAPORTY)
============================================================
✓ Imported report: RPT001 (Date: 2025-01-10)
✓ Imported report: RPT002 (Date: 2025-01-11)

📊 Reports Summary: 2 imported, 0 skipped

============================================================
IMPORTING DEFECTS (DEFEKTY)
============================================================
✓ Imported defect: niedolanie (23 pcs) for report RPT001
✓ Imported defect: wypływka (12 pcs) for report RPT001

📊 Defects Summary: 2 imported, 0 skipped

============================================================
✓ MIGRATION COMPLETED SUCCESSFULLY
============================================================
Finished at: 2025-01-12 10:30:05
```

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Solution: Run `pip install -r requirements.txt`

2. **"File not found" error**
   - Solution: Check the file path and ensure the Excel file exists

3. **"Required column 'X' not found"**
   - Solution: Ensure your Excel sheet has the correct column names (case-sensitive)

4. **"Category 'X' not found"**
   - Solution: Ensure all categories referenced in the Operators sheet exist in the Categories sheet

5. **"Operator #X not found"**
   - Solution: Ensure all operators referenced in the Reports sheet exist in the Operators sheet

6. **"Invalid date format"**
   - Solution: Use one of the supported date formats: YYYY-MM-DD, DD/MM/YYYY, DD.MM.YYYY

### Testing

To test the migration with sample data:

```bash
# Generate a template with sample data
python create_excel_template.py test_data.xlsx

# Import the sample data
python migrate_from_excel.py test_data.xlsx
```

## Advanced Usage

### Custom Output Filename

Generate a template with a custom name:

```bash
python create_excel_template.py my_custom_data.xlsx
```

### Re-running Migration

The script is idempotent - you can run it multiple times safely:
- Duplicate entries will be skipped
- Only new data will be imported
- The database remains consistent

### Incremental Updates

You can import additional data by creating a new Excel file with only the new records:
1. Create an Excel file with only new categories, operators, reports, or defects
2. Run the migration script
3. Existing records will be skipped, new ones will be imported

## Database Structure

The migration script works with the following database tables:

- **dzialy** (Categories/Departments)
- **operatorzy** (Operators)
- **dane_z_raportow** (Reports)
- **braki_defekty_raportow** (Defects)

All tables use SQLite and are managed by SQLAlchemy ORM.

## Support

For issues or questions:
1. Check this README
2. Review the error messages - they provide specific guidance
3. Verify your Excel file structure matches the specification
4. Check that all foreign key relationships are valid

## Version History

- **v1.0** (2025-01-12) - Initial release with full CRUD support for all entities
