import math


def reorder_point(avg_daily_demand: float, lead_time_days: int) -> int:
    safety_stock = avg_daily_demand * 3
    return math.ceil((avg_daily_demand * lead_time_days) + safety_stock)


def reorder_needed(available_stock: int, reorder_point_value: int) -> bool:
    return available_stock <= reorder_point_value


def recommended_order_qty(
    available_stock: int,
    reorder_point_value: int,
    min_order_quantity: int,
) -> int:
    if not reorder_needed(available_stock, reorder_point_value):
        return 0
    return max(min_order_quantity, (reorder_point_value * 2) - available_stock)


def test_reorder_point_calculation_is_correct():
    # Average demand is 10 units/day, lead time is 5 days, safety stock is 3 days.
    assert reorder_point(avg_daily_demand=10, lead_time_days=5) == 80


def test_reorder_needed_flag_is_correct():
    assert reorder_needed(available_stock=50, reorder_point_value=80) is True
    assert reorder_needed(available_stock=120, reorder_point_value=80) is False


def test_recommended_order_qty_uses_minimum_order_quantity():
    result = recommended_order_qty(
        available_stock=70,
        reorder_point_value=80,
        min_order_quantity=100,
    )
    assert result == 100


def test_recommended_order_qty_uses_target_stock_when_larger():
    result = recommended_order_qty(
        available_stock=20,
        reorder_point_value=80,
        min_order_quantity=50,
    )
    assert result == 140


def test_recommended_order_qty_is_not_negative():
    result = recommended_order_qty(
        available_stock=200,
        reorder_point_value=80,
        min_order_quantity=50,
    )
    assert result >= 0
    assert result == 0
