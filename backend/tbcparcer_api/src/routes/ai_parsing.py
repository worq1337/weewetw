from datetime import datetime
from typing import List, Optional

from flask import Blueprint, jsonify, request

from src.models.operator import Operator
from src.models.transaction import Transaction
from src.models.user import User, db
from src.services.ai_parser import AIParsingService

ai_parsing_bp = Blueprint('ai_parsing', __name__)
_ai_service: Optional[AIParsingService] = None


def _get_ai_service() -> AIParsingService:
    """Ленивая инициализация сервиса парсинга."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIParsingService()
    return _ai_service


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """Преобразовать строку с датой в объект datetime."""
    if not value:
        return None

    normalized = value.replace('T', ' ').replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        pass

    for fmt in ('%Y-%m-%d %H:%M:%S', '%d.%m.%Y %H:%M:%S', '%Y-%m-%d %H:%M'):
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            continue

    return None


def _to_float(value) -> Optional[float]:
    """Безопасно конвертировать значение в float."""
    if value in (None, ''):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _load_operators_for_user(user: Optional[User]) -> List[Operator]:
    """Получить список операторов для пользователя или глобальные."""
    if user:
        return Operator.get_operators_for_user(user.id)
    return Operator.get_global_operators()

@ai_parsing_bp.route('/parse', methods=['POST'])
def parse_receipt():
    """Парсинг одного чека через AI"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Отсутствует текст чека'}), 400
        
        receipt_text = data['text']
        telegram_id = data.get('telegram_id')
        
        if not receipt_text.strip():
            return jsonify({'error': 'Пустой текст чека'}), 400
        
        try:
            ai_service = _get_ai_service()
        except RuntimeError as config_error:
            return jsonify({'error': str(config_error)}), 503

        # Парсим чек через AI
        parsed_data = ai_service.parse_receipt(receipt_text)

        if 'error' in parsed_data:
            return jsonify(parsed_data), 400

        # Получаем операторов для обогащения данных
        user = None
        if telegram_id:
            try:
                user = User.query.filter_by(telegram_id=int(telegram_id)).first()
            except (TypeError, ValueError):
                return jsonify({'error': 'Некорректный telegram_id'}), 400

        operators = _load_operators_for_user(user)

        # Обогащаем данные информацией об операторе
        enhanced_data = ai_service.enhance_with_operator_info(parsed_data, operators)

        return jsonify({
            'success': True,
            'parsed_data': enhanced_data
        })
    
    except Exception as e:
        return jsonify({'error': f'Ошибка при парсинге: {str(e)}'}), 500

@ai_parsing_bp.route('/parse-and-save', methods=['POST'])
def parse_and_save_receipt():
    """Парсинг чека и сохранение в базу данных"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data or 'telegram_id' not in data:
            return jsonify({'error': 'Отсутствует текст чека или telegram_id'}), 400
        
        receipt_text = data['text']
        telegram_id = data['telegram_id']
        
        if not receipt_text.strip():
            return jsonify({'error': 'Пустой текст чека'}), 400
        
        try:
            telegram_id_int = int(telegram_id)
        except (TypeError, ValueError):
            return jsonify({'error': 'Некорректный telegram_id'}), 400

        # Получаем или создаем пользователя
        user = User.get_or_create_user(telegram_id_int, data.get('username'))

        # Проверяем на дубликат по исходному тексту
        existing_transaction = Transaction.query.filter_by(
            user_id=user.id,
            raw_text=receipt_text
        ).first()

        if existing_transaction:
            return jsonify({'error': 'Duplicate transaction detected'}), 409

        # Парсим чек через AI
        try:
            ai_service = _get_ai_service()
        except RuntimeError as config_error:
            return jsonify({'error': str(config_error)}), 503

        parsed_data = ai_service.parse_receipt(receipt_text)

        if 'error' in parsed_data:
            return jsonify(parsed_data), 400

        # Получаем операторов для обогащения данных
        operators = _load_operators_for_user(user)

        # Обогащаем данные информацией об операторе
        enhanced_data = ai_service.enhance_with_operator_info(parsed_data, operators)

        parsed_datetime = _parse_datetime(enhanced_data.get('date_time'))
        if not parsed_datetime:
            return jsonify({'error': 'Неверный формат даты операции'}), 400

        amount = _to_float(enhanced_data.get('amount'))
        if amount is None:
            return jsonify({'error': 'Неверный формат суммы операции'}), 400

        balance = _to_float(enhanced_data.get('balance'))

        operator_id = enhanced_data.get('operator_id')
        if not operator_id and enhanced_data.get('description'):
            operator = Operator.find_operator_by_description(
                enhanced_data['description'],
                user.id
            )
            operator_id = operator.id if operator else None

        transaction = Transaction(
            user_id=user.id,
            date_time=parsed_datetime,
            operation_type=enhanced_data.get('operation_type', 'payment'),
            amount=amount,
            currency=enhanced_data.get('currency', 'UZS'),
            card_number=enhanced_data.get('card_number'),
            description=enhanced_data.get('description'),
            balance=balance,
            operator_id=operator_id,
            raw_text=receipt_text
        )

        db.session.add(transaction)
        db.session.commit()

        transaction_dict = transaction.to_dict()
        transaction_dict['data_source'] = 'AI Parser'

        return jsonify({
            'success': True,
            'transaction': transaction_dict,
            'parsed_data': enhanced_data
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Ошибка при парсинге и сохранении: {str(e)}'}), 500

@ai_parsing_bp.route('/batch-parse', methods=['POST'])
def batch_parse_receipts():
    """Пакетная обработка чеков"""
    try:
        data = request.get_json()
        
        if not data or 'receipts' not in data:
            return jsonify({'error': 'Отсутствует список чеков'}), 400
        
        receipts_list = data['receipts']
        telegram_id = data.get('telegram_id')
        
        if not isinstance(receipts_list, list):
            return jsonify({'error': 'Список чеков должен быть массивом'}), 400
        
        if len(receipts_list) > 50:  # Ограничение на количество
            return jsonify({'error': 'Максимум 50 чеков за раз'}), 400
        
        user = None
        if telegram_id:
            try:
                user = User.query.filter_by(telegram_id=int(telegram_id)).first()
            except (TypeError, ValueError):
                return jsonify({'error': 'Некорректный telegram_id'}), 400

        operators = _load_operators_for_user(user)

        # Пакетная обработка
        try:
            ai_service = _get_ai_service()
        except RuntimeError as config_error:
            return jsonify({'error': str(config_error)}), 503

        results = ai_service.batch_parse_receipts(receipts_list)

        # Обогащаем каждый результат
        enhanced_results = []
        for result in results:
            if 'error' not in result:
                enhanced_result = ai_service.enhance_with_operator_info(result, operators)
                enhanced_results.append(enhanced_result)
            else:
                enhanced_results.append(result)
        
        return jsonify({
            'success': True,
            'results': enhanced_results,
            'total_processed': len(receipts_list),
            'successful': len([r for r in enhanced_results if 'error' not in r]),
            'failed': len([r for r in enhanced_results if 'error' in r])
        })
    
    except Exception as e:
        return jsonify({'error': f'Ошибка при пакетной обработке: {str(e)}'}), 500

@ai_parsing_bp.route('/validate', methods=['POST'])
def validate_parsed_data():
    """Валидация распарсенных данных"""
    try:
        data = request.get_json()
        
        if not data or 'parsed_data' not in data:
            return jsonify({'error': 'Отсутствуют данные для валидации'}), 400
        
        parsed_data = data['parsed_data']
        
        try:
            ai_service = _get_ai_service()
        except RuntimeError as config_error:
            return jsonify({'error': str(config_error)}), 503

        # Валидируем данные
        validation_result = ai_service.validate_receipt_data(parsed_data)
        
        return jsonify({
            'success': True,
            'validation_result': validation_result
        })
    
    except Exception as e:
        return jsonify({'error': f'Ошибка при валидации: {str(e)}'}), 500

