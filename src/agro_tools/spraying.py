import math
from dataclasses import dataclass


def calculate_product_amount(
    area_ha: float,
    product_rate: float,
) -> float:
    """Количество препарата на всю площадь."""
    return area_ha * product_rate


def calculate_solution_amount(
    area_ha: float,
    solution_rate_l_ha: float,
) -> float:
    """Количество рабочего раствора на всю площадь, л."""
    return area_ha * solution_rate_l_ha


def calculate_area_per_tank(
    tank_volume_l: float,
    solution_rate_l_ha: float,
) -> float:
    """Площадь, обрабатываемая одним полным баком, га."""
    return tank_volume_l / solution_rate_l_ha


def calculate_product_per_tank(
    tank_volume_l: float,
    solution_rate_l_ha: float,
    product_rate: float,
) -> float:
    """Количество препарата на один полный бак."""
    area_per_tank = calculate_area_per_tank(
        tank_volume_l=tank_volume_l,
        solution_rate_l_ha=solution_rate_l_ha,
    )

    return area_per_tank * product_rate


def calculate_tank_count(
    area_ha: float,
    tank_volume_l: float,
    solution_rate_l_ha: float,
) -> int:
    """Общее количество заправок."""
    area_per_tank = calculate_area_per_tank(
        tank_volume_l=tank_volume_l,
        solution_rate_l_ha=solution_rate_l_ha,
    )

    return math.ceil(area_ha / area_per_tank)


def calculate_full_tank_count(
    area_ha: float,
    tank_volume_l: float,
    solution_rate_l_ha: float,
) -> int:
    """Количество полностью используемых баков."""
    total_solution = calculate_solution_amount(
        area_ha=area_ha,
        solution_rate_l_ha=solution_rate_l_ha,
    )

    return int(total_solution // tank_volume_l)


def calculate_last_tank(
    area_ha: float,
    tank_volume_l: float,
    solution_rate_l_ha: float,
    product_rate: float,
) -> tuple[float, float, float]:
    """
    Рассчитать последнюю неполную заправку.

    Возвращает:
    - площадь последней заправки, га;
    - объём рабочего раствора, л;
    - количество препарата.
    """
    area_per_tank = calculate_area_per_tank(
        tank_volume_l=tank_volume_l,
        solution_rate_l_ha=solution_rate_l_ha,
    )

    full_tanks = calculate_full_tank_count(
        area_ha=area_ha,
        tank_volume_l=tank_volume_l,
        solution_rate_l_ha=solution_rate_l_ha,
    )

    remaining_area = area_ha - full_tanks * area_per_tank

    if math.isclose(remaining_area, 0.0, abs_tol=1e-9):
        return 0.0, 0.0, 0.0

    solution_amount = remaining_area * solution_rate_l_ha
    product_amount = remaining_area * product_rate

    return remaining_area, solution_amount, product_amount

# ============================================================
# Функции баковой смеси
# ============================================================


@dataclass
class SprayComponent:
    """Компонент баковой смеси."""

    name: str
    rate: float
    unit: str

    def amount_unit(self) -> str:
        """Единица измерения расчитанного количества компонента."""
        units = {
            "л/га": "л",
            "мл/га": "мл",
            "кг/га": "кг",
            "г/га": "г",
        }

        return units[self.unit]


def calculate_component_amount(
    area_ha: float,
    rate: float,
) -> float:
    """
    Рассчитать количество одного компонента на заданную площадь.

    Единица результата соответствует единице нормы:
    л/га  -> л
    мл/га -> мл
    кг/га -> кг
    г/га  -> г
    """
    return area_ha * rate


def calculate_component_per_tank(
    tank_volume_l: float,
    solution_rate_l_ha: float,
    component_rate: float,
) -> float:
    """
    Рассчитать количество компонента на один полный бак.

    Единица результата соответствует единице нормы компонента.
    """
    area_per_tank = calculate_area_per_tank(
        tank_volume_l=tank_volume_l,
        solution_rate_l_ha=solution_rate_l_ha,
    )

    return area_per_tank * component_rate


def calculate_component_for_last_tank(
    remaining_area_ha: float,
    component_rate: float,
) -> float:
    """
    Рассчитать количество компонента для последней
    неполной заправки.
    """
    return remaining_area_ha * component_rate


def convert_component_amount(
    amount: float,
    unit: str,
) -> tuple[float, str]:
    """
    Преобразовать большое количество мл в л,
    а большое количество г в кг.

    Например:
    2500 мл -> 2.5 л
    1800 г  -> 1.8 кг

    Для остальных единиц значение не изменяется.
    """
    unit = unit.lower().strip()

    if unit == "мл" and amount >= 1000:
        return amount / 1000, "л"

    if unit == "г" and amount >= 1000:
        return amount / 1000, "кг"

    return amount, unit


def calculate_remaining_area(
    area_ha: float,
    tank_volume_l: float,
    solution_rate_l_ha: float,
) -> float:
    """Площадь для последней неполной заправки, га."""
    area_per_tank = calculate_area_per_tank(
        tank_volume_l=tank_volume_l,
        solution_rate_l_ha=solution_rate_l_ha,
    )

    full_tanks = calculate_full_tank_count(
        area_ha=area_ha,
        tank_volume_l=tank_volume_l,
        solution_rate_l_ha=solution_rate_l_ha,
    )

    remaining_area = area_ha - full_tanks * area_per_tank

    if math.isclose(remaining_area, 0.0, abs_tol=1e-9):
        return 0.0

    return remaining_area


def calculate_tank_mix_for_area(
    components: list[SprayComponent],
    area_ha: float,
) -> list[tuple[SprayComponent, float]]:
    """
    Рассчитать количество всех компонентов
    баковой смеси для заданной площади.
    """
    result = []

    for component in components:
        amount = calculate_component_amount(
            area_ha=area_ha,
            rate=component.rate,
        )

        result.append((component, amount))

    return result


def calculate_tank_mix_for_full_tank(
    components: list[SprayComponent],
    tank_volume_l: float,
    solution_rate_l_ha: float,
) -> list[tuple[SprayComponent, float]]:
    """Рассчитать баковую смесь на один полный бак."""

    area_per_tank = calculate_area_per_tank(
        tank_volume_l=tank_volume_l,
        solution_rate_l_ha=solution_rate_l_ha,
    )

    return calculate_tank_mix_for_area(
        components=components,
        area_ha=area_per_tank,
    )


def calculate_tank_mix_for_last_tank(
    components: list[SprayComponent],
    area_ha: float,
    tank_volume_l: float,
    solution_rate_l_ha: float,
) -> list[tuple[SprayComponent, float]]:
    """Рассчитать баковую смесь для последней неполной заправки."""

    remaining_area = calculate_remaining_area(
        area_ha=area_ha,
        tank_volume_l=tank_volume_l,
        solution_rate_l_ha=solution_rate_l_ha,
    )

    if remaining_area == 0:
        return []

    return calculate_tank_mix_for_area(
        components=components,
        area_ha=remaining_area,
    )



'''
Функции модуля spraying.py:

ОБРАБОТКА ПОЛЯ
├── препарат на всю площадь <-----------+
├── рабочий раствор на всю площадь <----+
└── площадь на один бак <---------------+

ЗАПРАВКИ
├── количество заправок <---------------+
├── препарат на полный бак <------------+
├── количество полных баков <-----------+
└── последняя неполная заправка <-------+

БАКОВАЯ СМЕСЬ
├── несколько препаратов <||||||||||||||+
├── л/га <||||||||||||||||||||||||||||||+
├── мл/га <|||||||||||||||||||||||||||||+
├── кг/га <|||||||||||||||||||||||||||||+
└── г/га  <|||||||||||||||||||||||||||||+

КАЛИБРОВКА ОПРЫСКИВАТЕЛЯ
├── производительность, га/ч <----------+
├── требуемый расход одной форсунки <---+
└── фактическая норма рабочего раствора<+
'''