import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, expect, test, beforeEach, afterEach } from 'vitest'
import AddReceiptPage from '../AddReceiptPage.jsx'

const apiFetchMock = vi.fn()

vi.mock('@/lib/api.js', () => ({
  apiFetch: (...args) => apiFetchMock(...args),
  DEFAULT_TELEGRAM_ID: 777001,
  isDefaultTelegramConfigured: () => true
}))

const TEST_TELEGRAM_ID = 777001

const operatorsResponse = {
  ok: true,
  json: async () => ({ operators: [] })
}

const buildTransactionResponse = (overrides = {}) => ({
  id: 501,
  date_time: '2025-01-01T12:30:00',
  operation_type: 'payment',
  amount: 125.5,
  currency: 'UZS',
  description: 'Оплата услуги',
  balance: null,
  card_number: null,
  raw_text: 'Manual entry',
  ...overrides
})

beforeEach(() => {
  apiFetchMock.mockImplementation(async (url) => {
    if (url.startsWith('/api/operators')) {
      return operatorsResponse
    }

    if (url === '/api/transactions') {
      return {
        ok: true,
        json: async () => ({ transaction: buildTransactionResponse() })
      }
    }

    throw new Error(`Unhandled request: ${url}`)
  })
})

afterEach(() => {
  vi.resetAllMocks()
  vi.useRealTimers()
})

describe('AddReceiptPage manual form', () => {
  test('shows validation errors when required fields are missing', async () => {
    render(<AddReceiptPage onBack={vi.fn()} onTransactionAdded={vi.fn()} />)

    await waitFor(() => expect(apiFetchMock).toHaveBeenCalled())
    apiFetchMock.mockClear()

    const submitButton = screen.getByRole('button', { name: /Сохранить чек/i })
    await userEvent.click(submitButton)

    expect(apiFetchMock).not.toHaveBeenCalled()
    expect(
      await screen.findByText('Поле «Дата и время операции» обязательно для заполнения')
    ).toBeInTheDocument()
    expect(
      await screen.findByText('Поле «Сумма операции» обязательно для заполнения')
    ).toBeInTheDocument()
    expect(
      await screen.findByText('Поле «Описание операции» обязательно для заполнения')
    ).toBeInTheDocument()
  })

  test('submits valid payload and handles success workflow', async () => {
    const onBack = vi.fn()
    const onTransactionAdded = vi.fn()
    const transactionPayload = buildTransactionResponse({ id: 902 })

    apiFetchMock.mockImplementation(async (url) => {
      if (url.startsWith('/api/operators')) {
        return operatorsResponse
      }

      if (url === '/api/transactions') {
        return {
          ok: true,
          json: async () => ({ transaction: transactionPayload })
        }
      }

      throw new Error(`Unhandled request: ${url}`)
    })

    render(<AddReceiptPage onBack={onBack} onTransactionAdded={onTransactionAdded} />)

    await waitFor(() => expect(apiFetchMock).toHaveBeenCalled())
    apiFetchMock.mockClear()

    const dateInput = screen.getByLabelText(/Дата и время операции/)
    const amountInput = screen.getByLabelText(/Сумма операции/)
    const descriptionInput = screen.getByLabelText(/Описание операции/)

    fireEvent.change(dateInput, { target: { value: '2025-01-01T12:30' } })
    await userEvent.type(amountInput, '125.50')
    await userEvent.type(descriptionInput, 'Оплата услуги')

    const submitButton = screen.getByRole('button', { name: /Сохранить чек/i })
    await userEvent.click(submitButton)

    await waitFor(() => expect(apiFetchMock).toHaveBeenCalledTimes(1))

    const [url, options] = apiFetchMock.mock.calls[0]
    expect(url).toBe('/api/transactions')
    expect(options?.method).toBe('POST')
    expect(options?.headers).toMatchObject({ 'Content-Type': 'application/json' })

    const payload = JSON.parse(options.body)
    expect(payload).toMatchObject({
      telegram_id: TEST_TELEGRAM_ID,
      date_time: '2025-01-01T12:30',
      operation_type: 'payment',
      amount: 125.5,
      currency: 'UZS',
      description: 'Оплата услуги',
      raw_text: null
    })
    expect(payload).not.toHaveProperty('balance')
    expect(payload).not.toHaveProperty('card_number')

    await waitFor(() => expect(onTransactionAdded).toHaveBeenCalledWith(transactionPayload))
    const successMessages = await screen.findAllByText('Транзакция успешно сохранена')
    expect(successMessages.length).toBeGreaterThan(0)

    await waitFor(() => expect(onBack).toHaveBeenCalledTimes(1), { timeout: 2000 })
  })
})
