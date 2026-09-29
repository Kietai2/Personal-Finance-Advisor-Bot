from datetime import date
import pytest
from app.services.finance_service import FinanceService
from app.models import Income, Expense

def test_add_income(app):
    income = FinanceService.add_income("Salary", 35000.0, date(2026, 9, 1), "September salary")
    assert income.id is not None
    assert income.source == "Salary"
    assert income.amount == 35000.0
    assert income.date == date(2026, 9, 1)

def test_add_income_validation_invalid_amount(app):
    with pytest.raises(ValueError, match="greater than zero"):
        FinanceService.add_income("Salary", -500.0)

    with pytest.raises(ValueError, match="greater than zero"):
        FinanceService.add_income("Salary", 0)

def test_add_income_validation_empty_source(app):
    with pytest.raises(ValueError, match="source is required"):
        FinanceService.add_income("", 5000.0)

def test_update_and_delete_income(app):
    inc = FinanceService.add_income("Freelance", 8000.0, date(2026, 9, 5))
    updated = FinanceService.update_income(inc.id, amount=9500.0, notes="Bonus added")
    assert updated.amount == 9500.0
    assert updated.notes == "Bonus added"

    assert FinanceService.delete_income(inc.id) is True
    from app import db
    assert db.session.get(Income, inc.id) is None

def test_add_expense(app):
    exp = FinanceService.add_expense("Food", 4200.0, date(2026, 9, 4), "Supermarket groceries")
    assert exp.id is not None
    assert exp.category == "Food"
    assert exp.amount == 4200.0

def test_add_expense_validation(app):
    with pytest.raises(ValueError, match="greater than zero"):
        FinanceService.add_expense("Rent", -1000.0)

    with pytest.raises(ValueError, match="category is required"):
        FinanceService.add_expense("", 2000.0)

def test_update_and_delete_expense(app):
    exp = FinanceService.add_expense("Transport", 1500.0, date(2026, 9, 10))
    updated = FinanceService.update_expense(exp.id, amount=1750.0, description="Cab charges included")
    assert updated.amount == 1750.0
    assert updated.description == "Cab charges included"

    assert FinanceService.delete_expense(exp.id) is True
    from app import db
    assert db.session.get(Expense, exp.id) is None

def test_calculating_total_income_expenses_and_savings(app):
    # Add multiple incomes
    FinanceService.add_income("Salary", 35000.0, date(2026, 9, 1))
    FinanceService.add_income("Freelance", 5000.0, date(2026, 9, 15))
    
    # Add multiple expenses
    FinanceService.add_expense("Rent", 10000.0, date(2026, 9, 2))
    FinanceService.add_expense("Food", 6000.0, date(2026, 9, 4))
    FinanceService.add_expense("Utilities", 2000.0, date(2026, 9, 6))

    summary = FinanceService.get_monthly_summary(9, 2026)

    # Total income = 35000 + 5000 = 40000
    assert summary['total_income'] == 40000.0
    # Total expenses = 10000 + 6000 + 2000 = 18000
    assert summary['total_expenses'] == 18000.0
    # Savings = 40000 - 18000 = 22000
    assert summary['savings'] == 22000.0
    # Savings Rate = (22000 / 40000) * 100 = 55.0%
    assert summary['savings_rate'] == 55.0

def test_all_time_savings(app):
    FinanceService.add_income("Salary", 35000.0, date(2026, 8, 1))
    FinanceService.add_income("Salary", 35000.0, date(2026, 9, 1))
    FinanceService.add_expense("Rent", 10000.0, date(2026, 8, 2))
    FinanceService.add_expense("Rent", 10000.0, date(2026, 9, 2))

    all_time = FinanceService.get_all_time_savings()
    assert all_time == 50000.0
