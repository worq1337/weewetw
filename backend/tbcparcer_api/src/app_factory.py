"""Application factory that wires together services and blueprints."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from src.models.user import db
from src.services.operator_dictionary import get_operator_dictionary
from src.utils.http import api_error, ensure_request_id


def _default_database_uri() -> str:
    """Return the default SQLite connection string used by the API."""

    database_dir = os.path.join(os.path.dirname(__file__), 'database')
    os.makedirs(database_dir, exist_ok=True)
    return f"sqlite:///{os.path.join(database_dir, 'app.db')}"


def create_app(config: Optional[Dict[str, Any]] = None) -> Flask:
    """Create and configure Flask application instance."""

    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), 'static'),
    )

    app.config.setdefault('SECRET_KEY', 'tbcparcer_secret_key_2025')
    app.config.setdefault('SQLALCHEMY_DATABASE_URI', _default_database_uri())
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)

    if config:
        app.config.update(config)

    CORS(app, origins="*")

    db.init_app(app)

    _register_blueprints(app)
    _register_error_handlers(app)
    _initialise_database(app)
    _register_static_routes(app)

    return app


def _register_blueprints(app: Flask) -> None:
    """Attach API blueprints to the Flask application."""

    from src.routes.ai_parsing import ai_parsing_bp
    from src.routes.dictionary import dictionary_bp
    from src.routes.export import export_bp
    from src.routes.formatting import formatting_bp
    from src.routes.health import health_bp
    from src.routes.operator import operator_bp
    from src.routes.transaction import transaction_bp
    from src.routes.trash import trash_bp
    from src.routes.user import user_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(transaction_bp, url_prefix='/api')
    app.register_blueprint(operator_bp, url_prefix='/api')
    app.register_blueprint(formatting_bp, url_prefix='/api')
    app.register_blueprint(ai_parsing_bp, url_prefix='/api/ai')
    app.register_blueprint(export_bp, url_prefix='/api/export')
    app.register_blueprint(trash_bp, url_prefix='/api')
    app.register_blueprint(dictionary_bp, url_prefix='/api')


def _register_error_handlers(app: Flask) -> None:
    """Configure centralised error handling for the API."""

    from src.services.manual_transaction import ManualTransactionError
    from src.services.receipt_pipeline import ReceiptProcessingError
    from src.utils.errors import APIError

    def _get_request_path() -> str:
        try:
            return request.path
        except RuntimeError:
            return ''

    def _is_api_request(path: str) -> bool:
        return path.startswith('/api')

    def _build_error_response(
        status_code: int,
        error: str,
        message: str,
        *,
        details: Optional[Dict[str, Any]] = None,
    ):
        path = _get_request_path()
        request_id = ensure_request_id(request.headers.get('X-Request-ID'))
        return api_error(
            status_code,
            error,
            message,
            path=path,
            request_id=request_id,
            details=details,
        )

    @app.errorhandler(APIError)
    def handle_api_error(error: APIError):
        return _build_error_response(
            error.status_code,
            error.error,
            str(error),
            details=error.details,
        )

    @app.errorhandler(ManualTransactionError)
    def handle_manual_transaction_error(error: ManualTransactionError):
        return _build_error_response(
            error.status_code,
            'Manual transaction error',
            str(error),
            details=getattr(error, 'extra', None),
        )

    @app.errorhandler(ReceiptProcessingError)
    def handle_receipt_processing_error(error: ReceiptProcessingError):
        return _build_error_response(
            error.status_code,
            'Receipt processing error',
            str(error),
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):  # pragma: no cover - thin wrapper
        path = _get_request_path()
        if _is_api_request(path):
            return _build_error_response(
                error.code,
                error.name,
                error.description,
            )
        return error

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error: Exception):  # pragma: no cover - safety net
        path = _get_request_path()
        app.logger.exception('Unhandled exception on %s', path or 'unknown path')

        if _is_api_request(path):
            return _build_error_response(
                500,
                'Internal Server Error',
                'Произошла непредвиденная ошибка',
                details={'exception': str(error)},
            )

        return app.handle_exception(error)


def _initialise_database(app: Flask) -> None:
    """Create database schema and populate reference data."""

    from src.models.formatting import CellColor, FormattingSetting  # noqa: F401
    from src.models.operator import Operator
    from src.models.transaction import Transaction  # noqa: F401

    with app.app_context():
        db.create_all()

        try:
            dictionary = get_operator_dictionary()
            app.logger.info(
                'Loaded operator dictionary with %d entries',
                dictionary.size(),
            )
        except Exception as dict_error:  # pragma: no cover - diagnostic guard
            app.logger.warning('Failed to load operator dictionary: %s', dict_error)

        if Operator.query.count() == 0:
            operators_data = [
                ('NBU 2P2 U PLAT UZCARD, 99', 'Milliy 2.0'),
                ('NBU P2P HUMO UZCARD>', 'Milliy 2.0'),
                ('NBU P2P HUMOHUMO>tas', 'Milliy 2.0'),
                ('NBU P2P UZCARD HUMO, 99', 'Milliy 2.0'),
                ('PSP P2P AKSIYA>TASHK', 'MyUztelecom'),
                ('PSP P2P AKSIYA, UZ', 'MyUztelecom'),
                ('PSP P2P HUMO2UZCARD>', 'MyUztelecom'),
                ('UPAY P2P', 'Humans'),
                ('UPAY P2P, UZ', 'Humans'),
                ('UPAY Humo2Uzcard>TOS', 'Humans'),
                ('UPAY UZCARD2HUMO, UZ', 'Humans'),
                ('UPAY HUMO2HUMO P2P>T', 'Humans'),
                ('DAVR UPAY HUMANS UZCARD2UZCARD, UZ', 'Humans'),
                ('DAVR UPAY HUMANS UZCARD2HU, UZ', 'Humans'),
                ('TENGE UNIVERSAL P2P, UZ', 'Tenge24'),
                ('T24 P2P Humo to Uzca', 'Tenge24'),
                ('NEW DBO UZKART-HUMO, UZ', 'Tenge24'),
                ('TENGE 24 P2P UZCARD UZCARD, UZ', 'Tenge24'),
                ('TENGE 24 P2P UZCARD HUMO, UZ', 'Tenge24'),
                ('Tenge24 P2P UZCARDHU', 'Tenge24'),
                ('TENGE-24 WS P2P INTERBANK, UZ', 'Tenge24'),
                ('TENGE-24 WS P2P INTERBANK SPISANIYE UZCA, UZ', 'Tenge24'),
                ('TENGE-24 WS P2P U2H-E, UZ', 'Tenge24'),
                ('TENGE24 WS P2P H2UEW', 'Tenge24'),
                ('XAZNA OTHERS 2 ANY, 99', 'Xazna'),
                ('XAZNA OTHERS TO HUMO, 99', 'Xazna'),
                ('XAZNA HUMO 2 UZCARD', 'Xazna'),
                ('XAZNA P2P>TOSHKENT', 'Xazna'),
                ('DAVR MOBILE UZCARD UZCARD, UZ', 'Davr Mobile'),
                ('DAVR MOBILE P2P H2U>', 'Davr Mobile'),
                ('DAVR MOBILE P2P H2H>', 'Davr Mobile'),
                ('DAVR MOBILE HUMO UZCARD, UZ', 'Davr Mobile'),
                ('DAVR MOBILE P2P KOMIS, UZ', 'Davr Mobile'),
                ('DAVR MOBILE UZCARD HUMO, UZ', 'Davr Mobile'),
                ('HAMKORBANK ATB, UZ', 'Hamkor'),
                ('HAMKOR P2P UZKARD>AN', 'Hamkor'),
                ('OQ P2P, UZ', 'OQ'),
                ('OQ P2P>TASHKENT', 'OQ'),
                ('TOSHKENT SH., AT KHALK BANKI BOSH AMALIY, 99', 'Paynet'),
                ('UZPAYNET>Shayxontoxu', 'Paynet'),
                ('PAYNET HUM2UZC NEW>T', 'Paynet'),
                ('UZPAYNET>Toshkent Sh', 'Paynet'),
                ('UZCARD OTHERS 2 ANY PAYNET, 99', 'Paynet'),
                ('PAYNET P2P HUM2UZC>S', 'Paynet'),
                ('TOSHKENT SH., MIKROKREDITBANK ATB BOSH, UZ', 'Mavrid'),
                ('MKBANK MAVRID UZCARD', 'Mavrid'),
                ('MKBANK P2P UZCARD MAVRID, UZ', 'Mavrid'),
                ('UZCARD PLYUS P2P, 99', 'Joyda'),
                ('UZCARD PLYUS P2P HUMO BOSHQA BANK, 99', 'Joyda'),
                ('UZCARD P2P, UZ', 'Agrobank'),
                ('ASAKABANK HUMO UZCAR', 'Asakabank'),
                ('TOSHKENT SH., ASAKA AT BANKINING BOSH, 99', 'Asakabank'),
                ('ASAKABANK UZCARD HUMO P2P BB, 99', 'Asakabank'),
                ('ASAKA HUMO UZCARD P2', 'Asakabank'),
                ('SMARTBANK P2P O2O UZCARD, UZ', 'SmartBank'),
                ('SMARTBANK UZCARD HUMO P2P, UZ', 'SmartBank'),
                ('SmartBank P2P UZCARD', 'SmartBank'),
                ('SmartBank P2P HUMO U', 'SmartBank'),
                ('SmartBank P2P O2O HU', 'SmartBank'),
                ('BEEPUL UZCARD 2 UZCARD, UZ', 'Beepul'),
                ('BEEPUL UZCARD 2 HUMO, UZ', 'Beepul'),
                ('PAYWAY 05, UZ', 'PayWay'),
                ('PAYME P2P, UZ', 'Payme'),
                ('UB PEREVOD CROSSBORDER 6 SEND, UZ', 'UzumBank'),
                ('SQB MOBILE UZCARD P2P UZCARD, UZ', 'SQB'),
                ('SQB MOBILE HUMO P2P', 'SQB'),
                ('CHAKANAPAY UZCARD TOUZCARD, UZ', 'Chakanapay'),
                ('ChakanaPay Humo to Uzcard', 'Chakanapay'),
                ('ChakanaPay Humo Uzcard', 'Chakanapay'),
            ]

            for name, description in operators_data:
                operator = Operator(name=name, description=description, user_id=None)
                db.session.add(operator)

            db.session.commit()
            app.logger.info('Seeded %d operators', len(operators_data))


def _register_static_routes(app: Flask) -> None:
    """Serve compiled frontend files while protecting API routes."""

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path: str):
        static_folder_path = app.static_folder
        if not static_folder_path:
            return 'Static folder not configured', 404

        if path.startswith('api/'):
            return jsonify({'error': 'Not Found', 'path': f'/{path}'}), 404

        full_path = os.path.join(static_folder_path, path)
        if path and os.path.exists(full_path):
            return send_from_directory(static_folder_path, path)

        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')

        return 'index.html not found', 404

