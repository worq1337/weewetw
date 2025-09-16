from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False)
    username = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.telegram_id}: {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def get_by_telegram_id(telegram_id):
        """Получить пользователя по telegram_id"""
        return User.query.filter_by(telegram_id=telegram_id).first()
    
    @staticmethod
    def get_or_create_user(telegram_id, username=None):
        """Получить или создать пользователя по telegram_id"""
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if not user:
            user = User(telegram_id=telegram_id, username=username)
            db.session.add(user)
            db.session.commit()
        elif username and user.username != username:
            # Обновляем username если он изменился
            user.username = username
            db.session.commit()
        return user
