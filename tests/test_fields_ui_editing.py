"""UI integration tests; run with Kivy 2.3.1 and a working SDL2 display."""
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("KIVY_NO_ARGS", "1")

try:
    from kivy.app import App
except ImportError:
    App = None

if App is not None:
    from agro_tools.fields_ui import (
        FieldEditPopup, OperationEditPopup, FieldCardScreen, FieldsScreen,
    )
    from agro_tools.storage import FieldStorage
    from kivy.uix.screenmanager import ScreenManager


@unittest.skipIf(App is None, "Kivy is installed separately from the Android build environment")
class FieldEditingUITests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.storage = FieldStorage(Path(folder.name) / "test.db")
        self.field = self.storage.add_field("Первое", 86.4)
        self.app = App()
        self.app.storage = self.storage
        self.addCleanup(setattr, App, "_running_app", None)
        self.manager = ScreenManager()
        self.fields = FieldsScreen(name="fields")
        self.card = FieldCardScreen(name="field_card")
        self.manager.add_widget(self.fields)
        self.manager.add_widget(self.card)
        self.fields.open_field(self.field)

    def test_save_field_refreshes_card_and_list_and_accepts_comma(self):
        editor = FieldEditPopup(self.storage, self.storage.get_field(self.field), self.card.field_saved)
        editor.name_input.text = "Исправлено"
        editor.area_input.text = "90,5"
        editor.save(None)
        self.assertIn("Исправлено", self.card.heading.text)
        self.assertIn("90.5", self.card.heading.text)
        self.card.go_fields(None)
        self.assertTrue(any("Исправлено" in child.text for child in self.fields.field_list.children))

    def test_invalid_area_keeps_data_and_draft(self):
        editor = FieldEditPopup(self.storage, self.storage.get_field(self.field), self.card.field_saved)
        editor.area_input.text = "nan"
        editor.save(None)
        self.assertTrue(editor.error.text)
        self.assertEqual(editor.area_input.text, "nan")
        self.assertEqual(self.storage.get_field(self.field)["area_ha"], 86.4)

    def test_cancel_does_not_save_changes(self):
        editor = FieldEditPopup(self.storage, self.storage.get_field(self.field), self.card.field_saved)
        editor.name_input.text = "Не сохранять"
        editor.dismiss()
        self.assertEqual(self.storage.get_field(self.field)["name"], "Первое")

    def operation_editor(self, kind="Посев", season_id=None):
        self.operation = self.storage.add_operation(
            self.field, "2026-09-12", kind, "Старая заметка", season_id
        )
        return OperationEditPopup(
            self.storage, self.storage.get_operation(self.field, self.operation),
            self.card.operation_saved,
        )

    def test_edit_operation_prefills_and_saves_all_values(self):
        season = self.storage.add_season(self.field, 2027, "Пшеница")
        self.card.refresh()
        editor = self.operation_editor()
        self.assertEqual(editor.date_input.text, "2026-09-12")
        self.assertEqual(editor.note_input.text, "Старая заметка")
        editor.date_input.text = "2027-04-05"
        editor.operation_type.text = "Обследование"
        editor.note_input.text = "Новая заметка\nВторая строка"
        editor.season_picker.text = next(iter(editor.season_choices))
        editor.save(None)
        record = self.storage.get_operation(self.field, self.operation)
        self.assertEqual(record["operation_date"], "2027-04-05")
        self.assertEqual(record["operation_type"], "Обследование")
        self.assertEqual(record["note"], "Новая заметка\nВторая строка")
        self.assertEqual(record["season_id"], season)
        self.assertEqual(len(self.storage.list_operations(self.field)), 1)

    def test_invalid_date_leaves_editor_and_record_intact(self):
        editor = self.operation_editor()
        editor.date_input.text = "2026-02-30"
        editor.note_input.text = "Черновик"
        editor.save(None)
        self.assertTrue(editor.error.text)
        self.assertEqual(editor.note_input.text, "Черновик")
        self.assertEqual(self.storage.get_operation(self.field, self.operation)["note"], "Старая заметка")

    def test_cancel_operation_does_not_save(self):
        editor = self.operation_editor()
        editor.note_input.text = "Не сохранять"
        editor.dismiss()
        self.assertEqual(self.storage.get_operation(self.field, self.operation)["note"], "Старая заметка")

    def test_preserves_unknown_and_calculation_types(self):
        for kind in ("Расчёт опрыскивания", "Старая нестандартная работа"):
            editor = self.operation_editor(kind)
            self.assertEqual(editor.operation_type.text, kind)
            self.assertIn(kind, editor.operation_type.values)
            editor.save(None)
            self.assertEqual(self.storage.get_operation(self.field, self.operation)["operation_type"], kind)

    def test_seasons_are_limited_to_current_field(self):
        own = self.storage.add_season(self.field, 2027, "Пшеница")
        other = self.storage.add_field("Другое", 10)
        self.storage.add_season(other, 2028, "Рожь")
        editor = self.operation_editor()
        self.assertEqual(set(editor.season_choices.values()), {own})

    def test_moving_record_updates_active_filter_and_history(self):
        old = self.storage.add_season(self.field, 2026, "Пшеница")
        new = self.storage.add_season(self.field, 2027, "Ячмень")
        self.card.refresh()
        old_label = next(k for k, v in self.card.season_choices.items() if v == old)
        new_label = next(k for k, v in self.card.season_choices.items() if v == new)
        self.card.history_filter.text = old_label
        editor = self.operation_editor(season_id=old)
        editor.season_picker.text = new_label
        editor.save(None)
        self.assertEqual(self.card.history_filter.text, new_label)
        self.assertTrue(any("Старая заметка" in getattr(c, "text", "") for c in self.card.history.children))
        editor = OperationEditPopup(
            self.storage, self.storage.get_operation(self.field, self.operation), self.card.operation_saved,
        )
        editor.season_picker.text = "Без сезона"
        editor.save(None)
        self.assertEqual(self.card.history_filter.text, "Без сезона")
        self.assertIsNone(self.storage.get_operation(self.field, self.operation)["season_id"])


if __name__ == "__main__":
    unittest.main()
