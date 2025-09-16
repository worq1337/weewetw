from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Operator(db.Model):
    __tablename__ = 'operators'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255))  # Приложение которое относится к оператору
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # NULL для глобальных операторов
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('operators', lazy=True))

    def __repr__(self):
        return f'<Operator {self.id}: {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'user_id': self.user_id,
            'is_global': self.user_id is None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def get_operators_for_user(user_id):
        """Получить операторов для пользователя (глобальные + персональные)"""
        # Сначала персональные операторы, потом глобальные
        personal_operators = Operator.query.filter_by(user_id=user_id).all()
        global_operators = Operator.query.filter_by(user_id=None).all()
        
        # Создаем словарь для быстрого поиска персональных операторов по имени
        personal_names = {op.name for op in personal_operators}
        
        # Фильтруем глобальные операторы, исключая те, что переопределены персональными
        filtered_global = [op for op in global_operators if op.name not in personal_names]
        
        return personal_operators + filtered_global
    
    @staticmethod
    def find_operator_by_description(description_text, user_id=None):
        """Найти оператора по тексту описания"""
        operators = Operator.get_operators_for_user(user_id) if user_id else Operator.query.filter_by(user_id=None).all()
        
        # Ищем точное совпадение в названии оператора
        for operator in operators:
            if operator.name.lower() in description_text.lower():
                return operator
        
        # Если точного совпадения нет, ищем по ключевым словам
        for operator in operators:
            if operator.description:
                keywords = operator.description.lower().split()
                if any(keyword in description_text.lower() for keyword in keywords):
                    return operator
        
        return None

