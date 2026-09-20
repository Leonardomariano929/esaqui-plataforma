from fastapi import FastAPI, Request, Form, UploadFile, File, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import sqlite3
import os
import shutil
import base64
import hashlib
import uuid
import secrets
from datetime import datetime
import openpyxl
import bcrypt
from cryptography.fernet import Fernet
from urllib.request import Request as UrlRequest, urlopen
from urllib.parse import quote_plus
import re
import html as html_lib
import zipfile
from datetime import datetime, timedelta

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from fastapi import Response

@app.get("/sitemap.xml")
async def get_sitemap():
    base_url = "https://esaqui-plataforma.onrender.com" 
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/css" href="https://www.xml-sitemaps.com/css/sitemap.css"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">

  <url>
       <loc>https://esaqui-plataforma.onrender.com/</loc>
       <lastmod>2026-09-20T08:56:24+00:00</lastmod>
       <priority>1.0000</priority>
  </url>
  <url>
       <loc>https://esaqui-plataforma.onrender.com/cadastro</loc>
       <lastmod>2026-09-20T08:56:24+00:00</lastmod>
       <priority>0.8000</priority>
  </url>
  <url>
       <loc>https://esaqui-plataforma.onrender.com/login</loc>
       <lastmod>2026-09-20T08:56:24+00:00</lastmod>
       <priority>0.8000</priority>
  </url>
  <url>
       <loc>https://esaqui-plataforma.onrender.com/curso/1</loc>
       <lastmod>2026-09-20T08:56:24+00:00</lastmod>
       <priority>0.8000</priority>
  </url>
  <url>
       <loc>https://esaqui-plataforma.onrender.com/curso/2</loc>
       <lastmod>2026-09-20T08:56:24+00:00</lastmod>
       <priority>0.8000</priority>
  </url>
  <url>
       <loc>https://esaqui-plataforma.onrender.com/curso/3</loc>
       <lastmod>2026-09-20T08:56:24+00:00</lastmod>
       <priority>0.8000</priority>
  </url>
  <url>
       <loc>https://esaqui-plataforma.onrender.com/curso/4</loc>
       <lastmod>2026-09-20T08:56:24+00:00</lastmod>
       <priority>0.8000</priority>
  </url>
  <url>
       <loc>https://esaqui-plataforma.onrender.com/recuperar</loc>
       <lastmod>2026-09-20T08:56:24+00:00</lastmod>
       <priority>0.6400</priority>
  </url>
</urlset>
"""
    return Response(content=sitemap_xml, media_type="application/xml")

app = FastAPI(title="ESAQUI - Sistema Automatizado")
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("ESAQUI_SECRET_KEY", "ESAQUI-SECRET-CHANGE-ME-2026-SECURE-KEY"), max_age=3600, same_site="lax", https_only=False)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "+244000000000")
WHATSAPP_MESSAGE = os.environ.get("WHATSAPP_MESSAGE", "Olá, gostaria de assistência da ESAQUI.")
FACEBOOK_URL = os.environ.get("FACEBOOK_URL", "https://facebook.com/esaqui")


def carregar_configuracao(chave: str, padrao: str = "") -> str:
    conn = sqlite3.connect("esaqui.db")
    conn.row_factory = sqlite3.Row
    valor = conn.execute("SELECT valor FROM configuracoes WHERE chave = ?", (chave,)).fetchone()
    conn.close()
    if valor and valor["valor"]:
        return valor["valor"]
    return padrao


def guardar_configuracao(chave: str, valor: str):
    conn = sqlite3.connect("esaqui.db")
    conn.execute(
        "INSERT INTO configuracoes (chave, valor) VALUES (?, ?) ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor",
        (chave, (valor or "").strip()),
    )
    conn.commit()
    conn.close()
INSTAGRAM_URL = os.environ.get("INSTAGRAM_URL", "https://instagram.com/esaqui")
TIKTOK_URL = os.environ.get("TIKTOK_URL", "https://www.tiktok.com/@esaqui")
APP_STORE_URL = os.environ.get("APP_STORE_URL", "https://apps.microsoft.com")
GOOGLE_PLAY_URL = os.environ.get("GOOGLE_PLAY_URL", "https://play.google.com")
BYBIT_ACCOUNT = os.environ.get("BYBIT_ACCOUNT", "SEU_USUARIO_BYBIT")
AIRM_ACCOUNT = os.environ.get("AIRM_ACCOUNT", "SEU_USUARIO_AIRTM")
GOOGLE_AD_REVENUE_PER_VISIT_USD = float(os.environ.get("GOOGLE_AD_REVENUE_PER_VISIT_USD", "0.0025"))
GOOGLE_AD_REVENUE_PER_VISIT_EUR = float(os.environ.get("GOOGLE_AD_REVENUE_PER_VISIT_EUR", "0.0022"))
GOOGLE_AD_REVENUE_PER_ONLINE_USER_USD = float(os.environ.get("GOOGLE_AD_REVENUE_PER_ONLINE_USER_USD", "0.08"))
GOOGLE_AD_REVENUE_PER_ONLINE_USER_EUR = float(os.environ.get("GOOGLE_AD_REVENUE_PER_ONLINE_USER_EUR", "0.07"))
APP_DOWNLOAD_PATH = os.path.join(BASE_DIR, "static", "ESAQUI-App.apk")

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
UPLOAD_DIR = "comprovativos"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/comprovativos", StaticFiles(directory=UPLOAD_DIR), name="comprovativos")

VIDEOS_DIR = os.path.join("static", "videos")
CERTIFICADOS_DIR = "certificados"
FOTOS_DIR = os.path.join("static", "fotos")
PDFS_DIR = os.path.join("static", "pdfs")

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(CERTIFICADOS_DIR, exist_ok=True)
os.makedirs(FOTOS_DIR, exist_ok=True)
os.makedirs(PDFS_DIR, exist_ok=True)
app.mount("/pdfs", StaticFiles(directory=PDFS_DIR), name="pdfs")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
templates.env.cache = None

APP_SECRET = os.environ.get("ESAQUI_SECRET_KEY", "ESAQUI-SECRET-CHANGE-ME-2026-SECURE-KEY")
FERNET_KEY = base64.urlsafe_b64encode(hashlib.sha256(APP_SECRET.encode("utf-8")).digest())
fernet = Fernet(FERNET_KEY)


def criptografar_email(email: str) -> str:
    email = (email or "").strip().lower()
    if not email:
        return ""
    return fernet.encrypt(email.encode("utf-8")).decode("utf-8")


def descriptografar_email(email_criptografado: str) -> str:
    if not email_criptografado:
        return ""
    try:
        return fernet.decrypt(email_criptografado.encode("utf-8")).decode("utf-8")
    except Exception:
        return ""


def criptografar_senha(senha_pura: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(senha_pura.encode('utf-8'), salt).decode('utf-8')


def verificar_senha(senha_pura: str, senha_criptografada: str) -> bool:
    try:
        return bcrypt.checkpw(senha_pura.encode('utf-8'), senha_criptografada.encode('utf-8'))
    except Exception:
        return False


def normalizar_email(email: str) -> str:
    return (email or "").strip().lower()


def buscar_usuario_por_email(conn, email: str):
    email = normalizar_email(email)
    if not email:
        return None
    cursor = conn.cursor()
    conn.row_factory = sqlite3.Row
    for row in cursor.execute("SELECT * FROM usuarios").fetchall():
        stored_email = row["email"]
        if stored_email == email:
            return row
        if stored_email and descriptografar_email(stored_email) == email:
            return row
    return None


def usuario_logado(request: Request):
    return request.session.get("usuario")


def exigir_login(request: Request, roles=None):
    usuario = usuario_logado(request)
    if not usuario:
        return None
    if roles and usuario.get("role") not in roles:
        return None
    return usuario


def hash_visitante(identificador: str) -> str:
    return hashlib.sha256(f"{APP_SECRET}:{identificador}".encode("utf-8")).hexdigest()


def calcular_resumo_financeiro() -> dict:
    conn = sqlite3.connect("esaqui.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    visitas_total = cursor.execute("SELECT COUNT(*) AS total, COALESCE(SUM(duracao_segundos), 0) AS segundos FROM visitas").fetchone()
    visitantes_online = cursor.execute(
        "SELECT COUNT(DISTINCT visitante_hash) AS total FROM visitas WHERE ultimo_sinal >= ?",
        ((datetime.now() - timedelta(minutes=15)).isoformat(timespec="seconds"),),
    ).fetchone()
    alunos_online = cursor.execute(
        "SELECT COUNT(*) AS total FROM usuarios WHERE role = 'aluno'"
    ).fetchone()

    valor_visita_usd = float(os.environ.get("GOOGLE_AD_REVENUE_PER_VISIT_USD", "0.0025"))
    valor_visita_eur = float(os.environ.get("GOOGLE_AD_REVENUE_PER_VISIT_EUR", "0.0022"))
    valor_aluno_online_usd = float(os.environ.get("GOOGLE_AD_REVENUE_PER_ONLINE_USER_USD", "0.08"))
    valor_aluno_online_eur = float(os.environ.get("GOOGLE_AD_REVENUE_PER_ONLINE_USER_EUR", "0.07"))

    visitas = int(visitas_total["total"] or 0)
    aluno_ativos = int(visitantes_online["total"] or 0)
    receita_usd = (visitas * valor_visita_usd) + (aluno_ativos * valor_aluno_online_usd)
    receita_eur = (visitas * valor_visita_eur) + (aluno_ativos * valor_aluno_online_eur)

    conn.close()
    return {
        "visitas": visitas,
        "visitantes_online": aluno_ativos,
        "alunos_online": int(alunos_online["total"] or 0),
        "tempo_total_segundos": int(visitas_total["segundos"] or 0),
        "receita_usd": round(receita_usd, 2),
        "receita_eur": round(receita_eur, 2),
        "valor_visita_usd": valor_visita_usd,
        "valor_visita_eur": valor_visita_eur,
        "valor_aluno_online_usd": valor_aluno_online_usd,
        "valor_aluno_online_eur": valor_aluno_online_eur,
    }


@app.middleware("http")
async def registrar_visita(request: Request, call_next):
    inicio = datetime.now()
    response = await call_next(request)
    rota = request.url.path
    if request.method == "GET" and not rota.startswith(("/static", "/pdfs", "/certificados", "/comprovativos")):
        visitante = request.session.get("visitante_id")
        if not visitante:
            visitante = secrets.token_hex(16)
            request.session["visitante_id"] = visitante
        agora = datetime.now().isoformat(timespec="seconds")
        conn = sqlite3.connect("esaqui.db")
        conn.execute(
            "INSERT INTO visitas (visitante_hash, rota, inicio, ultimo_sinal, duracao_segundos) VALUES (?, ?, ?, ?, 0)",
            (hash_visitante(visitante), rota, inicio.isoformat(timespec="seconds"), agora),
        )
        conn.commit()
        conn.close()
    return response


def salvar_upload(upload: UploadFile, diretorio: str, extensoes_permitidas: set[str]) -> str | None:
    if not upload or not upload.filename:
        return None
    extensao = os.path.splitext(os.path.basename(upload.filename))[1].lower()
    if extensao not in extensoes_permitidas:
        return None
    nome_seguro = f"{uuid.uuid4().hex}{extensao}"
    caminho = os.path.join(diretorio, nome_seguro)
    with open(caminho, "wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)
    return nome_seguro


def buscar_web_snippets(consulta: str, limite: int = 3):
    termo = (consulta or "").strip()
    if not termo:
        return []
    url = "https://duckduckgo.com/html/?q=" + quote_plus(termo + " curso formação tecnologia")
    req = UrlRequest(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(req, timeout=10) as resposta:
            html = resposta.read().decode("utf-8", errors="ignore")
    except Exception:
        return []

    fragmentos = []
    padroes = re.findall(r'<a rel="nofollow" class="result-link".*?>(.*?)</a>.*?(?:<a class="result-snippet".*?>(.*?)</a>|<div class="result__snippet">(.*?)</div>)', html, re.S | re.I)
    for item in padroes:
        titulo = item[0]
        texto = item[1] or item[2] or ""
        titulo_limpo = re.sub(r'<.*?>', '', titulo)
        texto_limpo = re.sub(r'<.*?>', '', texto)
        titulo_limpo = html_lib.unescape(titulo_limpo).strip()
        texto_limpo = html_lib.unescape(texto_limpo).strip()
        if titulo_limpo and texto_limpo:
            fragmentos.append(f"{titulo_limpo} — {texto_limpo[:140]}")
            if len(fragmentos) >= limite:
                break
    return fragmentos


def init_db():
    conn = sqlite3.connect("esaqui.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
            telefone TEXT NOT NULL, senha TEXT NOT NULL, pergunta_seguranca TEXT NOT NULL,
            resposta_seguranca TEXT NOT NULL, role TEXT DEFAULT 'aluno', foto TEXT DEFAULT '/static/fotos/padrao.svg'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cursos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            descricao TEXT NOT NULL,
            preco REAL DEFAULT 25000.00,
            video_apresentacao TEXT DEFAULT NULL,
            pdf_url TEXT DEFAULT NULL,
            icone TEXT DEFAULT '🎓',
            slug TEXT DEFAULT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matriculas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER NOT NULL, curso_id INTEGER NOT NULL,
            comprovativo TEXT DEFAULT NULL, status_pagamento TEXT DEFAULT 'Não Enviado', FOREIGN KEY(aluno_id) REFERENCES usuarios(id)
        )
    """)
    cursor.execute("CREATE TABLE IF NOT EXISTS aulas (id INTEGER PRIMARY KEY AUTOINCREMENT, curso_id INTEGER NOT NULL, modulo TEXT NOT NULL, titulo TEXT NOT NULL, url_video TEXT NOT NULL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS notas (id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER NOT NULL, nota REAL DEFAULT 0.00, resultado TEXT DEFAULT 'Pendente')")
    cursor.execute("CREATE TABLE IF NOT EXISTS mensagens_chat (id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER NOT NULL, remetente TEXT NOT NULL, conteudo TEXT NOT NULL, data_envio TEXT NOT NULL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS certificados (id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER NOT NULL, curso_id INTEGER NOT NULL, codigo TEXT UNIQUE NOT NULL, arquivo TEXT NOT NULL, emitido_em TEXT NOT NULL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS visitas (id INTEGER PRIMARY KEY AUTOINCREMENT, visitante_hash TEXT NOT NULL, rota TEXT NOT NULL, inicio TEXT NOT NULL, ultimo_sinal TEXT NOT NULL, duracao_segundos INTEGER DEFAULT 0)")
    cursor.execute("CREATE TABLE IF NOT EXISTS configuracoes (chave TEXT PRIMARY KEY, valor TEXT NOT NULL DEFAULT '')")
    cursor.execute("INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES ('whatsapp_numero', ?)", (WHATSAPP_NUMBER,))
    cursor.execute("INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES ('whatsapp_mensagem', ?)", (WHATSAPP_MESSAGE,))

    colunas_cursos = {coluna[1] for coluna in cursor.execute("PRAGMA table_info(cursos)").fetchall()}
    colunas_cursos_necessarias = {
        "video_apresentacao": "TEXT DEFAULT NULL",
        "pdf_url": "TEXT DEFAULT NULL",
        "icone": "TEXT DEFAULT '🎓'",
        "slug": "TEXT DEFAULT NULL",
    }
    for nome_coluna, definicao in colunas_cursos_necessarias.items():
        if nome_coluna not in colunas_cursos:
            cursor.execute(f"ALTER TABLE cursos ADD COLUMN {nome_coluna} {definicao}")
    cursor.execute("UPDATE usuarios SET foto = '/static/fotos/padrao.svg' WHERE foto IS NULL OR foto = '/static/fotos/padrao.png'")

    cursos_iniciais = [
        (1, "Gestão Comercial Primavera v10", "Controlo de stock e faturação no Primavera ERP.", 35000.00, "https://www.youtube.com/watch?v=ScMzIvxBSi4", "", "📦", "gestao-comercial"),
        (2, "Contabilidade", "Plano de contas angolano, lançamentos e balanços.", 30000.00, "https://www.youtube.com/watch?v=QH2-TGUlwu4", "", "📊", "contabilidade"),
        (3, "Gestão de Recursos Humanos", "Processamento de salários, IRT e Segurança Social.", 25000.00, "https://www.youtube.com/watch?v=RGOj5yH7evk", "", "👥", "rh"),
        (4, "Informática", "Fundamentos de redes e ferramentas de escritório office.", 20000.00, "https://www.youtube.com/watch?v=9iQ_7q7QmPI", "", "💻", "informatica")
    ]
    for c_id, nome, desc, preco, video, pdf_url, icone, slug in cursos_iniciais:
        cursor.execute("INSERT OR IGNORE INTO cursos (id, nome, descricao, preco, video_apresentacao, pdf_url, icone, slug) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (c_id, nome, desc, preco, video, pdf_url, icone, slug))

    senha_admin_hash = criptografar_senha("senha_admin_hash")
    email_admin_criptografado = criptografar_email("email_admin_criptografado")
    cursor.execute("""
        INSERT OR IGNORE INTO usuarios (id, nome, email, telefone, senha, pergunta_seguranca, resposta_seguranca, role, foto)
        VALUES (1, 'Admin ESAQUI', ?, '900000000', ?, 'Animal', 'Rex', 'admin', '/static/fotos/padrao.svg')
    """, (email_admin_criptografado, senha_admin_hash))

    senha_prof_hash = criptografar_senha("senha_prof_hash")
    email_prof_criptografado = criptografar_email(" email_prof_criptografado")
    cursor.execute("""
        INSERT OR IGNORE INTO usuarios (id, nome, email, telefone, senha, pergunta_seguranca, resposta_seguranca, role, foto)
        VALUES (2, 'Professor Primavera', ?, '911111111', ?, 'Escola', 'Puniv', 'professor', '/static/fotos/padrao.svg')
    """, (email_prof_criptografado, senha_prof_hash))
    conn.commit()
    conn.close()

init_db()

@app.post("/assistente-bot")
def responder_bot(mensagem: str = Form(...)):
    msg = mensagem.lower().strip()
    if not msg:
        return {"resposta": "Olá! Como posso ajudar hoje?"}

    if "primavera" in msg or "v10" in msg:
        return {"resposta": "O Curso de Gestão Comercial Primavera v10 abrange faturação, gestão de stocks, controlo comercial e operação de ERP."}
    if "pagar" in msg or "pagamento" in msg or "iban" in msg or "express" in msg:
        return {"resposta": "Os pagamentos podem ser feitos por Multicaixa Express: 923 000 000 ou por IBAN indicado no site. Depois do comprovativo, a sua matrícula é validada."}
    if "certificado" in msg or "diploma" in msg:
        return {"resposta": "Após aprovação final, emitimos certificado digital do curso com apoio do ambiente académico da ESAQUI."}

    pesquisa = buscar_web_snippets(msg)
    if pesquisa:
        resposta = "Informação relevante para o tema: " + " | ".join(pesquisa)
        return {"resposta": resposta}

    return {"resposta": "Olá! Sou o Assistente ESAQUI. Posso apoiar em matrículas, cursos, pagamentos, certificados e materiais de estudo."}


@app.get("/", response_class=HTMLResponse)
def pagina_inicial(request: Request):
    conn = sqlite3.connect("esaqui.db")
    conn.row_factory = sqlite3.Row
    cursos = conn.cursor().execute("SELECT * FROM cursos ORDER BY id").fetchall()
    conn.close()
    return templates.TemplateResponse(request, "index.html", context={"cursos": cursos})


@app.get("/curso/{curso_id}", response_class=HTMLResponse)
def curso_detalhe(request: Request, curso_id: int):
    conn = sqlite3.connect("esaqui.db")
    conn.row_factory = sqlite3.Row
    curso = conn.cursor().execute("SELECT * FROM cursos WHERE id = ?", (curso_id,)).fetchone()
    conn.close()
    if not curso:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(request, "curso.html", context={"curso": curso})


@app.get("/cadastro", response_class=HTMLResponse)
def tela_cadastro(request: Request):
    conn = sqlite3.connect("esaqui.db")
    conn.row_factory = sqlite3.Row
    cursos = conn.cursor().execute("SELECT * FROM cursos").fetchall()
    conn.close()
    return templates.TemplateResponse(request, "cadastro.html", context={"erro": None, "cursos": cursos})


@app.get("/baixar-app")
def pagina_baixar_app(request: Request):
    package_path = os.path.join(BASE_DIR, "static", "ESAQUI-App.apk")
    os.makedirs(os.path.dirname(package_path), exist_ok=True)
    if not os.path.exists(package_path):
        with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as apk:
            apk.writestr("manifest.json", '{"name": "ESAQUI App", "version": "1.0.0", "type": "release"}')
            apk.writestr("README.txt", "ESAQUI - pacote de distribuição para download oficial\nAcesso: https://esaqui-plataforma.onrender.com/login\n")
    return FileResponse(
        package_path,
        filename="ESAQUI-App.apk",
        media_type="application/vnd.android.package-archive",
        headers={"Content-Disposition": "attachment; filename=ESAQUI-App.apk"},
    )


@app.post("/cadastro")
def processar_cadastro(request: Request, nome: str = Form(...), email: str = Form(...), telefone: str = Form(...), senha: str = Form(...), curso_id: int = Form(...), pergunta: str = Form(...), resposta: str = Form(...)):
    email = normalizar_email(email)
    telefone = telefone.strip()
    if len(senha) < 8:
        return templates.TemplateResponse(request, "cadastro.html", context={"erro": "Mínimo de 8 caracteres na senha!", "cursos": []})
    if not email or "@" not in email:
        return templates.TemplateResponse(request, "cadastro.html", context={"erro": "E-mail inválido!", "cursos": []})

    senha_segura = criptografar_senha(senha)
    email_criptografado = criptografar_email(email)
    try:
        conn = sqlite3.connect("esaqui.db")
        conn.row_factory = sqlite3.Row
        if buscar_usuario_por_email(conn, email):
            conn.close()
            return templates.TemplateResponse(request, "cadastro.html", context={"erro": "E-mail já cadastrado!", "cursos": []})
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (nome, email, telefone, senha, pergunta_seguranca, resposta_seguranca) VALUES (?, ?, ?, ?, ?, ?)", (nome.strip(), email_criptografado, telefone, senha_segura, pergunta.strip(), resposta.lower().strip()))
        aluno_id = cursor.lastrowid
        cursor.execute("INSERT INTO matriculas (aluno_id, curso_id) VALUES (?, ?)", (aluno_id, curso_id))
        conn.commit()
        conn.close()
        return RedirectResponse(url="/login", status_code=302)
    except sqlite3.IntegrityError:
        return templates.TemplateResponse(request, "cadastro.html", context={"erro": "E-mail já cadastrado!", "cursos": []})


@app.get("/login", response_class=HTMLResponse)
def tela_login(request: Request):
    return templates.TemplateResponse(request, "login.html", context={"erro": None})


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


@app.post("/login")
def processar_login(request: Request, email: str = Form(...), senha: str = Form(...)):
    email = normalizar_email(email)
    conn = sqlite3.connect("esaqui.db")
    conn.row_factory = sqlite3.Row
    usuario = buscar_usuario_por_email(conn, email)
    conn.close()
    if usuario and verificar_senha(senha, usuario["senha"]):
        request.session["usuario"] = {"id": usuario["id"], "nome": usuario["nome"], "role": usuario["role"], "email": email}
        if usuario["role"] == "admin":
            return RedirectResponse(url="/admin", status_code=302)
        if usuario["role"] == "professor":
            return RedirectResponse(url=f"/dashboard-professor?professor_id={usuario['id']}", status_code=302)
        return RedirectResponse(url=f"/dashboard?aluno_id={usuario['id']}", status_code=302)
    return templates.TemplateResponse(request, "login.html", context={"erro": "Credenciais inválidas!"})


@app.get("/dashboard", response_class=HTMLResponse)
def area_aluno(request: Request, aluno_id: int):
    usuario = exigir_login(request, {"aluno"})
    if not usuario:
        return RedirectResponse(url="/login", status_code=302)
    if usuario["id"] != aluno_id:
        return RedirectResponse(url=f"/dashboard?aluno_id={usuario['id']}", status_code=302)

    conn = sqlite3.connect("esaqui.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    dados = cursor.execute("SELECT c.id as curso_id, c.nome as curso_nome, c.pdf_url as pdf_url, c.video_apresentacao, m.status_pagamento FROM matriculas m JOIN cursos c ON m.curso_id = c.id WHERE m.aluno_id = ?", (aluno_id,)).fetchone()
    nota_aluno = cursor.execute("SELECT * FROM notas WHERE aluno_id = ?", (aluno_id,)).fetchone()
    status_pago = dados["status_pagamento"] if dados else "Não Enviado"
    aulas_cadastradas = []
    if status_pago != "Não Enviado" and dados:
        aulas_cadastradas = cursor.execute("SELECT * FROM aulas WHERE curso_id = ?", (dados["curso_id"],)).fetchall()
    conn.close()
    return templates.TemplateResponse(request, "dashboard.html", context={
        "aluno_id": aluno_id,
        "aulas": aulas_cadastradas,
        "curso_nome": dados["curso_nome"] if dados else "Nenhum",
        "status_pagamento": status_pago,
        "nota": nota_aluno,
        "curso_pdf": dados["pdf_url"] if dados else None,
        "curso_video": dados["video_apresentacao"] if dados else None,
    })


@app.get("/recuperar", response_class=HTMLResponse)
def tela_recuperar(request: Request):
    return templates.TemplateResponse(request, "recuperar.html", context={"erro": None, "sucesso": None})


@app.post("/recuperar")
def processar_recuperar(request: Request, identificador: str = Form(...), resposta: str = Form(...), nova_senha: str = Form(...)):
    if len(nova_senha) < 8:
        return templates.TemplateResponse(request, "recuperar.html", context={"erro": "A nova senha precisa de 8 ou mais caracteres!", "sucesso": None})

    conn = sqlite3.connect("esaqui.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    identificador = identificador.strip()
    usuario = None
    if "@" in identificador:
        usuario = buscar_usuario_por_email(conn, identificador)
    if not usuario:
        usuario = cursor.execute("SELECT * FROM usuarios WHERE telefone = ?", (identificador,)).fetchone()

    if usuario and usuario["resposta_seguranca"] == resposta.lower().strip():
        nova_senha_hash = criptografar_senha(nova_senha)
        cursor.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (nova_senha_hash, usuario["id"]))
        conn.commit()
        conn.close()
        return templates.TemplateResponse(request, "recuperar.html", context={"erro": None, "sucesso": "Sua palavra-passe foi atualizada com sucesso!"})

    conn.close()
    return templates.TemplateResponse(request, "recuperar.html", context={"erro": "Identificador (E-mail/Telefone) ou resposta secreta incorretos!", "sucesso": None})


@app.get("/admin", response_class=HTMLResponse)
def painel_admin(request: Request):
    usuario = exigir_login(request, {"admin"})
    if not usuario:
        return RedirectResponse(url="/login", status_code=302)

    conn = sqlite3.connect("esaqui.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    whatsapp_numero = carregar_configuracao("whatsapp_numero", WHATSAPP_NUMBER)
    whatsapp_mensagem = carregar_configuracao("whatsapp_mensagem", WHATSAPP_MESSAGE)

    alunos = cursor.execute("""
        SELECT u.id, u.nome, u.telefone, c.nome as curso_nome, m.comprovativo, m.status_pagamento
        FROM usuarios u
        JOIN matriculas m ON u.id = m.aluno_id
        JOIN cursos c ON m.curso_id = c.id
        WHERE u.role = 'aluno'
    """).fetchall()
    todos_cursos = cursor.execute("SELECT * FROM cursos ORDER BY id").fetchall()

    faturado = cursor.execute(
        "SELECT SUM(c.preco) FROM matriculas m JOIN cursos c ON m.curso_id = c.id WHERE m.status_pagamento = 'Aprovado'"
    ).fetchone()[0] or 0.0
    pendente = cursor.execute(
        "SELECT SUM(c.preco) FROM matriculas m JOIN cursos c ON m.curso_id = c.id WHERE m.status_pagamento = 'Pendente'"
    ).fetchone()[0] or 0.0

    total_geral = faturado + pendente
    pct_faturado = (faturado / total_geral * 100) if total_geral > 0 else 0
    pct_pendente = (pendente / total_geral * 100) if total_geral > 0 else 0

    conn.close()
    return templates.TemplateResponse(request, "admin.html", context={
        "alunos": alunos,
        "cursos": todos_cursos,
        "faturado": faturado,
        "pendente": pendente,
        "pct_faturado": pct_faturado,
        "pct_pendente": pct_pendente,
        "whatsapp_numero": whatsapp_numero,
        "whatsapp_mensagem": whatsapp_mensagem,
    })


@app.get("/admin/decidir-pagamento")
def decidir_pagamento(request: Request, aluno_id: int, acao: str):
    if not exigir_login(request, {"admin"}):
        return RedirectResponse(url="/login", status_code=302)
    novo_status = "Aprovado" if acao == "aprovar" else "Rejeitado"
    conn = sqlite3.connect("esaqui.db")
    conn.cursor().execute("UPDATE matriculas SET status_pagamento = ? WHERE aluno_id = ?", (novo_status, aluno_id))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/admin", status_code=302)


@app.get("/chat-admin", response_class=HTMLResponse)
def carregar_chat_admin(request: Request, aluno_id: int):
    if not exigir_login(request, {"admin"}):
        return RedirectResponse(url="/login", status_code=302)
    conn = sqlite3.connect("esaqui.db")
    conn.row_factory = sqlite3.Row
    aluno = conn.cursor().execute("SELECT nome FROM usuarios WHERE id = ?", (aluno_id,)).fetchone()
    historico = conn.cursor().execute("SELECT * FROM mensagens_chat WHERE aluno_id = ? ORDER BY id ASC", (aluno_id,)).fetchall()
    conn.close()
    return templates.TemplateResponse(request, "chat_admin.html", context={"aluno_id": aluno_id, "aluno_nome": aluno["nome"], "historico": historico})


@app.post("/chat-admin/enviar")
def admin_enviar_mensagem(request: Request, aluno_id: int, conteudo: str = Form(...)):
    if not exigir_login(request, {"admin"}):
        return RedirectResponse(url="/login", status_code=302)
    if conteudo.strip():
        conn = sqlite3.connect("esaqui.db")
        conn.cursor().execute(
            "INSERT INTO mensagens_chat (aluno_id, remetente, conteudo, data_envio) VALUES (?, 'admin', ?, ?)",
            (aluno_id, conteudo.strip(), datetime.now().strftime("%H:%M")),
        )
        conn.commit()
        conn.close()
    return RedirectResponse(url=f"/chat-admin?aluno_id={aluno_id}", status_code=302)


@app.get("/assistencia-whatsapp")
def suporte_whatsapp(request: Request, numero: str = None, mensagem: str = None):
    telefone = (numero or request.query_params.get("numero") or carregar_configuracao("whatsapp_numero", WHATSAPP_NUMBER)).strip()
    texto = (mensagem or request.query_params.get("mensagem") or carregar_configuracao("whatsapp_mensagem", WHATSAPP_MESSAGE)).strip()
    return RedirectResponse(url=f"https://wa.me/{telefone}?text={quote_plus(texto)}", status_code=302)


@app.post("/admin/atualizar-whatsapp")
def atualizar_whatsapp_admin(request: Request, numero: str = Form(...), mensagem: str = Form(...)):
    if not exigir_login(request, {"admin"}):
        return RedirectResponse(url="/login", status_code=302)
    guardar_configuracao("whatsapp_numero", numero)
    guardar_configuracao("whatsapp_mensagem", mensagem)
    return RedirectResponse(url="/admin", status_code=302)


@app.get("/admin/exportar-financeiro")
def exportar_excel_caixa(request: Request):
    if not exigir_login(request, {"admin"}):
        return RedirectResponse(url="/login", status_code=302)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Caixa"
    ws.append(["ID", "Nome", "Contacto", "Curso", "Preço", "Estado"])
    conn = sqlite3.connect("esaqui.db")
    conn.row_factory = sqlite3.Row
    registos = conn.cursor().execute(
        "SELECT m.id, u.nome, u.telefone, c.nome as curso_nome, c.preco, m.status_pagamento FROM matriculas m JOIN usuarios u ON m.aluno_id = u.id JOIN cursos c ON m.curso_id = c.id"
    ).fetchall()
    conn.close()
    for r in registos:
        ws.append([r["id"], r["nome"], r["telefone"], r["curso_nome"], r["preco"], r["status_pagamento"]])
    excel_filename = "Relatorio_Financeiro_ESAQUI.xlsx"
    wb.save(excel_filename)
    return FileResponse(excel_filename, filename=excel_filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.post("/admin/criar-curso")
async def criar_curso(request: Request, nome: str = Form(...), descricao: str = Form(...), preco: float = Form(...), video_apresentacao: str = Form(""), pdf_file: UploadFile = File(None), icone: str = Form("🎓")):
    if not exigir_login(request, {"admin"}):
        return RedirectResponse(url="/login", status_code=302)

    pdf_url = ""
    nome_pdf = salvar_upload(pdf_file, PDFS_DIR, {".pdf"})
    if nome_pdf:
        pdf_url = f"/pdfs/{nome_pdf}"

    conn = sqlite3.connect("esaqui.db")
    conn.cursor().execute(
        "INSERT INTO cursos (nome, descricao, preco, video_apresentacao, pdf_url, icone, slug) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (nome.strip(), descricao.strip(), preco, video_apresentacao.strip() or None, pdf_url or None, icone.strip() or "🎓", nome.strip().lower().replace(" ", "-"))
    )
    conn.commit()
    conn.close()
    return RedirectResponse(url="/admin", status_code=302)


@app.post("/admin/upload-video")
async def admin_upload_video(
    request: Request,
    curso_id: int = Form(...),
    modulo: str = Form(...),
    titulo: str = Form(...),
    video_file: UploadFile = File(...),
):
    if not exigir_login(request, {"admin"}):
        return RedirectResponse(url="/login", status_code=302)
    clean_filename = salvar_upload(video_file, VIDEOS_DIR, {".mp4", ".webm", ".ogg", ".mov"})
    if not clean_filename:
        return RedirectResponse(url="/admin", status_code=302)

    conn = sqlite3.connect("esaqui.db")
    conn.cursor().execute(
        "INSERT INTO aulas (curso_id, modulo, titulo, url_video) VALUES (?, ?, ?, ?)",
        (curso_id, modulo, titulo, f"/static/videos/{clean_filename}"),
    )
    conn.commit()
    conn.close()
    return RedirectResponse(url="/admin", status_code=302)


@app.get("/chat-aluno", response_class=HTMLResponse)
def carregar_chat_aluno(request: Request, aluno_id: int):
    usuario = exigir_login(request, {"aluno"})
    if not usuario or usuario["id"] != aluno_id:
        return RedirectResponse(url="/login", status_code=302)
    conn = sqlite3.connect("esaqui.db")
    conn.row_factory = sqlite3.Row
    historico = conn.cursor().execute(
        "SELECT * FROM mensagens_chat WHERE aluno_id = ? ORDER BY id ASC", (aluno_id,)
    ).fetchall()
    conn.close()
    return templates.TemplateResponse(request, "chat_aluno.html", context={
        "aluno_id": aluno_id,
        "historico": historico,
    })


@app.post("/chat-aluno/enviar")
def aluno_enviar_mensagem(request: Request, aluno_id: int, conteudo: str = Form(...)):
    usuario = exigir_login(request, {"aluno"})
    if not usuario or usuario["id"] != aluno_id:
        return RedirectResponse(url="/login", status_code=302)
    if conteudo.strip():
        conn = sqlite3.connect("esaqui.db")
        conn.cursor().execute(
            "INSERT INTO mensagens_chat (aluno_id, remetente, conteudo, data_envio) VALUES (?, 'aluno', ?, ?)",
            (aluno_id, conteudo.strip(), datetime.now().strftime("%H:%M")),
        )
        conn.commit()
        conn.close()
    return RedirectResponse(url=f"/chat-aluno?aluno_id={aluno_id}", status_code=302)


@app.get("/perfil-aluno", response_class=HTMLResponse)
def perfil_aluno(request: Request, aluno_id: int):
    usuario = exigir_login(request, {"aluno"})
    if not usuario or usuario["id"] != aluno_id:
        return RedirectResponse(url="/login", status_code=302)
    conn = sqlite3.connect("esaqui.db")
    conn.row_factory = sqlite3.Row
    aluno = conn.cursor().execute("SELECT * FROM usuarios WHERE id = ? AND role = 'aluno'", (aluno_id,)).fetchone()
    conn.close()
    if not aluno:
        return RedirectResponse(url="/login", status_code=302)
    dados = dict(aluno)
    dados["email"] = descriptografar_email(dados["email"]) or dados["email"]
    return templates.TemplateResponse(request, "perfil_aluno.html", context={"aluno": dados, "sucesso": None})


@app.post("/perfil-aluno/atualizar")
async def atualizar_perfil_aluno(
    request: Request,
    aluno_id: int,
    nome: str = Form(...),
    telefone: str = Form(...),
    email: str = Form(...),
    foto_file: UploadFile = File(None),
):
    usuario = exigir_login(request, {"aluno"})
    if not usuario or usuario["id"] != aluno_id:
        return RedirectResponse(url="/login", status_code=302)
    nome = nome.strip()
    telefone = telefone.strip()
    email = normalizar_email(email)
    if not nome or not telefone or "@" not in email:
        return RedirectResponse(url=f"/perfil-aluno?aluno_id={aluno_id}", status_code=302)

    conn = sqlite3.connect("esaqui.db")
    conn.row_factory = sqlite3.Row
    outro_usuario = buscar_usuario_por_email(conn, email)
    if outro_usuario and outro_usuario["id"] != aluno_id:
        conn.close()
        return RedirectResponse(url=f"/perfil-aluno?aluno_id={aluno_id}", status_code=302)
    foto = salvar_upload(foto_file, FOTOS_DIR, {".jpg", ".jpeg", ".png", ".webp"})
    campos = ["nome = ?", "telefone = ?", "email = ?"]
    valores = [nome, telefone, criptografar_email(email)]
    if foto:
        campos.append("foto = ?")
        valores.append(f"/static/fotos/{foto}")
    valores.append(aluno_id)
    conn.execute(f"UPDATE usuarios SET {', '.join(campos)} WHERE id = ?", valores)
    conn.commit()
    conn.close()
    request.session["usuario"]["email"] = email
    return RedirectResponse(url=f"/perfil-aluno?aluno_id={aluno_id}", status_code=302)


@app.post("/upload-comprovativo")
async def upload_comprovativo(
    request: Request,
    aluno_id: int,
    file: UploadFile = File(...),
):
    usuario = exigir_login(request, {"aluno"})
    if not usuario or usuario["id"] != aluno_id:
        return RedirectResponse(url="/login", status_code=302)
    nome_arquivo = salvar_upload(file, UPLOAD_DIR, {".jpg", ".jpeg", ".png", ".pdf", ".webp"})
    if nome_arquivo:
        conn = sqlite3.connect("esaqui.db")
        conn.execute(
            "UPDATE matriculas SET comprovativo = ?, status_pagamento = 'Pendente' WHERE aluno_id = ?",
            (f"/comprovativos/{nome_arquivo}", aluno_id),
        )
        conn.commit()
        conn.close()
    return RedirectResponse(url=f"/dashboard?aluno_id={aluno_id}", status_code=302)


@app.get("/dashboard-professor", response_class=HTMLResponse)
def dashboard_professor(request: Request, professor_id: int):
    usuario = exigir_login(request, {"professor"})
    if not usuario or usuario["id"] != professor_id:
        return RedirectResponse(url="/login", status_code=302)
    conn = sqlite3.connect("esaqui.db")
    conn.row_factory = sqlite3.Row
    professor = conn.cursor().execute(
        "SELECT * FROM usuarios WHERE id = ? AND role = 'professor'", (professor_id,)
    ).fetchone()
    alunos = conn.cursor().execute(
        """SELECT u.nome, u.telefone, n.nota, n.resultado
           FROM usuarios u
           JOIN matriculas m ON m.aluno_id = u.id
           LEFT JOIN notas n ON n.aluno_id = u.id
           WHERE u.role = 'aluno'
           ORDER BY u.nome"""
    ).fetchall()
    conn.close()
    if not professor:
        return RedirectResponse(url="/login", status_code=302)
    dados = dict(professor)
    dados["email"] = descriptografar_email(dados["email"]) or dados["email"]
    return templates.TemplateResponse(request, "dashboard_professor.html", context={
        "professor": dados,
        "alunos": alunos,
    })


@app.post("/perfil-professor/atualizar")
async def atualizar_perfil_professor(
    request: Request,
    professor_id: int,
    nome: str = Form(...),
    telefone: str = Form(...),
    foto_file: UploadFile = File(None),
):
    usuario = exigir_login(request, {"professor"})
    if not usuario or usuario["id"] != professor_id:
        return RedirectResponse(url="/login", status_code=302)
    foto = salvar_upload(foto_file, FOTOS_DIR, {".jpg", ".jpeg", ".png", ".webp"})
    campos = ["nome = ?", "telefone = ?"]
    valores = [nome.strip(), telefone.strip()]
    if foto:
        campos.append("foto = ?")
        valores.append(f"/static/fotos/{foto}")
    valores.append(professor_id)
    conn = sqlite3.connect("esaqui.db")
    conn.execute(f"UPDATE usuarios SET {', '.join(campos)} WHERE id = ?", valores)
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/dashboard-professor?professor_id={professor_id}", status_code=302)


PERGUNTAS_PROVA = [
    {"id": 1, "texto": "Qual é a principal função de um sistema ERP?", "a": "Integrar processos de gestão", "b": "Editar fotografias", "c": "Criar redes sociais", "correta": "a"},
    {"id": 2, "texto": "O que representa o stock numa empresa?", "a": "Apenas o dinheiro em caixa", "b": "Os bens disponíveis para operação ou venda", "c": "A lista de funcionários", "correta": "b"},
    {"id": 3, "texto": "Qual prática ajuda a proteger uma conta?", "a": "Partilhar a senha", "b": "Usar a mesma senha em tudo", "c": "Usar uma senha forte e exclusiva", "correta": "c"},
]


@app.get("/prova", response_class=HTMLResponse)
def tela_prova(request: Request, aluno_id: int):
    usuario = exigir_login(request, {"aluno"})
    if not usuario or usuario["id"] != aluno_id:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(request, "prova.html", context={
        "aluno_id": aluno_id,
        "perguntas": PERGUNTAS_PROVA,
    })


@app.post("/submeter-prova")
async def submeter_prova(request: Request, aluno_id: int):
    usuario = exigir_login(request, {"aluno"})
    if not usuario or usuario["id"] != aluno_id:
        return RedirectResponse(url="/login", status_code=302)
    formulario = await request.form()
    acertos = sum(1 for pergunta in PERGUNTAS_PROVA if formulario.get(f"q{pergunta['id']}") == pergunta["correta"])
    nota = round(acertos * 20 / len(PERGUNTAS_PROVA), 2)
    resultado = "Aprovado" if nota >= 10 else "Reprovado"
    conn = sqlite3.connect("esaqui.db")
    conn.execute("DELETE FROM notas WHERE aluno_id = ?", (aluno_id,))
    conn.execute("INSERT INTO notas (aluno_id, nota, resultado) VALUES (?, ?, ?)", (aluno_id, nota, resultado))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/dashboard?aluno_id={aluno_id}", status_code=302)


def emitir_certificado(conn, aluno_id: int):
    dados = conn.execute(
        """SELECT u.nome, c.id AS curso_id, c.nome AS curso_nome, n.nota
           FROM usuarios u
           JOIN matriculas m ON m.aluno_id = u.id
           JOIN cursos c ON c.id = m.curso_id
           JOIN notas n ON n.aluno_id = u.id
           WHERE u.id = ? AND m.status_pagamento = 'Aprovado' AND n.resultado = 'Aprovado'""",
        (aluno_id,),
    ).fetchone()
    if not dados:
        return None
    existente = conn.execute(
        "SELECT * FROM certificados WHERE aluno_id = ? AND curso_id = ?",
        (aluno_id, dados["curso_id"] if isinstance(dados, sqlite3.Row) else dados[1]),
    ).fetchone()
    if existente:
        return existente

    codigo = f"ESAQUI-{datetime.now().strftime('%Y%m')}-{secrets.token_hex(5).upper()}"
    arquivo = f"certificado_{aluno_id}_{codigo}.pdf"
    caminho = os.path.join(CERTIFICADOS_DIR, arquivo)
    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle("TituloCertificado", parent=estilos["Title"], alignment=TA_CENTER, fontSize=26, spaceAfter=28)
    centro = ParagraphStyle("CentroCertificado", parent=estilos["Normal"], alignment=TA_CENTER, fontSize=15, leading=24)
    documento = SimpleDocTemplate(caminho, pagesize=landscape(letter), leftMargin=70, rightMargin=70, topMargin=65, bottomMargin=65)
    nome = dados["nome"] if isinstance(dados, sqlite3.Row) else dados[0]
    curso_nome = dados["curso_nome"] if isinstance(dados, sqlite3.Row) else dados[2]
    nota = dados["nota"] if isinstance(dados, sqlite3.Row) else dados[3]
    documento.build([
        Paragraph("ESAQUI", titulo),
        Paragraph("CERTIFICADO DE CONCLUSÃO", titulo),
        Spacer(1, 18),
        Paragraph(f"Certificamos que <b>{nome}</b> concluiu a formação", centro),
        Paragraph(f"<b>{curso_nome}</b>", centro),
        Paragraph(f"com aproveitamento de {nota}/20.", centro),
        Spacer(1, 30),
        Paragraph(f"Código de verificação: {codigo}", centro),
        Paragraph(f"Emitido em {datetime.now().strftime('%d/%m/%Y')}", centro),
    ])
    emitido_em = datetime.now().isoformat(timespec="seconds")
    conn.execute(
        "INSERT INTO certificados (aluno_id, curso_id, codigo, arquivo, emitido_em) VALUES (?, ?, ?, ?, ?)",
        (aluno_id, dados["curso_id"] if isinstance(dados, sqlite3.Row) else dados[1], codigo, arquivo, emitido_em),
    )
    conn.commit()
    return conn.execute("SELECT * FROM certificados WHERE codigo = ?", (codigo,)).fetchone()


@app.get("/certificado/{codigo}")
def baixar_certificado(request: Request, codigo: str):
    usuario = exigir_login(request)
    if not usuario:
        return RedirectResponse(url="/login", status_code=302)
    conn = sqlite3.connect("esaqui.db")
    conn.row_factory = sqlite3.Row
    certificado = conn.execute("SELECT * FROM certificados WHERE codigo = ?", (codigo,)).fetchone()
    permitido = certificado and (usuario["role"] == "admin" or certificado["aluno_id"] == usuario["id"])
    conn.close()
    if not permitido:
        raise HTTPException(status_code=404, detail="Certificado não encontrado")
    caminho = os.path.join(CERTIFICADOS_DIR, certificado["arquivo"])
    if not os.path.isfile(caminho):
        raise HTTPException(status_code=404, detail="Arquivo do certificado não encontrado")
    return FileResponse(caminho, filename=certificado["arquivo"], media_type="application/pdf")


@app.get("/certificado/emitir/{aluno_id}")
def gerar_certificado(request: Request, aluno_id: int):
    usuario = exigir_login(request, {"aluno", "admin"})
    if not usuario or (usuario["role"] == "aluno" and usuario["id"] != aluno_id):
        return RedirectResponse(url="/login", status_code=302)
    conn = sqlite3.connect("esaqui.db")
    conn.row_factory = sqlite3.Row
    certificado = emitir_certificado(conn, aluno_id)
    conn.close()
    if not certificado:
        return RedirectResponse(url=f"/dashboard?aluno_id={aluno_id}", status_code=302)
    return RedirectResponse(url=f"/certificado/{certificado['codigo']}", status_code=302)


@app.post("/analytics/heartbeat")
def analytics_heartbeat(request: Request, duracao_segundos: int = Form(...)):
    visitante = request.session.get("visitante_id")
    if not visitante:
        visitante = secrets.token_hex(16)
        request.session["visitante_id"] = visitante
    duracao = max(0, min(duracao_segundos, 86400))
    conn = sqlite3.connect("esaqui.db")
    conn.execute(
        "UPDATE visitas SET duracao_segundos = ?, ultimo_sinal = ? WHERE id = (SELECT id FROM visitas WHERE visitante_hash = ? ORDER BY id DESC LIMIT 1)",
        (duracao, datetime.now().isoformat(timespec="seconds"), hash_visitante(visitante)),
    )
    conn.commit()
    conn.close()
    return JSONResponse({"ok": True})


@app.get("/admin/engajamento", response_class=HTMLResponse)
def painel_engajamento(request: Request):
    if not exigir_login(request, {"admin"}):
        return RedirectResponse(url="/login", status_code=302)
    conn = sqlite3.connect("esaqui.db")
    conn.row_factory = sqlite3.Row
    resumo = conn.execute(
        """SELECT COUNT(*) AS visitas, COUNT(DISTINCT visitante_hash) AS visitantes,
                  COALESCE(AVG(duracao_segundos), 0) AS media_segundos,
                  COALESCE(SUM(duracao_segundos), 0) AS total_segundos
           FROM visitas"""
    ).fetchone()
    rotas = conn.execute(
        "SELECT rota, COUNT(*) AS total FROM visitas GROUP BY rota ORDER BY total DESC LIMIT 10"
    ).fetchall()
    conn.close()
    financeiro = calcular_resumo_financeiro()
    return templates.TemplateResponse(request, "engajamento.html", context={
        "resumo": resumo,
        "rotas": rotas,
        "financeiro": financeiro,
    })


@app.get("/admin/contas-digitais", response_class=HTMLResponse)
def contas_digitais_admin(request: Request):
    if not exigir_login(request, {"admin"}):
        return RedirectResponse(url="/login", status_code=302)
    financeiro = calcular_resumo_financeiro()
    return templates.TemplateResponse(request, "contas_digitais.html", context={
        "bybit_account": BYBIT_ACCOUNT or "Não configurada",
        "airtm_account": AIRM_ACCOUNT or "Não configurada",
        "financeiro": financeiro,
    })