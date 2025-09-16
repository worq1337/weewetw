from flask import Blueprint, request, jsonify, send_file
from src.services.excel_export import ExcelExportService
from src.models.transaction import Transaction
from src.models.user import User
from datetime import datetime
import tempfile
import os

export_bp = Blueprint('export', __name__)
excel_service = ExcelExportService()

@export_bp.route('/excel', methods=['POST'])
def export_to_excel():
    """Экспорт транзакций в Excel"""
    try:
        data = request.get_json()
        
        if not data or 'telegram_id' not in data:
            return jsonify({'error': 'Отсутствует telegram_id'}), 400
        
        telegram_id = data['telegram_id']
        
        # Получаем пользователя
        user = User.get_by_telegram_id(telegram_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        # Получаем параметры экспорта
        export_type = data.get('export_type', 'all')  # 'all' или 'latest'
        limit = data.get('limit', None)
        column_settings = data.get('column_settings', {})
        cell_colors = data.get('cell_colors', {})
        column_widths = data.get('column_widths', {})
        column_order = data.get('column_order', None)
        
        # Получаем транзакции
        if export_type == 'latest' and limit:
            transactions = Transaction.get_user_transactions(user.id, limit=limit)
        else:
            transactions = Transaction.get_user_transactions(user.id)
        
        if not transactions:
            return jsonify({'error': 'Нет данных для экспорта'}), 404
        
        # Конвертируем в словари
        transactions_data = [t.to_dict() for t in transactions]
        
        # Создаем Excel файл
        excel_buffer = excel_service.export_transactions(transactions_data)
        
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_file.write(excel_buffer.getvalue())
            tmp_file_path = tmp_file.name
        
        # Генерируем имя файла
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"TBCparcer_transactions_{timestamp}.xlsx"
        
        def remove_file(response):
            try:
                os.unlink(tmp_file_path)
            except Exception:
                pass
            return response
        
        # Отправляем файл
        response = send_file(
            tmp_file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Удаляем временный файл после отправки
        response.call_on_close(lambda: remove_file(response))
        
        return response
    
    except Exception as e:
        return jsonify({'error': f'Ошибка при экспорте: {str(e)}'}), 500

@export_bp.route('/excel/summary', methods=['POST'])
def export_summary_to_excel():
    """Экспорт сводного отчета в Excel"""
    try:
        data = request.get_json()
        
        if not data or 'telegram_id' not in data:
            return jsonify({'error': 'Отсутствует telegram_id'}), 400
        
        telegram_id = data['telegram_id']
        
        # Получаем пользователя
        user = User.get_by_telegram_id(telegram_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        # Получаем все транзакции
        transactions = Transaction.get_user_transactions(user.id)
        
        if not transactions:
            return jsonify({'error': 'Нет данных для экспорта'}), 404
        
        # Конвертируем в словари
        transactions_data = [t.to_dict() for t in transactions]
        
        # Создаем сводный отчет
        excel_buffer = excel_service.export_summary_report(transactions_data)
        
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_file.write(excel_buffer.getvalue())
            tmp_file_path = tmp_file.name
        
        # Генерируем имя файла
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"TBCparcer_summary_report_{timestamp}.xlsx"
        
        def remove_file(response):
            try:
                os.unlink(tmp_file_path)
            except Exception:
                pass
            return response
        
        # Отправляем файл
        response = send_file(
            tmp_file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Удаляем временный файл после отправки
        response.call_on_close(lambda: remove_file(response))
        
        return response
    
    except Exception as e:
        return jsonify({'error': f'Ошибка при экспорте сводного отчета: {str(e)}'}), 500

@export_bp.route('/json', methods=['POST'])
def export_to_json():
    """Экспорт транзакций в JSON"""
    try:
        data = request.get_json()
        
        if not data or 'telegram_id' not in data:
            return jsonify({'error': 'Отсутствует telegram_id'}), 400
        
        telegram_id = data['telegram_id']
        
        # Получаем пользователя
        user = User.get_by_telegram_id(telegram_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        # Получаем параметры экспорта
        export_type = data.get('export_type', 'all')
        limit = data.get('limit', None)
        
        # Получаем транзакции
        if export_type == 'latest' and limit:
            transactions = Transaction.get_user_transactions(user.id, limit=limit)
        else:
            transactions = Transaction.get_user_transactions(user.id)
        
        if not transactions:
            return jsonify({'error': 'Нет данных для экспорта'}), 404
        
        # Конвертируем в словари
        transactions_data = [t.to_dict() for t in transactions]
        
        # Добавляем метаданные
        export_data = {
            'export_info': {
                'timestamp': datetime.now().isoformat(),
                'user_id': telegram_id,
                'total_transactions': len(transactions_data),
                'export_type': export_type
            },
            'transactions': transactions_data
        }
        
        return jsonify(export_data)
    
    except Exception as e:
        return jsonify({'error': f'Ошибка при экспорте JSON: {str(e)}'}), 500

@export_bp.route('/csv', methods=['POST'])
def export_to_csv():
    """Экспорт транзакций в CSV"""
    try:
        data = request.get_json()
        
        if not data or 'telegram_id' not in data:
            return jsonify({'error': 'Отсутствует telegram_id'}), 400
        
        telegram_id = data['telegram_id']
        
        # Получаем пользователя
        user = User.get_by_telegram_id(telegram_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        # Получаем транзакции
        transactions = Transaction.get_user_transactions(user.id)

        if not transactions:
            return jsonify({'error': 'Нет данных для экспорта'}), 404

        # Создаем CSV
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Заголовки
        headers = [
            'Дата и время', 'Тип операции', 'Сумма', 'Валюта',
            'Номер карты', 'Описание', 'Баланс', 'Оператор', 'Приложение'
        ]
        writer.writerow(headers)

        # Данные
        for transaction in transactions:
            transaction_dict = transaction.to_dict()

            date_time_str = ''
            if transaction_dict.get('date_time'):
                try:
                    dt = datetime.fromisoformat(transaction_dict['date_time'].replace('Z', '+00:00'))
                    date_time_str = dt.strftime('%d.%m.%Y %H:%M')
                except ValueError:
                    date_time_str = transaction_dict['date_time']

            row = [
                date_time_str,
                excel_service.operation_types.get(transaction_dict.get('operation_type'), transaction_dict.get('operation_type')),
                transaction_dict.get('amount'),
                transaction_dict.get('currency'),
                transaction_dict.get('card_number'),
                transaction_dict.get('description'),
                transaction_dict.get('balance'),
                transaction_dict.get('operator_name'),
                transaction_dict.get('operator_description')
            ]
            writer.writerow(row)
        
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as tmp_file:
            tmp_file.write(output.getvalue())
            tmp_file_path = tmp_file.name
        
        # Генерируем имя файла
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"TBCparcer_transactions_{timestamp}.csv"
        
        def remove_file(response):
            try:
                os.unlink(tmp_file_path)
            except Exception:
                pass
            return response
        
        # Отправляем файл
        response = send_file(
            tmp_file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
        
        # Удаляем временный файл после отправки
        response.call_on_close(lambda: remove_file(response))
        
        return response
    
    except Exception as e:
        return jsonify({'error': f'Ошибка при экспорте CSV: {str(e)}'}), 500

