from datetime import date
import pytest
from app.services.budget_service import BudgetService
from app.services.finance_service import FinanceService
from app.models import Budget

def test_set_and_update_budget(app):
    b1 = BudgetService.set_or_update_budget("Food", 5000.0, 9, 2026)
    assert b1.id is not None
    assert b1.amount == 5000.0

    # Updating the same month/year budget for Food
    b2 = BudgetService.set_or_update_budget("Food", 6000.0, 9, 2026)
    assert b2.id == b1.id
    assert b2.amount == 6000.0
    assert Budget.query.filter_by(category="Food", month=9, year=2026).count() == 1

def test_budget_vs_actual_and_over_budget_detection(app):
    # Set budgets
    BudgetService.set_or_update_budget("Food", 5000.0, 9, 2026)
    BudgetService.set_or_update_budget("Transport", 2000.0, 9, 2026)
    BudgetService.set_or_update_budget("Entertainment", 1500.0, 9, 2026)

    # Add expenses
    # Food is under budget (4200 / 5000 = 84%)
    FinanceService.add_expense("Food", 4200.0, date(2026, 9, 5))
    # Transport is OVER budget (2500 / 2000 = 125%)
    FinanceService.add_expense("Transport", 2500.0, date(2026, 9, 8))
    # Entertainment is near limit (1400 / 1500 = 93.3% -> warning)
    FinanceService.add_expense("Entertainment", 1400.0, date(2026, 9, 12))

    data = BudgetService.get_budget_vs_actual(9, 2026)

    # Check totals
    assert data['total_budget'] == 8500.0
    assert data['total_spent'] == 8100.0
    assert data['total_remaining'] == 400.0
    assert data['over_budget_count'] == 1

    # Check Transport over-budget flag
    transport_item = next(i for i in data['items'] if i['category'] == 'Transport')
    assert transport_item['is_over_budget'] is True
    assert transport_item['status'] == 'over'
    assert transport_item['spent'] == 2500.0
    assert transport_item['remaining'] == -500.0
    assert transport_item['percentage_used'] == 125.0

    # Check Food is normal
    food_item = next(i for i in data['items'] if i['category'] == 'Food')
    assert food_item['is_over_budget'] is False
    assert food_item['status'] == 'normal'
    assert food_item['remaining'] == 800.0

    # Check Entertainment warning
    ent_item = next(i for i in data['items'] if i['category'] == 'Entertainment')
    assert ent_item['is_over_budget'] is False
    assert ent_item['status'] == 'warning'

def test_automatic_budget_recommendation(app):
    FinanceService.add_income("Salary", 35000.0, date(2026, 9, 1))
    FinanceService.add_expense("Food", 5000.0, date(2026, 9, 5))
    FinanceService.add_expense("Rent", 10000.0, date(2026, 9, 2))

    rec = BudgetService.generate_recommended_budget(9, 2026)

    assert rec['income_analyzed'] == 35000.0
    assert len(rec['suggested_categories']) > 0
    assert rec['total_recommended_budget'] < 35000.0
    assert rec['projected_savings'] > 0
    assert rec['projected_savings_rate'] > 0
    assert len(rec['explanation_steps']) >= 3

def test_apply_recommended_budget(app):
    FinanceService.add_income("Salary", 35000.0, date(2026, 9, 1))
    rec = BudgetService.generate_recommended_budget(9, 2026)
    applied = BudgetService.apply_recommended_budget(9, 2026, rec['suggested_categories'])

    assert len(applied) == len(rec['suggested_categories'])
    # Verify budgets exist in DB
    budgets = Budget.query.filter_by(month=9, year=2026).all()
    assert len(budgets) == len(rec['suggested_categories'])
