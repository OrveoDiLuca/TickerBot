import httpx
import os
from datetime import datetime, timedelta

BASE_URL = "https://finnhub.io/api/v1"


async def get_stock_quote(symbol: str) -> dict:
    api_key = os.getenv("FINNHUB_API_KEY")
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
        import yfinance as yf
        hist = yf.Ticker(symbol.upper()).history(period="3mo", interval="1d")
        if hist.empty:
            return None
        timestamps = [int(ts.timestamp()) for ts in hist.index]
        closes = [round(float(c), 2) for c in hist["Close"].tolist()]
        return {"timestamps": timestamps, "closes": closes}
    except Exception:
        return None


async def get_company_news(symbol: str) -> list:
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
        for item in news[:4]:
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
