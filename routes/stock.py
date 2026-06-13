from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Product, StockMovement, User
from utils.database import db
from sqlalchemy import func

bp = Blueprint('stock', __name__)

@bp.route('/summary', methods=['GET'])
@jwt_required()
def get_stock_summary():
    """Get stock summary"""
    total_products = Product.query.filter_by(is_active=True).count()
    total_value = db.session.query(func.sum(Product.stock_quantity * Product.cost_price)).scalar() or 0
    low_stock_count = Product.query.filter(Product.stock_quantity <= Product.reorder_level).count()
    
    return jsonify({
        'total_products': total_products,
        'total_stock_value': float(total_value),
        'low_stock_count': low_stock_count
    }), 200

@bp.route('/movements', methods=['GET'])
@jwt_required()
def get_movements():
    """Get stock movements"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    movements = StockMovement.query.order_by(StockMovement.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'movements': [m.to_dict() for m in movements.items],
        'total': movements.total,
        'page': page,
        'pages': movements.pages
    }), 200

@bp.route('/adjust', methods=['POST'])
@jwt_required()
def adjust_stock():
    """Manual stock adjustment"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.json
    product = Product.query.get(data['product_id'])
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    old_quantity = product.stock_quantity
    new_quantity = data['new_quantity']
    quantity_change = new_quantity - old_quantity
    
    product.stock_quantity = new_quantity
    
    movement = StockMovement(
        product_id=product.id,
        quantity=abs(quantity_change),
        movement_type='adjustment',
        notes=f"Adjusted from {old_quantity} to {new_quantity}. Reason: {data.get('reason', '')}",
        created_by=user_id
    )
    
    db.session.add(movement)
    db.session.commit()
    
    return jsonify({'message': 'Stock adjusted', 'product': product.to_dict()}), 200