import sqlite3
from datetime import date
from math import isfinite
from pathlib import Path

_ALL_SEASONS = object()


class FieldStorage:
    def __init__(self, database_path):
        self.database_path = str(database_path)

        connection = self.connect()
        try:
            old_operations = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='operations'"
            ).fetchone()
            if old_operations:
                columns = {row["name"] for row in connection.execute("PRAGMA table_info(operations)")}
                if "season_id" not in columns:
                    backup_path = Path(self.database_path + ".before-seasons.bak")
                    if backup_path.exists():
                        raise ValueError("Резервная копия уже существует. Сохраните её отдельно перед обновлением базы.")
                    backup = sqlite3.connect(str(backup_path))
                    try:
                        connection.backup(backup)
                    finally:
                        backup.close()
            with connection:
                connection.executescript("""
                CREATE TABLE IF NOT EXISTS fields (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    area_ha REAL NOT NULL CHECK (area_ha > 0)
                );

                CREATE TABLE IF NOT EXISTS seasons (
                    id INTEGER PRIMARY KEY,
                    field_id INTEGER NOT NULL REFERENCES fields(id),
                    harvest_year INTEGER NOT NULL CHECK (harvest_year BETWEEN 1900 AND 2200),
                    crop TEXT NOT NULL,
                    variety TEXT NOT NULL DEFAULT '',
                    UNIQUE(field_id, harvest_year)
                );

                CREATE TABLE IF NOT EXISTS operations (
                    id INTEGER PRIMARY KEY,
                    field_id INTEGER NOT NULL,
                    operation_date TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    note TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY (field_id) REFERENCES fields(id)
                );

                CREATE INDEX IF NOT EXISTS operations_field_date
                ON operations(field_id, operation_date);
            """)
                columns = {row["name"] for row in connection.execute("PRAGMA table_info(operations)")}
                if "season_id" not in columns:
                    connection.execute(
                        "ALTER TABLE operations ADD COLUMN season_id INTEGER REFERENCES seasons(id)"
                    )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS operations_season ON operations(season_id)"
                )
        finally:
            connection.close()

    def connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def add_field(self, name, area_ha):
        name = name.strip()
        if not name:
            raise ValueError("Введите название поля.")

        area_ha = float(area_ha)
        if not isfinite(area_ha) or area_ha <= 0:
            raise ValueError("Площадь должна быть больше нуля.")

        connection = self.connect()
        try:
            with connection:
                cursor = connection.execute(
                    "INSERT INTO fields (name, area_ha) VALUES (?, ?)",
                    (name, area_ha),
                )
                return cursor.lastrowid
        finally:
            connection.close()

    def list_fields(self):
        connection = self.connect()
        try:
            rows = connection.execute(
                "SELECT id, name, area_ha FROM fields ORDER BY name, id"
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def get_field(self, field_id):
        connection = self.connect()
        try:
            row = connection.execute(
                "SELECT id, name, area_ha FROM fields WHERE id = ?",
                (field_id,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            connection.close()

    def add_operation(self, field_id, operation_date, operation_type, note="", season_id=None):
        try:
            normalized_date = date.fromisoformat(operation_date).isoformat()
        except ValueError:
            raise ValueError("Дата должна быть в формате ГГГГ-ММ-ДД.")

        operation_type = operation_type.strip()
        if not operation_type:
            raise ValueError("Выберите тип работы.")

        connection = self.connect()
        try:
            with connection:
                exists = connection.execute(
                    "SELECT id FROM fields WHERE id = ?", (field_id,)
                ).fetchone()
                if exists is None:
                    raise ValueError("Поле не найдено.")

                if season_id is not None:
                    season = connection.execute(
                        "SELECT id FROM seasons WHERE id = ? AND field_id = ?",
                        (season_id, field_id),
                    ).fetchone()
                    if season is None:
                        raise ValueError("Сезон не принадлежит выбранному полю.")

                cursor = connection.execute(
                    """
                    INSERT INTO operations
                        (field_id, operation_date, operation_type, note, season_id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (field_id, normalized_date, operation_type, note.strip(), season_id),
                )
                return cursor.lastrowid
        finally:
            connection.close()

    def add_season(self, field_id, harvest_year, crop, variety=""):
        try:
            year = int(str(harvest_year).strip())
        except (ValueError, TypeError):
            raise ValueError("Введите год урожая целым числом.")
        if not 1900 <= year <= 2200:
            raise ValueError("Год урожая должен быть от 1900 до 2200.")
        crop = crop.strip()
        if not crop:
            raise ValueError("Введите культуру.")
        connection = self.connect()
        try:
            with connection:
                if connection.execute("SELECT id FROM fields WHERE id=?", (field_id,)).fetchone() is None:
                    raise ValueError("Поле не найдено.")
                try:
                    cursor = connection.execute(
                        "INSERT INTO seasons(field_id, harvest_year, crop, variety) VALUES (?, ?, ?, ?)",
                        (field_id, year, crop, variety.strip()),
                    )
                except sqlite3.IntegrityError:
                    raise ValueError("Для этого поля уже есть сезон с таким годом урожая.")
                return cursor.lastrowid
        finally:
            connection.close()

    def list_seasons(self, field_id):
        connection = self.connect()
        try:
            return [dict(row) for row in connection.execute(
                "SELECT id, field_id, harvest_year, crop, variety FROM seasons WHERE field_id=? ORDER BY harvest_year DESC",
                (field_id,),
            )]
        finally:
            connection.close()

    def list_operations(self, field_id, season_id=_ALL_SEASONS):
        # Без второго аргумента возвращаем всю историю, как в прежней версии.
        query = """
            SELECT o.id, o.operation_date, o.operation_type, o.note, o.season_id,
                   s.harvest_year, s.crop, s.variety
            FROM operations o LEFT JOIN seasons s ON s.id=o.season_id
            WHERE o.field_id=?
        """
        parameters = [field_id]
        if season_id is None:
            query += " AND o.season_id IS NULL"
        elif season_id is not _ALL_SEASONS:
            query += " AND o.season_id=?"
            parameters.append(season_id)
        query += " ORDER BY o.operation_date DESC, o.id DESC"
        connection = self.connect()
        try:
            return [dict(row) for row in connection.execute(query, parameters)]
        finally:
            connection.close()
