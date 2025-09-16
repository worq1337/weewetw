from telegram import Update
from telegram.ext import ContextTypes
from utils.api_client import APIClient
import io
import json

api_client = APIClient()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    welcome_message = f"""
Добро пожаловать в TBCparcer!

Я помогу вам автоматически обрабатывать и учитывать финансовые чеки из Узбекистана.

Доступные команды:
/help - Справка по использованию
/operators - Управление операторами
/db - Статистика базы данных
/export - Экспорт данных в Excel

Для начала работы просто отправьте мне текст чека, и я автоматически его обработаю.
"""
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📋 СПРАВКА ПО ИСПОЛЬЗОВАНИЮ TBCparcer

🔹 ОСНОВНЫЕ ФУНКЦИИ:
• Автоматический парсинг финансовых чеков
• Учет и анализ транзакций
• Управление операторами и приложениями
• Экспорт данных в Excel

🔹 КАК ИСПОЛЬЗОВАТЬ:
1. Отправьте текст чека в чат
2. Бот автоматически распарсит данные
3. Проверит на дубликаты
4. Сохранит в базу данных

🔹 КОМАНДЫ:
/start - Начать работу
/help - Эта справка
/operators - Управление операторами
/db - Статистика базы данных
/export - Экспорт в Excel

🔹 ФОРМАТЫ ЧЕКОВ:
Поддерживаются чеки от всех основных банков и платежных систем Узбекистана:
• HUMO, UZCARD, NBU
• Milliy Bank, Hamkor Bank, SmartBank
• PayMe, Click, Paynet и другие

🔹 РЕЗЕРВНОЕ КОПИРОВАНИЕ:
Ежедневно в 00:00 автоматически создается резервная копия базы данных.
"""
    await update.message.reply_text(help_text)

async def operators_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /operators"""
    user_id = update.effective_user.id
    
    try:
        # Получаем операторов пользователя
        result = api_client.get_operators(user_id)
        
        if 'error' in result:
            await update.message.reply_text(f"Ошибка при получении операторов: {result['error']}")
            return
        
        operators = result.get('operators', [])
        
        if not operators:
            await update.message.reply_text("Операторы не найдены.")
            return
        
        # Разделяем на глобальные и персональные
        global_ops = [op for op in operators if op['is_global']]
        personal_ops = [op for op in operators if not op['is_global']]
        
        message = "📊 ОПЕРАТОРЫ И ПРИЛОЖЕНИЯ\n\n"
        
        if global_ops:
            message += "🌐 ГЛОБАЛЬНЫЕ ОПЕРАТОРЫ:\n"
            for op in global_ops[:10]:  # Показываем первые 10
                message += f"• {op['name']}"
                if op['description']:
                    message += f" ({op['description']})"
                message += "\n"
            
            if len(global_ops) > 10:
                message += f"... и еще {len(global_ops) - 10} операторов\n"
        
        if personal_ops:
            message += "\n👤 ПЕРСОНАЛЬНЫЕ ОПЕРАТОРЫ:\n"
            for op in personal_ops:
                message += f"• {op['name']}"
                if op['description']:
                    message += f" ({op['description']})"
                message += "\n"
        
        message += f"\nВсего операторов: {len(operators)}"
        message += "\n\nДля добавления персонального оператора используйте формат:"
        message += "\n/add_operator Название - Описание"
        
        await update.message.reply_text(message)
    
    except Exception as e:
        await update.message.reply_text(f"Ошибка при обработке команды: {str(e)}")

async def db_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /db"""
    user_id = update.effective_user.id
    
    try:
        # Получаем транзакции пользователя
        result = api_client.get_transactions(user_id, per_page=1)
        
        if 'error' in result:
            await update.message.reply_text(f"Ошибка при получении данных: {result['error']}")
            return
        
        total_transactions = result.get('total', 0)
        
        message = f"""
📊 СТАТИСТИКА БАЗЫ ДАННЫХ

👤 Пользователь: {update.effective_user.first_name}
📋 Всего транзакций: {total_transactions}
📄 Страниц данных: {result.get('pages', 0)}

🔄 Последнее обновление: сейчас
💾 Резервное копирование: ежедневно в 00:00

Для экспорта всех данных используйте команду /export
"""
        
        await update.message.reply_text(message)
    
    except Exception as e:
        await update.message.reply_text(f"Ошибка при обработке команды: {str(e)}")

async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /export"""
    user_id = update.effective_user.id
    
    try:
        await update.message.reply_text("📤 Подготавливаю экспорт данных...")
        
        # Получаем данные для экспорта
        result = api_client.export_transactions(user_id)
        
        if 'error' in result:
            await update.message.reply_text(f"Ошибка при экспорте: {result['error']}")
            return
        
        export_data = result.get('data', [])
        
        if not export_data:
            await update.message.reply_text("Нет данных для экспорта.")
            return
        
        # Создаем JSON файл для отправки
        json_data = json.dumps(export_data, ensure_ascii=False, indent=2)
        file_buffer = io.BytesIO(json_data.encode('utf-8'))
        file_buffer.name = f"transactions_{user_id}.json"
        
        await update.message.reply_document(
            document=file_buffer,
            filename=f"TBCparcer_export_{user_id}.json",
            caption=f"📊 Экспорт завершен!\n\nВсего транзакций: {len(export_data)}\n\nДанные в формате JSON для дальнейшей обработки."
        )
    
    except Exception as e:
        await update.message.reply_text(f"Ошибка при экспорте: {str(e)}")

async def add_operator_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /add_operator"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "Использование: /add_operator Название - Описание\n"
            "Пример: /add_operator НОВЫЙ БАНК - Мое приложение"
        )
        return
    
    try:
        # Парсим аргументы
        full_text = ' '.join(context.args)
        if ' - ' in full_text:
            name, description = full_text.split(' - ', 1)
        else:
            name = full_text
            description = None
        
        # Создаем оператора
        result = api_client.create_operator(user_id, name.strip(), description.strip() if description else None)
        
        if 'error' in result:
            await update.message.reply_text(f"Ошибка при создании оператора: {result['error']}")
            return
        
        operator = result.get('operator', {})
        message = f"✅ Персональный оператор создан:\n\n"
        message += f"📝 Название: {operator['name']}\n"
        if operator['description']:
            message += f"📋 Описание: {operator['description']}\n"
        message += f"🆔 ID: {operator['id']}"
        
        await update.message.reply_text(message)
    
    except Exception as e:
        await update.message.reply_text(f"Ошибка при создании оператора: {str(e)}")

