import { useEffect, useMemo, useState } from 'react'
import { ArrowLeft, Save, X } from 'lucide-react'
import { apiFetch, DEFAULT_TELEGRAM_ID } from '@/lib/api.js'
import {
  manualTransactionFieldGroups,
  createEmptyManualTransaction
} from '@/lib/manualTransactionSchema.js'

const buildOperatorOption = (operator) => ({
  value: String(operator.id),
  label: operator.description
    ? `${operator.name} — ${operator.description}`
    : operator.name,
  raw: operator
})

const getFieldError = (field, rawValue) => {
  const value = typeof rawValue === 'string' ? rawValue.trim() : rawValue
  const { validation = {}, required, label } = field

  if (required && (value === '' || value === null || value === undefined)) {
    return `Поле «${label}» обязательно для заполнения`
  }

  if (value === '' || value === null || value === undefined) {
    return undefined
  }

  switch (validation.type) {
    case 'datetime': {
      const dateValue = new Date(value)
      if (Number.isNaN(dateValue.valueOf())) {
        return 'Укажите корректную дату и время'
      }
      return undefined
    }
    case 'enum': {
      if (validation.values && !validation.values.includes(value)) {
        return 'Выберите значение из списка'
      }
      return undefined
    }
    case 'number': {
      const numericValue = Number(value)
      if (Number.isNaN(numericValue)) {
        return 'Введите число'
      }
      if (validation.min !== undefined && numericValue < validation.min) {
        return validation.message || `Значение должно быть не меньше ${validation.min}`
      }
      if (validation.max !== undefined && numericValue > validation.max) {
        return validation.message || `Значение должно быть не больше ${validation.max}`
      }
      return undefined
    }
    case 'pattern': {
      if (validation.pattern && !validation.pattern.test(value)) {
        if (validation.allowEmpty && value === '') {
          return undefined
        }
        return validation.message || 'Неверный формат значения'
      }
      return undefined
    }
    case 'string': {
      if (validation.minLength && value.length < validation.minLength) {
        return validation.message || `Минимальная длина — ${validation.minLength} символа`
      }
      if (validation.maxLength && value.length > validation.maxLength) {
        return validation.message || `Максимальная длина — ${validation.maxLength} символов`
      }
      return undefined
    }
    default:
      return undefined
  }
}

const buildPayload = (formValues) => {
  const payload = {
    telegram_id: DEFAULT_TELEGRAM_ID,
    date_time: formValues.date_time,
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
      [field.name]: undefined
    }))
  }

  const validateForm = () => {
    const validationErrors = {}

    manualTransactionFieldGroups.forEach(group => {
      group.fields.forEach(field => {
        const fieldValue = formValues[field.name]
        const fieldError = getFieldError(field, fieldValue)
        if (fieldError) {
          validationErrors[field.name] = fieldError
        }
      })
    })

    return validationErrors
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setErrorMessage('')
    setSuccessMessage('')

    const validationErrors = validateForm()
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

  const handleReset = () => {
    setFormValues(createEmptyManualTransaction())
    setErrors({})
    setErrorMessage('')
    setSuccessMessage('')
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

        <div className="bg-white rounded-lg shadow-sm border p-6">
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
