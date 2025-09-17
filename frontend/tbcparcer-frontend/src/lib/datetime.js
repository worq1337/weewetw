const ensureDate = (value) => {
  if (!value) {
    return null
  }

  if (value instanceof Date) {
    return Number.isNaN(value.valueOf()) ? null : value
  }

  const parsed = new Date(value)
  return Number.isNaN(parsed.valueOf()) ? null : parsed
}

const DATE_FORMATTER = new Intl.DateTimeFormat('ru-RU', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric'
})

const TIME_FORMATTER = new Intl.DateTimeFormat('ru-RU', {
  hour: '2-digit',
  minute: '2-digit',
  hour12: false
})

export const formatDateOnly = (value) => {
  const date = ensureDate(value)
  return date ? DATE_FORMATTER.format(date) : ''
}

export const formatTimeOnly = (value) => {
  const date = ensureDate(value)
  return date ? TIME_FORMATTER.format(date) : ''
}

export const formatDateTime = (value) => {
  const date = ensureDate(value)
  if (!date) {
    return ''
  }

  const datePart = DATE_FORMATTER.format(date)
  const timePart = TIME_FORMATTER.format(date)
  return `${datePart} ${timePart}`.trim()
}

export const getDayIndex = (value) => {
  const date = ensureDate(value)
  return date ? date.getDay() : null
}

export { ensureDate }
