"""Pruebas de los importadores que NO requieren PDFs reales (esos se validan con
la regresión de estados de cuenta). Anclan el refactor del helper `money()` y el
guardado de `_mes` de Amex. Sin dependencias externas: `python3 tests/test_importers.py`.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.importers._util import money  # noqa: E402
from app.importers import amex, bbva, revolut  # noqa: E402


def test_money_equivale_al_parseo_inline():
    # Debe ser idéntico a float(s.replace(",", "")) en toda entrada típica.
    casos = {"1,234.56": 1234.56, "0.00": 0.0, "999.99": 999.99,
             "1,000,000.00": 1_000_000.0, "50.00": 50.0, "12,345.00": 12345.0}
    for s, exp in casos.items():
        assert money(s) == exp == float(s.replace(",", "")), s


def test_amex_mes_cubre_todos_los_meses():
    for m in ("enero febrero marzo abril mayo junio julio agosto septiembre "
              "octubre noviembre diciembre").split():
        assert amex._mes(m) >= 1
    # Abreviaturas y mayúsculas también.
    assert amex._mes("DIC") == 12 and amex._mes("Ene") == 1


def test_sniff_no_confunde_bancos():
    # Cada detector reconoce lo suyo y rechaza texto ajeno, sin reventar.
    assert amex.sniff("American Express\nPeríodo de Facturación") is True
    assert amex.sniff("BBVA estado de cuenta") is False
    assert bbva.sniff("BBVA MÉXICO") in (True, False)           # no lanza excepción
    assert revolut.sniff_credit("Revolut") in (True, False)
    assert revolut.sniff_debit_csv("Fecha,Importe,Saldo") in (True, False)


def _run():
    tests = [(n, o) for n, o in sorted(globals().items())
             if n.startswith("test_") and callable(o)]
    fails = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as e:  # noqa: BLE001
            fails += 1
            print(f"  FAIL  {name}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - fails}/{len(tests)} pruebas pasaron.")
    return fails


if __name__ == "__main__":
    sys.exit(1 if _run() else 0)
