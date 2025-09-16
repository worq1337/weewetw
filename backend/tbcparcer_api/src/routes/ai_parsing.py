from flask import Blueprint, request, jsonify
from src.services.ai_parser import AIParsingService
from src.models.operator import Operator
from src.models.transaction import Transaction
from src.models.user import User, db
import hashlib

ai_parsing_bp = Blueprint('ai_parsing', __name__)
# ai_service = AIParsingService()  # Временно отключено

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
        
        # Парсим чек через AI
        parsed_data = ai_service.parse_receipt(receipt_text)
        
        if 'error' in parsed_data:
            return jsonify(parsed_data), 400
        
        # Получаем операторов для обогащения данных
        if telegram_id:
            operators = Operator.get_user_operators(telegram_id)
        else:
            operators = Operator.get_global_operators()
        
        # Обогащаем данные информацией об операторе
        enhanced_data = ai_service.enhance_with_operator_info(
            parsed_data, 
            [op.to_dict() for op in operators]
        )
        
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
        
        # Получаем или создаем пользователя
        user = User.get_by_telegram_id(telegram_id)
        if not user:
            user = User.create(telegram_id=telegram_id)
        
        # Проверяем на дубликат по хешу
        text_hash = hashlib.md5(receipt_text.encode()).hexdigest()
        existing_transaction = Transaction.query.filter_by(
            user_id=user.id,
            text_hash=text_hash
        ).first()
        
        if existing_transaction:
            return jsonify({'error': 'Duplicate transaction detected'}), 409
        
        # Парсим чек через AI
        parsed_data = ai_service.parse_receipt(receipt_text)
        
        if 'error' in parsed_data:
            return jsonify(parsed_data), 400
        
        # Получаем операторов для обогащения данных
        operators = Operator.get_user_operators(telegram_id)
        
        # Обогащаем данные информацией об операторе
        enhanced_data = ai_service.enhance_with_operator_info(
            parsed_data, 
            [op.to_dict() for op in operators]
        )
        
        # Создаем транзакцию
        transaction_data = {
            'user_id': user.id,
            'date_time': enhanced_data.get('date_time'),
            'operation_type': enhanced_data.get('operation_type'),
            'amount': enhanced_data.get('amount'),
            'currency': enhanced_data.get('currency', 'UZS'),
            'card_number': enhanced_data.get('card_number'),
            'description': enhanced_data.get('description'),
            'balance': enhanced_data.get('balance'),
            'operator_name': enhanced_data.get('operator_name', enhanced_data.get('operator')),
            'operator_description': enhanced_data.get('operator_description'),
            'raw_text': receipt_text,
            'text_hash': text_hash,
            'ai_model': enhanced_data.get('ai_model', 'gpt-4o-mini'),
            'parsed_at': enhanced_data.get('parsed_at')
        }
        
        transaction = Transaction.create(**transaction_data)
        
        return jsonify({
            'success': True,
            'transaction': transaction.to_dict(),
            'parsed_data': enhanced_data
        })
    
    except Exception as e:
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
        
        # Получаем операторов для обогащения данных
        if telegram_id:
            operators = Operator.get_user_operators(telegram_id)
        else:
            operators = Operator.get_global_operators()
        
        operators_dict = [op.to_dict() for op in operators]
        
        # Пакетная обработка
        results = ai_service.batch_parse_receipts(receipts_list)
        
        # Обогащаем каждый результат
        enhanced_results = []
        for result in results:
            if 'error' not in result:
                enhanced_result = ai_service.enhance_with_operator_info(result, operators_dict)
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
        
        # Валидируем данные
        validation_result = ai_service.validate_receipt_data(parsed_data)
        
        return jsonify({
            'success': True,
            'validation_result': validation_result
        })
    
    except Exception as e:
        return jsonify({'error': f'Ошибка при валидации: {str(e)}'}), 500

