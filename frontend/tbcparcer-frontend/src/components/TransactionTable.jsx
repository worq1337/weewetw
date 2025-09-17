import { useState, useRef, useEffect, useCallback, useLayoutEffect } from 'react'
import { Settings, GripVertical, Edit3, Check, X, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button.jsx'
import ColumnSettings from './ColumnSettings'
import { apiFetch } from '@/lib/api.js'

// Ключ для сохранения настроек в localStorage
const STORAGE_KEY = 'tbcparcer_table_settings'

const COLUMN_LABELS = {
  receipt_number: 'Номер чека',
  date_time: 'Дата и время',
  day_name: 'Д.н.',
  date: 'Дата',
  time: 'Время',
  operator_seller: 'Оператор/Продавец',
  application: 'Приложение',
  amount: 'Сумма',
  balance: 'Остаток',
  card_number: 'ПК',
  p2p: 'P2P',
  transaction_type: 'Тип транзакции',
  currency: 'Валюта',
  data_source: 'Источник данных',
  category: 'Категория',
  actions: 'Действия'
}

const OPERATION_TYPE_LABELS = {
  payment: 'Оплата',
  refill: 'Пополнение',
  conversion: 'Конверсия',
  cancel: 'Отмена'
}

const DEFAULT_COLUMN_WIDTHS = {
  receipt_number: 120,
  date_time: 150,
  day_name: 60,
  date: 100,
  time: 80,
  operator_seller: 150,
  application: 150,
  amount: 120,
  balance: 120,
  card_number: 80,
  p2p: 80,
  transaction_type: 120,
  currency: 80,
  data_source: 120,
  category: 120,
  actions: 80
}

const DEFAULT_COLUMN_ORDER = [
  'receipt_number', 'date_time', 'day_name', 'date', 'time',
  'operator_seller', 'application', 'amount', 'balance', 'card_number',
  'p2p', 'transaction_type', 'currency', 'data_source', 'category', 'actions'
]

const MIN_COLUMN_WIDTH = 72
const MAX_COLUMN_WIDTH = 360
const HEADER_PADDING = 40
const CELL_PADDING = 28
const HEADER_FONT = '600 12px Inter, system-ui, sans-serif'
const CELL_FONT = '12px Inter, system-ui, sans-serif'
const HEADER_FALLBACK_CHAR_WIDTH = 9
const CELL_FALLBACK_CHAR_WIDTH = 8
const DAY_NAMES = ['ВС', 'ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ']
const numberFormatter = new Intl.NumberFormat('ru-RU')
const DATE_FORMATTER = new Intl.DateTimeFormat('ru-RU', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric'
})
const TIME_FORMATTER = new Intl.DateTimeFormat('ru-RU', {
  hour: '2-digit',
  minute: '2-digit'
})

const formatCellValue = (transaction, column) => {
  if (!transaction) {
    return ''
  }

  const rawValue = transaction[column]

  if (column === 'amount' || column === 'balance') {
    if (rawValue === null || rawValue === undefined || rawValue === '') {
      return ''
    }

    const numericValue = Number(rawValue)
    if (Number.isNaN(numericValue)) {
      return ''
    }

    return numberFormatter.format(numericValue)
  }

  if (column === 'transaction_type') {
    return OPERATION_TYPE_LABELS[rawValue] || rawValue || ''
  }

  if (column === 'date_time') {
    const source = rawValue || transaction.date_time
    if (!source) {
      return ''
    }

    const date = new Date(source)
    if (Number.isNaN(date.valueOf())) {
      return ''
    }

    return `${DATE_FORMATTER.format(date)} ${TIME_FORMATTER.format(date)}`
  }

  if (column === 'date') {
    const source = rawValue || transaction.date_time
    if (!source) {
      return ''
    }

    const date = new Date(source)
    return Number.isNaN(date.valueOf()) ? '' : DATE_FORMATTER.format(date)
  }

  if (column === 'time') {
    const source = rawValue || transaction.date_time
    if (!source) {
      return ''
    }

    const date = new Date(source)
    return Number.isNaN(date.valueOf()) ? '' : TIME_FORMATTER.format(date)
  }

  if (column === 'day_name') {
    const source = rawValue || transaction.date_time
    if (!source) {
      return ''
    }

    const date = new Date(source)
    if (Number.isNaN(date.valueOf())) {
      return ''
    }

    return DAY_NAMES[date.getDay()] || ''
  }

  if (column === 'card_number') {
    if (!rawValue) {
      return ''
    }

    const value = String(rawValue)
    return value.startsWith('*') ? value : `*${value.slice(-4)}`
  }

  if (column === 'p2p') {
    return rawValue ? 'Да' : 'Нет'
  }

  if (column === 'receipt_number') {
    return transaction.receipt_number || ''
  }

  if (column === 'data_source') {
    return transaction.data_source || 'Telegram Bot'
  }

  if (column === 'category') {
    return transaction.category || 'Общие'
  }

  if (column === 'operator_seller') {
    return transaction.operator_seller || 'Неизвестно'
  }

  if (column === 'application') {
    return transaction.application || 'Неизвестно'
  }

  if (column === 'actions') {
    return ''
  }

  return rawValue || ''
}

const TransactionTable = ({ transactions, onTransactionUpdate }) => {
  const [editingCell, setEditingCell] = useState(null)
  const [editValue, setEditValue] = useState('')
  const [columnWidths, setColumnWidths] = useState({ ...DEFAULT_COLUMN_WIDTHS })
  const [columnOrder, setColumnOrder] = useState([...DEFAULT_COLUMN_ORDER])
  const [columnSettings, setColumnSettings] = useState({})
  const [cellColors, setCellColors] = useState({})
  const [showColumnSettings, setShowColumnSettings] = useState(null)
  const [showColorPicker, setShowColorPicker] = useState(null)
  const [draggedColumn, setDraggedColumn] = useState(null)
  const [resizingColumn, setResizingColumn] = useState(null)
  const [resizeStartX, setResizeStartX] = useState(0)
  const [resizeStartWidth, setResizeStartWidth] = useState(0)

  const tableRef = useRef(null)
  const measurementCanvasRef = useRef(null)
  const userAdjustedColumnsRef = useRef(new Set())

  const measureText = useCallback((text, font, fallbackCharWidth) => {
    const normalized = typeof text === 'string' ? text : String(text ?? '')

    if (typeof window === 'undefined') {
      return normalized.length * fallbackCharWidth
    }

    if (!measurementCanvasRef.current) {
      measurementCanvasRef.current = document.createElement('canvas')
    }

    const context = measurementCanvasRef.current.getContext('2d')
    if (!context) {
      return normalized.length * fallbackCharWidth
    }

    context.font = font
    const metrics = context.measureText(normalized)
    return metrics.width
  }, [])

  const computeAutoWidths = useCallback(({ includeManuallyAdjusted = false } = {}) => {
    if (!transactions || transactions.length === 0) {
      return null
    }

    const calculatedWidths = {}

    columnOrder.forEach((column) => {
      if (column === 'actions') {
        return
      }

      if (!includeManuallyAdjusted && userAdjustedColumnsRef.current.has(column)) {
        return
      }

      const headerLabel = COLUMN_LABELS[column] || column
      const headerWidth = measureText(headerLabel, HEADER_FONT, HEADER_FALLBACK_CHAR_WIDTH) + HEADER_PADDING

      let maxWidth = headerWidth

      for (const transaction of transactions) {
        const displayValue = formatCellValue(transaction, column)
        const width = measureText(displayValue, CELL_FONT, CELL_FALLBACK_CHAR_WIDTH) + CELL_PADDING
        if (width > maxWidth) {
          maxWidth = width
        }
      }

      const clampedWidth = Math.min(
        MAX_COLUMN_WIDTH,
        Math.max(MIN_COLUMN_WIDTH, Math.ceil(maxWidth))
      )

      calculatedWidths[column] = clampedWidth
    })

    return Object.keys(calculatedWidths).length > 0 ? calculatedWidths : null
  }, [columnOrder, measureText, transactions])

  useLayoutEffect(() => {
    const autoWidths = computeAutoWidths()
    if (!autoWidths) {
      return
    }

    setColumnWidths((previous) => {
      let changed = false
      const next = { ...previous }

      Object.entries(autoWidths).forEach(([column, width]) => {
        if (Math.abs((next[column] ?? 0) - width) > 1) {
          next[column] = width
          changed = true
        }
      })

      return changed ? next : previous
    })
  }, [computeAutoWidths])

  // Функции для работы с localStorage
  const saveSettingsToStorage = (settings) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
    } catch (error) {
      console.warn('Не удалось сохранить настройки таблицы:', error)
    }
  }

  const loadSettingsFromStorage = () => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      return saved ? JSON.parse(saved) : null
    } catch (error) {
      console.warn('Не удалось загрузить настройки таблицы:', error)
      return null
    }
  }

  const applySettings = (settings, { markUserAdjusted = true } = {}) => {
    if (settings.columnWidths) {
      setColumnWidths(prev => ({
        ...prev,
        ...settings.columnWidths
      }))

      if (markUserAdjusted) {
        const updatedSet = new Set(userAdjustedColumnsRef.current)
        Object.keys(settings.columnWidths).forEach(column => {
          updatedSet.add(column)
        })
        userAdjustedColumnsRef.current = updatedSet
      }
    }
    if (settings.columnOrder) {
      setColumnOrder(settings.columnOrder)
    }
    if (settings.columnSettings) {
      setColumnSettings(settings.columnSettings)
    }
    if (settings.cellColors) {
      setCellColors(settings.cellColors)
    }
  }

  // Сброс настроек к значениям по умолчанию
  const resetToDefaults = () => {
    userAdjustedColumnsRef.current.clear()

    const defaultSettings = {
      columnWidths: { ...DEFAULT_COLUMN_WIDTHS },
      columnOrder: [...DEFAULT_COLUMN_ORDER],
      columnSettings: {},
      cellColors: {},
      version: '1.0'
    }

    applySettings(defaultSettings, { markUserAdjusted: false })
    saveSettingsToStorage(defaultSettings)
  }

  // Загрузка настроек при монтировании компонента
  useEffect(() => {
    const savedSettings = loadSettingsFromStorage()
    if (savedSettings) {
      applySettings(savedSettings)
    }
  }, [])

  // Автоматическое сохранение при изменении настроек
  useEffect(() => {
    const settings = {
      columnWidths,
      columnOrder,
      columnSettings,
      cellColors,
      version: '1.0'
    }
    saveSettingsToStorage(settings)
  }, [columnWidths, columnOrder, columnSettings, cellColors])

  // Обработка редактирования ячейки
  const handleCellEdit = (rowId, column, currentValue) => {
    setEditingCell({ rowId, column })
    setEditValue(currentValue || '')
  }

  const handleCellSave = () => {
    if (editingCell) {
      const { rowId, column } = editingCell
      const transaction = transactions.find(t => t.id === rowId)
      if (transaction) {
        const updatedTransaction = { ...transaction, [column]: editValue }
        onTransactionUpdate(updatedTransaction)
      }
    }
    setEditingCell(null)
    setEditValue('')
  }

  const handleCellCancel = () => {
    setEditingCell(null)
    setEditValue('')
  }

  // Обработка удаления транзакции
  const handleDeleteTransaction = async (transactionId) => {
    if (window.confirm('Вы уверены, что хотите переместить эту транзакцию в корзину?')) {
      try {
        const response = await apiFetch(`/api/transactions/${transactionId}/soft-delete`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          }
        })
        
        if (response.ok) {
          // Удаляем транзакцию из локального состояния
          if (onTransactionUpdate) {
            onTransactionUpdate({ id: transactionId, deleted: true })
          }
        } else {
          console.error('Ошибка при удалении транзакции')
          alert('Ошибка при удалении транзакции')
        }
      } catch (error) {
        console.error('Ошибка при удалении транзакции:', error)
        alert('Ошибка при удалении транзакции')
      }
    }
  }

  // Обработка изменения размера колонок
  const handleResizeStart = (e, column) => {
    e.preventDefault()
    userAdjustedColumnsRef.current.add(column)
    setResizingColumn(column)
    setResizeStartX(e.clientX)
    setResizeStartWidth(columnWidths[column])
  }

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (resizingColumn) {
        const diff = e.clientX - resizeStartX
        const newWidth = Math.max(MIN_COLUMN_WIDTH, resizeStartWidth + diff)
        setColumnWidths(prev => ({
          ...prev,
          [resizingColumn]: newWidth
        }))
      }
    }

    const handleMouseUp = () => {
      setResizingColumn(null)
    }

    if (resizingColumn) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [resizingColumn, resizeStartX, resizeStartWidth])

  // Обработка перетаскивания колонок
  const handleDragStart = (e, column) => {
    setDraggedColumn(column)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  const handleDrop = (e, targetColumn) => {
    e.preventDefault()
    if (draggedColumn && draggedColumn !== targetColumn) {
      const newOrder = [...columnOrder]
      const draggedIndex = newOrder.indexOf(draggedColumn)
      const targetIndex = newOrder.indexOf(targetColumn)
      
      newOrder.splice(draggedIndex, 1)
      newOrder.splice(targetIndex, 0, draggedColumn)
      
      setColumnOrder(newOrder)
    }
    setDraggedColumn(null)
  }

  // Обработка настроек колонки
  const handleColumnSettingsChange = (column, settings) => {
    setColumnSettings(prev => ({
      ...prev,
      [column]: settings
    }))
  }

  // Обработка цвета ячейки
  const handleCellColorChange = (rowId, column, color) => {
    setCellColors(prev => ({
      ...prev,
      [`${rowId}-${column}`]: color
    }))
  }

  // Функция авто-подстройки колонок
  const autoFitColumns = () => {
    const calculated = computeAutoWidths({ includeManuallyAdjusted: true })
    if (!calculated) {
      return
    }

    userAdjustedColumnsRef.current.clear()

    setColumnWidths((previous) => {
      let changed = false
      const next = { ...previous }

      Object.entries(calculated).forEach(([column, width]) => {
        if (Math.abs((next[column] ?? 0) - width) > 1) {
          next[column] = width
          changed = true
        }
      })

      return changed ? next : previous
    })
  }

  const getCellAlignment = (column) => {
    const settings = columnSettings[column]
    return settings?.alignment || 'left'
  }

  const getCellStyle = (rowId, column) => {
    const colorKey = `${rowId}-${column}`
    const backgroundColor = cellColors[colorKey]
    const alignment = getCellAlignment(column)
    
    return {
      backgroundColor: backgroundColor || 'transparent',
      textAlign: alignment,
      width: columnWidths[column],
      minWidth: columnWidths[column],
      maxWidth: columnWidths[column]
    }
  }

  return (
    <div className="border border-border rounded-lg overflow-hidden bg-card relative">
      <div className="overflow-x-auto" ref={tableRef}>
        <table className="w-full professional-table">
          <thead>
            <tr className="border-b border-border bg-muted/50">
              {columnOrder.map((column) => (
                <th
                  key={column}
                  className="relative group border-r border-border last:border-r-0 h-10"
                  style={{ width: columnWidths[column], minWidth: columnWidths[column] }}
                  draggable
                  onDragStart={(e) => handleDragStart(e, column)}
                  onDragOver={handleDragOver}
                  onDrop={(e) => handleDrop(e, column)}
                >
                  <div className="flex items-center justify-between px-3 py-2 h-full">
                    <div className="flex items-center space-x-2 flex-1 min-w-0">
                      <GripVertical className="h-3 w-3 text-muted-foreground column-drag-handle" />
                      <span className="text-xs font-medium text-foreground truncate">
                        {COLUMN_LABELS[column]}
                      </span>
                    </div>
                    
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                      onClick={() => setShowColumnSettings(showColumnSettings === column ? null : column)}
                    >
                      <Settings className="h-3 w-3" />
                    </Button>
                  </div>
                  
                  {/* Resize handle */}
                  <div
                    className="column-resizer"
                    onMouseDown={(e) => handleResizeStart(e, column)}
                  />
                  
                  {/* Column settings dropdown */}
                  {showColumnSettings === column && (
                    <ColumnSettings
                      column={column}
                      settings={columnSettings[column] || {}}
                      onSettingsChange={(settings) => handleColumnSettingsChange(column, settings)}
                      onClose={() => setShowColumnSettings(null)}
                    />
                  )}
                </th>
              ))}
            </tr>
          </thead>
          
          <tbody>
            {transactions.map((transaction) => (
              <tr key={transaction.id} className="border-b border-border hover:bg-muted/30 transition-colors">
                {columnOrder.map((column) => (
                  <td
                    key={`${transaction.id}-${column}`}
                    className="border-r border-border last:border-r-0 h-10 relative group"
                    style={getCellStyle(transaction.id, column)}
                    onContextMenu={(e) => {
                      e.preventDefault()
                      if (column !== 'actions') {
                        setShowColorPicker({
                          rowId: transaction.id,
                          column: column,
                          x: e.clientX,
                          y: e.clientY
                        })
                      }
                    }}
                  >
                    {column === 'actions' ? (
                      <div className="px-3 py-2 h-full flex items-center justify-center">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                          onClick={() => handleDeleteTransaction(transaction.id)}
                          title="Переместить в корзину"
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    ) : editingCell?.rowId === transaction.id && editingCell?.column === column ? (
                      <div className="flex items-center px-2 py-1 h-full">
                        <input
                          type="text"
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          className="flex-1 bg-transparent border-none outline-none text-xs"
                          autoFocus
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleCellSave()
                            if (e.key === 'Escape') handleCellCancel()
                          }}
                        />
                        <div className="flex space-x-1 ml-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-5 w-5 p-0"
                            onClick={handleCellSave}
                          >
                            <Check className="h-3 w-3 text-green-600" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-5 w-5 p-0"
                            onClick={handleCellCancel}
                          >
                            <X className="h-3 w-3 text-red-600" />
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div
                        className="px-3 py-2 h-full flex items-center cursor-pointer"
                        onClick={() => handleCellEdit(transaction.id, column, transaction[column])}
                      >
                        <span className="text-xs text-foreground truncate w-full">
                          {formatCellValue(transaction, column)}
                        </span>
                        <Edit3 className="h-3 w-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity ml-2 flex-shrink-0" />
                      </div>
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {transactions.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          <p>Нет данных для отображения</p>
        </div>
      )}
      
      {/* Кнопки управления */}
      <div className="absolute bottom-4 right-4 flex space-x-2">
        <Button
          variant="outline"
          size="sm"
          onClick={autoFitColumns}
          className="compact-button opacity-70 hover:opacity-100 transition-opacity"
          title="Автоматически подогнать ширину колонок под содержимое"
        >
          <GripVertical className="h-3 w-3 mr-1" />
          Авто-размер
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={resetToDefaults}
          className="compact-button opacity-70 hover:opacity-100 transition-opacity"
          title="Сбросить настройки таблицы к значениям по умолчанию"
        >
          <Settings className="h-3 w-3 mr-1" />
          Сбросить вид
        </Button>
      </div>

      {/* Палитра цветов */}
      {showColorPicker && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setShowColorPicker(null)}
          />
          <div 
            className="fixed z-50 color-palette"
            style={{
              left: showColorPicker.x,
              top: showColorPicker.y,
              transform: 'translate(-50%, -100%)'
            }}
          >
            <div className="text-xs font-medium mb-2 text-gray-700">Выберите цвет ячейки:</div>
            <div className="grid grid-cols-5 gap-2">
              {[
                'transparent', '#ffebee', '#e8f5e8', '#e3f2fd', '#fff3e0', 
                '#f3e5f5', '#ffffff', '#ffcdd2', '#c8e6c9', '#bbdefb', 
                '#ffcc80', '#ce93d8', '#f5f5f5', '#ef9a9a', '#a5d6a7', 
                '#90caf9', '#ffb74d', '#ba68c8', '#eeeeee', '#e57373', 
                '#81c784', '#64b5f6', '#ff9800', '#ab47bc', '#e0e0e0'
              ].map(color => (
                <button
                  key={color}
                  className="color-option"
                  style={{ backgroundColor: color === 'transparent' ? 'white' : color }}
                  onClick={() => {
                    handleCellColorChange(
                      showColorPicker.rowId, 
                      showColorPicker.column, 
                      color === 'transparent' ? null : color
                    )
                    setShowColorPicker(null)
                  }}
                  title={color === 'transparent' ? 'Убрать цвет' : color}
                >
                  {color === 'transparent' && (
                    <div className="w-full h-full flex items-center justify-center text-red-500 text-xs">×</div>
                  )}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default TransactionTable

