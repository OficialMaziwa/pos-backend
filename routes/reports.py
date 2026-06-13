from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import Sale, SaleItem, Product
from utils.database import db
from datetime import datetime, timedelta
from sqlalchemy import func, extract

bp = Blueprint('reports', __name__)

@bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    """Get dashboard data"""
    today = datetime.now().date()
    
    # Today's sales
    today_sales = Sale.query.filter(func.date(Sale.sale_date) == today).all()
    today_revenue = sum(float(s.total_amount) for s in today_sales)
    
    # Total products
    total_products = Product.query.filter_by(is_active=True).count()
    
    # Low stock
    low_stock = Product.query.filter(Product.stock_quantity <= Product.reorder_level).count()
    
    # Total customers
    from models import Customer
    total_customers = Customer.query.count()
    
    # Recent sales
    recent_sales = Sale.query.order_by(Sale.sale_date.desc()).limit(5).all()
    
    return jsonify({
        'today': {'revenue': float(today_revenue), 'sales_count': len(today_sales)},
        'counts': {
            'total_products': total_products,
            'low_stock_products': low_stock,
            'total_customers': total_customers
        },
        'recent_sales': [s.to_dict() for s in recent_sales]
    }), 200

@bp.route('/best-sellers', methods=['GET'])
@jwt_required()
def best_sellers():
    """Get best selling products"""
    limit = request.args.get('limit', 10, type=int)
    
    results = db.session.query(
        Product.name,
        func.sum(SaleItem.quantity).label('total_quantity'),
        func.sum(SaleItem.total_price).label('total_revenue')
    ).join(SaleItem, SaleItem.product_id == Product.id)\
     .group_by(Product.id)\
     .order_by(func.sum(SaleItem.quantity).desc())\
     .limit(limit).all()
    
    return jsonify({
        'products': [
            {'name': r[0], 'quantity': int(r[1]), 'revenue': float(r[2])}
            for r in results
        ]
    }), 200