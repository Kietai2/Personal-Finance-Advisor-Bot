from datetime import datetime, date
import calendar
import csv
import io
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, jsonify, Response, current_app
)
from app import db
from app.models import Income, Expense, Budget, SavingsGoal
from app.services.finance_service import FinanceService
from app.services.budget_service import BudgetService
from app.services.gemini_service import GeminiService

main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__)

# --- Helper function for default month/year ---
def get_month_year_from_request():
    today = date.today()
    try:
        month = int(request.args.get('month', today.month))
        year = int(request.args.get('year', today.year))
    except (ValueError, TypeError):
        month, year = today.month, today.year
    if month < 1 or month > 12:
        month = today.month
    if year < 2000 or year > 2100:
        year = today.year
    return month, year


# ==========================================
# 1. DASHBOARD
# ==========================================
@main_bp.route('/')
@main_bp.route('/dashboard')
def dashboard():
    month, year = get_month_year_from_request()
    summary = FinanceService.get_monthly_summary(month, year)
    history = FinanceService.get_historical_monthly_data(months_count=6)
    recent_transactions = FinanceService.get_all_transactions(sort_by='date_desc')[:8]
    goals = FinanceService.get_savings_goals()
    all_time_savings = FinanceService.get_all_time_savings()
    
    return render_template(
        'dashboard.html',
        summary=summary,
        history=history,
        recent_transactions=recent_transactions,
        goals=goals,
        all_time_savings=all_time_savings,
        selected_month=month,
        selected_year=year,
        months=list(enumerate(calendar.month_name))[1:]
    )


# ==========================================
# 2. INCOME MANAGEMENT
# ==========================================
@main_bp.route('/income', methods=['GET', 'POST'])
def income_view():
    if request.method == 'POST':
        try:
            source = request.form.get('source')
            amount = request.form.get('amount')
            date_val = request.form.get('date')
            notes = request.form.get('notes')
            
            FinanceService.add_income(source, amount, date_val, notes)
            flash(f"Income of ₹{float(amount):,.2f} from '{source}' successfully recorded!", "success")
            return redirect(url_for('main.income_view'))
        except ValueError as ve:
            flash(str(ve), "danger")
        except Exception as e:
            flash(f"Error recording income: {str(e)}", "danger")

    month_str = request.args.get('month')
    year_str = request.args.get('year')
    search = request.args.get('search')
    source_filter = request.args.get('source')
    
    month = int(month_str) if month_str and month_str.isdigit() else None
    year = int(year_str) if year_str and year_str.isdigit() else None
    
    incomes = FinanceService.get_incomes(month=month, year=year, search=search, source=source_filter)
    total_filtered_income = sum(i.amount for i in incomes)
    
    return render_template(
        'income.html',
        incomes=incomes,
        total_filtered_income=total_filtered_income,
        selected_month=month,
        selected_year=year,
        search=search or '',
        selected_source=source_filter or '',
        months=list(enumerate(calendar.month_name))[1:]
    )

@main_bp.route('/income/<int:income_id>/edit', methods=['POST'])
def edit_income(income_id):
    try:
        source = request.form.get('source')
        amount = request.form.get('amount')
        date_val = request.form.get('date')
        notes = request.form.get('notes')
        
        updated = FinanceService.update_income(income_id, source, amount, date_val, notes)
        if updated:
            flash("Income record updated successfully!", "success")
        else:
            flash("Income record not found.", "warning")
    except ValueError as ve:
        flash(str(ve), "danger")
    except Exception as e:
        flash(f"Error updating income: {str(e)}", "danger")
    return redirect(request.referrer or url_for('main.income_view'))

@main_bp.route('/income/<int:income_id>/delete', methods=['POST'])
def delete_income(income_id):
    if FinanceService.delete_income(income_id):
        flash("Income entry deleted successfully.", "info")
    else:
        flash("Record not found.", "warning")
    return redirect(request.referrer or url_for('main.income_view'))


# ==========================================
# 3. EXPENSE MANAGEMENT
# ==========================================
@main_bp.route('/expenses', methods=['GET', 'POST'])
def expenses_view():
    if request.method == 'POST':
        try:
            category = request.form.get('category')
            amount = request.form.get('amount')
            date_val = request.form.get('date')
            description = request.form.get('description')
            
            FinanceService.add_expense(category, amount, date_val, description)
            flash(f"Expense of ₹{float(amount):,.2f} in '{category}' logged successfully!", "success")
            return redirect(url_for('main.expenses_view'))
        except ValueError as ve:
            flash(str(ve), "danger")
        except Exception as e:
            flash(f"Error recording expense: {str(e)}", "danger")

    month_str = request.args.get('month')
    year_str = request.args.get('year')
    category_filter = request.args.get('category')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    search = request.args.get('search')
    
    month = int(month_str) if month_str and month_str.isdigit() else None
    year = int(year_str) if year_str and year_str.isdigit() else None
    start_date = FinanceService.parse_date(start_date_str) if start_date_str else None
    end_date = FinanceService.parse_date(end_date_str) if end_date_str else None

    expenses = FinanceService.get_expenses(
        month=month,
        year=year,
        category=category_filter,
        start_date=start_date,
        end_date=end_date,
        search=search
    )
    total_filtered_expenses = sum(e.amount for e in expenses)

    return render_template(
        'expenses.html',
        expenses=expenses,
        total_filtered_expenses=total_filtered_expenses,
        selected_month=month,
        selected_year=year,
        selected_category=category_filter or '',
        start_date=start_date_str or '',
        end_date=end_date_str or '',
        search=search or '',
        months=list(enumerate(calendar.month_name))[1:]
    )

@main_bp.route('/expenses/<int:expense_id>/edit', methods=['POST'])
def edit_expense(expense_id):
    try:
        category = request.form.get('category')
        amount = request.form.get('amount')
        date_val = request.form.get('date')
        description = request.form.get('description')
        
        updated = FinanceService.update_expense(expense_id, category, amount, date_val, description)
        if updated:
            flash("Expense record updated successfully!", "success")
        else:
            flash("Expense record not found.", "warning")
    except ValueError as ve:
        flash(str(ve), "danger")
    except Exception as e:
        flash(f"Error updating expense: {str(e)}", "danger")
    return redirect(request.referrer or url_for('main.expenses_view'))

@main_bp.route('/expenses/<int:expense_id>/delete', methods=['POST'])
def delete_expense(expense_id):
    if FinanceService.delete_expense(expense_id):
        flash("Expense entry removed.", "info")
    else:
        flash("Record not found.", "warning")
    return redirect(request.referrer or url_for('main.expenses_view'))


# ==========================================
# 4. BUDGET MANAGEMENT & AUTO-GENERATION
# ==========================================
@main_bp.route('/budgets', methods=['GET', 'POST'])
def budgets_view():
    month, year = get_month_year_from_request()
    
    if request.method == 'POST':
        try:
            category = request.form.get('category')
            amount = request.form.get('amount')
            b_month = int(request.form.get('month', month))
            b_year = int(request.form.get('year', year))
            
            BudgetService.set_or_update_budget(category, amount, b_month, b_year)
            flash(f"Budget for '{category}' set to ₹{float(amount):,.2f} for {calendar.month_name[b_month]} {b_year}.", "success")
            return redirect(url_for('main.budgets_view', month=b_month, year=b_year))
        except ValueError as ve:
            flash(str(ve), "danger")
        except Exception as e:
            flash(f"Error setting budget: {str(e)}", "danger")

    budget_vs_actual = BudgetService.get_budget_vs_actual(month, year)
    recommendation = BudgetService.generate_recommended_budget(month, year)

    return render_template(
        'budgets.html',
        budget_data=budget_vs_actual,
        recommendation=recommendation,
        selected_month=month,
        selected_year=year,
        month_name=calendar.month_name[month],
        months=list(enumerate(calendar.month_name))[1:]
    )

@main_bp.route('/budgets/<int:budget_id>/delete', methods=['POST'])
def delete_budget(budget_id):
    if BudgetService.delete_budget(budget_id):
        flash("Budget limit removed.", "info")
    else:
        flash("Budget item not found.", "warning")
    return redirect(request.referrer or url_for('main.budgets_view'))

@main_bp.route('/budgets/apply-recommendation', methods=['POST'])
def apply_budget_recommendations():
    month, year = get_month_year_from_request()
    rec = BudgetService.generate_recommended_budget(month, year)
    applied = BudgetService.apply_recommended_budget(month, year, rec.get('suggested_categories', []))
    flash(f"Successfully applied {len(applied)} recommended budget limits for {calendar.month_name[month]} {year}!", "success")
    return redirect(url_for('main.budgets_view', month=month, year=year))


# ==========================================
# 5. SAVINGS TRACKING & GOALS
# ==========================================
@main_bp.route('/savings')
def savings_view():
    month, year = get_month_year_from_request()
    summary = FinanceService.get_monthly_summary(month, year)
    all_time_savings = FinanceService.get_all_time_savings()
    goals = FinanceService.get_savings_goals()
    history = FinanceService.get_historical_monthly_data(months_count=6)
    
    return render_template(
        'savings.html',
        summary=summary,
        all_time_savings=all_time_savings,
        goals=goals,
        history=history,
        selected_month=month,
        selected_year=year,
        months=list(enumerate(calendar.month_name))[1:]
    )

@main_bp.route('/savings/goals', methods=['POST'])
def add_savings_goal():
    try:
        name = request.form.get('name')
        target_amount = request.form.get('target_amount')
        current_amount = request.form.get('current_amount', 0.0)
        target_date = request.form.get('target_date')
        
        FinanceService.add_savings_goal(name, target_amount, current_amount, target_date)
        flash(f"Savings Goal '{name}' created successfully!", "success")
    except ValueError as ve:
        flash(str(ve), "danger")
    except Exception as e:
        flash(f"Error creating savings goal: {str(e)}", "danger")
    return redirect(url_for('main.savings_view'))

@main_bp.route('/savings/goals/<int:goal_id>/edit', methods=['POST'])
def edit_savings_goal(goal_id):
    try:
        name = request.form.get('name')
        target_amount = request.form.get('target_amount')
        current_amount = request.form.get('current_amount')
        target_date = request.form.get('target_date')
        
        updated = FinanceService.update_savings_goal(goal_id, name, target_amount, current_amount, target_date)
        if updated:
            flash("Savings goal updated!", "success")
        else:
            flash("Goal not found.", "warning")
    except ValueError as ve:
        flash(str(ve), "danger")
    except Exception as e:
        flash(f"Error updating goal: {str(e)}", "danger")
    return redirect(url_for('main.savings_view'))

@main_bp.route('/savings/goals/<int:goal_id>/contribute', methods=['POST'])
def contribute_to_goal(goal_id):
    try:
        amount = request.form.get('amount')
        goal = FinanceService.contribute_to_goal(goal_id, amount)
        if goal:
            flash(f"Added ₹{float(amount):,.2f} to '{goal.name}'! (Now {goal.progress_percentage}% complete)", "success")
        else:
            flash("Goal not found.", "warning")
    except ValueError as ve:
        flash(str(ve), "danger")
    except Exception as e:
        flash(f"Error contributing: {str(e)}", "danger")
    return redirect(url_for('main.savings_view'))

@main_bp.route('/savings/goals/<int:goal_id>/delete', methods=['POST'])
def delete_savings_goal(goal_id):
    if FinanceService.delete_savings_goal(goal_id):
        flash("Savings goal deleted.", "info")
    else:
        flash("Goal not found.", "warning")
    return redirect(url_for('main.savings_view'))


# ==========================================
# 6. GEMINI AI FINANCIAL ADVISOR
# ==========================================
@main_bp.route('/advisor', methods=['GET', 'POST'])
def advisor_view():
    month, year = get_month_year_from_request()
    summary = FinanceService.get_monthly_summary(month, year)
    budget_comparison = BudgetService.get_budget_vs_actual(month, year)
    goals = FinanceService.get_savings_goals()
    history = FinanceService.get_historical_monthly_data(months_count=6)
    
    financial_data = {
        'summary': summary,
        'budget_items': budget_comparison.get('items', []),
        'goals': goals,
        'history': history
    }

    custom_query = None
    ai_result = None
    
    if request.method == 'POST':
        custom_query = request.form.get('custom_query', '').strip()
        ai_result = GeminiService.analyze_finances(financial_data, custom_query)
    elif request.args.get('auto_analyze') == '1':
        ai_result = GeminiService.analyze_finances(financial_data)

    return render_template(
        'advisor.html',
        summary=summary,
        ai_result=ai_result,
        selected_month=month,
        selected_year=year,
        custom_query=custom_query or '',
        has_gemini=GeminiService.is_configured(),
        months=list(enumerate(calendar.month_name))[1:]
    )


# ==========================================
# 7. MONTHLY FINANCIAL REPORT
# ==========================================
@main_bp.route('/reports')
def reports_view():
    month, year = get_month_year_from_request()
    summary = FinanceService.get_monthly_summary(month, year)
    budget_comparison = BudgetService.get_budget_vs_actual(month, year)
    goals = FinanceService.get_savings_goals()
    
    financial_data = {
        'summary': summary,
        'budget_items': budget_comparison.get('items', []),
        'goals': goals
    }
    
    # Generate concise AI/Heuristic executive summary for the report
    ai_summary = GeminiService.analyze_finances(
        financial_data,
        custom_query="Provide a concise 2-3 paragraph executive summary of this specific month's financial health, key highlights, and primary actionable recommendation."
    )

    return render_template(
        'reports.html',
        summary=summary,
        budget_comparison=budget_comparison,
        ai_summary=ai_summary,
        selected_month=month,
        selected_year=year,
        month_name=calendar.month_name[month],
        months=list(enumerate(calendar.month_name))[1:]
    )


# ==========================================
# 8. TRANSACTION HISTORY & EXPORT
# ==========================================
@main_bp.route('/transactions')
def transactions_view():
    trans_type = request.args.get('type')  # 'income', 'expense', or None
    category = request.args.get('category')
    search = request.args.get('search')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    sort_by = request.args.get('sort', 'date_desc')

    start_date = FinanceService.parse_date(start_date_str) if start_date_str else None
    end_date = FinanceService.parse_date(end_date_str) if end_date_str else None

    all_tx = FinanceService.get_all_transactions(
        trans_type=trans_type,
        category=category,
        start_date=start_date,
        end_date=end_date,
        search=search,
        sort_by=sort_by
    )

    # Basic pagination
    page = int(request.args.get('page', 1))
    per_page = 20
    total_tx = len(all_tx)
    total_pages = max(1, (total_tx + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_tx = all_tx[start_idx:end_idx]

    # Metrics on filtered transactions
    total_inc = sum(t['amount'] for t in all_tx if t['type'] == 'income')
    total_exp = sum(t['amount'] for t in all_tx if t['type'] == 'expense')
    net_diff = total_inc - total_exp

    return render_template(
        'transactions.html',
        transactions=paginated_tx,
        total_tx=total_tx,
        page=page,
        total_pages=total_pages,
        total_income=total_inc,
        total_expense=total_exp,
        net_difference=net_diff,
        trans_type=trans_type or '',
        category=category or '',
        search=search or '',
        start_date=start_date_str or '',
        end_date=end_date_str or '',
        sort=sort_by
    )

@main_bp.route('/transactions/export')
def export_transactions():
    """Export filtered transactions to CSV format."""
    trans_type = request.args.get('type')
    category = request.args.get('category')
    search = request.args.get('search')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    start_date = FinanceService.parse_date(start_date_str) if start_date_str else None
    end_date = FinanceService.parse_date(end_date_str) if end_date_str else None

    transactions = FinanceService.get_all_transactions(
        trans_type=trans_type,
        category=category,
        start_date=start_date,
        end_date=end_date,
        search=search
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Type', 'Category / Source', 'Amount (INR)', 'Description / Notes', 'Is Demo Data'])

    for t in transactions:
        writer.writerow([
            t['date'].strftime('%Y-%m-%d'),
            t['type'].upper(),
            t['category_or_source'],
            f"{t['amount']:.2f}",
            t['description'],
            'Yes' if t['is_demo'] else 'No'
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=transactions_{date.today().strftime('%Y%m%d')}.csv"}
    )


# ==========================================
# 9. DEMO DATA MANAGEMENT
# ==========================================
@main_bp.route('/demo/load', methods=['POST', 'GET'])
def load_demo():
    FinanceService.populate_demo_data()
    flash("Realistic Indian sample financial dataset loaded! (Monthly salary ₹35,000, categorized expenses, budgets, and savings goals)", "success")
    return redirect(request.referrer or url_for('main.dashboard'))

@main_bp.route('/demo/clear', methods=['POST', 'GET'])
def clear_demo():
    FinanceService.clear_demo_data()
    flash("Sample demo records have been cleared without affecting your personal records.", "info")
    return redirect(request.referrer or url_for('main.dashboard'))

@main_bp.route('/demo/reset-all', methods=['POST', 'GET'])
def reset_all():
    FinanceService.clear_all_data()
    flash("Database reset: All income, expenses, budgets, and goals have been cleared.", "warning")
    return redirect(url_for('main.dashboard'))


# ==========================================
# 10. REST API ENDPOINTS
# ==========================================
@api_bp.route('/summary')
def api_summary():
    month, year = get_month_year_from_request()
    summary = FinanceService.get_monthly_summary(month, year)
    return jsonify(summary)

@api_bp.route('/history')
def api_history():
    history = FinanceService.get_historical_monthly_data(months_count=6)
    return jsonify(history)

@api_bp.route('/budget-vs-actual')
def api_budget_vs_actual():
    month, year = get_month_year_from_request()
    data = BudgetService.get_budget_vs_actual(month, year)
    return jsonify(data)

@api_bp.route('/advisor/analyze', methods=['POST'])
def api_advisor_analyze():
    data = request.get_json() or {}
    month, year = get_month_year_from_request()
    summary = FinanceService.get_monthly_summary(month, year)
    budget_comparison = BudgetService.get_budget_vs_actual(month, year)
    goals = FinanceService.get_savings_goals()
    history = FinanceService.get_historical_monthly_data(months_count=6)

    payload = {
        'summary': summary,
        'budget_items': budget_comparison.get('items', []),
        'goals': goals,
        'history': history
    }
    custom_query = data.get('query')
    result = GeminiService.analyze_finances(payload, custom_query)
    return jsonify(result)
