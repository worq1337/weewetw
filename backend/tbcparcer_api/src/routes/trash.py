from flask import Blueprint, jsonify, request

from src.models.transaction import Transaction, db
from src.utils.errors import APIError

trash_bp = Blueprint('trash', __name__)

@trash_bp.route('/transactions/<int:transaction_id>/soft-delete', methods=['POST'])
def soft_delete_transaction(transaction_id):
    """Помечает транзакцию как удаленную (soft delete)"""
    transaction = Transaction.query.filter_by(id=transaction_id).first()
    if not transaction:
        raise APIError(404, 'Транзакция не найдена', error='Not Found')

    transaction.is_deleted = True
    try:
        db.session.commit()
    except Exception as exc:  # pragma: no cover
        db.session.rollback()
        raise APIError(500, 'Не удалось переместить в корзину', details={'reason': str(exc)})

    return jsonify({
        'success': True,
        'message': 'Транзакция перемещена в корзину',
        'transaction_id': transaction_id,
    })

@trash_bp.route('/transactions/<int:transaction_id>/restore', methods=['POST'])
def restore_transaction(transaction_id):
    """Восстанавливает транзакцию из корзины"""
    transaction = Transaction.query.filter_by(id=transaction_id).first()
    if not transaction:
        raise APIError(404, 'Транзакция не найдена', error='Not Found')

    transaction.is_deleted = False
    try:
        db.session.commit()
    except Exception as exc:  # pragma: no cover
        db.session.rollback()
        raise APIError(500, 'Не удалось восстановить транзакцию', details={'reason': str(exc)})

    return jsonify({
        'success': True,
        'message': 'Транзакция восстановлена',
        'transaction_id': transaction_id,
    })

@trash_bp.route('/transactions/<int:transaction_id>/permanent-delete', methods=['DELETE'])
def permanent_delete_transaction(transaction_id):
    """Окончательно удаляет транзакцию из базы данных"""
    transaction = Transaction.query.filter_by(id=transaction_id).first()
    if not transaction:
        raise APIError(404, 'Транзакция не найдена', error='Not Found')

    if not transaction.is_deleted:
        raise APIError(400, 'Транзакция должна быть сначала помещена в корзину', error='Bad Request')

    db.session.delete(transaction)
    try:
        db.session.commit()
    except Exception as exc:  # pragma: no cover
        db.session.rollback()
        raise APIError(500, 'Не удалось удалить транзакцию', details={'reason': str(exc)})

    return jsonify({
        'success': True,
        'message': 'Транзакция окончательно удалена',
        'transaction_id': transaction_id,
    })

@trash_bp.route('/trash/transactions', methods=['GET'])
def get_trash_transactions():
    """Получает все удаленные транзакции (корзина)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    deleted_transactions = (
        Transaction.query.filter_by(is_deleted=True)
        .order_by(Transaction.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return jsonify(
        {
            'success': True,
            'transactions': [t.to_dict() for t in deleted_transactions.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': deleted_transactions.total,
                'pages': deleted_transactions.pages,
                'has_next': deleted_transactions.has_next,
                'has_prev': deleted_transactions.has_prev,
            },
        }
    )

@trash_bp.route('/trash/empty', methods=['DELETE'])
def empty_trash():
    """Окончательно удаляет все транзакции из корзины"""
    deleted_transactions = Transaction.query.filter_by(is_deleted=True).all()
    count = len(deleted_transactions)

    for transaction in deleted_transactions:
        db.session.delete(transaction)

    try:
        db.session.commit()
    except Exception as exc:  # pragma: no cover
        db.session.rollback()
        raise APIError(500, 'Не удалось очистить корзину', details={'reason': str(exc)})

    return jsonify(
        {
            'success': True,
            'message': f'Корзина очищена. Удалено транзакций: {count}',
            'deleted_count': count,
        }
    )

