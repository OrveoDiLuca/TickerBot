import json
import os
import asyncio
from groq import AsyncGroq
from .finnhub import get_stock_quote, get_company_profile, get_stock_candles, get_company_news, search_symbol
from .sec import get_10k_text, get_10k_accession
from .vector_store import ingest_10k, query_10k
from .yfinance_service import get_fundamentals
from .functios import resolve_ticker_alias, extract_ticker, extract_risk_profile, generate_reply, ASSET_ALIASES, MODEL, QUALITATIVE_TOPICS, RISK_TOPICS, GROWTH_TOPICS


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

    # Paso 2: resolver alias conocido (índice/materia prima) o buscar en Finnhub
    ticker = resolve_ticker_alias(query) or await search_symbol(query)
    if not ticker:
        return {
            "reply": f"No encontré ningún activo para '{query}'. Verifica el nombre o ticker.",
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

    # Paso 2: resolver alias conocido (índice/materia prima) o buscar en Finnhub
    ticker = resolve_ticker_alias(query) or await search_symbol(query)
    if not ticker:
        return {
            "reply": f"No encontré ningún activo para '{query}'. Verifica el nombre o ticker.",
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
        is_etf = ticker in {v for v in ASSET_ALIASES.values()}
        if is_etf:
            reply = (
                f"El análisis fundamental basado en 10-K no aplica para **{ticker}** "
                f"ya que es un ETF o fondo indexado, no una empresa individual. "
                f"Los ETFs no presentan reportes 10-K ante la SEC. "
                f"Para consultar precio, gráfico y noticias usa el análisis de datos de mercado."
            )
        else:
            reply = f"No pude obtener el reporte 10-K de {ticker} desde la SEC."
        return {
            "reply": reply,
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
                    "Usa formato markdown con negritas y listas.\n\n"
                    "7) **Veredicto Final** — al terminar el análisis, genera SIEMPRE esta sección con exactamente este formato:\n\n"
                    "---\n"
                    "## Veredicto Final\n\n"
                    "| Dimensión | Puntuación | Interpretación |\n"
                    "|---|---|---|\n"
                    "| Valoración de la empresa | X/5 | [breve justificación basada en ratios de valoración] |\n"
                    "| Potencial de crecimiento | X/5 | [breve justificación basada en perspectivas y crecimiento de ingresos] |\n"
                    "| Salud financiera | X/5 | [breve justificación basada en deuda, liquidez y flujo de caja] |\n"
                    "| Riesgo de inversión | X/5 | [breve justificación basada en los riesgos identificados] |\n\n"
                    "Criterios de puntuación obligatorios:\n"
                    "- **Valoración de la empresa** (¿está barata o cara?): "
                    "1=extremadamente sobrevalorada, 2=sobrevalorada, 3=valoración justa, 4=algo infravalorada, 5=muy infravalorada. "
                    "Basa el score en P/E, P/B, EV/EBITDA comparados con la industria.\n"
                    "- **Potencial de crecimiento** (¿tiene momentum y perspectivas?): "
                    "1=decrecimiento o sin perspectivas, 2=crecimiento débil, 3=crecimiento moderado, 4=crecimiento sólido, 5=crecimiento excepcional. "
                    "Basa el score en crecimiento de ingresos, EPS y proyectos futuros del 10-K.\n"
                    "- **Salud financiera** (¿puede sostenerse a largo plazo?): "
                    "1=muy frágil (deuda excesiva, flujo negativo), 2=débil, 3=aceptable, 4=sólida, 5=excelente (baja deuda, FCF positivo fuerte). "
                    "Basa el score en Debt/Equity, Current Ratio, Free Cash Flow.\n"
                    "- **Riesgo de inversión** (¿cuánto riesgo asume el inversor?): "
                    "1=riesgo mínimo, 2=bajo riesgo, 3=riesgo moderado, 4=alto riesgo, 5=riesgo muy alto. "
                    "Basa el score en la cantidad y gravedad de riesgos identificados en el 10-K.\n\n"
                    "Después de la tabla agrega una línea de **Conclusión** de máximo 2 oraciones que sintetice el perfil inversor de la empresa."
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
        temperature=0.2, #Le dice al agente que tan determinista sea la respuesta al usuario. 
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

async def recommendation_agent(user_message: str, history: list[dict] | None = None) -> dict:
    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    loop = asyncio.get_running_loop()
    if history is None:
        history = []

    full_history = history + [{"role": "user", "content": user_message}]
    query, risk_profile = await asyncio.gather(
        extract_ticker(client, user_message),
        extract_risk_profile(client, full_history),
    )

    # Si el ticker no está en el mensaje actual, buscarlo en el historial
    if not query:
        for msg in history:
            if msg.get("role") == "user":
                query = await extract_ticker(client, msg["content"])
                if query:
                    break

    if not query:
        return {
            "reply": "No identifiqué ninguna empresa. ¿Puedes especificar cuál acción te interesa?",
            "ticker": None, "chart": None, "news": [], "quote": None,
            "name": None, "exchange": None, "logo": None,
        }
    
    ticker = resolve_ticker_alias(query) or await search_symbol(query)
    if not ticker:
        return {
            "reply": f"No encontré ningún activo para '{query}'. Verifica el nombre o ticker.",
            "ticker": None, "chart": None, "news": [], "quote": None,
            "name": None, "exchange": None, "logo": None,
        }
    ticker = ticker.upper()
    if risk_profile is None: 
        return{
            "reply": "Para darte una recomendación personalizada, ¿cuál es tu perfil como inversor?\n\n**Conservador** — prefieres bajo riesgo y estabilidad.\n**Agresivo** — buscas altos rendimientos y aceptas mayor riesgo",                                                                                                                                                                                                
            "ticker": ticker, "chart": None, "news": [], "quote": None,
            "name": None, "exchange": None, "logo": None,  
        }
    #Obteniendo los 4 datos al mismo tiempo. 
    quote_data, fundamentals_data, profile_data, news_data = await asyncio.gather(
      get_stock_quote(ticker),                                                                                                                                                                                   
      loop.run_in_executor(None, get_fundamentals, ticker),
      get_company_profile(ticker),                                                                                                                                                                               
      get_company_news(ticker),                                                                                                                                                                                  
      return_exceptions=True,
    ) 
    #En caso de que algunas de los datos no funcione. 
    if isinstance(quote_data, Exception):                                                                                                                                                                          
        quote_data = None                                                                                                                                                                                          
    if isinstance(fundamentals_data, Exception):                                                                                                                                                                   
        fundamentals_data = None                                                                                                                                                                                   
    if isinstance(profile_data, Exception):
        profile_data = None
    if isinstance(news_data, Exception):
        news_data = []

    #Construyendo el contexto. 
    current_price = quote_data.get("c") if quote_data else "N/D"
    day_change = f"{quote_data.get('dp', 0):.2f}%" if quote_data else "N/D" 
    company_name = profile_data.get("name") if profile_data else ticker  
    fundamentals_summary = fundamentals_data.get("summary", "No disponible") if fundamentals_data else "No disponible" 

    news_summary = "" 
    if news_data:                                                                                                                                                                                                  
      headlines = [n.get("headline", "") for n in news_data[:3]]
      news_summary = "\n".join(f"- {h}" for h in headlines)

    data_context = (                                                                                                                                                                                               
      f"**Empresa:** {company_name} ({ticker})\n"                                                                                                                                                                
      f"**Precio actual:** ${current_price} (cambio hoy: {day_change})\n\n"
      f"**Métricas fundamentales:**\n{fundamentals_summary}\n\n"                                                                                                                                                 
      f"**Noticias recientes:**\n{news_summary or 'No disponibles'}"                                                                                                                                             
    )

    if risk_profile == "CONSERVATIVE": 
        profile_instruction = (
            "El usuario es un inversor CONSERVADOR. "
            "Enfócate en: estabilidad de ingresos, dividendos, deuda baja (Debt/Equity < 1,"                                                                                                                     
            "flujo de caja positivo, empresa establecida con bajo riesgo. "                                                                                                                                        
            "Penaliza fuertemente alta volatilidad, deuda excesiva o pérdidas netas."
        ) 
    else:
        profile_instruction =(
            "El usuario es un inversor AGRESIVO. "
            "Enfócate en: crecimiento de ingresos, momentum, upside potencial, "                                                                                                                                   
            "sectores de alto crecimiento (tech, biotech, etc.), expansión de mercado. "                                                                                                                           
            "Acepta mayor deuda si el crecimiento lo justifica."
        )
    response = await client.chat.completions.create(
        model = MODEL, 
        messages = [{
            "role": "system",
            "content": (
                "Eres TickerBot, un asesor de inversiones experto. "
                "Responde en el mismo idioma del usuario. "                                                                                                                                                    
                f"{profile_instruction}\n\n"                                                                                                                                                                   
                "Con base en los datos financieros proporcionados, emite una recomendación clara con este formato:\n\n"                                                                                        
                "## Recomendación: [COMPRAR / MANTENER / VENDER]\n\n"                                                                                                                                          
                "**Justificación:** (2-3 puntos clave que sustentan la decisión)\n\n"
                "**Factores a favor:**\n- ...\n\n"                                                                                                                                                             
                "**Factores de riesgo:**\n- ...\n\n"                                                                                                                                                           
                "**Conclusión:** Una oración final adaptada al perfil del inversor.\n\n"                                                                                                                       
                "Sé directo y específico. No uses frases genéricas."  
            ),
        },
        *history, 
        {
            "role": "user",
            "content": f"Datos actuales de {ticker}:\n{data_context}\n\nPregunta del usuario: {user_message}"
        }], 
        temperature = 0.3,
        max_tokens = 1000,
    )
    reply = response.choices[0].message.content or ""

    return {
        "reply": reply,
        "ticker": ticker,
        "chart": None,
        "news": news_data if not isinstance(news_data, Exception) else [],
        "quote": quote_data,
        "name": profile_data.get("name") if profile_data else None,
        "exchange": profile_data.get("exchange") if profile_data else None,
        "logo": profile_data.get("logo") if profile_data else None,
    }


async def ideas_agent(user_message: str, history: list[dict] | None = None) -> dict:
    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    if history is None:
        history = []

    full_history = history + [{"role": "user", "content": user_message}]
    risk_profile = await extract_risk_profile(client, full_history)

    if risk_profile is None:
        return {
            "reply": (
                "¡Claro! Para darte **ideas de inversión personalizadas**, primero necesito conocer tu perfil como inversor:\n\n"
                "**Conservador** — prefieres estabilidad, dividendos y bajo riesgo.\n"
                "**Moderado** — buscas equilibrio entre crecimiento y estabilidad.\n"
                "**Agresivo** — buscas alto crecimiento y aceptas mayor riesgo.\n\n"
                "¿Con cuál te identificas?"
            ),
            "ticker": None, "chart": None, "news": [], "quote": None,
            "name": None, "exchange": None, "logo": None,
        }

    if risk_profile == "CONSERVATIVE":
        profile_label = "CONSERVADOR"
        criteria = (
            "El usuario es un inversor CONSERVADOR. "
            "Recomienda empresas con: dividendos estables y consistentes (yield > 2%), baja volatilidad (beta < 1), "
            "balance sólido, deuda baja o manejable, historial probado de más de 10 años en bolsa. "
            "Sectores preferidos: utilities (servicios públicos), consumer staples (bienes de consumo básico), "
            "salud (farmacéuticas grandes y establecidas), financiero (bancos grandes), REITs de calidad. "
            "Evita empresas especulativas, con pérdidas netas o alta deuda."
        )
    elif risk_profile == "MODERATE":
        profile_label = "MODERADO"
        criteria = (
            "El usuario es un inversor MODERADO. "
            "Recomienda empresas con: crecimiento moderado y sostenible, dividendos opcionales pero valorados, "
            "balance saludable, presencia en sectores con perspectivas sólidas a mediano plazo. "
            "Mezcla sectores defensivos (salud, consumer staples) con sectores de crecimiento estable "
            "(tecnología consolidada, industriales líderes, energía diversificada). "
            "Equilibra rendimiento y estabilidad."
        )
    else:  # AGGRESSIVE
        profile_label = "AGRESIVO"
        criteria = (
            "El usuario es un inversor AGRESIVO. "
            "Recomienda empresas con: alto crecimiento de ingresos (>20% YoY), liderazgo en sectores disruptivos, "
            "gran potencial de upside a largo plazo. "
            "Sectores preferidos: tecnología (IA, cloud, semiconductores), biotecnología, fintech, "
            "energías renovables, mercados emergentes. "
            "Acepta mayor volatilidad y riesgo si el potencial de crecimiento lo justifica."
        )

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres TickerBot, un asesor de inversiones experto. "
                    "Responde en el mismo idioma del usuario. "
                    f"{criteria}\n\n"
                    "Genera una lista de exactamente 6 ideas de inversión usando este formato para cada una:\n\n"
                    "### [Número]. [Nombre completo de la empresa] ([TICKER])\n"
                    "**Sector:** [sector]\n"
                    "**Por qué encaja con tu perfil:** [2-3 oraciones específicas con datos concretos]\n"
                    "**Riesgo principal a tener en cuenta:** [1 oración concreta]\n\n"
                    "Al final, añade una sección **Nota sobre diversificación** de 2-3 oraciones.\n\n"
                    "Usa exclusivamente empresas reales con tickers válidos de NYSE o NASDAQ. "
                    "Sé específico, no uses frases genéricas."
                )
            },
            *history,
            {"role": "user", "content": user_message}
        ],
        temperature=0.4,
        max_tokens=1800,
    )
    reply = response.choices[0].message.content or ""

    return {
        "reply": reply,
        "ticker": None,
        "chart": None,
        "news": [],
        "quote": None,
        "name": None,
        "exchange": None,
        "logo": None,
    }