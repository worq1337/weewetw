import { useState, useEffect } from 'react'
import { Search, Filter, X, Calendar, DollarSign, Tag, Activity } from 'lucide-react'
import { Button } from '@/components/ui/button.jsx'

const FilterPanel = ({ transactions, onFilteredTransactions, onFiltersChange, filteredCount }) => {
  const [filters, setFilters] = useState({
    search: '',
    dateFrom: '',
    dateTo: '',
    category: '',
    transactionType: '',
    amountFrom: '',
    amountTo: '',
    operator: '',
    application: ''
  })

  const [isExpanded, setIsExpanded] = useState(false)

  // Получаем уникальные значения для выпадающих списков
  const getUniqueValues = (field) => {
    const values = transactions.map(t => t[field]).filter(Boolean)
    return [...new Set(values)].sort()
  }

  const categories = getUniqueValues('category')
  const transactionTypes = [
    { value: 'payment', label: 'Оплата' },
    { value: 'refill', label: 'Пополнение' },
    { value: 'conversion', label: 'Конверсия' },
    { value: 'cancel', label: 'Отмена' }
  ]
  const operators = getUniqueValues('operator_seller')
  const applications = getUniqueValues('application')

  // Функция фильтрации
  const applyFilters = (currentFilters) => {
    let filtered = [...transactions]

    // Глобальный поиск
    if (currentFilters.search) {
      const searchTerm = currentFilters.search.toLowerCase()
      filtered = filtered.filter(transaction => 
        Object.values(transaction).some(value => 
          value && value.toString().toLowerCase().includes(searchTerm)
        )
      )
    }

    // Фильтр по дате "от"
    if (currentFilters.dateFrom) {
      const fromDate = new Date(currentFilters.dateFrom)
      filtered = filtered.filter(transaction => 
        new Date(transaction.date_time) >= fromDate
      )
    }

    // Фильтр по дате "до"
    if (currentFilters.dateTo) {
      const toDate = new Date(currentFilters.dateTo)
      toDate.setHours(23, 59, 59, 999) // Включаем весь день
      filtered = filtered.filter(transaction => 
        new Date(transaction.date_time) <= toDate
      )
    }

    // Фильтр по категории
    if (currentFilters.category) {
      filtered = filtered.filter(transaction => 
        transaction.category === currentFilters.category
      )
    }

    // Фильтр по типу транзакции
    if (currentFilters.transactionType) {
      filtered = filtered.filter(transaction => 
        transaction.transaction_type === currentFilters.transactionType
      )
    }

    // Фильтр по сумме "от"
    if (currentFilters.amountFrom) {
      const fromAmount = parseFloat(currentFilters.amountFrom)
      filtered = filtered.filter(transaction => 
        parseFloat(transaction.amount) >= fromAmount
      )
    }

    // Фильтр по сумме "до"
    if (currentFilters.amountTo) {
      const toAmount = parseFloat(currentFilters.amountTo)
      filtered = filtered.filter(transaction => 
        parseFloat(transaction.amount) <= toAmount
      )
    }

    // Фильтр по оператору
    if (currentFilters.operator) {
      filtered = filtered.filter(transaction => 
        transaction.operator_seller === currentFilters.operator
      )
    }

    // Фильтр по приложению
    if (currentFilters.application) {
      filtered = filtered.filter(transaction => 
        transaction.application === currentFilters.application
      )
    }

    return filtered
  }

  // Обновление фильтров
  const updateFilter = (field, value) => {
    const newFilters = { ...filters, [field]: value }
    setFilters(newFilters)
    
    const filteredTransactions = applyFilters(newFilters)
    onFilteredTransactions(filteredTransactions)
    onFiltersChange(newFilters)
  }

  // Сброс всех фильтров
  const clearAllFilters = () => {
    const emptyFilters = {
      search: '',
      dateFrom: '',
      dateTo: '',
      category: '',
      transactionType: '',
      amountFrom: '',
      amountTo: '',
      operator: '',
      application: ''
    }
    setFilters(emptyFilters)
    onFilteredTransactions(transactions)
    onFiltersChange(emptyFilters)
  }

  // Проверка, есть ли активные фильтры
  const hasActiveFilters = Object.values(filters).some(value => value !== '')

  // Применение фильтров при изменении транзакций
  useEffect(() => {
    const filteredTransactions = applyFilters(filters)
    onFilteredTransactions(filteredTransactions)
  }, [transactions])

  return (
    <div className="bg-card border border-border rounded-lg p-4 mb-4">
      {/* Заголовок панели фильтров */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <h3 className="text-sm font-medium text-foreground">Фильтры и поиск</h3>
          {hasActiveFilters && (
            <span className="bg-primary text-primary-foreground text-xs px-2 py-1 rounded-full">
              Активны
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {hasActiveFilters && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearAllFilters}
              className="text-xs"
            >
              <X className="h-3 w-3 mr-1" />
              Сбросить
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-xs"
          >
            {isExpanded ? 'Свернуть' : 'Развернуть'}
          </Button>
        </div>
      </div>

      {/* Глобальный поиск - всегда видимый */}
      <div className="mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Поиск по всем полям..."
            value={filters.search}
            onChange={(e) => updateFilter('search', e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-border rounded-md bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          />
        </div>
      </div>

      {/* Расширенные фильтры */}
      {isExpanded && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Фильтр по датам */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-foreground flex items-center">
              <Calendar className="h-3 w-3 mr-1" />
              Период
            </label>
            <div className="space-y-2">
              <input
                type="date"
                value={filters.dateFrom}
                onChange={(e) => updateFilter('dateFrom', e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground text-xs focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="От"
              />
              <input
                type="date"
                value={filters.dateTo}
                onChange={(e) => updateFilter('dateTo', e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground text-xs focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="До"
              />
            </div>
          </div>

          {/* Фильтр по сумме */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-foreground flex items-center">
              <DollarSign className="h-3 w-3 mr-1" />
              Сумма
            </label>
            <div className="space-y-2">
              <input
                type="number"
                placeholder="От"
                value={filters.amountFrom}
                onChange={(e) => updateFilter('amountFrom', e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground text-xs focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <input
                type="number"
                placeholder="До"
                value={filters.amountTo}
                onChange={(e) => updateFilter('amountTo', e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground text-xs focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          {/* Фильтр по категории */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-foreground flex items-center">
              <Tag className="h-3 w-3 mr-1" />
              Категория
            </label>
            <select
              value={filters.category}
              onChange={(e) => updateFilter('category', e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground text-xs focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">Все категории</option>
              {categories.map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
          </div>

          {/* Фильтр по типу транзакции */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-foreground flex items-center">
              <Activity className="h-3 w-3 mr-1" />
              Тип транзакции
            </label>
            <select
              value={filters.transactionType}
              onChange={(e) => updateFilter('transactionType', e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground text-xs focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">Все типы</option>
              {transactionTypes.map(type => (
                <option key={type.value} value={type.value}>{type.label}</option>
              ))}
            </select>
          </div>

          {/* Фильтр по оператору */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-foreground">
              Оператор/Продавец
            </label>
            <select
              value={filters.operator}
              onChange={(e) => updateFilter('operator', e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground text-xs focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">Все операторы</option>
              {operators.map(operator => (
                <option key={operator} value={operator}>{operator}</option>
              ))}
            </select>
          </div>

          {/* Фильтр по приложению */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-foreground">
              Приложение
            </label>
            <select
              value={filters.application}
              onChange={(e) => updateFilter('application', e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground text-xs focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">Все приложения</option>
              {applications.map(app => (
                <option key={app} value={app}>{app}</option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* Статистика результатов */}
      <div className="mt-4 pt-4 border-t border-border">
        <p className="text-xs text-muted-foreground">
          Показано транзакций: <span className="font-medium text-foreground">{filteredCount || 0}</span> из {transactions.length}
        </p>
      </div>
    </div>
  )
}

export default FilterPanel

