import type { FinnhubQuote, FinnhubProfile } from '../types'

//Este archivo se encarga de interactuar con la API de Finnhub para obtener las cotizaciones de acciones de las empresas que pida el usuario. 

const API_KEY = import.meta.env.VITE_FINNHUB_API_KEY
const BASE_URL = 'https://finnhub.io/api/v1'

async function finnhubFetch<T>(path: string): Promise<T> {
  const url = `${BASE_URL}${path}&token=${API_KEY}`
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Finnhub request failed: ${response.status}`)
  }
  return response.json() as Promise<T>
}

export async function getStockQuote(symbol: string): Promise<FinnhubQuote> {
  const data = await finnhubFetch<FinnhubQuote>(`/quote?symbol=${symbol.toUpperCase()}`)
  if (data.c === 0) {
    throw new Error(`Invalid ticker symbol: ${symbol}`)
  }
  return data
} //Esto nos permite obtener el precio actual de la compañia. 

export async function getCompanyProfile(symbol: string): Promise<FinnhubProfile> {
  const data = await finnhubFetch<FinnhubProfile>(`/stock/profile2?symbol=${symbol.toUpperCase()}`)
  console.log('Finnhub profile data:', data)
  if (!data.name) {
    throw new Error(`No company profile found for: ${symbol}`)
  }
  return data
}//y esto nos permite obtener información general de la compañia. 
