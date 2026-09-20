document.addEventListener('DOMContentLoaded', function () {
    const loadingScreen = document.getElementById('loading-screen');
    const hideLoadingScreen = function () {
        if (!loadingScreen) return;
        loadingScreen.classList.add('hidden');
        document.body.classList.remove('loading');
        window.setTimeout(function () {
            loadingScreen.remove();
        }, 500);
    };

    if (loadingScreen) {
        document.body.classList.add('loading');
        window.addEventListener('load', function () {
            window.setTimeout(hideLoadingScreen, 350);
        }, { once: true });
    }

    const startedAt = Date.now();
    const nav = document.querySelector('.main-nav');
    const toggle = document.querySelector('.menu-toggle');
    const installButton = document.querySelector('[data-install-app]');

    if (toggle && nav) {
        toggle.addEventListener('click', function () {
            nav.classList.toggle('mobile-open');
        });
    }

    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js?v=3').catch(function (error) {
            console.warn('Service Worker not available:', error);
        });
    }

    let deferredPrompt = null;
    window.addEventListener('beforeinstallprompt', function (event) {
        event.preventDefault();
        deferredPrompt = event;
        if (installButton) {
            installButton.hidden = false;
        }
    });

    if (installButton) {
        installButton.addEventListener('click', function () {
            if (!deferredPrompt) {
                window.location.href = '/baixar-app';
                return;
            }
            deferredPrompt.prompt();
            deferredPrompt.userChoice.finally(function () {
                deferredPrompt = null;
            });
        });
    }

    function enviarPermanencia() {
        const duracao = Math.floor((Date.now() - startedAt) / 1000);
        const dados = new FormData();
        dados.append('duracao_segundos', String(duracao));
        fetch('/analytics/heartbeat', { method: 'POST', body: dados, keepalive: true }).catch(function () {});
    }

    window.setInterval(enviarPermanencia, 30000);
    window.addEventListener('pagehide', enviarPermanencia);
});
