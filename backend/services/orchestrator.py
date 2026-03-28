import os
from groq import Groq
from services.agent import data_agent, fundamental_agent, recommendation_agent, ideas_agent


client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def classify_mssg(message: str) -> str:
    """Le pregunta a la LLM qué tipo de consulta escribió el usuario."""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un clasificador de intenciones para un bot financiero. "
                    "Analiza el mensaje del usuario y responde ÚNICAMENTE con una de estas palabras:\n"
                    "DATA - si pregunta por precio actual, cotización, noticias, o datos generales de una acción\n"
                    "FUNDAMENTAL - si pregunta por análisis fundamental, ingresos, deuda, balances, ratios financieros\n"
                    "RECOMMENDATION - si pide una recomendación de compra, venta o inversión sobre una empresa o activo ESPECÍFICO\n"
                    "IDEAS - si pide ideas generales de inversión, un portafolio, qué empresas comprar, sugerencias sin especificar un activo concreto\n"
                    "UNKNOWN - si no es una consulta financiera sobre acciones\n\n"
                    "Responde solo la palabra, sin explicación."
                ),
            },
            {
                "role": "user",
                "content": message,
            },
        ],
        temperature=0,
        max_tokens=10,
    )
    intent = response.choices[0].message.content.strip().upper()
    valid_intents = ["DATA", "FUNDAMENTAL", "RECOMMENDATION", "IDEAS"]
    if intent not in valid_intents:
        return "UNKNOWN"
    return intent


def _is_pending_recommendation(history: list[dict]) -> bool:
    """Detecta si el bot ya preguntó por el perfil de riesgo para una acción específica."""
    for msg in reversed(history):
        if msg.get("role") == "assistant":
            content = msg.get("content", "")
            return (
                "perfil como inversor" in content
                and "ideas de inversión personalizadas" not in content
            )
    return False


def _is_pending_ideas(history: list[dict]) -> bool:
    """Detecta si el bot ya preguntó por el perfil de riesgo en el contexto de ideas generales."""
    for msg in reversed(history):
        if msg.get("role") == "assistant":
            content = msg.get("content", "")
            return "ideas de inversión personalizadas" in content
    return False


async def orchestrator(message: str, history: list[dict] = []):
    intent = classify_mssg(message)

    if intent == "DATA":
        return await data_agent(message)

    elif intent == "FUNDAMENTAL":
        return await fundamental_agent(message)

    elif intent == "RECOMMENDATION":
        return await recommendation_agent(message, history)

    elif intent == "IDEAS":
        return await ideas_agent(message, history)

    else:
        # El usuario puede estar respondiendo al perfil solicitado en un turno anterior
        if _is_pending_ideas(history):
            return await ideas_agent(message, history)
        if _is_pending_recommendation(history):
            return await recommendation_agent(message, history)
        return {
            "reply": "Solo puedo ayudarte con consultas sobre acciones y mercados financieros.",
            "ticker": None,
            "chart": None,
            "news": [],
            "quote": None,
            "name": None,
            "exchange": None,
            "logo": None,
        }
