"""End-to-end pipeline that connects parsing, database and export services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Sequence, Tuple

from sqlalchemy.exc import SQLAlchemyError

from src.models.operator import Operator
from src.models.transaction import Transaction
from src.models.user import User, db
from src.services.ai_parser import AIParsingService


class ReceiptProcessingError(Exception):
    """Base exception for predictable pipeline errors."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class DuplicateTransactionError(ReceiptProcessingError):
    """Raised when a transaction with the same raw text already exists."""

    transaction: Transaction

    def __init__(self, transaction: Transaction):
        super().__init__('Duplicate transaction detected', status_code=409)
        self.transaction = transaction


class ReceiptPipeline:
    """Service that glues together parser, operator dictionary and database."""

    def __init__(self, parser: Optional[AIParsingService] = None):
        self._parser = parser or AIParsingService()

    @property
    def parser(self) -> AIParsingService:
        """Expose underlying AI parsing service for advanced scenarios."""
        return self._parser

    def get_operators_for_user(self, user: Optional[User]) -> Sequence[Operator]:
        """Public helper that exposes available operators for a user."""
        return self._load_operators_for_user(user)

    def parse_receipt(
        self,
        receipt_text: str,
        telegram_id: Optional[int] = None,
    ) -> Tuple[Dict, Optional[User]]:
        """
        Parse receipt text and enrich the result with operator information.

        Args:
            receipt_text: raw receipt text provided by the user.
            telegram_id: optional telegram id to load user specific operators.

        Returns:
            Tuple of enhanced parsed data and user instance (if any).
        """

        parsed_data = self._parser.parse_receipt(receipt_text)
        if 'error' in parsed_data:
            raise ReceiptProcessingError(parsed_data['error'], status_code=400)

        user = self._resolve_user(telegram_id)
        operators = self._load_operators_for_user(user)
        enhanced_data = self._parser.enhance_with_operator_info(parsed_data, operators)

        return enhanced_data, user

    def parse_and_store_receipt(
        self,
        receipt_text: str,
        telegram_id: int,
        username: Optional[str] = None,
    ) -> Tuple[Transaction, Dict]:
        """Parse receipt, persist transaction and return enriched payload."""

        user = User.get_or_create_user(telegram_id, username)

        existing = Transaction.query.filter_by(
            user_id=user.id,
            raw_text=receipt_text,
        ).first()
        if existing:
            raise DuplicateTransactionError(existing)

        enhanced_data, _ = self.parse_receipt(receipt_text, telegram_id)

        parsed_datetime = self._parse_datetime(enhanced_data.get('date_time'))
        if not parsed_datetime:
            raise ReceiptProcessingError('Неверный формат даты операции')

        amount = self._to_float(enhanced_data.get('amount'))
        if amount is None:
            raise ReceiptProcessingError('Неверный формат суммы операции')

        balance = self._to_float(enhanced_data.get('balance'))
        operator_id = self._resolve_operator_id(enhanced_data, user.id)

        transaction = Transaction(
            user_id=user.id,
            date_time=parsed_datetime,
            operation_type=enhanced_data.get('operation_type', 'payment'),
            amount=amount,
            currency=enhanced_data.get('currency', 'UZS'),
            card_number=enhanced_data.get('card_number'),
            description=enhanced_data.get('description'),
            balance=balance,
            operator_id=operator_id,
            raw_text=receipt_text,
        )

        try:
            db.session.add(transaction)
            db.session.commit()
        except SQLAlchemyError as exc:  # pragma: no cover - defensive
            db.session.rollback()
            raise ReceiptProcessingError(
                f'Не удалось сохранить транзакцию: {exc}'
            ) from exc

        return transaction, enhanced_data

    def _resolve_user(self, telegram_id: Optional[int]) -> Optional[User]:
        if telegram_id is None:
            return None
        try:
            return User.query.filter_by(telegram_id=int(telegram_id)).first()
        except (TypeError, ValueError):
            raise ReceiptProcessingError('Некорректный telegram_id', status_code=400)

    def _load_operators_for_user(self, user: Optional[User]) -> Sequence[Operator]:
        if user:
            return Operator.get_operators_for_user(user.id)
        return Operator.get_global_operators()

    def _resolve_operator_id(self, parsed_data: Dict, user_id: int) -> Optional[int]:
        operator_id_value = parsed_data.get('operator_id')
        if operator_id_value not in (None, '', []):
            try:
                operator_id_int = int(operator_id_value)
            except (TypeError, ValueError):
                raise ReceiptProcessingError('operator_id must be an integer')

            operator = Operator.query.filter_by(id=operator_id_int).first()
            if not operator:
                raise ReceiptProcessingError('Operator not found', status_code=404)
            if operator.user_id and operator.user_id != user_id:
                raise ReceiptProcessingError('Operator does not belong to user', status_code=403)
            return operator.id

        description = parsed_data.get('description')
        if description:
            operator = Operator.find_operator_by_description(description, user_id)
            if operator:
                return operator.id
        return None

    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None

        normalized = value.replace('T', ' ').replace('Z', '+00:00')
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            for fmt in ('%Y-%m-%d %H:%M:%S', '%d.%m.%Y %H:%M:%S', '%Y-%m-%d %H:%M'):
                try:
                    parsed = datetime.strptime(normalized, fmt)
                    break
                except ValueError:
                    continue
            else:
                return None

        if parsed.tzinfo:
            parsed = parsed.replace(tzinfo=None)
        return parsed

    def _to_float(self, value) -> Optional[float]:
        if value in (None, ''):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

