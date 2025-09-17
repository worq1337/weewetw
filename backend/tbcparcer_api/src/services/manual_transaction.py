import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from src.models.operator import Operator
from src.models.transaction import Transaction
from src.models.user import User, db

ALLOWED_OPERATION_TYPES = {'payment', 'refill', 'conversion', 'cancel'}
ALLOWED_CURRENCIES = {'UZS', 'USD', 'EUR', 'RUB'}
CARD_NUMBER_PATTERN = re.compile(r'^\d{4}$')


class ManualTransactionError(Exception):
    """Ошибка валидации ручной транзакции"""

    def __init__(self, message: str, status_code: int = 400, *, extra: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.extra = extra or {}


@dataclass
class ManualTransactionContext:
    user: User
    transaction_kwargs: Dict[str, Any]
    generated_raw_text: bool


def _normalize_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    string_value = str(value).strip()
    return string_value or None


def _parse_datetime(value: Any) -> datetime:
    normalized = _normalize_string(value)
    if not normalized:
        raise ManualTransactionError('date_time is required')

    try:
        parsed = datetime.fromisoformat(normalized.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ManualTransactionError('Invalid date_time format') from exc

    if parsed.tzinfo:
        parsed = parsed.replace(tzinfo=None)

    parsed = parsed.replace(second=0, microsecond=0)

    return parsed


def _parse_operation_type(value: Any) -> str:
    operation_type = _normalize_string(value)
    if not operation_type:
        raise ManualTransactionError('operation_type is required')

    operation_type = operation_type.lower()
    if operation_type not in ALLOWED_OPERATION_TYPES:
        raise ManualTransactionError('operation_type must be one of payment, refill, conversion, cancel')

    return operation_type


def _parse_currency(value: Any) -> str:
    currency = _normalize_string(value) or 'UZS'
    currency = currency.upper()
    if currency not in ALLOWED_CURRENCIES:
        raise ManualTransactionError('currency must be one of UZS, USD, EUR, RUB')
    return currency


def _parse_amount(value: Any) -> float:
    try:
        amount = float(value)
    except (TypeError, ValueError) as exc:
        raise ManualTransactionError('amount must be a number') from exc

    if amount <= 0:
        raise ManualTransactionError('amount must be greater than zero')

    return amount


def _parse_balance(value: Any) -> Optional[float]:
    if value in (None, '', []):
        return None

    try:
        balance = float(value)
    except (TypeError, ValueError) as exc:
        raise ManualTransactionError('balance must be a number') from exc

    if balance < 0:
        raise ManualTransactionError('balance must be greater or equal to zero')

    return balance


def _parse_card_number(value: Any) -> Optional[str]:
    card_number = _normalize_string(value)
    if not card_number:
        return None

    if not CARD_NUMBER_PATTERN.fullmatch(card_number):
        raise ManualTransactionError('card_number must contain exactly 4 digits')

    return card_number


def _resolve_operator(value: Any, description: Optional[str], user: User) -> Optional[Operator]:
    if value in (None, '', []):
        if description:
            return Operator.find_operator_by_description(description, user.id)
        return None

    try:
        operator_id = int(value)
    except (TypeError, ValueError) as exc:
        raise ManualTransactionError('operator_id must be an integer') from exc

    operator = Operator.query.filter_by(id=operator_id).first()
    if not operator:
        raise ManualTransactionError('Operator not found', status_code=404)

    if operator.user_id and operator.user_id != user.id:
        raise ManualTransactionError('Operator does not belong to user', status_code=403)

    return operator


def prepare_manual_transaction(data: Dict[str, Any]) -> ManualTransactionContext:
    if not isinstance(data, dict):
        raise ManualTransactionError('Invalid payload format')

    if 'telegram_id' not in data:
        raise ManualTransactionError('telegram_id is required')

    try:
        telegram_id = int(data['telegram_id'])
    except (TypeError, ValueError) as exc:
        raise ManualTransactionError('telegram_id must be an integer') from exc

    user = User.get_or_create_user(telegram_id, data.get('username'))

    description = _normalize_string(data.get('description'))
    if not description:
        raise ManualTransactionError('description is required')

    raw_text_provided = _normalize_string(data.get('raw_text'))
    if raw_text_provided and len(raw_text_provided) > 4000:
        raise ManualTransactionError('raw_text length must not exceed 4000 characters')

    parsed_datetime = _parse_datetime(data.get('date_time'))
    operation_type = _parse_operation_type(data.get('operation_type'))
    amount = _parse_amount(data.get('amount'))
    currency = _parse_currency(data.get('currency'))
    balance = _parse_balance(data.get('balance'))
    card_number = _parse_card_number(data.get('card_number'))
    operator = _resolve_operator(data.get('operator_id'), description, user)

    raw_text = raw_text_provided
    generated_raw_text = False
    if not raw_text:
        generated_raw_text = True
        raw_text_parts = [
            f'Manual entry: {parsed_datetime.strftime("%Y-%m-%d %H:%M")}',
            f'{amount:.2f} {currency}'
        ]
        if description:
            raw_text_parts.append(description)
        raw_text = ' — '.join(raw_text_parts)

    duplicate = Transaction.query.filter_by(
        user_id=user.id,
        raw_text=raw_text
    ).first()

    if duplicate:
        raise ManualTransactionError(
            'Duplicate transaction',
            status_code=409,
            extra={'transaction': duplicate.to_dict()}
        )

    transaction_kwargs = {
        'user_id': user.id,
        'date_time': parsed_datetime,
        'operation_type': operation_type,
        'amount': amount,
        'currency': currency,
        'card_number': card_number,
        'description': description,
        'balance': balance,
        'operator_id': operator.id if operator else None,
        'raw_text': raw_text,
    }

    return ManualTransactionContext(
        user=user,
        transaction_kwargs=transaction_kwargs,
        generated_raw_text=generated_raw_text,
    )


def create_manual_transaction(data: Dict[str, Any]) -> Tuple[Transaction, ManualTransactionContext]:
    context = prepare_manual_transaction(data)

    transaction = Transaction(**context.transaction_kwargs)
    db.session.add(transaction)
    db.session.commit()

    return transaction, context

