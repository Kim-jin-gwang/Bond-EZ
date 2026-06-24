const DEFAULT_BASE_URL = '/api/v1'

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || DEFAULT_BASE_URL).replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message, response, payload = null) {
    super(message)
    this.name = 'ApiError'
    this.response = response
    this.payload = payload
  }
}

export async function apiGet(path, options = {}) {
  const response = await fetch(buildUrl(path, options.params), {
    method: 'GET',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...options.headers,
    },
  })
  const payload = await parseJson(response)

  if (!response.ok || payload?.success === false) {
    throw new ApiError(payload?.message || response.statusText || 'API request failed', response, payload)
  }

  if (options.raw) {
    return payload
  }

  return payload?.data ?? payload
}

export async function apiPost(path, body = {}, options = {}) {
  const response = await fetch(buildUrl(path, options.params), {
    method: options.method || 'POST',
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...options.headers,
    },
    body: body ? JSON.stringify(body) : undefined,
  })
  const payload = await parseJson(response)

  if (!response.ok || payload?.success === false) {
    throw new ApiError(payload?.message || response.statusText || 'API request failed', response, payload)
  }

  return payload?.data ?? payload
}

export async function apiDelete(path, options = {}) {
  return apiPost(path, null, { ...options, method: 'DELETE' })
}


function buildUrl(path, params = null) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  const url = new URL(`${API_BASE_URL}${normalizedPath}`, window.location.origin)

  Object.entries(params || {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') {
      return
    }

    url.searchParams.set(key, Array.isArray(value) ? value.join(',') : value)
  })

  return url.toString()
}

async function parseJson(response) {
  const text = await response.text()

  if (!text) {
    return null
  }

  try {
    return JSON.parse(text)
  } catch {
    throw new ApiError('Invalid JSON response', response)
  }
}
