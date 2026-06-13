from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Sale, SaleItem, Customer, Product, User
from utils.database import db
from datetime import datetime, date
from sqlalchemy import func
import uuid

bp = Blueprint('sales', __name__)

def generate_invoice_number():
    today = datetime.now().strftime('%Y%m%d')
    random_part = uuid.uuid4().hex[:6].upper()
    return f"INV-{today}-{random_part}"

@bp.route('/', methods=['POST'])
@jwt_required()
def record_sale():
    user_id = get_jwt_identity()
    data = request.json
    
    if not data.get('items') or len(data['items']) == 0:
        return jsonify({'error': 'Sale must have at least one item'}), 400
    
    invoice_no = generate_invoice_number()
    
    try:
        subtotal = 0
        sale_items_data = []
        
        for item in data['items']:
            product = Product.query.get(item['product_id'])
            if not product:
                return jsonify({'error': f'Product not found'}), 404
            
            if product.stock_quantity < item['quantity']:
                return jsonify({'error': f'Insufficient stock for {product.name}'}), 400
            
            item_total = float(product.selling_price) * item['quantity']
            subtotal += item_total
            
            sale_items_data.append({
                'product': product,
                'quantity': item['quantity'],
                'unit_price': float(product.selling_price),
                'total_price': item_total
            })
        
        vat = data.get('vat', 0)
        discount = data.get('discount', 0)
        total_amount = subtotal + vat - discount
        
        sale = Sale(
            invoice_no=invoice_no,
            customer_id=data.get('customer_id'),
            user_id=user_id,
            subtotal=subtotal,
            vat=vat,
            discount=discount,
            total_amount=total_amount,
            payment_method=data['payment_method']
        )
        
        db.session.add(sale)
        db.session.flush()
        
        for item_data in sale_items_data:
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=item_data['product'].id,
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                total_price=item_data['total_price']
            )
            db.session.add(sale_item)
            item_data['product'].stock_quantity -= item_data['quantity']
        
        if data.get('customer_id'):
            customer = Customer.query.get(data['customer_id'])
            if customer:
                customer.total_purchases = float(customer.total_purchases) + total_amount
        
        db.session.commit()
        
        return jsonify({
            'message': 'Sale recorded',
            'invoice_no': invoice_no,
            'sale_id': sale.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/', methods=['GET'])
@jwt_required()
def get_sales():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    paginated = Sale.query.order_by(Sale.sale_date.desc()).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'sales': [s.to_dict() for s in paginated.items],
        'total': paginated.total,
        'page': page,
        'pages': paginated.pages
    }), 200

@bp.route('/<int:sale_id>', methods=['GET'])
@jwt_required()
def get_sale(sale_id):
    sale = Sale.query.get(sale_id)
    if not sale:
        return jsonify({'error': 'Sale not found'}), 404
    return jsonify(sale.to_dict()), 200

@bp.route('/today', methods=['GET'])
@jwt_required()
def get_today_sales():
    today_date = date.today()
    total_sales = db.session.query(func.sum(Sale.total_amount)).filter(func.date(Sale.sale_date) == today_date).scalar() or 0
    transaction_count = db.session.query(func.count(Sale.id)).filter(func.date(Sale.sale_date) == today_date).scalar() or 0
    return jsonify({
        'date': today_date.isoformat(),
        'total_revenue': float(total_sales),
        'transaction_count': transaction_count
    }), 200