import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-here')
    
    # PostgreSQL database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://neondb_owner:npg_BAmMf1DGw4Ji@ep-young-heart-aosjgg7z-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    DEBUG = os.getenv('DEBUG', 'False') == 'True'