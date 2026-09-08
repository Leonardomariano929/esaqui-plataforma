 function abrirZoom(url) {
            document.getElementById('imgZoomed').src = url;
            document.getElementById('zoomModal').style.display = 'flex';
        }
        function fecharZoom() {
            document.getElementById('zoomModal').style.display = 'none';
        }