from datetime import date
import sqlite3

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
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


class EditPopup(Popup):
    """Прокручиваемая форма: изменения пишутся только кнопкой сохранения."""

    def __init__(self, **kwargs):
        super().__init__(size_hint=(0.95, 0.9), **kwargs)
        scroll = ScrollView()
        self.form = BoxLayout(
            orientation="vertical", spacing=dp(10),
            padding=[dp(16), dp(16), dp(16), dp(64)], size_hint_y=None,
        )
        self.form.bind(minimum_height=self.form.setter("height"))
        scroll.add_widget(self.form)
        self.content = scroll

    def add_actions(self, save_callback):
        self.error = add_label(self.form, "")
        add_button(self.form, "Сохранить изменения", save_callback)
        add_button(self.form, "Отмена", lambda _button: self.dismiss())


class FieldEditPopup(EditPopup):
    def __init__(self, storage, field, on_saved, **kwargs):
        super().__init__(title="Редактирование поля", **kwargs)
        self.storage = storage
        self.field_id = field["id"]
        self.on_saved = on_saved
        self.name_input = add_input(self.form, "Название поля", field["name"])
        self.area_input = add_input(self.form, "Площадь, га", str(field["area_ha"]))
        self.area_input.input_type = "number"
        self.add_actions(self.save)

    def save(self, _button):
        try:
            area = self.area_input.text.strip().replace(",", ".")
            self.storage.update_field(self.field_id, self.name_input.text, area)
        except ValueError as error:
            self.error.text = str(error)
            return
        except sqlite3.Error:
            self.error.text = "Не удалось сохранить поле. Повторите попытку."
            return
        self.dismiss()
        self.on_saved()


class OperationEditPopup(EditPopup):
    def __init__(self, storage, operation, on_saved, **kwargs):
        super().__init__(title="Редактирование записи", **kwargs)
        self.storage = storage
        self.field_id = operation["field_id"]
        self.operation_id = operation["id"]
        self.on_saved = on_saved
        self.date_input = add_input(
            self.form, "Дата: ГГГГ-ММ-ДД", operation["operation_date"]
        )
        add_label(self.form, "Тип работы")
        kinds = (
            "Посев", "Опрыскивание", "Внесение удобрений", "Обследование",
            "Обработка почвы", "Уборка", "Другая работа", "Расчёт опрыскивания",
        )
        # Не заменяем неизвестный старый тип на первый пункт списка.
        self.operation_type = Spinner(
            text=operation["operation_type"],
            values=tuple(dict.fromkeys((*kinds, operation["operation_type"]))),
            size_hint_y=None, height=dp(48),
        )
        self.form.add_widget(self.operation_type)
        add_label(self.form, "Сезон записи")
        self.season_choices = {
            f"{s['harvest_year']} — {s['crop']}"
            + (f" ({s['variety']})" if s["variety"] else ""): s["id"]
            for s in storage.list_seasons(self.field_id)
        }
        selected = next(
            (label for label, season_id in self.season_choices.items()
             if season_id == operation["season_id"]), "Без сезона"
        )
        self.season_picker = Spinner(
            text=selected, values=("Без сезона", *self.season_choices),
            size_hint_y=None, height=dp(48),
        )
        self.form.add_widget(self.season_picker)
        self.note_input = add_input(self.form, "Заметка", operation["note"], multiline=True)
        self.add_actions(self.save)

    def save(self, _button):
        season_id = self.season_choices.get(self.season_picker.text)
        try:
            self.storage.update_operation(
                self.field_id, self.operation_id, self.date_input.text.strip(),
                self.operation_type.text, self.note_input.text, season_id=season_id,
            )
        except ValueError as error:
            self.error.text = str(error)
            return
        except sqlite3.Error:
            self.error.text = "Не удалось сохранить запись. Повторите попытку."
            return
        self.dismiss()
        self.on_saved(season_id)


class JournalScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        scroll = ScrollView()
        self.content = BoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(16), dp(16), dp(64)],
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
        add_button(self.content, "Редактировать поле", self.edit_field)
        self.field_message = add_label(self.content, "")

        add_label(self.content, "Новый сезон", "22sp")
        self.year_input = add_input(self.content, "Год урожая", str(date.today().year))
        self.year_input.input_type = "number"
        self.crop_input = add_input(self.content, "Культура")
        self.variety_input = add_input(self.content, "Сорт / гибрид (необязательно)")
        add_button(self.content, "Создать сезон", self.save_season)
        self.season_message = add_label(self.content, "")

        add_label(self.content, "Сезон для новой работы")
        self.season_choices = {}
        self.season_picker = Spinner(text="Без сезона", values=("Без сезона",),
                                     size_hint_y=None, height=dp(48))
        self.content.add_widget(self.season_picker)

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
        self.history_filter = Spinner(text="Все сезоны", values=("Все сезоны", "Без сезона"),
                                      size_hint_y=None, height=dp(48))
        self.content.add_widget(self.history_filter)
        self.history_filter.bind(text=lambda *args: self.refresh_history())
        self.history = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint_y=None,
        )
        self.history.bind(minimum_height=self.history.setter("height"))
        self.content.add_widget(self.history)

        add_button(self.content, "К списку полей", self.go_fields)

    def on_pre_enter(self, *args):
        self.field_message.text = ""
        self.date_input.text = date.today().isoformat()
        self.operation_type.text = "Посев"
        self.note_input.text = ""
        self.message.text = ""
        self.season_message.text = ""
        self.crop_input.text = ""
        self.variety_input.text = ""
        self.year_input.text = str(date.today().year)
        self.season_picker.text = "Без сезона"
        self.history_filter.text = "Все сезоны"
        self.refresh()

    def edit_field(self, _button):
        field = self.storage.get_field(self.field_id)
        if field is None:
            self.field_message.text = "Поле не найдено."
            return
        FieldEditPopup(self.storage, field, self.field_saved).open()

    def field_saved(self):
        self.field_message.text = "Изменения поля сохранены."
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
        self.season_choices = {
            f"{s['harvest_year']} — {s['crop']}" + (f" ({s['variety']})" if s['variety'] else ""): s["id"]
            for s in self.storage.list_seasons(self.field_id)
        }
        self.season_picker.values = ("Без сезона", *self.season_choices)
        self.history_filter.values = ("Все сезоны", "Без сезона", *self.season_choices)
        if self.season_picker.text not in self.season_picker.values:
            self.season_picker.text = "Без сезона"
        if self.history_filter.text not in self.history_filter.values:
            self.history_filter.text = "Все сезоны"
        self.refresh_history()

    def refresh_history(self):
        self.history.clear_widgets()
        selected = self.history_filter.text
        if selected == "Все сезоны":
            operations = self.storage.list_operations(self.field_id)
        else:
            operations = self.storage.list_operations(
                self.field_id, season_id=self.season_choices.get(selected)
            )

        if not operations:
            add_label(self.history, "Работы ещё не добавлены.")

        for operation in operations:
            text = (
                f"{operation['operation_date']} — "
                f"{operation['operation_type']}"
            )
            season_label = (
                f"Урожай {operation['harvest_year']} — {operation['crop']}"
                if operation["season_id"] is not None else "Без сезона"
            )
            text += f"\n{season_label}"
            if operation["note"]:
                text += f"\n{operation['note']}"
            add_label(self.history, text)
            add_button(
                self.history, "Редактировать запись",
                lambda _button, operation_id=operation["id"]:
                self.edit_operation(operation_id),
            )

    def edit_operation(self, operation_id):
        operation = self.storage.get_operation(self.field_id, operation_id)
        if operation is None:
            self.message.text = "Запись не найдена в истории этого поля."
            return
        OperationEditPopup(self.storage, operation, self.operation_saved).open()

    def operation_saved(self, season_id):
        # После переноса запись остаётся видна, даже если был включён фильтр.
        if self.history_filter.text != "Все сезоны":
            self.history_filter.text = next(
                (label for label, value in self.season_choices.items() if value == season_id),
                "Без сезона",
            )
        self.message.text = "Изменения записи сохранены."
        self.refresh_history()

    def save_operation(self, _button):
        try:
            self.storage.add_operation(
                self.field_id,
                self.date_input.text.strip(),
                self.operation_type.text,
                self.note_input.text,
                season_id=self.season_choices.get(self.season_picker.text),
            )
        except ValueError as error:
            self.message.text = str(error)
            return

        self.note_input.text = ""
        self.message.text = "Работа сохранена."
        self.refresh()

    def save_season(self, _button):
        try:
            season_id = self.storage.add_season(
                self.field_id, self.year_input.text,
                self.crop_input.text, self.variety_input.text,
            )
        except ValueError as error:
            self.season_message.text = str(error)
            return
        self.refresh()
        label = next(label for label, value in self.season_choices.items() if value == season_id)
        self.season_picker.text = label
        self.history_filter.text = label
        self.crop_input.text = ""
        self.variety_input.text = ""
        self.season_message.text = "Сезон создан и выбран для новых работ."

    def go_fields(self, _button):
        self.manager.current = "fields"
