const CACHE_NAME = 'shadesense-v2'
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/shadesense-icon.svg',
  '/manifest.json',
]

// Install — cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  )
  self.skipWaiting()
})

// Activate — clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  )
  self.clients.claim()
})

// Fetch — cache first, then network
self.addEventListener('fetch', (event) => {
  const requestUrl = new URL(event.request.url)

  // Skip non-GET and API requests
  if (
    event.request.method !== 'GET' ||
    !['http:', 'https:'].includes(requestUrl.protocol) ||
    requestUrl.pathname.startsWith('/api/')
  ) {
    return
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached

      return fetch(event.request).then((response) => {
        // Cache successful responses for static assets
        if (response.ok && (
          requestUrl.pathname.endsWith('.js') ||
          requestUrl.pathname.endsWith('.css') ||
          requestUrl.pathname.endsWith('.svg') ||
          requestUrl.pathname.endsWith('.png') ||
          requestUrl.pathname.endsWith('.jpg') ||
          requestUrl.pathname.endsWith('.woff2')
        )) {
          const clone = response.clone()
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone))
        }
        return response
      })
    }).catch(() => caches.match('/'))
  )
})
