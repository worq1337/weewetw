from flask import Blueprint, jsonify

from src.services.operator_dictionary import (
    get_operator_dictionary,
    normalize_operator_value,
    reload_operator_dictionary,
)

_SAMPLE_ALIASES = [
    'UPAY P2P',
    'PAYME P2P, UZ',
    'TENGE 24 P2P UZCARD HUMO, UZ',
    'Unknown provider',
]


def _collect_examples(dictionary):
    examples = []
    for raw_value in _SAMPLE_ALIASES:
        normalized_value = normalize_operator_value(raw_value)
        dictionary_entry = dictionary.lookup(raw_value)
        examples.append({
            'input': raw_value,
            'normalized': normalized_value,
            'matched': bool(dictionary_entry),
            'alias': dictionary_entry['alias'] if dictionary_entry else None,
            'operator': dictionary_entry['operator'] if dictionary_entry else None,
        })
    return examples


dictionary_bp = Blueprint('dictionary', __name__)


@dictionary_bp.route('/dictionary/reload', methods=['POST'])
def reload_dictionary():
    dictionary = get_operator_dictionary()
    before_entries = dictionary.size()
    before_examples = _collect_examples(dictionary)

    try:
        loaded_entries = reload_operator_dictionary()
    except FileNotFoundError:
        return jsonify({'status': 'error', 'message': 'Dictionary file not found'}), 500
    except ValueError as error:
        return jsonify({'status': 'error', 'message': str(error)}), 400

    after_examples = _collect_examples(dictionary)
    payload = {
        'status': 'ok',
        'entries': loaded_entries,
        'before_entries': before_entries,
        'after_entries': dictionary.size(),
        'path': str(dictionary.path),
        'examples': {
            'before': before_examples,
            'after': after_examples,
        },
    }
    return jsonify(payload)
