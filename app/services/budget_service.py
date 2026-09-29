from datetime import date
from sqlalchemy import func
from app import db
from app.models import Budget, Expense, Income

class BudgetService:
    @classmethod
    def set_or_update_budget(cls, category, amount, month, year, is_demo=False):
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Budget amount must be greater than zero.")
        if not category or not str(category).strip():
            raise ValueError("Category is required.")
        month = int(month)
        year = int(year)
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12.")

        category = category.strip()
        existing = Budget.query.filter_by(category=category, month=month, year=year).first()
        if existing:
            existing.amount = amount
            db.session.commit()
            return existing
        else:
            budget = Budget(
                category=category,
                amount=amount,
                month=month,
                year=year,
                is_demo=is_demo
            )
            db.session.add(budget)
            db.session.commit()
            return budget

    @staticmethod
    def delete_budget(budget_id):
        budget = db.session.get(Budget, budget_id)
        if budget:
            db.session.delete(budget)
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_budgets_for_month(month, year):
        month = int(month)
        year = int(year)
        return Budget.query.filter_by(month=month, year=year).order_by(Budget.category.asc()).all()

    @classmethod
    def get_budget_vs_actual(cls, month, year):
        month = int(month)
        year = int(year)

        budgets = cls.get_budgets_for_month(month, year)
        budget_map = {b.category.lower(): b for b in budgets}

        # Query actual spending in that month grouped by category
        expenses = Expense.query.filter(
            func.strftime('%Y', Expense.date) == f"{year:04d}",
            func.strftime('%m', Expense.date) == f"{month:02d}"
        ).all()

        spent_map = {}
        original_cat_names = {}
        for exp in expenses:
            cat_key = exp.category.strip().lower()
            spent_map[cat_key] = spent_map.get(cat_key, 0.0) + exp.amount
            if cat_key not in original_cat_names:
                original_cat_names[cat_key] = exp.category.strip()

        # Combine all categories from both budgets and expenses
        all_cat_keys = set(budget_map.keys()) | set(spent_map.keys())
        
        items = []
        for cat_key in sorted(all_cat_keys):
            b_obj = budget_map.get(cat_key)
            budget_amt = b_obj.amount if b_obj else 0.0
            spent_amt = spent_map.get(cat_key, 0.0)
            remaining = budget_amt - spent_amt
            budget_id = b_obj.id if b_obj else None

            # Get display category name
            display_name = b_obj.category if b_obj else original_cat_names.get(cat_key, cat_key.title())

            if budget_amt > 0:
                pct = (spent_amt / budget_amt) * 100.0
                is_over = spent_amt > budget_amt
                if is_over:
                    status = 'over'
                elif pct >= 85.0:
                    status = 'warning'
                else:
                    status = 'normal'
            else:
                pct = 100.0 if spent_amt > 0 else 0.0
                is_over = False
                status = 'unbudgeted'

            items.append({
                'id': budget_id,
                'category': display_name,
                'budget': round(budget_amt, 2),
                'spent': round(spent_amt, 2),
                'remaining': round(remaining, 2),
                'percentage_used': round(pct, 1),
                'is_over_budget': is_over,
                'status': status
            })

        total_budget = sum(i['budget'] for i in items)
        total_spent = sum(i['spent'] for i in items)
        total_remaining = total_budget - total_spent
        overall_pct = (total_spent / total_budget * 100.0) if total_budget > 0 else 0.0
        over_budget_count = sum(1 for i in items if i['is_over_budget'])

        return {
            'month': month,
            'year': year,
            'budget_items': items,
            'items': items,
            'total_budget': round(total_budget, 2),
            'total_spent': round(total_spent, 2),
            'total_remaining': round(total_remaining, 2),
            'overall_percentage': round(overall_pct, 1),
            'over_budget_count': over_budget_count
        }

    @classmethod
    def generate_recommended_budget(cls, month, year):
        """
        Deterministic budgeting baseline:
        Uses a tailored 50/30/20 guideline (Needs / Wants / Savings)
        calibrated against recent historical spending patterns.
        """
        month = int(month)
        year = int(year)

        # 1. Determine baseline monthly income
        curr_incomes = Income.query.filter(
            func.strftime('%Y', Income.date) == f"{year:04d}",
            func.strftime('%m', Income.date) == f"{month:02d}"
        ).all()
        curr_income_total = sum(i.amount for i in curr_incomes)

        # If current month has no income yet, check previous month or all-time average
        if curr_income_total <= 0:
            prev_m = 12 if month == 1 else month - 1
            prev_y = year - 1 if month == 1 else year
            prev_incomes = Income.query.filter(
                func.strftime('%Y', Income.date) == f"{prev_y:04d}",
                func.strftime('%m', Income.date) == f"{prev_m:02d}"
            ).all()
            curr_income_total = sum(i.amount for i in prev_incomes)

        if curr_income_total <= 0:
            # Fallback baseline of ₹35,000 for realistic demonstration
            curr_income_total = 35000.0
            income_source_note = "Estimated baseline income of ₹35,000 (No recorded income for target month)."
        else:
            income_source_note = f"Based on recorded monthly income of ₹{curr_income_total:,.2f}."

        # 2. Analyze historical expenses over the past 3 months
        all_expenses = Expense.query.all()
        cat_historical_sums = {}
        historical_months = set()

        for exp in all_expenses:
            m_key = (exp.date.year, exp.date.month)
            historical_months.add(m_key)
            cat = exp.category.strip()
            cat_historical_sums[cat] = cat_historical_sums.get(cat, 0.0) + exp.amount

        months_count = max(1, len(historical_months))
        cat_historical_avg = {cat: (total / months_count) for cat, total in cat_historical_sums.items()}

        # 3. Categorization into Needs vs Wants
        needs_categories = {'Rent', 'Food', 'Utilities', 'Transport', 'Healthcare', 'Education', 'Bills'}
        wants_categories = {'Entertainment', 'Shopping', 'Other'}

        # Target allocations: 50% Needs, 30% Wants, 20% Savings
        target_needs_budget = curr_income_total * 0.50
        target_wants_budget = curr_income_total * 0.30
        target_savings = curr_income_total * 0.20

        # Proportions of income for standard categories when history is lean
        standard_weights = {
            'Rent': 0.26,        # ~26% of income
            'Food': 0.16,        # ~16% of income
            'Transport': 0.06,   # ~6% of income
            'Utilities': 0.05,   # ~5% of income
            'Education': 0.06,   # ~6% of income
            'Healthcare': 0.04,  # ~4% of income
            'Bills': 0.03,       # ~3% of income
            'Shopping': 0.07,    # ~7% of income
            'Entertainment': 0.05,# ~5% of income
            'Other': 0.02        # ~2% of income
        }

        suggested_categories = []
        explanation_steps = [
            f"1. Evaluated Monthly Income: ₹{curr_income_total:,.2f} ({income_source_note})",
            f"2. Target 50/30/20 Allocation: Needs envelope: ₹{target_needs_budget:,.2f} (50%), Wants envelope: ₹{target_wants_budget:,.2f} (30%), Guaranteed Savings target: ₹{target_savings:,.2f} (20%).",
            f"3. Calibrated against {months_count} month(s) of historical transaction records."
        ]

        total_suggested_budget = 0.0

        for cat, weight in standard_weights.items():
            hist_avg = cat_historical_avg.get(cat, 0.0)
            
            if hist_avg > 0:
                # If historical data exists:
                if cat in needs_categories:
                    # For needs, allocate historical avg + slight 5% buffer, capped at 1.25x standard weight
                    recommended = min(curr_income_total * weight * 1.35, max(hist_avg * 1.05, curr_income_total * weight * 0.8))
                    reason = f"Essential need calibrated from historical spending (₹{hist_avg:,.0f}/mo) with inflation cushion."
                else:
                    # For wants, encourage 15% reduction if exceeding budget
                    standard_cap = curr_income_total * weight
                    if hist_avg > standard_cap:
                        recommended = round((hist_avg * 0.85 + standard_cap) / 2, -1)
                        reason = f"Discretionary spending trimmed by 15% from historical average (₹{hist_avg:,.0f}) to optimize savings."
                    else:
                        recommended = round(hist_avg * 1.05, -1)
                        reason = f"Discretionary category aligned with your disciplined historical pace (₹{hist_avg:,.0f}/mo)."
            else:
                # No historical data, use standard benchmark weight
                recommended = round(curr_income_total * weight, -1)
                reason = f"Allocated based on 50/30/20 benchmark guideline ({int(weight*100)}% of income)."

            # Round to nearest 50
            recommended = round(recommended / 50.0) * 50.0
            pct_of_income = round((recommended / curr_income_total) * 100.0, 1)

            suggested_categories.append({
                'category': cat,
                'recommended_amount': recommended,
                'historical_avg': round(hist_avg, 2),
                'percentage_of_income': pct_of_income,
                'type': 'Need' if cat in needs_categories else 'Want',
                'reasoning': reason
            })
            total_suggested_budget += recommended

        # Ensure total budget allows positive savings
        projected_savings = curr_income_total - total_suggested_budget
        projected_savings_rate = (projected_savings / curr_income_total * 100.0) if curr_income_total > 0 else 0.0

        explanation_steps.append(
            f"4. Total recommended budget is ₹{total_suggested_budget:,.2f}, leaving ₹{projected_savings:,.2f} ({projected_savings_rate:.1f}%) directly available for your savings goals."
        )

        return {
            'month': month,
            'year': year,
            'income_analyzed': round(curr_income_total, 2),
            'baseline_rule': "Deterministic 50/30/20 Rule + Historical Trend Weighting",
            'suggested_categories': suggested_categories,
            'total_recommended_budget': round(total_suggested_budget, 2),
            'projected_savings': round(projected_savings, 2),
            'projected_savings_rate': round(projected_savings_rate, 1),
            'explanation_steps': explanation_steps
        }

    @classmethod
    def apply_recommended_budget(cls, month, year, recommendations, is_demo=False):
        """Applies a list of category amounts as budgets for the given month/year."""
        applied = []
        for item in recommendations:
            cat = item.get('category')
            amt = float(item.get('recommended_amount', 0))
            if cat and amt > 0:
                b = cls.set_or_update_budget(cat, amt, month, year, is_demo=is_demo)
                applied.append(b)
        return applied
