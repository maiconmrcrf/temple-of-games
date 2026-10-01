#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Temple of Games — Flask + Asaas PIX + Admin.
O token vem da variável de ambiente ASAAS_API_KEY configurada no Render."""

import os, json
from datetime import datetime
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="public", static_url_path="")

ACCESS_TOKEN = os.environ.get("ASAAS_API_KEY", "").strip()

if ACCESS_TOKEN and "_prod_" in ACCESS_TOKEN:
    BASE_URL, AMBIENTE = "https://api.asaas.com", "PRODUÇÃO"
elif ACCESS_TOKEN and "_sandbox_" in ACCESS_TOKEN:
    BASE_URL, AMBIENTE = "https://api-sandbox.asaas.com", "SANDBOX"
elif ACCESS_TOKEN:
    BASE_URL, AMBIENTE = "https://api.asaas.com", "PRODUÇÃO"
else:
    BASE_URL, AMBIENTE = "https://api.asaas.com", "SEM TOKEN"

HEADERS = {"access_token": ACCESS_TOKEN, "Content-Type": "application/json"}
VALOR_MINIMO = 5.00
ADMIN_SENHA = "temple2026"

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
USERS_FILE  = os.path.join(BASE_DIR, "usuarios.json")
PIX_FILE    = os.path.join(BASE_DIR, "pix_pendentes.json")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

CONFIG_PADRAO = {
    "empresa": {"nome": "Temple of Games",
                "descricao_pix": "Temple of Games - Créditos",
                "logo_emoji": "🏛️"},
    "banner": "ONLINE CASINO GAMES",
    "cores": {"dourado": "#d4af37", "dourado_claro": "#f0c040"},
    "jogos": [
        {"nome": "Zeus vs Hades",
         "link": "https://www.pragmaticplay.com/br/jogos/zeus-vs-hades-gods-of-war-250/?gamelang=br&cur=BRL",
         "imagem": "https://i.ibb.co/PzcPLBtg/Screenshot-2026-09-30-10-34-24-313-com-android-chrome.png"},
        {"nome": "Fortune Tiger",
         "link": "https://templeofgames.com/gameDetailIos?gameId=23537",
         "imagem": "https://i.ibb.co/bRgRw8kF/Screenshot-2026-09-30-10-34-02-165-com-android-chrome.png"},
        {"nome": "Gates of Olympus",
         "link": "https://www.pragmaticplay.com/br/jogos/gates-of-olympus/",
         "imagem": "https://i.ibb.co/PvtjC7rg/Screenshot-2026-09-30-10-33-44-230-com-android-chrome.png"},
        {"nome": "Fortune Rabbit",
         "link": "https://templeofgames.com/gameDetailIos?gameId=23536",
         "imagem": "https://i.ibb.co/bTkYQCz/Screenshot-2026-09-30-10-33-26-327-com-android-chrome.png"},
        {"nome": "Fortune Ox",
         "link": "https://templeofgames.com/gameDetailIos?gameId=12475",
         "imagem": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSPlVsMXAaZ130eBumGDhW3NVDNn5-LTJx-mqtT5ha3ww&s=10"},
        {"nome": "Tigre Sortudo",
         "link": "#",
         "imagem": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRRIuMG3iUsuQD8dvF50cbQiohl7vcsek71fV98_pRYCg&s=10"},
        {"nome": "Fortune Dragon",
         "link": "#",
         "imagem": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQYNKBNAec0CrMnlVic1KyG0f80jsI9Q9WmYhBY7NlSPw&s=10"}
    ]
}


def ler_json(c, p):
    if not os.path.exists(c): return p
    try:
        with open(c, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return p


def salvar_json(c, d):
    with open(c, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def get_config():
    cfg = ler_json(CONFIG_FILE, None)
    if not cfg:
        salvar_json(CONFIG_FILE, CONFIG_PADRAO)
        return CONFIG_PADRAO
    for k, v in CONFIG_PADRAO.items():
        if k not in cfg: cfg[k] = v

    # MIGRAÇÃO: força atualizar os jogos se a versão antiga estiver salva
    versao_atual = cfg.get("_versao_jogos", 0)
    if versao_atual < 4:
        cfg["jogos"] = CONFIG_PADRAO["jogos"]
        cfg["_versao_jogos"] = 4
        salvar_json(CONFIG_FILE, cfg)

    return cfg


def get_ip_cliente():
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    return request.remote_addr or "desconhecido"


@app.route("/")
def root(): return send_from_directory("public", "index.html")


@app.route("/<path:path>")
def static_files(path): return send_from_directory("public", path)


@app.route("/api/config")
def api_get_config(): return jsonify(get_config())


@app.route("/api/saldo/<email>")
def api_saldo(email):
    u = ler_json(USERS_FILE, {}).get(email.lower())
    if not u: return jsonify({"saldo": 0})
    return jsonify({"saldo": u.get("saldo", 0.0)})


@app.route("/api/usuarios", methods=["GET"])
def listar_usuarios(): return jsonify(ler_json(USERS_FILE, {}))


@app.route("/api/usuarios", methods=["POST"])
def salvar_usuario():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    if not email: return jsonify({"erro": "E-mail obrigatório"}), 400
    users = ler_json(USERS_FILE, {})
    if email in users: return jsonify({"erro": "E-mail já cadastrado"}), 409
    users[email] = {
        "nome": (data.get("nome") or "").strip(),
        "cpf":  (data.get("cpf") or "").strip(),
        "email": email, "senha": data.get("senha", ""),
        "nasc": data.get("nasc", ""), "saldo": 0.0, "historico": [],
        "ip_capturado": get_ip_cliente(),
        "criado_em": datetime.now().isoformat(),
        "user_agent": request.headers.get("User-Agent", "")[:200]
    }
    salvar_json(USERS_FILE, users)
    return jsonify({"ok": True, "email": email})


@app.route("/api/usuarios/<email>", methods=["GET"])
def obter_usuario(email):
    u = ler_json(USERS_FILE, {}).get(email.lower())
    if not u: return jsonify({"erro": "Usuário não encontrado"}), 404
    return jsonify({k: v for k, v in u.items() if k != "senha"})


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    senha = data.get("senha", "")
    u = ler_json(USERS_FILE, {}).get(email)
    if not u: return jsonify({"erro": "E-mail não cadastrado"}), 404
    if u.get("senha") != senha: return jsonify({"erro": "Senha incorreta"}), 401
    return jsonify({"ok": True, "nome": u.get("nome"), "email": u.get("email"),
                    "saldo": u.get("saldo", 0.0)})


@app.route("/api/usuarios/<email>/saldo", methods=["POST"])
def atualizar_saldo(email):
    data = request.get_json() or {}
    delta = float(data.get("delta", 0))
    motivo = data.get("motivo", "Ajuste")
    users = ler_json(USERS_FILE, {})
    u = users.get(email.lower())
    if not u: return jsonify({"erro": "Usuário não encontrado"}), 404
    u["saldo"] = round((u.get("saldo", 0.0) + delta), 2)
    u.setdefault("historico", []).insert(0, {
        "tipo": motivo, "valor": delta, "data": datetime.now().isoformat()})
    u["historico"] = u["historico"][:50]
    salvar_json(USERS_FILE, users)
    return jsonify({"ok": True, "saldo": u["saldo"]})


@app.route("/api/usuarios/<email>/historico")
def historico_usuario(email):
    u = ler_json(USERS_FILE, {}).get(email.lower())
    if not u: return jsonify({"erro": "Usuário não encontrado"}), 404
    return jsonify(u.get("historico", []))


@app.route("/api/testar-token")
def testar_token():
    if not ACCESS_TOKEN:
        return jsonify({"ok": False, "erro": "Token não configurado. Defina ASAAS_API_KEY no Render."})
    try:
        r = requests.get(f"{BASE_URL}/v3/customers?limit=1", headers=HEADERS, timeout=15)
        return jsonify({"ok": r.status_code == 200, "status_code": r.status_code,
                        "ambiente": AMBIENTE, "base_url": BASE_URL,
                        "token_prefixo": ACCESS_TOKEN[:30] + "...",
                        "token_tamanho": len(ACCESS_TOKEN),
                        "resposta": r.text[:400]})
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e), "ambiente": AMBIENTE})


def asaas_cadastrar_cliente(nome, cpf, email):
    r = requests.post(f"{BASE_URL}/v3/customers",
        json={"name": nome, "cpfCnpj": cpf, "email": email, "notificationDisabled": True},
        headers=HEADERS, timeout=30)
    if r.status_code == 200: return r.json().get("id"), None
    try: erro = r.json().get("errors", [{}])[0].get("description", "Erro")
    except Exception: erro = r.text[:300]
    return None, f"{r.status_code} - {erro}"


def asaas_criar_cobranca(customer_id, valor, descricao):
    r = requests.post(f"{BASE_URL}/v3/payments",
        json={"customer": customer_id, "billingType": "PIX",
              "dueDate": datetime.now().strftime("%Y-%m-%d"),
              "value": round(valor, 2), "description": descricao,
              "postalService": False},
        headers=HEADERS, timeout=30)
    if r.status_code == 200: return r.json(), None
    try: erro = r.json().get("errors", [{}])[0].get("description", "Erro")
    except Exception: erro = r.text[:300]
    return None, f"{r.status_code} - {erro}"


@app.route("/api/criar-pix", methods=["POST"])
def api_criar_pix():
    if not ACCESS_TOKEN:
        return jsonify({"erro": "Token do Asaas não configurado no servidor."}), 500

    data = request.get_json() or {}
    try: valor = float(data.get("valor", 0))
    except (TypeError, ValueError): return jsonify({"erro": "Valor inválido."}), 400
    if valor < VALOR_MINIMO:
        return jsonify({"erro": f"Valor mínimo: R$ {VALOR_MINIMO:.2f}"}), 400

    cfg = get_config()
    emp = cfg.get("empresa", {})
    nome_emp = emp.get("nome", "Temple of Games")
    desc_pix = emp.get("descricao_pix", f"{nome_emp} - Créditos")

    customer_id, err = asaas_cadastrar_cliente(nome_emp, "11144477735",
                                               "cliente@templegames.demo")
    if not customer_id:
        return jsonify({"erro": f"Asaas (cliente): {err}"}), 500

    cobranca, err = asaas_criar_cobranca(customer_id, valor, desc_pix)
    if not cobranca:
        return jsonify({"erro": f"Asaas (cobrança): {err}"}), 500
    payment_id = cobranca.get("id")

    try:
        r = requests.get(f"{BASE_URL}/v3/payments/{payment_id}/pixQrCode",
                         headers=HEADERS, timeout=20)
        if r.status_code >= 400:
            return jsonify({"erro": f"Asaas (QR): {r.text[:300]}"}), 500
        qr = r.json()
    except Exception as e:
        return jsonify({"erro": f"Falha no QR: {e}"}), 500

    email_user = (data.get("email") or "").strip().lower()
    pend = ler_json(PIX_FILE, {})
    pend[payment_id] = {"email": email_user, "valor": valor,
                        "criado_em": datetime.now().isoformat(), "status": "PENDING"}
    salvar_json(PIX_FILE, pend)

    return jsonify({"payment_id": payment_id, "encodedImage": qr.get("encodedImage", ""),
                    "payload": qr.get("payload", ""),
                    "expirationDate": qr.get("expirationDate", "")})


@app.route("/api/verificar-pagamento/<payment_id>")
def verificar_pagamento(payment_id):
    try:
        r = requests.get(f"{BASE_URL}/v3/payments/{payment_id}", headers=HEADERS, timeout=20)
        if r.status_code >= 400: return jsonify({"erro": r.text[:300]}), 500
        d = r.json(); status = d.get("status")
        if status in ("RECEIVED", "CONFIRMED", "RECEIVED_IN_CASH"):
            pend = ler_json(PIX_FILE, {})
            info = pend.get(payment_id)
            if info and info.get("status") != "PAGO":
                users = ler_json(USERS_FILE, {})
                u = users.get(info["email"])
                if u:
                    u["saldo"] = round(u.get("saldo", 0.0) + info["valor"], 2)
                    u.setdefault("historico", []).insert(0, {
                        "tipo": "Depósito PIX", "valor": info["valor"],
                        "data": datetime.now().isoformat()})
                    u["historico"] = u["historico"][:50]
                    salvar_json(USERS_FILE, users)
                info["status"] = "PAGO"
                info["pago_em"] = datetime.now().isoformat()
                salvar_json(PIX_FILE, pend)
        return jsonify({"status": status, "value": d.get("value")})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


ADMIN_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Admin</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0a0a0a;color:#e5e7eb;font-family:Arial;padding:16px 16px 90px}
h1{color:#d4af37;font-size:22px;margin-bottom:16px}
h2{color:#d4af37;font-size:16px;margin:20px 0 10px}
.tabs{display:flex;gap:8px;margin-bottom:20px;flex-wrap:wrap}
.tab{padding:10px 16px;background:#111;border:1px solid #222;color:#9ca3af;border-radius:8px;cursor:pointer;font-weight:bold}
.tab.ativo{background:#d4af37;color:#000}
.painel{display:none}.painel.ativo{display:block}
.card{background:#111;border:1px solid #222;border-radius:10px;padding:16px;margin-bottom:12px}
label{display:block;font-size:11px;color:#9ca3af;text-transform:uppercase;margin:8px 0 4px;letter-spacing:1px}
input{width:100%;padding:10px;background:#050505;border:1px solid #222;color:#fff;border-radius:8px;font-size:14px;font-family:inherit}
input:focus{outline:none;border-color:#d4af37}
button{padding:10px 16px;border:none;border-radius:8px;font-weight:bold;cursor:pointer;font-size:13px;margin-top:10px}
.btn-gold{background:#d4af37;color:#000}
.btn-red{background:#ef4444;color:#fff}
.btn-green{background:#22c55e;color:#000}
.stats{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}
.stat{background:#111;border:1px solid #222;border-radius:10px;padding:12px;min-width:120px;flex:1}
.stat b{color:#d4af37;display:block;font-size:10px;text-transform:uppercase}
.stat span{font-size:20px;font-weight:bold;color:#22c55e}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:#111;color:#d4af37;padding:8px;text-align:left;border-bottom:1px solid #333;font-size:11px;text-transform:uppercase}
td{padding:8px;border-bottom:1px solid #222;font-size:12px}
tr:hover{background:#111}
.jogo-editor{display:grid;grid-template-columns:80px 1fr auto;gap:10px;align-items:flex-start;background:#0d0d0d;padding:12px;border-radius:8px;border:1px solid #222;margin-bottom:10px}
.jogo-editor img{width:80px;height:80px;object-fit:cover;border-radius:6px;background:#000}
.jogo-editor .campos{display:flex;flex-direction:column;gap:6px}
.jogo-editor .campos input{font-size:12px;padding:8px}
.msg{padding:10px;border-radius:8px;margin-top:10px;font-size:13px;display:none}
.msg.ok{background:#052e16;color:#4ade80;border:1px solid #22c55e;display:block}
.msg.erro{background:#450a0a;color:#f87171;border:1px solid #ef4444;display:block}
.salvar-bar{position:fixed;bottom:0;left:0;right:0;background:#111;padding:12px;border-top:1px solid #333;display:flex;gap:10px}
.salvar-bar button{flex:1;margin:0}
</style></head><body>
<h1>🏛️ Painel Admin</h1>
<div class="tabs">
  <div class="tab ativo" onclick="mostrarAba('stats', this)">📊 Stats</div>
  <div class="tab" onclick="mostrarAba('config', this)">⚙️ Config</div>
  <div class="tab" onclick="mostrarAba('jogos', this)">🎰 Jogos</div>
  <div class="tab" onclick="mostrarAba('users', this)">👥 Usuários</div>
</div>
<div class="painel ativo" id="painel-stats">
  <div class="stats" id="stats"></div>
  <div class="card">
    <h2 style="margin-top:0">💡 Como usar</h2>
    <p style="font-size:13px;color:#9ca3af;line-height:1.6">
      • Aba <b>Config</b>: edite nome, descrição do PIX, banner e cores.<br>
      • Aba <b>Jogos</b>: adicione, edite ou remova jogos.<br>
      • Aba <b>Usuários</b>: veja todos os cadastros.<br>
      • Tudo é salvo em <code>config.json</code>.
    </p>
  </div>
</div>
<div class="painel" id="painel-config">
  <div class="card">
    <h2 style="margin-top:0">🏢 Empresa</h2>
    <label>Nome da empresa</label><input id="cfg_nome">
    <label>Descrição do PIX</label><input id="cfg_desc">
    <label>Emoji do logo</label><input id="cfg_logo">
    <label>Banner</label><input id="cfg_banner">
    <label>Cor dourada</label><input id="cfg_dourado" type="color">
    <label>Cor dourada clara</label><input id="cfg_dourado2" type="color">
  </div>
</div>
<div class="painel" id="painel-jogos">
  <h2>🎰 Lista de Jogos</h2>
  <div id="lista-jogos"></div>
  <button class="btn-green" onclick="addJogo()">➕ Adicionar Jogo</button>
</div>
<div class="painel" id="painel-users">
  <h2>👥 Usuários</h2>
  <div style="overflow-x:auto;"><table id="tabela-users">
    <thead><tr><th>Nome</th><th>E-mail</th><th>CPF</th><th>Saldo</th><th>IP</th><th>Data</th></tr></thead>
    <tbody></tbody>
  </table></div>
</div>
<div class="msg" id="msg"></div>
<div class="salvar-bar">
  <button class="btn-gold" onclick="salvarTudo()">💾 Salvar Tudo</button>
  <button class="btn-gold" onclick="location.reload()" style="max-width:120px;">🔄</button>
</div>
<script>
const SENHA = new URLSearchParams(location.search).get('s');
const AMB = "{AMBIENTE}";
let cfg = {};
function mostrarAba(nome, el){
  document.querySelectorAll('.painel').forEach(p=>p.classList.remove('ativo'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('ativo'));
  document.getElementById('painel-'+nome).classList.add('ativo');
  el.classList.add('ativo');
}
function setMsg(txt, ok){
  const m=document.getElementById('msg'); m.textContent=txt;
  m.className='msg '+(ok?'ok':'erro');
  setTimeout(()=>{m.className='msg';}, 4000);
}
async function carregar(){
  cfg = await (await fetch('/api/config')).json();
  const users = await (await fetch('/api/usuarios')).json();
  const total = Object.keys(users).length;
  const saldoTotal = Object.values(users).reduce((s,u)=>s+(u.saldo||0),0);
  document.getElementById('stats').innerHTML =
    '<div class="stat"><b>Usuários</b><span>'+total+'</span></div>'+
    '<div class="stat"><b>Saldo</b><span>R$ '+saldoTotal.toFixed(2)+'</span></div>'+
    '<div class="stat"><b>Ambiente</b><span style="font-size:14px;">'+AMB+'</span></div>';
  document.getElementById('cfg_nome').value    = cfg.empresa.nome || '';
  document.getElementById('cfg_desc').value    = cfg.empresa.descricao_pix || '';
  document.getElementById('cfg_logo').value    = cfg.empresa.logo_emoji || '';
  document.getElementById('cfg_banner').value  = cfg.banner || '';
  document.getElementById('cfg_dourado').value = (cfg.cores&&cfg.cores.dourado)||'#d4af37';
  document.getElementById('cfg_dourado2').value= (cfg.cores&&cfg.cores.dourado_claro)||'#f0c040';
  renderJogos();
  renderUsers(users);
}
function renderJogos(){
  document.getElementById('lista-jogos').innerHTML = cfg.jogos.map(function(j,i){
    return '<div class="jogo-editor">'+
      '<img src="'+(j.imagem||'')+'">'+
      '<div class="campos">'+
        '<input placeholder="Nome" value="'+(j.nome||'').replace(/"/g,'&quot;')+'" onchange="cfg.jogos['+i+'].nome=this.value">'+
        '<input placeholder="Link" value="'+(j.link||'').replace(/"/g,'&quot;')+'" onchange="cfg.jogos['+i+'].link=this.value">'+
        '<input placeholder="Imagem URL" value="'+(j.imagem||'').replace(/"/g,'&quot;')+'" onchange="cfg.jogos['+i+'].imagem=this.value;renderJogos()">'+
      '</div>'+
      '<button class="btn-red" onclick="remJogo('+i+')" style="margin-top:0">🗑</button>'+
    '</div>';
  }).join('');
}
function addJogo(){ cfg.jogos.push({nome:'', link:'', imagem:''}); renderJogos(); }
function remJogo(i){ if(confirm('Remover?')){ cfg.jogos.splice(i,1); renderJogos(); } }
function renderUsers(users){
  const tb=document.querySelector('#tabela-users tbody');
  const arr = Object.entries(users);
  if(!arr.length){ tb.innerHTML='<tr><td colspan="6">Nenhum.</td></tr>'; return; }
  tb.innerHTML = arr.map(function(p){
    const e=p[0], u=p[1];
    return '<tr><td>'+(u.nome||'—')+'</td><td>'+e+'</td><td>'+(u.cpf||'—')+'</td>'+
      '<td style="color:#22c55e">R$ '+(u.saldo||0).toFixed(2)+'</td>'+
      '<td>'+(u.ip_capturado||'—')+'</td>'+
      '<td style="color:#666">'+((u.criado_em||'').slice(0,16))+'</td></tr>';
  }).join('');
}
async function salvarTudo(){
  cfg.empresa.nome = document.getElementById('cfg_nome').value;
  cfg.empresa.descricao_pix = document.getElementById('cfg_desc').value;
  cfg.empresa.logo_emoji = document.getElementById('cfg_logo').value;
  cfg.banner = document.getElementById('cfg_banner').value;
  cfg.cores = {
    dourado: document.getElementById('cfg_dourado').value,
    dourado_claro: document.getElementById('cfg_dourado2').value
  };
  const r = await fetch('/admin/salvar?s='+SENHA, {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify(cfg)
  });
  if(r.ok) setMsg('✅ Salvo!', true); else setMsg('❌ Erro.', false);
}
carregar();
</script></body></html>"""


@app.route("/admin")
def admin_panel():
    if request.args.get("s", "") != ADMIN_SENHA:
        return """<html><body style='background:#000;color:#fff;font-family:Arial;padding:40px'>
        <h2>🔒 Admin</h2><form method='get'>
        <input name='s' type='password' placeholder='Senha' style='padding:10px;font-size:16px'>
        <button type='submit' style='padding:10px 20px;background:#d4af37;border:none;font-weight:bold'>Entrar</button>
        </form></body></html>""", 401
    return ADMIN_HTML.replace("{AMBIENTE}", AMBIENTE)


@app.route("/admin/salvar", methods=["POST"])
def admin_salvar():
    if request.args.get("s", "") != ADMIN_SENHA:
        return jsonify({"erro": "Senha inválida"}), 401
    salvar_json(CONFIG_FILE, request.get_json() or {})
    return jsonify({"ok": True})


if __name__ == "__main__":
    get_config()
    port = int(os.environ.get("PORT", 8080))
    print("=" * 60)
    print(f"  🏛️  TEMPLE OF GAMES — {AMBIENTE}")
    print(f"  Porta: {port}")
    print(f"  Token: {len(ACCESS_TOKEN)} chars" if ACCESS_TOKEN else "  Token: NÃO CONFIGURADO")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=False)
