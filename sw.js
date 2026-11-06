/* Bitácora Viva · service worker del lanzador.
   Cambia VERSION en cada publicación: las apps instaladas mostrarán «Hay una versión nueva».
   Solo guarda archivos de este sitio. Nunca guarda nada de script.google.com ni datos de estudiantes. */
const VERSION = '2026-11-05.1';
const CACHE = 'bv-lanzador-' + VERSION;
const BASICOS = [
  './',
  './index.html',
  './instalar.html',
  './lanzador.css',
  './lanzador.js',
  './config.js',
  './manifest.webmanifest',
  './icons/icon.svg',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/maskable-192.png',
  './icons/maskable-512.png',
  './icons/apple-touch-icon.png',
  './icons/favicon-32.png',
  './fonts/bricolage-grotesque-latin-700-normal.woff2',
  './fonts/bricolage-grotesque-latin-800-normal.woff2',
  './fonts/atkinson-hyperlegible-latin-400-normal.woff2',
  './fonts/atkinson-hyperlegible-latin-700-normal.woff2'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(BASICOS.map(u => new Request(u, { cache: 'reload' })))));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k.startsWith('bv-lanzador-') && k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('message', e => { if (e.data === 'actualizar') self.skipWaiting(); });

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;          // Google y la app no pasan por aquí

  // Páginas: primero la red (para tener lo último), sin conexión la copia guardada
  if (req.mode === 'navigate') {
    e.respondWith(
      fetch(req)
        .then(r => { if (r.ok) { const c = r.clone(); caches.open(CACHE).then(x => x.put(req, c)); } return r; })
        .catch(() => caches.match(req, { ignoreSearch: true }).then(r => r || caches.match('./index.html')))
    );
    return;
  }
  // config.js: siempre el más nuevo si hay red (por si cambian los enlaces)
  if (url.pathname.endsWith('/config.js')) {
    e.respondWith(fetch(req).then(r => { const c = r.clone(); caches.open(CACHE).then(x => x.put(req, c)); return r; }).catch(() => caches.match(req)));
    return;
  }
  // Resto de archivos propios: copia guardada primero (carga instantánea)
  e.respondWith(caches.match(req, { ignoreSearch: true }).then(r => r || fetch(req)));
});
