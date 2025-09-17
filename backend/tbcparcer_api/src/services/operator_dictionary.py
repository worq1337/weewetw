import json
import os
import threading
from pathlib import Path
from typing import Dict, List, Optional
import re

_NORMALIZE_PATTERN = re.compile(r'[^A-Z0-9]+')


def _normalize(value: str) -> str:
    normalized = _NORMALIZE_PATTERN.sub(' ', value.upper())
    return ' '.join(normalized.split())


class OperatorDictionary:
    """Dictionary of operator aliases loaded from a JSON file."""

    def __init__(self, dictionary_path: Path):
        self._path = Path(dictionary_path)
        self._lock = threading.Lock()
        self._entries: List[Dict[str, str]] = []
        self.reload()

    def _load_file(self) -> Dict:
        with self._path.open('r', encoding='utf-8') as stream:
            return json.load(stream)

    def reload(self) -> int:
        """Reload dictionary from file and return number of entries."""
        data = self._load_file()
        raw_aliases = data.get('aliases', {})

        if isinstance(raw_aliases, list):
            items = []
            for item in raw_aliases:
                if not isinstance(item, dict):
                    continue
                alias = item.get('alias') or item.get('pattern')
                operator = item.get('operator') or item.get('value')
                if alias and operator:
                    items.append((str(alias), str(operator)))
        elif isinstance(raw_aliases, dict):
            items = [(str(alias), str(operator)) for alias, operator in raw_aliases.items()]
        else:
            raise ValueError('Invalid dictionary format: "aliases" must be dict or list')

        entries: List[Dict[str, str]] = []
        for alias, operator in items:
            cleaned_alias = alias.strip()
            cleaned_operator = operator.strip()
            if not cleaned_alias or not cleaned_operator:
                continue
            entries.append({
                'alias': cleaned_alias,
                'operator': cleaned_operator,
                'normalized': _normalize(cleaned_alias)
            })

        entries.sort(key=lambda entry: len(entry['normalized']), reverse=True)

        with self._lock:
            self._entries = entries

        return len(entries)

    def lookup(self, candidate: Optional[str]) -> Optional[Dict[str, str]]:
        if not candidate:
            return None

        normalized_candidate = _normalize(candidate)
        if not normalized_candidate:
            return None

        with self._lock:
            for entry in self._entries:
                normalized_alias = entry['normalized']
                if not normalized_alias:
                    continue
                if normalized_alias == normalized_candidate:
                    return entry.copy()
                if normalized_alias in normalized_candidate:
                    return entry.copy()
                if normalized_candidate in normalized_alias:
                    return entry.copy()
        return None

    def normalize(self, candidate: Optional[str]) -> str:
        if not candidate:
            return ''

        entry = self.lookup(candidate)
        if entry:
            return entry['normalized']

        return _normalize(candidate)

    def size(self) -> int:
        with self._lock:
            return len(self._entries)

    @property
    def path(self) -> Path:
        return self._path


def _default_dictionary_path() -> Path:
    module_path = Path(__file__).resolve()
    project_root = module_path.parents[4]
    primary_path = project_root / 'data' / 'operators_dict.json'
    if primary_path.exists():
        return primary_path

    legacy_path = module_path.parents[2] / 'data' / 'operators_dict.json'
    return legacy_path


_DICTIONARY_INSTANCE: Optional[OperatorDictionary] = None
_DICTIONARY_LOCK = threading.Lock()


def get_operator_dictionary() -> OperatorDictionary:
    global _DICTIONARY_INSTANCE
    with _DICTIONARY_LOCK:
        if _DICTIONARY_INSTANCE is None:
            dictionary_path = Path(os.getenv('OPERATORS_DICTIONARY_PATH', _default_dictionary_path()))
            _DICTIONARY_INSTANCE = OperatorDictionary(dictionary_path)
        return _DICTIONARY_INSTANCE


def reload_operator_dictionary() -> int:
    dictionary = get_operator_dictionary()
    return dictionary.reload()


def normalize_operator_value(value: str, dictionary: Optional[OperatorDictionary] = None) -> str:
    if dictionary is None:
        dictionary = get_operator_dictionary()
    return dictionary.normalize(value)
