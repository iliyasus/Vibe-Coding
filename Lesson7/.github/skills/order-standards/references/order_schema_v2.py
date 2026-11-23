"""Pydantic models and SQLite persistence for customer orders."""

import sqlite3
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, ValidationError, field_validator

OrderValidationError = ValidationError


class OrderItem(BaseModel):
    """A validated item in an order."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True, extra="forbid")

    sku: str = Field(min_length=1)
    quantity: int = Field(gt=0, strict=True)


class Order(BaseModel):
    """Validated order data."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True, extra="forbid")

    order_id: str = Field(min_length=1)
    customer_email: EmailStr
    amount: Decimal = Field(gt=0)
    status: Literal["pending", "paid", "shipped", "cancelled"] = "pending"
    items: list[OrderItem] = Field(min_length=1)

    @field_validator("amount")
    @classmethod
    def amount_must_be_finite(cls, value: Decimal) -> Decimal:
        if not value.is_finite():
            raise ValueError("amount must be finite.")
        return value


def validate_order(order: object) -> None:
    """Validate an order mapping or ORM-style object."""
    Order.model_validate(order)


def save_order(connection: sqlite3.Connection, order: object) -> None:
    """Validate and save an order as JSON in the SQLite database."""
    validated_order = Order.model_validate(order)
    with connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "INSERT INTO orders (order_id, payload) VALUES (?, ?)",
            (validated_order.order_id, validated_order.model_dump_json()),
        )
