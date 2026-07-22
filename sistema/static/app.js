/* SPA — Finanzas personales y familiares. Sin dependencias, es-MX. */
"use strict";

const $app = document.getElementById("app");
const $tabbar = document.getElementById("tabbar");
const state = { user: null, categories: [], accounts: [], view: "inicio" };

const fmt = new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN" });
const money = (n) => fmt.format(n ?? 0);
const fdate = (iso) => new Date(iso + "T12:00:00").toLocaleDateString("es-MX", { day: "numeric", month: "short" });
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

async function api(path, opts = {}) {
  if (opts.body && !(opts.body instanceof FormData)) {
    opts.headers = { "Content-Type": "application/json", ...opts.headers };
    opts.body = JSON.stringify(opts.body);
  }
  const r = await fetch("/api" + path, opts);
  if (r.status === 401) { state.user = null; renderLogin(); throw new Error("sesión"); }
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || "Error de servidor");
  return data;
}

function toast(msg) {
  const t = document.createElement("div");
  t.className = "toast"; t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 2600);
}

/* ---------- login ---------- */

function renderLogin() {
  $tabbar.classList.add("hidden");
  $app.innerHTML = `
  <div class="login-wrap">
    <h1>💰 Finanzas familiares</h1>
    <p class="sub">De Jaime y Nurit</p>
    <div class="card">
      <label>Usuario</label>
      <input id="lu" autocomplete="username" placeholder="jaime o nurit">
      <label>Contraseña</label>
      <input id="lp" type="password" autocomplete="current-password">
      <div class="mt"><button class="btn-block" id="lbtn">Entrar</button></div>
      <div class="error" id="lerr"></div>
    </div>
  </div>`;
  const go = async () => {
    try {
      const r = await api("/login", { method: "POST", body: { user: lu.value, password: lp.value } });
      if (r.must_change_password) toast("Recuerda cambiar tu contraseña en Más → Seguridad");
      await boot();
    } catch (e) { lerr.textContent = e.message; }
  };
  lbtn.onclick = go;
  lp.addEventListener("keydown", (e) => e.key === "Enter" && go());
}

/* ---------- shell ---------- */

async function boot() {
  try { state.user = await api("/me"); } catch { return; }
  [state.categories, state.accounts] = await Promise.all([api("/categories"), api("/accounts")]);
  $tabbar.classList.remove("hidden");
  show(state.view);
}

function show(view) {
  state.view = view;
  document.querySelectorAll(".tabbar button").forEach((b) =>
    b.classList.toggle("active", b.dataset.view === view));
  ({ inicio: renderInicio, movs: renderMovs, capturar: renderCapturar,
     presupuesto: renderPresupuesto, mas: renderMas }[view] || renderInicio)();
}
$tabbar.addEventListener("click", (e) => {
  const b = e.target.closest("button");
  if (b) show(b.dataset.view);
});

/* ---------- inicio: las 5 preguntas ---------- */

async function renderInicio() {
  $app.innerHTML = `<div class="loading">Cargando…</div>`;
  const d = await api("/dashboard");
  const cv = d.como_voy, nw = d.cuanto_valgo;
  const hoy = new Date().toLocaleDateString("es-MX", { weekday: "long", day: "numeric", month: "long" });
  $app.innerHTML = `
  <h1>Hola, ${esc(d.usuario)} 👋</h1>
  <p class="sub" style="margin:-8px 2px 14px;text-align:left">${hoy}</p>

  ${d.por_catalogar ? `<div class="card accent">
    <div class="q">📝 Movimientos por catalogar</div>
    <div class="big">${d.por_catalogar}</div>
    <div class="sub">El sistema no supo su categoría. <a id="gocat">Revisar y enseñarle ›</a></div>
  </div>` : ""}

  <div class="card">
    <div class="q">¿Cuánto tengo? (líquido)</div>
    <div class="big">${money(d.cuanto_tengo.liquido)}</div>
    <div class="sub">BBVA + Revolut + efectivo. No incluye inversiones.</div>
  </div>

  <div class="card">
    <div class="q">¿Cómo voy este mes? <span class="pill ${cv.semaforo}">${cv.semaforo}</span></div>
    <div class="big">${money(cv.sobrante_real_proyectado)} <small>sobrante proyectado</small></div>
    <div class="sub">Gastado ${money(cv.gasto_real)} · MSI del mes ${money(cv.msi_mes)} · plan de sobrante ${money(cv.sobrante_plan)}</div>
  </div>

  ${cv.puedo_gastar_hoy ? `<div class="card">
    <div class="q">¿Puedo gastar hoy?</div>
    <div class="big ${cv.puedo_gastar_hoy.por_dia < 0 ? "neg" : ""}">${money(cv.puedo_gastar_hoy.por_dia)} <small>al día</small></div>
    <div class="sub">${cv.puedo_gastar_hoy.disponible_mes < 0
      ? "Vas por encima de tu plan este mes. Con calma los próximos días."
      : `Libre para el resto del mes: ${money(cv.puedo_gastar_hoy.disponible_mes)} en ${cv.puedo_gastar_hoy.dias_restantes} días (ya restados fijos, seguros y MSI).`}</div>
  </div>` : ""}

  <div class="card">
    <div class="q">¿Qué viene? (30 días)</div>
    ${d.que_viene.map((u) => `
      <div class="row"><div class="l">
        <div class="name">${esc(u.label)}</div><div class="meta">${fdate(u.date)}</div></div>
        <div class="amt">${u.amount ? money(u.amount) : ""}</div></div>`).join("") ||
      '<div class="sub">Nada programado próximo.</div>'}
  </div>

  <div class="card">
    <div class="q">¿Cómo van mis metas?</div>
    ${d.metas.map((g) => `
      <div class="row"><div class="l" style="flex:1">
        <div class="name">${g.emoji} ${esc(g.name)}</div>
        <div class="bar"><i style="width:${Math.min(g.pct, 100)}%"></i></div>
        <div class="meta">${money(g.current_amount)} de ${money(g.target_amount)} (${g.pct}%)</div>
      </div></div>`).join("")}
  </div>

  <div class="card">
    <div class="q">¿Cuánto valgo?</div>
    <div class="big">${money(nw.patrimonio_mxn)}</div>
    <div class="sub">Patrimonio líquido/invertido (USD a $${nw.tc_usd}) − MSI pendiente ${money(nw.msi_pendiente)}</div>
  </div>`;
  const gc = document.getElementById("gocat");
  if (gc) gc.onclick = renderPorCatalogar;
}

async function refreshCategories() {
  state.categories = await api("/categories");
}

function catChips(cats) {
  // Categorías gastables, en orden alfabético, + botón para crear una nueva.
  const gastables = cats.filter((c) => c.kind !== "ingreso")
    .sort((a, b) => a.name.localeCompare(b.name, "es"));
  return gastables.map((c) => `<button class="chip" data-cat="${c.id}">${c.emoji} ${esc(c.name)}</button>`).join("")
    + `<button class="chip" data-new="1" style="border-style:dashed">➕ Otra…</button>`;
}

// Selector reutilizable: muestra chips en `slot`; al elegir, asigna al comercio,
// aprende, y deja un estado "✅ En X · Cambiar" para rectificar cuando quieras.
function mountCategoryPicker(slot, desc, { override = false } = {}) {
  slot.innerHTML = `<div class="chips">${catChips(state.categories)}</div>`;
  slot.querySelectorAll(".chip").forEach((chip) => chip.onclick = async () => {
    try {
      let catId = chip.dataset.cat;
      if (chip.dataset.new) {
        const name = (prompt("Nombre de la nueva categoría (ej. Ropa):") || "").trim();
        if (!name) return;
        const nc = await api("/categories", { method: "POST", body: { name } });
        await refreshCategories();
        catId = nc.id;
        if (nc.created) toast(`Categoría "${name}" creada ✅`);
      }
      await api("/categorize-merchant", { method: "POST", body: {
        description: desc, category_id: +catId, remember: true, override } });
      const cat = state.categories.find((c) => c.id === +catId);
      slot.innerHTML = `<div class="sub">✅ En <b>${cat ? cat.emoji + " " + esc(cat.name) : "categoría"}</b> · <a class="chg">Cambiar</a></div>`;
      slot.querySelector(".chg").onclick = () => mountCategoryPicker(slot, desc, { override: true });
      toast("Guardado ✅");
    } catch (e) { toast(e.message); }
  });
}

async function renderPorCatalogar() {
  $app.innerHTML = `<div class="loading">Cargando…</div>`;
  const grupos = await api("/uncategorized");
  if (!grupos.length) {
    $app.innerHTML = `
    <h1>Por catalogar</h1>
    <div class="card"><div class="sub">🎉 ¡Todo catalogado! No hay gastos pendientes.</div></div>
    <div class="card">
      <div class="name">🧹 Limpiar categorías</div>
      <div class="sub mt">Quita las categorías que no usaste en ningún movimiento, para dejar la lista limpia.</div>
      <div class="mt"><button class="btn-line btn-block" id="cleanup">Quitar categorías sin usar</button></div>
    </div>`;
    document.getElementById("cleanup").onclick = doCleanup;
    return;
  }
  $app.innerHTML = `
  <h1>Por catalogar (${grupos.length})</h1>
  <p class="sub" style="margin:0 4px 12px">Toca la categoría de cada comercio (o <b>➕ Otra…</b> para crear una nueva). Si te equivocas, usa <b>Cambiar</b>. El sistema lo recuerda y ya no vuelve a preguntar.</p>
  <div id="glist">${grupos.map((gp) => `
    <div class="card" data-desc="${esc(gp.description)}">
      <div class="name">${gp.direction === "abono" ? "＋ " : ""}${esc(gp.description)}</div>
      <div class="meta">${gp.count} movimiento(s) · ${money(gp.total)}${gp.variants > 1 ? ` · ${gp.variants} variantes` : ""}</div>
      ${gp.refs ? `<div class="meta" style="opacity:.85">📎 ${esc(gp.refs)}</div>` : ""}
      <div class="slot"></div>
    </div>`).join("")}</div>
  <div class="mt"><button class="btn-line btn-block" id="cleanup">🧹 Quitar categorías que no uso</button></div>`;
  $app.querySelectorAll(".card[data-desc]").forEach((card) =>
    mountCategoryPicker(card.querySelector(".slot"), card.dataset.desc, { override: false }));
  document.getElementById("cleanup").onclick = doCleanup;
}

async function renderComercios() {
  $app.innerHTML = `
  <h1>Editar categorías</h1>
  <p class="sub" style="margin:0 4px 12px">Busca cualquier comercio y cambia su categoría. Se actualizan todos sus movimientos y el sistema reaprende.</p>
  <div class="card"><input id="mq" placeholder="Busca un comercio… (ej. Uber, Amazon)"></div>
  <div id="mlist"><div class="loading">Cargando…</div></div>`;
  let deb;
  mq.oninput = () => { clearTimeout(deb); deb = setTimeout(load, 300); };
  async function load() {
    const q = mq.value.trim();
    const items = await api("/merchants" + (q ? "?q=" + encodeURIComponent(q) : ""));
    document.getElementById("mlist").innerHTML = items.length ? items.map((m) => `
      <div class="card" data-desc="${esc(m.description)}">
        <div class="name">${esc(m.description)}</div>
        <div class="meta">${m.count} mov · ${money(m.total)} · ahora: ${m.category_emoji} ${esc(m.category)}</div>
        <div class="slot"><a class="chg">Cambiar categoría ›</a></div>
      </div>`).join("") : '<div class="card"><div class="sub">Sin resultados.</div></div>';
    document.querySelectorAll("#mlist .card[data-desc]").forEach((card) => {
      const link = card.querySelector(".chg");
      if (link) link.onclick = () => mountCategoryPicker(card.querySelector(".slot"), card.dataset.desc, { override: true });
    });
  }
  load();
}

async function doCleanup() {
  if (!confirm("¿Quitar las categorías que no tienen ningún movimiento? (No borra nada de tus gastos, solo categorías vacías.)")) return;
  try {
    const r = await api("/categories/cleanup", { method: "POST", body: {} });
    await refreshCategories();
    toast(r.count ? `${r.count} categorías sin usar eliminadas` : "No había categorías sin usar");
    renderPorCatalogar();
  } catch (e) { toast(e.message); }
}

/* ---------- captura rápida ---------- */

function renderCapturar() {
  const cats = state.categories.filter((c) => ["fijo", "variable"].includes(c.kind));
  const accs = state.accounts.filter((a) => a.active && ["debito", "credito", "efectivo"].includes(a.kind));
  $app.innerHTML = `
  <h1>Capturar gasto</h1>
  <div class="card">
    <input id="camt" class="amount-input" type="number" inputmode="decimal" placeholder="$0">
    <input id="cdesc" placeholder="¿En qué fue? (ej. propina valet)" class="mt">
    <label>Categoría</label>
    <div class="chips" id="cchips">
      ${cats.map((c) => `<button class="chip" data-id="${c.id}">${c.emoji} ${esc(c.name)}</button>`).join("")}
    </div>
    <label>Cuenta</label>
    <select id="cacc">
      ${accs.map((a) => `<option value="${a.id}" ${a.kind === "efectivo" ? "selected" : ""}>${esc(a.name)}</option>`).join("")}
    </select>
    <div class="field-grid">
      <div><label>Fecha</label><input id="cdate" type="date" value="${new Date().toISOString().slice(0, 10)}"></div>
      <div><label>Etiquetas</label>
        <div class="chips">
          <button class="chip" data-tag="bebe">👶 bebé</button>
          <button class="chip" data-tag="viaje">✈️ viaje</button>
          <button class="chip" data-tag="facturable">🧾 facturar</button>
        </div></div>
    </div>
    <div class="mt"><button class="btn-block" id="csave">Guardar</button></div>
  </div>
  <p class="sub" style="text-align:center">Tip: si eliges categoría no necesitas descripción — dos toques y listo.</p>`;

  let selCat = null; const selTags = new Set();
  cchips.addEventListener("click", (e) => {
    const b = e.target.closest(".chip"); if (!b) return;
    cchips.querySelectorAll(".chip").forEach((x) => x.classList.remove("sel"));
    b.classList.add("sel"); selCat = +b.dataset.id;
  });
  $app.querySelectorAll("[data-tag]").forEach((b) => b.onclick = () => {
    b.classList.toggle("sel");
    selTags.has(b.dataset.tag) ? selTags.delete(b.dataset.tag) : selTags.add(b.dataset.tag);
  });
  csave.onclick = async () => {
    const amount = parseFloat(camt.value);
    if (!amount) { toast("Pon el monto 🙂"); return; }
    csave.disabled = true;
    try {
      const cat = state.categories.find((c) => c.id === selCat);
      await api("/transactions", { method: "POST", body: {
        amount, description: cdesc.value || (cat ? cat.name : "Gasto"),
        category_id: selCat, account_id: +cacc.value, date: cdate.value,
        tags: [...selTags].join(",") } });
      toast("Guardado ✅"); show("inicio");
    } catch (e) { toast(e.message); csave.disabled = false; }
  };
}

/* ---------- movimientos ---------- */

async function renderMovs(filters = {}) {
  const month = filters.month || new Date().toISOString().slice(0, 7);
  $app.innerHTML = `
  <h1>Movimientos</h1>
  <div class="card">
    <div class="field-grid">
      <div><label>Mes</label><input id="fmonth" type="month" value="${month}"></div>
      <div><label>Buscar</label><input id="fq" placeholder="comercio…" value="${esc(filters.q || "")}"></div>
    </div>
  </div>
  <div id="mlist"><div class="loading">Cargando…</div></div>`;
  fmonth.onchange = () => renderMovs({ ...filters, month: fmonth.value });
  let deb;
  fq.oninput = () => { clearTimeout(deb); deb = setTimeout(() => renderMovs({ ...filters, month: fmonth.value, q: fq.value }), 350); };

  const qs = new URLSearchParams({ month, ...(filters.q ? { q: filters.q } : {}) });
  const txns = await api("/transactions?" + qs);
  const total = txns.filter((t) => t.direction === "cargo").reduce((s, t) => s + t.amount, 0);
  document.getElementById("mlist").innerHTML = `
  <div class="card">
    <div class="sub">${txns.length} movimientos · cargos del filtro: <b>${money(total)}</b></div>
    ${txns.map((t) => `
      <div class="row" data-id="${t.id}"><div class="l">
        <div class="name">${t.category_emoji} ${esc(t.description)}</div>
        <div class="meta">${fdate(t.date)} · ${esc(t.account)} · ${esc(t.category || "sin categoría")}${t.tags ? " · " + esc(t.tags) : ""}</div>
        ${t.notes ? `<div class="meta" style="opacity:.85">📎 ${esc(t.notes)}</div>` : ""}
      </div>
      <div class="amt ${t.direction === "abono" ? "pos" : ""}">${t.direction === "abono" ? "+" : "−"}${money(t.amount)}</div>
      </div>`).join("") || '<div class="sub">Sin movimientos con este filtro.</div>'}
  </div>`;
  document.getElementById("mlist").addEventListener("click", (e) => {
    const row = e.target.closest(".row"); if (!row) return;
    const t = txns.find((x) => x.id === +row.dataset.id);
    if (t) editTxn(t, () => renderMovs(filters));
  });
}

function editTxn(t, done) {
  $app.innerHTML = `
  <h1>Editar movimiento</h1>
  <div class="card">
    <div class="big">${t.direction === "abono" ? "+" : "−"}${money(t.amount)}</div>
    <div class="sub">${esc(t.description)} · ${fdate(t.date)} · ${esc(t.account)}</div>
    ${t.notes ? `<div class="sub">📎 Referencia: ${esc(t.notes)}</div>` : ""}
    <label>Categoría</label>
    <select id="ecat">
      <option value="">— sin categoría —</option>
      ${state.categories.map((c) => `<option value="${c.id}" ${c.id === t.category_id ? "selected" : ""}>${c.emoji} ${esc(c.name)}</option>`).join("")}
    </select>
    <label>Etiquetas (separadas por coma)</label>
    <input id="etags" value="${esc(t.tags)}">
    <label>Factura</label>
    <select id="efact">
      ${["", "pendiente", "facturado", "no_facturable"].map((v) =>
        `<option value="${v}" ${v === t.factura_status ? "selected" : ""}>${v || "—"}</option>`).join("")}
    </select>
    <div class="mt field-grid">
      <button class="btn-line" id="edel">Borrar</button>
      <button id="esave">Guardar</button>
    </div>
  </div>`;
  esave.onclick = async () => {
    await api(`/transactions/${t.id}`, { method: "PATCH", body: {
      category_id: ecat.value ? +ecat.value : null, tags: etags.value, factura_status: efact.value } });
    toast("Actualizado ✅"); done();
  };
  edel.onclick = async () => {
    if (!confirm("¿Borrar este movimiento?")) return;
    await api(`/transactions/${t.id}`, { method: "DELETE" });
    toast("Borrado"); done();
  };
}

/* ---------- presupuesto ---------- */

async function renderPresupuesto() {
  const month = new Date().toISOString().slice(0, 7);
  $app.innerHTML = `<div class="loading">Cargando…</div>`;
  const b = await api("/budget?month=" + month);
  const grupo = (kind, titulo) => {
    const rows = b.categorias.filter((c) => c.kind === kind);
    if (!rows.length) return "";
    return `<h2>${titulo}</h2><div class="card">${rows.map((c) => `
      <div class="row"><div class="l" style="flex:1">
        <div class="name">${c.emoji} ${esc(c.name)}</div>
        ${c.budget ? `<div class="bar"><i class="${c.estado}" style="width:${Math.min((c.spent / c.budget) * 100, 100)}%"></i></div>` : ""}
        <div class="meta">${money(c.spent)}${c.budget ? " de " + money(c.budget) : ""}</div>
      </div></div>`).join("")}</div>`;
  };
  $app.innerHTML = `
  <h1>Presupuesto · ${month}</h1>
  <div class="card">
    <div class="q">La regla del sobrante</div>
    <div class="row"><div class="l name">Ingreso</div><div class="amt pos">${money(b.ingreso)}</div></div>
    <div class="row"><div class="l name">− Fijos (plan)</div><div class="amt">${money(b.fijos_plan)}</div></div>
    <div class="row"><div class="l name">− Aprovisionamiento anual</div><div class="amt">${money(b.aprovisionamiento)}</div></div>
    <div class="row"><div class="l name">− MSI del mes</div><div class="amt">${money(b.msi_mes)}</div></div>
    <div class="row"><div class="l name">− Variables (plan)</div><div class="amt">${money(b.variables_plan)}</div></div>
    <div class="row"><div class="l name"><b>= Sobrante invertible</b></div><div class="amt pos"><b>${money(b.sobrante_plan)}</b></div></div>
    <div class="sub mt">Real: llevas gastado ${money(b.gasto_real)} → sobrante proyectado <b>${money(b.sobrante_real_proyectado)}</b></div>
  </div>
  ${grupo("fijo", "Fijos")}${grupo("variable", "Variables")}${grupo("aprovisionamiento", "Aprovisionamiento")}`;
}

/* ---------- más: submenú ---------- */

function renderMas() {
  $app.innerHTML = `
  <h1>Más</h1>
  <div class="card menu-list" id="menu">
    <div class="row" data-go="asesor"><div class="l name">🤖 Asesor (ahorro e IA)</div><div>›</div></div>
    <div class="row" data-go="catalogar"><div class="l name">📝 Por catalogar</div><div>›</div></div>
    <div class="row" data-go="comercios"><div class="l name">✏️ Editar categorías</div><div>›</div></div>
    <div class="row" data-go="msi"><div class="l name">📆 Pagos a meses (MSI)</div><div>›</div></div>
    <div class="row" data-go="subs"><div class="l name">🔁 Suscripciones</div><div>›</div></div>
    <div class="row" data-go="metas"><div class="l name">🎯 Metas</div><div>›</div></div>
    <div class="row" data-go="cuentas"><div class="l name">🏦 Cuentas y patrimonio</div><div>›</div></div>
    <div class="row" data-go="importar"><div class="l name">📥 Importar estado de cuenta</div><div>›</div></div>
    <div class="row" data-go="seguridad"><div class="l name">🔒 Seguridad</div><div>›</div></div>
    <div class="row" data-go="actualizar"><div class="l name">⬆️ Actualizar programa</div><div>›</div></div>
    <div class="row" data-go="salir"><div class="l name">👋 Cerrar sesión</div><div>›</div></div>
  </div>`;
  menu.addEventListener("click", (e) => {
    const r = e.target.closest("[data-go]"); if (!r) return;
    ({ asesor: renderAsesor,
       catalogar: renderPorCatalogar, comercios: renderComercios, msi: renderMsi,
       subs: renderSubs, metas: renderMetas,
       cuentas: renderCuentas, importar: renderImportar, seguridad: renderSeguridad,
       actualizar: renderActualizar,
       salir: async () => { await api("/logout", { method: "POST" }); renderLogin(); } }[r.dataset.go])();
  });
}

function trendBars(trend) {
  // Mini-gráfica de barras (SVG puro, sin dependencias) del gasto por mes.
  const max = Math.max(...trend.map((t) => t.gasto), 1);
  const W = 300, H = 96, n = trend.length, gap = 10;
  const bw = (W - gap * (n - 1)) / n;
  const mName = (m) => new Date(m + "-15T12:00:00").toLocaleDateString("es-MX", { month: "short" });
  const bars = trend.map((t, i) => {
    const h = Math.max((t.gasto / max) * (H - 22), 2);
    const x = i * (bw + gap), y = H - h - 14;
    const last = i === n - 1;
    return `<rect x="${x}" y="${y}" width="${bw}" height="${h}" rx="4"
      fill="var(--brand)" opacity="${last ? 1 : 0.42}"></rect>
      <text x="${x + bw / 2}" y="${H - 2}" text-anchor="middle"
        font-size="9" fill="var(--muted)">${mName(t.month)}</text>`;
  }).join("");
  return `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Gasto por mes">${bars}</svg>`;
}

async function renderAsesor() {
  $app.innerHTML = `<div class="loading">Cargando…</div>`;
  const ins = await api("/insights");
  const nivel = { bueno: "verde", info: "amarillo", alerta: "rojo" };
  const h = ins.health;
  const salud = h.score >= 80 ? "verde" : h.score >= 60 ? "verde" : h.score >= 40 ? "amarillo" : "rojo";
  const mom = ins.mom || { movers: [] };
  const sugeridas = [
    "¿En qué 3 cosas puedo ahorrar sin sufrir?",
    "¿Cómo elimino mis gastos hormiga este mes?",
    "¿Cuánto debería apartar al mes para el bebé?",
    "¿Voy bien para mi fondo de emergencia?",
  ];
  $app.innerHTML = `
  <h1>Asesor</h1>
  <p class="lead">Consejos automáticos de tus números (gratis) y, si está activado, un
  asesor con inteligencia artificial para optimizar, ahorrar y cazar gastos hormiga.</p>

  ${h ? `
  <div class="card">
    <div class="q">🩺 Salud financiera <span class="pill ${salud}">${esc(h.label)}</span></div>
    <div class="big">${h.score}<small> / 100</small></div>
    <div class="bar mt"><i style="width:${h.score}%"></i></div>
    <div class="comp mt">
      ${h.componentes.map((c) => `
        <div class="comp-row"><span class="meta">${esc(c.name)}</span>
          <span class="bar sm"><i style="width:${c.pct}%"></i></span>
          <span class="meta right">${c.pct}%</span></div>`).join("")}
    </div>
    <div class="sub">Tu colchón cubre ~${h.meses_fondo} meses de gasto. Sube el fondo de
    emergencia y baja las suscripciones para mejorar el número.</div>
    <div class="meta" style="margin-top:8px">Índice propio basado en reglas estándar de
    finanzas personales (ahorro 20% de la regla 50/30/20, fondo de 3–6 meses, deuda 28/36).
    Es una guía, no un puntaje oficial de banco.</div>
  </div>` : ""}

  ${ins.gastos_hormiga_mensual > 0 ? `
  <div class="card">
    <div class="q">🐜 Gastos hormiga (compras chicas frecuentes)</div>
    <div class="big">${money(ins.gastos_hormiga_mensual)}<small> / mes</small></div>
    <div class="sub">≈ ${money(ins.gastos_hormiga_anual)} al año. Este es el goteo que no se
    siente pero suma — el mejor lugar para empezar a ahorrar.</div>
  </div>` : ""}

  ${ins.tips.map((t) => `
  <div class="card">
    <div class="name" style="font-size:1.02rem">${t.icon} ${esc(t.title)}
      <span class="pill ${nivel[t.level] || "amarillo"}">${t.level}</span></div>
    <p class="sub" style="text-align:justify">${esc(t.body)}</p>
  </div>`).join("")}

  ${ins.trend && ins.trend.some((t) => t.gasto > 0) ? `
  <h2>Tendencia de gasto</h2>
  <div class="card">
    ${trendBars(ins.trend)}
    <div class="sub">Gasto real por mes (últimos 6). El mes en curso resaltado.</div>
  </div>` : ""}

  ${mom.movers.length ? `
  <h2>Este mes vs. el pasado</h2>
  <div class="card">
    ${mom.movers.map((m) => `
      <div class="row"><div class="l">
        <div class="name">${m.emoji} ${esc(m.name)}</div>
        <div class="meta">antes ${money(m.prev)}${m.pct !== null ? ` · ${m.diff > 0 ? "+" : ""}${m.pct}%` : ""}</div>
      </div><div class="amt">
        <span class="${m.diff > 0 ? "neg" : "pos"}">${m.diff > 0 ? "▲" : "▼"} ${money(Math.abs(m.diff))}</span>
        <div class="meta right">ahora ${money(m.current)}</div></div></div>`).join("")}
    <div class="sub">Lo que más se movió respecto al mes anterior.</div>
  </div>` : ""}

  ${ins.alertas && ins.alertas.length ? `
  <h2>Cobros inusuales 🚨</h2>
  <div class="card">
    <div class="sub" style="margin-top:0">Cargos mucho más grandes de lo normal para ese
    comercio. Verifica que sean correctos (errores, cargos duplicados o no reconocidos).</div>
    ${ins.alertas.map((a) => `
      <div class="row"><div class="l">
        <div class="name">${esc(a.description)}</div>
        <div class="meta">${fdate(a.date)} · ${a.veces}× lo típico (${money(a.tipico)})</div>
      </div><div class="amt neg">${money(a.amount)}</div></div>`).join("")}
  </div>` : ""}

  ${ins.recurrentes && ins.recurrentes.length ? `
  <h2>Cargos recurrentes detectados</h2>
  <div class="card">
    <div class="sub" style="margin-top:0">Se repiten mes con mes (con monto estable) y NO están
    en tu lista de suscripciones. Revisa si aún los usas o si conviene registrarlos.</div>
    ${ins.recurrentes.map((r) => `
      <div class="row"><div class="l">
        <div class="name">${esc(r.description)}</div>
        <div class="meta">${r.months} meses seguidos</div>
      </div><div class="amt">${money(r.avg)}<div class="meta right">/mes aprox.</div></div></div>`).join("")}
  </div>` : ""}

  ${ins.gastos_hormiga.length ? `
  <h2>Dónde se va el goteo</h2>
  <div class="card">
    ${ins.gastos_hormiga.map((h) => `
      <div class="row"><div class="l">
        <div class="name">${esc(h.description)}</div>
        <div class="meta">${h.count} cargos · ${money(h.avg)} c/u · ${esc(h.category)}</div>
      </div><div class="amt">${money(h.mensual)}<div class="meta right">/mes</div></div></div>`).join("")}
  </div>` : ""}

  <h2>Pregúntale al asesor 🤖</h2>
  <div class="card">
    ${ins.ai_available ? "" : `<div class="note-warn">🔒 <b>IA no activada.</b> Se enciende
      poniendo una clave de Anthropic en el servidor (ver el instructivo de despliegue). Mientras
      tanto, los consejos automáticos de arriba funcionan igual.</div>`}
    <div class="chips" id="sug">
      ${sugeridas.map((q) => `<button class="chip" data-q="${esc(q)}">${esc(q)}</button>`).join("")}
    </div>
    <textarea id="pregunta" rows="2" placeholder="Escribe tu pregunta de dinero…"
      style="width:100%;margin-top:10px"></textarea>
    <div class="mt"><button class="btn" id="preguntar">Preguntar</button></div>
    <div id="respuesta" class="mt"></div>
    <p class="meta" style="margin-top:14px;text-align:justify">Solo se comparte un resumen
    agregado de tus números (totales y categorías) — nunca números de cuenta ni movimientos
    individuales. Es una ayuda para organizar decisiones, no sustituye a un asesor
    financiero o fiscal profesional.</p>
  </div>`;

  const ta = document.getElementById("pregunta");
  document.getElementById("sug").addEventListener("click", (e) => {
    const b = e.target.closest("[data-q]"); if (!b) return;
    ta.value = b.dataset.q; ta.focus();
  });
  document.getElementById("preguntar").onclick = async () => {
    const q = ta.value.trim();
    const out = document.getElementById("respuesta");
    if (!q) { out.innerHTML = `<div class="sub">Escribe una pregunta primero.</div>`; return; }
    out.innerHTML = `<div class="loading">Pensando…</div>`;
    try {
      const r = await api("/advisor", { method: "POST", body: { question: q } });
      out.innerHTML = `<div class="answer ${r.ok ? "" : "muted"}">${esc(r.answer).replace(/\n/g, "<br>")}</div>`;
    } catch (e) {
      out.innerHTML = `<div class="answer muted">${esc(e.message)}</div>`;
    }
  };
}

async function renderMsi() {
  $app.innerHTML = `<div class="loading">Cargando…</div>`;
  const d = await api("/msi");
  const activos = d.plans.filter((p) => p.status === "activo");
  $app.innerHTML = `
  <h1>Pagos a meses (MSI)</h1>
  <div class="card">
    <div class="q">Comprometido total</div>
    <div class="big">${money(d.total_pending)}</div>
    <h2 style="margin-left:0">Flujo próximos 6 meses</h2>
    ${d.committed_next_6.map((m) => `
      <div class="row"><div class="l name">${m.month}</div><div class="amt">${money(m.amount)}</div></div>`).join("")}
  </div>
  <h2>Planes activos (${activos.length})</h2>
  <div class="card">
    ${activos.map((p) => `
      <div class="row"><div class="l">
        <div class="name">${esc(p.merchant)}</div>
        <div class="meta">${esc(p.account)} · ${p.payments_made}/${p.months} pagados · termina ${p.ends}</div>
      </div><div class="amt">${money(p.monthly_payment)}<div class="meta right">/mes</div></div></div>`).join("") ||
      '<div class="sub">Sin planes activos 🎉</div>'}
  </div>
  ${d.plans.some((p) => p.status === "liquidado") ? `<h2>Liquidados</h2><div class="card">${
    d.plans.filter((p) => p.status === "liquidado").map((p) =>
      `<div class="row"><div class="l"><div class="name">${esc(p.merchant)}</div>
       <div class="meta">${esc(p.account)} · ${money(p.total_amount)}</div></div><div>✅</div></div>`).join("")}</div>` : ""}`;
}

async function renderSubs() {
  $app.innerHTML = `<div class="loading">Cargando…</div>`;
  const d = await api("/subscriptions");
  const badge = { activa: "verde", por_confirmar: "amarillo", cancelada: "rojo" };
  $app.innerHTML = `
  <h1>Suscripciones</h1>
  <div class="card">
    <div class="q">Costo anual total (activas)</div>
    <div class="big">${money(d.annual_total_mxn)}</div>
    <div class="sub">≈ ${money(d.annual_total_mxn / 12)} al mes</div>
  </div>
  <div class="card">
    ${d.subscriptions.map((s) => `
      <div class="row"><div class="l">
        <div class="name">${esc(s.name)} <span class="pill ${badge[s.status]}">${s.status.replace("_", " ")}</span></div>
        <div class="meta">${s.currency === "USD" ? "USD " : ""}${s.amount} ${s.frequency}${s.account ? " · " + esc(s.account) : ""}${s.next_renewal ? " · renueva " + fdate(s.next_renewal) : ""}</div>
      </div><div class="amt">${money(s.annual_mxn)}<div class="meta right">/año</div></div></div>`).join("")}
  </div>`;
}

async function renderMetas() {
  $app.innerHTML = `<div class="loading">Cargando…</div>`;
  const goals = await api("/goals");
  $app.innerHTML = `
  <h1>Metas</h1>
  ${goals.map((g) => {
    const p = g.proyeccion || {};
    let proy = "";
    if (p.cumplida) {
      proy = `<div class="note-ok mt">✅ Meta cumplida. ¡Felicidades!</div>`;
    } else {
      const partes = [];
      if (p.aporte_requerido) partes.push(`Para llegar a tu fecha meta, aparta <b>${money(p.aporte_requerido)}/mes</b>.`);
      if (p.fecha_estimada) partes.push(`Si le dedicas tu sobrante actual, la completas ~<b>${fdate(p.fecha_estimada)}</b> (${p.meses_estimados} meses).`);
      if (!partes.length && g.falta > 0) partes.push(`Te faltan <b>${money(g.falta)}</b>. Genera sobrante mensual para proyectar una fecha.`);
      if (partes.length) proy = `<div class="note-proj mt">🔮 ${partes.join(" ")}</div>`;
    }
    return `
  <div class="card">
    <div class="name" style="font-size:1.05rem">${g.emoji} ${esc(g.name)}</div>
    <div class="bar mt"><i style="width:${Math.min(g.pct, 100)}%"></i></div>
    <div class="sub">${money(g.current_amount)} de ${money(g.target_amount)} (${g.pct}%)${g.target_date ? " · para " + fdate(g.target_date) : ""}</div>
    ${g.notes ? `<div class="sub">${esc(g.notes)}</div>` : ""}
    ${proy}
    <div class="mt"><button class="btn-line" data-id="${g.id}" data-cur="${g.current_amount}">Actualizar monto</button></div>
  </div>`;
  }).join("")}`;
  $app.querySelectorAll("[data-id]").forEach((b) => b.onclick = async () => {
    const v = prompt("¿Cuánto llevas ahorrado para esta meta?", b.dataset.cur);
    if (v === null) return;
    await api(`/goals/${b.dataset.id}`, { method: "PATCH", body: { current_amount: parseFloat(v) || 0 } });
    renderMetas();
  });
}

async function renderCuentas() {
  state.accounts = await api("/accounts");
  const groups = [["debito", "Cuentas"], ["credito", "Tarjetas de crédito"],
                  ["inversion", "Inversiones"], ["efectivo", "Efectivo"]];
  $app.innerHTML = `
  <h1>Cuentas y patrimonio</h1>
  ${groups.map(([k, titulo]) => {
    const rows = state.accounts.filter((a) => a.kind === k && a.active);
    if (!rows.length) return "";
    return `<h2>${titulo}</h2><div class="card">${rows.map((a) => `
      <div class="row" data-id="${a.id}"><div class="l">
        <div class="name">${esc(a.name)}</div>
        <div class="meta">${esc(a.institution)}${a.cut_day ? " · corte " + a.cut_day : ""}${a.pay_day ? " · pago " + a.pay_day : ""}${a.balance_date ? " · al " + fdate(a.balance_date) : ""}</div>
      </div><div class="amt">${a.kind === "credito" ? "" : (a.currency === "USD" ? "USD " + a.balance.toLocaleString("es-MX") : money(a.balance))}</div></div>`).join("")}</div>`;
  }).join("")}
  <p class="sub">Toca una cuenta de inversión para actualizar su saldo (del estado de cuenta más reciente).</p>`;
  $app.querySelectorAll(".row[data-id]").forEach((r) => r.onclick = async () => {
    const a = state.accounts.find((x) => x.id === +r.dataset.id);
    if (!a || a.kind === "credito") return;
    const v = prompt(`Saldo actual de ${a.name} (${a.currency}):`, a.balance);
    if (v === null) return;
    await api(`/accounts/${a.id}`, { method: "PATCH", body: { balance: parseFloat(v) || 0 } });
    toast("Saldo actualizado ✅"); renderCuentas();
  });
}

async function renderImportar() {
  $app.innerHTML = `
  <h1>Importar estados de cuenta</h1>
  <div class="card">
    <p class="sub">Sube <b>uno o varios archivos a la vez</b>: PDF de BBVA, Amex Gold/Platinum o Revolut crédito, y el CSV de Revolut débito. El sistema detecta cada banco, concilia contra los totales oficiales y cataloga solo.</p>
    <label class="mt">Archivos (puedes seleccionar varios)</label>
    <input id="ifile" type="file" accept=".pdf,.csv" multiple>
    <div class="mt"><button class="btn-block" id="igo">Importar</button></div>
    <div id="ires"></div>
  </div>
  <h2>Historial</h2>
  <div class="card" id="ihist"><div class="sub">Cargando…</div></div>`;
  igo.onclick = async () => {
    const files = [...ifile.files];
    if (!files.length) { toast("Elige uno o más archivos"); return; }
    igo.disabled = true;
    ires.innerHTML = `<div class="sub mt">Procesando ${files.length} archivo(s)…</div><div id="ilines"></div>`;
    let okc = 0;
    for (const f of files) {
      const fd = new FormData(); fd.append("file", f);
      let line;
      try {
        const r = await api("/import", { method: "POST", body: fd });
        okc++;
        line = `✅ <b>${esc(f.name)}</b> → ${esc(r.account)} · ${r.imported} nuevos, ${r.skipped} repetidos · ${r.reconciled === false ? "⚠️ no cuadra" : "conciliado"}`;
      } catch (e) {
        line = `⛔ <b>${esc(f.name)}</b> → ${esc(e.message)}`;
      }
      document.getElementById("ilines").insertAdjacentHTML("beforeend",
        `<div class="row"><div class="l meta">${line}</div></div>`);
    }
    await api("/recategorize", { method: "POST", body: {} });
    const dash = await api("/dashboard");
    ires.insertAdjacentHTML("beforeend", `<div class="sub mt">Listo: ${okc}/${files.length} importados. ${
      dash.por_catalogar ? `<b>${dash.por_catalogar} movimientos por catalogar</b> → <a id="gocat2">revisar ›</a>` : "Todo catalogado ✅"}</div>`);
    const gc = document.getElementById("gocat2");
    if (gc) gc.onclick = renderPorCatalogar;
    loadHist();
    igo.disabled = false;
  };
  async function loadHist() {
    const hist = await api("/imports");
    ihist.innerHTML = hist.map((b) => `
      <div class="row"><div class="l">
        <div class="name">${esc(b.filename)}</div>
        <div class="meta">${b.bank} · ${b.period[0] || "?"} → ${b.period[1] || "?"} · ${b.imported} nuevos</div>
      </div><div>${b.reconciled === false ? "⚠️" : "✅"}</div></div>`).join("") ||
      '<div class="sub">Aún no has importado estados.</div>';
  }
  loadHist();
}

async function renderActualizar() {
  const v = await api("/version").catch(() => ({ version: "?" }));
  const cmd = "unzip -o ~/finanzas-*.zip -d ~/sistema";
  $app.innerHTML = `
  <h1>Actualizar programa</h1>
  <div class="card">
    <div class="q">Versión instalada</div>
    <div class="big">v${esc(v.version)}</div>
    <div class="sub">Tu información (movimientos, catálogo, metas) NUNCA se borra al actualizar — vive en un archivo aparte que no se toca.</div>
  </div>
  <h2>Cómo actualizar (3 pasos)</h2>
  <div class="card">
    <div class="row"><div class="l"><div class="name">1. Sube el ZIP nuevo</div>
      <div class="meta">En PythonAnywhere → pestaña Files → Upload a file → el zip que te pasé.</div></div></div>
    <div class="row"><div class="l"><div class="name">2. Corre este comando en la consola Bash</div>
      <div class="meta">Reemplaza el código sin tocar tus datos:</div>
      <div class="mt" style="display:flex;gap:8px;align-items:center">
        <code style="flex:1;background:var(--bg);padding:10px 12px;border-radius:10px;font-size:.8rem;overflow:auto">${cmd}</code>
        <button class="btn-line" id="cpcmd">Copiar</button>
      </div></div></div>
    <div class="row"><div class="l"><div class="name">3. Reload</div>
      <div class="meta">Pestaña Web → botón verde Reload. Listo, ya tienes la versión nueva.</div></div></div>
  </div>
  <p class="sub">Nota: nunca necesitas borrar nada. El comando solo sobrescribe los archivos del programa.</p>`;
  document.getElementById("cpcmd").onclick = () => {
    navigator.clipboard.writeText(cmd).then(() => toast("Comando copiado ✅"),
      () => toast("Selecciónalo y cópialo manualmente"));
  };
}

function renderSeguridad() {
  $app.innerHTML = `
  <h1>Seguridad</h1>
  <div class="card">
    <label>Contraseña actual</label><input id="pc" type="password">
    <label>Nueva contraseña (mínimo 8)</label><input id="pn" type="password">
    <div class="mt"><button class="btn-block" id="pgo">Cambiar contraseña</button></div>
    <div class="error" id="perr"></div>
  </div>`;
  pgo.onclick = async () => {
    try {
      await api("/password", { method: "POST", body: { current: pc.value, new: pn.value } });
      toast("Contraseña cambiada ✅"); renderMas();
    } catch (e) { perr.textContent = e.message; }
  };
}

/* ---------- arranque ---------- */

if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
boot().catch(renderLogin);
