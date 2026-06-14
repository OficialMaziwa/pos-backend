from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from config import Config
from utils.database import init_db
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

# ============ CORS CONFIGURATION - HII INASULUHISHA TATIZO LA CORS ============
CORS(app, 
     origins=['*'],
     allow_headers=['Content-Type', 'Authorization', 'Accept'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     supports_credentials=True)

# Middleware ya kushughulikia CORS kwa manually
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Accept')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    
    if request.method == 'OPTIONS':
        response.status_code = 200
    
    return response
# =============================================================================

jwt = JWTManager(app)
db = init_db(app)

# ============ CREATE TABLES ============
with app.app_context():
    from sqlalchemy import inspect
    from models.user import User
    from models.product import Product
    from models.customer import Customer
    from models.sale import Sale, SaleItem
    from models.stock_movement import StockMovement
    
    inspector = inspect(db.engine)
    print(f"Tables before create_all: {inspector.get_table_names()}")
    
    db.create_all()
    print(f"Tables after create_all: {inspector.get_table_names()}")
    
    # Create default admin user
    admin = User.query.filter_by(email='malabamalaba26@gmail.com').first()
    if not admin:
        admin = User(
            name='Malaba Maziwa',
            email='malabamalaba26@gmail.com',
            phone='0763387403',
            role='admin'
        )
        admin.set_password('Malaba@03')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created successfully!")
    else:
        print("✅ Admin user already exists.")
# ========================================

@app.route('/health', methods=['GET', 'OPTIONS'])
def health_check():
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({
        'status': 'healthy',
        'message': 'POS Backend is running',
        'database': 'PostgreSQL/SQLite'
    }), 200

# ============ AUTH ENDPOINTS (Direct without blueprint) ============
@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    from models.user import User
    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id)
        return jsonify({
            'success': True,
            'access_token': access_token,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role
            }
        }), 200
    
    return jsonify({'success': False, 'message': 'Email au password si sahihi'}), 401

@app.route('/api/auth/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    from models.user import User
    
    existing = User.query.filter_by(email=data['email']).first()
    if existing:
        return jsonify({'success': False, 'message': 'Email tayari ipo'}), 400
    
    user = User(
        name=data['name'],
        email=data['email'],
        phone=data.get('phone', ''),
        role=data.get('role', 'cashier')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'User created successfully'}), 201

# ============ PRODUCTS ENDPOINTS ============
@app.route('/api/products', methods=['GET', 'OPTIONS'])
def get_products():
    if request.method == 'OPTIONS':
        return '', 200
    
    from models.product import Product
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'sku': p.sku,
        'category': p.category,
        'stock': p.stock,
        'costPrice': p.cost_price,
        'sellingPrice': p.selling_price,
        'alertLevel': p.alert_level
    } for p in products]), 200

@app.route('/api/products', methods=['POST', 'OPTIONS'])
def add_product():
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    from models.product import Product
    
    product = Product(
        name=data['name'],
        sku=data.get('sku', data['name'][:3].upper() + '-' + str(int(datetime.now().timestamp()))),
        category=data['category'],
        stock=data.get('stock', 0),
        cost_price=data.get('costPrice', 0),
        selling_price=data['sellingPrice'],
        alert_level=data.get('alertLevel', 10)
    )
    
    db.session.add(product)
    db.session.commit()
    
    return jsonify({'success': True, 'id': product.id}), 201

@app.route('/api/products/<int:product_id>', methods=['PUT', 'OPTIONS'])
def update_product(product_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    from models.product import Product
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404
    
    if 'sellingPrice' in data:
        product.selling_price = data['sellingPrice']
    
    db.session.commit()
    return jsonify({'success': True}), 200

@app.route('/api/products/<int:product_id>', methods=['DELETE', 'OPTIONS'])
def delete_product(product_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    from models.product import Product
    
    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
    
    return jsonify({'success': True}), 200

@app.route('/api/products/stock', methods=['POST', 'OPTIONS'])
def update_stock():
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    from models.product import Product
    from models.stock_movement import StockMovement
    
    product = Product.query.get(data['productId'])
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404
    
    product.stock += data['quantity']
    
    if data.get('newPrice') and data['newPrice'] > 0:
        product.selling_price = data['newPrice']
    
    # Record stock movement
    movement = StockMovement(
        product_id=product.id,
        quantity=data['quantity'],
        type='add',
        note='Stock added from POS'
    )
    db.session.add(movement)
    db.session.commit()
    
    return jsonify({'success': True}), 200

# ============ CATEGORIES ENDPOINTS ============
@app.route('/api/categories', methods=['GET', 'OPTIONS'])
def get_categories():
    if request.method == 'OPTIONS':
        return '', 200
    
    from models.product import Product
    categories = db.session.query(Product.category).distinct().all()
    cats = [c[0] for c in categories if c[0]]
    
    # Default categories if none exist
    if not cats:
        cats = ['Vyakula', 'Dawa', 'Nguo', 'Vifaa', 'Vinywaji', 'Vipodozi', 'Electronics']
    
    return jsonify(cats), 200

@app.route('/api/categories', methods=['POST', 'OPTIONS'])
def add_category():
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    # Categories are just strings, no separate table needed
    return jsonify({'success': True}), 201

@app.route('/api/categories/<string:name>', methods=['DELETE', 'OPTIONS'])
def delete_category(name):
    if request.method == 'OPTIONS':
        return '', 200
    
    # Check if any product uses this category
    from models.product import Product
    products = Product.query.filter_by(category=name).all()
    if products:
        return jsonify({'success': False, 'message': 'Category ina bidhaa, futa bidhaa kwanza'}), 400
    
    return jsonify({'success': True}), 200

# ============ CUSTOMERS ENDPOINTS ============
@app.route('/api/customers', methods=['GET', 'OPTIONS'])
def get_customers():
    if request.method == 'OPTIONS':
        return '', 200
    
    from models.customer import Customer
    customers = Customer.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'phone': c.phone,
        'email': c.email,
        'address': c.address
    } for c in customers]), 200

@app.route('/api/customers', methods=['POST', 'OPTIONS'])
def add_customer():
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    from models.customer import Customer
    
    customer = Customer(
        name=data['name'],
        phone=data.get('phone', ''),
        email=data.get('email', ''),
        address=data.get('address', '')
    )
    
    db.session.add(customer)
    db.session.commit()
    
    return jsonify({'success': True}), 201

@app.route('/api/customers/<int:customer_id>', methods=['DELETE', 'OPTIONS'])
def delete_customer(customer_id):
    if request.method == 'OPTIONS':
        return '', 200
    
    from models.customer import Customer
    
    customer = Customer.query.get(customer_id)
    if customer:
        db.session.delete(customer)
        db.session.commit()
    
    return jsonify({'success': True}), 200

# ============ SALES ENDPOINTS ============
@app.route('/api/sales', methods=['GET', 'OPTIONS'])
def get_sales():
    if request.method == 'OPTIONS':
        return '', 200
    
    from models.sale import Sale
    
    sales = Sale.query.order_by(Sale.date.desc()).all()
    return jsonify([{
        'id': s.id,
        'invoice': s.invoice,
        'customerName': s.customer_name,
        'customerPhone': s.customer_phone,
        'total': s.total,
        'profit': s.profit,
        'payment': s.payment_method,
        'date': s.date.isoformat()
    } for s in sales]), 200

@app.route('/api/sales', methods=['POST', 'OPTIONS'])
def add_sale():
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    from models.sale import Sale, SaleItem
    from models.product import Product
    
    # Create sale
    sale = Sale(
        invoice=data['invoice'],
        customer_name=data.get('customerName', 'Mteja wa Kawaida'),
        customer_phone=data.get('customerPhone', ''),
        total=data['total'],
        profit=data['profit'],
        payment_method=data['payment']
    )
    
    db.session.add(sale)
    db.session.flush()
    
    # Add sale items
    for item in data['items']:
        sale_item = SaleItem(
            sale_id=sale.id,
            product_name=item['productName'],
            quantity=item['quantity'],
            price=item['price'],
            total=item['total']
        )
        db.session.add(sale_item)
        
        # Update product stock
        product = Product.query.filter_by(name=item['productName']).first()
        if product:
            product.stock -= item['quantity']
    
    db.session.commit()
    
    return jsonify({'success': True, 'id': sale.id}), 201

# ============ USERS ENDPOINTS ============
@app.route('/api/users', methods=['GET', 'OPTIONS'])
def get_users():
    if request.method == 'OPTIONS':
        return '', 200
    
    from models.user import User
    
    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'name': u.name,
        'email': u.email,
        'phone': u.phone,
        'role': u.role
    } for u in users]), 200

@app.route('/api/users', methods=['POST', 'OPTIONS'])
def add_user():
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    from models.user import User
    
    existing = User.query.filter_by(email=data['email']).first()
    if existing:
        return jsonify({'success': False, 'message': 'Email tayari ipo'}), 400
    
    user = User(
        name=data['name'],
        email=data['email'],
        phone=data.get('phone', ''),
        role=data.get('role', 'cashier')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'success': True}), 201

@app.route('/api/users/<string:email>', methods=['DELETE', 'OPTIONS'])
def delete_user(email):
    if request.method == 'OPTIONS':
        return '', 200
    
    from models.user import User
    
    if email == 'malabamalaba26@gmail.com':
        return jsonify({'success': False, 'message': 'Hauwezi kufuta admin mkuu!'}), 400
    
    user = User.query.filter_by(email=email).first()
    if user:
        db.session.delete(user)
        db.session.commit()
    
    return jsonify({'success': True}), 200

# ============ DASHBOARD ENDPOINTS ============
@app.route('/api/dashboard', methods=['GET', 'OPTIONS'])
def get_dashboard():
    if request.method == 'OPTIONS':
        return '', 200
    
    from models.product import Product
    from models.sale import Sale
    
    today = datetime.now().date()
    
    # Today's sales
    today_sales = Sale.query.filter(db.func.date(Sale.date) == today).all()
    today_revenue = sum(s.total for s in today_sales)
    today_profit = sum(s.profit for s in today_sales)
    
    # Stock value
    products = Product.query.all()
    stock_value = sum(p.stock * p.selling_price for p in products)
    total_cost = sum(p.stock * p.cost_price for p in products)
    expected_profit = stock_value - total_cost
    
    # Low stock count
    low_stock_count = sum(1 for p in products if p.stock <= p.alert_level)
    
    return jsonify({
        'todayRevenue': today_revenue,
        'todayProfit': today_profit,
        'stockValue': stock_value,
        'expectedProfit': expected_profit,
        'lowStockCount': low_stock_count
    }), 200

# ============ IMPORT BLUEPRINTS (Optional - for additional routes) ============
try:
    from routes import auth, products, customers, sales, stock, reports
    
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(products.bp, url_prefix='/api/products')
    app.register_blueprint(customers.bp, url_prefix='/api/customers')
    app.register_blueprint(sales.bp, url_prefix='/api/sales')
    app.register_blueprint(stock.bp, url_prefix='/api/stock')
    app.register_blueprint(reports.bp, url_prefix='/api/reports')
    print("✅ Blueprints registered successfully")
except Exception as e:
    print(f"⚠️ Blueprints not found or error: {e}")

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 SMART POS BACKEND - FIXED VERSION")
    print("=" * 50)
    print("📍 Server: http://localhost:5000")
    print("📊 Health: http://localhost:5000/health")
    print("🔐 Login: POST /api/login")
    print("📝 Register: POST /api/auth/register")
    print("📋 Products: GET /api/products")
    print("📊 Dashboard: GET /api/dashboard")
    print("=" * 50)
    print("✅ CORS enabled - Frontend can connect from any domain")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
