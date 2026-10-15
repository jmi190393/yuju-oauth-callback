#!/usr/bin/env node
// Reporte de "oportunidades de mejora" (calidad / performance) de las publicaciones
// activas de un vendedor de Mercado Libre. Es la misma informacion que muestra
// vendedores.mercadolibre.com.mx/publicaciones?filters=ACTIVE_WITH_ITEM_PERFORMANCE_OPPORTUNITY
//
// Uso:
//   ML_ACCESS_TOKEN=APP_USR-... node meli/oportunidades.mjs [--limit 50] [--out reporte]
//
// Intercambiar un code de OAuth por token (el code lo muestra index.html):
//   ML_CLIENT_ID=... ML_CLIENT_SECRET=... ML_REDIRECT_URI=https://... \
//     node meli/oportunidades.mjs token <code>
//
// Aplicar cambios desde un archivo JSON (ver meli/cambios.ejemplo.json):
//   ML_ACCESS_TOKEN=... node meli/oportunidades.mjs aplicar cambios.json              # solo vista previa
//   ML_ACCESS_TOKEN=... node meli/oportunidades.mjs aplicar cambios.json --confirmar  # pregunta item por item
//
// Requiere Node 18+ (fetch nativo). El reporte solo lee; unicamente "aplicar --confirmar"
// modifica publicaciones, y antes guarda los valores anteriores para poder revertir.

import { readFile, writeFile } from "node:fs/promises";
import { createInterface } from "node:readline/promises";

const API = "https://api.mercadolibre.com";
const CONCURRENCY = 5;

function arg(name, fallback) {
  const i = process.argv.indexOf(`--${name}`);
  return i > -1 ? process.argv[i + 1] : fallback;
}

async function api(path, { token, method = "GET", body, json, retries = 3 } = {}) {
  const res = await fetch(API + path, {
    method,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(body ? { "Content-Type": "application/x-www-form-urlencoded" } : {}),
      ...(json ? { "Content-Type": "application/json" } : {}),
    },
    body: json ? JSON.stringify(json) : body,
  });
  if (res.status === 429 && retries > 0) {
    await new Promise((r) => setTimeout(r, 2000));
    return api(path, { token, method, body, json, retries: retries - 1 });
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const err = new Error(`${method} ${path} -> ${res.status} ${data?.message || data?.error || ""}`);
    err.status = res.status;
    throw err;
  }
  return data;
}

async function exchangeCode(code) {
  const { ML_CLIENT_ID, ML_CLIENT_SECRET, ML_REDIRECT_URI } = process.env;
  if (!code || !ML_CLIENT_ID || !ML_CLIENT_SECRET || !ML_REDIRECT_URI) {
    throw new Error("Faltan <code>, ML_CLIENT_ID, ML_CLIENT_SECRET o ML_REDIRECT_URI");
  }
  const body = new URLSearchParams({
    grant_type: "authorization_code",
    client_id: ML_CLIENT_ID,
    client_secret: ML_CLIENT_SECRET,
    code,
    redirect_uri: ML_REDIRECT_URI,
  });
  const data = await api("/oauth/token", { method: "POST", body });
  console.log(JSON.stringify(data, null, 2));
}

// Todas las publicaciones activas. search_type=scan evita el tope de offset 1000.
async function activeItemIds(token, userId, limit) {
  const ids = [];
  let scrollId;
  do {
    const qs = new URLSearchParams({ status: "active", search_type: "scan", limit: "100" });
    if (scrollId) qs.set("scroll_id", scrollId);
    const page = await api(`/users/${userId}/items/search?${qs}`, { token });
    ids.push(...page.results);
    scrollId = page.results.length ? page.scroll_id : null;
  } while (scrollId && ids.length < limit);
  return ids.slice(0, limit);
}

async function itemsDetail(token, ids) {
  const out = new Map();
  for (let i = 0; i < ids.length; i += 20) {
    const chunk = ids.slice(i, i + 20);
    const attrs = "id,title,price,permalink,category_id,sold_quantity,available_quantity,listing_type_id,catalog_listing,pictures";
    const rows = await api(`/items?ids=${chunk.join(",")}&attributes=${attrs}`, { token });
    for (const r of rows) if (r.code === 200) out.set(r.body.id, r.body);
  }
  return out;
}

// Reglas pendientes de /item/{id}/performance, aplanadas a una fila por regla.
function pendingRules(perf) {
  const rows = [];
  for (const bucket of perf?.buckets ?? []) {
    for (const variable of bucket.variables ?? []) {
      for (const rule of variable.rules ?? []) {
        if (rule.status === "COMPLETED") continue;
        rows.push({
          bucket: bucket.title || bucket.key,
          variable: variable.title || variable.key,
          rule: rule.key,
          mode: rule.mode || "",
          detail: rule.wordings?.title || rule.wordings?.label || variable.title || rule.key,
          link: rule.wordings?.link || "",
        });
      }
    }
  }
  return rows;
}

async function pool(items, fn) {
  const results = [];
  let next = 0;
  await Promise.all(
    Array.from({ length: CONCURRENCY }, async () => {
      while (next < items.length) {
        const i = next++;
        results[i] = await fn(items[i]);
      }
    }),
  );
  return results;
}

const csvCell = (v) => `"${String(v ?? "").replaceAll('"', '""')}"`;

async function report() {
  const token = process.env.ML_ACCESS_TOKEN;
  if (!token) throw new Error("Define ML_ACCESS_TOKEN (token APP_USR-... del vendedor)");
  const limit = Number(arg("limit", Infinity));
  const outBase = arg("out", "reporte-oportunidades");

  const me = await api("/users/me", { token });
  console.error(`Vendedor: ${me.nickname} (${me.id}, ${me.site_id})`);

  const ids = await activeItemIds(token, me.id, limit);
  console.error(`Publicaciones activas: ${ids.length}. Consultando calidad...`);
  const details = await itemsDetail(token, ids);

  const perf = await pool(ids, async (id) => {
    try {
      return { id, data: await api(`/item/${id}/performance`, { token }) };
    } catch (e) {
      return { id, error: e.message };
    }
  });

  const items = perf
    .map(({ id, data, error }) => ({
      id,
      item: details.get(id) || {},
      score: data?.score ?? null,
      level: data?.level_wording || data?.level || "",
      rules: data ? pendingRules(data) : [],
      error,
    }))
    .filter((x) => x.rules.length || x.error)
    // Primero lo que mas vende con peor calidad: ahi esta el mayor impacto.
    .sort((a, b) => (b.item.sold_quantity || 0) - (a.item.sold_quantity || 0) || (a.score ?? 100) - (b.score ?? 100));

  const csv = [["item_id", "titulo", "precio", "vendidos", "score", "nivel", "seccion", "variable", "regla", "modo", "accion", "link", "permalink"].join(",")];
  for (const x of items) {
    for (const r of x.rules.length ? x.rules : [{ detail: `ERROR: ${x.error}` }]) {
      csv.push(
        [x.id, x.item.title, x.item.price, x.item.sold_quantity, x.score, x.level, r.bucket, r.variable, r.rule, r.mode, r.detail, r.link, x.item.permalink]
          .map(csvCell)
          .join(","),
      );
    }
  }
  await writeFile(`${outBase}.csv`, csv.join("\n"));
  await writeFile(`${outBase}.json`, JSON.stringify(items, null, 2));

  // Resumen: que tipo de problema se repite mas (para atacarlo en lote).
  const byRule = new Map();
  for (const x of items) for (const r of x.rules) {
    const k = `${r.variable} — ${r.detail}`;
    byRule.set(k, (byRule.get(k) || 0) + 1);
  }
  console.log(`\n${items.length} de ${ids.length} publicaciones tienen oportunidades.\n`);
  console.log("Problemas mas frecuentes:");
  for (const [k, n] of [...byRule].sort((a, b) => b[1] - a[1]).slice(0, 15)) console.log(`  ${String(n).padStart(4)}  ${k}`);
  console.log("\nTop 10 a corregir primero (mas vendidas):");
  for (const x of items.slice(0, 10)) {
    console.log(`  ${x.id}  score ${x.score ?? "?"}  ${x.item.title || ""}`);
    for (const r of x.rules) console.log(`      - ${r.detail}`);
    if (x.error) console.log(`      ! ${x.error}`);
  }
  console.log(`\nDetalle completo: ${outBase}.csv y ${outBase}.json`);
}

// ---- Modo aplicar ----
// cambios.json: [{ "id": "MLM123", "title": "...", "attributes": [{ "id": "BRAND", "value_name": "..." }],
//                  "description": "texto plano" }]  — cada campo es opcional.

const attrValue = (a) => a?.value_name ?? (a?.value_id ? `#${a.value_id}` : "");
const short = (s, n = 160) => (s.length > n ? `${s.slice(0, n)}…` : s);

// Compara lo pedido contra lo publicado; devuelve solo lo que realmente cambia.
async function planChange(token, change) {
  const item = await api(`/items/${change.id}?attributes=id,title,sold_quantity,catalog_listing,status,attributes`, { token });
  const plan = { id: change.id, item, warnings: [], before: { id: change.id } };

  if (change.title != null && change.title !== item.title) {
    plan.title = change.title;
    plan.before.title = item.title;
    if (item.sold_quantity > 0) plan.warnings.push("tiene ventas: Mercado Libre suele rechazar cambios de titulo");
    if (item.catalog_listing) plan.warnings.push("es publicacion de catalogo: el titulo lo define el catalogo");
  }

  const current = new Map((item.attributes ?? []).map((a) => [a.id, a]));
  const attrs = (change.attributes ?? []).filter((a) => {
    const cur = current.get(a.id);
    return !cur || (a.value_name != null ? a.value_name !== cur.value_name : a.value_id !== cur.value_id);
  });
  if (attrs.length) {
    plan.attributes = attrs;
    plan.before.attributes = attrs.map((a) => {
      const cur = current.get(a.id);
      return cur ? { id: a.id, value_id: cur.value_id, value_name: cur.value_name } : { id: a.id, value_name: null };
    });
  }

  if (change.description != null) {
    const desc = await api(`/items/${change.id}/description`, { token }).catch((e) => (e.status === 404 ? {} : Promise.reject(e)));
    if ((desc.plain_text ?? "") !== change.description) {
      plan.description = change.description;
      plan.before.description = desc.plain_text ?? "";
    }
  }
  return plan;
}

function printPlan(plan) {
  console.log(`\n${plan.id}  ${plan.item.title}  (${plan.item.status}, ${plan.item.sold_quantity ?? 0} vendidos)`);
  if (plan.title != null) console.log(`  titulo:\n    - ${plan.before.title}\n    + ${plan.title}  (${plan.title.length} caracteres)`);
  for (const a of plan.attributes ?? []) {
    const prev = plan.before.attributes.find((b) => b.id === a.id);
    console.log(`  atributo ${a.id}: ${attrValue(prev) || "(vacio)"} -> ${attrValue(a)}`);
  }
  if (plan.description != null) {
    console.log(`  descripcion (${plan.before.description.length} -> ${plan.description.length} caracteres):`);
    console.log(`    - ${short(plan.before.description.replace(/\s+/g, " ")) || "(vacia)"}`);
    console.log(`    + ${short(plan.description.replace(/\s+/g, " "))}`);
  }
  for (const w of plan.warnings) console.log(`  ! ${w}`);
}

// Cada parte va en su propia llamada: si ML rechaza el titulo, los atributos y la
// descripcion igual se aplican. Devuelve los valores anteriores solo de lo aplicado.
async function applyPlan(token, plan) {
  const parts = [
    ["attributes", () => api(`/items/${plan.id}`, { token, method: "PUT", json: { attributes: plan.attributes } })],
    ["title", () => api(`/items/${plan.id}`, { token, method: "PUT", json: { title: plan.title } })],
    ["description", () => api(`/items/${plan.id}/description?api_version=2`, { token, method: "PUT", json: { plain_text: plan.description } })],
  ];
  const before = { id: plan.id };
  const errors = [];
  for (const [field, put] of parts) {
    if (plan[field] == null) continue;
    try {
      await put();
      before[field] = plan.before[field];
    } catch (e) {
      errors.push(`${field}: ${e.message}`);
    }
  }
  return { before, errors };
}

async function applyChanges() {
  const token = process.env.ML_ACCESS_TOKEN;
  if (!token) throw new Error("Define ML_ACCESS_TOKEN (token APP_USR-... del vendedor)");
  const file = process.argv[3];
  if (!file) throw new Error("Uso: node meli/oportunidades.mjs aplicar cambios.json [--confirmar]");
  const confirm = process.argv.includes("--confirmar");
  if (confirm && !process.stdin.isTTY) throw new Error("--confirmar necesita una terminal interactiva para preguntar item por item");

  const changes = JSON.parse(await readFile(file, "utf8"));
  const plans = [];
  for (const change of changes) {
    try {
      const plan = await planChange(token, change);
      if (plan.title == null && !plan.attributes && plan.description == null) {
        console.log(`\n${change.id}: sin cambios (ya coincide con lo publicado)`);
        continue;
      }
      printPlan(plan);
      plans.push(plan);
    } catch (e) {
      console.log(`\n${change.id}: ERROR al leer la publicacion: ${e.message}`);
    }
  }

  if (!confirm) {
    console.log(`\nVista previa: ${plans.length} publicaciones con cambios. No se modifico nada.`);
    console.log("Para aplicarlos, repite el comando con --confirmar.");
    return;
  }

  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const undoFile = `revertir-${stamp}.json`;
  const undo = [];
  const rl = createInterface({ input: process.stdin, output: process.stdout });
  let all = false;
  let applied = 0;
  try {
    for (const plan of plans) {
      if (!all) {
        const ans = (await rl.question(`\n¿Aplicar cambios a ${plan.id}? [s]i / [n]o / [t]odos / [q] salir: `)).trim().toLowerCase();
        if (ans === "q") break;
        if (ans === "t") all = true;
        else if (ans !== "s") continue;
      }
      const { before, errors } = await applyPlan(token, plan);
      if (Object.keys(before).length > 1) {
        undo.push(before);
        // Se guarda despues de cada item para no perder el respaldo si algo falla a medias.
        await writeFile(undoFile, JSON.stringify(undo, null, 2));
        applied++;
        console.log(`  ✓ ${plan.id} actualizado: ${Object.keys(before).slice(1).join(", ")}`);
      }
      for (const err of errors) console.log(`  ✗ ${plan.id} ${err}`);
    }
  } finally {
    rl.close();
  }
  console.log(`\n${applied} publicaciones actualizadas.`);
  if (applied) console.log(`Valores anteriores en ${undoFile} (para revertir: aplicar ${undoFile} --confirmar)`);
}

const commands = { token: () => exchangeCode(process.argv[3]), aplicar: applyChanges };
const main = commands[process.argv[2]] || report;
main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
