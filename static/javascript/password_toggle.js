document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.password-toggle').forEach(function (button) {
        button.addEventListener('click', function () {
            const targetId = button.getAttribute('data-target');
            const input = document.getElementById(targetId);
            if (!input) return;
            const isPassword = input.type === 'password';
            input.type = isPassword ? 'text' : 'password';
            button.textContent = isPassword ? 'Ocultar' : 'Mostrar';
            button.setAttribute('aria-label', isPassword ? 'Ocultar senha' : 'Mostrar senha');
        });
    });
});
