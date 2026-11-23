from decimal import Decimal

import pytest
from pydantic import ValidationError

from models import RefundRequest


def test_refund_request_accepts_valid_data() -> None:
    request = RefundRequest(
        order_id="order-123",
        reason="The product arrived damaged.",
        refund_amount=Decimal("49.99"),
    )

    assert request.order_id == "order-123"
    assert request.reason == "The product arrived damaged."
    assert request.refund_amount == Decimal("49.99")


def test_refund_request_rejects_short_reason() -> None:
    with pytest.raises(ValidationError):
        RefundRequest(
            order_id="order-123",
            reason="Damaged",
            refund_amount=Decimal("49.99"),
        )


@pytest.mark.parametrize("refund_amount", ["0", "-0.01", "NaN", "Infinity"])
def test_refund_request_rejects_non_positive_or_non_finite_amount(
    refund_amount: str,
) -> None:
    with pytest.raises(ValidationError):
        RefundRequest(
            order_id="order-123",
            reason="The product arrived damaged.",
            refund_amount=refund_amount,
        )
