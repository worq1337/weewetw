import React, { useState, useEffect } from 'react';
import { ArrowLeft, Plus, Save, Trash2, Edit3, X } from 'lucide-react';
import { apiFetch, DEFAULT_TELEGRAM_ID } from '@/lib/api.js';

const SettingsPage = ({ onBack }) => {
  const [operators, setOperators] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Состояние для форм
  const [newOperator, setNewOperator] = useState({ name: '', description: '' });
  const [newCategory, setNewCategory] = useState({ name: '', description: '' });
  const [editingOperator, setEditingOperator] = useState(null);

  useEffect(() => {
    fetchOperators();
    fetchCategories();
  }, []);

  const fetchOperators = async () => {
    try {
      const response = await apiFetch(`/api/operators?telegram_id=${DEFAULT_TELEGRAM_ID}`);
      if (response.ok) {
        const data = await response.json();
        setOperators(data.operators || []);
      }
    } catch (error) {
      console.error('Ошибка загрузки операторов:', error);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await apiFetch('/api/categories');
      if (response.ok) {
        const data = await response.json();
        const categoryList = Array.isArray(data)
          ? data
          : Array.isArray(data?.categories)
            ? data.categories
            : [];
        setCategories(categoryList);
      } else {
        setCategories([]);
      }
    } catch (error) {
      console.warn('Категории пока недоступны:', error);
      setCategories([]);
    }
  };

  const handleAddOperator = async (e) => {
    e.preventDefault();
    if (!newOperator.name.trim()) return;

    setLoading(true);
    try {
      const response = await apiFetch('/api/operators', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: newOperator.name.trim(),
          description: newOperator.description.trim(),
          telegram_id: DEFAULT_TELEGRAM_ID // Тестовый ID пользователя
        })
      });

      if (response.ok) {
        setSuccess('Оператор успешно добавлен!');
        setNewOperator({ name: '', description: '' });
        fetchOperators();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Ошибка при добавлении оператора');
      }
    } catch (error) {
      setError('Ошибка сети: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleEditOperator = async (operator) => {
    if (!editingOperator) return;

    setLoading(true);
    try {
      const response = await apiFetch(`/api/operators/${operator.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: editingOperator.name.trim(),
          description: editingOperator.description.trim(),
          telegram_id: DEFAULT_TELEGRAM_ID
        })
      });

      if (response.ok) {
        setSuccess('Оператор успешно обновлен!');
        setEditingOperator(null);
        fetchOperators();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Ошибка при обновлении оператора');
      }
    } catch (error) {
      setError('Ошибка сети: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteOperator = async (operatorId) => {
    if (!confirm('Вы уверены, что хотите удалить этого оператора?')) return;

    setLoading(true);
    try {
      const response = await apiFetch(`/api/operators/${operatorId}?telegram_id=${DEFAULT_TELEGRAM_ID}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setSuccess('Оператор успешно удален!');
        fetchOperators();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Ошибка при удалении оператора');
      }
    } catch (error) {
      setError('Ошибка сети: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Заголовок */}
        <div className="flex items-center gap-4 mb-6">
          <button
            onClick={onBack}
            className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft size={20} />
            Назад
          </button>
          <h1 className="text-2xl font-bold text-gray-800">Настройки системы</h1>
        </div>

        {/* Сообщения */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-green-800">{success}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Управление операторами */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Операторы и продавцы</h2>
            
            {/* Форма добавления оператора */}
            <form onSubmit={handleAddOperator} className="mb-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="text-lg font-medium text-gray-700 mb-3">Добавить нового оператора</h3>
              <div className="space-y-3">
                <input
                  type="text"
                  placeholder="Название оператора (например: HUMO)"
                  value={newOperator.name}
                  onChange={(e) => setNewOperator(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
                <input
                  type="text"
                  placeholder="Описание (например: Milliy 2.0)"
                  value={newOperator.description}
                  onChange={(e) => setNewOperator(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  <Plus size={16} />
                  Добавить
                </button>
              </div>
            </form>

            {/* Список операторов */}
            <div className="space-y-2">
              <h3 className="text-lg font-medium text-gray-700 mb-3">Существующие операторы</h3>
              {operators.length === 0 ? (
                <p className="text-gray-500 text-center py-4">Операторы не найдены</p>
              ) : (
                operators.map(operator => (
                  <div key={operator.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    {editingOperator && editingOperator.id === operator.id ? (
                      <div className="flex-1 flex gap-2">
                        <input
                          type="text"
                          value={editingOperator.name}
                          onChange={(e) => setEditingOperator(prev => ({ ...prev, name: e.target.value }))}
                          className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                        />
                        <input
                          type="text"
                          value={editingOperator.description}
                          onChange={(e) => setEditingOperator(prev => ({ ...prev, description: e.target.value }))}
                          className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                        />
                        <button
                          onClick={() => handleEditOperator(operator)}
                          className="px-2 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                        >
                          <Save size={14} />
                        </button>
                        <button
                          onClick={() => setEditingOperator(null)}
                          className="px-2 py-1 bg-gray-500 text-white rounded text-sm hover:bg-gray-600"
                        >
                          <X size={14} />
                        </button>
                      </div>
                    ) : (
                      <>
                        <div className="flex-1">
                          <div className="font-medium text-gray-800">{operator.name}</div>
                          <div className="text-sm text-gray-600">{operator.description}</div>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => setEditingOperator({ ...operator })}
                            className="p-1 text-blue-600 hover:bg-blue-100 rounded"
                          >
                            <Edit3 size={16} />
                          </button>
                          <button
                            onClick={() => handleDeleteOperator(operator.id)}
                            className="p-1 text-red-600 hover:bg-red-100 rounded"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Управление категориями */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Категории расходов</h2>
            
            {/* Форма добавления категории */}
            <form className="mb-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="text-lg font-medium text-gray-700 mb-3">Добавить новую категорию</h3>
                <div className="space-y-3">
                  <input
                    type="text"
                    placeholder="Название категории"
                    value={newCategory.name}
                    onChange={(e) => setNewCategory(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-500"
                    disabled
                  />
                  <input
                    type="text"
                    placeholder="Описание категории"
                    value={newCategory.description}
                    onChange={(e) => setNewCategory(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-500"
                    disabled
                  />
                  <button
                    type="button"
                    className="flex items-center gap-2 px-4 py-2 bg-gray-300 text-gray-600 rounded-lg cursor-not-allowed"
                    disabled
                    title="Добавление категорий будет доступно после интеграции с backend"
                  >
                    <Plus size={16} />
                    Добавить
                  </button>
                  <p className="text-xs text-gray-500">
                    Добавление категорий станет доступным после подключения backend API.
                  </p>
                </div>
              </form>

              {/* Список категорий */}
              <div className="space-y-2">
                <h3 className="text-lg font-medium text-gray-700 mb-3">Существующие категории</h3>
                {categories.length === 0 ? (
                  <p className="text-sm text-gray-500">Категории отсутствуют. Ожидается интеграция с backend.</p>
                ) : (
                  categories.map(category => (
                    <div key={category.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex-1">
                        <div className="font-medium text-gray-800">{category.name}</div>
                        <div className="text-sm text-gray-600">{category.description}</div>
                      </div>
                      <div className="flex gap-2">
                        <button className="p-1 text-blue-600 hover:bg-blue-100 rounded">
                          <Edit3 size={16} />
                        </button>
                        <button
                          onClick={() => {
                            if (confirm('Удалить эту категорию?')) {
                              setCategories(prev => prev.filter(c => c.id !== category.id));
                              setSuccess('Категория удалена!');
                              setTimeout(() => setSuccess(''), 3000);
                            }
                          }}
                          className="p-1 text-red-600 hover:bg-red-100 rounded"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
          </div>
        </div>

        {/* Дополнительные настройки */}
        <div className="mt-6 bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Общие настройки</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Валюта по умолчанию
              </label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <option value="UZS">UZS - Узбекский сум</option>
                <option value="USD">USD - Доллар США</option>
                <option value="EUR">EUR - Евро</option>
                <option value="RUB">RUB - Российский рубль</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Часовой пояс
              </label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <option value="Asia/Tashkent">Asia/Tashkent (UTC+5)</option>
                <option value="Europe/Moscow">Europe/Moscow (UTC+3)</option>
                <option value="UTC">UTC (UTC+0)</option>
              </select>
            </div>
          </div>
          
          <div className="mt-6">
            <button className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              Сохранить настройки
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;

