#!/usr/bin/env python3
"""
Скрипт для инициализации тестовых данных в базе данных TBCparcer
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.main import app
from src.models.user import User, db
from src.models.transaction import Transaction
from src.models.operator import Operator
from datetime import datetime

def init_test_data():
    """Инициализация тестовых данных"""
    with app.app_context():
        # Создаем таблицы
        db.create_all()
        
        # Создаем тестового пользователя
        test_user = User.get_or_create_user(
            telegram_id=123456789,
            username="test_user"
        )
        
        # Создаем операторов из словаря заказчика (используем реальные названия)
        operators_data = [
            {"name": "NBU 2P2 U PLAT UZCARD, 99", "description": "Milliy 2.0"},
            {"name": "OQ P2P, UZ", "description": "OQ"},
            {"name": "UZCARD PLYUS P2P, 99", "description": "Joyda"},
            {"name": "UPAY P2P", "description": "Humans"},
        ]
        
        for op_data in operators_data:
            existing_op = Operator.query.filter_by(
                name=op_data["name"], 
                user_id=test_user.id
            ).first()
            if not existing_op:
                operator = Operator(
                    name=op_data["name"],
                    description=op_data["description"],
                    user_id=test_user.id
                )
                db.session.add(operator)
        
        # Получаем операторов для связи (используем реальные названия)
        nbu_op = Operator.query.filter_by(name="NBU 2P2 U PLAT UZCARD, 99", user_id=test_user.id).first()
        oq_op = Operator.query.filter_by(name="OQ P2P, UZ", user_id=test_user.id).first()
        uzcard_op = Operator.query.filter_by(name="UZCARD PLYUS P2P, 99", user_id=test_user.id).first()
        upay_op = Operator.query.filter_by(name="UPAY P2P", user_id=test_user.id).first()
        
        # Создаем тестовые транзакции с реальными операторами
        test_transactions = [
            {
                "date_time": datetime(2025, 4, 4, 18, 46),
                "operation_type": "payment",
                "amount": 6000000,
                "currency": "UZS",
                "card_number": "*6714",
                "description": "Оплата через UPAY",
                "balance": 935000.4,
                "operator_id": upay_op.id if upay_op else None,
                "raw_text": "UPAY P2P: Оплата 6000000 UZS, карта *6714, баланс 935000.4",
                "user_id": test_user.id
            },
            {
                "date_time": datetime(2025, 4, 5, 12, 58),
                "operation_type": "refill",
                "amount": 400000,
                "currency": "UZS",
                "card_number": "*6714",
                "description": "Пополнение через OQ",
                "balance": 535000.4,
                "operator_id": oq_op.id if oq_op else None,
                "raw_text": "OQ P2P, UZ: Пополнение 400000 UZS, карта *6714, баланс 535000.4",
                "user_id": test_user.id
            },
            {
                "date_time": datetime(2025, 4, 6, 23, 0),
                "operation_type": "conversion",
                "amount": 11488000,
                "currency": "UZS",
                "card_number": "*6714",
                "description": "Конверсия через UPAY",
                "balance": 11818000,
                "operator_id": upay_op.id if upay_op else None,
                "raw_text": "UPAY P2P: Конверсия 11488000 UZS, карта *6714, баланс 11818000",
                "user_id": test_user.id
            },
            {
                "date_time": datetime(2025, 4, 2, 8, 37),
                "operation_type": "payment",
                "amount": 44000,
                "currency": "UZS",
                "card_number": "*0907",
                "description": "Оплата через UZCARD",
                "balance": 2607792.5,
                "operator_id": uzcard_op.id if uzcard_op else None,
                "raw_text": "UZCARD PLYUS P2P, 99: Оплата 44000 UZS, карта *0907, баланс 2607792.5",
                "user_id": test_user.id
            },
            {
                "date_time": datetime(2025, 4, 14, 10, 29),
                "operation_type": "cancel",
                "amount": 37,
                "currency": "USD",
                "card_number": "*6905",
                "description": "Отмена операции NBU",
                "balance": 0,
                "operator_id": nbu_op.id if nbu_op else None,
                "raw_text": "NBU 2P2 U PLAT UZCARD, 99: Отмена 37 USD, карта *6905, баланс 0",
                "user_id": test_user.id
            }
        ]
        
        # Удаляем старые транзакции
        Transaction.query.filter_by(user_id=test_user.id).delete()
        
        # Добавляем новые транзакции
        for trans_data in test_transactions:
            transaction = Transaction(**trans_data)
            db.session.add(transaction)
        
        # Сохраняем изменения
        db.session.commit()
        
        print(f"✅ Тестовые данные успешно созданы!")
        print(f"   - Пользователь: {test_user.username} (ID: {test_user.telegram_id})")
        print(f"   - Операторы: {len(operators_data)}")
        print(f"   - Транзакции: {len(test_transactions)}")

if __name__ == "__main__":
    init_test_data()

