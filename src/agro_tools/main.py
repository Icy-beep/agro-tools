from math import isfinite

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput


def calculate_seed_rate(target_plants, thousand_seed_weight, germination):
    return target_plants * thousand_seed_weight / germination


class AgroToolsApp(App):
    def build(self):
        self.title = "Agro Tools"

        layout = BoxLayout(
            orientation="vertical",
            padding=dp(20),
            spacing=dp(12),
        )

        layout.add_widget(
            Label(
                text="Agro Tools — Посев",
                font_size="24sp",
                size_hint_y=None,
                height=dp(60),
            )
        )

        self.inputs = {}

        fields = [
            ("density", "Желаемая густота, шт/м²", "450"),
            ("weight", "Масса 1000 семян, г", "40"),
            ("germination", "Всхожесть, %", "95"),
        ]

        for key, title, default in fields:
            layout.add_widget(
                Label(
                    text=title,
                    size_hint_y=None,
                    height=dp(28),
                )
            )

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

        button = Button(
            text="Рассчитать",
            size_hint_y=None,
            height=dp(56),
        )
        button.bind(on_release=self.calculate)
        layout.add_widget(button)

        self.result = Label(
            text="Введите данные и нажмите «Рассчитать»",
            font_size="18sp",
            halign="center",
            valign="middle",
        )
        self.result.bind(
            size=lambda widget, size: setattr(widget, "text_size", size)
        )
        layout.add_widget(self.result)

        return layout

    def calculate(self, _button):
        try:
            values = {
                key: float(entry.text.strip().replace(",", "."))
                for key, entry in self.inputs.items()
            }

            if not all(isfinite(value) for value in values.values()):
                raise ValueError("Введите конечные числовые значения.")

            if values["density"] <= 0 or values["weight"] <= 0:
                raise ValueError("Густота и масса семян должны быть больше нуля.")

            if not 0 < values["germination"] <= 100:
                raise ValueError("Всхожесть должна быть больше 0 и не выше 100%.")

            rate = calculate_seed_rate(
                values["density"],
                values["weight"],
                values["germination"],
            )

            self.result.text = f"Норма высева: {rate:.1f} кг/га"

        except ValueError as error:
            self.result.text = (
                str(error)
                if not str(error).startswith("could not convert")
                else "Проверьте ввод: нужны числа."
            )


if __name__ == "__main__":
    AgroToolsApp().run()