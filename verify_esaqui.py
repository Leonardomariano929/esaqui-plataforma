import esaqui
from fastapi.testclient import TestClient

with open('esaqui.py', 'r', encoding='utf-8') as fh:
    source = fh.read()
assert '244923000000' not in source, 'Número real ainda presente no código padrão.'
assert 'SEU_USUARIO_BYBIT' in source, 'Placeholder de conta bancária não foi definido.'

print('HAS_WHATSAPP', hasattr(esaqui, 'suporte_whatsapp'))
print('HAS_SOURCE_ROUTE', '/assistencia-whatsapp' in source)
print('ROUTES', [getattr(r, 'path', None) for r in esaqui.app.routes if ('assistencia' in getattr(r, 'path', '') or 'curso' in getattr(r, 'path', '') or 'chat-admin' in getattr(r, 'path', '') or 'dashboard' in getattr(r, 'path', '') or 'login' in getattr(r, 'path', ''))])

client = TestClient(esaqui.app)
resp_home = client.get('/')
print('HOME', resp_home.status_code, resp_home.headers.get('content-type'))
resp_wa = client.get('/assistencia-whatsapp', params={'numero': '+244000000000', 'mensagem': 'Oi'})
print('WA', resp_wa.status_code, resp_wa.headers.get('location'))
resp_manifest = client.get('/static/manifest.json')
print('MANIFEST', resp_manifest.status_code, resp_manifest.headers.get('content-type'))
