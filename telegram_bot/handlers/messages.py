from telegram import Update
from telegram.ext import ContextTypes
from utils.api_client import APIClient
from utils.receipt_parser import ReceiptParser

api_client = APIClient()
receipt_parser = ReceiptParser()

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений (чеков)"""
    user = update.effective_user
    message_text = update.message.text
    
    # Проверяем, что это не команда
    if message_text.startswith('/'):
        await update.message.reply_text("Неизвестная команда. Используйте /help для справки.")
        return
    
    # Проверяем минимальную длину сообщения
    if len(message_text.strip()) < 10:
        await update.message.reply_text(
            "Сообщение слишком короткое. Пожалуйста, отправьте полный текст чека."
        )
        return
    
    try:
        # Уведомляем о начале обработки
        processing_message = await update.message.reply_text("🔄 Обрабатываю чек...")
        
        # Парсим чек с помощью AI
        parsed_data = receipt_parser.parse_receipt(message_text, retry_count=1)
        
        # Проверяем результат парсинга
        if 'error' in parsed_data:
            await processing_message.edit_text(
                f"❌ Ошибка парсинга: {parsed_data['error']}\n\n"
                "Убедитесь, что отправили корректный финансовый чек."
            )
            return
        
        # Валидируем данные
        validation_result = receipt_parser.validate_receipt_data(parsed_data)
        if 'error' in validation_result:
            await processing_message.edit_text(
                f"❌ Ошибка валидации: {validation_result['error']}"
            )
            return
        
        # Сохраняем в базу данных
        save_result = api_client.create_transaction(user.id, parsed_data)
        
        if 'error' in save_result:
            if 'Duplicate transaction' in save_result['error']:
                await processing_message.edit_text(
                    "⚠️ Дубликат транзакции!\n\n"
                    "Этот чек уже был обработан ранее."
                )
            else:
                await processing_message.edit_text(
                    f"❌ Ошибка сохранения: {save_result['error']}"
                )
            return
        
        # Формируем сообщение об успешном сохранении
        transaction = save_result.get('transaction', {})
        
        success_message = "✅ Чек успешно обработан!\n\n"
        success_message += f"📅 Дата: {transaction.get('date_time', 'Не указана')}\n"
        success_message += f"💰 Сумма: {transaction.get('amount', 0)} {transaction.get('currency', 'UZS')}\n"
        success_message += f"🔄 Операция: {get_operation_emoji(transaction.get('operation_type'))} {get_operation_name(transaction.get('operation_type'))}\n"
        
        if transaction.get('card_number'):
            success_message += f"💳 Карта: {transaction['card_number']}\n"
        
        if transaction.get('description'):
            success_message += f"📝 Описание: {transaction['description']}\n"
        
        if transaction.get('operator_name'):
            success_message += f"🏦 Оператор: {transaction['operator_name']}\n"
        
        if transaction.get('balance') is not None:
            success_message += f"💵 Баланс: {transaction['balance']} {transaction.get('currency', 'UZS')}\n"
        
        success_message += f"\n🆔 ID транзакции: {transaction.get('id')}"
        
        await processing_message.edit_text(success_message)
    
    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка: {str(e)}")

def get_operation_emoji(operation_type: str) -> str:
    """Получить эмодзи для типа операции"""
    emoji_map = {
        'payment': '💸',
        'refill': '💰',
        'conversion': '🔄',
        'cancel': '❌'
    }
    return emoji_map.get(operation_type, '📋')

def get_operation_name(operation_type: str) -> str:
    """Получить название типа операции"""
    name_map = {
        'payment': 'Оплата/Списание',
        'refill': 'Пополнение',
        'conversion': 'Конверсия',
        'cancel': 'Отмена'
    }
    return name_map.get(operation_type, 'Неизвестная операция')

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик документов"""
    await update.message.reply_text(
        "📄 Обработка документов пока не поддерживается.\n\n"
        "Пожалуйста, отправьте текст чека обычным сообщением."
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик фотографий"""
    await update.message.reply_text(
        "📸 Обработка изображений пока не поддерживается.\n\n"
        "Пожалуйста, отправьте текст чека обычным сообщением."
    )

