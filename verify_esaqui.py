import esaqui
from fastapi.testclient import TestClient

print('HAS_WHATSAPP', hasattr(esaqui, 'suporte_whatsapp'))
with open('esaqui.py', 'r', encoding='utf-8') as fh:
    source = fh.read()
print('HAS_SOURCE_ROUTE', '/assistencia-whatsapp' in source)
print('ROUTES', [getattr(r, 'path', None) for r in esaqui.app.routes if ('assistencia' in getattr(r, 'path', '') or 'curso' in getattr(r, 'path', '') or 'chat-admin' in getattr(r, 'path', '') or 'dashboard' in getattr(r, 'path', '') or 'login' in getattr(r, 'path', ''))])

client = TestClient(esaqui.app)
resp_home = client.get('/')
print('HOME', resp_home.status_code, resp_home.headers.get('content-type'))
resp_wa = client.get('/assistencia-whatsapp', params={'numero': '244923000000', 'mensagem': 'Oi'})
print('WA', resp_wa.status_code, resp_wa.headers.get('location'))
resp_manifest = client.get('/static/manifest.json')
print('MANIFEST', resp_manifest.status_code, resp_manifest.headers.get('content-type'))
