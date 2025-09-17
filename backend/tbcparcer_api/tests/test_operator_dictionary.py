import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from src.services.operator_dictionary import (
    OperatorDictionary,
    normalize_operator_value,
)


class OperatorDictionaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.dictionary_path = Path(self.tempdir.name) / 'operators.json'
        self._write_aliases({
            'Custom alias': 'Brand',
            'UPAY P2P': 'Humans',
        })
        self.dictionary = OperatorDictionary(self.dictionary_path)

    def _write_aliases(self, mapping) -> None:
        payload = {'aliases': mapping}
        self.dictionary_path.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')

    def test_lookup_resolves_partial_match(self):
        entry = self.dictionary.lookup('Custom alias extra info')
        self.assertIsNotNone(entry)
        self.assertEqual(entry['alias'], 'Custom alias')
        self.assertEqual(entry['operator'], 'Brand')
        self.assertEqual(entry['normalized'], 'CUSTOM ALIAS')

    def test_reload_applies_new_content(self):
        self._write_aliases({'Another Alias': 'Another'})
        loaded = self.dictionary.reload()
        self.assertEqual(loaded, 1)
        self.assertIsNone(self.dictionary.lookup('Custom alias extra info'))
        reloaded_entry = self.dictionary.lookup('Another alias transfer')
        self.assertIsNotNone(reloaded_entry)
        self.assertEqual(reloaded_entry['alias'], 'Another Alias')
        self.assertEqual(reloaded_entry['operator'], 'Another')

    def test_normalize_operator_value_uses_dictionary_alias(self):
        normalized = normalize_operator_value('Custom alias extra info', self.dictionary)
        self.assertEqual(normalized, 'CUSTOM ALIAS')

        fallback = normalize_operator_value('Unknown operator 123', self.dictionary)
        self.assertEqual(fallback, 'UNKNOWN OPERATOR 123')


if __name__ == '__main__':
    unittest.main()
