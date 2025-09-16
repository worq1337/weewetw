from flask import Blueprint, request, jsonify
from src.models.user import db, User
from src.models.operator import Operator

operator_bp = Blueprint('operator', __name__)

@operator_bp.route('/operators', methods=['GET'])
def get_operators():
    """Получить операторов для пользователя (глобальные + персональные)"""
    try:
        telegram_id = request.args.get('telegram_id')
        if not telegram_id:
            # Возвращаем только глобальные операторы
            operators = Operator.query.filter_by(user_id=None).all()
            return jsonify({'operators': [op.to_dict() for op in operators]})
        
        user = User.query.filter_by(telegram_id=int(telegram_id)).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        operators = Operator.get_operators_for_user(user.id)
        return jsonify({'operators': [op.to_dict() for op in operators]})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@operator_bp.route('/operators', methods=['POST'])
def create_operator():
    """Создать персонального оператора"""
    try:
        data = request.get_json()
        
        # Проверяем обязательные поля
        required_fields = ['telegram_id', 'name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Получаем или создаем пользователя
        user = User.get_or_create_user(data['telegram_id'], data.get('username'))
        
        # Проверяем, нет ли уже такого персонального оператора
        existing = Operator.query.filter_by(
            user_id=user.id,
            name=data['name']
        ).first()
        
        if existing:
            return jsonify({'error': 'Operator already exists', 'operator': existing.to_dict()}), 409
        
        # Создаем оператора
        operator = Operator(
            name=data['name'],
            description=data.get('description'),
            user_id=user.id
        )
        
        db.session.add(operator)
        db.session.commit()
        
        return jsonify({'operator': operator.to_dict()}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@operator_bp.route('/operators/<int:operator_id>', methods=['PUT'])
def update_operator(operator_id):
    """Обновить персонального оператора"""
    try:
        data = request.get_json()
        telegram_id = data.get('telegram_id')
        
        if not telegram_id:
            return jsonify({'error': 'telegram_id is required'}), 400
        
        user = User.query.filter_by(telegram_id=int(telegram_id)).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        operator = Operator.query.filter_by(id=operator_id, user_id=user.id).first()
        if not operator:
            return jsonify({'error': 'Operator not found or not owned by user'}), 404
        
        # Обновляем поля
        if 'name' in data:
            operator.name = data['name']
        if 'description' in data:
            operator.description = data['description']
        
        db.session.commit()
        
        return jsonify({'operator': operator.to_dict()})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@operator_bp.route('/operators/<int:operator_id>', methods=['DELETE'])
def delete_operator(operator_id):
    """Удалить персонального оператора"""
    try:
        telegram_id = request.args.get('telegram_id')
        if not telegram_id:
            return jsonify({'error': 'telegram_id is required'}), 400
        
        user = User.query.filter_by(telegram_id=int(telegram_id)).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        operator = Operator.query.filter_by(id=operator_id, user_id=user.id).first()
        if not operator:
            return jsonify({'error': 'Operator not found or not owned by user'}), 404
        
        db.session.delete(operator)
        db.session.commit()
        
        return jsonify({'message': 'Operator deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@operator_bp.route('/operators/<int:operator_id>/copy', methods=['POST'])
def copy_operator(operator_id):
    """Скопировать глобального оператора в персональные"""
    try:
        data = request.get_json()
        telegram_id = data.get('telegram_id')
        
        if not telegram_id:
            return jsonify({'error': 'telegram_id is required'}), 400
        
        user = User.get_or_create_user(telegram_id, data.get('username'))
        
        # Находим глобального оператора
        global_operator = Operator.query.filter_by(id=operator_id, user_id=None).first()
        if not global_operator:
            return jsonify({'error': 'Global operator not found'}), 404
        
        # Проверяем, нет ли уже такого персонального оператора
        existing = Operator.query.filter_by(
            user_id=user.id,
            name=global_operator.name
        ).first()
        
        if existing:
            return jsonify({'error': 'Operator already copied', 'operator': existing.to_dict()}), 409
        
        # Создаем копию
        personal_operator = Operator(
            name=global_operator.name,
            description=global_operator.description,
            user_id=user.id
        )
        
        db.session.add(personal_operator)
        db.session.commit()
        
        return jsonify({'operator': personal_operator.to_dict()}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

