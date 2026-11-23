/**
 * LIV-SENSI AI – PWA SERVICE WORKER
 * Ultra-fast, non-blocking mobile service worker
 */

const CACHE_NAME = 'livsensi-v2';

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

// Pass-through without blocking navigation
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  // Let browser handle navigation directly for instant loading
  if (event.request.mode === 'navigate') return;
});
