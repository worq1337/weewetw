from flask import Blueprint, request, jsonify
from src.models.transaction import Transaction, db
from src.models.user import User

trash_bp = Blueprint('trash', __name__)

@trash_bp.route('/api/transactions/<int:transaction_id>/soft-delete', methods=['POST'])
def soft_delete_transaction(transaction_id):
    """Помечает транзакцию как удаленную (soft delete)"""
    try:
        transaction = Transaction.query.get_or_404(transaction_id)
        
        # Помечаем как удаленную
        transaction.is_deleted = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Транзакция перемещена в корзину',
            'transaction_id': transaction_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@trash_bp.route('/api/transactions/<int:transaction_id>/restore', methods=['POST'])
def restore_transaction(transaction_id):
    """Восстанавливает транзакцию из корзины"""
    try:
        transaction = Transaction.query.get_or_404(transaction_id)
        
        # Восстанавливаем транзакцию
        transaction.is_deleted = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Транзакция восстановлена',
            'transaction_id': transaction_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@trash_bp.route('/api/transactions/<int:transaction_id>/permanent-delete', methods=['DELETE'])
def permanent_delete_transaction(transaction_id):
    """Окончательно удаляет транзакцию из базы данных"""
    try:
        transaction = Transaction.query.get_or_404(transaction_id)
        
        # Проверяем, что транзакция помечена как удаленная
        if not transaction.is_deleted:
            return jsonify({
                'success': False,
                'error': 'Транзакция должна быть сначала помещена в корзину'
            }), 400
        
        # Окончательно удаляем
        db.session.delete(transaction)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Транзакция окончательно удалена',
            'transaction_id': transaction_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@trash_bp.route('/api/trash/transactions', methods=['GET'])
def get_trash_transactions():
    """Получает все удаленные транзакции (корзина)"""
    try:
        # Получаем параметры пагинации
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Получаем удаленные транзакции
        deleted_transactions = Transaction.query.filter_by(is_deleted=True)\
            .order_by(Transaction.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'transactions': [t.to_dict() for t in deleted_transactions.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': deleted_transactions.total,
                'pages': deleted_transactions.pages,
                'has_next': deleted_transactions.has_next,
                'has_prev': deleted_transactions.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@trash_bp.route('/api/trash/empty', methods=['DELETE'])
def empty_trash():
    """Окончательно удаляет все транзакции из корзины"""
    try:
        # Получаем все удаленные транзакции
        deleted_transactions = Transaction.query.filter_by(is_deleted=True).all()
        count = len(deleted_transactions)
        
        # Удаляем все
        for transaction in deleted_transactions:
            db.session.delete(transaction)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Корзина очищена. Удалено транзакций: {count}',
            'deleted_count': count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

