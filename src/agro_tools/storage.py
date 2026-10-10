import sqlite3
from datetime import date
from math import isfinite


class FieldStorage:
    def __init__(self, database_path):
        self.database_path = str(database_path)

        connection = self.connect()
        try:
            with connection:
                connection.executescript("""
                CREATE TABLE IF NOT EXISTS fields (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    area_ha REAL NOT NULL CHECK (area_ha > 0)
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

    def add_operation(self, field_id, operation_date, operation_type, note=""):
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

                cursor = connection.execute(
                    """
                    INSERT INTO operations
                        (field_id, operation_date, operation_type, note)
                    VALUES (?, ?, ?, ?)
                    """,
                    (field_id, normalized_date, operation_type, note.strip()),
                )
                return cursor.lastrowid
        finally:
            connection.close()

    def list_operations(self, field_id):
        connection = self.connect()
        try:
            rows = connection.execute(
                """
                SELECT id, operation_date, operation_type, note
                FROM operations
                WHERE field_id = ?
                ORDER BY operation_date DESC, id DESC
                """,
                (field_id,),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()