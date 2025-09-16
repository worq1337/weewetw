# Анализ требований TBCparcer

## Общее описание проекта
TBCparcer - это система для автоматического парсинга, учета и анализа финансовых чеков из Узбекистана, состоящая из веб-сайта и Telegram-бота.

## Технический стек
- **Backend**: Python 11-13 или Go (выберем Python с Flask)
- **Frontend**: React
- **База данных**: PostgreSQL или SQLite (выберем SQLite для простоты)
- **AI API**: OpenAI GPT-4o-mini
- **Telegram Bot**: Python telegram-bot

## Анализ форматов чеков

### Типы чеков из примеров:

1. **HUMO Card** (эмодзи формат):
   ```
   💸 Оплата
   ➖ 6.000.000,00 UZS
   📍 NBU P2P HUMO UZCARD>
   💳 HUMOCARD *6714
   🕓 18:46 04.04.2025
   💰 935.000,40 UZS
   ```

2. **Текстовый формат банков**:
   ```
   Pokupka: OOO "AGAT SYSTEM", tashkent, g tashkent Ul Gavhar 151 02.04.25 08:37 karta ***0907. summa:44000.00 UZS, balans:2607792.14 UZS
   ```

3. **CardXabar формат**:
   ```
   🔴 Pokupka
   ➖ 44 000.00 UZS
   💳 ***0907
   📍 OOO "AGAT SYSTEM", tashkent, g tashkent  Ul  Gavhar 151 
   🕓 02.04.25 08:37
   💵 2 607 792.14 UZS
   ```

4. **NBU Card конверсия**:
   ```
   💸 Конверсия
   ➖ 37.00 USD
   💳 479091**6905
   🕓 14.04.25 10:29
   💵 0.00 USD
   ```

### Поля для извлечения:
1. **Дата и время** - в различных форматах
2. **Тип операции** - оплата, пополнение, конверсия, отмена
3. **Сумма** - с валютой (UZS, USD)
4. **Номер карты** - замаскированный
5. **Место/описание** - название магазина или операции
6. **Баланс** - остаток на карте
7. **Оператор** - банк или платежная система

## Функциональные требования

### Telegram Bot:
- Команды: /start, /help, /operators, /db, /export
- Обработка текстовых чеков
- Парсинг через AI API
- Проверка дубликатов
- Резервное копирование в 00:00
- Строгий деловой стиль общения

### Web Interface:
- Интерактивная таблица с редактированием
- Настройка колонок (ширина, перемещение)
- Форматирование (выравнивание, цвет ячеек)
- Бургер-меню с разделами
- WebSocket синхронизация
- Минималистичный дизайн (черный, белый, серый)

### Экспорт Excel:
- Формат .xlsx
- Сортировка по дате
- Сохранение форматирования
- Автоматическая ширина столбцов

## Структура базы данных

### Таблица transactions:
- id (PRIMARY KEY)
- date_time (DATETIME)
- operation_type (VARCHAR)
- amount (DECIMAL)
- currency (VARCHAR)
- card_number (VARCHAR)
- description (TEXT)
- balance (DECIMAL)
- operator (VARCHAR)
- raw_text (TEXT)
- created_at (TIMESTAMP)
- user_id (INTEGER)

### Таблица operators:
- id (PRIMARY KEY)
- name (VARCHAR)
- user_id (INTEGER, NULL для глобальных)
- created_at (TIMESTAMP)

### Таблица users:
- id (PRIMARY KEY)
- telegram_id (BIGINT)
- username (VARCHAR)
- created_at (TIMESTAMP)

## Безопасность
- AI API токен в переменных окружения
- Telegram Bot токен в переменных окружения
- Валидация входных данных
- Защита от SQL инъекций

## Архитектура системы
```
[Telegram Bot] ←→ [Flask API] ←→ [SQLite DB]
                      ↕
[React Frontend] ←→ [WebSocket]
                      ↕
                 [OpenAI API]
```

