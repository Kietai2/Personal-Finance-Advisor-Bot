import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env if present
load_dotenv(BASE_DIR / '.env')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-super-secure-default-2026')
    
    # Instance directory for SQLite database
    INSTANCE_DIR = BASE_DIR / 'instance'
    INSTANCE_DIR.mkdir(exist_ok=True)
    
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        f"sqlite:///{INSTANCE_DIR / 'finance.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Gemini AI configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')
    
    # Application settings
    CURRENCY_SYMBOL = '₹'
    DEFAULT_EXPENSE_CATEGORIES = [
        'Food',
        'Rent',
        'Transport',
        'Utilities',
        'Education',
        'Healthcare',
        'Entertainment',
        'Shopping',
        'Bills',
        'Other'
    ]
    
    DEFAULT_INCOME_SOURCES = [
        'Salary',
        'Freelance',
        'Allowance',
        'Business',
        'Investment',
        'Other'
    ]

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    GEMINI_API_KEY = ''
