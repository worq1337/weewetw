import json
import openai
from typing import Dict, Optional
from config.settings import OPENAI_API_KEY, OPENAI_API_BASE, PARSING_PROMPT

class ReceiptParser:
    def __init__(self):
        openai.api_key = OPENAI_API_KEY
        openai.api_base = OPENAI_API_BASE
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE)
    
    def parse_receipt(self, receipt_text: str, retry_count: int = 1) -> Dict:
        """
        Парсинг чека с помощью OpenAI API
        
        Args:
            receipt_text: Текст чека для парсинга
            retry_count: Количество попыток (по умолчанию 1)
        
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
                            "content": PARSING_PROMPT
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
                    required_fields = ['date_time', 'operation_type', 'amount']
                    for field in required_fields:
                        if field not in parsed_data or parsed_data[field] is None:
                            return {'error': f'Отсутствует обязательное поле: {field}'}
                    
                    # Добавляем исходный текст
                    parsed_data['raw_text'] = receipt_text
                    
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
        
        if errors:
            return {'error': '; '.join(errors)}
        
        return {'valid': True}

