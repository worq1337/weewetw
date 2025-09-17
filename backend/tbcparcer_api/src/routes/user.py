from flask import Blueprint, jsonify, request

from src.models.user import User, db
from src.utils.errors import APIError

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json() or {}

    if 'telegram_id' not in data:
        raise APIError(400, 'telegram_id is required', error='Bad Request')

    try:
        telegram_id = int(data['telegram_id'])
    except (TypeError, ValueError):
        raise APIError(400, 'Invalid telegram_id value', error='Bad Request')

    username = data.get('username')
    user = User.query.filter_by(telegram_id=telegram_id).first()

    if user:
        if username and user.username != username:
            user.username = username
            db.session.commit()
        status_code = 200
    else:
        user = User(telegram_id=telegram_id, username=username)
        db.session.add(user)
        db.session.commit()
        status_code = 201

    return jsonify(user.to_dict()), status_code

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}

    if 'telegram_id' in data:
        try:
            new_telegram_id = int(data['telegram_id'])
        except (TypeError, ValueError):
            raise APIError(400, 'Invalid telegram_id value', error='Bad Request')

        existing_user = User.query.filter_by(telegram_id=new_telegram_id).first()
        if existing_user and existing_user.id != user.id:
            raise APIError(409, 'telegram_id already in use', error='Conflict')

        user.telegram_id = new_telegram_id

    if 'username' in data:
        user.username = data['username']

    db.session.commit()
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return '', 204
