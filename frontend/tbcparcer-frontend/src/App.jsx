import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Menu, Settings, Plus, Database, FileDown, MessageSquare } from 'lucide-react'
import TransactionTable from './components/TransactionTable'
import BurgerMenu from './components/BurgerMenu'
import FilterPanel from './components/FilterPanel'
import TrashPage from './components/TrashPage'
import AddReceiptPage from './components/AddReceiptPage'
import SettingsPage from './components/SettingsPage'
import './App.css'

function App() {
  const [transactions, setTransactions] = useState([])
  const [filteredTransactions, setFilteredTransactions] = useState([])
  const [activeFilters, setActiveFilters] = useState({})
  const [loading, setLoading] = useState(true)
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [currentPage, setCurrentPage] = useState('main') // 'main' или 'trash'

  // Моковые данные для демонстрации
  const mockTransactions = [
    {
      id: 1,
      receipt_number: 'CHK001',
      date_time: '2025-04-04 18:46:00',
      day_name: '2025-04-04 18:46:00', // Будет преобразовано в ПТ
      date: '2025-04-04 18:46:00',
      time: '2025-04-04 18:46:00',
      operator_seller: 'HUMO',
      application: 'Milliy 2.0',
      amount: 6000000.00,
      balance: 935000.40,
      card_number: '6714',
      p2p: true,
      transaction_type: 'payment',
      currency: 'UZS',
      data_source: 'Telegram Bot',
      category: 'Переводы'
    },
    {
      id: 2,
      receipt_number: 'CHK002',
      date_time: '2025-04-05 12:58:00',
      day_name: '2025-04-05 12:58:00', // Будет преобразовано в СБ
      date: '2025-04-05 12:58:00',
      time: '2025-04-05 12:58:00',
      operator_seller: 'OQ',
      application: 'OQ',
      amount: 400000.00,
      balance: 535000.40,
      card_number: '6714',
      p2p: true,
      transaction_type: 'payment',
      currency: 'UZS',
      data_source: 'Telegram Bot',
      category: 'Переводы'
    },
    {
      id: 3,
      receipt_number: 'CHK003',
      date_time: '2025-04-06 23:00:00',
      day_name: '2025-04-06 23:00:00', // Будет преобразовано в ВС
      date: '2025-04-06 23:00:00',
      time: '2025-04-06 23:00:00',
      operator_seller: 'HUMO',
      application: 'Milliy 2.0',
      amount: 11488000.00,
      balance: 11818000.00,
      card_number: '6714',
      p2p: false,
      transaction_type: 'refill',
      currency: 'UZS',
      data_source: 'Telegram Bot',
      category: 'Пополнения'
    },
    {
      id: 4,
      receipt_number: 'CHK004',
      date_time: '2025-04-02 08:37:00',
      day_name: '2025-04-02 08:37:00', // Будет преобразовано в СР
      date: '2025-04-02 08:37:00',
      time: '2025-04-02 08:37:00',
      operator_seller: 'UZCARD',
      application: 'Agrobank',
      amount: 44000.00,
      balance: 2607792.14,
      card_number: '0907',
      p2p: false,
      transaction_type: 'payment',
      currency: 'UZS',
      data_source: 'Telegram Bot',
      category: 'Покупки'
    },
    {
      id: 5,
      receipt_number: 'CHK005',
      date_time: '2025-04-14 10:29:00',
      day_name: '2025-04-14 10:29:00', // Будет преобразовано в ПН
      date: '2025-04-14 10:29:00',
      time: '2025-04-14 10:29:00',
      operator_seller: 'NBU',
      application: 'Milliy 2.0',
      amount: 37.00,
      balance: 0.00,
      card_number: '6905',
      p2p: false,
      transaction_type: 'conversion',
      currency: 'USD',
      data_source: 'Telegram Bot',
      category: 'Конверсия'
    }
  ]

  useEffect(() => {
    // Загрузка данных с Backend API
    const loadTransactions = async () => {
      try {
        setLoading(true)
        // Используем тестовый telegram_id для демонстрации
        const response = await fetch('http://localhost:5000/api/transactions?telegram_id=123456789')
        
        if (response.ok) {
          const data = await response.json()
          // Преобразуем данные API в формат, ожидаемый Frontend
          const transformedTransactions = (data.transactions || []).map(transaction => ({
            id: transaction.id,
            receipt_number: transaction.raw_text?.split(':')[0] || `CHK${transaction.id}`,
            date_time: transaction.date_time,
            day_name: transaction.date_time,
            date: transaction.date_time,
            time: transaction.date_time,
            operator_seller: transaction.operator_name || 'Неизвестно',
            application: transaction.operator_description || 'Неизвестно',
            amount: transaction.amount,
            balance: transaction.balance || 0,
            card_number: transaction.card_number || '',
            p2p: transaction.operation_type === 'p2p',
            transaction_type: transaction.operation_type || 'payment',
            currency: transaction.currency || 'UZS',
            data_source: 'Telegram Bot',
            category: 'Общие'
          }))
          
          setTransactions(transformedTransactions)
          setFilteredTransactions(transformedTransactions)
        } else {
          console.error('Ошибка загрузки данных:', response.statusText)
          // Fallback на моковые данные при ошибке
          setTransactions(mockTransactions)
          setFilteredTransactions(mockTransactions)
        }
      } catch (error) {
        console.error('Ошибка подключения к API:', error)
        // Fallback на моковые данные при ошибке
        setTransactions(mockTransactions)
        setFilteredTransactions(mockTransactions)
      } finally {
        setLoading(false)
      }
    }
    
    loadTransactions()
  }, [])

  // Обработчики для фильтров
  const handleFilteredTransactions = (filtered) => {
    setFilteredTransactions(filtered)
  }

  const handleFiltersChange = (filters) => {
    setActiveFilters(filters)
  }

  // Обновление транзакции
  const handleTransactionUpdate = (updatedTransaction) => {
    // Если транзакция помечена как удаленная, удаляем ее из списка
    if (updatedTransaction.deleted) {
      const newTransactions = transactions.filter(t => t.id !== updatedTransaction.id)
      setTransactions(newTransactions)
      
      const newFilteredTransactions = filteredTransactions.filter(t => t.id !== updatedTransaction.id)
      setFilteredTransactions(newFilteredTransactions)
    } else {
      // Обычное обновление транзакции
      const newTransactions = transactions.map(t => 
        t.id === updatedTransaction.id ? updatedTransaction : t
      )
      setTransactions(newTransactions)
      
      // Также обновляем отфильтрованные данные
      const newFilteredTransactions = filteredTransactions.map(t => 
        t.id === updatedTransaction.id ? updatedTransaction : t
      )
      setFilteredTransactions(newFilteredTransactions)
    }
  }

  const handleMenuAction = (action) => {
    switch (action) {
      case 'overview':
        setCurrentPage('main')
        break
      case 'add':
        setCurrentPage('add-receipt')
        break
      case 'settings':
        setCurrentPage('settings')
        break
      case 'trash':
        setCurrentPage('trash')
        break
      case 'telegram':
        window.open('https://t.me/tbcparcer_bot', '_blank')
        break
      default:
        break
    }
    setIsMenuOpen(false)
  }

  const handleTransactionAdded = (newTransaction) => {
    // Добавляем новую транзакцию в список
    setTransactions(prev => [newTransaction, ...prev])
    setFilteredTransactions(prev => [newTransaction, ...prev])
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      {currentPage === 'trash' ? (
        <TrashPage onBack={() => setCurrentPage('main')} />
      ) : currentPage === 'add-receipt' ? (
        <AddReceiptPage 
          onBack={() => setCurrentPage('main')} 
          onTransactionAdded={handleTransactionAdded}
        />
      ) : currentPage === 'settings' ? (
        <SettingsPage onBack={() => setCurrentPage('main')} />
      ) : (
        <>
          {/* Header */}
          <header className="border-b border-border bg-card">
            <div className="flex items-center justify-between px-6 py-4">
              <div className="flex items-center space-x-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsMenuOpen(true)}
                  className="p-2"
                >
                  <Menu className="h-5 w-5" />
                </Button>
                <h1 className="text-xl font-semibold text-foreground">TBCparcer</h1>
              </div>
              
              <div className="flex items-center space-x-2">
                <Button variant="outline" size="sm">
                  <FileDown className="h-4 w-4 mr-2" />
                  Экспорт
                </Button>
                <Button variant="outline" size="sm" onClick={() => handleMenuAction('add')}>
                  <Plus className="h-4 w-4 mr-2" />
                  Добавить
                </Button>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="p-6">
            <div className="mb-6">
              <h2 className="text-lg font-medium text-foreground mb-2">
                Финансовые транзакции
              </h2>
              <p className="text-sm text-muted-foreground">
                Управление и анализ ваших финансовых операций
              </p>
            </div>

            {loading ? (
              <div className="flex items-center justify-center h-64">
                <div className="text-muted-foreground">Загрузка данных...</div>
              </div>
            ) : (
              <div className="space-y-6">
                <FilterPanel
                  transactions={transactions}
                  onFilteredTransactions={handleFilteredTransactions}
                  onFiltersChange={handleFiltersChange}
                  filteredCount={filteredTransactions.length}
                />
                
                <TransactionTable 
                  transactions={filteredTransactions}
                  onTransactionUpdate={handleTransactionUpdate}
                />
              </div>
            )}
          </main>
        </>
      )}

      {/* Burger Menu */}
      <BurgerMenu
        isOpen={isMenuOpen}
        onClose={() => setIsMenuOpen(false)}
        onAction={handleMenuAction}
      />
    </div>
  )
}

export default App

