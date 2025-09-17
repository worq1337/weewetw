from flask import Blueprint, jsonify, request

from src.models.formatting import FormattingSetting
from typing import Optional

from flask import Blueprint, jsonify, request

from src.models.formatting import FormattingSetting
from src.models.user import User, db


formatting_bp = Blueprint('formatting', __name__)


def _get_user_by_telegram(telegram_id: str) -> Optional[User]:
    try:
        telegram_int = int(telegram_id)
    except (TypeError, ValueError):
        return None

    return User.query.filter_by(telegram_id=telegram_int).first()


@formatting_bp.route('/formatting/columns', methods=['GET'])
def get_column_formatting():
    telegram_id = request.args.get('telegram_id')
    if not telegram_id:
        return jsonify({'error': 'telegram_id is required'}), 400

    user = _get_user_by_telegram(telegram_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    settings = FormattingSetting.query.filter_by(user_id=user.id).all()
    columns = {}
    for setting in settings:
        columns[setting.column_name] = {
            'alignment': setting.alignment,
            'width': setting.width,
            'position': setting.position,
        }

    return jsonify({'columns': columns})


@formatting_bp.route('/formatting/columns/<string:column_name>', methods=['PUT'])
def update_column_formatting(column_name: str):
    data = request.get_json() or {}

    telegram_id = data.get('telegram_id')
    if not telegram_id:
        return jsonify({'error': 'telegram_id is required'}), 400

    user = _get_user_by_telegram(telegram_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    alignment = data.get('alignment')
    if alignment is not None and alignment not in {'left', 'center', 'right'}:
        return jsonify({'error': 'alignment must be one of left, center, right'}), 400

    setting = FormattingSetting.query.filter_by(user_id=user.id, column_name=column_name).first()

    try:
        if alignment is None:
            if setting:
                db.session.delete(setting)
                db.session.commit()
            return jsonify({'column_name': column_name, 'alignment': None})

        if not setting:
            setting = FormattingSetting(user_id=user.id, column_name=column_name)

        setting.alignment = alignment
        db.session.add(setting)
        db.session.commit()

        return jsonify({'column_name': column_name, 'alignment': alignment})
    except Exception as exc:  # pragma: no cover - defensive logging
        db.session.rollback()
        return jsonify({'error': f'Failed to update column formatting: {exc}'}), 500
