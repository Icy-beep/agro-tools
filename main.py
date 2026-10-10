import sys
from math import isfinite
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from kivy.uix.spinner import Spinner

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from agro_tools.storage import FieldStorage
from agro_tools.fields_ui import FieldsScreen, FieldCardScreen

from agro_tools.seeding import calculate_seed_rate
from agro_tools.spraying import (
    calculate_product_amount,
    calculate_solution_amount,
    calculate_area_per_tank,
    calculate_product_per_tank,
    calculate_tank_count,
    calculate_last_tank,
)


class CalculatorScreen(Screen):
    def __init__(self, title, fields, calculator, **kwargs):
        super().__init__(**kwargs)
        self.calculator = calculator
        self.inputs = {}

        scroll = ScrollView()
        layout = BoxLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(10),
            size_hint_y=None,
        )
        layout.bind(minimum_height=layout.setter("height"))

        layout.add_widget(Label(
            text=title,
            font_size="24sp",
            size_hint_y=None,
            height=dp(60),
        ))

        for key, caption, default in fields:
            label = Label(
                text=caption,
                size_hint_y=None,
                height=dp(40),
                halign="left",
                valign="middle",
            )
            label.bind(size=lambda w, size: setattr(w, "text_size", size))
            layout.add_widget(label)

            entry = TextInput(
                text=default,
                multiline=False,
                input_type="number",
                font_size="20sp",
                size_hint_y=None,
                height=dp(48),
            )
            self.inputs[key] = entry
            layout.add_widget(entry)

        calculate_button = Button(
            text="Рассчитать",
            size_hint_y=None,
            height=dp(56),
        )
        calculate_button.bind(on_release=self.calculate)
        layout.add_widget(calculate_button)

        self.result = Label(
            text="Введите данные и нажмите «Рассчитать»",
            font_size="18sp",
            size_hint_y=None,
            halign="left",
            valign="top",
        )
        self.result.bind(
            width=lambda w, width: setattr(w, "text_size", (width, None)),
            texture_size=lambda w, size: setattr(w, "height", size[1] + dp(24)),
        )
        layout.add_widget(self.result)

        back_button = Button(
            text="В главное меню",
            size_hint_y=None,
            height=dp(52),
        )
        back_button.bind(on_release=self.go_back)
        layout.add_widget(back_button)

        scroll.add_widget(layout)
        self.add_widget(scroll)

    def go_back(self, _button):
        self.manager.current = "menu"

    def calculate(self, _button):
        values = {}

        for key, entry in self.inputs.items():
            try:
                value = float(entry.text.strip().replace(",", "."))
            except ValueError:
                self.result.text = "Заполните все поля числами."
                return

            if not isfinite(value) or value <= 0:
                self.result.text = "Все значения должны быть больше нуля."
                return

            values[key] = value

        try:
            self.result.text = self.calculator(values)
        except ValueError as error:
            self.result.text = str(error)


class FieldSprayingScreen(CalculatorScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.selected_field_id = None
        self.field_choices = {}
        self.season_choices = {}
        self.selected_season_id = None
        self.saved_calculation = None

        # Получаем существующий вертикальный контейнер.
        layout = self.children[0].children[0]

        self.field_picker = Spinner(
            text="Без привязки к полю",
            values=("Без привязки к полю",),
            size_hint_y=None,
            height=dp(56),
        )
        # Ставим выбор поля сразу после заголовка.
        layout.add_widget(
            self.field_picker,
            index=len(layout.children) - 1,
        )
        self.season_picker = Spinner(
            text="Без сезона",
            values=("Без сезона",),
            disabled=True,
            size_hint_y=None,
            height=dp(56),
        )
        layout.add_widget(self.season_picker, index=len(layout.children) - 2)
        self.season_picker.bind(text=self.select_season)
        self.field_picker.bind(text=self.select_field)

        self.save_button = Button(
            text="Сохранить расчёт в историю поля",
            disabled=True,
            size_hint_y=None,
            height=dp(56),
        )
        self.save_button.bind(on_release=self.save_calculation)

        # Ставим кнопку перед кнопкой возврата в меню.
        layout.add_widget(self.save_button, index=1)

        self.save_message = Label(
            text="",
            size_hint_y=None,
            height=dp(64),
            halign="center",
            valign="middle",
        )
        self.save_message.bind(
            size=lambda w, size: setattr(w, "text_size", size)
        )
        layout.add_widget(self.save_message, index=1)

        for entry in self.inputs.values():
            entry.bind(text=self.invalidate_calculation)

    @property
    def storage(self):
        return App.get_running_app().storage

    def on_pre_enter(self, *args):
        fields = self.storage.list_fields()

        self.field_choices = {
            f"№{field['id']} — {field['name']}": field
            for field in fields
        }

        self.field_picker.values = (
            "Без привязки к полю",
            *self.field_choices.keys(),
        )

        if self.field_picker.text not in self.field_picker.values:
            self.field_picker.text = "Без привязки к полю"

        self.refresh_seasons()
        self.invalidate_calculation()

    def select_field(self, _spinner, text):
        field = self.field_choices.get(text)
        self.selected_field_id = field["id"] if field else None

        if field:
            self.inputs["area"].text = str(field["area_ha"])

        self.refresh_seasons(reset=True)
        self.invalidate_calculation()

    def refresh_seasons(self, reset=False):
        field = self.field_choices.get(self.field_picker.text)
        self.selected_field_id = field["id"] if field else None
        seasons = self.storage.list_seasons(self.selected_field_id) if field else []
        self.season_choices = {
            f"Урожай {season['harvest_year']} — {season['crop']}"
            + (f" ({season['variety']})" if season['variety'] else ""): season["id"]
            for season in seasons
        }
        self.season_picker.values = ("Без сезона", *self.season_choices)
        self.season_picker.disabled = not bool(field)
        if reset or self.season_picker.text not in self.season_picker.values:
            self.season_picker.text = "Без сезона"
        self.selected_season_id = self.season_choices.get(self.season_picker.text)

    def select_season(self, _spinner, text):
        self.selected_season_id = self.season_choices.get(text)
        self.invalidate_calculation()

    def invalidate_calculation(self, *args):
        self.saved_calculation = None
        self.save_button.disabled = True
        self.save_message.text = ""
        self.result.text = "Введите данные и нажмите «Рассчитать»"

    def calculate(self, _button):
        self.invalidate_calculation()
        values = {}

        for key, entry in self.inputs.items():
            try:
                value = float(entry.text.strip().replace(",", "."))
            except ValueError:
                self.result.text = "Заполните все поля числами."
                return

            if not isfinite(value) or value <= 0:
                self.result.text = "Все значения должны быть больше нуля."
                return

            values[key] = value

        try:
            result = self.calculator(values)
        except ValueError as error:
            self.result.text = str(error)
            return

        self.result.text = result

        if self.selected_field_id is None:
            self.save_message.text = (
                "Для сохранения выберите поле и повторите расчёт."
            )
            return

        note = (
            f"Площадь обработки: {values['area']:g} га\n"
            f"Норма препарата: {values['product_rate']:g} л/га\n"
            f"Норма раствора: {values['solution_rate']:g} л/га\n"
            f"Объём бака: {values['tank']:g} л\n\n"
            f"{result}"
        )

        note = f"Сезон: {self.season_picker.text}\n" + note
        self.saved_calculation = (
            self.selected_field_id, self.selected_season_id, note
        )
        self.save_button.disabled = False

    def save_calculation(self, _button):
        if self.saved_calculation is None:
            return

        field_id, season_id, note = self.saved_calculation

        try:
            self.storage.add_operation(
                field_id=field_id,
                operation_date=date.today().isoformat(),
                operation_type="Расчёт опрыскивания",
                note=note,
                season_id=season_id,
            )
        except ValueError as error:
            self.save_message.text = str(error)
            return

        self.saved_calculation = None
        self.save_button.disabled = True
        self.save_message.text = "Расчёт сохранён в истории поля."


def seeding_result(values):
    if values["germination"] > 100:
        raise ValueError("Всхожесть не может превышать 100%.")

    rate = calculate_seed_rate(
        target_plants=values["density"],
        thousand_seed_weight=values["weight"],
        germination=values["germination"],
    )
    return f"Норма высева: {rate:.1f} кг/га"


def spraying_result(values):
    area = values["area"]
    product_rate = values["product_rate"]
    solution_rate = values["solution_rate"]
    tank = values["tank"]

    total_product = calculate_product_amount(area, product_rate)
    total_solution = calculate_solution_amount(area, solution_rate)
    tank_area = calculate_area_per_tank(tank, solution_rate)
    tank_product = calculate_product_per_tank(
        tank, solution_rate, product_rate
    )
    tank_count = calculate_tank_count(area, tank, solution_rate)
    last_area, last_volume, last_product = calculate_last_tank(
        area, tank, solution_rate, product_rate
    )

    text = (
        f"Препарата на поле: {total_product:.2f} л\n"
        f"Рабочего раствора: {total_solution:.1f} л\n"
        f"Площадь на полный бак: {tank_area:.2f} га\n"
        f"Препарата на полный бак: {tank_product:.2f} л\n"
        f"Всего заправок: {tank_count}"
    )

    if last_area > 0:
        text += (
            "\n\nПоследняя неполная заправка:\n"
            f"Площадь: {last_area:.2f} га\n"
            f"Рабочего раствора: {last_volume:.1f} л\n"
            f"Препарата: {last_product:.2f} л"
        )
    else:
        text += "\n\nВсе заправки полные."

    return text


class AgroToolsApp(App):
    def build(self):
        self.title = "Agro Tools"
        data_dir = Path(self.user_data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        self.storage = FieldStorage(data_dir / "agro_tools.db")
        manager = ScreenManager()

        menu = Screen(name="menu")
        layout = BoxLayout(
            orientation="vertical",
            padding=dp(24),
            spacing=dp(16),
        )
        layout.add_widget(Label(text="Agro Tools", font_size="30sp"))

        for caption, destination in [
            ("Посев", "seeding"),
            ("Опрыскивание", "spraying"),
            ("Мои поля", "fields"),
        ]:
            button = Button(
                text=caption,
                font_size="22sp",
                size_hint_y=None,
                height=dp(70),
            )
            button.bind(
                on_release=lambda _button, target=destination:
                setattr(manager, "current", target)
            )
            layout.add_widget(button)

        layout.add_widget(Label(text="Полевые калькуляторы"))
        menu.add_widget(layout)
        manager.add_widget(menu)

        manager.add_widget(CalculatorScreen(
            name="seeding",
            title="Посев",
            fields=[
                ("density", "Желаемая густота, шт/м²", "450"),
                ("weight", "Масса 1000 семян, г", "40"),
                ("germination", "Всхожесть, %", "95"),
            ],
            calculator=seeding_result,
        ))

        manager.add_widget(FieldSprayingScreen(
            name="spraying",
            title="Опрыскивание",
            fields=[
                ("area", "Площадь обработки, га", "86.4"),
                ("product_rate", "Норма препарата, л/га", "0.5"),
                ("solution_rate", "Норма рабочего раствора, л/га", "200"),
                ("tank", "Объём бака, л", "3000"),
            ],
            calculator=spraying_result,
        ))
        
        manager.add_widget(FieldsScreen(name="fields"))
        manager.add_widget(FieldCardScreen(name="field_card"))

        return manager


if __name__ == "__main__":
    AgroToolsApp().run()