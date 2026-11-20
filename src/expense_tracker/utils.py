"""Reusable parsing and validation helpers."""

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


CENT = Decimal("0.01")


def format_cents(cents: int) -> str:
    """Format integer cents as a presentation value such as ``$12.34``."""
    return f"${Decimal(cents) / 100:,.2f}"


def parse_amount_to_cents(value: Decimal | str | int | float) -> int:
    """Validate a positive amount and convert it exactly to integer cents."""
    if isinstance(value, bool):
        raise ValueError("amount must be a positive monetary value")
    try:
        amount = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("amount must be a valid monetary value") from None
    if not amount.is_finite() or amount <= 0:
        raise ValueError("amount must be greater than zero")
    if amount != amount.quantize(CENT):
        raise ValueError("amount must have no more than two decimal places")
    return int((amount * 100).to_integral_exact(rounding=ROUND_HALF_UP))


def parse_iso_date(value: date | str) -> date:
    """Parse an ISO-8601 calendar date."""
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value.strip():
        raise ValueError("date must be an ISO date (YYYY-MM-DD)")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError("date must be an ISO date (YYYY-MM-DD)") from None


def validate_category(value: str) -> str:
    """Return a nonempty, trimmed category."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("category must not be empty")
    return value.strip()
