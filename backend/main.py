from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from services.agent import data_agent

load_dotenv()

app = FastAPI(title="TickerBot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str


class ChartData(BaseModel):
    timestamps: list[int]
    closes: list[float]


class NewsItem(BaseModel):
    headline: str
    url: str
    source: str
    datetime: int
    image: str = ""
    summary: str = ""


class StockQuote(BaseModel):
    c: float
    d: float
    dp: float


class ChatResponse(BaseModel):
    reply: str
    ticker: str | None = None
    chart: ChartData | None = None
    news: list[NewsItem] = []
    quote: StockQuote | None = None
    name: str | None = None
    exchange: str | None = None
    logo: str | None = None


@app.post("/chat", response_model=ChatResponse) #Registra el endpoint /chat que es el endpoint principal de la aplicacion. 
async def chat(body: ChatRequest):
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    result = await data_agent(body.message)
    return ChatResponse(
        reply=result["reply"],
        ticker=result.get("ticker"),
        chart=ChartData(**result["chart"]) if result.get("chart") else None,
        news=[NewsItem(**n) for n in (result.get("news") or [])],
        quote=StockQuote(
            c=result["quote"].get("c", 0),
            d=result["quote"].get("d", 0),
            dp=result["quote"].get("dp", 0),
        ) if result.get("quote") else None,
        name=result.get("name"),
        exchange=result.get("exchange"),
        logo=result.get("logo"),
    )

@app.get("/health")
def health():
    return {"status": "ok"}
