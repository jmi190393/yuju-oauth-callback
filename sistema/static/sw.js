/* Service worker: acelera la apertura sin arriesgar servir contenido roto.
 * - Navegaciones y API: SIEMPRE red primero; el caché es solo respaldo offline.
 * - Estáticos: se cachean SOLO si la respuesta fue exitosa (r.ok).
 * Subir CACHE_VERSION invalida cachés viejas en el próximo activate.
 */
const CACHE = "finanzas-v2";

self.addEventListener("install", () => self.skipWaiting());

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  const url = new URL(req.url);
  // La API y todo lo que no sea GET del mismo origen va directo a la red.
  if (req.method !== "GET" || url.origin !== self.location.origin || url.pathname.startsWith("/api")) return;

  const isStatic = url.pathname.startsWith("/static/");
  e.respondWith(
    fetch(req)
      .then((r) => {
        if (isStatic && r.ok) {
          const copy = r.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
        }
        return r;
      })
      .catch(() => caches.match(req).then((r) => r || caches.match(req, { ignoreSearch: true })))
  );
});
