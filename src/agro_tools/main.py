from agro_tools.seeding import calculate_seed_rate
from agro_tools.spraying import (
    SprayComponent,
    SprayUnit,
    calculate_application_rate,
    calculate_area_per_tank,
    calculate_field_capacity,
    calculate_last_tank,
    calculate_product_amount,
    calculate_product_per_tank,
    calculate_required_nozzle_flow,
    calculate_solution_amount,
    calculate_tank_count,
    calculate_tank_mix_for_area,
    calculate_tank_mix_for_full_tank,
    calculate_tank_mix_for_last_tank,
    convert_component_amount,
)


def seeding_menu():
    target_plants = float(input("Желаемая густота, шт/м²: "))
    thousand_seed_weight = float(input("Масса 1000 семян, г: "))
    germination = float(input("Всхожесть, %: "))

    seed_rate = calculate_seed_rate(
        target_plants=target_plants,
        thousand_seed_weight=thousand_seed_weight,
        germination=germination,
    )

    print(f"\nНорма высева: {seed_rate:.1f} кг/га")


def single_product_menu():
    print("\n--- Расчёт опрыскивания ---")

    area_ha = float(input("Площадь поля, га: "))
    product_rate = float(input("Норма препарата, л/га: "))
    solution_rate_l_ha = float(input("Норма рабочего раствора, л/га: "))
    tank_volume_l = float(input("Объём бака, л: "))

    product_amount = calculate_product_amount(
        area_ha=area_ha,
        product_rate=product_rate,
    )

    solution_amount = calculate_solution_amount(
        area_ha=area_ha,
        solution_rate_l_ha=solution_rate_l_ha,
    )

    area_per_tank = calculate_area_per_tank(
        tank_volume_l=tank_volume_l,
        solution_rate_l_ha=solution_rate_l_ha,
    )

    product_per_tank = calculate_product_per_tank(
        tank_volume_l=tank_volume_l,
        solution_rate_l_ha=solution_rate_l_ha,
        product_rate=product_rate,
    )

    tank_count = calculate_tank_count(
        area_ha=area_ha,
        tank_volume_l=tank_volume_l,
        solution_rate_l_ha=solution_rate_l_ha,
    )

    remaining_area, last_tank_volume, last_tank_product = calculate_last_tank(
        area_ha=area_ha,
        tank_volume_l=tank_volume_l,
        solution_rate_l_ha=solution_rate_l_ha,
        product_rate=product_rate,
    )

    print("\n--- Результат ---")
    print(f"Препарата на всё поле: {product_amount:.2f} л")
    print(f"Рабочего раствора: {solution_amount:.0f} л")
    print(f"Площадь на один полный бак: {area_per_tank:.2f} га")
    print(f"Препарата на полный бак: {product_per_tank:.2f} л")
    print(f"Количество заправок: {tank_count}")

    if remaining_area > 0:
        print("\nПоследняя неполная заправка:")
        print(f"Оставшаяся площадь: {remaining_area:.2f} га")
        print(f"Рабочего раствора: {last_tank_volume:.0f} л")
        print(f"Препарата: {last_tank_product:.2f} л")
    else:
        print("\nПоследняя заправка будет полной.")


def tank_mix_menu():
    print("\n--- Баковая смесь ---")

    area_ha = float(input("Площадь поля, га: "))
    solution_rate_l_ha = float(input("Норма рабочего раствора, л/га: "))
    tank_volume_l = float(input("Объём бака, л: "))

    component_count = int(input("Количество компонентов смеси: "))

    components = []

    units = {
        "1": SprayUnit.L_PER_HA,
        "2": SprayUnit.ML_PER_HA,
        "3": SprayUnit.KG_PER_HA,
        "4": SprayUnit.G_PER_HA,
    }

    for number in range(1, component_count + 1):
        print(f"\nКомпонент {number}")

        name = input("Название: ")
        rate = float(input("Норма: "))

        print("1. л/га")
        print("2. мл/га")
        print("3. кг/га")
        print("4. г/га")

        unit_choice = input("Единица нормы: ")
        unit = units[unit_choice]

        components.append(
            SprayComponent(
                name=name,
                rate=rate,
                unit=unit,
            )
        )

    total_mix = calculate_tank_mix_for_area(
        components=components,
        area_ha=area_ha,
    )

    full_tank_mix = calculate_tank_mix_for_full_tank(
        components=components,
        tank_volume_l=tank_volume_l,
        solution_rate_l_ha=solution_rate_l_ha,
    )

    last_tank_mix = calculate_tank_mix_for_last_tank(
        components=components,
        area_ha=area_ha,
        tank_volume_l=tank_volume_l,
        solution_rate_l_ha=solution_rate_l_ha,
    )

    print("\n--- На всё поле ---")

    for component, amount in total_mix:
        amount, unit = convert_component_amount(
            amount=amount,
            unit=component.unit.amount_unit,
        )

        print(f"{component.name}: {amount:.2f} {unit}")

    print("\n--- На один полный бак ---")

    for component, amount in full_tank_mix:
        amount, unit = convert_component_amount(
            amount=amount,
            unit=component.unit.amount_unit,
        )

        print(f"{component.name}: {amount:.2f} {unit}")

    if last_tank_mix:
        print("\n--- На последнюю неполную заправку ---")

        for component, amount in last_tank_mix:
            amount, unit = convert_component_amount(
                amount=amount,
                unit=component.unit.amount_unit,
            )

            print(f"{component.name}: {amount:.2f} {unit}")
    else:
        print("\nПоследней неполной заправки нет.")


def calibration_menu():
    print("\n--- Калибровка опрыскивателя ---")

    print("1. Производительность, га/ч")
    print("2. Требуемый расход форсунки")
    print("3. Фактическая норма рабочего раствора")

    choice = input("\nВыберите расчёт: ")

    if choice == "1":
        speed_kmh = float(input("Рабочая скорость, км/ч: "))
        boom_width_m = float(input("Ширина штанги, м: "))

        result = calculate_field_capacity(
            speed_kmh=speed_kmh,
            boom_width_m=boom_width_m,
        )

        print(f"\nПроизводительность: {result:.2f} га/ч")

    elif choice == "2":
        application_rate_l_ha = float(
            input("Требуемая норма рабочего раствора, л/га: ")
        )
        speed_kmh = float(input("Рабочая скорость, км/ч: "))
        nozzle_spacing_cm = float(input("Расстояние между форсунками, см: "))

        result = calculate_required_nozzle_flow(
            application_rate_l_ha=application_rate_l_ha,
            speed_kmh=speed_kmh,
            nozzle_spacing_cm=nozzle_spacing_cm,
        )

        print(f"\nТребуемый расход форсунки: {result:.3f} л/мин")

    elif choice == "3":
        nozzle_flow_l_min = float(input("Расход одной форсунки, л/мин: "))
        speed_kmh = float(input("Рабочая скорость, км/ч: "))
        nozzle_spacing_cm = float(input("Расстояние между форсунками, см: "))

        result = calculate_application_rate(
            nozzle_flow_l_min=nozzle_flow_l_min,
            speed_kmh=speed_kmh,
            nozzle_spacing_cm=nozzle_spacing_cm,
        )

        print(f"\nФактическая норма рабочего раствора: {result:.1f} л/га")

    else:
        print("Неизвестная команда")


def spraying_menu():
    print("\n=== Опрыскивание ===")
    print("1. Расчёт одного препарата")
    print("2. Расчёт баковой смеси")
    print("3. Калибровка опрыскивателя")
    print("0. Назад")

    choice = input("\nВыберите действие: ")

    if choice == "1":
        single_product_menu()
    elif choice == "2":
        tank_mix_menu()
    elif choice == "3":
        calibration_menu()
    elif choice == "0":
        return
    else:
        print("Неизвестная команда")


def main():
    print("=== Agro Tools ===")
    print("1. Расчёт нормы высева")
    print("2. Опрыскивание")
    print("0. Выход")

    choice = input("\nВыберите действие: ")

    if choice == "1":
        seeding_menu()
    elif choice == "2":
        spraying_menu()
    elif choice == "0":
        print("Выход")
    else:
        print("Неизвестная команда")


if __name__ == "__main__":
    main()
