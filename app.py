import os, json, uuid, hashlib, hmac
from datetime import datetime, timedelta
from functools import wraps
from flask import (Flask, request, jsonify, render_template,
                   redirect, url_for, session, send_file)
import requests
import io

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "alerta360-secret-2026")

# ─── Z-API ────────────────────────────────────────────────────────────────────
ZAPI_INSTANCE = os.environ.get("ZAPI_INSTANCE", "")
ZAPI_TOKEN    = os.environ.get("ZAPI_TOKEN", "")
ZAPI_BASE     = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}"
ALERT_NUMBERS = [n.strip() for n in os.environ.get("ALERT_NUMBERS","").split(",") if n.strip()]

# ─── Arquivos de dados ────────────────────────────────────────────────────────
USERS_FILE     = "data_users.json"
ALERTS_FILE    = "data_alerts.json"
INCIDENTS_FILE = "data_incidents.json"
UNITS_FILE     = "data_units.json"
LOGS_FILE      = "data_logs.json"

def load_json(path, default=[]):
    if not os.path.exists(path):
        return default
    try:
        with open(path) as f: return json.load(f)
    except: return default

def save_json(path, data):
    with open(path, "w") as f: json.dump(data, f, ensure_ascii=False, indent=2)

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# ─── Seed inicial ─────────────────────────────────────────────────────────────
def seed():
    if not os.path.exists(USERS_FILE):
        save_json(USERS_FILE, [
            {"id":"u1","nome":"Admin Master","email":"admin@alerta360.com",
             "senha":hash_senha("admin123"),"perfil":"master","unidade_id":"all","ativo":True},
            {"id":"u2","nome":"Operador Silva","email":"operador@alerta360.com",
             "senha":hash_senha("op123"),"perfil":"operador","unidade_id":"un1","ativo":True},
            {"id":"u3","nome":"Escola Estadual","email":"escola@alerta360.com",
             "senha":hash_senha("escola123"),"perfil":"usuario","unidade_id":"un1","ativo":True},
        ])
    if not os.path.exists(UNITS_FILE):
        save_json(UNITS_FILE, [
            {"id":"un1","nome":"Escola Estadual Central","tipo":"escola",
             "endereco":"Asa Norte, Brasília-DF","ativa":True,"sirene_ativa":False},
            {"id":"un2","nome":"Condomínio Jardins","tipo":"condominio",
             "endereco":"Sudoeste, Brasília-DF","ativa":True,"sirene_ativa":False},
            {"id":"un3","nome":"Empresa TechCorp","tipo":"empresa",
             "endereco":"Setor Comercial, Brasília-DF","ativa":True,"sirene_ativa":False},
        ])
    if not os.path.exists(ALERTS_FILE):
        save_json(ALERTS_FILE, [])
    if not os.path.exists(INCIDENTS_FILE):
        save_json(INCIDENTS_FILE, [])
    if not os.path.exists(LOGS_FILE):
        save_json(LOGS_FILE, [])

seed()

# ─── Auth helpers ─────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def master_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("perfil") != "master":
            return jsonify({"ok":False,"erro":"Acesso restrito"}), 403
        return f(*args, **kwargs)
    return decorated

def get_user(uid):
    users = load_json(USERS_FILE)
    return next((u for u in users if u["id"]==uid), None)

def log_acao(user_id, acao, detalhe=""):
    logs = load_json(LOGS_FILE)
    logs.append({
        "id": str(uuid.uuid4())[:8].upper(),
        "timestamp": datetime.now().isoformat(),
        "ts_br": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "user_id": user_id,
        "acao": acao,
        "detalhe": detalhe,
        "ip": request.remote_addr or "—"
    })
    if len(logs) > 500: logs = logs[-500:]
    save_json(LOGS_FILE, logs)

# ─── WhatsApp ─────────────────────────────────────────────────────────────────
def enviar_whatsapp(local, horario, tipo="SOS"):
    if not ZAPI_INSTANCE or not ZAPI_TOKEN:
        return ["simulado"]
    msg = (f"🚨 *ALERTA SILENCIOSO ATIVADO*\n\n"
           f"*Sistema:* ALERTA SILENCIOSO 360\n"
           f"*Tipo:* {tipo}\n"
           f"*Local:* {local}\n"
           f"*Horário:* {horario}\n\n"
           f"⚠️ Verificar imediatamente!")
    enviados = []
    for num in ALERT_NUMBERS:
        try:
            r = requests.post(f"{ZAPI_BASE}/send-text",
                json={"phone":num,"message":msg}, timeout=8)
            enviados.append({"numero":num,"status":r.status_code})
        except Exception as e:
            enviados.append({"numero":num,"erro":str(e)})
    return enviados

# ══════════════════════════════════════════════════════════════════════════════
# AUTENTICAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET","POST"])
def login():
    erro = None
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        senha = request.form.get("senha","").strip()
        users = load_json(USERS_FILE)
        user = next((u for u in users if u["email"]==email
                     and u["senha"]==hash_senha(senha) and u.get("ativo")), None)
        if user:
            session["user_id"]  = user["id"]
            session["nome"]     = user["nome"]
            session["perfil"]   = user["perfil"]
            session["unidade_id"] = user["unidade_id"]
            log_acao(user["id"], "LOGIN", f"Email: {email}")
            return redirect(url_for("dashboard"))
        erro = "E-mail ou senha incorretos."
    return render_template("login.html", erro=erro)

@app.route("/logout")
def logout():
    if "user_id" in session:
        log_acao(session["user_id"], "LOGOUT")
    session.clear()
    return redirect(url_for("login"))

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/dashboard")
@login_required
def dashboard():
    alerts   = load_json(ALERTS_FILE)
    incidents= load_json(INCIDENTS_FILE)
    units    = load_json(UNITS_FILE)
    logs     = load_json(LOGS_FILE)

    hoje = datetime.now().strftime("%Y-%m-%d")
    alertas_hoje = [a for a in alerts if a.get("timestamp","").startswith(hoje)]
    alertas_ativos = [a for a in alerts if a.get("status") == "ativo"]
    incidentes_abertos = [i for i in incidents if i.get("status") == "aberto"]

    return render_template("dashboard.html",
        usuario=session["nome"],
        perfil=session["perfil"],
        alertas_hoje=len(alertas_hoje),
        alertas_ativos=len(alertas_ativos),
        total_unidades=len(units),
        incidentes_abertos=len(incidentes_abertos),
        logs_recentes=logs[-10:][::-1],
        units=units[:6],
        alertas_recentes=alerts[-5:][::-1],
    )

# ══════════════════════════════════════════════════════════════════════════════
# BOTÃO SOS — ACIONAMENTO
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/sos")
@login_required
def sos_page():
    units = load_json(UNITS_FILE)
    return render_template("sos.html",
        usuario=session["nome"],
        perfil=session["perfil"],
        units=units)

@app.route("/api/sos", methods=["POST"])
@login_required
def acionar_sos():
    data      = request.get_json(silent=True) or {}
    unidade   = data.get("unidade", "Não informada")
    tipo      = data.get("tipo", "SOS")
    descricao = data.get("descricao", "")
    agora     = datetime.now()
    ts_br     = agora.strftime("%d/%m/%Y às %H:%M:%S")
    alert_id  = str(uuid.uuid4())[:8].upper()

    alert = {
        "id":        alert_id,
        "timestamp": agora.isoformat(),
        "ts_br":     ts_br,
        "user_id":   session["user_id"],
        "usuario":   session["nome"],
        "unidade":   unidade,
        "tipo":      tipo,
        "descricao": descricao,
        "status":    "ativo",
        "enviados":  []
    }

    enviados = enviar_whatsapp(unidade, ts_br, tipo)
    alert["enviados"] = enviados

    alerts = load_json(ALERTS_FILE)
    alerts.append(alert)
    save_json(ALERTS_FILE, alerts)

    log_acao(session["user_id"], "SOS_ACIONADO",
             f"ID:{alert_id} Unidade:{unidade} Tipo:{tipo}")

    return jsonify({"ok":True,"id":alert_id,"ts":ts_br,
                    "enviados":len(enviados)})

@app.route("/api/sos/fechar/<alert_id>", methods=["POST"])
@login_required
def fechar_alerta(alert_id):
    alerts = load_json(ALERTS_FILE)
    for a in alerts:
        if a["id"] == alert_id:
            a["status"] = "fechado"
            a["fechado_por"] = session["nome"]
            a["fechado_em"] = datetime.now().isoformat()
    save_json(ALERTS_FILE, alerts)
    log_acao(session["user_id"], "ALERTA_FECHADO", f"ID:{alert_id}")
    return jsonify({"ok":True})

# ══════════════════════════════════════════════════════════════════════════════
# ALERTAS — PAINEL
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/alertas")
@login_required
def alertas():
    alerts = load_json(ALERTS_FILE)
    alerts = sorted(alerts, key=lambda x: x["timestamp"], reverse=True)
    return render_template("alertas.html",
        usuario=session["nome"],
        perfil=session["perfil"],
        alerts=alerts)

@app.route("/api/alertas")
@login_required
def api_alertas():
    alerts = load_json(ALERTS_FILE)
    return jsonify(sorted(alerts, key=lambda x: x["timestamp"], reverse=True))

# ══════════════════════════════════════════════════════════════════════════════
# SIRENE
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/sirene")
@login_required
def sirene_page():
    units = load_json(UNITS_FILE)
    return render_template("sirene.html",
        usuario=session["nome"],
        perfil=session["perfil"],
        units=units)

@app.route("/api/sirene/<unit_id>", methods=["POST"])
@login_required
def toggle_sirene(unit_id):
    data  = request.get_json(silent=True) or {}
    ativa = data.get("ativa", False)
    units = load_json(UNITS_FILE)
    for u in units:
        if u["id"] == unit_id:
            u["sirene_ativa"] = ativa
    save_json(UNITS_FILE, units)
    acao = "SIRENE_ON" if ativa else "SIRENE_OFF"
    log_acao(session["user_id"], acao, f"Unidade:{unit_id}")
    return jsonify({"ok":True,"ativa":ativa})

# ══════════════════════════════════════════════════════════════════════════════
# OCORRÊNCIAS
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/ocorrencias")
@login_required
def ocorrencias():
    incidents = load_json(INCIDENTS_FILE)
    incidents = sorted(incidents, key=lambda x: x["timestamp"], reverse=True)
    units = load_json(UNITS_FILE)
    return render_template("ocorrencias.html",
        usuario=session["nome"],
        perfil=session["perfil"],
        incidents=incidents,
        units=units)

@app.route("/api/ocorrencias", methods=["POST"])
@login_required
def criar_ocorrencia():
    data = request.get_json(silent=True) or {}
    agora = datetime.now()
    inc = {
        "id":          str(uuid.uuid4())[:8].upper(),
        "timestamp":   agora.isoformat(),
        "ts_br":       agora.strftime("%d/%m/%Y %H:%M:%S"),
        "titulo":      data.get("titulo","Sem título"),
        "descricao":   data.get("descricao",""),
        "unidade":     data.get("unidade",""),
        "responsavel": session["nome"],
        "risco":       data.get("risco","medio"),
        "status":      "aberto",
        "evidencias":  data.get("evidencias",""),
        "observacoes": data.get("observacoes",""),
    }
    incidents = load_json(INCIDENTS_FILE)
    incidents.append(inc)
    save_json(INCIDENTS_FILE, incidents)
    log_acao(session["user_id"], "OCORRENCIA_CRIADA", f"ID:{inc['id']}")
    return jsonify({"ok":True,"id":inc["id"]})

@app.route("/api/ocorrencias/<inc_id>", methods=["PUT"])
@login_required
def atualizar_ocorrencia(inc_id):
    data = request.get_json(silent=True) or {}
    incidents = load_json(INCIDENTS_FILE)
    for inc in incidents:
        if inc["id"] == inc_id:
            for k in ["status","risco","observacoes","responsavel"]:
                if k in data: inc[k] = data[k]
            inc["atualizado_em"] = datetime.now().isoformat()
    save_json(INCIDENTS_FILE, incidents)
    log_acao(session["user_id"], "OCORRENCIA_ATUALIZADA", f"ID:{inc_id}")
    return jsonify({"ok":True})

# ══════════════════════════════════════════════════════════════════════════════
# UNIDADES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/unidades")
@login_required
def unidades():
    units = load_json(UNITS_FILE)
    return render_template("unidades.html",
        usuario=session["nome"],
        perfil=session["perfil"],
        units=units)

@app.route("/api/unidades", methods=["POST"])
@login_required
def criar_unidade():
    data = request.get_json(silent=True) or {}
    unit = {
        "id":           str(uuid.uuid4())[:8],
        "nome":         data.get("nome","Nova Unidade"),
        "tipo":         data.get("tipo","empresa"),
        "endereco":     data.get("endereco",""),
        "ativa":        True,
        "sirene_ativa": False,
        "criado_em":    datetime.now().isoformat(),
    }
    units = load_json(UNITS_FILE)
    units.append(unit)
    save_json(UNITS_FILE, units)
    log_acao(session["user_id"], "UNIDADE_CRIADA", f"Nome:{unit['nome']}")
    return jsonify({"ok":True,"id":unit["id"]})

# ══════════════════════════════════════════════════════════════════════════════
# USUÁRIOS
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/usuarios")
@login_required
def usuarios():
    if session.get("perfil") != "master":
        return redirect(url_for("dashboard"))
    users = load_json(USERS_FILE)
    for u in users: u.pop("senha", None)
    return render_template("usuarios.html",
        usuario=session["nome"],
        perfil=session["perfil"],
        users=users)

@app.route("/api/usuarios", methods=["POST"])
@login_required
def criar_usuario():
    if session.get("perfil") != "master":
        return jsonify({"ok":False,"erro":"Acesso negado"}), 403
    data = request.get_json(silent=True) or {}
    users = load_json(USERS_FILE)
    if any(u["email"] == data.get("email","") for u in users):
        return jsonify({"ok":False,"erro":"E-mail já cadastrado"})
    user = {
        "id":        str(uuid.uuid4())[:8],
        "nome":      data.get("nome",""),
        "email":     data.get("email","").lower(),
        "senha":     hash_senha(data.get("senha","123456")),
        "perfil":    data.get("perfil","operador"),
        "unidade_id":data.get("unidade_id","all"),
        "ativo":     True,
        "criado_em": datetime.now().isoformat(),
    }
    users.append(user)
    save_json(USERS_FILE, users)
    log_acao(session["user_id"], "USUARIO_CRIADO", f"Email:{user['email']}")
    return jsonify({"ok":True,"id":user["id"]})

# ══════════════════════════════════════════════════════════════════════════════
# LOGS
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/logs")
@login_required
def logs():
    if session.get("perfil") != "master":
        return redirect(url_for("dashboard"))
    all_logs = load_json(LOGS_FILE)
    return render_template("logs.html",
        usuario=session["nome"],
        perfil=session["perfil"],
        logs=all_logs[::-1])

# ══════════════════════════════════════════════════════════════════════════════
# API POLLING — dashboard em tempo real (sem WebSocket)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/status")
@login_required
def api_status():
    alerts   = load_json(ALERTS_FILE)
    incidents= load_json(INCIDENTS_FILE)
    units    = load_json(UNITS_FILE)
    hoje     = datetime.now().strftime("%Y-%m-%d")
    return jsonify({
        "alertas_ativos":    len([a for a in alerts if a.get("status")=="ativo"]),
        "alertas_hoje":      len([a for a in alerts if a.get("timestamp","").startswith(hoje)]),
        "incidentes_abertos":len([i for i in incidents if i.get("status")=="aberto"]),
        "sirenes_ativas":    len([u for u in units if u.get("sirene_ativa")]),
        "ultimo_alerta":     alerts[-1] if alerts else None,
        "ts":                datetime.now().strftime("%H:%M:%S"),
    })

# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO FINANCEIRO SaaS
# ══════════════════════════════════════════════════════════════════════════════

PLANOS = {
    "basico": {
        "nome": "Básico", "preco": 497, "usuarios": 5,
        "unidades": 1, "trial_dias": 7,
        "features": ["Botão SOS PWA","Alertas WhatsApp","Painel básico","Suporte email"],
        "cor": "#3B82F6"
    },
    "profissional": {
        "nome": "Profissional", "preco": 997, "usuarios": 20,
        "unidades": 5, "trial_dias": 14,
        "features": ["Tudo do Básico","PDF jurídico","Sirene remota","Ocorrências","Relatórios","Suporte WhatsApp"],
        "cor": "#DC2626"
    },
    "enterprise": {
        "nome": "Enterprise", "preco": 2497, "usuarios": 999,
        "unidades": 999, "trial_dias": 30,
        "features": ["Tudo do Profissional","Usuários ilimitados","Multi-empresa","API access","SLA 99.9%","Suporte 24h"],
        "cor": "#F59E0B"
    },
}

ASSINATURAS_FILE = "data_assinaturas.json"

def get_assinatura(company_id="default"):
    assinaturas = load_json(ASSINATURAS_FILE, {})
    if isinstance(assinaturas, list): assinaturas = {}
    return assinaturas.get(company_id)

def salvar_assinatura(company_id, dados):
    assinaturas = load_json(ASSINATURAS_FILE, {})
    if isinstance(assinaturas, list): assinaturas = {}
    assinaturas[company_id] = dados
    save_json(ASSINATURAS_FILE, assinaturas)

def checar_acesso():
    """Retorna True se o acesso está liberado."""
    ass = get_assinatura("default")
    if not ass:
        return True  # sem assinatura = trial ativo
    if ass.get("status") == "bloqueado":
        return False
    if ass.get("status") == "trial":
        trial_fim = datetime.fromisoformat(ass["trial_fim"])
        if datetime.now() > trial_fim:
            ass["status"] = "bloqueado"
            ass["motivo"] = "Trial expirado"
            salvar_assinatura("default", ass)
            return False
    return True

@app.route("/planos")
def planos():
    ass = get_assinatura("default")
    return render_template("planos.html",
        planos=PLANOS,
        assinatura=ass,
        usuario=session.get("nome",""),
        perfil=session.get("perfil",""),
        logado="user_id" in session)

@app.route("/api/assinar", methods=["POST"])
@login_required
def assinar_plano():
    data = request.get_json(silent=True) or {}
    plano_id = data.get("plano","profissional")
    plano = PLANOS.get(plano_id)
    if not plano:
        return jsonify({"ok":False,"erro":"Plano inválido"})

    agora = datetime.now()
    trial_fim = agora + timedelta(days=plano["trial_dias"])
    ass = {
        "plano_id":    plano_id,
        "plano_nome":  plano["nome"],
        "preco":       plano["preco"],
        "status":      "trial",
        "trial_inicio":agora.isoformat(),
        "trial_fim":   trial_fim.isoformat(),
        "trial_fim_br":trial_fim.strftime("%d/%m/%Y"),
        "ativo_desde": agora.isoformat(),
        "renovacao_em":None,
        "empresa":     session.get("nome",""),
        "pagamentos":  [],
    }
    salvar_assinatura("default", ass)
    log_acao(session["user_id"], "ASSINAR_PLANO", f"Plano:{plano_id} Trial:{plano['trial_dias']}d")

    # Link de pagamento Asaas (simulado — troque pela URL real do Asaas)
    link_pagamento = f"https://wa.me/5561993962090?text=Quero+assinar+o+plano+{plano['nome']}+do+ALERTA+SILENCIOSO+360+por+R$+{plano['preco']}/mes"

    return jsonify({
        "ok": True,
        "trial_fim": ass["trial_fim_br"],
        "link_pagamento": link_pagamento,
        "msg": f"Trial de {plano['trial_dias']} dias ativado! Vence em {ass['trial_fim_br']}."
    })

@app.route("/financeiro")
@login_required
def financeiro():
    if session.get("perfil") != "master":
        return redirect(url_for("dashboard"))
    ass = get_assinatura("default")
    alerts = load_json(ALERTS_FILE)
    incidents = load_json(INCIDENTS_FILE)
    users = load_json(USERS_FILE)
    hoje = datetime.now().strftime("%Y-%m-%d")
    mes = datetime.now().strftime("%Y-%m")
    return render_template("financeiro.html",
        usuario=session["nome"],
        perfil=session["perfil"],
        assinatura=ass,
        planos=PLANOS,
        total_alertas=len(alerts),
        alertas_mes=len([a for a in alerts if a.get("timestamp","").startswith(mes)]),
        total_usuarios=len(users),
        total_incidents=len(incidents),
    )

@app.route("/api/financeiro/registrar-pagamento", methods=["POST"])
@login_required
def registrar_pagamento():
    if session.get("perfil") != "master":
        return jsonify({"ok":False}), 403
    data = request.get_json(silent=True) or {}
    ass = get_assinatura("default")
    if not ass:
        return jsonify({"ok":False,"erro":"Sem assinatura"})
    pagamento = {
        "id":     str(uuid.uuid4())[:8].upper(),
        "data":   datetime.now().strftime("%d/%m/%Y"),
        "valor":  data.get("valor", ass.get("preco",0)),
        "metodo": data.get("metodo","PIX"),
        "status": "pago",
    }
    ass.setdefault("pagamentos",[]).append(pagamento)
    ass["status"] = "ativo"
    prox = datetime.now() + timedelta(days=30)
    ass["renovacao_em"] = prox.strftime("%d/%m/%Y")
    salvar_assinatura("default", ass)
    log_acao(session["user_id"], "PAGAMENTO_REGISTRADO", f"R${pagamento['valor']} via {pagamento['metodo']}")
    return jsonify({"ok":True,"id":pagamento["id"]})

@app.route("/api/financeiro/bloquear", methods=["POST"])
@login_required
def bloquear_acesso():
    if session.get("perfil") != "master":
        return jsonify({"ok":False}), 403
    ass = get_assinatura("default")
    if ass:
        ass["status"] = "bloqueado"
        ass["motivo"] = "Inadimplência"
        salvar_assinatura("default", ass)
    return jsonify({"ok":True})

# ── Middleware de bloqueio ────────────────────────────────────────────────────
@app.before_request
def checar_bloqueio():
    rotas_livres = ["login","logout","planos","static","assinar_plano"]
    if request.endpoint in rotas_livres: return
    if "user_id" not in session: return
    if session.get("perfil") == "master": return
    if not checar_acesso():
        return render_template("bloqueado.html",
            usuario=session.get("nome",""),
            perfil=session.get("perfil",""),
            assinatura=get_assinatura("default"))


# ══════════════════════════════════════════════════════════════════════════════
# MODO DEMONSTRAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

import random

NOMES_FAKE = ["Carlos Silva","Ana Oliveira","João Santos","Maria Costa","Pedro Lima","Fernanda Rocha"]
UNIDADES_FAKE = ["Escola Estadual Central","Condomínio Jardins","Empresa TechCorp","Portaria Shopping Sul","Colégio São Lucas","Condomínio Park Way"]
TIPOS_FAKE = ["SOS","Intruso","Incêndio","Agressão","Pânico","Médico"]
TITULOS_FAKE = ["Pessoa suspeita na entrada","Conflito no corredor","Alerta médico — sala 12","Invasão detectada no setor B","Situação de pânico — recepção","Incidente com visitante"]

@app.route("/demo")
@login_required
def demo_page():
    return render_template("demo.html",
        usuario=session["nome"],
        perfil=session["perfil"])

@app.route("/api/demo/gerar", methods=["POST"])
@login_required
def gerar_demo():
    data   = request.get_json(silent=True) or {}
    qtd    = min(int(data.get("qtd", 5)), 20)
    agora  = datetime.now()

    alerts_gerados = []
    incs_gerados   = []

    alerts   = load_json(ALERTS_FILE)
    incidents= load_json(INCIDENTS_FILE)

    for i in range(qtd):
        delta = timedelta(minutes=random.randint(5, 60*24*7))
        ts    = agora - delta
        ts_br = ts.strftime("%d/%m/%Y às %H:%M:%S")
        aid   = str(uuid.uuid4())[:8].upper()
        status= random.choice(["ativo","fechado","fechado","fechado"])

        alert = {
            "id":        aid,
            "timestamp": ts.isoformat(),
            "ts_br":     ts_br,
            "user_id":   "demo",
            "usuario":   random.choice(NOMES_FAKE),
            "unidade":   random.choice(UNIDADES_FAKE),
            "tipo":      random.choice(TIPOS_FAKE),
            "descricao": "Alerta gerado automaticamente pelo modo demonstração.",
            "status":    status,
            "enviados":  [{"numero":"demo","status":200}],
            "demo":      True,
        }
        if status == "fechado":
            ts_f = ts + timedelta(minutes=random.randint(2, 45))
            alert["fechado_por"] = random.choice(NOMES_FAKE)
            alert["fechado_em"]  = ts_f.isoformat()
        alerts.append(alert)
        alerts_gerados.append(aid)

        iid = str(uuid.uuid4())[:8].upper()
        inc = {
            "id":          iid,
            "timestamp":   ts.isoformat(),
            "ts_br":       ts_br,
            "titulo":      random.choice(TITULOS_FAKE),
            "descricao":   "Ocorrência gerada pelo modo demonstração.",
            "unidade":     random.choice(UNIDADES_FAKE),
            "responsavel": random.choice(NOMES_FAKE),
            "risco":       random.choice(["alto","medio","medio","baixo"]),
            "status":      random.choice(["aberto","andamento","finalizado","finalizado"]),
            "evidencias":  "",
            "observacoes": "Demo automático.",
            "demo":        True,
        }
        incidents.append(inc)
        incs_gerados.append(iid)

    save_json(ALERTS_FILE, alerts)
    save_json(INCIDENTS_FILE, incidents)
    log_acao(session["user_id"], "DEMO_GERADO", f"{qtd} alertas e ocorrências simulados")

    return jsonify({"ok":True, "alertas":len(alerts_gerados), "incidentes":len(incs_gerados)})

@app.route("/api/demo/limpar", methods=["POST"])
@login_required
def limpar_demo():
    alerts    = [a for a in load_json(ALERTS_FILE)    if not a.get("demo")]
    incidents = [i for i in load_json(INCIDENTS_FILE) if not i.get("demo")]
    save_json(ALERTS_FILE, alerts)
    save_json(INCIDENTS_FILE, incidents)
    log_acao(session["user_id"], "DEMO_LIMPO", "Dados de demonstração removidos")
    return jsonify({"ok":True})


@app.route("/landing")
def landing():
    return render_template("landing.html")

# ══════════════════════════════════════════════════════════════════════════════
# RELATÓRIO PDF DO SISTEMA
# ══════════════════════════════════════════════════════════════════════════════

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

@app.route("/relatorio/alerta/<alert_id>")
@login_required
def relatorio_alerta(alert_id):
    alerts = load_json(ALERTS_FILE)
    alert  = next((a for a in alerts if a["id"] == alert_id), None)
    if not alert:
        return "Alerta não encontrado.", 404
    buf = gerar_pdf_alerta(alert)
    nome = f"ALERTA360-{alert_id}-{datetime.now().strftime('%Y%m%d')}.pdf"
    return send_file(buf, mimetype="application/pdf",
                     as_attachment=True, download_name=nome)

@app.route("/relatorio/geral")
@login_required
def relatorio_geral():
    if session.get("perfil") != "master":
        return redirect(url_for("dashboard"))
    alerts    = load_json(ALERTS_FILE)
    incidents = load_json(INCIDENTS_FILE)
    units     = load_json(UNITS_FILE)
    users     = load_json(USERS_FILE)
    buf = gerar_pdf_geral(alerts, incidents, units, users)
    nome = f"ALERTA360-RELATORIO-GERAL-{datetime.now().strftime('%Y%m%d')}.pdf"
    return send_file(buf, mimetype="application/pdf",
                     as_attachment=True, download_name=nome)

def _cores():
    return {
        "V":  colors.HexColor("#EF4444"),
        "VL": colors.HexColor("#1A0A0A"),
        "CE": colors.HexColor("#1E293B"),
        "CM": colors.HexColor("#64748B"),
        "CC": colors.HexColor("#0D1321"),
        "CB": colors.HexColor("#1F2A3C"),
        "AZ": colors.HexColor("#3B82F6"),
        "GR": colors.HexColor("#22C55E"),
        "AM": colors.HexColor("#F59E0B"),
        "BR": colors.white,
    }

def _s(name, **kw):
    base = dict(fontName="Helvetica", fontSize=10,
                textColor=colors.HexColor("#E2E8F0"), leading=15)
    base.update(kw)
    return ParagraphStyle(name, **base)

def _cab(titulo, sub, num, W):
    c = _cores()
    rows = [
        [Paragraph(titulo, _s("t", fontName="Helvetica-Bold", fontSize=22,
            textColor=c["BR"], alignment=TA_CENTER))],
        [Paragraph(sub, _s("s", fontSize=11,
            textColor=colors.HexColor("#94A3B8"), alignment=TA_CENTER))],
        [Paragraph(num, _s("n", fontSize=10,
            textColor=colors.HexColor("#64748B"), alignment=TA_CENTER))],
    ]
    t = Table(rows, colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), c["CE"]),
        ("TOPPADDING",(0,0),(-1,0), 16),
        ("BOTTOMPADDING",(0,-1),(-1,-1), 14),
        ("LEFTPADDING",(0,0),(-1,-1), 20),
        ("RIGHTPADDING",(0,0),(-1,-1), 20),
    ]))
    return t

def _sec(txt, cor, W):
    c = _cores()
    t = Table([[Paragraph(f"  {txt}", _s("h",
        fontName="Helvetica-Bold", fontSize=10, textColor=c["BR"]))]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), cor),
        ("TOPPADDING",(0,0),(-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
    ]))
    return t

def _kv(linhas, W, c1=4.5*cm):
    c = _cores()
    rows = [[Paragraph(f"<b>{r}</b>", _s("k")), Paragraph(str(v), _s("v"))]
            for r,v in linhas]
    t = Table(rows, colWidths=[c1, W-c1])
    t.setStyle(TableStyle([
        ("ROWBACKGROUNDS",(0,0),(-1,-1), [c["CC"], c["CE"]]),
        ("GRID",(0,0),(-1,-1), 0.3, c["CB"]),
        ("TOPPADDING",(0,0),(-1,-1), 7),
        ("BOTTOMPADDING",(0,0),(-1,-1), 7),
        ("LEFTPADDING",(0,0),(-1,-1), 10),
        ("RIGHTPADDING",(0,0),(-1,-1), 10),
        ("VALIGN",(0,0),(-1,-1), "TOP"),
    ]))
    return t

def _rodape(W):
    c = _cores()
    return [
        Spacer(1, 0.4*cm),
        HRFlowable(width=W, thickness=0.3, color=c["CB"]),
        Spacer(1, 0.2*cm),
        Paragraph(
            f"ALERTA SILENCIOSO 360 · SPYNET Security · CNPJ 64.000.808/0001-51 · "
            f"Brasília-DF · (61) 99396-2090 · Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            _s("r", fontSize=8, textColor=c["CM"], alignment=TA_CENTER)
        )
    ]

def gerar_pdf_alerta(alert: dict) -> io.BytesIO:
    buf = io.BytesIO()
    W   = A4[0] - 5*cm
    doc = SimpleDocTemplate(buf, pagesize=A4,
          leftMargin=2.5*cm, rightMargin=2.5*cm,
          topMargin=2*cm, bottomMargin=2*cm)
    c   = _cores()
    s   = []

    s.append(_cab("ALERTA SILENCIOSO 360",
        "Relatório de Ocorrência de Segurança",
        f"Protocolo #{alert['id']} · SPYNET Security · Brasília-DF", W))
    s.append(Spacer(1, 0.5*cm))

    # Status
    cor_status = c["V"] if alert.get("status")=="ativo" else c["GR"]
    box = Table([[Paragraph(
        f"STATUS: {alert.get('status','—').upper()}",
        _s("st", fontName="Helvetica-Bold", fontSize=14,
           textColor=cor_status, alignment=TA_CENTER)
    )]], colWidths=[W])
    box.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), c["CE"]),
        ("BOX",(0,0),(-1,-1), 1.5, cor_status),
        ("TOPPADDING",(0,0),(-1,-1), 10),
        ("BOTTOMPADDING",(0,0),(-1,-1), 10),
    ]))
    s.append(box)
    s.append(Spacer(1, 0.35*cm))

    s.append(_sec("1. DADOS DO ALERTA", c["V"], W))
    s.append(Spacer(1, 0.15*cm))
    s.append(_kv([
        ("Protocolo:",     f"#{alert['id']}"),
        ("Data e hora:",   alert.get("ts_br","—")),
        ("Tipo:",          alert.get("tipo","—")),
        ("Unidade/Local:", alert.get("unidade","—")),
        ("Status:",        alert.get("status","—").upper()),
    ], W))
    s.append(Spacer(1, 0.35*cm))

    s.append(_sec("2. OPERADOR ACIONADOR", c["CE"], W))
    s.append(Spacer(1, 0.15*cm))
    s.append(_kv([
        ("Usuário:",  alert.get("usuario","—")),
        ("User ID:",  alert.get("user_id","—")),
    ], W))
    s.append(Spacer(1, 0.35*cm))

    s.append(_sec("3. DESCRIÇÃO DO INCIDENTE", c["V"], W))
    s.append(Spacer(1, 0.15*cm))
    desc = alert.get("descricao") or "Nenhuma descrição adicional informada."
    db = Table([[Paragraph(desc, _s("d"))]], colWidths=[W])
    db.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), c["CE"]),
        ("BOX",(0,0),(-1,-1), 0.3, c["CB"]),
        ("TOPPADDING",(0,0),(-1,-1), 10),
        ("BOTTOMPADDING",(0,0),(-1,-1), 10),
        ("LEFTPADDING",(0,0),(-1,-1), 12),
        ("RIGHTPADDING",(0,0),(-1,-1), 12),
    ]))
    s.append(db)
    s.append(Spacer(1, 0.35*cm))

    # Encerramento
    if alert.get("status") == "fechado":
        s.append(_sec("4. ENCERRAMENTO", c["GR"], W))
        s.append(Spacer(1, 0.15*cm))
        try:
            fem = datetime.fromisoformat(alert.get("fechado_em","")).strftime("%d/%m/%Y às %H:%M:%S")
        except:
            fem = alert.get("fechado_em","—")
        s.append(_kv([
            ("Encerrado por:", alert.get("fechado_por","—")),
            ("Encerrado em:",  fem),
        ], W))
        s.append(Spacer(1, 0.35*cm))

    # Assinatura
    s.append(Spacer(1, 0.8*cm))
    s.append(HRFlowable(width=W, thickness=0.5, color=c["CB"]))
    s.append(Spacer(1, 0.4*cm))
    ass = Table([[
        Paragraph("_" * 38, _s("a", alignment=TA_CENTER)),
        Paragraph("_" * 38, _s("a", alignment=TA_CENTER)),
    ],[
        Paragraph("Operador acionador", _s("b", fontSize=9, textColor=c["CM"], alignment=TA_CENTER)),
        Paragraph("Coordenador / Responsável", _s("c", fontSize=9, textColor=c["CM"], alignment=TA_CENTER)),
    ]], colWidths=[W/2, W/2])
    ass.setStyle(TableStyle([
        ("TOPPADDING",(0,0),(-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
    ]))
    s.append(ass)
    s.append(Spacer(1, 0.5*cm))

    # LGPD
    s.append(HRFlowable(width=W, thickness=0.3, color=c["CB"]))
    s.append(Spacer(1, 0.2*cm))
    s.append(Paragraph(
        "Este documento contém dados pessoais tratados com base no legítimo interesse "
        "institucional para fins de segurança patrimonial, nos termos da Lei 13.709/2018 "
        "(LGPD), Art. 7º, IX. Acesso restrito às partes envolvidas e autoridades competentes.",
        _s("l", fontSize=8, textColor=c["CM"], fontName="Helvetica-Oblique")
    ))

    s += _rodape(W)
    doc.build(s)
    buf.seek(0)
    return buf


def gerar_pdf_geral(alerts, incidents, units, users) -> io.BytesIO:
    buf = io.BytesIO()
    W   = A4[0] - 5*cm
    doc = SimpleDocTemplate(buf, pagesize=A4,
          leftMargin=2.5*cm, rightMargin=2.5*cm,
          topMargin=2*cm, bottomMargin=2*cm)
    c   = _cores()
    s   = []
    hoje = datetime.now().strftime("%Y-%m-%d")
    mes  = datetime.now().strftime("%Y-%m")

    s.append(_cab("ALERTA SILENCIOSO 360",
        "Relatório Executivo Geral",
        f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')} · SPYNET Security", W))
    s.append(Spacer(1, 0.5*cm))

    # Resumo executivo
    s.append(_sec("1. RESUMO EXECUTIVO", c["V"], W))
    s.append(Spacer(1, 0.15*cm))
    ativos   = len([a for a in alerts if a.get("status")=="ativo"])
    hoje_qt  = len([a for a in alerts if a.get("timestamp","").startswith(hoje)])
    mes_qt   = len([a for a in alerts if a.get("timestamp","").startswith(mes)])
    abertos  = len([i for i in incidents if i.get("status")=="aberto"])
    s.append(_kv([
        ("Total de alertas:",          str(len(alerts))),
        ("Alertas ativos:",            str(ativos)),
        ("Alertas hoje:",              str(hoje_qt)),
        ("Alertas este mês:",          str(mes_qt)),
        ("Ocorrências abertas:",       str(abertos)),
        ("Total de ocorrências:",      str(len(incidents))),
        ("Unidades cadastradas:",      str(len(units))),
        ("Usuários cadastrados:",      str(len(users))),
    ], W))
    s.append(Spacer(1, 0.35*cm))

    # Alertas recentes
    s.append(_sec("2. ÚLTIMOS 10 ALERTAS", c["CE"], W))
    s.append(Spacer(1, 0.15*cm))
    recentes = sorted(alerts, key=lambda x: x.get("timestamp",""), reverse=True)[:10]
    if recentes:
        header = [["#ID","Data/Hora","Unidade","Tipo","Status"]]
        rows   = header + [[
            a.get("id",""),
            a.get("ts_br","")[:16] if a.get("ts_br") else "—",
            (a.get("unidade","") or "—")[:25],
            a.get("tipo","—"),
            a.get("status","—").upper()
        ] for a in recentes]
        t = Table(rows, colWidths=[2*cm, 4*cm, 5*cm, 3*cm, W-14*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0), c["CE"]),
            ("TEXTCOLOR",(0,0),(-1,0), c["BR"]),
            ("FONTNAME",(0,0),(-1,0), "Helvetica-Bold"),
            ("FONTSIZE",(0,0),(-1,-1), 9),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [c["CC"], c["CE"]]),
            ("GRID",(0,0),(-1,-1), 0.3, c["CB"]),
            ("TOPPADDING",(0,0),(-1,-1), 6),
            ("BOTTOMPADDING",(0,0),(-1,-1), 6),
            ("LEFTPADDING",(0,0),(-1,-1), 8),
            ("RIGHTPADDING",(0,0),(-1,-1), 8),
            ("VALIGN",(0,0),(-1,-1), "MIDDLE"),
            ("TEXTCOLOR",(4,1),(4,-1), c["V"]),
        ]))
        s.append(t)
    else:
        s.append(Paragraph("Nenhum alerta registrado.", _s("e", textColor=c["CM"])))
    s.append(Spacer(1, 0.35*cm))

    # Ocorrências por status
    s.append(_sec("3. OCORRÊNCIAS POR STATUS", c["CE"], W))
    s.append(Spacer(1, 0.15*cm))
    for status_label in ["aberto","andamento","finalizado"]:
        grupo = [i for i in incidents if i.get("status")==status_label]
        s.append(Paragraph(
            f"<b>{status_label.upper()}</b> — {len(grupo)} ocorrência(s)",
            _s("g", fontSize=11, textColor={
                "aberto":c["V"],"andamento":c["AM"],"finalizado":c["GR"]
            }.get(status_label, c["CM"]))
        ))
        s.append(Spacer(1, 0.1*cm))
    s.append(Spacer(1, 0.25*cm))

    # Unidades
    s.append(_sec("4. UNIDADES MONITORADAS", c["CE"], W))
    s.append(Spacer(1, 0.15*cm))
    s.append(_kv([(u["nome"], f"{u['tipo']} · {u.get('endereco','—')} · Sirene: {'ATIVA' if u.get('sirene_ativa') else 'desligada'}") for u in units], W))

    s += _rodape(W)
    doc.build(s)
    buf.seek(0)
    return buf


# ══════════════════════════════════════════════════════════════════════════════
# CONTROLES DO SISTEMA — reiniciar, limpar, parar tudo
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/sistema/reiniciar", methods=["POST"])
@login_required
def reiniciar_sistema():
    if session.get("perfil") != "master":
        return jsonify({"ok":False,"erro":"Acesso negado"}), 403
    # Limpa dados temporários mantendo usuários e unidades
    save_json(ALERTS_FILE, [])
    save_json(INCIDENTS_FILE, [])
    save_json(LOGS_FILE, [])
    log_acao(session["user_id"], "SISTEMA_REINICIADO", "Dados limpos pelo master")
    return jsonify({"ok":True,"msg":"Sistema reiniciado. Alertas, ocorrências e logs limpos."})

@app.route("/api/sistema/limpar-alertas", methods=["POST"])
@login_required
def limpar_alertas():
    if session.get("perfil") not in ["master","operador"]:
        return jsonify({"ok":False}), 403
    save_json(ALERTS_FILE, [])
    log_acao(session["user_id"], "ALERTAS_LIMPOS", "Todos os alertas removidos")
    return jsonify({"ok":True,"msg":"Todos os alertas foram removidos."})

@app.route("/api/sistema/parar-tudo", methods=["POST"])
@login_required
def parar_tudo():
    """Para todas as sirenes e fecha todos os alertas ativos."""
    if session.get("perfil") not in ["master","operador"]:
        return jsonify({"ok":False}), 403
    # Fechar todos alertas ativos
    alerts = load_json(ALERTS_FILE)
    agora  = datetime.now().isoformat()
    count  = 0
    for a in alerts:
        if a.get("status") == "ativo":
            a["status"]     = "fechado"
            a["fechado_por"]= session["nome"]
            a["fechado_em"] = agora
            count += 1
    save_json(ALERTS_FILE, alerts)
    # Desligar todas as sirenes
    units = load_json(UNITS_FILE)
    for u in units:
        u["sirene_ativa"] = False
    save_json(UNITS_FILE, units)
    log_acao(session["user_id"], "PARAR_TUDO",
             f"{count} alerta(s) fechado(s) + todas sirenes desligadas")
    return jsonify({"ok":True, "alertas_fechados":count,
                    "msg":f"{count} alerta(s) encerrado(s) e todas as sirenes desligadas."})

@app.route("/api/sistema/resetar-senha", methods=["POST"])
@login_required
def resetar_senha():
    """Master pode resetar senha de qualquer usuário."""
    if session.get("perfil") != "master":
        return jsonify({"ok":False}), 403
    data     = request.get_json(silent=True) or {}
    user_id  = data.get("user_id")
    nova     = data.get("nova_senha","123456")
    users    = load_json(USERS_FILE)
    for u in users:
        if u["id"] == user_id:
            u["senha"] = hash_senha(nova)
    save_json(USERS_FILE, users)
    log_acao(session["user_id"], "SENHA_RESETADA", f"UserID:{user_id}")
    return jsonify({"ok":True})

