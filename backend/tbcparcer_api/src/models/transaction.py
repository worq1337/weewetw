from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date_time = db.Column(db.DateTime, nullable=False)
    operation_type = db.Column(db.String(50), nullable=False)  # 'payment', 'refill', 'conversion', 'cancel'
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(10), nullable=False, default='UZS')
    card_number = db.Column(db.String(20))
    description = db.Column(db.Text)
    balance = db.Column(db.Numeric(15, 2))
    operator_id = db.Column(db.Integer, db.ForeignKey('operators.id'))
    raw_text = db.Column(db.Text, nullable=False)  # Оригинальный текст чека
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)  # Soft delete flag
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('transactions', lazy=True))
    operator = db.relationship('Operator', backref=db.backref('transactions', lazy=True))

    def __repr__(self):
        return f'<Transaction {self.id}: {self.operation_type} {self.amount} {self.currency}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date_time': self.date_time.isoformat() if self.date_time else None,
            'operation_type': self.operation_type,
            'amount': float(self.amount) if self.amount else None,
            'currency': self.currency,
            'card_number': self.card_number,
            'description': self.description,
            'balance': float(self.balance) if self.balance else None,
            'operator_id': self.operator_id,
            'operator_name': self.operator.name if self.operator else None,
            'operator_description': self.operator.description if self.operator else None,
            'raw_text': self.raw_text,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'data_source': 'API',
            'category': None
        }

    @staticmethod
    def get_user_transactions(user_id, limit=None):
        """Получить транзакции пользователя"""
        query = Transaction.query.filter_by(user_id=user_id, is_deleted=False).order_by(Transaction.date_time.desc())
        if limit:
            query = query.limit(limit)
        return query.all()

