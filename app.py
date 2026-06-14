from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import sys

app = Flask(__name__)

# ============ CONFIGURATION ============
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///pos.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'super-secret-key-change-this')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

# ============ CORS CONFIGURATION ============
CORS(app, 
     origins=['*'],
     allow_headers=['Content-Type', 'Authorization', 'Accept'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     supports_credentials=True)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Accept')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    if request.method == 'OPTIONS':
        response.status_code = 200
    return response

# ============ INITIALIZE DATABASE ============
db = SQLAlchemy(app)
jwt = JWTManager(app)

# ============ MODELS ============
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), default='')
    role = db.Column(db.String(20), default='cashier')
    password_hash = db.Column(db.String(200), nullable=False)
    
    def set_password(self, password):
        import bcrypt
        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    def check_password(self, password):
        import bcrypt
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sku = db.Column(db.String(50), unique=True)
    category = db.Column(db.String(50))
    stock = db.Column(db.Integer, default=0)
    cost_price = db.Column(db.Float, default=0)
    selling_price = db.Column(db.Float, nullable=False)
    alert_level = db.Column(db.Integer, default=10)

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.String(200))

class Sale(db.Model):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    invoice = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), default='Mteja wa Kawaida')
    customer_phone = db.Column(db.String(20), default='')
    total = db.Column(db.Float, default=0)
    profit = db.Column(db.Float, default=0)
    payment_method = db.Column(db.String(20), default='cash')
    date = db.Column(db.DateTime, default=datetime.utcnow)

class SaleItem(db.Model):
    __tablename__ = 'sale_items'
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'))
    product_name = db.Column(db.String(100))
    quantity = db.Column(db.Integer, default=0)
    price = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)

class StockMovement(db.Model):
    __tablename__ = 'stock_movements'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer)
    type = db.Column(db.String(20))
    note = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)

# ============ INITIALIZE DATABASE TABLES (Bila reset) ============
def init_database():
    with app.app_context():
        print("=" * 50)
        print("🔄 CHECKING DATABASE...")
        print("=" * 50)
        
        # Create tables only (NOT dropping)
        db.create_all()
        print("✅ Tables created/verified successfully!")
        
        # Create default admin user if not exists
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
            print("✅ Admin user created: malabamalaba26@gmail.com / Malaba@03")
        else:
            print("✅ Admin user already exists.")
        
        # Add default products if none exist
        if Product.query.count() == 0:
            default_products = [
                {'name': 'Maziwa Tatu', 'sku': 'MAZ-001', 'category': 'Vyakula', 'stock': 50, 'cost_price': 1500, 'selling_price': 2000, 'alert_level': 10},
                {'name': 'Sukari 1kg', 'sku': 'SUK-001', 'category': 'Vyakula', 'stock': 30, 'cost_price': 2000, 'selling_price': 2800, 'alert_level': 5},
                {'name': 'Unga 1kg', 'sku': 'UNG-001', 'category': 'Vyakula', 'stock': 40, 'cost_price': 1800, 'selling_price': 2500, 'alert_level': 8},
                {'name': 'Paracetamol', 'sku': 'PAR-001', 'category': 'Dawa', 'stock': 100, 'cost_price': 500, 'selling_price': 1000, 'alert_level': 20},
                {'name': 'T-Shirt', 'sku': 'TSH-001', 'category': 'Nguo', 'stock': 20, 'cost_price': 5000, 'selling_price': 10000, 'alert_level': 5},
            ]
            for p in default_products:
                product = Product(**p)
                db.session.add(product)
            db.session.commit()
            print(f"✅ {len(default_products)} default products added!")
        
        print("=" * 50)
        print("✅ DATABASE INITIALIZATION COMPLETED!")
        print("=" * 50)

# Run initialization
init_database()
# ================================================

# ============ HEALTH CHECK ============
@app.route('/health', methods=['GET', 'OPTIONS'])
def health_check():
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({
        'status': 'healthy',
        'message': 'POS Backend is running',
        'database': 'PostgreSQL/SQLite'
    }), 200

# ============ AUTH ENDPOINTS ============
@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
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

# ============ PRODUCTS ENDPOINTS ============
@app.route('/api/products', methods=['GET', 'OPTIONS'])
def get_products():
    if request.method == 'OPTIONS':
        return '', 200
    
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
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'success': False}), 404
    
    if 'sellingPrice' in data:
        product.selling_price = data['sellingPrice']
    db.session.commit()
    return jsonify({'success': True}), 200

@app.route('/api/products/<int:product_id>', methods=['DELETE', 'OPTIONS'])
def delete_product(product_id):
    if request.method == 'OPTIONS':
        return '', 200
    
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
    product = Product.query.get(data['productId'])
    if not product:
        return jsonify({'success': False}), 404
    
    product.stock += data['quantity']
    if data.get('newPrice') and data['newPrice'] > 0:
        product.selling_price = data['newPrice']
    db.session.commit()
    return jsonify({'success': True}), 200

# ============ CATEGORIES ENDPOINTS ============
@app.route('/api/categories', methods=['GET', 'OPTIONS'])
def get_categories():
    if request.method == 'OPTIONS':
        return '', 200
    
    categories = db.session.query(Product.category).distinct().all()
    cats = [c[0] for c in categories if c[0]]
    if not cats:
        cats = ['Vyakula', 'Dawa', 'Nguo', 'Vifaa', 'Vinywaji', 'Vipodozi', 'Electronics']
    return jsonify(cats), 200

@app.route('/api/categories', methods=['POST', 'OPTIONS'])
def add_category():
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({'success': True}), 201

@app.route('/api/categories/<string:name>', methods=['DELETE', 'OPTIONS'])
def delete_category(name):
    if request.method == 'OPTIONS':
        return '', 200
    
    products = Product.query.filter_by(category=name).all()
    if products:
        return jsonify({'success': False, 'message': 'Category ina bidhaa'}), 400
    return jsonify({'success': True}), 200

# ============ CUSTOMERS ENDPOINTS ============
@app.route('/api/customers', methods=['GET', 'OPTIONS'])
def get_customers():
    if request.method == 'OPTIONS':
        return '', 200
    
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
    
    for item in data['items']:
        sale_item = SaleItem(
            sale_id=sale.id,
            product_name=item['productName'],
            quantity=item['quantity'],
            price=item['price'],
            total=item['total']
        )
        db.session.add(sale_item)
        
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
    
    if email == 'malabamalaba26@gmail.com':
        return jsonify({'success': False, 'message': 'Hauwezi kufuta admin!'}), 400
    
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
    
    today = datetime.now().date()
    today_sales = Sale.query.filter(db.func.date(Sale.date) == today).all()
    
    today_revenue = sum(s.total for s in today_sales)
    today_profit = sum(s.profit for s in today_sales)
    
    products = Product.query.all()
    stock_value = sum(p.stock * p.selling_price for p in products)
    total_cost = sum(p.stock * p.cost_price for p in products)
    expected_profit = stock_value - total_cost
    low_stock_count = sum(1 for p in products if p.stock <= p.alert_level)
    
    return jsonify({
        'todayRevenue': today_revenue,
        'todayProfit': today_profit,
        'stockValue': stock_value,
        'expectedProfit': expected_profit,
        'lowStockCount': low_stock_count
    }), 200

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 SMART POS BACKEND - READY")
    print("=" * 50)
    print("📍 Server: http://localhost:5000")
    print("📊 Health: GET /health")
    print("🔐 Login: POST /api/auth/login")
    print("📋 Products: GET /api/products")
    print("=" * 50)
    print("✅ Admin Email: malabamalaba26@gmail.com")
    print("✅ Admin Password: Malaba@03")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
