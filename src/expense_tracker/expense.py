"""Expense domain model."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from expense_tracker.utils import parse_amount_to_cents, parse_iso_date, validate_category


@dataclass
class Expense:
    """A validated expense record, without persistence behavior."""

    amount: Decimal
    category: str
    description: str
    date: date

    def __post_init__(self) -> None:
        parse_amount_to_cents(self.amount)
        self.amount = Decimal(str(self.amount))
        self.category = validate_category(self.category)
        self.date = parse_iso_date(self.date)

    @property
    def amount_cents(self) -> int:
        """Return the precise integer-cent representation of the amount."""
        return parse_amount_to_cents(self.amount)

    @property
    def date_iso(self) -> str:
        """Return the date in ISO ``YYYY-MM-DD`` form."""
        return self.date.isoformat()
