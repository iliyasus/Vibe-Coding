from decimal import Decimal

import pytest

from legacy_processor import LegacyOrder, LegacyOrderItem, process_order


@pytest.fixture
def valid_order() -> dict[str, object]:
    return {
        "order_id": "order-123",
        "customer_email": "buyer@example.com",
        "amount": "49.99",
        "status": "pending",
        "items": [{"sku": "widget-1", "quantity": 2}],
    }


def test_process_order_accepts_valid_data(valid_order: dict[str, object]) -> None:
    assert process_order(valid_order) == {"ok": True, "order_id": "order-123"}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("order_id", ""),
        ("customer_email", "invalid"),
        ("amount", "0"),
        ("amount", "-1"),
        ("amount", "NaN"),
        ("status", "unknown"),
        ("items", []),
        ("unexpected", "not allowed"),
    ],
)
def test_process_order_rejects_invalid_fields(
    valid_order: dict[str, object],
    field: str,
    value: object,
) -> None:
    valid_order[field] = value

    assert process_order(valid_order)["ok"] is False


def test_legacy_order_accepts_orm_style_attributes() -> None:
    class OrderRecord:
        order_id = "order-123"
        customer_email = "buyer@example.com"
        amount = Decimal("49.99")
        status = "paid"
        items = [LegacyOrderItem(sku="widget-1", quantity=2)]

    order = LegacyOrder.model_validate(OrderRecord())

    assert order.status == "paid"
