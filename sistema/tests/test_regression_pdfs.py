"""Regresión con estados de cuenta REALES (si están disponibles).

Importa todos los archivos de la carpeta indicada en FINANZAS_PDFS (o la ruta
por defecto de la sesión) contra una base limpia y valida:
  - Cada archivo importable concilia al centavo (reconciled=True).
  - El patrimonio y el MSI pendiente cuadran con el análisis documentado.
  - Vuelca un hash del resultado completo de parseo (para comparar refactors).

Si la carpeta no existe (p. ej. en PythonAnywhere), se salta con código 0.
Uso:  python3 tests/test_regression_pdfs.py
"""
import hashlib
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PDF_DIR = os.environ.get(
    "FINANZAS_PDFS",
    "/root/.claude/uploads/5ff39287-14ad-5994-ad64-dce986c50959")

# Cifras oficiales del análisis (docs 08 y 09 de la bóveda).
PATRIMONIO_ESPERADO = 3_532_045
MSI_PENDIENTE_ESPERADO = 136_602
TOLERANCIA = 5  # pesos, por redondeos de captura


def main():
    if not os.path.isdir(PDF_DIR):
        print(f"SKIP: no hay carpeta de PDFs ({PDF_DIR}) — regresión no aplicable aquí.")
        return 0

    os.environ["DATABASE_URL"] = "sqlite:///" + tempfile.mktemp(suffix=".db")
    from app.main import app
    from app.importers import detect_and_parse

    files = sorted(os.listdir(PDF_DIR))
    c = app.test_client()
    r = c.post("/api/login", json={"user": "jaime", "password": "finanzas2026"})
    assert r.status_code == 200, "login falló"

    imported, skipped, failures, parse_dump = [], [], [], {}
    for fn in files:
        path = os.path.join(PDF_DIR, fn)
        if not os.path.isfile(path):
            continue
        # 1) Parseo directo (para el hash de comparación entre refactors)
        try:
            parsed = detect_and_parse(path, fn)
            parse_dump[fn] = parsed
        except ValueError:
            skipped.append(fn)          # banco no soportado (CETES, GBM, CSF…)
            continue
        except Exception as e:          # noqa: BLE001 — un crash es fallo real
            failures.append((fn, f"CRASH parse: {type(e).__name__}: {e}"))
            continue
        # 2) Import end-to-end por el endpoint real
        with open(path, "rb") as fh:
            r = c.post("/api/import", data={"file": (fh, fn)},
                       content_type="multipart/form-data")
        if r.status_code != 200:
            failures.append((fn, f"HTTP {r.status_code}: {r.get_json()}"))
            continue
        res = r.get_json()
        if res.get("reconciled") is False:
            failures.append((fn, f"NO CONCILIA: {res.get('reconciliation')}"))
        imported.append(fn)

    # Hash estable del parseo completo: ancla para verificar refactors.
    blob = json.dumps(parse_dump, sort_keys=True, ensure_ascii=True, default=str)
    digest = hashlib.sha256(blob.encode()).hexdigest()[:16]

    d = c.get("/api/dashboard").get_json()
    patrimonio = d["cuanto_valgo"]["patrimonio_mxn"]
    msi = d["cuanto_valgo"]["msi_pendiente"]

    print(f"Importados y conciliados: {len(imported)}  ·  No importables: {len(skipped)}")
    print(f"Hash de parseo: {digest}")
    print(f"Patrimonio: ${patrimonio:,.2f} (esperado ~${PATRIMONIO_ESPERADO:,})")
    print(f"MSI pendiente: ${msi:,.2f} (esperado ~${MSI_PENDIENTE_ESPERADO:,})")
    ok = True
    for fn, why in failures:
        ok = False
        print(f"  FAIL  {fn}: {why}")
    if abs(patrimonio - PATRIMONIO_ESPERADO) > TOLERANCIA:
        ok = False
        print("  FAIL  patrimonio no cuadra")
    if abs(msi - MSI_PENDIENTE_ESPERADO) > TOLERANCIA:
        ok = False
        print("  FAIL  MSI pendiente no cuadra")
    print("RESULTADO:", "OK" if ok else "FALLO")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
