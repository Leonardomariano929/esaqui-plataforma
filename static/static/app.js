function toggleMenu() {
            document.getElementById('navbarPrincipal').classList.toggle('show');
        }
        // Ativador do Service Worker para o App poder ser baixado
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js');
        }