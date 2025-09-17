import os
import sys
from pathlib import Path

import pytest
from flask import Flask

BACKEND_ROOT = Path(__file__).resolve().parents[2] / 'backend' / 'tbcparcer_api'
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.models.user import db  # noqa: E402
from src.routes.user import user_bp  # noqa: E402
from src.routes.transaction import transaction_bp  # noqa: E402
from src.routes.ai_parsing import ai_parsing_bp  # noqa: E402
from src.routes.export import export_bp  # noqa: E402


@pytest.fixture(scope='session')
def app(tmp_path_factory):
    """Create a Flask app with an isolated SQLite database for E2E tests."""
    os.environ.pop('OPENAI_API_KEY', None)
    os.environ.setdefault(
        'OPERATORS_DICTIONARY_PATH',
        str(BACKEND_ROOT / 'data' / 'operators_dict.json')
    )

    database_dir = tmp_path_factory.mktemp('e2e-db')
    database_path = database_dir / 'app.db'

    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f'sqlite:///{database_path}',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(app)
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(transaction_bp, url_prefix='/api')
    app.register_blueprint(ai_parsing_bp, url_prefix='/api/ai')
    app.register_blueprint(export_bp, url_prefix='/api/export')

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    """Provide a Flask test client for API calls."""
    return app.test_client()
