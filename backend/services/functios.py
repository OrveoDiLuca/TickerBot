from groq import AsyncGroq
import json

MODEL = "llama-3.3-70b-versatile"

# Mapeo de aliases comunes (materias primas, índices) a sus tickers ETF
ASSET_ALIASES: dict[str, str] = {
    # Oro / Gold
    "oro": "GLD", "gold": "GLD", "xau": "GLD", "xauusd": "GLD",
    # Petróleo / Oil
    "petróleo": "USO", "petroleo": "USO", "oil": "USO", "crude": "USO",
    "wti": "USO", "brent": "BNO",
    # Plata / Silver
    "plata": "SLV", "silver": "SLV",
    # S&P 500
    "s&p 500": "VOO", "s&p500": "VOO", "sp500": "VOO", "s&p": "VOO",
    # Nasdaq
    "nasdaq": "QQQ", "nasdaq 100": "QQQ", "nasdaq100": "QQQ",
    # Dow Jones
    "dow jones": "DIA", "djia": "DIA", "dow": "DIA",
    # Russell 2000
    "russell 2000": "IWM", "russell": "IWM",
    # VIX
    "vix": "VIXY",
}

# Temas cualitativos generales — contexto estratégico y de negocio
QUALITATIVE_TOPICS = [
    "competitive advantage moat brand differentiation barriers to entry",
    "management strategy capital allocation priorities",
    "environmental social governance ESG sustainability",
]

# Temas de perspectivas de crecimiento — orientados al futuro, no a productos actuales
GROWTH_TOPICS = [
    "future product upcoming launch plan will introduce next generation announced roadmap",
    "new technology under development plan intend will invest artificial intelligence machine learning",
    "expected revenue growth forecast guidance future outlook anticipate project next year",
    "geographic market expansion plan intend will enter new region country emerging market target",
    "research development pipeline future innovation invest will develop next generation platform",
    "upcoming service product category planned future initiative will launch introduce",
    "strategic priority future investment area focus intend allocate capital next years plan",
    "new segment business unit future potential growth opportunity plan will expand",
]

# Temas de riesgo específicos — se consultan con más chunks para mayor profundidad
RISK_TOPICS = [
    "manufacturing concentration geographic risk country supplier single source",
    "antitrust monopoly regulatory investigation platform competition law enforcement",
    "revenue concentration product segment dependence single product category percentage",
    "key person risk executive leadership CEO management retention talent departure",
    "regulatory payment services financial regulation platform fees legislation government",
    "supply chain disruption geopolitical tariff trade restriction export control sanction",
    "macroeconomic risk inflation interest rate currency foreign exchange recession",
    "cybersecurity data privacy breach intellectual property theft attack vulnerability",
    "litigation legal proceedings pending lawsuits settlement class action damages",
    "competition market share rival substitute technology disruption new entrant",
    "share buyback repurchase program treasury stock equity reduction stockholders deficit",
]

def resolve_ticker_alias(query: str) -> str | None:
    """Resuelve aliases de materias primas e índices a sus tickers ETF equivalentes."""
    if query:
        return ASSET_ALIASES.get(query.lower().strip())
    return None


async def extract_ticker(client: AsyncGroq, user_message: str) -> str | None:
    """Le pide al modelo que extraiga el ticker, nombre de empresa, materia prima o índice del mensaje del usuario."""
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Extrae el activo financiero mencionado en el mensaje del usuario. "
                    "Puede ser: nombre de empresa, ticker, materia prima (oro, petróleo, plata) o índice bursátil (S&P 500, Nasdaq, Dow Jones). "
                    "Responde ÚNICAMENTE con un JSON como: {\"query\": \"Apple\"}, {\"query\": \"AAPL\"}, "
                    "{\"query\": \"oro\"}, {\"query\": \"S&P 500\"} o {\"query\": \"Nasdaq\"}. "
                    "Si no hay ningún activo financiero mencionado, responde: {\"query\": null}. "
                    "Sin explicaciones, solo el JSON."
                ),
            },
            {"role": "user", "content": user_message},
        ],
        temperature=0,
        max_tokens=30,
        response_format={"type": "json_object"},
    )
    try:
        data = json.loads(response.choices[0].message.content or "{}")
        return data.get("query")
    except Exception:
        return None


async def generate_reply(client: AsyncGroq, user_message: str, ticker: str, quote: dict, profile: dict) -> str:
    """Genera una respuesta en lenguaje natural con los datos obtenidos."""
    context = f"Ticker: {ticker}\n"
    if profile:
        context += f"Empresa: {profile.get('name')}, Bolsa: {profile.get('exchange')}, Industria: {profile.get('finnhubIndustry')}\n"
    if quote:
        context += f"Precio actual: ${quote.get('c')}, Cambio: {quote.get('d')} ({quote.get('dp')}%)\n"

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres TickerBot, un asistente de datos financieros. "
                    "Responde en el mismo idioma del usuario usando los datos proporcionados. "
                    "El activo puede ser una acción, ETF, índice bursátil (S&P 500, Nasdaq, etc.) o materia prima (oro, petróleo, plata). "
                    "Menciona el precio actual, el cambio del día y, si está disponible, la bolsa y la industria. "
                    "Si es un índice o ETF, contextualiza qué representa ese activo."
                ),
            },
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": f"Datos obtenidos:\n{context}"},
            {"role": "user", "content": "Con esos datos, responde al usuario de forma clara y concisa."},
        ],
        temperature=0.3,
        max_tokens=300,
    )
    return response.choices[0].message.content or ""


async def extract_risk_profile(client: AsyncGroq, history: list[dict]) -> str | None:
    """Analiza el historial y extrae el perfil de riesgo del usuario (CONSERVATIVE, MODERATE o AGGRESSIVE)."""
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Analiza el historial de la conversación y determina si el usuario ya indicó su perfil de riesgo como inversor. "
                    "Responde ÚNICAMENTE con un JSON con lo siguiente: "
                    "{\"risk_profile\": \"CONSERVATIVE\"} si el usuario dijo que es conservador, cauteloso, prefiere bajo riesgo, estabilidad o dividendos. "
                    "{\"risk_profile\": \"MODERATE\"} si dijo que es moderado, equilibrado, prefiere balance entre crecimiento y estabilidad. "
                    "{\"risk_profile\": \"AGGRESSIVE\"} si dijo que es arriesgado, agresivo, busca altos rendimientos o crecimiento. "
                    "{\"risk_profile\": null} si el usuario todavía no ha indicado su perfil de riesgo. "
                    "Sin explicaciones, solo el JSON."
                )
            },
            *history
        ],
        temperature=0,
        max_tokens=20,
        response_format={"type": "json_object"},
    )
    try:
        data = json.loads(response.choices[0].message.content or "{}")
        return data.get("risk_profile")
    except Exception:
        return None
