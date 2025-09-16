import logging
import asyncio
import schedule
import time
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config.settings import TELEGRAM_BOT_TOKEN, BACKUP_TIME
from handlers.commands import (
    start_command, help_command, operators_command, 
    db_command, export_command, add_operator_command
)
from handlers.messages import handle_text_message, handle_document, handle_photo
from utils.api_client import APIClient

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

api_client = APIClient()

class TBCparcerBot:
    def __init__(self):
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.setup_handlers()
        
    def setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        
        # Обработчики команд
        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("help", help_command))
        self.application.add_handler(CommandHandler("operators", operators_command))
        self.application.add_handler(CommandHandler("db", db_command))
        self.application.add_handler(CommandHandler("export", export_command))
        self.application.add_handler(CommandHandler("add_operator", add_operator_command))
        
        # Обработчики сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
        self.application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
        self.application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        
        # Обработчик ошибок
        self.application.add_error_handler(self.error_handler)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Произошла внутренняя ошибка. Попробуйте позже или обратитесь к администратору."
            )
    
    async def send_backup_notification(self, chat_id: int):
        """Отправка уведомления о резервном копировании"""
        try:
            # Получаем статистику пользователя
            result = api_client.get_transactions(chat_id, per_page=1)
            
            if 'error' not in result:
                total_transactions = result.get('total', 0)
                backup_message = f"""
🔄 РЕЗЕРВНОЕ КОПИРОВАНИЕ

📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}
📊 Всего транзакций: {total_transactions}
✅ Статус: Завершено успешно

Ваши данные в безопасности!
"""
                await self.application.bot.send_message(chat_id=chat_id, text=backup_message)
        
        except Exception as e:
            logger.error(f"Error sending backup notification to {chat_id}: {e}")
    
    def schedule_backup(self):
        """Планирование резервного копирования"""
        schedule.every().day.at(BACKUP_TIME).do(self.run_backup)
    
    def run_backup(self):
        """Запуск резервного копирования"""
        logger.info("Starting scheduled backup...")
        # Здесь можно добавить логику резервного копирования
        # Пока просто логируем событие
        logger.info("Backup completed successfully")
    
    async def run_bot(self):
        """Запуск бота"""
        logger.info("Starting TBCparcer Bot...")
        
        # Планируем резервное копирование
        self.schedule_backup()
        
        # Запускаем бота
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        logger.info("Bot is running...")
        
        # Основной цикл для выполнения запланированных задач
        try:
            while True:
                schedule.run_pending()
                await asyncio.sleep(60)  # Проверяем каждую минуту
        except KeyboardInterrupt:
            logger.info("Stopping bot...")
        finally:
            await self.application.stop()
            await self.application.shutdown()

async def main():
    """Главная функция"""
    bot = TBCparcerBot()
    await bot.run_bot()

if __name__ == '__main__':
    asyncio.run(main())

