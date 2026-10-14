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
// Requiere Node 18+ (fetch nativo). Solo lee datos: no modifica ninguna publicacion.

import { writeFile } from "node:fs/promises";

const API = "https://api.mercadolibre.com";
const CONCURRENCY = 5;

function arg(name, fallback) {
  const i = process.argv.indexOf(`--${name}`);
  return i > -1 ? process.argv[i + 1] : fallback;
}

async function api(path, { token, method = "GET", body, retries = 3 } = {}) {
  const res = await fetch(API + path, {
    method,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(body ? { "Content-Type": "application/x-www-form-urlencoded" } : {}),
    },
    body,
  });
  if (res.status === 429 && retries > 0) {
    await new Promise((r) => setTimeout(r, 2000));
    return api(path, { token, method, body, retries: retries - 1 });
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

const main = process.argv[2] === "token" ? () => exchangeCode(process.argv[3]) : report;
main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
