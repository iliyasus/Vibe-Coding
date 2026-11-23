"""Validated order processing implementation."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class LegacyOrderItem(BaseModel):
    """A validated item in a legacy order."""

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        extra="forbid",
    )

    sku: str = Field(min_length=1)
    quantity: int = Field(gt=0, strict=True)


class LegacyOrder(BaseModel):
    """Validated legacy order data."""

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        extra="forbid",
    )

    order_id: str = Field(min_length=1)
    customer_email: str = Field(min_length=3)
    amount: Decimal = Field(gt=0)
    status: Literal["pending", "paid", "shipped", "cancelled"] = "pending"
    items: list[LegacyOrderItem] = Field(min_length=1)

    @field_validator("customer_email")
    @classmethod
    def customer_email_must_be_valid(cls, value: str) -> str:
        if "@" not in value:
            raise ValueError("customer_email is invalid.")
        return value

    @field_validator("amount")
    @classmethod
    def amount_must_be_finite(cls, value: Decimal) -> Decimal:
        if not value.is_finite():
            raise ValueError("amount must be finite.")
        return value


def process_order(order: object) -> dict[str, object]:
    """Validate an order and return a processing result."""
    try:
        validated = LegacyOrder.model_validate(order)
    except ValidationError as error:
        return {"ok": False, "error": error.errors()[0]["msg"]}
    return {"ok": True, "order_id": validated.order_id}
