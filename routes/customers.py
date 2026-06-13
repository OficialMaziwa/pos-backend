from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import Customer
from utils.database import db

bp = Blueprint('customers', __name__)

@bp.route('/', methods=['GET'])
@jwt_required()
def get_customers():
    customers = Customer.query.all()
    return jsonify({'customers': [c.to_dict() for c in customers]}), 200

@bp.route('/', methods=['POST'])
@jwt_required()
def create_customer():
    data = request.json
    customer = Customer(
        name=data['name'],
        phone=data.get('phone'),
        email=data.get('email'),
        address=data.get('address')
    )
    db.session.add(customer)
    db.session.commit()
    return jsonify({'message': 'Customer created', 'customer': customer.to_dict()}), 201