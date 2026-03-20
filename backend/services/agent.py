import json
import os
import asyncio
from groq import AsyncGroq
from .finnhub import get_stock_quote, get_company_profile, get_stock_candles, get_company_news, search_symbol
from .sec import get_10k_text, get_10k_accession
from .vector_store import ingest_10k, query_10k
from .yfinance_service import get_fundamentals

MODEL = "llama-3.3-70b-versatile"


async def extract_ticker(client: AsyncGroq, user_message: str) -> str | None:
    """Le pide al modelo que extraiga el ticker o nombre de empresa del mensaje del usuario."""
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Extrae el nombre de empresa o ticker del mensaje del usuario. "
                    "Responde ÚNICAMENTE con un JSON como: {\"query\": \"Apple\"} o {\"query\": \"AAPL\"}. "
                    "Si no hay ninguna empresa o ticker mencionado, responde: {\"query\": null}. "
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
                    "Menciona el precio actual, el cambio del día, la bolsa y la industria."
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


async def data_agent(user_message: str) -> dict:
    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

    # Paso 1: extraer el ticker/empresa del mensaje
    query = await extract_ticker(client, user_message)
    if not query:
        return {
            "reply": "No identifiqué ninguna empresa o ticker en tu mensaje. ¿Puedes especificar cuál acción te interesa?",
            "ticker": None, "chart": None, "news": [], "quote": None,
            "name": None, "exchange": None, "logo": None,
        }

    # Paso 2: buscar el ticker correcto en Finnhub
    ticker = await search_symbol(query)
    if not ticker:
        return {
            "reply": f"No encontré ninguna acción para '{query}'. Verifica el nombre o ticker.",
            "ticker": None, "chart": None, "news": [], "quote": None,
            "name": None, "exchange": None, "logo": None,
        }
    ticker = ticker.upper()

    # Paso 3: obtener todos los datos en paralelo
    chart_data = await asyncio.get_running_loop().run_in_executor(None, get_stock_candles, ticker)
    results = await asyncio.gather(
        get_company_news(ticker),
        get_stock_quote(ticker),
        get_company_profile(ticker),
        return_exceptions=True,
    )
    news_data = results[0] if not isinstance(results[0], Exception) else []
    quote_data = results[1] if not isinstance(results[1], Exception) else None
    profile_data = results[2] if not isinstance(results[2], Exception) else None

    # Paso 4: generar respuesta en lenguaje natural
    reply = await generate_reply(client, user_message, ticker, quote_data, profile_data)

    return {
        "reply": reply,
        "ticker": ticker,
        "chart": chart_data,
        "news": news_data,
        "quote": quote_data,
        "name": profile_data.get("name") if profile_data else None,
        "exchange": profile_data.get("exchange") if profile_data else None,
        "logo": profile_data.get("logo") if profile_data else None,
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


async def fundamental_agent(user_message: str) -> dict:
    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    loop = asyncio.get_running_loop()

    # Paso 1: extraer el ticker del mensaje
    query = await extract_ticker(client, user_message)
    if not query:
        return {
            "reply": "No identifiqué ninguna empresa. ¿Puedes especificar cuál acción te interesa?",
            "ticker": None, "chart": None, "news": [], "quote": None,
            "name": None, "exchange": None, "logo": None,
        }

    # Paso 2: buscar el ticker correcto en Finnhub
    ticker = await search_symbol(query)
    if not ticker:
        return {
            "reply": f"No encontré ninguna acción para '{query}'. Verifica el nombre o ticker.",
            "ticker": None, "chart": None, "news": [], "quote": None,
            "name": None, "exchange": None, "logo": None,
        }
    ticker = ticker.upper()

    # Paso 3: obtener todas las fuentes en paralelo
    (text, accession, fundamentals_data), (quote_data, profile_data) = await asyncio.gather(
        asyncio.gather(
            loop.run_in_executor(None, get_10k_text, ticker),
            loop.run_in_executor(None, get_10k_accession, ticker),
            loop.run_in_executor(None, get_fundamentals, ticker),
        ),
        asyncio.gather(get_stock_quote(ticker), get_company_profile(ticker), return_exceptions=True),
    )

    if not text:
        return {
            "reply": f"No pude obtener el reporte 10-K de {ticker} desde la SEC.",
            "ticker": ticker, "chart": None, "news": [], "quote": None,
            "name": None, "exchange": None, "logo": None,
        }

    if isinstance(quote_data, Exception):
        quote_data = None
    if isinstance(profile_data, Exception):
        profile_data = None

    await loop.run_in_executor(None, ingest_10k, ticker, text)

    # Paso 4: consultar ChromaDB — generales (3), riesgos (5) y crecimiento (5)
    general_results, risk_results, growth_results = await asyncio.gather(
        asyncio.gather(
            *[loop.run_in_executor(None, query_10k, ticker, topic, 3) for topic in QUALITATIVE_TOPICS]
        ),
        asyncio.gather(
            *[loop.run_in_executor(None, query_10k, ticker, topic, 5) for topic in RISK_TOPICS]
        ),
        asyncio.gather(
            *[loop.run_in_executor(None, query_10k, ticker, topic, 5) for topic in GROWTH_TOPICS]
        ),
    )

    # Unir chunks eliminando duplicados y truncando cada uno a 600 caracteres
    seen = set()
    unique_chunks = []  # list of (chunk_index, text, section)

    for chunk_list in general_results:
        for item in chunk_list:
            truncated = item["text"][:600]
            if truncated not in seen:
                seen.add(truncated)
                unique_chunks.append((item["chunk_index"], truncated, "general"))

    for chunk_list in risk_results:
        for item in chunk_list:
            truncated = item["text"][:600]
            if truncated not in seen:
                seen.add(truncated)
                unique_chunks.append((item["chunk_index"], truncated, "risk"))

    for chunk_list in growth_results:
        for item in chunk_list:
            truncated = item["text"][:600]
            if truncated not in seen:
                seen.add(truncated)
                unique_chunks.append((item["chunk_index"], truncated, "growth"))

    # Separar fragmentos por sección para pasarlos al LLM de forma estructurada
    general_parts = [f"[Fragmento {idx}]\n{text}" for idx, text, sec in unique_chunks if sec == "general"]
    risk_parts = [f"[Fragmento {idx}]\n{text}" for idx, text, sec in unique_chunks if sec == "risk"]
    growth_parts = [f"[Fragmento {idx}]\n{text}" for idx, text, sec in unique_chunks if sec == "growth"]

    qualitative_context = (
        "=== CONTEXTO ESTRATÉGICO ===\n"
        + "\n---\n".join(general_parts)
        + "\n\n=== RIESGOS ESPECÍFICOS ===\n"
        + "\n---\n".join(risk_parts)
        + "\n\n=== PERSPECTIVAS DE CRECIMIENTO ===\n"
        + "\n---\n".join(growth_parts)
    )

    # Construir URL SEC EDGAR
    sec_url = (
        f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-K&dateb=&owner=include&count=1"
    )

    # Paso 5: generar el análisis fundamental
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres TickerBot, un analista financiero experto. "
                    "Responde en el mismo idioma del usuario. "
                    "Tienes DOS fuentes de datos con roles estrictamente separados:\n\n"
                    "FUENTE A — MÉTRICAS FINANCIERAS (yfinance): "
                    "Números financieros oficiales: ingresos, márgenes, EPS, deuda, ratios de valoración, ROE, ROA, free cash flow. "
                    "USA EXCLUSIVAMENTE esta fuente para todos los números. Cita cada cifra con '(yfinance)'.\n\n"
                    "FUENTE B — ANÁLISIS CUALITATIVO (10-K SEC EDGAR): "
                    "Contiene TRES subsecciones etiquetadas: "
                    "'=== CONTEXTO ESTRATÉGICO ===' (ventaja competitiva, estrategia), "
                    "'=== RIESGOS ESPECÍFICOS ===' (riesgos detallados del negocio), "
                    "'=== PERSPECTIVAS DE CRECIMIENTO ===' (segmentos, mercados, productos, I+D, tendencias). "
                    "NUNCA uses esta fuente para números financieros. Cita con '(10-K, SEC EDGAR — Frag. N)'.\n\n"
                    "Genera un análisis con estas secciones:\n\n"
                    "1) **Ingresos y Crecimiento** — usa solo yfinance\n\n"
                    "2) **Rentabilidad** — usa solo yfinance. "
                    "ATENCIÓN ROE: Si el ROE supera el 100%, NO lo presentes como señal positiva. "
                    "Aplica este protocolo obligatorio: "
                    "→ Muestra el valor exacto del ROE (yfinance) "
                    "→ Explica en términos simples: un ROE >100% casi siempre significa que el patrimonio contable (equity) es negativo o muy bajo, "
                    "no que la empresa sea extraordinariamente rentable "
                    "→ Busca en los fragmentos de RIESGOS ESPECÍFICOS si hay un programa de recompra de acciones (share buyback/repurchase) "
                    "que esté reduciendo el equity artificialmente; si lo encuentras, cita el fragmento "
                    "→ Muestra el ROA como métrica alternativa y explica que es más representativa de la rentabilidad real en estos casos\n\n"
                    "3) **Salud Financiera** — usa solo yfinance\n\n"
                    "4) **Ratios de Valoración** — usa solo yfinance\n\n"
                    "5) **Riesgos Principales** — usa los fragmentos de RIESGOS ESPECÍFICOS. "
                    "Para cada riesgo: (a) describe el riesgo concreto, (b) cita cualquier porcentaje o concentración del 10-K, "
                    "(c) explica el impacto potencial. Cubre: concentración geográfica/manufactura, regulatorio/antimonopolio, "
                    "concentración de ingresos por producto, dependencia de ejecutivos clave, cadena de suministro. "
                    "Cita el fragmento fuente para cada punto.\n\n"
                    "6) **Perspectivas de Crecimiento** — usa EXCLUSIVAMENTE los fragmentos de '=== PERSPECTIVAS DE CRECIMIENTO ==='. "
                    "PROHIBIDO escribir frases genéricas como: 'se espera que continúe creciendo', 'ha invertido en I+D', "
                    "'tiene una posición sólida', 'busca expandirse', 'apuesta por la innovación'. "
                    "Estas frases aplican a cualquier empresa del mundo y no aportan información. "
                    "SOLO escribe lo que esté explícitamente en los fragmentos. Para cada punto usa este formato: "
                    "→ **[tema concreto]**: [dato específico del fragmento con cifra si existe] (10-K, SEC EDGAR — Frag. N). "
                    "CRÍTICO — SOLO FUTURO: Esta sección es exclusivamente sobre lo que la empresa PLANEA, ANTICIPA o DESARROLLARÁ. "
                    "PROHIBIDO mencionar productos o tecnologías que ya existen y están en el mercado como si fueran perspectivas. "
                    "Si un fragmento habla de un producto existente sin mencionar planes futuros concretos sobre él, ignóralo. "
                    "Solo son válidos fragmentos que contengan palabras como: 'will', 'plan', 'intend', 'expect', 'anticipate', "
                    "'future', 'upcoming', 'next generation', 'under development', 'invest in', o sus equivalentes en español. "
                    "Cubre con lo que encuentres en los fragmentos: "
                    "(a) productos o tecnologías en desarrollo que aún no están en el mercado, con fecha estimada si existe, "
                    "(b) mercados geográficos que planea entrar o donde planea crecer, con objetivos concretos, "
                    "(c) áreas de I+D donde está invirtiendo para el futuro, con monto si está disponible, "
                    "(d) guidance o proyecciones de crecimiento que el management haya declarado, "
                    "(e) nuevos segmentos de negocio o categorías de producto planificadas. "
                    "Si algún punto NO aparece en los fragmentos, escribe: '→ **[tema]**: El 10-K no detalla esta información.' "
                    "Nunca rellenes con suposiciones ni con descripción de productos actuales.\n\n"
                    "Si un dato de yfinance aparece como N/D, indícalo explícitamente. "
                    "Usa formato markdown con negritas y listas."
                ),
            },
            {
                "role": "user",
                "content": f"FUENTE A — Métricas financieras verificadas (yfinance):\n{fundamentals_data['summary']}",
            },
            {
                "role": "user",
                "content": f"FUENTE B — Contexto cualitativo del 10-K de {ticker} (SEC EDGAR):\n{qualitative_context}",
            },
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        max_tokens=2500,
    )
    reply = response.choices[0].message.content or ""

    # Añadir sección de fuentes al final
    sources_section = (
        "\n\n---\n"
        "**Fuentes utilizadas:**\n"
        f"- 📊 **Métricas financieras**: [yfinance](https://finance.yahoo.com/quote/{ticker})\n"
        f"- 📄 **Análisis cualitativo** (10-K anual, SEC EDGAR): [{ticker} — Annual Report - accession {accession}]({sec_url})\n"
    )

    reply += sources_section

    return {
        "reply": reply,
        "ticker": ticker,
        "chart": None,
        "news": [],
        "quote": quote_data,
        "name": profile_data.get("name") if profile_data else None,
        "exchange": profile_data.get("exchange") if profile_data else None,
        "logo": profile_data.get("logo") if profile_data else None,
    }
