def calculate_seed_rate(
    target_plants: float,
    thousand_seed_weight: float,
    germination: float,
) -> float:
    """Рассчитать норму высева в кг/га."""

    seeds_needed = target_plants / (germination / 100)

    seed_rate = seeds_needed * thousand_seed_weight / 100

    return seed_rate



"""
ПОСЕВ
├── расчёт нормы высева, кг/га
├── семян/м²
├── млн семян/га
├── масса 1000 семян
├── всхожесть
├── чистота семян
├── полевая всхожесть / ожидаемая сохранность
├── потребность семян на всё поле
└── фактическая густота после всходов
"""