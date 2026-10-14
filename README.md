# yuju-oauth-callback
Pagina de callback OAuth temporal para integracion Yuju API

## Oportunidades de mejora en Mercado Libre

`meli/oportunidades.mjs` lista las publicaciones activas con oportunidades de
calidad (lo mismo que el filtro `ACTIVE_WITH_ITEM_PERFORMANCE_OPPORTUNITY` del
panel de vendedores), usando `GET /item/{id}/performance`. Solo lee; no modifica nada.

```bash
# 1. (opcional) cambiar el code de OAuth que muestra index.html por un token
ML_CLIENT_ID=... ML_CLIENT_SECRET=... ML_REDIRECT_URI=https://... \
  node meli/oportunidades.mjs token <code>

# 2. generar el reporte (reporte-oportunidades.csv / .json)
ML_ACCESS_TOKEN=APP_USR-... node meli/oportunidades.mjs
```
