"""Healthcheck endpoint for infrastructure monitoring."""

from __future__ import annotations

import os
import platform
from datetime import datetime
from typing import Dict

from flask import Blueprint, current_app, jsonify
from sqlalchemy import text

from src.models.user import db


health_bp = Blueprint('health', __name__)


def _check_database() -> Dict[str, str]:
    """Execute a simple query to ensure the database is reachable."""

    try:
        db.session.execute(text('SELECT 1'))
        return {'status': 'ok'}
    except Exception as exc:  # pragma: no cover - executed in runtime environments
        current_app.logger.warning('Healthcheck database failure: %s', exc)
        return {'status': 'error', 'details': str(exc)}


@health_bp.route('/health', methods=['GET'])
def healthcheck():
    """Return the current status of the service and dependencies."""

    database_status = _check_database()
    openai_configured = bool(os.getenv('OPENAI_API_KEY'))

    status_code = 200 if database_status.get('status') == 'ok' else 503

    payload = {
        'status': 'ok' if status_code == 200 else 'degraded',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'application': {
            'version': os.getenv('APP_VERSION', 'unknown'),
            'environment': os.getenv('APP_ENV', 'development'),
        },
        'runtime': {
            'python': platform.python_version(),
            'platform': platform.platform(),
        },
        'database': database_status,
        'openai': {
            'status': 'configured' if openai_configured else 'disabled',
        },
    }

    return jsonify(payload), status_code
