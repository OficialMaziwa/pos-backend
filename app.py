from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from utils.database import init_db

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
jwt = JWTManager(app)
db = init_db(app)

# ============ CREATE TABLES AND ADMIN USER ============
with app.app_context():
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    print(f"Tables before: {inspector.get_table_names()}")
    
    db.create_all()
    print(f"Tables after: {inspector.get_table_names()}")
    
    from models.user import User
    admin = User.query.filter_by(email='admin@shop.com').first()
    if not admin:
        admin = User(
            name='Admin User',
            email='admin@shop.com',
            phone='0712345678',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created!")
    else:
        print("✅ Admin user exists.")
# =====================================================

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'POS Backend is running',
        'database': 'PostgreSQL'
    }), 200

from routes import auth, products, customers, sales, stock, reports

app.register_blueprint(auth.bp, url_prefix='/api/auth')
app.register_blueprint(products.bp, url_prefix='/api/products')
app.register_blueprint(customers.bp, url_prefix='/api/customers')
app.register_blueprint(sales.bp, url_prefix='/api/sales')
app.register_blueprint(stock.bp, url_prefix='/api/stock')
app.register_blueprint(reports.bp, url_prefix='/api/reports')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)