from flask import Blueprint, request, jsonify
from src.models.user import db, User
from src.models.transaction import Transaction
from src.models.operator import Operator
from datetime import datetime
import json

transaction_bp = Blueprint('transaction', __name__)

@transaction_bp.route('/transactions', methods=['GET'])
def get_transactions():
    """Получить все транзакции пользователя"""
    try:
        telegram_id = request.args.get('telegram_id')
        if not telegram_id:
            return jsonify({'error': 'telegram_id is required'}), 400
        
        user = User.query.filter_by(telegram_id=int(telegram_id)).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Получаем транзакции с пагинацией
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        transactions = Transaction.query.filter_by(user_id=user.id, is_deleted=False)\
            .order_by(Transaction.date_time.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'transactions': [t.to_dict() for t in transactions.items],
            'total': transactions.total,
            'pages': transactions.pages,
            'current_page': page
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transaction_bp.route('/transactions', methods=['POST'])
def create_transaction():
    """Создать новую транзакцию"""
    try:
        data = request.get_json()
        
        # Проверяем обязательные поля
        required_fields = ['telegram_id', 'date_time', 'operation_type', 'amount', 'raw_text']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Получаем или создаем пользователя
        user = User.get_or_create_user(data['telegram_id'], data.get('username'))
        
        # Проверяем дубликаты
        existing = Transaction.query.filter_by(
            user_id=user.id,
            raw_text=data['raw_text']
        ).first()
        
        if existing:
            return jsonify({'error': 'Duplicate transaction', 'transaction': existing.to_dict()}), 409
        
        # Ищем оператора
        operator = None
        if 'description' in data and data['description']:
            operator = Operator.find_operator_by_description(data['description'], user.id)
        
        # Создаем транзакцию
        transaction = Transaction(
            user_id=user.id,
            date_time=datetime.fromisoformat(data['date_time'].replace('Z', '+00:00')),
            operation_type=data['operation_type'],
            amount=float(data['amount']),
            currency=data.get('currency', 'UZS'),
            card_number=data.get('card_number'),
            description=data.get('description'),
            balance=float(data['balance']) if data.get('balance') else None,
            operator_id=operator.id if operator else None,
            raw_text=data['raw_text']
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({'transaction': transaction.to_dict()}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@transaction_bp.route('/transactions/<int:transaction_id>', methods=['PUT'])
def update_transaction(transaction_id):
    """Обновить транзакцию"""
    try:
        data = request.get_json()
        telegram_id = data.get('telegram_id')
        
        if not telegram_id:
            return jsonify({'error': 'telegram_id is required'}), 400
        
        user = User.query.filter_by(telegram_id=int(telegram_id)).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        transaction = Transaction.query.filter_by(id=transaction_id, user_id=user.id).first()
        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404
        
        # Обновляем поля
        if 'date_time' in data:
            transaction.date_time = datetime.fromisoformat(data['date_time'].replace('Z', '+00:00'))
        if 'operation_type' in data:
            transaction.operation_type = data['operation_type']
        if 'amount' in data:
            transaction.amount = float(data['amount'])
        if 'currency' in data:
            transaction.currency = data['currency']
        if 'card_number' in data:
            transaction.card_number = data['card_number']
        if 'description' in data:
            transaction.description = data['description']
            # Обновляем оператора
            operator = Operator.find_operator_by_description(data['description'], user.id)
            transaction.operator_id = operator.id if operator else None
        if 'balance' in data:
            transaction.balance = float(data['balance']) if data['balance'] else None
        
        db.session.commit()
        
        return jsonify({'transaction': transaction.to_dict()})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@transaction_bp.route('/transactions/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    """Удалить транзакцию"""
    try:
        telegram_id = request.args.get('telegram_id')
        if not telegram_id:
            return jsonify({'error': 'telegram_id is required'}), 400
        
        user = User.query.filter_by(telegram_id=int(telegram_id)).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        transaction = Transaction.query.filter_by(id=transaction_id, user_id=user.id).first()
        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404
        
        db.session.delete(transaction)
        db.session.commit()
        
        return jsonify({'message': 'Transaction deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@transaction_bp.route('/transactions/export', methods=['GET'])
def export_transactions():
    """Экспорт транзакций в Excel"""
    try:
        telegram_id = request.args.get('telegram_id')
        if not telegram_id:
            return jsonify({'error': 'telegram_id is required'}), 400
        
        user = User.query.filter_by(telegram_id=int(telegram_id)).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        transactions = Transaction.query.filter_by(user_id=user.id, is_deleted=False)\
            .order_by(Transaction.date_time.desc()).all()
        
        # Возвращаем данные для экспорта
        export_data = []
        for t in transactions:
            export_data.append({
                'Дата': t.date_time.strftime('%d.%m.%Y %H:%M') if t.date_time else '',
                'Тип операции': t.operation_type,
                'Сумма': float(t.amount) if t.amount else 0,
                'Валюта': t.currency,
                'Номер карты': t.card_number or '',
                'Описание': t.description or '',
                'Баланс': float(t.balance) if t.balance else 0,
                'Оператор': t.operator.name if t.operator else '',
                'Приложение': t.operator.description if t.operator else ''
            })
        
        return jsonify({'data': export_data})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

