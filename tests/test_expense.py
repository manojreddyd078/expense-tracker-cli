from datetime import date
from decimal import Decimal

import pytest

from expense_tracker.expense import Expense
from expense_tracker.utils import parse_amount_to_cents, parse_iso_date


def test_valid_expense_record_and_precise_cents():
    expense = Expense(Decimal("12.34"), " food ", "Lunch", "2026-11-18")

    assert expense.amount == Decimal("12.34")
    assert expense.amount_cents == 1234
    assert expense.category == "food"
    assert expense.date == date(2026, 11, 18)
    assert expense.date_iso == "2026-11-18"


@pytest.mark.parametrize("amount", [Decimal("0"), Decimal("-1.00")])
def test_zero_and_negative_amounts_are_rejected(amount):
    with pytest.raises(ValueError):
        parse_amount_to_cents(amount)


def test_malformed_iso_date_is_rejected():
    with pytest.raises(ValueError):
        parse_iso_date("18/11/2026")


def test_empty_category_is_rejected():
    with pytest.raises(ValueError):
        Expense("1.00", "   ", "Description", "2026-11-18")


def test_amount_with_more_than_two_decimal_places_is_rejected():
    with pytest.raises(ValueError):
        parse_amount_to_cents("1.001")
