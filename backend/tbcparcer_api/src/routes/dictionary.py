from flask import Blueprint, jsonify

from src.services.operator_dictionary import reload_operator_dictionary, get_operator_dictionary


dictionary_bp = Blueprint('dictionary', __name__)


@dictionary_bp.route('/dictionary/reload', methods=['POST'])
def reload_dictionary():
    try:
        loaded_entries = reload_operator_dictionary()
    except FileNotFoundError:
        return jsonify({'status': 'error', 'message': 'Dictionary file not found'}), 500
    except ValueError as error:
        return jsonify({'status': 'error', 'message': str(error)}), 400

    dictionary = get_operator_dictionary()
    payload = {
        'status': 'ok',
        'entries': loaded_entries,
        'path': str(dictionary.path),
    }
    return jsonify(payload)
