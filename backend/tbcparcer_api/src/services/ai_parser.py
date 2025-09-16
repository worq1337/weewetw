import json
import openai
import os
from typing import Dict, Optional
from datetime import datetime

class AIParsingService:
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            base_url=os.getenv('OPENAI_API_BASE')
        )
        
        self.parsing_prompt = """
Ты - специализированный парсер финансовых чеков из Узбекистана. Твоя задача - извлечь структурированные данные из текста чека и вернуть их в формате JSON.

ВАЖНО: Анализируй ТОЛЬКО финансовые транзакции. Если текст не содержит информацию о финансовой операции, верни {"error": "Не является финансовым чеком"}.

Извлекай следующие поля:
1. date_time - дата и время в формате "YYYY-MM-DD HH:MM:SS"
2. operation_type - тип операции: "payment" (оплата/списание), "refill" (пополнение), "conversion" (конверсия), "cancel" (отмена)
3. amount - сумма операции (только число, без валюты)
4. currency - валюта (UZS, USD, EUR и т.д.)
5. card_number - номер карты (замаскированный)
6. description - описание операции/место покупки
7. balance - остаток на счете после операции (только число)
8. operator - банк или платежная система

Правила парсинга:
- Даты могут быть в форматах: DD.MM.YY, DD-MM-YY, DD.MM.YYYY
- Суммы могут содержать точки, запятые, пробелы как разделители
- Операции: "Оплата"/"oplata"/"Pokupka" = payment, "Пополнение"/"popolnenie" = refill, "Конверсия" = conversion, "OTMENA" = cancel
- Если баланс не указан, поставь null
- Если какое-то поле не найдено, поставь null
- Номера карт могут быть в форматах: *1234, ***1234, **1234, HUMOCARD *1234

Пример ответа:
{
  "date_time": "2025-04-04 18:46:00",
  "operation_type": "payment",
  "amount": 6000000.00,
  "currency": "UZS",
  "card_number": "*6714",
  "description": "NBU P2P HUMO UZCARD>",
  "balance": 935000.40,
  "operator": "HUMO"
}

Если не можешь распарсить чек, верни:
{
  "error": "Не удалось распарсить чек"
}
"""
    
    def parse_receipt(self, receipt_text: str, retry_count: int = 2) -> Dict:
        """
        Парсинг чека с помощью OpenAI API
        
        Args:
            receipt_text: Текст чека для парсинга
            retry_count: Количество попыток (по умолчанию 2)
        
        Returns:
            Dict с распарсенными данными или ошибкой
        """
        for attempt in range(retry_count + 1):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": self.parsing_prompt
                        },
                        {
                            "role": "user",
                            "content": f"Распарси этот чек:\n\n{receipt_text}"
                        }
                    ],
                    temperature=0.1,
                    max_tokens=500
                )
                
                # Извлекаем ответ
                content = response.choices[0].message.content.strip()
                
                # Пытаемся распарсить JSON
                try:
                    parsed_data = json.loads(content)
                    
                    # Проверяем, есть ли ошибка в ответе
                    if 'error' in parsed_data:
                        return parsed_data
                    
                    # Валидируем обязательные поля
                    validation_result = self.validate_receipt_data(parsed_data)
                    if 'error' in validation_result:
                        return validation_result
                    
                    # Добавляем исходный текст и метаданные
                    parsed_data['raw_text'] = receipt_text
                    parsed_data['parsed_at'] = datetime.now().isoformat()
                    parsed_data['ai_model'] = "gpt-4o-mini"
                    
                    return parsed_data
                
                except json.JSONDecodeError:
                    if attempt == retry_count:
                        return {'error': 'Не удалось распарсить ответ AI как JSON'}
                    continue
            
            except Exception as e:
                if attempt == retry_count:
                    return {'error': f'Ошибка при обращении к AI API: {str(e)}'}
                continue
        
        return {'error': 'Не удалось распарсить чек после всех попыток'}
    
    def validate_receipt_data(self, data: Dict) -> Dict:
        """Валидация данных чека"""
        errors = []
        
        # Проверяем обязательные поля
        required_fields = ['date_time', 'operation_type', 'amount']
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f'Отсутствует поле: {field}')
        
        # Проверяем тип операции
        valid_operations = ['payment', 'refill', 'conversion', 'cancel']
        if 'operation_type' in data and data['operation_type'] not in valid_operations:
            errors.append(f'Неверный тип операции: {data["operation_type"]}')
        
        # Проверяем сумму
        if 'amount' in data:
            try:
                float(data['amount'])
            except (ValueError, TypeError):
                errors.append('Неверный формат суммы')
        
        # Проверяем дату
        if 'date_time' in data:
            try:
                datetime.fromisoformat(data['date_time'].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                errors.append('Неверный формат даты')
        
        if errors:
            return {'error': '; '.join(errors)}
        
        return {'valid': True}
    
    def enhance_with_operator_info(self, parsed_data: Dict, operators_list: list) -> Dict:
        """
        Улучшение данных с информацией об операторе из базы данных
        
        Args:
            parsed_data: Распарсенные данные чека
            operators_list: Список операторов из базы данных
        
        Returns:
            Обогащенные данные с информацией об операторе
        """
        if 'operator' not in parsed_data or not parsed_data['operator']:
            return parsed_data
        
        operator_name = parsed_data['operator'].upper()
        
        # Ищем оператора в базе данных
        for operator in operators_list:
            if operator['name'].upper() == operator_name:
                parsed_data['operator_id'] = operator['id']
                parsed_data['operator_name'] = operator['name']
                parsed_data['operator_description'] = operator.get('description', '')
                break
        
        return parsed_data
    
    def batch_parse_receipts(self, receipts_list: list) -> list:
        """
        Пакетная обработка чеков
        
        Args:
            receipts_list: Список текстов чеков
        
        Returns:
            Список результатов парсинга
        """
        results = []
        
        for i, receipt_text in enumerate(receipts_list):
            try:
                result = self.parse_receipt(receipt_text)
                result['batch_index'] = i
                results.append(result)
            except Exception as e:
                results.append({
                    'batch_index': i,
                    'error': f'Ошибка при обработке чека {i}: {str(e)}'
                })
        
        return results

