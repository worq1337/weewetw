"""Routes that expose AI parsing capabilities via HTTP API."""

from __future__ import annotations

from typing import Optional, Sequence

from flask import Blueprint, jsonify, request

from src.models.user import User, db
from src.services.receipt_pipeline import (
    DuplicateTransactionError,
    ReceiptPipeline,
    ReceiptProcessingError,
)

ai_parsing_bp = Blueprint('ai_parsing', __name__)
_pipeline: Optional[ReceiptPipeline] = None


def _get_pipeline() -> ReceiptPipeline:
    """Lazy pipeline initialisation so we reuse heavy resources."""
    global _pipeline
    if _pipeline is None:
        _pipeline = ReceiptPipeline()
    return _pipeline


def _parse_optional_telegram_id(raw_value) -> Optional[int]:
    """Convert incoming telegram id into integer or return None."""
    if raw_value in (None, ''):
        return None
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        raise ReceiptProcessingError('Некорректный telegram_id', status_code=400)


@ai_parsing_bp.route('/parse', methods=['POST'])
def parse_receipt():
    """Parse a single receipt without saving it to the database."""
    try:
        data = request.get_json() or {}
        if 'text' not in data:
            return jsonify({'error': 'Отсутствует текст чека'}), 400

        receipt_text = str(data['text'])
        if not receipt_text.strip():
            return jsonify({'error': 'Пустой текст чека'}), 400

        telegram_id = data.get('telegram_id')
        pipeline = _get_pipeline()

        try:
            telegram_id_value = _parse_optional_telegram_id(telegram_id)
            enhanced_data, _ = pipeline.parse_receipt(receipt_text, telegram_id_value)
        except ReceiptProcessingError as pipeline_error:
            return jsonify({'error': str(pipeline_error)}), pipeline_error.status_code

        return jsonify({'success': True, 'parsed_data': enhanced_data})

    except ReceiptProcessingError as pipeline_error:
        return jsonify({'error': str(pipeline_error)}), pipeline_error.status_code
    except Exception as error:  # pragma: no cover - defensive guard
        return jsonify({'error': f'Ошибка при парсинге: {error}'}), 500


@ai_parsing_bp.route('/parse-and-save', methods=['POST'])
def parse_and_save_receipt():
    """Parse a receipt and persist the transaction for the user."""
    try:
        data = request.get_json() or {}
        if 'text' not in data or 'telegram_id' not in data:
            return jsonify({'error': 'Отсутствует текст чека или telegram_id'}), 400

        receipt_text = str(data['text'])
        if not receipt_text.strip():
            return jsonify({'error': 'Пустой текст чека'}), 400

        try:
            telegram_id_int = _parse_optional_telegram_id(data['telegram_id'])
        except ReceiptProcessingError as parse_error:
            return jsonify({'error': str(parse_error)}), parse_error.status_code

        if telegram_id_int is None:
            return jsonify({'error': 'Не указан telegram_id'}), 400

        pipeline = _get_pipeline()

        try:
            transaction, enhanced_data = pipeline.parse_and_store_receipt(
                receipt_text,
                telegram_id_int,
                data.get('username'),
            )
        except DuplicateTransactionError as duplicate_error:
            return jsonify({
                'error': str(duplicate_error),
                'transaction': duplicate_error.transaction.to_dict(),
            }), duplicate_error.status_code
        except ReceiptProcessingError as pipeline_error:
            return jsonify({'error': str(pipeline_error)}), pipeline_error.status_code

        transaction_dict = transaction.to_dict()
        transaction_dict['data_source'] = 'AI Parser'

        return jsonify({
            'success': True,
            'transaction': transaction_dict,
            'parsed_data': enhanced_data,
        })

    except ReceiptProcessingError as pipeline_error:
        db.session.rollback()
        return jsonify({'error': str(pipeline_error)}), pipeline_error.status_code
    except Exception as error:  # pragma: no cover - defensive guard
        db.session.rollback()
        return jsonify({'error': f'Ошибка при парсинге и сохранении: {error}'}), 500


@ai_parsing_bp.route('/batch-parse', methods=['POST'])
def batch_parse_receipts():
    """Parse multiple receipts in a single request."""
    try:
        data = request.get_json() or {}
        if 'receipts' not in data:
            return jsonify({'error': 'Отсутствует список чеков'}), 400

        receipts_list = data['receipts']
        if not isinstance(receipts_list, list):
            return jsonify({'error': 'Список чеков должен быть массивом'}), 400
        if len(receipts_list) > 50:
            return jsonify({'error': 'Максимум 50 чеков за раз'}), 400

        pipeline = _get_pipeline()
        telegram_id_value = None
        user: Optional[User] = None

        if 'telegram_id' in data:
            try:
                telegram_id_value = _parse_optional_telegram_id(data['telegram_id'])
            except ReceiptProcessingError as parse_error:
                return jsonify({'error': str(parse_error)}), parse_error.status_code

        if telegram_id_value is not None:
            user = User.query.filter_by(telegram_id=telegram_id_value).first()

        operators: Sequence = pipeline.get_operators_for_user(user)
        ai_service = pipeline.parser

        results = ai_service.batch_parse_receipts(receipts_list)
        enhanced_results = []
        for result in results:
            if 'error' in result:
                enhanced_results.append(result)
                continue
            enhanced_results.append(
                ai_service.enhance_with_operator_info(result, operators)
            )

        return jsonify({
            'success': True,
            'results': enhanced_results,
            'total_processed': len(receipts_list),
            'successful': len([r for r in enhanced_results if 'error' not in r]),
            'failed': len([r for r in enhanced_results if 'error' in r]),
        })

    except ReceiptProcessingError as pipeline_error:
        return jsonify({'error': str(pipeline_error)}), pipeline_error.status_code
    except Exception as error:  # pragma: no cover - defensive guard
        return jsonify({'error': f'Ошибка при пакетной обработке: {error}'}), 500


@ai_parsing_bp.route('/validate', methods=['POST'])
def validate_parsed_data():
    """Validate parsed payload and return validation result."""
    try:
        data = request.get_json() or {}
        if 'parsed_data' not in data:
            return jsonify({'error': 'Отсутствуют данные для валидации'}), 400

        pipeline = _get_pipeline()
        ai_service = pipeline.parser
        validation_result = ai_service.validate_receipt_data(data['parsed_data'])

        return jsonify({'success': True, 'validation_result': validation_result})

    except ReceiptProcessingError as pipeline_error:
        return jsonify({'error': str(pipeline_error)}), pipeline_error.status_code
    except Exception as error:  # pragma: no cover - defensive guard
        return jsonify({'error': f'Ошибка при валидации: {error}'}), 500

