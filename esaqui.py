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
from datetime import datetime
import openpyxl
import bcrypt
from cryptography.fernet import Fernet
from urllib.request import Request, urlopen
from urllib.parse import quote_plus
import re
import html as html_lib

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

app = FastAPI(title="ESAQUI - Sistema Automatizado")
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("ESAQUI_SECRET_KEY", "ESAQUI-SECRET-CHANGE-ME-2026-SECURE-KEY"), max_age=3600, same_site="lax", https_only=False)

WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "244923000000")
WHATSAPP_MESSAGE = os.environ.get("WHATSAPP_MESSAGE", "Olá, gostaria de assistência remota da ESAQUI.")
FACEBOOK_URL = os.environ.get("FACEBOOK_URL", "https://facebook.com/esaqui")
INSTAGRAM_URL = os.environ.get("INSTAGRAM_URL", "https://instagram.com/esaqui")
TIKTOK_URL = os.environ.get("TIKTOK_URL", "https://www.tiktok.com/@esaqui")
APP_STORE_URL = os.environ.get("APP_STORE_URL", "https://apps.microsoft.com")
GOOGLE_PLAY_URL = os.environ.get("GOOGLE_PLAY_URL", "https://play.google.com")

app.mount("/static", StaticFiles(directory="static"), name="static")
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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


def buscar_web_snippets(consulta: str, limite: int = 3):
    termo = (consulta or "").strip()
    if not termo:
        return []
    url = "https://duckduckgo.com/html/?q=" + quote_plus(termo + " curso formação tecnologia")
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
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
            resposta_seguranca TEXT NOT NULL, role TEXT DEFAULT 'aluno', foto TEXT DEFAULT '/static/fotos/padrao.png'
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

    cursos_iniciais = [
        (1, "Gestão Comercial Primavera v10", "Controlo de stock e faturação no Primavera ERP.", 35000.00, "https://www.youtube.com/watch?v=ScMzIvxBSi4", "", "📦", "gestao-comercial"),
        (2, "Contabilidade", "Plano de contas angolano, lançamentos e balanços.", 30000.00, "https://www.youtube.com/watch?v=QH2-TGUlwu4", "", "📊", "contabilidade"),
        (3, "Gestão de Recursos Humanos", "Processamento de salários, IRT e Segurança Social.", 25000.00, "https://www.youtube.com/watch?v=RGOj5yH7evk", "", "👥", "rh"),
        (4, "Informática", "Fundamentos de redes e ferramentas de escritório office.", 20000.00, "https://www.youtube.com/watch?v=9iQ_7q7QmPI", "", "💻", "informatica")
    ]
    for c_id, nome, desc, preco, video, pdf_url, icone, slug in cursos_iniciais:
        cursor.execute("INSERT OR IGNORE INTO cursos (id, nome, descricao, preco, video_apresentacao, pdf_url, icone, slug) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (c_id, nome, desc, preco, video, pdf_url, icone, slug))

    senha_admin_hash = criptografar_senha("Admin12345")
    email_admin_criptografado = criptografar_email("admin@esaqui.com")
    cursor.execute("""
        INSERT OR IGNORE INTO usuarios (id, nome, email, telefone, senha, pergunta_seguranca, resposta_seguranca, role, foto)
        VALUES (1, 'Admin ESAQUI', ?, '900000000', ?, 'Animal', 'Rex', 'admin', '/static/fotos/padrao.png')
    """, (email_admin_criptografado, senha_admin_hash))

    senha_prof_hash = criptografar_senha("Prof12345")
    email_prof_criptografado = criptografar_email("professor@esaqui.com")
    cursor.execute("""
        INSERT OR IGNORE INTO usuarios (id, nome, email, telefone, senha, pergunta_seguranca, resposta_seguranca, role, foto)
        VALUES (2, 'Professor Primavera', ?, '911111111', ?, 'Escola', 'Puniv', 'professor', '/static/fotos/padrao.png')
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
    return templates.TemplateResponse(request, "index.html", context={
        "cursos": [],
        "download_focus": True,
        "facebook_url": FACEBOOK_URL,
        "instagram_url": INSTAGRAM_URL,
        "tiktok_url": TIKTOK_URL,
        "microsoft_store_url": APP_STORE_URL,
        "google_play_url": GOOGLE_PLAY_URL,
    })


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
    telefone = (numero or request.query_params.get("numero") or WHATSAPP_NUMBER).strip()
    texto = (mensagem or request.query_params.get("mensagem") or WHATSAPP_MESSAGE).strip()
    return RedirectResponse(url=f"https://wa.me/{telefone}?text={quote_plus(texto)}", status_code=302)

app.add_api_route("/assistencia-whatsapp", suporte_whatsapp, methods=["GET"], include_in_schema=False)


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
    if pdf_file and pdf_file.filename:
        nome_pdf = f"curso_{datetime.now().strftime('%Y%m%d%H%M%S')}_{pdf_file.filename.replace(' ', '_')}"
        caminho_pdf = os.path.join(PDFS_DIR, nome_pdf)
        with open(caminho_pdf, "wb") as buffer:
            shutil.copyfileobj(pdf_file.file, buffer)
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
    clean_filename = f"curso_{curso_id}_{video_file.filename.replace(' ', '')}"
    video_path = os.path.join(VIDEOS_DIR, clean_filename)
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(video_file.file, buffer)

    conn = sqlite3.connect("esaqui.db")
    conn.cursor().execute(
        "INSERT INTO aulas (curso_id, modulo, titulo, url_video) VALUES (?, ?, ?, ?)",
        (curso_id, modulo, titulo, f"/static/videos/{clean_filename}"),
    )
    conn.commit()
    conn.close()
    return RedirectResponse(url="/admin", status_code=302)