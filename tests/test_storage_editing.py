import tempfile
import unittest
from pathlib import Path

from agro_tools.storage import FieldStorage


class StorageEditingTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / 'fields.db'
        self.storage = FieldStorage(self.path)
        self.field = self.storage.add_field('Первое', 86.4)
        self.other_field = self.storage.add_field('Второе', 20)
        self.season = self.storage.add_season(self.field, 2026, 'Пшеница')
        self.next_season = self.storage.add_season(self.field, 2027, 'Ячмень')
        self.other_season = self.storage.add_season(self.other_field, 2026, 'Рожь')
        self.operation = self.storage.add_operation(
            self.field, '2026-09-12', 'Посев', 'Исходная заметка', self.season
        )

    def test_update_field_preserves_relationships_and_survives_reopen(self):
        original = self.storage.get_operation(self.field, self.operation)
        self.storage.update_field(self.field, '  Новое название  ', 90.5)
        reopened = FieldStorage(self.path)
        self.assertEqual(reopened.get_field(self.field), {
            'id': self.field, 'name': 'Новое название', 'area_ha': 90.5,
        })
        self.assertEqual(len(reopened.list_seasons(self.field)), 2)
        self.assertEqual(reopened.get_operation(self.field, self.operation), original)
        self.assertEqual(reopened.get_field(self.other_field)['area_ha'], 20)

    def test_invalid_field_update_leaves_original_untouched(self):
        original = self.storage.get_field(self.field)
        for name, area in [('', 20), ('  ', 20), ('Название', 0),
                           ('Название', -1), ('Название', float('nan')),
                           ('Название', float('inf')), ('Название', 'нет'),
                           ('Название', None)]:
            with self.subTest(name=name, area=area), self.assertRaises(ValueError):
                self.storage.update_field(self.field, name, area)
            self.assertEqual(self.storage.get_field(self.field), original)
        with self.assertRaisesRegex(ValueError, 'Поле не найдено'):
            self.storage.update_field(999, 'Нет поля', 10)

    def test_update_operation_all_fields_and_filtering(self):
        self.storage.update_operation(
            self.field, self.operation, '2027-04-05', 'Обследование',
            '  Исправленная заметка  ', self.next_season,
        )
        reopened = FieldStorage(self.path)
        self.assertEqual(reopened.get_operation(self.field, self.operation), {
            'id': self.operation, 'field_id': self.field,
            'operation_date': '2027-04-05', 'operation_type': 'Обследование',
            'note': 'Исправленная заметка', 'season_id': self.next_season,
        })
        self.assertEqual(reopened.list_operations(self.field, self.season), [])
        self.assertEqual(len(reopened.list_operations(self.field, self.next_season)), 1)
        self.assertEqual(len(reopened.list_operations(self.field)), 1)

    def test_assign_and_remove_season_on_legacy_record(self):
        legacy = self.storage.add_operation(self.field, '2026-10-10', 'Другая работа')
        self.storage.update_operation(self.field, legacy, '2026-10-10', 'Посев', '', self.season)
        self.assertEqual(self.storage.get_operation(self.field, legacy)['season_id'], self.season)
        self.storage.update_operation(self.field, legacy, '2026-10-10', 'Посев', '', None)
        self.assertIsNone(self.storage.get_operation(self.field, legacy)['season_id'])

    def test_invalid_operation_update_is_atomic(self):
        original = self.storage.get_operation(self.field, self.operation)
        invalid = [
            ('2026-02-30', 'Посев', self.season),
            ('20261010', 'Посев', self.season),
            ('2026-W41-6', 'Посев', self.season),
            ('10.10.2026', 'Посев', self.season),
            ('2026-10-10', ' ', self.season),
            ('2026-10-10', 'Посев', self.other_season),
            ('2026-10-10', 'Посев', 999),
        ]
        for day, kind, season in invalid:
            with self.subTest(day=day, kind=kind, season=season), self.assertRaises(ValueError):
                self.storage.update_operation(self.field, self.operation, day, kind, 'Изменено', season)
            self.assertEqual(self.storage.get_operation(self.field, self.operation), original)

    def test_cannot_read_or_update_another_fields_record(self):
        self.assertIsNone(self.storage.get_operation(self.other_field, self.operation))
        with self.assertRaises(ValueError):
            self.storage.update_operation(self.other_field, self.operation, '2026-10-10', 'Посев')
        with self.assertRaises(ValueError):
            self.storage.update_operation(self.field, 999, '2026-10-10', 'Посев')
        self.assertEqual(self.storage.get_operation(self.field, self.operation)['note'], 'Исходная заметка')

    def test_edit_preserves_calculation_kind_and_multiline_note(self):
        note = 'Норма: 0.5 л/га\nПрепарат: 43.2 л'
        calculation = self.storage.add_operation(self.field, '2026-10-10', 'Расчёт опрыскивания', note)
        self.storage.update_operation(self.field, calculation, '2026-10-11', 'Расчёт опрыскивания', note, self.season)
        record = self.storage.get_operation(self.field, calculation)
        self.assertEqual(record['operation_type'], 'Расчёт опрыскивания')
        self.assertEqual(record['note'], note)


if __name__ == '__main__':
    unittest.main()
