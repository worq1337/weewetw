from flask import Blueprint, jsonify, request

from src.models.operator import Operator
from src.models.user import User, db
from src.utils.errors import APIError

operator_bp = Blueprint('operator', __name__)

@operator_bp.route('/operators', methods=['GET'])
def get_operators():
    """Получить операторов для пользователя (глобальные + персональные)"""
    telegram_id_raw = request.args.get('telegram_id')
    if not telegram_id_raw:
        operators = Operator.query.filter_by(user_id=None).all()
        return jsonify({'operators': [op.to_dict() for op in operators]})

    try:
        telegram_id = int(telegram_id_raw)
    except (TypeError, ValueError):
        raise APIError(400, 'telegram_id must be an integer', error='Bad Request')

    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        raise APIError(404, 'User not found', error='Not Found')

    operators = Operator.get_operators_for_user(user.id)
    return jsonify({'operators': [op.to_dict() for op in operators]})

@operator_bp.route('/operators', methods=['POST'])
def create_operator():
    """Создать персонального оператора"""
    data = request.get_json() or {}

    for field in ('telegram_id', 'name'):
        if field not in data:
            raise APIError(400, f'{field} is required', error='Bad Request')

    try:
        telegram_id = int(data['telegram_id'])
    except (TypeError, ValueError):
        raise APIError(400, 'telegram_id must be an integer', error='Bad Request')

    user = User.get_or_create_user(telegram_id, data.get('username'))

    existing = Operator.query.filter_by(
        user_id=user.id,
        name=data['name'],
    ).first()

    if existing:
        raise APIError(
            409,
            'Operator already exists',
            error='Conflict',
            details={'operator': existing.to_dict()},
        )

    operator = Operator(
        name=data['name'],
        description=data.get('description'),
        user_id=user.id,
    )

    db.session.add(operator)
    try:
        db.session.commit()
    except Exception as exc:  # pragma: no cover - db integrity guard
        db.session.rollback()
        raise APIError(500, 'Failed to create operator', details={'reason': str(exc)})

    return jsonify({'operator': operator.to_dict()}), 201

@operator_bp.route('/operators/<int:operator_id>', methods=['PUT'])
def update_operator(operator_id):
    """Обновить персонального оператора"""
    data = request.get_json() or {}
    telegram_id_raw = data.get('telegram_id')

    if not telegram_id_raw:
        raise APIError(400, 'telegram_id is required', error='Bad Request')

    try:
        telegram_id = int(telegram_id_raw)
    except (TypeError, ValueError):
        raise APIError(400, 'telegram_id must be an integer', error='Bad Request')

    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        raise APIError(404, 'User not found', error='Not Found')

    operator = Operator.query.filter_by(id=operator_id, user_id=user.id).first()
    if not operator:
        raise APIError(404, 'Operator not found or not owned by user', error='Not Found')

    if 'name' in data:
        operator.name = data['name']
    if 'description' in data:
        operator.description = data['description']

    db.session.commit()

    return jsonify({'operator': operator.to_dict()})

@operator_bp.route('/operators/<int:operator_id>', methods=['DELETE'])
def delete_operator(operator_id):
    """Удалить персонального оператора"""
    telegram_id_raw = request.args.get('telegram_id')
    if not telegram_id_raw:
        raise APIError(400, 'telegram_id is required', error='Bad Request')

    try:
        telegram_id = int(telegram_id_raw)
    except (TypeError, ValueError):
        raise APIError(400, 'telegram_id must be an integer', error='Bad Request')

    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        raise APIError(404, 'User not found', error='Not Found')

    operator = Operator.query.filter_by(id=operator_id, user_id=user.id).first()
    if not operator:
        raise APIError(404, 'Operator not found or not owned by user', error='Not Found')

    db.session.delete(operator)
    db.session.commit()

    return jsonify({'message': 'Operator deleted successfully'})

@operator_bp.route('/operators/<int:operator_id>/copy', methods=['POST'])
def copy_operator(operator_id):
    """Скопировать глобального оператора в персональные"""
    data = request.get_json() or {}
    telegram_id_raw = data.get('telegram_id')

    if not telegram_id_raw:
        raise APIError(400, 'telegram_id is required', error='Bad Request')

    try:
        telegram_id = int(telegram_id_raw)
    except (TypeError, ValueError):
        raise APIError(400, 'telegram_id must be an integer', error='Bad Request')

    user = User.get_or_create_user(telegram_id, data.get('username'))

    global_operator = Operator.query.filter_by(id=operator_id, user_id=None).first()
    if not global_operator:
        raise APIError(404, 'Global operator not found', error='Not Found')

    existing = Operator.query.filter_by(
        user_id=user.id,
        name=global_operator.name,
    ).first()

    if existing:
        raise APIError(
            409,
            'Operator already copied',
            error='Conflict',
            details={'operator': existing.to_dict()},
        )

    personal_operator = Operator(
        name=global_operator.name,
        description=global_operator.description,
        user_id=user.id,
    )

    db.session.add(personal_operator)
    try:
        db.session.commit()
    except Exception as exc:  # pragma: no cover - integrity guard
        db.session.rollback()
        raise APIError(500, 'Failed to copy operator', details={'reason': str(exc)})

    return jsonify({'operator': personal_operator.to_dict()}), 201

