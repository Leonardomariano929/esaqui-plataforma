document.addEventListener('DOMContentLoaded', function () {
    const nav = document.querySelector('.main-nav');
    const toggle = document.querySelector('.menu-toggle');
    const installButton = document.querySelector('[data-install-app]');

    if (toggle && nav) {
        toggle.addEventListener('click', function () {
            nav.classList.toggle('mobile-open');
        });
    }

    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js').catch(function (error) {
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
});
