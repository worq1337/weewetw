from flask import Blueprint, request, jsonify
from src.models.user import db, User
from src.models.transaction import Transaction
from src.models.operator import Operator
from datetime import datetime

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
        data = request.get_json() or {}

        required_fields = ['telegram_id', 'date_time', 'operation_type', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400

        try:
            telegram_id = int(data['telegram_id'])
        except (TypeError, ValueError):
            return jsonify({'error': 'telegram_id must be an integer'}), 400

        operation_type = str(data['operation_type']).lower()
        allowed_operations = {'payment', 'refill', 'conversion', 'cancel'}
        if operation_type not in allowed_operations:
            return jsonify({'error': 'operation_type must be one of payment, refill, conversion, cancel'}), 400

        date_input = data['date_time']
        if not isinstance(date_input, str):
            return jsonify({'error': 'date_time must be a string'}), 400

        normalized_date = date_input.strip()
        if not normalized_date:
            return jsonify({'error': 'date_time is required'}), 400

        parsed_datetime = None
        try:
            parsed_datetime = datetime.fromisoformat(normalized_date.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid date_time format'}), 400

        if parsed_datetime.tzinfo:
            parsed_datetime = parsed_datetime.replace(tzinfo=None)

        try:
            amount_value = float(data['amount'])
        except (TypeError, ValueError):
            return jsonify({'error': 'amount must be a number'}), 400

        if amount_value <= 0:
            return jsonify({'error': 'amount must be greater than zero'}), 400

        balance_value = None
        if data.get('balance') not in (None, ''):
            try:
                balance_value = float(data['balance'])
            except (TypeError, ValueError):
                return jsonify({'error': 'balance must be a number'}), 400

        description = (data.get('description') or '').strip() or None
        raw_text = (data.get('raw_text') or '').strip()

        currency = str(data.get('currency', 'UZS')).upper()

        # Получаем или создаем пользователя
        user = User.get_or_create_user(telegram_id, data.get('username'))

        operator = None
        operator_id_value = data.get('operator_id')
        if operator_id_value not in (None, '', []):
            try:
                operator_id_int = int(operator_id_value)
            except (TypeError, ValueError):
                return jsonify({'error': 'operator_id must be an integer'}), 400

            operator = Operator.query.filter_by(id=operator_id_int).first()
            if not operator:
                return jsonify({'error': 'Operator not found'}), 404
            if operator.user_id and operator.user_id != user.id:
                return jsonify({'error': 'Operator does not belong to user'}), 403

        if operator is None and description:
            operator = Operator.find_operator_by_description(description, user.id)

        if not raw_text:
            raw_text_parts = [
                f'Manual entry: {parsed_datetime.strftime("%Y-%m-%d %H:%M")}',
                f'{amount_value:.2f} {currency}'
            ]
            if description:
                raw_text_parts.append(description)
            raw_text = ' — '.join(raw_text_parts)

        existing = Transaction.query.filter_by(
            user_id=user.id,
            raw_text=raw_text
        ).first()

        if existing:
            return jsonify({'error': 'Duplicate transaction', 'transaction': existing.to_dict()}), 409

        card_number = data.get('card_number')
        if card_number is not None:
            card_number = str(card_number).strip() or None

        transaction = Transaction(
            user_id=user.id,
            date_time=parsed_datetime,
            operation_type=operation_type,
            amount=amount_value,
            currency=currency,
            card_number=card_number,
            description=description,
            balance=balance_value,
            operator_id=operator.id if operator else None,
            raw_text=raw_text
        )

        db.session.add(transaction)
        db.session.commit()

        transaction_dict = transaction.to_dict()
        if not data.get('raw_text'):
            transaction_dict['data_source'] = 'Manual form'

        return jsonify({'transaction': transaction_dict}), 201
    
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

