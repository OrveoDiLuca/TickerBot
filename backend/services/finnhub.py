import httpx
import os
from datetime import datetime, timedelta

BASE_URL = "https://finnhub.io/api/v1"


async def get_stock_quote(symbol: str) -> dict:
    api_key = os.getenv("FINNHUB_API_KEY")#Obtiene el valor de la variable de entorno, que se comunica con FINNHUB_API_KEY. 
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{BASE_URL}/quote",
            params={"symbol": symbol.upper(), "token": api_key},
        )
        r.raise_for_status()
        data = r.json()
        if data.get("c") == 0:
            raise ValueError(f"Invalid ticker symbol: {symbol}")
        return data


async def get_company_profile(symbol: str) -> dict:
    #Obtiene la informacion de la empresa, osea el nombre, el logo, la industria, etc.
    api_key = os.getenv("FINNHUB_API_KEY")
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{BASE_URL}/stock/profile2",
            params={"symbol": symbol.upper(), "token": api_key},
        )
        r.raise_for_status()
        data = r.json()
        if not data.get("name"):
            raise ValueError(f"No company profile found for: {symbol}")
        return data


def get_stock_candles(symbol: str) -> dict | None:
    try:
        #Obtiene el historial de los precios de los ultimos 3 meses. 
        import yfinance as yf
        hist = yf.Ticker(symbol.upper()).history(period="3mo", interval="1d")
        if hist.empty:
            return None
        timestamps = [int(ts.timestamp()) for ts in hist.index]
        closes = [round(float(c), 2) for c in hist["Close"].tolist()]
        return {"timestamps": timestamps, "closes": closes}
    except Exception:
        return None


async def search_symbol(query: str) -> str | None:
    """Busca el ticker correcto dado el nombre de una empresa o un ticker parcial."""
    api_key = os.getenv("FINNHUB_API_KEY")
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{BASE_URL}/search",
            params={"q": query, "token": api_key},
        )
        r.raise_for_status()
        data = r.json()
        results = data.get("result", [])
        # Prioriza coincidencia exacta de símbolo (acciones, ETFs e índices)
        query_upper = query.upper()
        for item in results:
            if item.get("symbol", "").upper() == query_upper and item.get("type") in ("Common Stock", "ETP"):
                return item["symbol"]
        # Luego el primer resultado de tipo "Common Stock"
        for item in results:
            if item.get("type") == "Common Stock":
                return item["symbol"]
        # Luego el primer ETF/ETP (fondos indexados, materias primas)
        for item in results:
            if item.get("type") == "ETP":
                return item["symbol"]
        if results:
            return results[0].get("symbol")
        return None


async def get_company_news(symbol: str) -> list:
    #Obtiene las noticias de la empresa. 
    api_key = os.getenv("FINNHUB_API_KEY")
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{BASE_URL}/company-news",
            params={
                "symbol": symbol.upper(),
                "from": from_date,
                "to": to_date,
                "token": api_key,
            },
        )
        r.raise_for_status()
        news = r.json()
        if not isinstance(news, list):
            return []
        result = []
        for item in news[:8]:
            if item.get("headline"):
                result.append({
                    "headline": item.get("headline", ""),
                    "url": item.get("url", ""),
                    "source": item.get("source", ""),
                    "datetime": item.get("datetime", 0),
                    "image": item.get("image", ""),
                    "summary": item.get("summary", ""),
                })
        return result
