import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime, date, time
import io
from typing import List, Dict, Optional

class ExcelExportService:
    def __init__(self):
        # Колонки точно соответствуют таблице на сайте (ТЗ)
        self.columns = [
            'Номер чека',
            'Дата и время', 
            'Д.н.',
            'Дата',
            'Время',
            'Оператор/Продавец',
            'Приложение',
            'Сумма',
            'Остаток',
            'ПК',
            'P2P',
            'Тип транзакции',
            'Валюта',
            'Источник данных',
            'Категория'
        ]
        
        self.operation_types = {
            'payment': 'Оплата',
            'refill': 'Пополнение',
            'conversion': 'Конверсия',
            'cancel': 'Отмена'
        }
    
    def _get_day_of_week(self, date_time):
        """Получить день недели на русском"""
        if not date_time:
            return ""
        
        if isinstance(date_time, str):
            try:
                date_time = datetime.fromisoformat(date_time.replace('Z', '+00:00'))
            except:
                return ""
        
        days = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']
        return days[date_time.weekday()]
    
    def _format_card_number(self, card_number):
        """Форматировать номер карты для колонки ПК"""
        if not card_number:
            return ""
        # Если уже есть *, возвращаем как есть, иначе добавляем *
        if card_number.startswith('*'):
            return card_number
        return f"*{card_number[-4:]}" if len(card_number) >= 4 else card_number
    
    def _get_transaction_data(self, transaction):
        """Преобразовать транзакцию в данные для Excel согласно ТЗ"""
        date_time_obj = None
        if transaction.get('date_time'):
            if isinstance(transaction['date_time'], str):
                try:
                    date_time_obj = datetime.fromisoformat(transaction['date_time'].replace('Z', '+00:00'))
                    if date_time_obj.tzinfo is not None:
                        date_time_obj = date_time_obj.replace(tzinfo=None)
                except Exception:
                    date_time_obj = None
            else:
                date_time_obj = transaction['date_time']
                if isinstance(date_time_obj, datetime) and date_time_obj.tzinfo is not None:
                    date_time_obj = date_time_obj.replace(tzinfo=None)

        # Генерируем номер чека (если нет в данных)
        receipt_number = transaction.get('receipt_number')
        if not receipt_number:
            receipt_number = f"CHK{str(transaction.get('id', '000')).zfill(3)}"

        # Определяем P2P (пока заглушка, так как в модели нет этого поля)
        p2p_value = 'Нет'  # По умолчанию
        if transaction.get('operation_type') == 'conversion':
            p2p_value = 'Да'

        date_value: Optional[date] = None
        time_value: Optional[time] = None
        if isinstance(date_time_obj, datetime):
            date_value = date_time_obj.date()
            time_value = date_time_obj.time().replace(second=0, microsecond=0)

        return [
            receipt_number,  # Номер чека
            date_time_obj if date_time_obj else None,  # Дата и время
            self._get_day_of_week(date_time_obj),  # Д.н.
            date_value,  # Дата
            time_value,  # Время
            transaction.get('operator_name', ''),  # Оператор/Продавец
            transaction.get('operator_description', ''),  # Приложение
            transaction.get('amount', 0),  # Сумма
            transaction.get('balance', 0),  # Остаток
            self._format_card_number(transaction.get('card_number', '')),  # ПК
            p2p_value,  # P2P
            self.operation_types.get(transaction.get('operation_type', ''), transaction.get('operation_type', '')),  # Тип транзакции
            transaction.get('currency', 'UZS'),  # Валюта
            'API',  # Источник данных (заглушка)
            self._get_category_from_description(transaction.get('description', ''))  # Категория
        ]
    
    def _get_category_from_description(self, description):
        """Определить категорию по описанию"""
        if not description:
            return 'Прочее'
        
        description_lower = description.lower()
        if 'перевод' in description_lower or 'конверсия' in description_lower:
            return 'Переводы'
        elif 'оплата' in description_lower:
            return 'Покупки'
        elif 'пополнение' in description_lower:
            return 'Пополнения'
        else:
            return 'Прочее'
    
    def export_transactions(self, transactions: List[Dict]) -> io.BytesIO:
        """
        Экспорт транзакций в Excel с точным соответствием таблице сайта
        
        Args:
            transactions: Список транзакций
        
        Returns:
            BytesIO объект с Excel файлом
        """
        # Создаем новую книгу
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Финансовые транзакции"
        
        # Стиль границ
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Создаем заголовки (строка 1)
        for col_idx, column_name in enumerate(self.columns, 1):
            cell = worksheet.cell(row=1, column=col_idx, value=column_name)
            # Стиль заголовков
            cell.font = Font(bold=True, size=12)
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.fill = PatternFill(start_color='E6E6FA', end_color='E6E6FA', fill_type='solid')
            cell.border = thin_border
        
        # Заполняем данные транзакций
        for row_idx, transaction in enumerate(transactions, 2):  # Начинаем с 2-й строки
            transaction_data = self._get_transaction_data(transaction)
            
            for col_idx, value in enumerate(transaction_data, 1):
                cell = worksheet.cell(row=row_idx, column=col_idx, value=value)
                
                # Выравнивание по типу данных
                if col_idx in [8, 9]:  # Сумма, Остаток
                    cell.alignment = Alignment(horizontal='right')
                    if isinstance(value, (int, float)):
                        cell.number_format = '#,##0.00'
                elif col_idx in [1, 2, 3, 4, 5]:  # Номер чека, Дата и время, Дата, Время, Д.н.
                    cell.alignment = Alignment(horizontal='center')
                else:
                    cell.alignment = Alignment(horizontal='left')

                if isinstance(value, datetime):
                    cell.number_format = 'dd.mm.yyyy hh:mm'
                elif isinstance(value, date):
                    cell.number_format = 'dd.mm.yyyy'
                elif isinstance(value, time):
                    cell.number_format = 'hh:mm'

                # Границы для всех ячеек
                cell.border = thin_border
        
        # Устанавливаем ширину колонок
        column_widths = [
            15,  # Номер чека
            20,  # Дата и время
            8,   # Д.н.
            12,  # Дата
            8,   # Время
            20,  # Оператор/Продавец
            15,  # Приложение
            15,  # Сумма
            15,  # Остаток
            10,  # ПК
            8,   # P2P
            15,  # Тип транзакции
            10,  # Валюта
            15,  # Источник данных
            15   # Категория
        ]
        
        for col_idx, width in enumerate(column_widths, 1):
            worksheet.column_dimensions[get_column_letter(col_idx)].width = width
        
        # Сохраняем в BytesIO
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        
        return output

