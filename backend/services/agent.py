import json
import os
import asyncio
from groq import AsyncGroq
from .finnhub import get_stock_quote, get_company_profile, get_stock_candles, get_company_news, search_symbol

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
