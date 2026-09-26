from agro_tools.seeding import calculate_seed_rate
from agro_tools.spraying import (
    calculate_area_per_tank,
    calculate_last_tank,
    calculate_product_amount,
    calculate_product_per_tank,
    calculate_solution_amount,
    calculate_tank_count,
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


def spraying_menu():
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


def main():
    print("=== Agro Tools ===")
    print("1. Расчёт нормы высева")
    print("2. Расчёт опрыскивания")
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
