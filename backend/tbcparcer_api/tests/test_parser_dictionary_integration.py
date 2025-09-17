import json
import os
import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.services import operator_dictionary as dictionary_module
from src.services.ai_parser import AIParsingService, LocalReceiptParser

TEST_DICTIONARY = {
    "version": 1,
    "operators": {
        "Humans": {
            "display_name": "Humans",
            "applications": ["Humans"],
            "description": "Humans fintech",
        }
    },
    "applications": {
        "Humans": {
            "operator": "Humans",
            "platforms": ["ios", "android"],
        }
    },
    "aliases": [
        {"alias": "UPAY P2P, UZ", "operator": "Humans", "application": "Humans"}
    ],
}


@pytest.fixture(autouse=True)
def dictionary_fixture(tmp_path, monkeypatch):
    dictionary_path = tmp_path / 'operators_dict.json'
    dictionary_path.write_text(json.dumps(TEST_DICTIONARY, ensure_ascii=False, indent=2), encoding='utf-8')

    monkeypatch.setenv('OPERATORS_DICTIONARY_PATH', str(dictionary_path))
    os.environ.pop('OPENAI_API_KEY', None)

    dictionary_module._DICTIONARY_INSTANCE = None

    yield

    dictionary_module._DICTIONARY_INSTANCE = None


def test_local_parser_uses_dictionary_metadata():
    parser = LocalReceiptParser()

    result = parser.parse("""UPAY P2P, UZ\nСумма: 120 000 UZS\nБаланс: 45 000 UZS""")

    assert result['operator'] == 'UPAY P2P, UZ'
    assert result['operator_name'] == 'Humans'
    assert result['operator_description'] == 'Humans fintech'
    assert result['operator_application'] == 'Humans'
    assert result['operator_normalized'] == 'UPAY P2P UZ'
    assert 'operator_raw' not in result


def test_enhance_with_operator_info_preserves_application():
    service = AIParsingService()
    parsed = {'operator': 'UPAY P2P, UZ'}

    enhanced = service.enhance_with_operator_info(parsed, operators_list=[])

    assert enhanced['operator'] == 'UPAY P2P, UZ'
    assert enhanced['operator_name'] == 'Humans'
    assert enhanced['operator_application'] == 'Humans'
    assert enhanced['operator_brand'] == 'Humans'
    assert enhanced['operator_description'] == 'Humans fintech'
