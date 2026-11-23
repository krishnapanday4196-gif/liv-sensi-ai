/**
 * LIV-SENSI AI – PWA SERVICE WORKER
 * Enables mobile standalone app installation ("Add to Home Screen" / "Install App")
 */

const CACHE_NAME = 'livsensi-pwa-v1';

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
  // Pass-through to network for live data
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
