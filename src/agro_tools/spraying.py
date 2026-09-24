import math


def calculate_product_amount(
    area_ha: float,
    product_rate_l_ha: float,
) -> float:
    """Количество препарата на всю площадь, л."""
    return area_ha * product_rate_l_ha


def calculate_water_amount(
    area_ha: float,
    water_rate_l_ha: float,
) -> float:
    """Количество рабочего раствора на всю площадь, л."""
    return area_ha * water_rate_l_ha


def calculate_area_per_tank(
    tank_volume_l: float,
    water_rate_l_ha: float,
) -> float:
    """Площадь, обрабатываемая одним полным баком, га."""
    return tank_volume_l / water_rate_l_ha


def calculate_product_per_tank(
    tank_volume_l: float,
    water_rate_l_ha: float,
    product_rate_l_ha: float,
) -> float:
    """Количество препарата на один полный бак, л."""
    area_per_tank = tank_volume_l / water_rate_l_ha
    return area_per_tank * product_rate_l_ha


def calculate_tank_count(
    area_ha: float,
    tank_volume_l: float,
    water_rate_l_ha: float,
) -> int:
    """Количество заправок для обработки всей площади."""
    area_per_tank = tank_volume_l / water_rate_l_ha
    return math.ceil(area_ha / area_per_tank)


def calculate_last_tank(
    area_ha: float,
    tank_volume_l: float,
    water_rate_l_ha: float,
    product_rate_l_ha: float,
) -> tuple[float, float, float]:
    """Рассчитать последнюю неполную заправку.

    Возвращает:
    - оставшуюся площадь, га
    - объём рабочего раствора, л
    - количество препарата, л
    """

    area_per_tank = tank_volume_l / water_rate_l_ha

    full_tanks = int(area_ha // area_per_tank)
    remaining_area = area_ha - full_tanks * area_per_tank

    # Если площадь делится ровно на полные баки
    if remaining_area == 0:
        return 0.0, 0.0, 0.0

    last_tank_volume = remaining_area * water_rate_l_ha
    last_tank_product = remaining_area * product_rate_l_ha

    return remaining_area, last_tank_volume, last_tank_product