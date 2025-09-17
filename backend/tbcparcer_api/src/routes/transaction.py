from datetime import datetime

from flask import Blueprint, jsonify, request

from src.models.operator import Operator
from src.models.transaction import Transaction
from src.models.user import User, db
from src.services.manual_transaction import (
    ManualTransactionError,
    create_manual_transaction,
)
from src.utils.errors import APIError

transaction_bp = Blueprint('transaction', __name__)

@transaction_bp.route('/transactions', methods=['GET'])
def get_transactions():
    """Получить все транзакции пользователя"""
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

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    transactions = (
        Transaction.query.filter_by(user_id=user.id, is_deleted=False)
        .order_by(Transaction.date_time.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return jsonify(
        {
            'transactions': [t.to_dict() for t in transactions.items],
            'total': transactions.total,
            'pages': transactions.pages,
            'current_page': page,
        }
    )

@transaction_bp.route('/transactions', methods=['POST'])
def create_transaction():
    """Создать новую транзакцию"""
    data = request.get_json() or {}

    try:
        transaction, context = create_manual_transaction(data)
    except ManualTransactionError:
        db.session.rollback()
        raise
    except Exception as exc:  # pragma: no cover - unexpected failure
        db.session.rollback()
        raise APIError(500, 'Failed to create transaction', details={'reason': str(exc)})

    transaction_dict = transaction.to_dict()

    if context.generated_raw_text:
        transaction_dict['data_source'] = 'Manual form'

    return jsonify({'transaction': transaction_dict}), 201

@transaction_bp.route('/transactions/<int:transaction_id>', methods=['PUT'])
def update_transaction(transaction_id):
    """Обновить транзакцию"""
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

    transaction = Transaction.query.filter_by(id=transaction_id, user_id=user.id).first()
    if not transaction:
        raise APIError(404, 'Transaction not found', error='Not Found')

    try:
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
            operator = Operator.find_operator_by_description(data['description'], user.id)
            transaction.operator_id = operator.id if operator else None
        if 'balance' in data:
            transaction.balance = float(data['balance']) if data['balance'] else None

        db.session.commit()
    except Exception as exc:  # pragma: no cover - conversion guards
        db.session.rollback()
        raise APIError(400, 'Invalid transaction payload', details={'reason': str(exc)})

    return jsonify({'transaction': transaction.to_dict()})

@transaction_bp.route('/transactions/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    """Удалить транзакцию"""
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

    transaction = Transaction.query.filter_by(id=transaction_id, user_id=user.id).first()
    if not transaction:
        raise APIError(404, 'Transaction not found', error='Not Found')

    db.session.delete(transaction)
    db.session.commit()

    return jsonify({'message': 'Transaction deleted successfully'})

@transaction_bp.route('/transactions/export', methods=['GET'])
def export_transactions():
    """Экспорт транзакций в Excel"""
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

    transactions = (
        Transaction.query.filter_by(user_id=user.id, is_deleted=False)
        .order_by(Transaction.date_time.desc())
        .all()
    )

    export_data = [
        {
            'Дата': t.date_time.strftime('%d.%m.%Y %H:%M') if t.date_time else '',
            'Тип операции': t.operation_type,
            'Сумма': float(t.amount) if t.amount else 0,
            'Валюта': t.currency,
            'Номер карты': t.card_number or '',
            'Описание': t.description or '',
            'Баланс': float(t.balance) if t.balance else 0,
            'Оператор': t.operator.name if t.operator else '',
            'Приложение': t.operator.description if t.operator else '',
        }
        for t in transactions
    ]

    return jsonify({'data': export_data})

