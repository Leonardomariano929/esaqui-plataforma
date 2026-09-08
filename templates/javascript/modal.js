   // Correção da lógica de envio do robô de instruções
        function perguntarAoBot() {
            var input = document.getElementById('botInput');
            var log = document.getElementById('chatBotLog');
            var textoUser = input.value.trim();
            
            if(!textoUser) return;
            
            log.innerHTML += "<br><span style='color:white;'>Você: " + textoUser + "</span>";
            log.scrollTop = log.scrollHeight;
            
            var formData = new FormData();
            formData.append('mensagem', textoUser);
            
            fetch('/assistente-bot', { method: 'POST', body: formData })
            .then(res => res.json())
            .then(data => {
                log.innerHTML += "<br><span style='color:#00ecff;'>Bot: " + data.resposta + "</span>";
                log.scrollTop = log.scrollHeight;
            })
            .catch(err => {
                log.innerHTML += "<br><span style='color:#ef4444;'>Bot: Erro ao processar dados locais.</span>";
            });
            
            input.value = '';
        }

        // Funções para ativar o clique e zoom da foto de perfil grande
        function abrirZoom(url) {
            document.getElementById('imgZoomed').src = url;
            document.getElementById('zoomModal').style.display = 'flex';
        }
        function fecharZoom() {
            document.getElementById('zoomModal').style.display = 'none';
        }