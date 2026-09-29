from datetime import date, datetime, timedelta
import calendar
from sqlalchemy import func, desc, or_
from app import db
from app.models import Income, Expense, Budget, SavingsGoal

class FinanceService:
    @staticmethod
    def parse_date(date_str):
        if not date_str:
            return date.today()
        if isinstance(date_str, (date, datetime)):
            return date_str if isinstance(date_str, date) else date_str.date()
        try:
            return datetime.strptime(str(date_str).strip(), '%Y-%m-%d').date()
        except ValueError:
            return date.today()

    # --- Income Operations ---
    @classmethod
    def add_income(cls, source, amount, date_val=None, notes=None, is_demo=False):
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Income amount must be greater than zero.")
        if not source or not str(source).strip():
            raise ValueError("Income source is required.")
        
        income = Income(
            source=source.strip(),
            amount=amount,
            date=cls.parse_date(date_val),
            notes=notes.strip() if notes else None,
            is_demo=is_demo
        )
        db.session.add(income)
        db.session.commit()
        return income

    @classmethod
    def update_income(cls, income_id, source=None, amount=None, date_val=None, notes=None):
        income = db.session.get(Income, income_id)
        if not income:
            return None
        if source is not None:
            if not str(source).strip():
                raise ValueError("Income source cannot be empty.")
            income.source = str(source).strip()
        if amount is not None:
            amt = float(amount)
            if amt <= 0:
                raise ValueError("Income amount must be greater than zero.")
            income.amount = amt
        if date_val is not None:
            income.date = cls.parse_date(date_val)
        if notes is not None:
            income.notes = str(notes).strip() if notes else None
        
        db.session.commit()
        return income

    @staticmethod
    def delete_income(income_id):
        income = db.session.get(Income, income_id)
        if income:
            db.session.delete(income)
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_incomes(month=None, year=None, search=None, source=None):
        query = Income.query
        if year:
            query = query.filter(func.strftime('%Y', Income.date) == f"{year:04d}")
        if month:
            query = query.filter(func.strftime('%m', Income.date) == f"{month:02d}")
        if source:
            query = query.filter(Income.source.ilike(f"%{source}%"))
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Income.source.ilike(search_term),
                    Income.notes.ilike(search_term)
                )
            )
        return query.order_by(desc(Income.date), desc(Income.id)).all()

    # --- Expense Operations ---
    @classmethod
    def add_expense(cls, category, amount, date_val=None, description=None, is_demo=False):
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Expense amount must be greater than zero.")
        if not category or not str(category).strip():
            raise ValueError("Expense category is required.")
        
        expense = Expense(
            category=category.strip(),
            amount=amount,
            date=cls.parse_date(date_val),
            description=description.strip() if description else None,
            is_demo=is_demo
        )
        db.session.add(expense)
        db.session.commit()
        return expense

    @classmethod
    def update_expense(cls, expense_id, category=None, amount=None, date_val=None, description=None):
        expense = db.session.get(Expense, expense_id)
        if not expense:
            return None
        if category is not None:
            if not str(category).strip():
                raise ValueError("Category cannot be empty.")
            expense.category = str(category).strip()
        if amount is not None:
            amt = float(amount)
            if amt <= 0:
                raise ValueError("Expense amount must be greater than zero.")
            expense.amount = amt
        if date_val is not None:
            expense.date = cls.parse_date(date_val)
        if description is not None:
            expense.description = str(description).strip() if description else None
        
        db.session.commit()
        return expense

    @staticmethod
    def delete_expense(expense_id):
        expense = db.session.get(Expense, expense_id)
        if expense:
            db.session.delete(expense)
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_expenses(month=None, year=None, category=None, start_date=None, end_date=None, search=None):
        query = Expense.query
        if year:
            query = query.filter(func.strftime('%Y', Expense.date) == f"{year:04d}")
        if month:
            query = query.filter(func.strftime('%m', Expense.date) == f"{month:02d}")
        if category:
            query = query.filter(Expense.category.ilike(category))
        if start_date:
            query = query.filter(Expense.date >= start_date)
        if end_date:
            query = query.filter(Expense.date <= end_date)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Expense.category.ilike(search_term),
                    Expense.description.ilike(search_term)
                )
            )
        return query.order_by(desc(Expense.date), desc(Expense.id)).all()

    # --- Savings Goals Operations ---
    @classmethod
    def add_savings_goal(cls, name, target_amount, current_amount=0.0, target_date=None, is_demo=False):
        target_amount = float(target_amount)
        current_amount = float(current_amount or 0.0)
        if target_amount <= 0:
            raise ValueError("Target amount must be greater than zero.")
        if current_amount < 0:
            raise ValueError("Current amount cannot be negative.")
        if not name or not str(name).strip():
            raise ValueError("Goal name is required.")
        if not target_date:
            raise ValueError("Target date is required.")
            
        goal = SavingsGoal(
            name=name.strip(),
            target_amount=target_amount,
            current_amount=current_amount,
            target_date=cls.parse_date(target_date),
            is_demo=is_demo
        )
        db.session.add(goal)
        db.session.commit()
        return goal

    @classmethod
    def update_savings_goal(cls, goal_id, name=None, target_amount=None, current_amount=None, target_date=None):
        goal = SavingsGoal.query.get(goal_id)
        if not goal:
            return None
        if name is not None:
            if not str(name).strip():
                raise ValueError("Goal name cannot be empty.")
            goal.name = str(name).strip()
        if target_amount is not None:
            t_amt = float(target_amount)
            if t_amt <= 0:
                raise ValueError("Target amount must be greater than zero.")
            goal.target_amount = t_amt
        if current_amount is not None:
            c_amt = float(current_amount)
            if c_amt < 0:
                raise ValueError("Current amount cannot be negative.")
            goal.current_amount = c_amt
        if target_date is not None:
            goal.target_date = cls.parse_date(target_date)
            
        db.session.commit()
        return goal

    @staticmethod
    def contribute_to_goal(goal_id, amount):
        amt = float(amount)
        if amt <= 0:
            raise ValueError("Contribution amount must be greater than zero.")
        goal = db.session.get(SavingsGoal, goal_id)
        if not goal:
            return None
        goal.current_amount += amt
        db.session.commit()
        return goal

    @staticmethod
    def delete_savings_goal(goal_id):
        goal = db.session.get(SavingsGoal, goal_id)
        if goal:
            db.session.delete(goal)
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_savings_goals():
        return SavingsGoal.query.order_by(SavingsGoal.target_date.asc()).all()

    # --- Aggregations & Analytics ---
    @classmethod
    def get_monthly_summary(cls, month, year):
        month = int(month)
        year = int(year)
        
        # Incomes for month
        incomes = cls.get_incomes(month=month, year=year)
        total_income = sum(i.amount for i in incomes)
        
        # Expenses for month
        expenses = cls.get_expenses(month=month, year=year)
        total_expenses = sum(e.amount for e in expenses)
        
        # Savings
        savings = total_income - total_expenses
        savings_rate = (savings / total_income * 100.0) if total_income > 0 else 0.0
        
        # Category breakdown
        category_totals = {}
        for exp in expenses:
            category_totals[exp.category] = category_totals.get(exp.category, 0.0) + exp.amount
            
        category_breakdown = []
        for cat, amt in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
            pct = (amt / total_expenses * 100.0) if total_expenses > 0 else 0.0
            category_breakdown.append({
                'category': cat,
                'amount': round(amt, 2),
                'percentage': round(pct, 1)
            })
            
        # Top 3 biggest expense categories
        biggest_categories = category_breakdown[:3]
        
        # Budget utilization for this month
        from app.services.budget_service import BudgetService
        budget_comparison = BudgetService.get_budget_vs_actual(month, year)
        
        b_items = budget_comparison.get('budget_items', [])
        total_budget = sum(b['budget'] for b in b_items)
        total_budget_spent = sum(b['spent'] for b in b_items)
        remaining_budget = max(0.0, total_budget - total_budget_spent) if total_budget > 0 else 0.0
        
        # Previous Month Comparison
        if month == 1:
            prev_m, prev_y = 12, year - 1
        else:
            prev_m, prev_y = month - 1, year
            
        prev_incomes = cls.get_incomes(month=prev_m, year=prev_y)
        prev_income_total = sum(i.amount for i in prev_incomes)
        
        prev_expenses = cls.get_expenses(month=prev_m, year=prev_y)
        prev_expense_total = sum(e.amount for e in prev_expenses)
        
        prev_savings = prev_income_total - prev_expense_total
        
        def calc_change(current, previous):
            if previous == 0:
                return 100.0 if current > 0 else 0.0
            return round(((current - previous) / previous) * 100.0, 1)
            
        comparison = {
            'prev_month': prev_m,
            'prev_year': prev_y,
            'prev_income': prev_income_total,
            'prev_expenses': prev_expense_total,
            'prev_savings': prev_savings,
            'income_change_pct': calc_change(total_income, prev_income_total),
            'expense_change_pct': calc_change(total_expenses, prev_expense_total),
            'savings_change_pct': calc_change(savings, prev_savings)
        }
        
        # Month name
        month_name = calendar.month_name[month]
        
        return {
            'month': month,
            'year': year,
            'month_name': month_name,
            'total_income': round(total_income, 2),
            'total_expenses': round(total_expenses, 2),
            'savings': round(savings, 2),
            'savings_rate': round(savings_rate, 1),
            'total_budget': round(total_budget, 2),
            'remaining_budget': round(remaining_budget, 2),
            'category_breakdown': category_breakdown,
            'biggest_categories': biggest_categories,
            'budget_comparison': budget_comparison,
            'comparison': comparison,
            'incomes_count': len(incomes),
            'expenses_count': len(expenses)
        }

    @classmethod
    def get_historical_monthly_data(cls, months_count=6):
        today = date.today()
        history = []
        
        # Collect last `months_count` months in chronological order
        year = today.year
        month = today.month
        
        month_keys = []
        for _ in range(months_count):
            month_keys.append((month, year))
            month -= 1
            if month == 0:
                month = 12
                year -= 1
                
        month_keys.reverse()
        
        for m, y in month_keys:
            incomes = cls.get_incomes(month=m, year=y)
            inc_tot = sum(i.amount for i in incomes)
            expenses = cls.get_expenses(month=m, year=y)
            exp_tot = sum(e.amount for e in expenses)
            sav_tot = inc_tot - exp_tot
            
            history.append({
                'month': m,
                'year': y,
                'label': f"{calendar.month_abbr[m]} '{str(y)[-2:]}",
                'income': round(inc_tot, 2),
                'expenses': round(exp_tot, 2),
                'savings': round(sav_tot, 2)
            })
            
        return history

    @classmethod
    def get_all_time_savings(cls):
        tot_inc = db.session.query(func.coalesce(func.sum(Income.amount), 0.0)).scalar() or 0.0
        tot_exp = db.session.query(func.coalesce(func.sum(Expense.amount), 0.0)).scalar() or 0.0
        return round(tot_inc - tot_exp, 2)

    @classmethod
    def get_all_transactions(cls, trans_type=None, category=None, start_date=None, end_date=None, search=None, sort_by='date_desc'):
        transactions = []
        
        # Load Incomes if trans_type is None or 'income'
        if not trans_type or trans_type == 'income':
            incomes = Income.query
            if start_date:
                incomes = incomes.filter(Income.date >= start_date)
            if end_date:
                incomes = incomes.filter(Income.date <= end_date)
            if category:
                incomes = incomes.filter(Income.source.ilike(f"%{category}%"))
            if search:
                s = f"%{search}%"
                incomes = incomes.filter(or_(Income.source.ilike(s), Income.notes.ilike(s)))
                
            for inc in incomes.all():
                transactions.append({
                    'id': inc.id,
                    'type': 'income',
                    'category_or_source': inc.source,
                    'amount': inc.amount,
                    'date': inc.date,
                    'description': inc.notes or '',
                    'is_demo': inc.is_demo,
                    'created_at': inc.created_at
                })

        # Load Expenses if trans_type is None or 'expense'
        if not trans_type or trans_type == 'expense':
            expenses = Expense.query
            if start_date:
                expenses = expenses.filter(Expense.date >= start_date)
            if end_date:
                expenses = expenses.filter(Expense.date <= end_date)
            if category:
                expenses = expenses.filter(Expense.category.ilike(category))
            if search:
                s = f"%{search}%"
                expenses = expenses.filter(or_(Expense.category.ilike(s), Expense.description.ilike(s)))
                
            for exp in expenses.all():
                transactions.append({
                    'id': exp.id,
                    'type': 'expense',
                    'category_or_source': exp.category,
                    'amount': exp.amount,
                    'date': exp.date,
                    'description': exp.description or '',
                    'is_demo': exp.is_demo,
                    'created_at': exp.created_at
                })

        # Sorting
        if sort_by == 'date_asc':
            transactions.sort(key=lambda x: (x['date'], x.get('created_at') or datetime.min))
        elif sort_by == 'amount_desc':
            transactions.sort(key=lambda x: x['amount'], reverse=True)
        elif sort_by == 'amount_asc':
            transactions.sort(key=lambda x: x['amount'])
        else: # default date_desc
            transactions.sort(key=lambda x: (x['date'], x.get('created_at') or datetime.min), reverse=True)

        return transactions

    # --- Demo Data Population & Reset ---
    @classmethod
    def populate_demo_data(cls):
        """Populate database with realistic Indian scenario data for demo/evaluation."""
        # Clean existing demo records first to avoid duplication
        cls.clear_demo_data()
        
        today = date.today()
        curr_y = today.year
        curr_m = today.month
        
        # Calculate prev month
        prev_m = 12 if curr_m == 1 else curr_m - 1
        prev_y = curr_y - 1 if curr_m == 1 else curr_y
        
        # Incomes: Current Month
        cls.add_income("Salary", 35000.0, date(curr_y, curr_m, 1), "Monthly software engineer salary (credited to HDFC)", is_demo=True)
        cls.add_income("Freelance", 7500.0, date(curr_y, curr_m, 12), "Web design freelance gig payout", is_demo=True)
        
        # Incomes: Previous Month
        cls.add_income("Salary", 35000.0, date(prev_y, prev_m, 1), "Monthly salary", is_demo=True)
        cls.add_income("Freelance", 5000.0, date(prev_y, prev_m, 15), "Content writing and tech consulting", is_demo=True)
        
        # Expenses: Current Month (Realistic college / young professional Indian expenses)
        demo_expenses_curr = [
            ("Rent", 10000.0, date(curr_y, curr_m, 2), "Monthly 1BHK apartment rent shared"),
            ("Food", 4200.0, date(curr_y, curr_m, 4), "Monthly grocery & provisions from Supermarket"),
            ("Utilities", 1450.0, date(curr_y, curr_m, 6), "Electricity and WiFi fiber bill"),
            ("Transport", 1850.0, date(curr_y, curr_m, 9), "Metro smart card recharge & petrol"),
            ("Food", 1800.0, date(curr_y, curr_m, 14), "Dining out with college batchmates"),
            ("Education", 2500.0, date(curr_y, curr_m, 16), "AI & Full-stack online certification course"),
            ("Shopping", 2800.0, date(curr_y, curr_m, 18), "Formal work clothing and backpack"),
            ("Healthcare", 950.0, date(curr_y, curr_m, 20), "Doctor consultation & dental checkup"),
            ("Entertainment", 1200.0, date(curr_y, curr_m, 22), "Weekend movie tickets and OTT subscription"),
            ("Bills", 699.0, date(curr_y, curr_m, 24), "Mobile prepaid quarterly recharge plan"),
            ("Food", 1250.0, date(curr_y, curr_m, min(26, calendar.monthrange(curr_y, curr_m)[1])), "Mid-month groceries & dairy"),
        ]
        for cat, amt, dt, desc_txt in demo_expenses_curr:
            cls.add_expense(cat, amt, dt, desc_txt, is_demo=True)

        # Expenses: Previous Month
        demo_expenses_prev = [
            ("Rent", 10000.0, date(prev_y, prev_m, 2), "Monthly rent"),
            ("Food", 6800.0, date(prev_y, prev_m, 5), "Groceries & restaurant visits"),
            ("Transport", 2100.0, date(prev_y, prev_m, 8), "Metro pass & fuel"),
            ("Utilities", 1600.0, date(prev_y, prev_m, 10), "Electricity & water"),
            ("Entertainment", 2400.0, date(prev_y, prev_m, 14), "Concert tickets and dinners"),
            ("Shopping", 4500.0, date(prev_y, prev_m, 18), "Festival sale electronics accessories"),
            ("Healthcare", 600.0, date(prev_y, prev_m, 22), "Routine prescription medicines"),
            ("Bills", 850.0, date(prev_y, prev_m, 25), "Gas cylinder refill & mobile bill"),
        ]
        for cat, amt, dt, desc_txt in demo_expenses_prev:
            cls.add_expense(cat, amt, dt, desc_txt, is_demo=True)

        # Budgets for Current Month
        from app.services.budget_service import BudgetService
        demo_budgets = [
            ("Rent", 10000.0),
            ("Food", 6000.0),
            ("Transport", 2500.0),
            ("Utilities", 2000.0),
            ("Education", 3000.0),
            ("Entertainment", 1500.0),
            ("Shopping", 3000.0),
            ("Healthcare", 1500.0),
            ("Bills", 1000.0),
        ]
        for cat, amt in demo_budgets:
            BudgetService.set_or_update_budget(cat, amt, curr_m, curr_y, is_demo=True)
            
        # Also set budgets for previous month so historical analysis has data
        for cat, amt in demo_budgets:
            BudgetService.set_or_update_budget(cat, amt, prev_m, prev_y, is_demo=True)

        # Savings Goals
        target_dt_1 = date(curr_y, min(curr_m + 6, 12), 28)
        target_dt_2 = date(curr_y + 1, 3, 31)
        target_dt_3 = date(curr_y, min(curr_m + 3, 12), 15)
        
        cls.add_savings_goal("Emergency Fund (6 Months)", 100000.0, 52000.0, target_dt_1, is_demo=True)
        cls.add_savings_goal("High-Performance Coding Laptop", 75000.0, 38000.0, target_dt_2, is_demo=True)
        cls.add_savings_goal("Goa Tech Hackathon & Trip", 20000.0, 14500.0, target_dt_3, is_demo=True)
        
        return True

    @classmethod
    def clear_demo_data(cls):
        """Clears only records marked with is_demo=True."""
        Income.query.filter_by(is_demo=True).delete()
        Expense.query.filter_by(is_demo=True).delete()
        Budget.query.filter_by(is_demo=True).delete()
        SavingsGoal.query.filter_by(is_demo=True).delete()
        db.session.commit()
        return True

    @classmethod
    def clear_all_data(cls):
        """Clears all records in the database."""
        Income.query.delete()
        Expense.query.delete()
        Budget.query.delete()
        SavingsGoal.query.delete()
        db.session.commit()
        return True
