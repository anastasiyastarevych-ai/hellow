import pytest
from order_manager import Order


@pytest.fixture
def items():
    return [
        {"name": "book", "price": 100, "quantity": 2},
        {"name": "pen", "price": 10, "quantity": 5},
        {"name": "bag", "price": 50, "quantity": 1},
    ]


@pytest.fixture
def order(items):
    return Order(1, items)


def test_total_multiple_items(order):
    assert order.total() == 300


def test_total_single_item():
    assert Order(2, [{"price": 15, "quantity": 3}]).total() == 45


def test_total_empty_items():
    assert Order(3, []).total() == 0


def test_total_zero_quantity():
    assert Order(4, [{"price": 99, "quantity": 0}]).total() == 0


def test_total_float_prices():
    order = Order(5, [{"price": 9.99, "quantity": 3}])
    assert order.total() == pytest.approx(29.97)


def test_most_expensive(order):
    assert order.most_expensive()["name"] == "book"


def test_most_expensive_single_item():
    item = {"price": 5, "quantity": 1}
    assert Order(6, [item]).most_expensive() is item


def test_most_expensive_equal_prices_returns_first():
    a = {"name": "a", "price": 10, "quantity": 1}
    b = {"name": "b", "price": 10, "quantity": 1}
    assert Order(7, [a, b]).most_expensive() is a


def test_most_expensive_empty_items():
    with pytest.raises(ValueError):
        Order(8, []).most_expensive()


def test_apply_discount_changes_all_prices(order):
    order.apply_discount(10)
    prices = [item["price"] for item in order.items]
    assert prices == pytest.approx([90, 9, 45])


def test_apply_discount_total_after(order):
    order.apply_discount(50)
    assert order.total() == pytest.approx(150)


def test_apply_discount_zero_keeps_prices(order):
    order.apply_discount(0)
    assert [item["price"] for item in order.items] == [100, 10, 50]


def test_apply_discount_hundred_makes_prices_zero(order):
    order.apply_discount(100)
    assert all(item["price"] == 0 for item in order.items)
    assert order.total() == 0


def test_apply_discount_float_percent(order):
    order.apply_discount(12.5)
    assert order.items[0]["price"] == pytest.approx(87.5)


def test_apply_discount_twice(order):
    order.apply_discount(10)
    order.apply_discount(10)
    prices = [item["price"] for item in order.items]
    assert prices == pytest.approx([81, 8.1, 40.5])


def test_apply_discount_empty_items():
    order = Order(9, [])
    order.apply_discount(20)
    assert order.items == []


@pytest.mark.parametrize("percent", [-1, -0.01, 100.01, 101, 1000])
def test_apply_discount_invalid_raises(order, percent):
    with pytest.raises(ValueError):
        order.apply_discount(percent)


@pytest.mark.parametrize("percent", [-1, 101])
def test_apply_discount_invalid_keeps_prices(order, percent):
    with pytest.raises(ValueError):
        order.apply_discount(percent)
    assert [item["price"] for item in order.items] == [100, 10, 50]


def test_apply_discount_invalid_message(order):
    with pytest.raises(ValueError, match="Invalid discount"):
        order.apply_discount(150)


def test_apply_discount_wrong_type_raises(order):
    with pytest.raises(TypeError):
        order.apply_discount("10")


def test_repr(order):
    assert repr(order) == "<Order 1: 3 items>"


def test_repr_empty_items():
    assert repr(Order(5, [])) == "<Order 5: 0 items>"


def test_repr_string_id():
    assert repr(Order("A1", [{"price": 1, "quantity": 1}])) == "<Order A1: 1 items>"
    