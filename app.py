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

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'POS Backend is running',
        'database': 'SQLite'
    }), 200

# Import all blueprints
from routes import auth, products, customers, sales, stock, reports

# Register all blueprints
app.register_blueprint(auth.bp, url_prefix='/api/auth')
app.register_blueprint(products.bp, url_prefix='/api/products')
app.register_blueprint(customers.bp, url_prefix='/api/customers')
app.register_blueprint(sales.bp, url_prefix='/api/sales')
app.register_blueprint(stock.bp, url_prefix='/api/stock')
app.register_blueprint(reports.bp, url_prefix='/api/reports')

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 SMART POS BACKEND")
    print("=" * 50)
    print("📍 Server: http://localhost:5000")
    print("📊 Health: http://localhost:5000/health")
    print("🔐 Login: POST /api/auth/login")
    print("📝 Register: POST /api/auth/register")
    print("📋 Products: GET /api/products/")
    print("📊 Dashboard: GET /api/reports/dashboard")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)