"""Routes responsible for exporting transaction data."""

from __future__ import annotations

import csv
import io
import os
import tempfile
from datetime import datetime
from typing import Iterable, Tuple

from flask import Blueprint, jsonify, request, send_file

from src.models.transaction import Transaction
from src.models.user import User
from src.services.excel_export import ExcelExportService
from src.utils.errors import APIError


export_bp = Blueprint('export', __name__)
excel_service = ExcelExportService()


def _resolve_user(payload) -> Tuple[User, int]:
    if 'telegram_id' not in payload:
        raise APIError(400, 'Отсутствует telegram_id', error='Bad Request')

    try:
        telegram_id = int(payload['telegram_id'])
    except (TypeError, ValueError):
        raise APIError(400, 'telegram_id должен быть числом', error='Bad Request')

    user = User.get_by_telegram_id(telegram_id)
    if not user:
        raise APIError(404, 'Пользователь не найден', error='Not Found')

    return user, telegram_id


def _extract_limit(payload) -> Tuple[str, int | None]:
    export_type = payload.get('export_type', 'all')
    limit_raw = payload.get('limit')

    if limit_raw in (None, '', []):
        return export_type, None

    try:
        return export_type, int(limit_raw)
    except (TypeError, ValueError):
        raise APIError(400, 'limit должен быть целым числом', error='Bad Request')


def _load_transactions(user_id: int, export_type: str, limit: int | None) -> Iterable[Transaction]:
    if export_type == 'latest' and limit:
        return Transaction.get_user_transactions(user_id, limit=limit)
    return Transaction.get_user_transactions(user_id)


def _ensure_transactions(transactions: Iterable[Transaction]):
    transactions_list = list(transactions)
    if not transactions_list:
        raise APIError(404, 'Нет данных для экспорта', error='Not Found')
    return transactions_list


@export_bp.route('/excel', methods=['POST'])
def export_to_excel():
    payload = request.get_json() or {}
    user, telegram_id = _resolve_user(payload)
    export_type, limit = _extract_limit(payload)

    transactions = _ensure_transactions(_load_transactions(user.id, export_type, limit))
    transactions_data = [transaction.to_dict() for transaction in transactions]
    excel_buffer = excel_service.export_transactions(transactions_data)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
        tmp_file.write(excel_buffer.getvalue())
        tmp_file_path = tmp_file.name

    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f"TBCparcer_transactions_{timestamp}.xlsx"

    def cleanup(response):
        try:
            os.unlink(tmp_file_path)
        except Exception:  # pragma: no cover - best effort cleanup
            pass
        return response

    response = send_file(
        tmp_file_path,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response.call_on_close(lambda: cleanup(response))

    return response


@export_bp.route('/excel/summary', methods=['POST'])
def export_summary_to_excel():
    payload = request.get_json() or {}
    user, telegram_id = _resolve_user(payload)

    transactions = _ensure_transactions(Transaction.get_user_transactions(user.id))
    transactions_data = [transaction.to_dict() for transaction in transactions]
    excel_buffer = excel_service.export_summary_report(transactions_data)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
        tmp_file.write(excel_buffer.getvalue())
        tmp_file_path = tmp_file.name

    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f"TBCparcer_summary_report_{timestamp}.xlsx"

    def cleanup(response):
        try:
            os.unlink(tmp_file_path)
        except Exception:  # pragma: no cover
            pass
        return response

    response = send_file(
        tmp_file_path,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response.call_on_close(lambda: cleanup(response))

    return response


@export_bp.route('/json', methods=['POST'])
def export_to_json():
    payload = request.get_json() or {}
    user, telegram_id = _resolve_user(payload)
    export_type, limit = _extract_limit(payload)

    transactions = _ensure_transactions(_load_transactions(user.id, export_type, limit))
    transactions_data = [transaction.to_dict() for transaction in transactions]

    export_data = {
        'export_info': {
            'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M'),
            'user_id': telegram_id,
            'total_transactions': len(transactions_data),
            'export_type': export_type,
        },
        'transactions': transactions_data,
    }

    return jsonify(export_data)


@export_bp.route('/csv', methods=['POST'])
def export_to_csv():
    payload = request.get_json() or {}
    user, telegram_id = _resolve_user(payload)
    export_type, limit = _extract_limit(payload)

    transactions = _ensure_transactions(_load_transactions(user.id, export_type, limit))

    output = io.StringIO()
    writer = csv.writer(output)

    headers = [
        'Дата и время',
        'Тип операции',
        'Сумма',
        'Валюта',
        'Номер карты',
        'Описание',
        'Баланс',
        'Оператор',
        'Приложение',
    ]
    writer.writerow(headers)

    for transaction in transactions:
        transaction_dict = transaction.to_dict()
        date_value = transaction_dict.get('date_time')
        formatted_datetime = ''
        if date_value:
            try:
                parsed = datetime.fromisoformat(str(date_value).replace('Z', '+00:00'))
                formatted_datetime = parsed.strftime('%d.%m.%Y %H:%M')
            except ValueError:
                formatted_datetime = str(date_value)

        writer.writerow(
            [
                formatted_datetime,
                excel_service.operation_types.get(
                    transaction_dict.get('operation_type'),
                    transaction_dict.get('operation_type'),
                ),
                transaction_dict.get('amount'),
                transaction_dict.get('currency'),
                transaction_dict.get('card_number'),
                transaction_dict.get('description'),
                transaction_dict.get('balance'),
                transaction_dict.get('operator_name'),
                transaction_dict.get('operator_description'),
            ]
        )

    with tempfile.NamedTemporaryFile(
        mode='w', delete=False, suffix='.csv', encoding='utf-8'
    ) as tmp_file:
        tmp_file.write(output.getvalue())
        tmp_file_path = tmp_file.name

    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f"TBCparcer_transactions_{timestamp}.csv"

    def cleanup(response):
        try:
            os.unlink(tmp_file_path)
        except Exception:  # pragma: no cover
            pass
        return response

    response = send_file(
        tmp_file_path,
        as_attachment=True,
        download_name=filename,
        mimetype='text/csv',
    )
    response.call_on_close(lambda: cleanup(response))

    return response

