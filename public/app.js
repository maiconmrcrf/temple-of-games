const SESSION_KEY = "temple_session_v4";
const VALOR_MINIMO = 5.00;
let CFG = null;

function getSession() { return localStorage.getItem(SESSION_KEY); }
function setSession(e) { localStorage.setItem(SESSION_KEY, e); }
function clearSession() { localStorage.removeItem(SESSION_KEY); }
function BRL(v) { return "R$ " + Number(v).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }

function mostrarView(id) {
  document.querySelectorAll(".view").forEach(v => v.classList.remove("ativo"));
  document.getElementById(id).classList.add("ativo");
  window.scrollTo({ top: 0, behavior: "instant" });
}
function setMsg(id, txt, tipo) {
  const el = document.getElementById(id);
  el.textContent = txt;
  el.className = "auth-msg" + (tipo ? " " + tipo : "");
}
function mascaraCPF(inp) {
  let v = inp.value.replace(/\D/g, "").slice(0, 11);
  v = v.replace(/(\d{3})(\d)/, "$1.$2").replace(/(\d{3})(\d)/, "$1.$2").replace(/(\d{3})(\d{1,2})$/, "$1-$2");
  inp.value = v;
}

async function carregarConfig() {
  try { CFG = await (await fetch("/api/config")).json(); } catch { CFG = null; }
  if (!CFG) return;
  const emp = CFG.empresa || {};
  const nome = emp.nome || "Temple of Games";
  const logo = emp.logo_emoji || "🏛️";
  const partes = nome.split(" ");
  document.getElementById("splashLogo").textContent = logo;
  document.getElementById("splashNome").innerHTML = partes[0].toUpperCase() + "<span>" + partes.slice(1).join(" ").toUpperCase() + "</span>";
  document.getElementById("loginLogo").textContent = logo;
  document.getElementById("cadLogo").textContent = logo;
  document.getElementById("topLogo").innerHTML = partes[0].toUpperCase() + ' <span class="logo-icon">' + logo + '</span> ' + partes.slice(1).join(" ").toUpperCase();
  document.getElementById("footNome").textContent = nome;
  if (CFG.banner) document.getElementById("bannerApp").textContent = CFG.banner;
  if (CFG.cores) {
    const root = document.documentElement.style;
    if (CFG.cores.dourado) root.setProperty("--dourado", CFG.cores.dourado);
    if (CFG.cores.dourado_claro) root.setProperty("--dourado2", CFG.cores.dourado_claro);
  }
  document.getElementById("gameGrid").innerHTML = (CFG.jogos || []).map(j =>
    '<a href="' + (j.link || '#') + '" class="game-card" target="_blank" rel="noopener">' +
    '<img src="' + j.imagem + '" alt="' + j.nome + '"><span>' + j.nome + '</span></a>').join("");
}

async function fazerCadastro(e) {
  e.preventDefault();
  const nome   = document.getElementById("cadNome").value.trim();
  const nasc   = document.getElementById("cadNasc").value;
  const cpf    = document.getElementById("cadCpf").value.trim();
  const email  = document.getElementById("cadEmail").value.trim().toLowerCase();
  const senha  = document.getElementById("cadSenha").value;
  const senha2 = document.getElementById("cadSenha2").value;
  if (nome.split(" ").filter(Boolean).length < 2) return setMsg("msgCadastro", "Informe nome e sobrenome.", "erro");
  if (!nasc) return setMsg("msgCadastro", "Informe a data de nascimento.", "erro");
  if (cpf.replace(/\D/g, "").length !== 11) return setMsg("msgCadastro", "CPF deve ter 11 dígitos.", "erro");
  if (senha.length < 6) return setMsg("msgCadastro", "Senha mín. 6 caracteres.", "erro");
  if (senha !== senha2) return setMsg("msgCadastro", "As senhas não coincidem.", "erro");
  setMsg("msgCadastro", "Criando conta...", "");
  try {
    const r = await fetch("/api/usuarios", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nome, nasc, cpf, email, senha })
    });
    const d = await r.json();
    if (!r.ok) return setMsg("msgCadastro", "❌ " + (d.erro || "Erro"), "erro");
    setMsg("msgCadastro", "✅ Conta criada!", "ok");
    setTimeout(() => { setSession(email); abrirApp(); }, 900);
  } catch (err) { setMsg("msgCadastro", "❌ " + err.message, "erro"); }
}

async function fazerLogin(e) {
  e.preventDefault();
  const email = document.getElementById("loginEmail").value.trim().toLowerCase();
  const senha = document.getElementById("loginSenha").value;
  setMsg("msgLogin", "Verificando...", "");
  try {
    const r = await fetch("/api/login", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, senha })
    });
    const d = await r.json();
    if (!r.ok) return setMsg("msgLogin", "❌ " + (d.erro || "Erro"), "erro");
    setSession(email);
    setMsg("msgLogin", "✅ Bem-vindo!", "ok");
    setTimeout(abrirApp, 400);
  } catch (err) { setMsg("msgLogin", "❌ " + err.message, "erro"); }
}

function sair() {
  if (!confirm("Deseja realmente sair da conta?")) return;
  clearSession(); fecharMenu(); mostrarView("view-splash");
  document.getElementById("loginEmail").value = "";
  document.getElementById("loginSenha").value = "";
  document.getElementById("msgLogin").textContent = "";
}

async function abrirApp() {
  const email = getSession();
  if (!email) return mostrarView("view-splash");
  try {
    const r = await fetch("/api/usuarios/" + encodeURIComponent(email));
    if (!r.ok) { clearSession(); return mostrarView("view-splash"); }
    const u = await r.json();
    document.getElementById("saldoApp").textContent = BRL(u.saldo || 0);
    document.getElementById("sbSaldo").textContent  = BRL(u.saldo || 0);
    document.getElementById("sbNome").textContent   = u.nome;
    document.getElementById("sbEmail").textContent  = u.email;
    mostrarView("view-app");
  } catch { clearSession(); mostrarView("view-splash"); }
}

async function atualizarSaldo() {
  const email = getSession(); if (!email) return;
  try {
    const r = await fetch("/api/usuarios/" + encodeURIComponent(email));
    const u = await r.json();
    document.getElementById("saldoApp").textContent = BRL(u.saldo || 0);
    document.getElementById("sbSaldo").textContent  = BRL(u.saldo || 0);
  } catch {}
}

function abrirMenu() {
  document.getElementById("sidebar").classList.add("ativo");
  document.getElementById("overlay").classList.add("ativo");
}
function fecharMenu() {
  document.getElementById("sidebar").classList.remove("ativo");
  document.getElementById("overlay").classList.remove("ativo");
}
function abrirModal(titulo, corpo) {
  document.getElementById("modalTitulo").textContent = titulo;
  document.getElementById("modalCorpo").innerHTML = corpo;
  document.getElementById("modal").classList.add("ativo");
  fecharMenu();
}
function fecharModal() {
  document.getElementById("modal").classList.remove("ativo");
  if (window._pollTimer) { clearInterval(window._pollTimer); window._pollTimer = null; }
}

async function abrirPerfil() {
  const r = await fetch("/api/usuarios/" + encodeURIComponent(getSession()));
  const u = await r.json();
  abrirModal("Meu Perfil",
    '<label>Nome completo</label><div class="modal-info">' + u.nome + '</div>' +
    '<label>Data de nascimento</label><div class="modal-info">' + (u.nasc || "—") + '</div>' +
    '<label>CPF</label><div class="modal-info">' + (u.cpf || "—") + '</div>' +
    '<label>E-mail</label><div class="modal-info">' + u.email + '</div>' +
    '<label>Saldo atual</label><div class="modal-info"><strong>' + BRL(u.saldo || 0) + '</strong></div>');
}

function abrirDeposito() {
  abrirModal("Depositar via PIX",
    '<p style="font-size:.85rem;color:#9ca3af;margin-bottom:10px;">Informe o valor. Uma cobrança PIX será gerada.</p>' +
    '<label>Valor do depósito (mín. ' + BRL(VALOR_MINIMO) + ')</label>' +
    '<input type="number" id="depValor" placeholder="0,00" min="' + VALOR_MINIMO + '" step="0.01" />' +
    '<button class="btn-gold" onclick="confirmarDeposito()">Gerar QR Code PIX</button>' +
    '<p style="font-size:.72rem;color:#666;margin-top:12px;text-align:center;">⚠️ Demonstração.</p>');
}

async function confirmarDeposito() {
  const v = parseFloat(document.getElementById("depValor").value) || 0;
  if (v < VALOR_MINIMO) return alert("❌ Valor mínimo: " + BRL(VALOR_MINIMO));
  const email = getSession();
  document.getElementById("modalCorpo").innerHTML =
    '<p style="text-align:center;color:#9ca3af;padding:24px 0;"><span class="spinner"></span> Gerando QR Code PIX...</p>';
  try {
    const r = await fetch("/api/criar-pix", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ valor: v, email })
    });
    const data = await r.json();
    if (data.erro) {
      document.getElementById("modalCorpo").innerHTML =
        '<p class="pix-status erro">❌ ' + data.erro + '</p><button class="btn-gold" onclick="abrirDeposito()">Tentar novamente</button>';
      return;
    }
    document.getElementById("modalCorpo").innerHTML =
      '<p style="font-size:.85rem;color:#9ca3af;margin-bottom:10px;text-align:center;">Depósito de <strong style="color:#d4af37;">' + BRL(v) + '</strong></p>' +
      '<div class="pix-qr-box"><img src="data:image/png;base64,' + data.encodedImage + '" alt="QR"></div>' +
      '<label>PIX Copia e Cola</label>' +
      '<textarea class="pix-payload" readonly onclick="this.select()">' + data.payload + '</textarea>' +
      '<button class="btn-gold" onclick="copiarPix()">📋 Copiar Código PIX</button>' +
      '<p class="pix-status" id="pixStatus"><span class="spinner"></span> Aguardando pagamento...</p>';
    iniciarPolling(data.payment_id);
  } catch (err) {
    document.getElementById("modalCorpo").innerHTML =
      '<p class="pix-status erro">❌ ' + err.message + '</p><button class="btn-gold" onclick="abrirDeposito()">Tentar novamente</button>';
  }
}

function copiarPix() {
  const ta = document.querySelector(".pix-payload");
  if (!ta) return;
  ta.select();
  try { document.execCommand("copy"); alert("✅ Copiado!"); }
  catch { navigator.clipboard.writeText(ta.value).then(() => alert("✅ Copiado!"), () => alert("Copie manualmente.")); }
}

function iniciarPolling(payment_id) {
  if (window._pollTimer) clearInterval(window._pollTimer);
  let tentativas = 0;
  window._pollTimer = setInterval(async () => {
    tentativas++;
    if (tentativas > 120) {
      clearInterval(window._pollTimer); window._pollTimer = null;
      const el = document.getElementById("pixStatus");
      if (el) { el.className = "pix-status erro"; el.textContent = "⏱️ Tempo esgotado."; }
      return;
    }
    try {
      const r = await fetch("/api/verificar-pagamento/" + payment_id);
      const d = await r.json();
      if (["RECEIVED","CONFIRMED","RECEIVED_IN_CASH"].includes(d.status)) {
        clearInterval(window._pollTimer); window._pollTimer = null;
        await atualizarSaldo();
        const el = document.getElementById("pixStatus");
        if (el) { el.className = "pix-status ok"; el.textContent = "✅ Pagamento confirmado!"; }
        setTimeout(() => { fecharModal(); alert("✅ Pagamento confirmado!"); }, 1200);
      }
    } catch {}
  }, 5000);
}

function abrirSaque() {
  abrirModal("Sacar",
    '<label>Valor do saque</label><input type="number" id="saqValor" placeholder="0,00" min="1" step="0.01" />' +
    '<button class="btn-gold" onclick="confirmarSaque()">Solicitar Saque</button>' +
    '<p style="font-size:.72rem;color:#666;margin-top:12px;text-align:center;">⚠️ Demonstração.</p>');
}
async function confirmarSaque() {
  const v = parseFloat(document.getElementById("saqValor").value) || 0;
  if (v <= 0) return alert("Informe um valor válido.");
  const email = getSession();
  try {
    const r = await fetch('/api/usuarios/' + encodeURIComponent(email) + '/saldo', {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ delta: -v, motivo: "Saque" })
    });
    const d = await r.json();
    if (!r.ok) return alert("❌ " + (d.erro || "Erro"));
    if (d.saldo < 0) {
      await fetch('/api/usuarios/' + encodeURIComponent(email) + '/saldo', {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ delta: v, motivo: "Estorno saque" })
      });
      return alert("❌ Saldo insuficiente.");
    }
    await atualizarSaldo(); fecharModal();
    alert("✅ Saque de " + BRL(v) + " solicitado!");
  } catch (err) { alert("Erro: " + err.message); }
}

async function abrirHistorico() {
  const r = await fetch("/api/usuarios/" + encodeURIComponent(getSession()) + "/historico");
  const h = await r.json();
  const html = !h.length
    ? '<div class="hist-empty">Nenhuma movimentação.</div>'
    : h.map(item => {
        const dt = new Date(item.data).toLocaleString("pt-BR");
        const cls = item.valor >= 0 ? "val-pos" : "val-neg";
        const sinal = item.valor >= 0 ? "+" : "−";
        return '<div class="hist-item"><span>' + item.tipo + '<br><small style="color:#666">' + dt + '</small></span>' +
               '<span class="' + cls + '">' + sinal + ' ' + BRL(Math.abs(item.valor)) + '</span></div>';
      }).join("");
  abrirModal("Histórico", html);
}

function abrirLinks() {
  abrirModal("Links Úteis",
    '<a href="https://templeofgames.com" target="_blank" style="text-decoration:none;"><div class="modal-info" style="margin-bottom:8px;"><strong>🏛️ Temple of Games</strong><br><small>Site oficial</small></div></a>' +
    '<a href="https://www.pragmaticplay.com/br/" target="_blank" style="text-decoration:none;"><div class="modal-info" style="margin-bottom:8px;"><strong>🎰 Pragmatic Play</strong><br><small>Provedor</small></div></a>' +
    '<a href="https://www.pgsoft.com/" target="_blank" style="text-decoration:none;"><div class="modal-info"><strong>🐯 PG Soft</strong><br><small>Provedor</small></div></a>');
}
function abrirSuporte() {
  abrirModal("Suporte",
    '<label>E-mail</label><div class="modal-info">suporte@templeofgames.demo</div>' +
    '<label>WhatsApp</label><div class="modal-info">+55 (11) 99999-0000</div>' +
    '<label>Horário</label><div class="modal-info">24h / 7 dias</div>');
}

(async function init() {
  await carregarConfig();
  if (getSession()) setTimeout(abrirApp, 300);
})();
