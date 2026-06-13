from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Product, User
from utils.database import db

bp = Blueprint('products', __name__)

@bp.route('/', methods=['GET'])
@jwt_required()
def get_products():
    """Get all products"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    
    query = Product.query.filter_by(is_active=True)
    
    if search:
        query = query.filter(
            db.or_(
                Product.name.ilike(f'%{search}%'),
                Product.sku.ilike(f'%{search}%'),
                Product.barcode.ilike(f'%{search}%')
            )
        )
    
    paginated = query.order_by(Product.name).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'products': [p.to_dict() for p in paginated.items],
        'total': paginated.total,
        'page': page,
        'pages': paginated.pages
    }), 200

@bp.route('/<int:product_id>', methods=['GET'])
@jwt_required()
def get_product(product_id):
    """Get single product"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify(product.to_dict()), 200

@bp.route('/', methods=['POST'])
@jwt_required()
def create_product():
    """Create new product"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.json
    
    product = Product(
        sku=data['sku'],
        barcode=data.get('barcode'),
        name=data['name'],
        category=data.get('category'),
        cost_price=data['cost_price'],
        selling_price=data['selling_price'],
        stock_quantity=data.get('stock_quantity', 0),
        reorder_level=data.get('reorder_level', 10)
    )
    
    db.session.add(product)
    db.session.commit()
    
    return jsonify({'message': 'Product created', 'product': product.to_dict()}), 201

@bp.route('/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    """Update product"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    data = request.json
    product.name = data.get('name', product.name)
    product.category = data.get('category', product.category)
    product.cost_price = data.get('cost_price', product.cost_price)
    product.selling_price = data.get('selling_price', product.selling_price)
    product.reorder_level = data.get('reorder_level', product.reorder_level)
    
    db.session.commit()
    
    return jsonify({'message': 'Product updated', 'product': product.to_dict()}), 200

@bp.route('/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    """Soft delete product"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    product.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'Product deleted'}), 200

@bp.route('/low-stock', methods=['GET'])
@jwt_required()
def get_low_stock():
    """Get low stock products"""
    products = Product.query.filter(
        Product.stock_quantity <= Product.reorder_level,
        Product.is_active == True
    ).all()
    
    return jsonify({'products': [p.to_dict() for p in products]}), 200