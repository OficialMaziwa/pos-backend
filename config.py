import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-here')
    
    # PostgreSQL database - use DATABASE_URL from Render environment
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
        print("✅ Using PostgreSQL database")
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///shop.db'
        print("⚠️ Using SQLite database (no DATABASE_URL found)")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    DEBUG = os.getenv('DEBUG', 'False') == 'True'