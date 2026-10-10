import sqlite3
import tempfile
import unittest
from pathlib import Path

from agro_tools.storage import FieldStorage


class SeasonStorageTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'fields.db'

    def test_migration_preserves_old_records_and_backup(self):
        connection = sqlite3.connect(self.path)
        connection.executescript("""
            CREATE TABLE fields(id INTEGER PRIMARY KEY, name TEXT NOT NULL, area_ha REAL NOT NULL);
            CREATE TABLE operations(id INTEGER PRIMARY KEY, field_id INTEGER NOT NULL,
                operation_date TEXT NOT NULL, operation_type TEXT NOT NULL, note TEXT NOT NULL DEFAULT '');
            INSERT INTO fields VALUES(1, 'Поле 12', 86.4);
            INSERT INTO operations VALUES(1, 1, '2026-09-12', 'Посев', 'Старая запись');
        """)
        connection.close()
        store = FieldStorage(self.path)
        self.assertEqual(store.get_field(1)['area_ha'], 86.4)
        record = store.list_operations(1, season_id=None)[0]
        self.assertEqual(record['note'], 'Старая запись')
        self.assertIsNone(record['season_id'])
        backup = sqlite3.connect(str(self.path) + '.before-seasons.bak')
        try:
            self.assertEqual(backup.execute('SELECT note FROM operations').fetchone()[0], 'Старая запись')
            self.assertNotIn('season_id', [row[1] for row in backup.execute('PRAGMA table_info(operations)')])
        finally:
            backup.close()
        self.assertEqual(len(FieldStorage(self.path).list_operations(1)), 1)

    def test_filters_and_reopening(self):
        store = FieldStorage(self.path)
        field = store.add_field('Поле', 10)
        season = store.add_season(field, 2027, 'Пшеница', 'Сорт')
        store.add_operation(field, '2026-09-12', 'Посев', 'Осенний посев', season_id=season)
        store.add_operation(field, '2026-10-10', 'Расчёт опрыскивания', 'Расчёт')
        reopened = FieldStorage(self.path)
        self.assertEqual(len(reopened.list_operations(field)), 2)
        self.assertEqual(len(reopened.list_operations(field, season)), 1)
        self.assertEqual(len(reopened.list_operations(field, None)), 1)
        self.assertEqual(reopened.list_operations(field, season)[0]['harvest_year'], 2027)

    def test_rejects_other_fields_season(self):
        store = FieldStorage(self.path)
        first = store.add_field('Первое', 10)
        second = store.add_field('Второе', 20)
        season = store.add_season(first, 2026, 'Ячмень')
        with self.assertRaises(ValueError):
            store.add_operation(second, '2026-10-10', 'Посев', season_id=season)
        self.assertEqual(store.list_operations(second), [])

    def test_duplicate_year_and_invalid_inputs(self):
        store = FieldStorage(self.path)
        field = store.add_field('Поле', 10)
        store.add_season(field, 2026, 'Ячмень')
        for year, crop in [(2026, 'Пшеница'), ('2026.5', 'Пшеница'), (1800, 'Пшеница'), (2027, '')]:
            with self.assertRaises(ValueError):
                store.add_season(field, year, crop)
        with self.assertRaises(ValueError):
            store.add_season(999, 2027, 'Пшеница')


if __name__ == '__main__':
    unittest.main()
