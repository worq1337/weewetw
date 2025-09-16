const DEFAULT_API_BASE_URL = 'http://localhost:5000'

const trimTrailingSlash = (value) => {
  if (!value) {
    return value
  }

  return value.endsWith('/') ? value.slice(0, -1) : value
}

export const getApiBaseUrl = () => {
  const envBaseUrl = import.meta?.env?.VITE_API_BASE_URL

  if (envBaseUrl && typeof envBaseUrl === 'string') {
    return trimTrailingSlash(envBaseUrl)
  }

  return DEFAULT_API_BASE_URL
}

export const buildApiUrl = (path = '') => {
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }

  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${getApiBaseUrl()}${normalizedPath}`
}

export const apiFetch = (path, options) => {
  const url = buildApiUrl(path)
  return fetch(url, options)
}

export const DEFAULT_TELEGRAM_ID = 123456789
