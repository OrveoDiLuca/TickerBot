import json
import os
import asyncio
from groq import AsyncGroq
from .finnhub import get_stock_quote, get_company_profile, get_stock_candles, get_company_news

SYSTEM_PROMPT = (
    "Eres TickerBot, un asistente de datos financieros. "
    "Cuando el usuario pregunte sobre una acción o empresa, usa las herramientas "
    "disponibles para obtener datos en tiempo real. Responde en el mismo idioma del usuario. "
    "Cuando tengas el perfil de la empresa, siempre debes de mencionar en que bolsa cotiza "
    "esa empresa y que industria pertenece."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_quote",
            "description": "Get the real-time stock quote for a given ticker symbol",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "e.g. AAPL, TSLA"},
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_company_profile",
            "description": "Get company profile information for a given ticker symbol",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "e.g. AAPL, TSLA"},
                },
                "required": ["symbol"],
            },
        },
    },
]


async def execute_tool(name: str, args: dict) -> str:
    try:
        if name == "get_stock_quote":
            return json.dumps(await get_stock_quote(args["symbol"]))
        elif name == "get_company_profile":
            return json.dumps(await get_company_profile(args["symbol"]))
        raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        return json.dumps({"error": str(e)})


async def data_agent(user_message: str) -> dict:
    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    assistant_msg = response.choices[0].message

    if not assistant_msg.tool_calls:
        return {"reply": assistant_msg.content or "", "ticker": None, "chart": None, "news": [], "quote": None}

    messages.append(assistant_msg)

    # Extraer el ticker del primer tool call
    ticker = None
    for tc in assistant_msg.tool_calls:
        args = json.loads(tc.function.arguments)
        if "symbol" in args:
            ticker = args["symbol"].upper()
            break

    for tool_call in assistant_msg.tool_calls:
        args = json.loads(tool_call.function.arguments)
        result = await execute_tool(tool_call.function.name, args)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        })

    final = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
    )
    reply_text = final.choices[0].message.content or ""

    # Obtener gráfica + noticias + quote + perfil en paralelo
    chart_data = None
    news_data = []
    quote_data = None
    profile_data = None
    if ticker:
        chart_data = await asyncio.get_event_loop().run_in_executor(None, get_stock_candles, ticker)
        results = await asyncio.gather(
            get_company_news(ticker),
            get_stock_quote(ticker),
            get_company_profile(ticker),
            return_exceptions=True,
        )
        chart_data = chart_data  # ya obtenido arriba
        news_data = results[0] if not isinstance(results[0], Exception) else []
        quote_data = results[1] if not isinstance(results[1], Exception) else None
        profile_data = results[2] if not isinstance(results[2], Exception) else None

    return {
        "reply": reply_text,
        "ticker": ticker,
        "chart": chart_data,
        "news": news_data,
        "quote": quote_data,
        "name": profile_data.get("name") if profile_data else None,
        "exchange": profile_data.get("exchange") if profile_data else None,
        "logo": profile_data.get("logo") if profile_data else None,
    }
