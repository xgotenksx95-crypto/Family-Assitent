import sqlite3
from datetime import datetime
from contextlib import closing

from config import DB_FILE as DEFAULT_DB_FILE


class Database:
    DB_FILE = DEFAULT_DB_FILE

    # Falls Sie die DB-Datei dynamisch ändern wollen, tun Sie das über diese Klassenmethode
    @classmethod
    def set_db_file(cls, db_file: str):
        """Ändert den Datenbankpfad global für die Klasse."""
        cls.DB_FILE = db_file

    @classmethod
    def _connect(cls):
        """Öffnet die Verbindung und stellt sicher, dass sie danach geschlossen wird."""
        # closing() sorgt dafür, dass conn.close() beim Verlassen des with-Blocks aufgerufen wird
        return closing(sqlite3.connect(cls.DB_FILE))

    @classmethod
    def init_db(cls):
        """Erstellt die Tabellen, falls sie noch nicht existieren."""
        with cls._connect() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shopping_list (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    is_checked INTEGER DEFAULT 0
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    task TEXT NOT NULL,
                    due_datetime TEXT NOT NULL,
                    recurring TEXT,
                    is_done INTEGER DEFAULT 0
                )
            """)

            # Überprüfung, ob Spalten für Migration existieren
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reminders'")
            if cursor.fetchone():
                cursor.execute("PRAGMA table_info(reminders)")
                columns = {row[1] for row in cursor.fetchall()}
                if "chat_id" not in columns:
                    cursor.execute("ALTER TABLE reminders ADD COLUMN chat_id INTEGER")
                if "recurring" not in columns:
                    cursor.execute("ALTER TABLE reminders ADD COLUMN recurring TEXT")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS routines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT NOT NULL,
                    time_of_day TEXT NOT NULL
                )
            """)
            # sqlite3-Kontextmanager führt hier automatisch conn.commit() aus

    @classmethod
    def add_shopping_item(cls, item: str):
        """Speichert einen Artikel auf der Einkaufsliste."""
        now = datetime.now().isoformat()
        with cls._connect() as conn:
            conn.execute(
                "INSERT INTO shopping_list (item, created_at) VALUES (?, ?)",
                (item, now)
            )

    @classmethod
    def add_shop_item(cls, item: str):
        """Backward-compatible alias for add_shopping_item."""
        cls.add_shopping_item(item)

    @classmethod
    def add_reminder(cls, chat_id: int, task: str, due_datetime, recurring: str | None = None):
        """Speichert einen einmaligen Termin, wenn er noch nicht existiert."""
        dt_str = due_datetime.isoformat() if hasattr(due_datetime, 'isoformat') else str(due_datetime)
        with cls._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM reminders WHERE chat_id = ? AND task = ? AND due_datetime = ? AND is_done = 0 AND COALESCE(recurring, '') = COALESCE(?, '')",
                (chat_id, task, dt_str, recurring)
            )
            if cursor.fetchone():
                return None

            cursor.execute(
                "INSERT INTO reminders (chat_id, task, due_datetime, recurring) VALUES (?, ?, ?, ?)",
                (chat_id, task, dt_str, recurring)
            )
            return cursor.lastrowid

    @classmethod
    def add_routine(cls, task: str, time_str: str):
        """Speichert eine tägliche Aufgabe."""
        with cls._connect() as conn:
            conn.execute(
                "INSERT INTO routines (task, time_of_day) VALUES (?, ?)",
                (task, time_str)
            )

    @classmethod
    def get_shopping_list(cls):
        """Gibt alle noch nicht gekauften Artikel zurück."""
        with cls._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, item FROM shopping_list WHERE is_checked = 0")
            return cursor.fetchall()

    @classmethod
    def get_shop_items(cls):
        with cls._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, item FROM shopping_list WHERE is_checked = 0 ORDER BY id")
            return cursor.fetchall()

    @classmethod
    def mark_shop_item_done(cls, item_id: int):
        with cls._connect() as conn:
            conn.execute("UPDATE shopping_list SET is_checked = 1 WHERE id = ?", (item_id,))

    @classmethod
    def get_todays_reminders(cls):
        """Gibt alle einmaligen Termine für den heutigen Tag zurück."""
        heute = datetime.now().strftime("%Y-%m-%d")
        with cls._connect() as conn:
            cursor = conn.cursor()
            # FEHLER BEHOBEN: Anführungszeichen und Komma aus dem String-Template entfernt
            cursor.execute(
                "SELECT id, task, due_datetime FROM reminders WHERE is_done = 0 AND due_datetime LIKE ?",
                (f"{heute}%",)
            )
            return cursor.fetchall()

    @classmethod
    def get_open_reminders(cls):
        with cls._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, chat_id, task, due_datetime, recurring FROM reminders WHERE is_done = 0 ORDER BY due_datetime"
            )
            return cursor.fetchall()

    @classmethod
    def update_reminder_time(cls, reminder_id: int, due_datetime):
        dt_str = due_datetime.isoformat() if hasattr(due_datetime, 'isoformat') else str(due_datetime)
        with cls._connect() as conn:
            conn.execute("UPDATE reminders SET due_datetime = ? WHERE id = ?", (dt_str, reminder_id))

    @classmethod
    def mark_reminder_done(cls, reminder_id: int):
        with cls._connect() as conn:
            conn.execute("UPDATE reminders SET is_done = 1 WHERE id = ?", (reminder_id,))

