import React, { useState, useEffect } from 'react';
import { ArrowLeft, Plus, Save, X } from 'lucide-react';

const AddReceiptPage = ({ onBack, onTransactionAdded }) => {
  const [formData, setFormData] = useState({
    date_time: '',
    operation_type: 'payment',
    amount: '',
    currency: 'UZS',
    card_number: '',
    description: '',
    balance: '',
    operator_name: '',
    application: '',
    raw_text: ''
  });
  
  const [operators, setOperators] = useState([]);
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Загружаем список операторов и приложений
  useEffect(() => {
    fetchOperators();
    fetchApplications();
  }, []);

  const fetchOperators = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/operators');
      if (response.ok) {
        const data = await response.json();
        setOperators(data);
      }
    } catch (error) {
      console.error('Ошибка загрузки операторов:', error);
    }
  };

  const fetchApplications = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/operators');
      if (response.ok) {
        const data = await response.json();
        // Извлекаем уникальные приложения из операторов
        const uniqueApps = [...new Set(data.flatMap(op => op.applications || []))];
        setApplications(uniqueApps.map(app => ({ name: app })));
      }
    } catch (error) {
      console.error('Ошибка загрузки приложений:', error);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // Подготавливаем данные для отправки
      const transactionData = {
        ...formData,
        date_time: formData.date_time || new Date().toISOString(),
        amount: parseFloat(formData.amount) || 0,
        balance: parseFloat(formData.balance) || 0,
        raw_text: formData.raw_text || `Ручное добавление: ${formData.description}`,
        telegram_id: 123456789 // Тестовый ID пользователя
      };

      const response = await fetch('http://localhost:5000/api/transactions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(transactionData)
      });

      if (response.ok) {
        const newTransaction = await response.json();
        setSuccess('Транзакция успешно добавлена!');
        
        // Уведомляем родительский компонент о новой транзакции
        if (onTransactionAdded) {
          onTransactionAdded(newTransaction);
        }
        
        // Очищаем форму
        setFormData({
          date_time: '',
          operation_type: 'payment',
          amount: '',
          currency: 'UZS',
          card_number: '',
          description: '',
          balance: '',
          operator_name: '',
          raw_text: ''
        });

        // Через 2 секунды возвращаемся на главную
        setTimeout(() => {
          onBack();
        }, 2000);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Ошибка при добавлении транзакции');
      }
    } catch (error) {
      setError('Ошибка сети: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFormData({
      date_time: '',
      operation_type: 'payment',
      amount: '',
      currency: 'UZS',
      card_number: '',
      description: '',
      balance: '',
      operator_name: '',
      raw_text: ''
    });
    setError('');
    setSuccess('');
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      {/* Заголовок */}
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center gap-4 mb-6">
          <button
            onClick={onBack}
            className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft size={20} />
            Назад
          </button>
          <h1 className="text-2xl font-bold text-gray-800">Добавить чек</h1>
        </div>

        {/* Форма */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Дата и время */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Дата и время
                </label>
                <input
                  type="datetime-local"
                  name="date_time"
                  value={formData.date_time}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Тип операции
                </label>
                <select
                  name="operation_type"
                  value={formData.operation_type}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="payment">Оплата</option>
                  <option value="refill">Пополнение</option>
                  <option value="conversion">Конверсия</option>
                  <option value="cancel">Отмена</option>
                </select>
              </div>
            </div>

            {/* Сумма и валюта */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Сумма
                </label>
                <input
                  type="number"
                  name="amount"
                  value={formData.amount}
                  onChange={handleInputChange}
                  step="0.01"
                  placeholder="0.00"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Валюта
                </label>
                <select
                  name="currency"
                  value={formData.currency}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="UZS">UZS</option>
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                  <option value="RUB">RUB</option>
                </select>
              </div>
            </div>

            {/* Карта и баланс */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Номер карты (последние 4 цифры)
                </label>
                <input
                  type="text"
                  name="card_number"
                  value={formData.card_number}
                  onChange={handleInputChange}
                  placeholder="1234"
                  maxLength="4"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Остаток на счете
                </label>
                <input
                  type="number"
                  name="balance"
                  value={formData.balance}
                  onChange={handleInputChange}
                  step="0.01"
                  placeholder="0.00"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Оператор */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Оператор/Продавец
              </label>
              <select
                name="operator_name"
                value={formData.operator_name}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Выберите оператора</option>
                {operators.map((operator, index) => (
                  <option key={index} value={operator.name}>
                    {operator.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Приложение */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Приложение
              </label>
              <select
                name="application"
                value={formData.application}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Выберите приложение</option>
                {applications.map((app, index) => (
                  <option key={index} value={app.name}>
                    {app.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Описание */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Описание операции
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows="3"
                placeholder="Описание транзакции..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            {/* Исходный текст */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Исходный текст чека (необязательно)
              </label>
              <textarea
                name="raw_text"
                value={formData.raw_text}
                onChange={handleInputChange}
                rows="3"
                placeholder="Оригинальный текст SMS или уведомления..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Сообщения об ошибках и успехе */}
            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-800">{error}</p>
              </div>
            )}

            {success && (
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-green-800">{success}</p>
              </div>
            )}

            {/* Кнопки */}
            <div className="flex gap-4 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Save size={20} />
                {loading ? 'Сохранение...' : 'Сохранить'}
              </button>
              
              <button
                type="button"
                onClick={handleReset}
                className="flex items-center gap-2 px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
              >
                <X size={20} />
                Очистить
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AddReceiptPage;

