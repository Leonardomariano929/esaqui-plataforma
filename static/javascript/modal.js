function perguntarAoBot() {
    var input = document.getElementById('botInput');
    var log = document.getElementById('chatBotLog');
    var textoUser = input.value.trim();

    if (!textoUser) return;

    log.innerHTML += "<br><span style='color:white;'>Você: " + textoUser + "</span>";
    log.scrollTop = log.scrollHeight;

    var formData = new FormData();
    formData.append('mensagem', textoUser);

    fetch('/assistente-bot', { method: 'POST', body: formData })
        .then(function (res) { return res.json(); })
        .then(function (data) {
            log.innerHTML += "<br><span style='color:#00ecff;'>Bot: " + data.resposta + "</span>";
            log.scrollTop = log.scrollHeight;
        })
        .catch(function () {
            log.innerHTML += "<br><span style='color:#ef4444;'>Bot: Erro ao processar dados locais.</span>";
        });

    input.value = '';
}

function abrirZoom(url) {
    document.getElementById('imgZoomed').src = url;
    document.getElementById('zoomModal').style.display = 'flex';
}

function fecharZoom() {
    document.getElementById('zoomModal').style.display = 'none';
}
