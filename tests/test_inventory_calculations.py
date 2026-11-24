import pytest


def available_stock(current_stock: int, reserved_stock: int) -> int:
    return current_stock - reserved_stock


def average_daily_demand(quantity_sold: int, days: int) -> float:
    return quantity_sold / days


def stock_coverage_days(stock_available: int, avg_daily_demand: float) -> float | None:
    if avg_daily_demand == 0:
        return None
    return stock_available / avg_daily_demand


def test_available_stock_calculation_is_correct():
    assert available_stock(current_stock=100, reserved_stock=15) == 85


def test_average_daily_demand_calculation_is_correct():
    assert average_daily_demand(quantity_sold=70, days=7) == pytest.approx(10)
    assert average_daily_demand(quantity_sold=140, days=14) == pytest.approx(10)
    assert average_daily_demand(quantity_sold=300, days=30) == pytest.approx(10)


def test_stock_coverage_days_calculation_is_correct():
    result = stock_coverage_days(stock_available=80, avg_daily_demand=10)
    assert result == pytest.approx(8)


def test_stock_coverage_days_handles_zero_demand():
    assert stock_coverage_days(stock_available=80, avg_daily_demand=0) is None
