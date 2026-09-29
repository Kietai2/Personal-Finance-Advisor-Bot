import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize database
    db.init_app(app)
    
    # Register template filters
    @app.template_filter('currency')
    def currency_filter(value):
        try:
            val = float(value or 0)
            # Format Indian Rupee style if positive/negative
            negative = val < 0
            val_abs = abs(val)
            # Format with 2 decimal places or standard comma separation
            s = f"{val_abs:,.2f}"
            if s.endswith('.00'):
                s = s[:-3]
            formatted = f"₹{s}"
            return f"-{formatted}" if negative else formatted
        except (ValueError, TypeError):
            return "₹0"
    
    @app.template_filter('percentage')
    def percentage_filter(value):
        try:
            val = float(value or 0)
            return f"{val:.1f}%"
        except (ValueError, TypeError):
            return "0.0%"

    # Context processors for global template variables
    @app.context_processor
    def inject_globals():
        from datetime import datetime
        now = datetime.now()
        has_gemini = bool(app.config.get('GEMINI_API_KEY'))
        return {
            'now': now,
            'current_year': now.year,
            'current_month': now.month,
            'currency_symbol': app.config.get('CURRENCY_SYMBOL', '₹'),
            'has_gemini_key': has_gemini,
            'default_categories': app.config.get('DEFAULT_EXPENSE_CATEGORIES', []),
            'default_income_sources': app.config.get('DEFAULT_INCOME_SOURCES', [])
        }

    # Register blueprints / routes
    from app.routes import main_bp, api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    with app.app_context():
        # Ensure database tables exist
        from app import models  # noqa: F401
        db.create_all()
        
    return app
