const cache = new Map()
const DEFAULT_TTL = 1000 * 60 * 5

export function cachedQuery(key, fetcher, options = {}) {
  const ttl = options.ttl ?? DEFAULT_TTL
  const now = Date.now()
  const cached = cache.get(key)

  if (cached?.data && cached.expiresAt > now) {
    return Promise.resolve(cached.data)
  }

  if (cached?.promise) {
    return cached.promise
  }

  const promise = Promise.resolve()
    .then(fetcher)
    .then((data) => {
      cache.set(key, {
        data,
        expiresAt: Date.now() + ttl,
        promise: null,
      })
      return data
    })
    .catch((error) => {
      cache.delete(key)
      throw error
    })

  cache.set(key, {
    data: cached?.data,
    expiresAt: cached?.expiresAt ?? 0,
    promise,
  })

  return promise
}

export function clearCache(key) {
  if (key) {
    cache.delete(key)
    return
  }

  cache.clear()
}
