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
    from agro_tools.fields_ui import FieldEditPopup, FieldCardScreen, FieldsScreen
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


if __name__ == "__main__":
    unittest.main()
