import os
import sys
import os
import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.app_factory import create_app
from src.models.user import db
from src.utils.errors import APIError
DICTIONARY_PATH = BACKEND_ROOT / 'data' / 'operators_dict.json'


@pytest.fixture()
def app(tmp_path):
    """Provide an application with an isolated SQLite database."""
    os.environ.pop('OPENAI_API_KEY', None)
    os.environ.setdefault('OPERATORS_DICTIONARY_PATH', str(DICTIONARY_PATH))

    database_path = tmp_path / 'health-tests.db'

    app = create_app(
        {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': f'sqlite:///{database_path}',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        }
    )

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def test_health_endpoint_includes_request_id(client):
    response = client.get('/health', headers={'X-Request-ID': 'health-check'})
    assert response.status_code in (200, 503)

    payload = response.get_json()
    assert payload['status'] in {'ok', 'degraded'}
    assert payload.get('database')
    assert payload.get('dictionary')
    assert payload['request_id'] == 'health-check'
    assert response.headers['X-Request-ID'] == 'health-check'


def test_api_error_handler_returns_metadata(app):
    @app.route('/api/test-error')
    def _trigger_error():
        raise APIError(409, 'Conflict occurred', error='Conflict', details={'reason': 'duplicate'})

    test_client = app.test_client()
    response = test_client.get('/api/test-error', headers={'X-Request-ID': 'req-123'})

    assert response.status_code == 409
    payload = response.get_json()
    assert payload['status'] == 'error'
    assert payload['error'] == 'Conflict'
    assert payload['message'] == 'Conflict occurred'
    assert payload['request_id'] == 'req-123'
    assert payload['details'] == {'reason': 'duplicate'}
    assert response.headers['X-Request-ID'] == 'req-123'
