export type Message = {
  id: string
  role: 'user' | 'bot'
  text: string
}

export type FinnhubQuote = {
  c: number   // current price
  h: number   // high
  l: number   // low
  o: number   // open
  pc: number  // previous close
  t: number   // timestamp unix
}

export type FinnhubProfile = {
  name: string
  ticker: string
  exchange: string
  marketCapitalization: number
  currency: string
  country: string
  finnhubIndustry: string
}
