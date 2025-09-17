import json
import os
from datetime import datetime, timezone
from http import HTTPStatus
from typing import Optional

from flask import Blueprint, current_app, jsonify, request

from src.services.operator_dictionary import (
    get_operator_dictionary,
    normalize_operator_value,
    reload_operator_dictionary,
)

_SAMPLE_ALIASES = [
    'UPAY P2P',
    'PAYME P2P, UZ',
    'TENGE 24 P2P UZCARD HUMO, UZ',
    'Unknown provider',
]


def _collect_examples(dictionary):
    examples = []
    for raw_value in _SAMPLE_ALIASES:
        normalized_value = normalize_operator_value(raw_value, dictionary)
        dictionary_entry = dictionary.lookup(raw_value)
        examples.append({
            'input': raw_value,
            'normalized': normalized_value,
            'matched': bool(dictionary_entry),
            'alias': dictionary_entry.get('alias') if dictionary_entry else None,
            'operator': dictionary_entry.get('operator') if dictionary_entry else None,
            'application': dictionary_entry.get('application') if dictionary_entry else None,
        })
    return examples


def _load_dictionary_metadata(dictionary) -> dict:
    try:
        with dictionary.path.open('r', encoding='utf-8') as stream:
            data = json.load(stream)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

    operators = data.get('operators') if isinstance(data, dict) else {}
    applications = data.get('applications') if isinstance(data, dict) else {}
    if not isinstance(operators, dict):
        operators = {}
    if not isinstance(applications, dict):
        applications = {}

    return {
        'operators': len(operators),
        'applications': len(applications),
    }


def _build_auth_error(status: HTTPStatus, message: str):
    response = jsonify({'status': 'error', 'message': message})
    response.status_code = int(status)
    if status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
        response.headers['WWW-Authenticate'] = 'Bearer'
    return response


def _resolve_expected_token() -> Optional[str]:
    configured = current_app.config.get('DICT_ADMIN_TOKEN')
    if configured:
        return str(configured)
    env_token = os.getenv('DICT_ADMIN_TOKEN')
    if env_token:
        return env_token
    return None


def _ensure_authorized():
    expected_token = _resolve_expected_token()
    if not expected_token:
        current_app.logger.warning('Dictionary admin token is not configured')
        return _build_auth_error(
            HTTPStatus.SERVICE_UNAVAILABLE,
            'Dictionary admin token is not configured',
        )

    header = request.headers.get('Authorization', '')
    scheme, _, token = header.partition(' ')
    if scheme.lower() != 'bearer' or not token:
        return _build_auth_error(
            HTTPStatus.UNAUTHORIZED,
            'Authorization header must contain Bearer token',
        )
    if token != expected_token:
        current_app.logger.warning('Rejected dictionary reload with invalid token')
        return _build_auth_error(
            HTTPStatus.FORBIDDEN,
            'Provided token is not allowed',
        )
    return None


dictionary_bp = Blueprint('dictionary', __name__)


@dictionary_bp.route('/dictionary/reload', methods=['POST'])
def reload_dictionary():
    auth_error = _ensure_authorized()
    if auth_error:
        return auth_error

    dictionary = get_operator_dictionary()
    before_entries = dictionary.size()
    before_examples = _collect_examples(dictionary)

    try:
        reload_result = reload_operator_dictionary()
    except FileNotFoundError:
        return jsonify({'status': 'error', 'message': 'Dictionary file not found'}), 500
    except ValueError as error:
        return jsonify({'status': 'error', 'message': str(error)}), 400

    after_examples = _collect_examples(dictionary)
    metadata = _load_dictionary_metadata(dictionary)

    current_app.logger.info(
        'Operator dictionary hot-reloaded: %d entries (before=%d)',
        reload_result['entries'],
        before_entries,
    )

    payload = {
        'status': 'ok',
        'entries': reload_result['entries'],
        'changed': reload_result['changed'],
        'before_entries': before_entries,
        'after_entries': dictionary.size(),
        'path': str(dictionary.path),
        'metadata': metadata,
        'dictionary': {
            'version': reload_result.get('version'),
            'checksum': reload_result.get('checksum'),
            'sources': dictionary.sources(),
        },
        'reloaded_at': datetime.now(timezone.utc).isoformat(),
        'examples': {
            'before': before_examples,
            'after': after_examples,
        },
    }
    return jsonify(payload)
