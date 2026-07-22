"""Asesoría financiera: consejos automáticos (gratis, local) + asesor con IA (Claude).

La parte de IA usa la API de Claude (modelo por defecto claude-opus-4-8). Solo se
envía un RESUMEN agregado de las finanzas — nunca números de cuenta ni movimientos
individuales. Requiere la variable de entorno ANTHROPIC_API_KEY.
"""
import os

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")

SYSTEM = (
    "Eres un asistente de finanzas personales para una familia mexicana (Jaime y "
    "Nurit, con un bebé en camino). Respondes en español de México, con cifras en "
    "pesos ($1,234.56 MXN). Sé concreto, cálido y práctico: da recomendaciones "
    "accionables basadas SOLO en los datos que te comparto, no inventes cifras. "
    "Cuando sugieras montos, redondea. Estructura la respuesta en pocos puntos "
    "claros. Si detectas concentración de riesgo o un gasto hormiga grande, "
    "menciónalo con tacto. Cierra recordando, en una línea, que eres una ayuda "
    "para organizar decisiones y NO un sustituto de un asesor financiero o fiscal "
    "profesional para decisiones grandes de inversión."
)


def ai_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def ask_advisor(summary: str, question: str) -> str:
    """Llama a Claude con el resumen financiero + la pregunta. Lanza excepción si
    falla (sin API key, sin red, error de API) — el endpoint la traduce a un mensaje."""
    import anthropic  # import diferido: la app funciona aunque no esté instalado

    client = anthropic.Anthropic()  # lee ANTHROPIC_API_KEY del entorno
    msg = client.messages.create(
        model=MODEL,
        max_tokens=1200,
        system=SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Estos son mis números actuales:\n\n{summary}\n\n"
                       f"Mi pregunta: {question}",
        }],
    )
    return "".join(b.text for b in msg.content if b.type == "text").strip()
