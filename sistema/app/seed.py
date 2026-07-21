"""Siembra inicial con los datos REALES del análisis 2026 (docs 01–11 de la bóveda).

Se ejecuta una sola vez (si no hay usuarios). Contraseña inicial de ambos
usuarios: 'finanzas2026' — el sistema pide cambiarla al primer ingreso.
"""
from datetime import date

from sqlalchemy.orm import Session

from .auth import hash_password
from .models import (Account, Category, Goal, MsiPlan, Provision, Setting,
                     Subscription, User)

INITIAL_PASSWORD = "finanzas2026"


def seed(db: Session):
    if db.query(User).count():
        return False

    db.add_all([
        User(email="jmi190393@gmail.com", name="Jaime",
             password_hash=hash_password(INITIAL_PASSWORD)),
        User(email="nurit", name="Nurit",
             password_hash=hash_password(INITIAL_PASSWORD)),
    ])

    accounts = {
        "bbva": Account(name="BBVA Libretón", institution="BBVA", kind="debito",
                        cut_day=14, balance=6496.24, balance_date=date(2026, 7, 14),
                        notes="Cuenta eje: aquí entra la nómina"),
        "amex_gold": Account(name="Amex Gold", institution="American Express", kind="credito",
                             last4="3008", cut_day=8, pay_day=23, in_networth=False,
                             notes="Tarjeta única del día a día (pareja)"),
        "amex_plat": Account(name="Amex Platinum", institution="American Express", kind="credito",
                             last4="1000", cut_day=25, pay_day=17, in_networth=False,
                             notes="MSI automático ≥$6,000 o moneda extranjera"),
        "rev_cred": Account(name="Revolut Crédito", institution="Revolut", kind="credito",
                            last4="9378", pay_day=20, in_networth=False,
                            notes="Corte fin de mes. Solo viajes fuera de México"),
        "rev_deb": Account(name="Revolut Actual", institution="Revolut", kind="debito",
                           balance=10.09, balance_date=date(2026, 6, 27)),
        "rev_inv": Account(name="Revolut Inversión", institution="Revolut", kind="inversion",
                           balance=237762.85, balance_date=date(2026, 6, 30),
                           notes="Fondo Rendimientos Diarios ~8.9% anual, liquidez inmediata. BASE del fondo de emergencia"),
        "cetes": Account(name="Cetes Directo", institution="Cetes Directo", kind="inversion",
                         balance=56277.32, balance_date=date(2026, 6, 30),
                         notes="$2,000/mes domiciliado día ~1"),
        "gbm": Account(name="GBM+ (USD)", institution="GBM", kind="inversion", currency="USD",
                       balance=10609.17, balance_date=date(2026, 6, 30),
                       notes="~94% TQQQ. Contrato MXN CXZ82504 es solo puerta de entrada"),
        "etoro": Account(name="eToro (USD)", institution="eToro", kind="inversion", currency="USD",
                         balance=86713.24, balance_date=date(2026, 7, 19),
                         notes="TQQQ + tecnología. Alta concentración en apalancados ×3"),
        "safra": Account(name="Safra NY (conjunta)", institution="Banco Safra", kind="inversion",
                         currency="USD", balance=77353.21, balance_date=date(2026, 6, 30),
                         notes="Fondo de boda con Nurit. TQQQ 202 títulos + SPXL"),
        "banamex": Account(name="Banamex Descubre", institution="Banamex", kind="credito",
                           last4="5763", cut_day=18, pay_day=8, in_networth=False,
                           notes="POR CANCELAR: primero migrar domiciliaciones de CFE y Gas Natural"),
        "efectivo": Account(name="Efectivo", institution="—", kind="efectivo", balance=0,
                            notes="Propinas, estacionamientos, parte del servicio doméstico"),
    }
    db.add_all(accounts.values())
    db.flush()

    # Presupuestos mensuales calculados con el gasto real ene–jul 2026
    cats = [
        # (nombre, emoji, kind, presupuesto, orden)
        ("Nómina", "💵", "ingreso", None, 1),
        ("Rendimientos de inversión", "📈", "ingreso", None, 2),
        ("Mantenimiento casa", "🏠", "fijo", 21799, 10),
        ("Servicios casa", "💡", "fijo", 3500, 11),
        ("Internet y celular", "📶", "fijo", 1174, 12),
        ("Servicio doméstico", "🧹", "fijo", 6000, 13),
        ("Servicios profesionales", "🧾", "fijo", 2320, 14),
        ("Mascota", "🐕", "fijo", 2200, 15),
        ("Suscripciones", "🔁", "fijo", 1200, 16),
        ("Súper", "🛒", "variable", 12000, 20),
        ("Restaurantes", "🍽️", "variable", 8000, 21),
        ("Comida a domicilio", "🛵", "variable", 4800, 22),
        ("Gasolina y carga", "⛽", "variable", 3000, 23),
        ("Casetas", "🛣️", "variable", 2400, 24),
        ("Uber y transporte", "🚕", "variable", 2000, 25),
        ("Auto — otros", "🚗", "variable", 1500, 26),
        ("Farmacia", "💊", "variable", 3700, 26),
        ("Salud y cuidado personal", "🧠", "variable", 6000, 27),
        ("Bebé y embarazo", "👶", "variable", 8000, 28),
        ("Compras", "🛍️", "variable", 8500, 29),
        ("Ropa", "👕", "variable", 3000, 30),
        ("Regalos", "🎁", "variable", 2000, 31),
        ("Peluquería y salón", "💇", "variable", 1500, 32),
        ("Hogar y muebles", "🛋️", "variable", 2500, 33),
        ("Viajes", "✈️", "variable", 10000, 31),
        ("Efectivo", "💴", "variable", 2000, 32),
        ("Seguros", "🛡️", "aprovisionamiento", 28883, 40),
        ("Impuestos y gobierno", "🏛️", "aprovisionamiento", 2500, 41),
        ("Comisiones bancarias", "🏦", "variable", 200, 42),
        ("Pago de tarjeta", "💳", "transferencia", None, 90),
        ("Transferencia interna", "🔄", "transferencia", None, 91),
        ("Inversión y ahorro", "🌱", "inversion", None, 92),
        ("Familia", "👨‍👩‍👦", "variable", None, 93),
        ("Otros", "❓", "variable", 3000, 99),
    ]
    db.add_all([Category(name=n, emoji=e, kind=k, monthly_budget=b, sort=s)
                for n, e, k, b, s in cats])

    # Los planes MSI NO se siembran: los crean los importadores al subir estados
    # de cuenta (fuente de verdad), evitando duplicados.

    # Suscripciones conocidas (del análisis + respuestas del cuestionario)
    db.add_all([
        Subscription(name="Claude (Anthropic)", amount=3477.96, frequency="anual",
                     account_id=accounts["rev_cred"].id, next_renewal=date(2027, 4, 13),
                     notes="Plan anual, tarjeta virtual wallet"),
        Subscription(name="Apple / iCloud", amount=146, frequency="mensual",
                     account_id=accounts["amex_gold"].id,
                     notes="Promedio de 23 microcargos $49–$399; revisar desglose en Ajustes→Apple ID"),
        Subscription(name="AT&T", amount=675, frequency="mensual",
                     account_id=accounts["amex_gold"].id),
        Subscription(name="Telmex", amount=499, frequency="mensual",
                     account_id=accounts["amex_gold"].id),
        Subscription(name="Amazon Prime", amount=899, frequency="anual",
                     account_id=accounts["amex_gold"].id, status="por_confirmar",
                     notes="No apareció ene–jul; puede ser anual fuera del periodo o mes de prueba"),
        Subscription(name="Obsidian Sync", amount=96, currency="USD", frequency="anual",
                     account_id=accounts["rev_cred"].id, status="por_confirmar",
                     notes="Se cobra en Revolut; anual, no visto ene–jun"),
        Subscription(name="Nutrafol", amount=3576.87, frequency="mensual",
                     account_id=accounts["rev_cred"].id, status="por_confirmar",
                     notes="Suplementos para el pelo — confirmar recurrencia"),
        Subscription(name="OpenAI (ChatGPT)", amount=110, frequency="mensual",
                     account_id=accounts["rev_cred"].id, status="cancelada",
                     notes="Cancelada en marzo 2026"),
    ])

    # Metas (respuestas 23–24 del cuestionario final)
    db.add_all([
        Goal(name="Fondo de emergencia (3 meses)", emoji="🛟", target_amount=450000,
             current_amount=237763, target_date=date(2027, 6, 30),
             notes="Base: Revolut Inversión. Faltan ~$212k"),
        Goal(name="Cuenta del bebé", emoji="👶", target_amount=100000,
             current_amount=0, target_date=date(2026, 11, 11),
             notes="Nace 11/nov/2026. El reporte 'costo primeros 4 meses' se alimenta de la etiqueta bebe"),
        Goal(name="Próximo viaje", emoji="✈️", target_amount=80000, current_amount=0,
             notes="Europa 22/jul–2/ago pagado entre 4 personas; ajustar para el siguiente"),
    ])

    # Aprovisionamiento anual (calendario real de seguros + fiscal)
    db.add_all([
        Provision(name="Bupa GMM (2 pólizas, Jaime y Nurit)", annual_amount=277351,
                  due_months="01,05", notes="Dos exhibiciones semestrales"),
        Provision(name="Qualitas autos (2)", annual_amount=62356, due_months="10,12"),
        Provision(name="Zurich (casa)", annual_amount=6900, due_months="11"),
        Provision(name="Predial + tenencia + verificación", annual_amount=30000,
                  due_months="01", notes="Estimado — ajustar con recibos reales"),
    ])

    db.add_all([
        Setting(key="ingreso_mensual", value="195156"),
        Setting(key="moneda", value="MXN"),
        Setting(key="tc_usd", value="18.50"),
        Setting(key="nombre_sistema", value="Finanzas personales y familiares"),
    ])
    db.commit()
    return True
