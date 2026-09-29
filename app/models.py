from datetime import datetime, date
from app import db

class Income(db.Model):
    __tablename__ = 'incomes'
    
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_demo = db.Column(db.Boolean, default=False, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'source': self.source,
            'amount': self.amount,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'notes': self.notes or '',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_demo': self.is_demo
        }

    def __repr__(self):
        return f"<Income #{self.id} {self.source} ₹{self.amount}>"


class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_demo = db.Column(db.Boolean, default=False, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'amount': self.amount,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'description': self.description or '',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_demo': self.is_demo
        }

    def __repr__(self):
        return f"<Expense #{self.id} {self.category} ₹{self.amount}>"


class Budget(db.Model):
    __tablename__ = 'budgets'
    __table_args__ = (
        db.UniqueConstraint('category', 'month', 'year', name='uq_budget_cat_month_year'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.Integer, nullable=False)  # 1 to 12
    year = db.Column(db.Integer, nullable=False)   # e.g. 2026
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_demo = db.Column(db.Boolean, default=False, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'amount': self.amount,
            'month': self.month,
            'year': self.year,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_demo': self.is_demo
        }

    def __repr__(self):
        return f"<Budget {self.category} {self.month}/{self.year}: ₹{self.amount}>"


class SavingsGoal(db.Model):
    __tablename__ = 'savings_goals'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0, nullable=False)
    target_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_demo = db.Column(db.Boolean, default=False, nullable=False)

    @property
    def progress_percentage(self):
        if not self.target_amount or self.target_amount <= 0:
            return 0.0
        pct = (self.current_amount / self.target_amount) * 100.0
        return min(100.0, max(0.0, round(pct, 1)))

    @property
    def remaining_amount(self):
        return max(0.0, self.target_amount - self.current_amount)

    @property
    def is_achieved(self):
        return self.current_amount >= self.target_amount

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'target_amount': self.target_amount,
            'current_amount': self.current_amount,
            'target_date': self.target_date.strftime('%Y-%m-%d') if self.target_date else None,
            'progress_percentage': self.progress_percentage,
            'remaining_amount': self.remaining_amount,
            'is_achieved': self.is_achieved,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_demo': self.is_demo
        }

    def __repr__(self):
        return f"<SavingsGoal {self.name}: ₹{self.current_amount}/{self.target_amount}>"
