from datetime import date

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput


def add_label(layout, text, font_size="18sp"):
    label = Label(
        text=text,
        font_size=font_size,
        size_hint_y=None,
        halign="left",
        valign="middle",
    )
    label.bind(
        width=lambda w, width: setattr(w, "text_size", (width, None)),
        texture_size=lambda w, size: setattr(w, "height", size[1] + dp(16)),
    )
    layout.add_widget(label)
    return label


def add_button(layout, text, callback):
    button = Button(
        text=text,
        size_hint_y=None,
        height=dp(56),
    )
    button.bind(on_release=callback)
    layout.add_widget(button)
    return button


def add_input(layout, caption, text="", multiline=False):
    add_label(layout, caption)
    entry = TextInput(
        text=text,
        multiline=multiline,
        font_size="18sp",
        size_hint_y=None,
        height=dp(100) if multiline else dp(48),
    )
    layout.add_widget(entry)
    return entry


class JournalScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        scroll = ScrollView()
        self.content = BoxLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(10),
            size_hint_y=None,
        )
        self.content.bind(
            minimum_height=self.content.setter("height")
        )
        scroll.add_widget(self.content)
        self.add_widget(scroll)

    @property
    def storage(self):
        return App.get_running_app().storage

    def go_menu(self, _button):
        self.manager.current = "menu"


class FieldsScreen(JournalScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        add_label(self.content, "Мои поля", "24sp")

        self.name_input = add_input(self.content, "Название поля")
        self.area_input = add_input(self.content, "Площадь, га")
        self.area_input.input_type = "number"

        add_button(self.content, "Добавить поле", self.save_field)
        self.message = add_label(self.content, "")

        self.field_list = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint_y=None,
        )
        self.field_list.bind(
            minimum_height=self.field_list.setter("height")
        )
        self.content.add_widget(self.field_list)

        add_button(self.content, "В главное меню", self.go_menu)

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        self.field_list.clear_widgets()
        fields = self.storage.list_fields()

        if not fields:
            add_label(self.field_list, "Пока нет сохранённых полей.")

        for field in fields:
            button = add_button(
                self.field_list,
                f"{field['name']} — {field['area_ha']:g} га",
                lambda _button, field_id=field["id"]:
                self.open_field(field_id),
            )
            button.bind(
                size=lambda w, size: setattr(w, "text_size", size)
            )

    def save_field(self, _button):
        try:
            area = float(
                self.area_input.text.strip().replace(",", ".")
            )
        except ValueError:
            self.message.text = "Введите площадь числом."
            return

        try:
            self.storage.add_field(self.name_input.text, area)
        except ValueError as error:
            self.message.text = str(error)
            return

        self.name_input.text = ""
        self.area_input.text = ""
        self.message.text = "Поле сохранено."
        self.refresh()

    def open_field(self, field_id):
        card = self.manager.get_screen("field_card")
        card.field_id = field_id
        self.manager.current = "field_card"


class FieldCardScreen(JournalScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.field_id = None
        self.heading = add_label(self.content, "", "24sp")

        add_label(self.content, "Добавить выполненную работу")
        self.date_input = add_input(
            self.content, "Дата: ГГГГ-ММ-ДД", date.today().isoformat()
        )

        add_label(self.content, "Тип работы")
        self.operation_type = Spinner(
            text="Посев",
            values=(
                "Посев",
                "Опрыскивание",
                "Внесение удобрений",
                "Обследование",
                "Обработка почвы",
                "Уборка",
                "Другая работа",
            ),
            size_hint_y=None,
            height=dp(48),
        )
        self.content.add_widget(self.operation_type)

        self.note_input = add_input(
            self.content, "Заметка", multiline=True
        )
        add_button(self.content, "Сохранить работу", self.save_operation)
        self.message = add_label(self.content, "")

        add_label(self.content, "История работ", "22sp")
        self.history = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint_y=None,
        )
        self.history.bind(minimum_height=self.history.setter("height"))
        self.content.add_widget(self.history)

        add_button(self.content, "К списку полей", self.go_fields)

    def on_pre_enter(self, *args):
        self.date_input.text = date.today().isoformat()
        self.operation_type.text = "Посев"
        self.note_input.text = ""
        self.message.text = ""
        self.refresh()

    def refresh(self):
        field = self.storage.get_field(self.field_id)
        if field is None:
            self.heading.text = "Поле не найдено."
            self.history.clear_widgets()
            return

        self.heading.text = (
            f"{field['name']}\nПлощадь: {field['area_ha']:g} га"
        )
        self.history.clear_widgets()
        operations = self.storage.list_operations(self.field_id)

        if not operations:
            add_label(self.history, "Работы ещё не добавлены.")

        for operation in operations:
            text = (
                f"{operation['operation_date']} — "
                f"{operation['operation_type']}"
            )
            if operation["note"]:
                text += f"\n{operation['note']}"
            add_label(self.history, text)

    def save_operation(self, _button):
        try:
            self.storage.add_operation(
                self.field_id,
                self.date_input.text.strip(),
                self.operation_type.text,
                self.note_input.text,
            )
        except ValueError as error:
            self.message.text = str(error)
            return

        self.note_input.text = ""
        self.message.text = "Работа сохранена."
        self.refresh()

    def go_fields(self, _button):
        self.manager.current = "fields"