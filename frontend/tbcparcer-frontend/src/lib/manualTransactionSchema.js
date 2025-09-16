export const OPERATION_TYPE_OPTIONS = [
  { value: 'payment', label: 'Оплата' },
  { value: 'refill', label: 'Пополнение' },
  { value: 'conversion', label: 'Конверсия' },
  { value: 'cancel', label: 'Отмена' }
]

export const CURRENCY_OPTIONS = [
  { value: 'UZS', label: 'UZS — Сум' },
  { value: 'USD', label: 'USD — Доллар США' },
  { value: 'EUR', label: 'EUR — Евро' },
  { value: 'RUB', label: 'RUB — Российский рубль' }
]

export const manualTransactionFieldGroups = [
  {
    id: 'operation',
    title: 'Данные операции',
    description: 'Основные атрибуты транзакции, которые отображаются в таблице и экспорте.',
    columns: 2,
    fields: [
      {
        name: 'date_time',
        label: 'Дата и время операции',
        type: 'datetime-local',
        required: true,
        placeholder: 'Укажите дату и время',
        validation: { type: 'datetime' }
      },
      {
        name: 'operation_type',
        label: 'Тип операции',
        type: 'select',
        required: true,
        defaultValue: 'payment',
        options: OPERATION_TYPE_OPTIONS,
        validation: {
          type: 'enum',
          values: OPERATION_TYPE_OPTIONS.map(option => option.value)
        }
      },
      {
        name: 'currency',
        label: 'Валюта операции',
        type: 'select',
        required: true,
        defaultValue: 'UZS',
        options: CURRENCY_OPTIONS,
        validation: {
          type: 'enum',
          values: CURRENCY_OPTIONS.map(option => option.value)
        }
      }
    ]
  },
  {
    id: 'amounts',
    title: 'Финансовые показатели',
    description: 'Сумма транзакции и остаток на счёте после операции.',
    columns: 2,
    fields: [
      {
        name: 'amount',
        label: 'Сумма операции',
        type: 'number',
        required: true,
        placeholder: '0.00',
        step: '0.01',
        validation: {
          type: 'number',
          min: 0.01,
          message: 'Укажите сумму операции больше нуля'
        }
      },
      {
        name: 'balance',
        label: 'Остаток на счёте',
        type: 'number',
        placeholder: '0.00',
        step: '0.01',
        validation: {
          type: 'number',
          min: 0,
          allowEmpty: true
        }
      }
    ]
  },
  {
    id: 'card',
    title: 'Информация о карте',
    description: 'Используется для заполнения колонки «ПК».',
    columns: 2,
    fields: [
      {
        name: 'card_number',
        label: 'Последние 4 цифры карты',
        type: 'text',
        placeholder: '1234',
        inputMode: 'numeric',
        maxLength: 4,
        validation: {
          type: 'pattern',
          pattern: /^\d{4}$/,
          allowEmpty: true,
          message: 'Введите последние четыре цифры карты'
        }
      }
    ]
  },
  {
    id: 'classification',
    title: 'Классификация',
    description: 'Помогает связать транзакцию с оператором и описанием.',
    columns: 2,
    fields: [
      {
        name: 'operator_id',
        label: 'Оператор / продавец',
        type: 'select',
        placeholder: 'Выберите оператора',
        dynamicOptions: 'operators',
        validation: {
          type: 'enum',
          allowEmpty: true
        }
      },
      {
        name: 'description',
        label: 'Описание операции',
        type: 'textarea',
        required: true,
        minRows: 3,
        placeholder: 'Например: Перевод через HUMO',
        validation: {
          type: 'string',
          minLength: 3,
          message: 'Описание должно содержать минимум 3 символа'
        }
      }
    ]
  },
  {
    id: 'meta',
    title: 'Дополнительная информация',
    description: 'Исходный текст помогает обнаруживать дубликаты и хранить контекст.',
    fields: [
      {
        name: 'raw_text',
        label: 'Исходный текст чека',
        type: 'textarea',
        placeholder: 'Оригинальный текст SMS или уведомления...',
        minRows: 3,
        helperText: 'Поле необязательное, но помогает избежать дублей и сохраняет исходный текст.',
        validation: {
          type: 'string',
          maxLength: 4000,
          allowEmpty: true
        }
      }
    ]
  }
]

export const createEmptyManualTransaction = () => {
  const initialState = {}

  manualTransactionFieldGroups.forEach(group => {
    group.fields.forEach(field => {
      if (field.defaultValue !== undefined) {
        initialState[field.name] = field.defaultValue
      } else {
        initialState[field.name] = ''
      }
    })
  })

  return initialState
}

