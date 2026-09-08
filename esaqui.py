from fastapi import FastAPI, Request, Form, UploadFile, File, status
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3
import os
import shutil
from datetime import datetime
import openpyxl
import bcrypt

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

app = FastAPI(title="ESAQUI - Sistema Automatizado")

app.mount("/static", StaticFiles(directory="static"), name="static")
UPLOAD_DIR = "comprovativos"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/comprovativos", StaticFiles(directory=UPLOAD_DIR), name="comprovativos")

VIDEOS_DIR = os.path.join("static", "videos")
CERTIFICADOS_DIR = "certificados"
FOTOS_DIR = os.path.join("static", "fotos")

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(CERTIFICADOS_DIR, exist_ok=True)
os.makedirs(FOTOS_DIR, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
templates.env.cache = None

def criptografar_senha(senha_pura: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(senha_pura.encode('utf-8'), salt).decode('utf-8')

def verificar_senha(senha_pura: str, senha_criptografada: str) -> bool:
    try: return bcrypt.checkpw(senha_pura.encode('utf-8'), senha_criptografada.encode('utf-8'))
    except Exception: return False

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
    cursor.execute("CREATE TABLE IF NOT EXISTS cursos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE NOT NULL, descricao TEXT NOT NULL, preco REAL DEFAULT 25000.00)")
    
    # BANCO DE DADOS AUTOMATIZADO: Matriculas agora monitoram o caixa vinculado ao curso do aluno
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
        (1, "Gestão Comercial Primavera v10", "Controlo de stock e faturação no Primavera ERP.", 35000.00),
        (2, "Contabilidade", "Plano de contas angolano, lançamentos e balanços.", 30000.00),
        (3, "Gestão de Recursos Humanos", "Processamento de salários, IRT e Segurança Social.", 25000.00),
        (4, "Informática", "Fundamentos de redes e ferramentas de escritório office.", 20000.00)
    ]
    for c_id, nome, desc, preco in cursos_iniciais:
        cursor.execute("INSERT OR IGNORE INTO cursos (id, nome, descricao, preco) VALUES (?, ?, ?, ?)", (c_id, nome, desc, preco))
        
    senha_admin_hash = criptografar_senha("Admin12345")
    cursor.execute("""
        INSERT OR IGNORE INTO usuarios (id, nome, email, telefone, senha, pergunta_seguranca, resposta_seguranca, role, foto) 
        VALUES (1, 'Admin ESAQUI', 'admin@esaqui.com', '900000000', ?, 'Animal', 'Rex', 'admin', '/static/fotos/padrao.png')
    """, (senha_admin_hash,))
    
    senha_prof_hash = criptografar_senha("Prof12345")
    cursor.execute("""
        INSERT OR IGNORE INTO usuarios (id, nome, email, telefone, senha, pergunta_seguranca, resposta_seguranca, role, foto) 
        VALUES (2, 'Professor Primavera', 'professor@esaqui.com', '911111111', ?, 'Escola', 'Puniv', 'professor', '/static/fotos/padrao.png')
    """, (senha_prof_hash,))
    conn.commit()
    conn.close()

init_db()

# --- ASSISTENTE BOT ---
@app.post("/assistente-bot")
def responder_bot(mensagem: str = Form(...)):
    msg = mensagem.lower().strip()
    if "primavera" in msg or "v10" in msg: resposta = "O Curso de Primavera v10 aborda stocks e faturamento comercial."
    elif "pagar" in msg or "iban" in msg or "express" in msg: resposta = "Express para 923 000 000 ou IBAN AO06 0040 0000 1234 5678 1019 1."
    else: resposta = "Olá! Sou o Assistente da ESAQUI. Como posso ajudar com as instruções de formação?"
    return {"resposta": resposta}

# --- ROTAS FLUXO AUTOMÁTICO ---

@app.get("/", response_class=HTMLResponse)
def pagina_inicial(request: Request):
    conn = sqlite3.connect("esaqui.db")
    conn.row_factory = sqlite3.Row
    cursos = conn.cursor().execute("SELECT * FROM cursos").fetchall()
    conn.close()
    return templates.TemplateResponse(request, "index.html", context={"cursos": cursos})

@app.get("/cadastro", response_class=HTMLResponse)
def tela_cadastro(request: Request):
    conn = sqlite3.connect("esaqui.db")
    conn.row_factory = sqlite3.Row
    cursos = conn.cursor().execute("SELECT * FROM cursos").fetchall()
    conn.close()
    return templates.TemplateResponse(request, "cadastro.html", context={"erro": None, "cursos": cursos})

@app.post("/cadastro")
def processar_cadastro(request: Request, nome: str = Form(...), email: str = Form(...), telefone: str = Form(...), senha: str = Form(...), curso_id: int = Form(...), pergunta: str = Form(...), resposta: str = Form(...)):
    if len(senha) < 8: return templates.TemplateResponse(request, "cadastro.html", context={"erro": "Mínimo de 8 caracteres na senha!", "cursos": []})
    senha_segura = criptografar_senha(senha)
    try:
        conn = sqlite3.connect("esaqui.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (nome, email, telefone, senha, pergunta_seguranca, resposta_seguranca) VALUES (?, ?, ?, ?, ?, ?)", (nome, email, telefone, senha_segura, pergunta, resposta.lower().strip()))
        aluno_id = cursor.lastrowid
        cursor.execute("INSERT INTO matriculas (aluno_id, curso_id) VALUES (?, ?)", (aluno_id, curso_id))
        conn.commit()
        conn.close()
        return RedirectResponse(url="/login", status_code=302)
    except sqlite3.IntegrityError:
        return templates.TemplateResponse(request, "cadastro.html", context={"erro": "E-mail já cadastrado!", "cursos": []})

@app.get("/login", response_class=HTMLResponse)
def tela_login(request: Request): return templates.TemplateResponse(request, "login.html", context={"erro": None})

@app.post("/login")
def processar_login(request: Request, email: str = Form(...), senha: str = Form(...)):
    conn = sqlite3.connect("esaqui.db")
    conn.row_factory = sqlite3.Row
    usuario = conn.cursor().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    conn.close()
    if usuario and verificar_senha(senha, usuario["senha"]):
        if usuario["role"] == "admin": return RedirectResponse(url="/admin", status_code=302)
        if usuario["role"] == "professor": return RedirectResponse(url=f"/dashboard-professor?professor_id={usuario['id']}", status_code=302)
        return RedirectResponse(url=f"/dashboard?aluno_id={usuario['id']}", status_code=302)
    return templates.TemplateResponse(request, "login.html", context={"erro": "Credenciais inválidas!"})

@app.get("/dashboard", response_class=HTMLResponse)
def area_aluno(request: Request, aluno_id: int):
    conn = sqlite3.connect("esaqui.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    dados = cursor.execute("SELECT c.id as curso_id, c.nome as curso_nome, m.status_pagamento FROM matriculas m JOIN cursos c ON m.curso_id = c.id WHERE m.aluno_id = ?", (aluno_id,)).fetchone()
    nota_aluno = cursor.execute("SELECT * FROM notas WHERE aluno_id = ?", (aluno_id,)).fetchone()
    status_pago = dados["status_pagamento"] if dados else "Não Enviado"
    aulas_cadastradas = []
    if status_pago != "Não Enviado" and dados:
        aulas_cadastradas = cursor.execute("SELECT * FROM aulas WHERE curso_id = ?", (dados["curso_id"],)).fetchall()
    conn.close()
    return templates.TemplateResponse(request, "dashboard.html", context={"aluno_id": aluno_id, "aulas": aulas_cadastradas, "curso_nome": dados["curso_nome"] if dados else "Nenhum", "status_pagamento": status_pago, "nota": nota_aluno})

# AUTOMATIZAÇÃO DO UPLOAD: Altera o status para 'Pendente' e o gráfico do administrador capta o valor do curso na hora
# --- ROTAS DE RECUPERAÇÃO DE PALAVRA-PASSE SEGURA ---

@app.get("/recuperar", response_class=HTMLResponse)
def tela_recuperar(request: Request):
    # Entrega a página visual de recuperação para o navegador
    return templates.TemplateResponse(request, "recuperar.html", context={"erro": None, "sucesso": None})

@app.post("/recuperar")
def processar_recuperar(request: Request, identificador: str = Form(...), resposta: str = Form(...), nova_senha: str = Form(...)):
    if len(nova_senha) < 8: 
        return templates.TemplateResponse(request, "recuperar.html", context={"erro": "A nova senha precisa de 8 ou mais caracteres!", "sucesso": None})
    
    conn = sqlite3.connect("esaqui.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Procura o aluno pelo E-mail ou pelo Número de Telefone no banco de dados
    usuario = cursor.execute("SELECT * FROM usuarios WHERE email = ? OR telefone = ?", (identificador.strip(), identificador.strip())).fetchone()
    
    if usuario and usuario["resposta_seguranca"] == resposta.lower().strip():
        # Criptografa a nova senha com Bcrypt antes de salvar por segurança máxima
        nova_senha_hash = criptografar_senha(nova_senha)
        cursor.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (nova_senha_hash, usuario["id"]))
        conn.commit()
        conn.close()
        return templates.TemplateResponse(request, "recuperar.html", context={"erro": None, "sucesso": "Sua palavra-passe foi atualizada com sucesso!"})
        
    conn.close()
    return templates.TemplateResponse(request, "recuperar.html", context={"erro": "Identificador (E-mail/Telefone) ou resposta secreta incorretos!", "sucesso": None})

# --- RESTRITO ADMINISTRADOR COM CÁLCULO TOTAL MATEMÁTICO AUTOMÁTICO ---

@app.get("/admin", response_class=HTMLResponse)
def painel_admin(request: Request):
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
    todos_cursos = cursor.execute("SELECT * FROM cursos").fetchall()

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
    return templates.TemplateResponse(
        request,
        "admin.html",
        context={
            "alunos": alunos,
            "cursos": todos_cursos,
            "faturado": faturado,
            "pendente": pendente,
            "pct_faturado": pct_faturado,
            "pct_pendente": pct_pendente,
        },
    )


@app.get("/admin/decidir-pagamento")
def decidir_pagamento(aluno_id: int, acao: str):
    novo_status = "Aprovado" if acao == "aprovar" else "Rejeitado"
    conn = sqlite3.connect("esaqui.db")
    conn.cursor().execute("UPDATE matriculas SET status_pagamento = ? WHERE aluno_id = ?", (novo_status, aluno_id))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/admin", status_code=302)


@app.get("/chat-admin", response_class=HTMLResponse)
def carregar_chat_admin(request: Request, aluno_id: int):
    conn = sqlite3.connect("esaqui.db")
    conn.row_factory = sqlite3.Row
    aluno = conn.cursor().execute("SELECT nome FROM usuarios WHERE id = ?", (aluno_id,)).fetchone()
    historico = conn.cursor().execute("SELECT * FROM mensagens_chat WHERE aluno_id = ? ORDER BY id ASC", (aluno_id,)).fetchall()
    conn.close()
    return templates.TemplateResponse(request, "chat_admin.html", context={"aluno_id": aluno_id, "aluno_nome": aluno["nome"], "historico": historico})


@app.post("/chat-admin/enviar")
def admin_enviar_mensagem(aluno_id: int, conteudo: str = Form(...)):
    if conteudo.strip():
        conn = sqlite3.connect("esaqui.db")
        conn.cursor().execute(
            "INSERT INTO mensagens_chat (aluno_id, remetente, conteudo, data_envio) VALUES (?, 'admin', ?, ?)",
            (aluno_id, conteudo.strip(), datetime.now().strftime("%H:%M")),
        )
        conn.commit()
        conn.close()
    return RedirectResponse(url=f"/chat-admin?aluno_id={aluno_id}", status_code=302)


@app.get("/admin/exportar-financeiro")
def exportar_excel_caixa():
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
def criar_curso(nome: str = Form(...), descricao: str = Form(...), preco: float = Form(...)):
    conn = sqlite3.connect("esaqui.db")
    conn.cursor().execute("INSERT INTO cursos (nome, descricao, preco) VALUES (?, ?, ?)", (nome.strip(), descricao.strip(), preco))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/admin", status_code=302)


@app.post("/admin/upload-video")
async def admin_upload_video(
    curso_id: int = Form(...),
    modulo: str = Form(...),
    titulo: str = Form(...),
    video_file: UploadFile = File(...),
):
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