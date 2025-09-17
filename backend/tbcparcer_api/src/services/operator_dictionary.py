import hashlib
import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional
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
        self._operators: Dict[str, Dict[str, Any]] = {}
        self._applications: Dict[str, Dict[str, Any]] = {}
        self._sources: List[Dict[str, str]] = []
        self._version: Optional[Any] = None
        self._checksum: Optional[str] = None
        self.reload()

    def _load_file(self) -> Dict:
        with self._path.open('r', encoding='utf-8') as stream:
            return json.load(stream)

    def reload(self) -> int:
        """Reload dictionary from file and return number of entries."""
        data = self._load_file()

        raw_aliases = data.get('aliases', {})
        raw_operator_map = data.get('operators', {})
        raw_application_map = data.get('applications', {})
        raw_sources = data.get('sources', [])

        operator_map: Dict[str, Dict[str, Any]] = {}
        if isinstance(raw_operator_map, dict):
            for name, metadata in raw_operator_map.items():
                if not isinstance(name, str):
                    continue
                cleaned_name = name.strip()
                if not cleaned_name:
                    continue
                if isinstance(metadata, dict):
                    operator_map[cleaned_name] = metadata.copy()
                else:
                    operator_map[cleaned_name] = {'display_name': str(metadata)}

        application_map: Dict[str, Dict[str, Any]] = {}
        if isinstance(raw_application_map, dict):
            for name, metadata in raw_application_map.items():
                if not isinstance(name, str):
                    continue
                cleaned_name = name.strip()
                if not cleaned_name:
                    continue
                if isinstance(metadata, dict):
                    application_map[cleaned_name] = metadata.copy()
                else:
                    application_map[cleaned_name] = {'name': str(metadata)}

        if isinstance(raw_aliases, list):
            items: List[Dict[str, Any]] = []
            for item in raw_aliases:
                if not isinstance(item, dict):
                    continue
                alias = item.get('alias') or item.get('pattern')
                operator = item.get('operator') or item.get('value')
                application = item.get('application') or item.get('app')
                if alias and operator:
                    entry: Dict[str, Any] = {
                        'alias': str(alias),
                        'operator': str(operator),
                    }
                    if application:
                        entry['application'] = str(application)
                    items.append(entry)
        elif isinstance(raw_aliases, dict):
            items = [
                {
                    'alias': str(alias),
                    'operator': str(operator),
                }
                for alias, operator in raw_aliases.items()
                if alias and operator
            ]
        else:
            raise ValueError('Invalid dictionary format: "aliases" must be dict or list')

        entries: List[Dict[str, str]] = []
        for item in items:
            cleaned_alias = item['alias'].strip()
            cleaned_operator = item['operator'].strip()
            if not cleaned_alias or not cleaned_operator:
                continue

            entry: Dict[str, str] = {
                'alias': cleaned_alias,
                'operator': cleaned_operator,
                'normalized': _normalize(cleaned_alias),
            }

            application_value = item.get('application')
            if application_value:
                cleaned_application = str(application_value).strip()
                if cleaned_application:
                    entry['application'] = cleaned_application

            entries.append(entry)

        entries.sort(key=lambda entry: len(entry['normalized']), reverse=True)

        sources: List[Dict[str, str]] = []
        if isinstance(raw_sources, list):
            for candidate in raw_sources:
                if isinstance(candidate, dict):
                    url = str(candidate.get('url', '')).strip()
                    if not url:
                        continue
                    source_entry: Dict[str, str] = {'url': url}
                    label = candidate.get('label')
                    if isinstance(label, str) and label.strip():
                        source_entry['label'] = label.strip()
                    sources.append(source_entry)
                elif isinstance(candidate, str):
                    url = candidate.strip()
                    if url:
                        sources.append({'url': url})

        serialized = json.dumps(data, ensure_ascii=False, sort_keys=True).encode('utf-8')
        checksum = hashlib.sha256(serialized).hexdigest()

        with self._lock:
            self._entries = entries
            self._operators = operator_map
            self._applications = application_map
            self._version = data.get('version')
            self._sources = sources
            self._checksum = checksum

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

    def checksum(self) -> Optional[str]:
        with self._lock:
            return self._checksum

    def sources(self) -> List[Dict[str, str]]:
        with self._lock:
            return [source.copy() for source in self._sources]

    def get_operator_metadata(self, name: Optional[str]) -> Dict[str, Any]:
        if not name:
            return {}
        key = str(name).strip()
        if not key:
            return {}
        with self._lock:
            metadata = self._operators.get(key)
            return metadata.copy() if isinstance(metadata, dict) else {}

    def get_application_metadata(self, name: Optional[str]) -> Dict[str, Any]:
        if not name:
            return {}
        key = str(name).strip()
        if not key:
            return {}
        with self._lock:
            metadata = self._applications.get(key)
            return metadata.copy() if isinstance(metadata, dict) else {}

    @property
    def version(self) -> Optional[Any]:
        with self._lock:
            return self._version

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


def reload_operator_dictionary() -> Dict[str, Any]:
    dictionary = get_operator_dictionary()
    previous_checksum = dictionary.checksum()
    entries = dictionary.reload()
    current_checksum = dictionary.checksum()
    return {
        'entries': entries,
        'changed': previous_checksum != current_checksum,
        'checksum': current_checksum,
        'version': dictionary.version,
    }


def normalize_operator_value(value: str, dictionary: Optional[OperatorDictionary] = None) -> str:
    if dictionary is None:
        dictionary = get_operator_dictionary()
    return dictionary.normalize(value)
