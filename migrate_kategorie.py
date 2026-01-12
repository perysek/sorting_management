"""
Migration script to rename 'nazwa_dzial' column to 'opis_kategorii' in the 'dzialy' table.
This script handles the SQLite limitation of not supporting direct column renaming.
"""

from sqlalchemy import create_engine, text, inspect
from database.models import DATABASE_URL

def migrate_dzialy_table():
    """Migrates the dzialy table to use opis_kategorii instead of nazwa_dzial."""
    engine = create_engine(DATABASE_URL)

    with engine.connect() as connection:
        inspector = inspect(engine)

        # Check if the table exists
        if 'dzialy' not in inspector.get_table_names():
            print("Tabela 'dzialy' nie istnieje. Brak migracji do wykonania.")
            return

        # Get current columns
        columns = inspector.get_columns('dzialy')
        column_names = [col['name'] for col in columns]

        # Check if migration is needed
        if 'opis_kategorii' in column_names:
            print("Kolumna 'opis_kategorii' już istnieje. Migracja nie jest potrzebna.")
            return

        if 'nazwa_dzial' not in column_names:
            print("Kolumna 'nazwa_dzial' nie istnieje. Tabela może być już zaktualizowana.")
            return

        print("Rozpoczynam migrację tabeli 'dzialy'...")

        # SQLite doesn't support column renaming directly, so we need to:
        # 1. Create a new table with the correct schema
        # 2. Copy data from old table
        # 3. Drop old table
        # 4. Rename new table

        try:
            # Begin transaction
            trans = connection.begin()

            # Create new table with correct schema
            connection.execute(text("""
                CREATE TABLE dzialy_new (
                    id INTEGER NOT NULL PRIMARY KEY,
                    opis_kategorii VARCHAR UNIQUE
                )
            """))

            # Copy data from old table to new table
            connection.execute(text("""
                INSERT INTO dzialy_new (id, opis_kategorii)
                SELECT id, nazwa_dzial FROM dzialy
            """))

            # Drop old table
            connection.execute(text("DROP TABLE dzialy"))

            # Rename new table to old name
            connection.execute(text("ALTER TABLE dzialy_new RENAME TO dzialy"))

            # Commit transaction
            trans.commit()

            print("[OK] Migracja zakonczona pomyslnie!")
            print("[OK] Kolumna 'nazwa_dzial' zostala zmieniona na 'opis_kategorii'")

        except Exception as e:
            trans.rollback()
            print(f"[BLAD] Blad podczas migracji: {e}")
            raise

if __name__ == "__main__":
    print("=" * 60)
    print("Migracja bazy danych: dzialy.nazwa_dzial -> dzialy.opis_kategorii")
    print("=" * 60)
    migrate_dzialy_table()
    print("=" * 60)
