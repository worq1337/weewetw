import json
import os
import re
from datetime import datetime
from typing import Dict, Optional, Sequence

import openai

from src.services.operator_dictionary import (
    get_operator_dictionary,
    normalize_operator_value,
)


class LocalReceiptParser:
    """Rule-based parser that extracts receipt data without external APIs."""

    _DATE_PATTERNS = (
        (re.compile(r"(\d{4})[./-](\d{2})[./-](\d{2})[T\s,]*(\d{2}):(\d{2})(?::(\d{2}))?"), "ymd"),
        (re.compile(r"(\d{2})[./-](\d{2})[./-](\d{4})[T\s,]*(\d{2}):(\d{2})(?::(\d{2}))?"), "dmy"),
        (re.compile(r"(\d{2})[./-](\d{2})[./-](\d{2})[T\s,]*(\d{2}):(\d{2})(?::(\d{2}))?"), "dmy_short"),
    )

    _OPERATION_KEYWORDS = {
        "payment": {"payment", "оплата", "списание", "покупка"},
        "refill": {"refill", "пополнение", "зачисление", "поступление"},
        "conversion": {"conversion", "конверсия", "exchange", "обмен"},
        "cancel": {"cancel", "отмена", "refund", "возврат"},
    }

    _CURRENCY_ALIASES = {
        "uzs": "UZS",
        "сум": "UZS",
        "sum": "UZS",
        "usd": "USD",
        "$": "USD",
        "доллар": "USD",
        "eur": "EUR",
        "€": "EUR",
        "rub": "RUB",
        "руб": "RUB",
        "₽": "RUB",
    }

    _META_KEYWORDS = (
        "дата",
        "тип",
        "сум",
        "баланс",
        "карта",
        "operator",
        "оператор",
        "описание",
        "description",
    )

    def parse(self, receipt_text: str) -> Dict:
        """Parse receipt text using simple heuristics."""
        normalized_text = receipt_text.replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.strip() for line in normalized_text.split("\n") if line.strip()]
        lower_text = normalized_text.lower()

        parsed: Dict[str, Optional[str]] = {
            "date_time": self._extract_datetime(normalized_text),
            "operation_type": self._detect_operation_type(lower_text),
        }

        amount_value, currency = self._extract_amount(lower_text)
        if amount_value is not None:
            parsed["amount"] = amount_value
        if currency:
            parsed["currency"] = currency

        balance_value = self._extract_balance(lower_text)
        if balance_value is not None:
            parsed["balance"] = balance_value

        card_number = self._extract_card_number(normalized_text)
        if card_number:
            parsed["card_number"] = card_number

        operator = self._extract_operator(lines)
        if operator:
            parsed["operator"] = operator

        description = self._extract_description(lines)
        if description:
            parsed["description"] = description

        return parsed

    def _extract_datetime(self, text: str) -> Optional[str]:
        for pattern, ordering in self._DATE_PATTERNS:
            match = pattern.search(text)
            if not match:
                continue

            groups = match.groups(default="0")
            if ordering == "ymd":
                year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                hour, minute, second = int(groups[3]), int(groups[4]), int(groups[5] or 0)
            elif ordering == "dmy":
                day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                hour, minute, second = int(groups[3]), int(groups[4]), int(groups[5] or 0)
            else:  # dmy_short
                day, month = int(groups[0]), int(groups[1])
                year = 2000 + int(groups[2])
                hour, minute, second = int(groups[3]), int(groups[4]), int(groups[5] or 0)

            try:
                return datetime(year, month, day, hour, minute, second).isoformat()
            except ValueError:
                continue

        return None

    def _normalize_number(self, value: str) -> Optional[float]:
        cleaned = value.replace("\u00a0", " ").replace(" ", "").replace(",", ".")
        cleaned = cleaned.replace("'", "")
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None

    def _extract_amount(self, text: str) -> tuple[Optional[float], Optional[str]]:
        amount_patterns = (
            re.compile(
                r"(?:сумма|amount|на сумму|итого)\D*([\d\s.,']+)(?:\s*(uzs|usd|eur|rub|сум|sum|доллар|руб|₽|\$|€))?",
                re.IGNORECASE,
            ),
            re.compile(r"([\d\s.,']+)\s*(uzs|usd|eur|rub|сум|sum|доллар|руб|₽|\$|€)", re.IGNORECASE),
        )

        for pattern in amount_patterns:
            match = pattern.search(text)
            if not match:
                continue

            amount_raw = match.group(1)
            currency_raw = match.group(2) if len(match.groups()) > 1 else None
            amount_value = self._normalize_number(amount_raw)
            currency = self._normalize_currency(currency_raw)

            if amount_value is not None:
                return amount_value, currency

        return None, None

    def _extract_balance(self, text: str) -> Optional[float]:
        balance_pattern = re.compile(r"(?:баланс|остаток|balance)\D*([\d\s.,']+)", re.IGNORECASE)
        match = balance_pattern.search(text)
        if not match:
            return None
        return self._normalize_number(match.group(1))

    def _extract_card_number(self, text: str) -> Optional[str]:
        card_pattern = re.compile(r"(?:card|карта|pc|pan|ПК)\D*(\*+\d{4}|\d{4})", re.IGNORECASE)
        match = card_pattern.search(text)
        if match:
            card = match.group(1)
            if not card.startswith("*"):
                return f"*{card[-4:]}"
            return card

        masked_pattern = re.compile(r"\*(\d{4})")
        match = masked_pattern.search(text)
        if match:
            return f"*{match.group(1)}"
        return None

    def _normalize_currency(self, currency: Optional[str]) -> Optional[str]:
        if not currency:
            return None
        normalized = currency.lower().strip().replace(".", "")
        return self._CURRENCY_ALIASES.get(normalized, normalized.upper())

    def _detect_operation_type(self, text_lower: str) -> Optional[str]:
        for op_type, keywords in self._OPERATION_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                return op_type
        return None

    def _extract_operator(self, lines: Sequence[str]) -> Optional[str]:
        for line in lines:
            lowered = line.lower()
            if any(keyword in lowered for keyword in ("оператор", "operator", "отправитель", "sender")):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    candidate = parts[1].strip()
                    if candidate:
                        return candidate

        if lines:
            first_line = lines[0]
            if not any(keyword in first_line.lower() for keyword in self._META_KEYWORDS):
                return first_line
        return None

    def _extract_description(self, lines: Sequence[str]) -> Optional[str]:
        description_lines = []
        for line in lines[1:]:
            lowered = line.lower()
            if any(keyword in lowered for keyword in self._META_KEYWORDS):
                if lowered.startswith("описание") or lowered.startswith("description"):
                    parts = line.split(":", 1)
                    if len(parts) == 2 and parts[1].strip():
                        return parts[1].strip()
                continue
            description_lines.append(line)

        if description_lines:
            return " ".join(description_lines)
        return None


class AIParsingService:
    """Сервис для парсинга чеков с помощью OpenAI или локального пайплайна."""

    def __init__(self, client: Optional[openai.OpenAI] = None):
        api_key = os.getenv('OPENAI_API_KEY')
        base_url = os.getenv('OPENAI_API_BASE')
        self.client = None
        self._local_parser = LocalReceiptParser()

        if api_key:
            self.client = client or openai.OpenAI(api_key=api_key, base_url=base_url)
        
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
        Парсинг чека с помощью OpenAI API или локального пайплайна

        Args:
            receipt_text: Текст чека для парсинга
            retry_count: Количество попыток (по умолчанию 2)

        Returns:
            Dict с распарсенными данными или ошибкой
        """

        if not self.client:
            parsed_data = self._local_parser.parse(receipt_text)
            validation_result = self.validate_receipt_data(parsed_data)

            if 'error' in validation_result:
                return validation_result

            parsed_data['raw_text'] = receipt_text
            parsed_data['parsed_at'] = datetime.now().isoformat()
            parsed_data['ai_model'] = 'local-rule-based'

            return parsed_data

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
    
    def enhance_with_operator_info(self, parsed_data: Dict, operators_list: Sequence) -> Dict:
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

        dictionary = get_operator_dictionary()
        original_operator = str(parsed_data['operator']).strip()
        dictionary_entry = dictionary.lookup(original_operator)

        if dictionary_entry:
            resolved_alias = dictionary_entry['alias']
            resolved_brand = dictionary_entry['operator']
            if resolved_alias != original_operator:
                parsed_data['operator_raw'] = original_operator
                parsed_data['operator'] = resolved_alias
            parsed_data.setdefault('operator_description', resolved_brand)
        else:
            resolved_alias = original_operator
            resolved_brand = None

        normalized_alias = dictionary.normalize(resolved_alias)
        if normalized_alias:
            parsed_data['operator_normalized'] = normalized_alias

        target_normalized = normalized_alias

        normalized_operators = []
        for operator in operators_list:
            if isinstance(operator, dict):
                normalized_operators.append(operator)
            else:
                normalized_operators.append(operator.to_dict())

        # Ищем оператора в базе данных
        matched_operator: Optional[Dict] = None
        if target_normalized:
            for operator in normalized_operators:
                name = operator.get('name')
                if not name:
                    continue

                normalized_name = normalize_operator_value(name, dictionary)
                if not normalized_name:
                    continue

                if (
                    normalized_name == target_normalized
                    or normalized_name in target_normalized
                    or target_normalized in normalized_name
                ):
                    matched_operator = operator
                    break

        if matched_operator:
            parsed_data['operator_id'] = matched_operator.get('id')
            parsed_data['operator_name'] = matched_operator.get('name')
            description = matched_operator.get('description', '')
            if description:
                parsed_data['operator_description'] = description
            elif resolved_brand:
                parsed_data['operator_description'] = resolved_brand
        else:
            if resolved_alias:
                parsed_data.setdefault('operator_name', resolved_alias)
            if resolved_brand:
                parsed_data.setdefault('operator_description', resolved_brand)

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

