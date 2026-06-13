from app import app
from utils.database import db
from sqlalchemy import inspect
from models.user import User

with app.app_context():
    # Angalia tables
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print("Tables:", tables)
    
    # Angalia users
    users = User.query.all()
    print(f"Total users: {len(users)}")
    for u in users:
        print(f"  - {u.email} (role: {u.role})")
    
    # Angalia admin
    admin = User.query.filter_by(email='admin@shop.com').first()
    if admin:
        print(f"✅ Admin exists: {admin.email}")
    else:
        print("❌ Admin does NOT exist!")