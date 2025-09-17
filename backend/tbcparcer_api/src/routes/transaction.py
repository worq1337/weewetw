from flask import Blueprint, request, jsonify
from src.models.user import db, User
from src.models.transaction import Transaction
from src.models.operator import Operator
from datetime import datetime
from src.services.manual_transaction import (
    ManualTransactionError,
    create_manual_transaction,
)

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
    data = request.get_json() or {}

    try:
        transaction, context = create_manual_transaction(data)
        transaction_dict = transaction.to_dict()

        if context.generated_raw_text:
            transaction_dict['data_source'] = 'Manual form'

        return jsonify({'transaction': transaction_dict}), 201

    except ManualTransactionError as validation_error:
        db.session.rollback()
        response_body = {'error': str(validation_error)}
        if validation_error.extra:
            response_body.update(validation_error.extra)
        return jsonify(response_body), validation_error.status_code
    except Exception as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 500

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
            parsed_datetime = datetime.fromisoformat(data['date_time'].replace('Z', '+00:00'))
            transaction.date_time = parsed_datetime.replace(second=0, microsecond=0)
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

