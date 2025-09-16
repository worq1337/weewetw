import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.models.operator import Operator
from src.models.transaction import Transaction
from src.models.formatting import FormattingSetting, CellColor
from src.routes.user import user_bp
from src.routes.transaction import transaction_bp
from src.routes.operator import operator_bp
from src.routes.ai_parsing import ai_parsing_bp
from src.routes.export import export_bp
from src.routes.trash import trash_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'tbcparcer_secret_key_2025'

# Настройка CORS для взаимодействия с frontend
CORS(app, origins="*")

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(transaction_bp, url_prefix='/api')
app.register_blueprint(operator_bp, url_prefix='/api')
app.register_blueprint(ai_parsing_bp, url_prefix='/api/ai')
app.register_blueprint(export_bp, url_prefix='/api/export')
app.register_blueprint(trash_bp, url_prefix='/api')

# Настройка базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Создание таблиц и загрузка операторов
with app.app_context():
    db.create_all()
    
    # Загружаем операторы из словаря, если их еще нет
    if Operator.query.count() == 0:
        operators_data = [
            # Milliy 2.0
            ('NBU 2P2 U PLAT UZCARD, 99', 'Milliy 2.0'),
            ('NBU P2P HUMO UZCARD>', 'Milliy 2.0'),
            ('NBU P2P HUMOHUMO>tas', 'Milliy 2.0'),
            ('NBU P2P UZCARD HUMO, 99', 'Milliy 2.0'),
            # MyUztelecom
            ('PSP P2P AKSIYA>TASHK', 'MyUztelecom'),
            ('PSP P2P AKSIYA, UZ', 'MyUztelecom'),
            ('PSP P2P HUMO2UZCARD>', 'MyUztelecom'),
            # Humans
            ('UPAY P2P', 'Humans'),
            ('UPAY P2P, UZ', 'Humans'),
            ('UPAY Humo2Uzcard>TOS', 'Humans'),
            ('UPAY UZCARD2HUMO, UZ', 'Humans'),
            ('UPAY HUMO2HUMO P2P>T', 'Humans'),
            ('DAVR UPAY HUMANS UZCARD2UZCARD, UZ', 'Humans'),
            ('DAVR UPAY HUMANS UZCARD2HU, UZ', 'Humans'),
            # Tenge24
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
            # Xazna
            ('XAZNA OTHERS 2 ANY, 99', 'Xazna'),
            ('XAZNA OTHERS TO HUMO, 99', 'Xazna'),
            ('XAZNA HUMO 2 UZCARD', 'Xazna'),
            ('XAZNA P2P>TOSHKENT', 'Xazna'),
            # Davr Mobile
            ('DAVR MOBILE UZCARD UZCARD, UZ', 'Davr Mobile'),
            ('DAVR MOBILE P2P H2U>', 'Davr Mobile'),
            ('DAVR MOBILE P2P H2H>', 'Davr Mobile'),
            ('DAVR MOBILE HUMO UZCARD, UZ', 'Davr Mobile'),
            ('DAVR MOBILE P2P KOMIS, UZ', 'Davr Mobile'),
            ('DAVR MOBILE UZCARD HUMO, UZ', 'Davr Mobile'),
            # Hamkor
            ('HAMKORBANK ATB, UZ', 'Hamkor'),
            ('HAMKOR P2P UZKARD>AN', 'Hamkor'),
            # OQ
            ('OQ P2P, UZ', 'OQ'),
            ('OQ P2P>TASHKENT', 'OQ'),
            # Paynet
            ('TOSHKENT SH., AT KHALK BANKI BOSH AMALIY, 99', 'Paynet'),
            ('UZPAYNET>Shayxontoxu', 'Paynet'),
            ('PAYNET HUM2UZC NEW>T', 'Paynet'),
            ('UZPAYNET>Toshkent Sh', 'Paynet'),
            ('UZCARD OTHERS 2 ANY PAYNET, 99', 'Paynet'),
            ('PAYNET P2P HUM2UZC>S', 'Paynet'),
            # Mavrid
            ('TOSHKENT SH., MIKROKREDITBANK ATB BOSH, UZ', 'Mavrid'),
            ('MKBANK MAVRID UZCARD', 'Mavrid'),
            ('MKBANK P2P UZCARD MAVRID, UZ', 'Mavrid'),
            # Joyda
            ('UZCARD PLYUS P2P, 99', 'Joyda'),
            ('UZCARD PLYUS P2P HUMO BOSHQA BANK, 99', 'Joyda'),
            # Agrobank
            ('UZCARD P2P, UZ', 'Agrobank'),
            # Asakabank
            ('ASAKABANK HUMO UZCAR', 'Asakabank'),
            ('TOSHKENT SH., ASAKA AT BANKINING BOSH, 99', 'Asakabank'),
            ('ASAKABANK UZCARD HUMO P2P BB, 99', 'Asakabank'),
            ('ASAKA HUMO UZCARD P2', 'Asakabank'),
            # SmartBank
            ('SMARTBANK P2P O2O UZCARD, UZ', 'SmartBank'),
            ('SMARTBANK UZCARD HUMO P2P, UZ', 'SmartBank'),
            ('SmartBank P2P UZCARD', 'SmartBank'),
            ('SmartBank P2P HUMO U', 'SmartBank'),
            ('SmartBank P2P O2O HU', 'SmartBank'),
            # Beepul
            ('BEEPUL UZCARD 2 UZCARD, UZ', 'Beepul'),
            ('BEEPUL UZCARD 2 HUMO, UZ', 'Beepul'),
            # PayWay
            ('PAYWAY 05, UZ', 'PayWay'),
            # Payme
            ('PAYME P2P, UZ', 'Payme'),
            # UzumBank
            ('UB PEREVOD CROSSBORDER 6 SEND, UZ', 'UzumBank'),
            # SQB
            ('SQB MOBILE UZCARD P2P UZCARD, UZ', 'SQB'),
            ('SQB MOBILE HUMO P2P', 'SQB'),
            # Chakanapay
            ('CHAKANAPAY UZCARD TOUZCARD, UZ', 'Chakanapay'),
            ('ChakanaPay Humo to Uzcard', 'Chakanapay'),
            ('ChakanaPay Humo Uzcard', 'Chakanapay')
        ]
        
        for name, description in operators_data:
            operator = Operator(name=name, description=description, user_id=None)
            db.session.add(operator)
        
        db.session.commit()
        print(f"Загружено {len(operators_data)} операторов в базу данных")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
