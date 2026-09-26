import pytest

from agro_tools.spraying import (
    SprayComponent,
    SprayUnit,
    calculate_application_rate,
    calculate_area_per_tank,
    calculate_component_amount,
    calculate_component_for_last_tank,
    calculate_component_per_tank,
    calculate_field_capacity,
    calculate_full_tank_count,
    calculate_last_tank,
    calculate_product_amount,
    calculate_product_per_tank,
    calculate_remaining_area,
    calculate_required_nozzle_flow,
    calculate_solution_amount,
    calculate_tank_count,
    calculate_tank_mix_for_area,
    calculate_tank_mix_for_full_tank,
    calculate_tank_mix_for_last_tank,
    convert_component_amount,
)


def test_calculate_product_amount():
    result = calculate_product_amount(
        area_ha=10,
        product_rate=0.8,
    )

    assert result == pytest.approx(8.0)


def test_calculate_solution_amount():
    result = calculate_solution_amount(
        area_ha=53,
        solution_rate_l_ha=200,
    )

    assert result == pytest.approx(10600)


def test_calculate_area_per_tank():
    result = calculate_area_per_tank(
        tank_volume_l=3000,
        solution_rate_l_ha=200,
    )

    assert result == pytest.approx(15)


def test_calculate_product_per_tank():
    result = calculate_product_per_tank(
        tank_volume_l=3000,
        solution_rate_l_ha=200,
        product_rate=0.8,
    )

    assert result == pytest.approx(12)


def test_calculate_tank_count():
    result = calculate_tank_count(
        area_ha=53,
        tank_volume_l=3000,
        solution_rate_l_ha=200,
    )

    assert result == 4


def test_calculate_full_tank_count():
    result = calculate_full_tank_count(
        area_ha=53,
        tank_volume_l=3000,
        solution_rate_l_ha=200,
    )

    assert result == 3


def test_calculate_last_tank():
    remaining_area, solution_amount, product_amount = calculate_last_tank(
        area_ha=53,
        tank_volume_l=3000,
        solution_rate_l_ha=200,
        product_rate=0.8,
    )

    assert remaining_area == pytest.approx(8)
    assert solution_amount == pytest.approx(1600)
    assert product_amount == pytest.approx(6.4)


def test_calculate_last_tank_when_field_uses_full_tanks():
    remaining_area, solution_amount, product_amount = calculate_last_tank(
        area_ha=30,
        tank_volume_l=3000,
        solution_rate_l_ha=200,
        product_rate=0.8,
    )

    assert remaining_area == pytest.approx(0)
    assert solution_amount == pytest.approx(0)
    assert product_amount == pytest.approx(0)


def test_calculate_field_capacity():
    result = calculate_field_capacity(
        speed_kmh=10,
        boom_width_m=24,
    )

    assert result == pytest.approx(24)


def test_calculate_required_nozzle_flow():
    result = calculate_required_nozzle_flow(
        application_rate_l_ha=200,
        speed_kmh=10,
        nozzle_spacing_cm=50,
    )

    assert result == pytest.approx(1.6666667)


def test_calculate_application_rate():
    result = calculate_application_rate(
        nozzle_flow_l_min=1.6666667,
        speed_kmh=10,
        nozzle_spacing_cm=50,
    )

    assert result == pytest.approx(200, rel=1e-6)


def test_spray_component():
    component = SprayComponent(
        name="Гербицид",
        rate=0.8,
        unit=SprayUnit.L_PER_HA,
    )

    assert component.name == "Гербицид"
    assert component.rate == pytest.approx(0.8)
    assert component.unit == SprayUnit.L_PER_HA
    assert component.unit.rate_unit == "л/га"
    assert component.unit.amount_unit == "л"


def test_calculate_component_amount():
    result = calculate_component_amount(
        area_ha=10,
        rate=0.8,
    )

    assert result == pytest.approx(8)


def test_calculate_component_per_tank():
    result = calculate_component_per_tank(
        tank_volume_l=3000,
        solution_rate_l_ha=200,
        component_rate=0.8,
    )

    assert result == pytest.approx(12)


def test_calculate_component_for_last_tank():
    result = calculate_component_for_last_tank(
        remaining_area_ha=8,
        component_rate=0.8,
    )

    assert result == pytest.approx(6.4)


def test_convert_milliliters_to_liters():
    amount, unit = convert_component_amount(
        amount=2250,
        unit="мл",
    )

    assert amount == pytest.approx(2.25)
    assert unit == "л"


def test_convert_grams_to_kilograms():
    amount, unit = convert_component_amount(
        amount=1800,
        unit="г",
    )

    assert amount == pytest.approx(1.8)
    assert unit == "кг"


def test_convert_small_amount_is_not_changed():
    amount, unit = convert_component_amount(
        amount=500,
        unit="мл",
    )

    assert amount == pytest.approx(500)
    assert unit == "мл"


def test_calculate_remaining_area():
    result = calculate_remaining_area(
        area_ha=53,
        tank_volume_l=3000,
        solution_rate_l_ha=200,
    )

    assert result == pytest.approx(8)


def test_calculate_remaining_area_when_no_remainder():
    result = calculate_remaining_area(
        area_ha=30,
        tank_volume_l=3000,
        solution_rate_l_ha=200,
    )

    assert result == pytest.approx(0)


def test_calculate_tank_mix_for_area():
    components = [
        SprayComponent("Гербицид", 0.8, SprayUnit.L_PER_HA),
        SprayComponent("Инсектицид", 150, SprayUnit.ML_PER_HA),
        SprayComponent("Микроудобрение", 25, SprayUnit.G_PER_HA),
    ]

    result = calculate_tank_mix_for_area(
        components=components,
        area_ha=10,
    )

    assert result[0][1] == pytest.approx(8)
    assert result[1][1] == pytest.approx(1500)
    assert result[2][1] == pytest.approx(250)


def test_calculate_tank_mix_for_full_tank():
    components = [
        SprayComponent("Гербицид", 0.8, SprayUnit.L_PER_HA),
        SprayComponent("Инсектицид", 150, SprayUnit.ML_PER_HA),
        SprayComponent("Микроудобрение", 25, SprayUnit.G_PER_HA),
    ]

    result = calculate_tank_mix_for_full_tank(
        components=components,
        tank_volume_l=3000,
        solution_rate_l_ha=200,
    )

    assert result[0][1] == pytest.approx(12)
    assert result[1][1] == pytest.approx(2250)
    assert result[2][1] == pytest.approx(375)


def test_calculate_tank_mix_for_last_tank():
    components = [
        SprayComponent("Гербицид", 0.8, SprayUnit.L_PER_HA),
        SprayComponent("Инсектицид", 150, SprayUnit.ML_PER_HA),
        SprayComponent("Микроудобрение", 25, SprayUnit.G_PER_HA),
    ]

    result = calculate_tank_mix_for_last_tank(
        components=components,
        area_ha=53,
        tank_volume_l=3000,
        solution_rate_l_ha=200,
    )

    assert result[0][1] == pytest.approx(6.4)
    assert result[1][1] == pytest.approx(1200)
    assert result[2][1] == pytest.approx(200)


def test_calculate_tank_mix_for_last_tank_when_no_remainder():
    components = [
        SprayComponent("Гербицид", 0.8, SprayUnit.L_PER_HA),
    ]

    result = calculate_tank_mix_for_last_tank(
        components=components,
        area_ha=30,
        tank_volume_l=3000,
        solution_rate_l_ha=200,
    )

    assert result == []
