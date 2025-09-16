import requests
import json
from typing import Dict, List, Optional
from config.settings import BACKEND_API_URL

class APIClient:
    def __init__(self):
        self.base_url = BACKEND_API_URL
        
    def _make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
        """Выполнить HTTP запрос к API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            return {'error': f'API request failed: {str(e)}'}
    
    def get_transactions(self, telegram_id: int, page: int = 1, per_page: int = 50) -> Dict:
        """Получить транзакции пользователя"""
        params = {
            'telegram_id': telegram_id,
            'page': page,
            'per_page': per_page
        }
        return self._make_request('GET', 'transactions', params=params)
    
    def create_transaction(self, telegram_id: int, transaction_data: Dict) -> Dict:
        """Создать новую транзакцию"""
        data = {
            'telegram_id': telegram_id,
            **transaction_data
        }
        return self._make_request('POST', 'transactions', data=data)
    
    def update_transaction(self, transaction_id: int, telegram_id: int, updates: Dict) -> Dict:
        """Обновить транзакцию"""
        data = {
            'telegram_id': telegram_id,
            **updates
        }
        return self._make_request('PUT', f'transactions/{transaction_id}', data=data)
    
    def delete_transaction(self, transaction_id: int, telegram_id: int) -> Dict:
        """Удалить транзакцию"""
        params = {'telegram_id': telegram_id}
        return self._make_request('DELETE', f'transactions/{transaction_id}', params=params)
    
    def get_operators(self, telegram_id: int = None) -> Dict:
        """Получить операторов"""
        params = {'telegram_id': telegram_id} if telegram_id else {}
        return self._make_request('GET', 'operators', params=params)
    
    def create_operator(self, telegram_id: int, name: str, description: str = None) -> Dict:
        """Создать персонального оператора"""
        data = {
            'telegram_id': telegram_id,
            'name': name,
            'description': description
        }
        return self._make_request('POST', 'operators', data=data)
    
    def export_transactions(self, telegram_id: int) -> Dict:
        """Экспорт транзакций"""
        params = {'telegram_id': telegram_id}
        return self._make_request('GET', 'transactions/export', params=params)

