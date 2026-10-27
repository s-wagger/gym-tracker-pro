/* Gym Tracker Pro - Service Worker (PWA) */
const CACHE_NAME = 'gymtracker-v1.0.0';

const PRECACHE_ASSETS = [
  '/',
  '/dashboard',
  '/workouts',
  '/nutrition',
  '/one-rep-max',
  '/analytics',
  '/export',
  '/static/css/style.css',
  '/static/js/app.js',
  '/static/js/pwa.js',
  '/static/js/logger.js',
  '/static/js/nutrition.js',
  '/static/js/calculator.js',
  '/static/js/analytics.js',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/icons/favicon.png',
  '/static/icons/apple-touch-icon.png',
  '/offline.html'
];

// Install event - precache app shell and static resources
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Pre-caching static assets and offline shell');
      return cache.addAll(PRECACHE_ASSETS).catch((err) => {
        console.warn('[SW] Some precache assets failed to fetch during install:', err);
      });
    })
  );
  self.skipWaiting();
});

// Activate event - cleanup stale caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            console.log('[SW] Purging outdated cache:', cache);
            return caches.delete(cache);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch event - Network-first for dynamic navigation, Cache-first for static assets
self.addEventListener('fetch', (event) => {
  const request = event.request;

  // Don't intercept non-GET requests or browser extensions
  if (request.method !== 'GET' || !request.url.startsWith('http')) {
    return;
  }

  // API calls & CSV downloads: Always try network directly
  if (request.url.includes('/api/') || request.url.includes('/export/')) {
    event.respondWith(
      fetch(request).catch(() => {
        return new Response(JSON.stringify({ error: 'Offline. Connect to network to sync.' }), {
          headers: { 'Content-Type': 'application/json' }
        });
      })
    );
    return;
  }

  // Static assets (CSS, JS, Icons, Images): Cache-first with background network update
  if (
    request.destination === 'style' ||
    request.destination === 'script' ||
    request.destination === 'image' ||
    request.destination === 'font'
  ) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        if (cachedResponse) {
          // Fetch update in background
          fetch(request).then((networkResponse) => {
            if (networkResponse && networkResponse.status === 200) {
              caches.open(CACHE_NAME).then((cache) => cache.put(request, networkResponse));
            }
          }).catch(() => {/* ignore background fetch failure */});
          return cachedResponse;
        }

        return fetch(request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, responseClone));
          }
          return networkResponse;
        });
      })
    );
    return;
  }

  // HTML Page Navigation: Network-first, fallback to cache, then offline.html
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((networkResponse) => {
          const responseClone = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, responseClone));
          return networkResponse;
        })
        .catch(async () => {
          const cached = await caches.match(request);
          if (cached) return cached;
          return caches.match('/offline.html');
        })
    );
    return;
  }

  // Default fallback
  event.respondWith(
    caches.match(request).then((response) => response || fetch(request))
  );
});
