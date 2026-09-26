import pytest

from agro_tools.spraying import (
    calculate_application_rate,
    calculate_area_per_tank,
    calculate_field_capacity,
    calculate_full_tank_count,
    calculate_last_tank,
    calculate_product_amount,
    calculate_product_per_tank,
    calculate_required_nozzle_flow,
    calculate_solution_amount,
    calculate_tank_count,
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
