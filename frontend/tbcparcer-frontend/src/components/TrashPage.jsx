import { useState, useEffect } from 'react'
import { ArrowLeft, RotateCcw, Trash2, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button.jsx'
import { apiFetch } from '@/lib/api.js'
import { formatDateTime } from '@/lib/datetime.js'

const TrashPage = ({ onBack }) => {
  const [deletedTransactions, setDeletedTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [showConfirmModal, setShowConfirmModal] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')
  const [statusMessage, setStatusMessage] = useState('')

  // Загрузка удаленных транзакций
  useEffect(() => {
    fetchDeletedTransactions()
  }, [])

  const fetchDeletedTransactions = async () => {
    try {
      setLoading(true)
      setErrorMessage('')
      const response = await apiFetch('/api/trash/transactions')
      if (!response.ok) {
        throw new Error('Не удалось загрузить корзину')
      }

      const data = await response.json()
      setDeletedTransactions(Array.isArray(data.transactions) ? data.transactions : [])
      setStatusMessage('')
    } catch (error) {
      console.error('Ошибка при загрузке корзины:', error)
      setDeletedTransactions([])
      setErrorMessage(error.message || 'Ошибка при загрузке корзины')
    } finally {
      setLoading(false)
    }
  }

  // Восстановление транзакции
  const handleRestore = async (transactionId) => {
    try {
      const response = await apiFetch(`/api/transactions/${transactionId}/restore`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      })
      
      if (!response.ok) {
        throw new Error('Ошибка при восстановлении транзакции')
      }

      setDeletedTransactions(prev => prev.filter(t => t.id !== transactionId))
      setShowConfirmModal(null)
      setErrorMessage('')
      setStatusMessage('Транзакция успешно восстановлена')
    } catch (error) {
      console.error('Ошибка при восстановлении транзакции:', error)
      setStatusMessage('')
      setErrorMessage(error.message || 'Ошибка при восстановлении транзакции')
    }
  }

  // Окончательное удаление транзакции
  const handlePermanentDelete = async (transactionId) => {
    try {
      const response = await apiFetch(`/api/transactions/${transactionId}/permanent-delete`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        }
      })
      
      if (!response.ok) {
        throw new Error('Ошибка при окончательном удалении транзакции')
      }

      setDeletedTransactions(prev => prev.filter(t => t.id !== transactionId))
      setShowConfirmModal(null)
      setErrorMessage('')
      setStatusMessage('Транзакция окончательно удалена')
    } catch (error) {
      console.error('Ошибка при окончательном удалении транзакции:', error)
      setStatusMessage('')
      setErrorMessage(error.message || 'Ошибка при окончательном удалении транзакции')
    }
  }

  // Очистка всей корзины
  const handleEmptyTrash = async () => {
    if (window.confirm('Вы уверены, что хотите окончательно удалить ВСЕ транзакции из корзины? Это действие нельзя отменить!')) {
      try {
        const response = await apiFetch('/api/trash/empty', {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
          }
        })
        
        if (!response.ok) {
          throw new Error('Ошибка при очистке корзины')
        }

        setDeletedTransactions([])
        setErrorMessage('')
        setStatusMessage('Корзина очищена')
      } catch (error) {
        console.error('Ошибка при очистке корзины:', error)
        setStatusMessage('')
        setErrorMessage(error.message || 'Ошибка при очистке корзины')
      }
    }
  }

  const formatDate = (dateString) => formatDateTime(dateString)

  const formatAmount = (amount, currency) => {
    return new Intl.NumberFormat('ru-RU').format(amount) + ' ' + currency
  }

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center mb-6">
          <Button variant="ghost" onClick={onBack} className="mr-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Назад
          </Button>
          <h1 className="text-2xl font-bold">Корзина</h1>
        </div>
        <div className="text-center py-12">
          <p>Загрузка...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      {/* Заголовок */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Button variant="ghost" onClick={onBack} className="mr-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Назад
          </Button>
          <h1 className="text-2xl font-bold">Корзина</h1>
          <span className="ml-3 text-sm text-muted-foreground">
            ({deletedTransactions.length} транзакций)
          </span>
        </div>

        {deletedTransactions.length > 0 && (
          <Button
            variant="destructive"
            onClick={handleEmptyTrash}
            className="text-sm"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Очистить корзину
          </Button>
        )}
      </div>

      {(errorMessage || statusMessage) && (
        <div
          className={`mb-4 rounded-lg border p-4 text-sm ${errorMessage
            ? 'border-destructive/40 bg-destructive/10 text-destructive'
            : 'border-emerald-400/60 bg-emerald-50 text-emerald-700'
          }`}
        >
          {errorMessage || statusMessage}
        </div>
      )}

      {/* Список удаленных транзакций */}
      {deletedTransactions.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <Trash2 className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p className="text-lg mb-2">Корзина пуста</p>
          <p>Удаленные транзакции будут отображаться здесь</p>
        </div>
      ) : (
        <div className="border border-border rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="text-left p-3 text-sm font-medium">Дата и время</th>
                  <th className="text-left p-3 text-sm font-medium">Тип операции</th>
                  <th className="text-left p-3 text-sm font-medium">Сумма</th>
                  <th className="text-left p-3 text-sm font-medium">Оператор</th>
                  <th className="text-left p-3 text-sm font-medium">Описание</th>
                  <th className="text-center p-3 text-sm font-medium">Действия</th>
                </tr>
              </thead>
              <tbody>
                {deletedTransactions.map((transaction) => (
                  <tr key={transaction.id} className="border-b border-border hover:bg-muted/30">
                    <td className="p-3 text-sm">
                      {formatDate(transaction.date_time)}
                    </td>
                    <td className="p-3 text-sm">
                      {transaction.operation_type}
                    </td>
                    <td className="p-3 text-sm font-medium">
                      {formatAmount(transaction.amount, transaction.currency)}
                    </td>
                    <td className="p-3 text-sm">
                      {transaction.operator_name || ''}
                    </td>
                    <td className="p-3 text-sm text-muted-foreground">
                      {transaction.description || ''}
                    </td>
                    <td className="p-3">
                      <div className="flex items-center justify-center space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleRestore(transaction.id)}
                          className="text-green-600 hover:text-green-700 hover:bg-green-50"
                          title="Восстановить транзакцию"
                        >
                          <RotateCcw className="h-3 w-3 mr-1" />
                          Восстановить
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setShowConfirmModal(transaction.id)}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          title="Удалить навсегда"
                        >
                          <Trash2 className="h-3 w-3 mr-1" />
                          Удалить навсегда
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Модальное окно подтверждения */}
      {showConfirmModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center mb-4">
              <AlertTriangle className="h-6 w-6 text-red-600 mr-3" />
              <h3 className="text-lg font-semibold">Подтверждение удаления</h3>
            </div>
            <p className="text-muted-foreground mb-6">
              Вы уверены, что хотите окончательно удалить эту транзакцию? 
              Это действие нельзя отменить.
            </p>
            <div className="flex justify-end space-x-3">
              <Button
                variant="outline"
                onClick={() => setShowConfirmModal(null)}
              >
                Отмена
              </Button>
              <Button
                variant="destructive"
                onClick={() => handlePermanentDelete(showConfirmModal)}
              >
                Удалить навсегда
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default TrashPage

