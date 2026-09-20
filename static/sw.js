const CACHE_NAME = 'esaqui-shell-v3';
const APP_SHELL = [
    '/',
    '/static/style.css?v=3',
    '/static/app.js?v=3',
    '/static/manifest.json?v=3',
    '/static/fotos/padrao.svg?v=3'
];

self.addEventListener('install', function (event) {
    event.waitUntil(
        caches.open(CACHE_NAME).then(function (cache) {
            return cache.addAll(APP_SHELL);
        }).then(function () {
            return self.skipWaiting();
        })
    );
});

self.addEventListener('activate', function (event) {
    event.waitUntil(
        caches.keys().then(function (keys) {
            return Promise.all(keys.filter(function (key) {
                return key !== CACHE_NAME;
            }).map(function (key) {
                return caches.delete(key);
            }));
        }).then(function () {
            return self.clients.claim();
        })
    );
});

self.addEventListener('fetch', function (event) {
    if (event.request.method !== 'GET') return;

    event.respondWith(
        caches.match(event.request).then(function (cached) {
            if (cached) return cached;

            return fetch(event.request).then(function (response) {
                const cloned = response.clone();
                caches.open(CACHE_NAME).then(function (cache) {
                    cache.put(event.request, cloned);
                });
                return response;
            }).catch(function () {
                return caches.match('/') || Response.redirect('/');
            });
        })
    );
});
