import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot настройки
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8482297276:AAGgRybGOkdTH8_JHT1gXeiMYDwrJT_gBho')

# OpenAI настройки
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_API_BASE = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')

# Backend API настройки
BACKEND_API_URL = os.getenv('BACKEND_API_URL', 'http://localhost:5000/api')

# Настройки бота
BOT_STYLE = "строгий, деловой, профессиональный"
BACKUP_TIME = "00:00"  # Время резервного копирования

# Промт для парсинга чеков
PARSING_PROMPT = """
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

