from flask_sqlalchemy import SQLAlchemy
from src.models.user import db

class FormattingSetting(db.Model):
    __tablename__ = 'formatting_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    column_name = db.Column(db.String(50), nullable=False)
    alignment = db.Column(db.String(10), default='left')  # 'left', 'center', 'right'
    width = db.Column(db.Integer, default=150)
    position = db.Column(db.Integer, default=0)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('formatting_settings', lazy=True))
    
    __table_args__ = (db.UniqueConstraint('user_id', 'column_name'),)

    def __repr__(self):
        return f'<FormattingSetting {self.user_id}:{self.column_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'column_name': self.column_name,
            'alignment': self.alignment,
            'width': self.width,
            'position': self.position
        }

class CellColor(db.Model):
    __tablename__ = 'cell_colors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=False)
    column_name = db.Column(db.String(50), nullable=False)
    background_color = db.Column(db.String(7), default='#FFFFFF')  # HEX цвет
    
    # Relationships
    user = db.relationship('User', backref=db.backref('cell_colors', lazy=True))
    transaction = db.relationship('Transaction', backref=db.backref('cell_colors', lazy=True))
    
    __table_args__ = (db.UniqueConstraint('user_id', 'transaction_id', 'column_name'),)

    def __repr__(self):
        return f'<CellColor {self.user_id}:{self.transaction_id}:{self.column_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'transaction_id': self.transaction_id,
            'column_name': self.column_name,
            'background_color': self.background_color
        }

