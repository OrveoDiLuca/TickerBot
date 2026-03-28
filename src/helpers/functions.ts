//Funciones utiles para el proyecto. 
import type { ChartPoint } from "../types"
import type { StockData } from "../types"

export function buildChartData(timestamps: number[], closes: number[]): ChartPoint[] {
  return timestamps.map((ts, i) => {
    const d = new Date(ts * 1000)
    const label = d.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    })
    return { time: label, price: closes[i], ts }
  })
}


//Esta funcion realiza tres cosas las cuales son: 
//Envia el mensaje que coloca el usuario al backend. 
//Espera la respues del backend, la cual incluye el texto del bot y los datos de la acción. 
export async function callBackend(
  message: string,
  history: { role: string; content: string }[] = []
): Promise<{ botText: string; stockData: StockData | null }> {
  const apiUrl = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
  const res = await fetch(`${apiUrl}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history }),
  })
  if (!res.ok) throw new Error('Backend error')
  const data = await res.json()

  const stockData: StockData | null = data.ticker
    ? {
        ticker: data.ticker,
        name: data.name ?? null,
        exchange: data.exchange ?? null,
        logo: data.logo ?? null,
        chart: data.chart ?? null,
        news: data.news ?? [],
        quote: data.quote ?? null,
      }
    : null

  return { botText: data.reply, stockData }
}