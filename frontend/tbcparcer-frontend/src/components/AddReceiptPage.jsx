import { useEffect, useMemo, useState } from 'react'
import { ArrowLeft, Save, Sparkles, Upload, X } from 'lucide-react'
import { apiFetch, DEFAULT_TELEGRAM_ID } from '@/lib/api.js'
import {
  manualTransactionFieldGroups,
  createEmptyManualTransaction,
  validateManualTransaction,
  validateManualTransactionField
} from '@/lib/manualTransactionSchema.js'
import { normalizeDateTimeLocalString } from '@/lib/datetime.js'

const buildOperatorOption = (operator) => ({
  value: String(operator.id),
  label: operator.description
    ? `${operator.name} — ${operator.description}`
    : operator.name,
  raw: operator
})

const buildPayload = (formValues) => {
  const payload = {
    telegram_id: DEFAULT_TELEGRAM_ID,
    date_time: normalizeDateTimeLocalString(formValues.date_time),
    operation_type: formValues.operation_type,
    amount: Number(formValues.amount),
    currency: formValues.currency,
    description: formValues.description.trim(),
    raw_text: formValues.raw_text.trim() || null
  }

  if (formValues.balance !== '' && formValues.balance !== null) {
    payload.balance = Number(formValues.balance)
  }

  if (formValues.card_number) {
    payload.card_number = formValues.card_number.trim()
  }

  if (formValues.operator_id) {
    payload.operator_id = Number(formValues.operator_id)
  }

  return payload
}

const getGridColumnsClass = (columns) => {
  if (columns === 2) {
    return 'grid-cols-1 md:grid-cols-2'
  }
  if (columns === 3) {
    return 'grid-cols-1 md:grid-cols-3'
  }
  return 'grid-cols-1'
}

const AddReceiptPage = ({ onBack, onTransactionAdded }) => {
  const [formValues, setFormValues] = useState(createEmptyManualTransaction())
  const [errors, setErrors] = useState({})
  const [operators, setOperators] = useState([])
  const [loading, setLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [receiptText, setReceiptText] = useState('')
  const [parsePreview, setParsePreview] = useState(null)
  const [parseLoading, setParseLoading] = useState(false)
  const [parseError, setParseError] = useState('')

  useEffect(() => {
    const fetchOperators = async () => {
      try {
        const response = await apiFetch(`/api/operators?telegram_id=${DEFAULT_TELEGRAM_ID}`)
        if (!response.ok) {
          throw new Error('Не удалось загрузить операторов')
        }

        const data = await response.json()
        setOperators(Array.isArray(data.operators) ? data.operators : [])
      } catch (error) {
        console.warn('Ошибка загрузки операторов:', error)
        setOperators([])
      }
    }

    fetchOperators()
  }, [])

  const operatorOptions = useMemo(() => {
    return operators.map(buildOperatorOption)
  }, [operators])

  const handleFieldChange = (field, value) => {
    setFormValues(prevValues => {
      const nextValues = { ...prevValues, [field.name]: value }

      if (field.name === 'date_time') {
        nextValues.date_time = normalizeDateTimeLocalString(value)
      }

      if (field.name === 'operator_id') {
        const selected = operatorOptions.find(option => option.value === value)
        if (selected?.raw?.description && !prevValues.description) {
          nextValues.description = selected.raw.description
        }
      }

      return nextValues
    })

    setErrors(prevErrors => ({
      ...prevErrors,
      [field.name]: validateManualTransactionField(field, value)
    }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setErrorMessage('')
    setSuccessMessage('')

    const validationErrors = validateManualTransaction(formValues)
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }

    setLoading(true)

    try {
      const payload = buildPayload(formValues)
      const response = await apiFetch('/api/transactions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        let errorText = 'Ошибка при добавлении транзакции'
        try {
          const errorData = await response.json()
          errorText = errorData.error || errorText
        } catch (parseError) {
          console.warn('Не удалось разобрать ответ об ошибке:', parseError)
        }
        throw new Error(errorText)
      }

      const data = await response.json()
      const createdTransaction = data.transaction

      if (onTransactionAdded && createdTransaction) {
        onTransactionAdded(createdTransaction)
      }

      setSuccessMessage('Транзакция успешно сохранена')
      setFormValues(createEmptyManualTransaction())
      setErrors({})

      setTimeout(() => {
        setSuccessMessage('')
        onBack()
      }, 1500)
    } catch (error) {
      setErrorMessage(error.message || 'Ошибка при добавлении транзакции')
    } finally {
      setLoading(false)
    }
  }

  const handleParseAndSave = async (event) => {
    event.preventDefault()
    setParseError('')
    setSuccessMessage('')

    if (!receiptText.trim()) {
      setParseError('Вставьте текст чека для распознавания')
      return
    }

    setParseLoading(true)

    try {
      const response = await apiFetch('/api/ai/parse-and-save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          text: receiptText,
          telegram_id: DEFAULT_TELEGRAM_ID,
          username: 'web-client'
        })
      })

      if (!response.ok) {
        let errorText = 'Не удалось распознать чек'
        try {
          const errorData = await response.json()
          errorText = errorData.error || errorText
        } catch (parseError) {
          console.warn('Не удалось разобрать ответ об ошибке:', parseError)
        }
        throw new Error(errorText)
      }

      const data = await response.json()
      const createdTransaction = data.transaction

      if (createdTransaction) {
        onTransactionAdded?.(createdTransaction)
      }

      if (data.parsed_data) {
        const normalizedPreview = { ...data.parsed_data }
        if (normalizedPreview.date_time) {
          normalizedPreview.date_time = normalizeDateTimeLocalString(normalizedPreview.date_time)
        }
        setParsePreview(normalizedPreview)
      } else {
        setParsePreview(null)
      }
      setReceiptText('')
      setSuccessMessage('Чек распознан и сохранен')

      setTimeout(() => {
        setSuccessMessage('')
        onBack()
      }, 1500)
    } catch (error) {
      setParseError(error.message || 'Ошибка при распознавании чека')
      setParsePreview(null)
    } finally {
      setParseLoading(false)
    }
  }

  const handleReset = () => {
    setFormValues(createEmptyManualTransaction())
    setErrors({})
    setErrorMessage('')
    setSuccessMessage('')
    setReceiptText('')
    setParseError('')
    setParsePreview(null)
    setParseLoading(false)
  }

  const renderFieldControl = (field) => {
    const value = formValues[field.name]
    const fieldError = errors[field.name]
    const options = field.type === 'select'
      ? field.dynamicOptions === 'operators'
        ? [{ value: '', label: 'Без оператора' }, ...operatorOptions]
        : field.options || []
      : []

    const commonProps = {
      id: field.name,
      name: field.name,
      value: value,
      onChange: (event) => handleFieldChange(field, event.target.value),
      className: `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${fieldError ? 'border-red-400' : 'border-gray-300'}`,
      'aria-invalid': fieldError ? 'true' : 'false'
    }

    if (field.type === 'select') {
      return (
        <select {...commonProps}>
          {options.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      )
    }

    if (field.type === 'textarea') {
      return (
        <textarea
          {...commonProps}
          rows={field.minRows || 3}
          placeholder={field.placeholder}
        />
      )
    }

    const inputSpecificProps = {}

    if (field.type === 'number') {
      inputSpecificProps.type = 'number'
      inputSpecificProps.step = field.step || '0.01'
      inputSpecificProps.inputMode = 'decimal'
      inputSpecificProps.placeholder = field.placeholder
    } else if (field.type === 'datetime-local') {
      inputSpecificProps.type = 'datetime-local'
      inputSpecificProps.placeholder = field.placeholder
      inputSpecificProps.step = '60'
    } else {
      inputSpecificProps.type = field.type || 'text'
      if (field.inputMode) {
        inputSpecificProps.inputMode = field.inputMode
      }
      if (field.maxLength) {
        inputSpecificProps.maxLength = field.maxLength
      }
      inputSpecificProps.placeholder = field.placeholder
    }

    return <input {...commonProps} {...inputSpecificProps} />
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center gap-4 mb-6">
          <button
            onClick={onBack}
            className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft size={20} />
            Назад
          </button>
          <h1 className="text-2xl font-bold text-gray-800">Добавить чек вручную</h1>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6 space-y-8">
          <section className="space-y-4">
            <header className="space-y-2">
              <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                <Sparkles size={18} className="text-blue-500" />
                Распознать чек через AI
              </h2>
              <p className="text-sm text-gray-500">
                Вставьте текст чека, чтобы система распарсила его и сразу добавила в таблицу.
              </p>
            </header>

            <form onSubmit={handleParseAndSave} className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="receipt-text" className="text-sm font-medium text-gray-700">
                  Текст чека
                </label>
                <textarea
                  id="receipt-text"
                  value={receiptText}
                  onChange={(event) => setReceiptText(event.target.value)}
                  rows={6}
                  placeholder="Например, скопируйте текст из Telegram-бота"
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {parseError && (
                <div className="p-3 rounded-lg border border-red-200 bg-red-50 text-sm text-red-700">
                  {parseError}
                </div>
              )}

              {parsePreview && (
                <div className="p-3 rounded-lg border border-blue-200 bg-blue-50 text-sm text-blue-800">
                  <div className="font-medium mb-2">Предпросмотр</div>
                  <pre className="text-xs whitespace-pre-wrap text-blue-900 bg-white/70 border border-blue-100 rounded-md p-2 overflow-x-auto">
                    {JSON.stringify(parsePreview, null, 2)}
                  </pre>
                </div>
              )}

              {successMessage && (
                <div className="p-3 rounded-lg border border-green-200 bg-green-50 text-sm text-green-700">
                  {successMessage}
                </div>
              )}

              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={parseLoading}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
                >
                  <Upload size={18} />
                  {parseLoading ? 'Распознаем…' : 'Распознать и сохранить'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setReceiptText('')
                    setParseError('')
                    setParsePreview(null)
                  }}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100 transition-colors"
                >
                  <X size={16} />
                  Очистить
                </button>
              </div>
            </form>
          </section>

          <form onSubmit={handleSubmit} className="space-y-6">
            {manualTransactionFieldGroups.map(group => (
              <section key={group.id} className="space-y-4">
                <div>
                  <h2 className="text-lg font-semibold text-gray-800">{group.title}</h2>
                  {group.description && (
                    <p className="text-sm text-gray-500 mt-1">{group.description}</p>
                  )}
                </div>

                <div className={`grid gap-4 ${getGridColumnsClass(group.columns)}`}>
                  {group.fields.map(field => (
                    <div key={field.name} className="flex flex-col space-y-2">
                      <label htmlFor={field.name} className="text-sm font-medium text-gray-700">
                        {field.label}
                        {field.required && <span className="text-red-500 ml-1">*</span>}
                      </label>
                      {renderFieldControl(field)}
                      {field.helperText && (
                        <p className="text-xs text-gray-500">{field.helperText}</p>
                      )}
                      {errors[field.name] && (
                        <p className="text-xs text-red-600">{errors[field.name]}</p>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            ))}

            {errorMessage && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                {errorMessage}
              </div>
            )}

            {successMessage && (
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
                {successMessage}
              </div>
            )}

            <div className="flex gap-4 pt-2">
              <button
                type="submit"
                disabled={loading}
                className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
              >
                <Save size={18} />
                {loading ? 'Сохранение...' : 'Сохранить чек'}
              </button>

              <button
                type="button"
                onClick={handleReset}
                className="flex items-center gap-2 px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
              >
                <X size={18} />
                Очистить форму
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default AddReceiptPage
