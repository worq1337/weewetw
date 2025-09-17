import json
import os
import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.app_factory import create_app
from src.models.user import db
from src.services import operator_dictionary as dictionary_module

INITIAL_DICTIONARY = {
    "version": 1,
    "operators": {
        "Humans": {"display_name": "Humans"},
    },
    "applications": {
        "Humans": {"operator": "Humans"},
    },
    "aliases": [
        {"alias": "UPAY P2P", "operator": "Humans", "application": "Humans"},
    ],
}


@pytest.fixture()
def app(tmp_path, monkeypatch):
    database_path = tmp_path / 'dictionary.db'
    dictionary_path = tmp_path / 'operators_dict.json'
    dictionary_path.write_text(json.dumps(INITIAL_DICTIONARY, ensure_ascii=False, indent=2), encoding='utf-8')

    monkeypatch.setenv('OPERATORS_DICTIONARY_PATH', str(dictionary_path))
    monkeypatch.setenv('DICT_ADMIN_TOKEN', 'secret-token')
    os.environ.pop('OPENAI_API_KEY', None)

    dictionary_module._DICTIONARY_INSTANCE = None

    app = create_app(
        {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': f'sqlite:///{database_path}',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'DICT_ADMIN_TOKEN': 'secret-token',
        }
    )

    yield app, dictionary_path

    with app.app_context():
        db.session.remove()
        db.drop_all()

    dictionary_module._DICTIONARY_INSTANCE = None


@pytest.fixture()
def client(app):
    app_instance, _ = app
    return app_instance.test_client()


def test_reload_requires_authorization(client):
    response = client.post('/api/dictionary/reload')
    assert response.status_code == 401
    payload = response.get_json()
    assert payload['status'] == 'error'
    assert 'WWW-Authenticate' in response.headers


def test_reload_rejects_invalid_token(client):
    response = client.post(
        '/api/dictionary/reload',
        headers={'Authorization': 'Bearer wrong-token'},
    )
    assert response.status_code == 403
    payload = response.get_json()
    assert payload['status'] == 'error'
    assert 'WWW-Authenticate' in response.headers


def test_reload_refreshes_dictionary_and_metadata(app, client):
    _, dictionary_path = app

    updated_dictionary = {
        "version": 2,
        "operators": {
            "Humans": {"display_name": "Humans"},
            "Payme": {"display_name": "Payme"},
        },
        "applications": {
            "Humans": {"operator": "Humans"},
            "Payme": {"operator": "Payme"},
        },
        "aliases": [
            {"alias": "UPAY P2P", "operator": "Humans", "application": "Humans"},
            {"alias": "PAYME P2P, UZ", "operator": "Payme", "application": "Payme"},
        ],
    }
    dictionary_path.write_text(json.dumps(updated_dictionary, ensure_ascii=False, indent=2), encoding='utf-8')

    response = client.post(
        '/api/dictionary/reload',
        headers={'Authorization': 'Bearer secret-token'},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload['status'] == 'ok'
    assert payload['entries'] == 2
    assert payload['metadata'] == {'operators': 2, 'applications': 2}
    assert 'reloaded_at' in payload
    assert payload['before_entries'] == 1
    assert payload['after_entries'] == 2

    dictionary = dictionary_module.get_operator_dictionary()
    lookup = dictionary.lookup('PAYME P2P, UZ')
    assert lookup
    assert lookup['operator'] == 'Payme'
