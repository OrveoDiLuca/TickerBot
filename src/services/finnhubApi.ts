import { object, string, number, type InferOutput, parse } from 'valibot'

//Este archivo se encarga de interactuar con la API de Finnhub para obtener las cotizaciones de acciones de las empresas que pida el usuario.

//Schema
const FinnhubQuoteSchema = object({
  c: number(),   // current price
  h: number(),   // high
  l: number(),   // low
  o: number(),   // open
  pc: number(),  // previous close
  t: number(),   // timestamp unix
})

const FinnhubProfileSchema = object({
  name: string(),
  ticker: string(),
  exchange: string(),
  marketCapitalization: number(),
  currency: string(),
  country: string(),
  finnhubIndustry: string(),
})

export type FinnhubQuote = InferOutput<typeof FinnhubQuoteSchema>
export type FinnhubProfile = InferOutput<typeof FinnhubProfileSchema>

const API_KEY = import.meta.env.VITE_FINNHUB_API_KEY
const BASE_URL = 'https://finnhub.io/api/v1'

async function finnhubFetch(path: string): Promise<unknown> {
  const url = `${BASE_URL}${path}&token=${API_KEY}`
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Finnhub request failed: ${response.status}`)
  }
  return response.json()
}

export async function getStockQuote(symbol: string): Promise<FinnhubQuote> {
  const raw = await finnhubFetch(`/quote?symbol=${symbol.toUpperCase()}`)
  const result = parse(FinnhubQuoteSchema, raw)
  if (result.c === 0) {
    throw new Error(`Invalid ticker symbol: ${symbol}`)
  }
  return result
} //Esto nos permite obtener el precio actual de la compañia.

export async function getCompanyProfile(symbol: string): Promise<FinnhubProfile> {
  const raw = await finnhubFetch(`/stock/profile2?symbol=${symbol.toUpperCase()}`)
  const result = parse(FinnhubProfileSchema, raw)
  if (!result.name) {
    throw new Error(`No company profile found for: ${symbol}`)
  }
  return result
}//y esto nos permite obtener información general de la compañia.
