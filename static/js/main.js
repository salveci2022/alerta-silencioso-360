// ALERTA SILENCIOSO 360 — Global JS

// ── Relógio em tempo real ──────────────────────────────────────────────────
function updateClock() {
  const el = document.getElementById('clock');
  if (!el) return;
  const now = new Date();
  const pad = n => String(n).padStart(2,'0');
  el.textContent = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
}
setInterval(updateClock, 1000);
updateClock();

// ── Toast notifications ────────────────────────────────────────────────────
function toast(msg, tipo='error', duracao=5000) {
  const container = document.getElementById('toasts') ||
    (() => {
      const d = document.createElement('div');
      d.id = 'toasts';
      d.className = 'alert-popup';
      document.body.appendChild(d);
      return d;
    })();
  const ic = tipo==='success'?'✅':tipo==='info'?'ℹ️':'🚨';
  const div = document.createElement('div');
  div.className = `alert-toast ${tipo}`;
  div.innerHTML = `<span class="alert-toast-ic">${ic}</span><span class="alert-toast-msg">${msg}</span>`;
  container.appendChild(div);
  setTimeout(() => div.remove(), duracao);
}

// ── Modal helpers ──────────────────────────────────────────────────────────
function abrirModal(id) {
  document.getElementById(id)?.classList.add('open');
}
function fecharModal(id) {
  document.getElementById(id)?.classList.remove('open');
}
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
  }
});

// ── Polling status em tempo real ───────────────────────────────────────────
let alertasAtivos = 0;
async function pollStatus() {
  try {
    const r = await fetch('/api/status');
    const data = await r.json();

    // Atualiza counters no dashboard
    ['alertas_ativos','alertas_hoje','incidentes_abertos','sirenes_ativas'].forEach(k => {
      const el = document.getElementById(k);
      if (el) el.textContent = data[k];
    });

    // Banner de alerta ativo
    const banner = document.getElementById('banner-alerta');
    if (banner) {
      if (data.alertas_ativos > 0) {
        banner.style.display = 'flex';
        if (data.alertas_ativos !== alertasAtivos) {
          // Novo alerta detectado
          tocarSom();
        }
      } else {
        banner.style.display = 'none';
      }
    }
    alertasAtivos = data.alertas_ativos;

    // Atualiza horário do último alerta
    const ult = document.getElementById('ultimo_alerta');
    if (ult && data.ultimo_alerta) {
      ult.textContent = data.ultimo_alerta.ts_br || '—';
    }

  } catch(e) { /* silencioso */ }
}

// Inicia polling se estiver no dashboard
if (document.getElementById('alertas_ativos')) {
  pollStatus();
  setInterval(pollStatus, 5000);
}

// ── Som de emergência ──────────────────────────────────────────────────────
let somAtivado = false;
function tocarSom() {
  if (somAtivado) return;
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    function beep(freq, start, duration) {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = freq;
      osc.type = 'sawtooth';
      gain.gain.setValueAtTime(0.3, ctx.currentTime + start);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + start + duration);
      osc.start(ctx.currentTime + start);
      osc.stop(ctx.currentTime + start + duration);
    }
    // Padrão de alerta
    for (let i = 0; i < 3; i++) {
      beep(880, i * 0.4, 0.15);
      beep(660, i * 0.4 + 0.2, 0.15);
    }
    somAtivado = true;
    setTimeout(() => { somAtivado = false; }, 3000);
  } catch(e) { /* sem suporte */ }
}

// ── Sirene contínua ────────────────────────────────────────────────────────
let sireneCtx = null;
let sireneAtiva = false;

function ligarSirene() {
  if (sireneAtiva) return;
  try {
    sireneCtx = new (window.AudioContext || window.webkitAudioContext)();
    sireneAtiva = true;
    let freq = 440;
    let direcao = 1;
    const osc = sireneCtx.createOscillator();
    const gain = sireneCtx.createGain();
    osc.connect(gain);
    gain.connect(sireneCtx.destination);
    gain.gain.value = 0.4;
    osc.type = 'sawtooth';
    osc.start();
    const interval = setInterval(() => {
      if (!sireneAtiva) { osc.stop(); clearInterval(interval); return; }
      freq += direcao * 15;
      if (freq > 1200 || freq < 400) direcao *= -1;
      osc.frequency.value = freq;
    }, 50);
  } catch(e) {}
}

function desligarSirene() {
  sireneAtiva = false;
  if (sireneCtx) { try { sireneCtx.close(); } catch(e){} sireneCtx = null; }
}

// ── Fetch helper ───────────────────────────────────────────────────────────
async function api(url, method='GET', body=null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(url, opts);
  return r.json();
}

// ── Fechar alerta ──────────────────────────────────────────────────────────
async function fecharAlerta(id, btn) {
  if (btn) { btn.disabled = true; btn.textContent = '...'; }
  const data = await api(`/api/sos/fechar/${id}`, 'POST');
  if (data.ok) {
    toast('Alerta encerrado.', 'success', 3000);
    setTimeout(() => location.reload(), 800);
  } else {
    if (btn) { btn.disabled = false; btn.textContent = 'Fechar'; }
  }
}

// ── Toggle sirene ──────────────────────────────────────────────────────────
async function toggleSirene(unitId, btn) {
  const ativa = btn.classList.contains('on');
  const novaAtiva = !ativa;
  const data = await api(`/api/sirene/${unitId}`, 'POST', { ativa: novaAtiva });
  if (data.ok) {
    btn.classList.toggle('on', novaAtiva);
    const label = btn.nextElementSibling;
    if (label) label.textContent = novaAtiva ? '🔴 SIRENE ATIVA' : '';
    if (novaAtiva) { ligarSirene(); toast('Sirene ativada!', 'error'); }
    else { desligarSirene(); toast('Sirene desligada.', 'success', 2000); }
  }
}
