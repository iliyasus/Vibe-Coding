import json
import sqlite3
from decimal import Decimal
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from order_processor import Order, OrderItem, save_order, validate_order


@pytest.fixture
def valid_order() -> dict[str, object]:
    return {
        "order_id": "order-123",
        "customer_email": "buyer@example.com",
        "amount": "49.99",
        "status": "pending",
        "items": [{"sku": "widget-1", "quantity": 2}],
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("order_id", ""),
        ("order_id", "   "),
        ("customer_email", "buyerexample.com"),
        ("customer_email", "@example.com"),
        ("customer_email", "buyer@"),
        ("amount", "0"),
        ("amount", "-0.01"),
        ("amount", "NaN"),
        ("amount", "Infinity"),
        ("status", "unknown"),
        ("items", []),
        ("unexpected", "not allowed"),
    ],
)
def test_validate_order_rejects_invalid_fields(
    valid_order: dict[str, object], field: str, value: object
) -> None:
    valid_order[field] = value

    with pytest.raises(ValidationError):
        validate_order(valid_order)


@pytest.mark.parametrize(
    "item",
    [
        "not-a-model",
        {},
        {"sku": "   ", "quantity": 1},
        {"sku": "widget-1", "quantity": 0},
        {"sku": "widget-1", "quantity": -1},
        {"sku": "widget-1", "quantity": True},
        {"sku": "widget-1", "quantity": "2"},
    ],
)
def test_validate_order_rejects_invalid_items(
    valid_order: dict[str, object], item: object
) -> None:
    valid_order["items"] = [item]

    with pytest.raises(ValidationError):
        validate_order(valid_order)


def test_validate_order_accepts_valid_order(valid_order: dict[str, object]) -> None:
    validate_order(valid_order)


def test_order_accepts_orm_style_attributes() -> None:
    record = SimpleNamespace(
        order_id="order-123",
        customer_email="buyer@example.com",
        amount=Decimal("49.99"),
        status="paid",
        items=[SimpleNamespace(sku="widget-1", quantity=2)],
    )

    order = Order.model_validate(record)

    assert order.status == "paid"
    assert order.items == [OrderItem(sku="widget-1", quantity=2)]


def test_order_serializes_to_dict_and_json(valid_order: dict[str, object]) -> None:
    order = Order.model_validate(valid_order)

    assert order.model_dump()["amount"] == Decimal("49.99")
    assert json.loads(order.model_dump_json())["amount"] == "49.99"


def test_save_order_persists_valid_order(valid_order: dict[str, object]) -> None:
    with sqlite3.connect(":memory:") as connection:
        save_order(connection, valid_order)
        row = connection.execute(
            "SELECT order_id, payload FROM orders"
        ).fetchone()

    assert row is not None
    assert row[0] == "order-123"
    assert json.loads(row[1]) == Order.model_validate(valid_order).model_dump(mode="json")


def test_save_order_does_not_insert_invalid_order(valid_order: dict[str, object]) -> None:
    valid_order["amount"] = "0"

    with sqlite3.connect(":memory:") as connection:
        with pytest.raises(ValidationError):
            save_order(connection, valid_order)
        table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'orders'"
        ).fetchone()

    assert table is None


def test_save_order_surfaces_duplicate_order_id(valid_order: dict[str, object]) -> None:
    with sqlite3.connect(":memory:") as connection:
        save_order(connection, valid_order)

        with pytest.raises(sqlite3.IntegrityError):
            save_order(connection, valid_order)
