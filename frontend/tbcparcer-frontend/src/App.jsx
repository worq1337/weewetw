import { useState, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Menu, Plus, FileDown, AlertCircle } from 'lucide-react'
import TransactionTable from './components/TransactionTable'
import BurgerMenu from './components/BurgerMenu'
import FilterPanel from './components/FilterPanel'
import TrashPage from './components/TrashPage'
import AddReceiptPage from './components/AddReceiptPage'
import SettingsPage from './components/SettingsPage'
import './App.css'
import { apiFetch, DEFAULT_TELEGRAM_ID, isDefaultTelegramConfigured } from '@/lib/api.js'

const transformTransaction = (transaction) => {
  if (!transaction) {
    return null
  }

  let normalizedDateTime = null

  if (transaction.date_time) {
    const parsedDate = new Date(transaction.date_time)

    if (!Number.isNaN(parsedDate.valueOf())) {
      normalizedDateTime = parsedDate.toISOString()
    }
  }

  const operationType = typeof transaction.operation_type === 'string'
    ? transaction.operation_type.toLowerCase()
    : null

  const amountValue = transaction.amount
  let normalizedAmount = null
  if (amountValue !== null && amountValue !== undefined) {
    const parsedAmount = Number(amountValue)
    normalizedAmount = Number.isNaN(parsedAmount) ? null : parsedAmount
  }

  const balanceValue = transaction.balance
  let normalizedBalance = null
  if (balanceValue !== null && balanceValue !== undefined) {
    const parsedBalance = Number(balanceValue)
    normalizedBalance = Number.isNaN(parsedBalance) ? null : parsedBalance
  }

  const receiptCandidate = transaction.raw_text
    ? transaction.raw_text.split(/\r?\n/)[0].split(':')[0].trim()
    : ''

  return {
    id: transaction.id,
    receipt_number: receiptCandidate,
    date_time: normalizedDateTime,
    day_name: normalizedDateTime,
    date: normalizedDateTime,
    time: normalizedDateTime,
    operator_seller: transaction.operator_name || '',
    application: transaction.operator_description || transaction.description || '',
    amount: normalizedAmount,
    balance: normalizedBalance,
    card_number: transaction.card_number || '',
    p2p: operationType === 'p2p',
    transaction_type: operationType,
    currency: transaction.currency || '',
    data_source: transaction.data_source || '',
    category: transaction.category || '',
    raw_text: transaction.raw_text || ''
  }
}

function App() {
  const [transactions, setTransactions] = useState([])
  const [filteredTransactions, setFilteredTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [currentPage, setCurrentPage] = useState('main') // 'main' или 'trash'
  const [error, setError] = useState(null)

  const telegramConfigured = isDefaultTelegramConfigured()

  const loadTransactions = useCallback(async () => {
    if (!telegramConfigured) {
      setLoading(false)
      setTransactions([])
      setFilteredTransactions([])
      setError('Укажите VITE_DEFAULT_TELEGRAM_ID в настройках фронтенда, чтобы загрузить данные из API.')
      return
    }

    try {
      setLoading(true)
      setError(null)
      const response = await apiFetch(`/api/transactions?telegram_id=${DEFAULT_TELEGRAM_ID}`)

      if (!response.ok) {
        throw new Error('Не удалось загрузить список транзакций')
      }

      const data = await response.json()
      const transformedTransactions = (data.transactions || [])
        .map(transformTransaction)
        .filter(Boolean)

      setTransactions(transformedTransactions)
      setFilteredTransactions(transformedTransactions)
    } catch (apiError) {
      console.error('Ошибка подключения к API:', apiError)
      setTransactions([])
      setFilteredTransactions([])
      setError(apiError.message || 'Ошибка при загрузке транзакций')
    } finally {
      setLoading(false)
    }
  }, [telegramConfigured])

  useEffect(() => {
    loadTransactions()
  }, [loadTransactions])

  // Обработчики для фильтров
  const handleFilteredTransactions = (filtered) => {
    setFilteredTransactions(filtered)
  }

  const handleFiltersChange = () => {}

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

  const handleTransactionAdded = (transactionFromApi) => {
    if (!telegramConfigured) {
      return
    }

    const transformed = transformTransaction(transactionFromApi)

    if (!transformed) {
      return
    }

    setTransactions(prev => [transformed, ...prev])
    setFilteredTransactions(prev => [transformed, ...prev])
    setError(null)
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

            {error && (
              <div className="mb-4 flex items-start gap-3 rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
                <AlertCircle className="mt-0.5 h-4 w-4" />
                <div className="flex-1">
                  <p className="font-medium">{error}</p>
                  <Button
                    variant="link"
                    size="sm"
                    className="mt-1 px-0 text-destructive"
                    onClick={loadTransactions}
                  >
                    Повторить загрузку
                  </Button>
                </div>
              </div>
            )}

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

                {filteredTransactions.length === 0 ? (
                  <div className="flex h-48 flex-col items-center justify-center rounded-lg border border-dashed border-border text-center text-sm text-muted-foreground">
                    <p>Нет данных для отображения.</p>
                    <p className="mt-1">Попробуйте изменить фильтры или загрузить новые транзакции.</p>
                    <Button className="mt-4" variant="outline" size="sm" onClick={loadTransactions}>
                      Обновить данные
                    </Button>
                  </div>
                ) : (
                  <TransactionTable
                    transactions={filteredTransactions}
                    onTransactionUpdate={handleTransactionUpdate}
                  />
                )}
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
