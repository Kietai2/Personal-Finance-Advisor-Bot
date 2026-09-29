from datetime import date
import pytest
from app.services.finance_service import FinanceService
from app.models import SavingsGoal

def test_add_and_contribute_to_savings_goal(app):
    goal = FinanceService.add_savings_goal(
        name="Emergency Fund",
        target_amount=100000.0,
        current_amount=20000.0,
        target_date=date(2027, 3, 31)
    )

    assert goal.id is not None
    assert goal.progress_percentage == 20.0
    assert goal.remaining_amount == 80000.0
    assert goal.is_achieved is False

    # Contribute to goal
    updated = FinanceService.contribute_to_goal(goal.id, 30000.0)
    assert updated.current_amount == 50000.0
    assert updated.progress_percentage == 50.0

    # Complete goal
    FinanceService.contribute_to_goal(goal.id, 50000.0)
    assert goal.is_achieved is True
    assert goal.progress_percentage == 100.0

def test_savings_goal_validation(app):
    with pytest.raises(ValueError, match="Target amount must be greater than zero"):
        FinanceService.add_savings_goal("Car", 0, target_date=date(2027, 1, 1))

    with pytest.raises(ValueError, match="Goal name is required"):
        FinanceService.add_savings_goal("", 50000, target_date=date(2027, 1, 1))
