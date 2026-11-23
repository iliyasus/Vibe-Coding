"""Pydantic request models for order operations."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RefundRequest(BaseModel):
    """A validated request to refund an order."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    order_id: str = Field(min_length=1)
    reason: str = Field(min_length=10)
    refund_amount: Decimal = Field(gt=0)

    @field_validator("refund_amount")
    @classmethod
    def refund_amount_must_be_finite(cls, value: Decimal) -> Decimal:
        if not value.is_finite():
            raise ValueError("refund_amount must be finite.")
        return value
