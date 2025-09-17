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

const formatTimeParts = (date) => {
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${hours}:${minutes}`
}

export const formatDateOnly = (value) => {
  const date = ensureDate(value)
  return date ? DATE_FORMATTER.format(date) : ''
}

export const formatTimeOnly = (value) => {
  const date = ensureDate(value)
  if (!date) {
    return ''
  }

  const normalized = new Date(date.getTime())
  normalized.setSeconds(0, 0)
  return formatTimeParts(normalized)
}

export const formatDateTime = (value) => {
  const date = ensureDate(value)
  if (!date) {
    return ''
  }

  const datePart = DATE_FORMATTER.format(date)
  const timePart = formatTimeParts(date)
  return `${datePart} ${timePart}`.trim()
}

export const normalizeDateTimeLocalString = (value) => {
  const date = ensureDate(value)
  if (!date) {
    return ''
  }

  const normalized = new Date(date.getTime())
  normalized.setSeconds(0, 0)

  const year = normalized.getFullYear()
  const month = String(normalized.getMonth() + 1).padStart(2, '0')
  const day = String(normalized.getDate()).padStart(2, '0')

  return `${year}-${month}-${day}T${formatTimeParts(normalized)}`
}

export const getDayIndex = (value) => {
  const date = ensureDate(value)
  return date ? date.getDay() : null
}

export { ensureDate }
