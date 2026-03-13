export type NewsItem = {
  headline: string
  url: string
  source: string
  datetime: number
  image: string
  summary: string
}

export type StockData = {
  ticker: string
  name: string | null
  exchange: string | null
  logo: string | null
  chart: { timestamps: number[]; closes: number[] } | null
  news: NewsItem[]
  quote: { c: number; d: number; dp: number } | null
}

export type Conversation = {
  id: string
  userText: string
  botText: string | null  // null mientras el bot está respondiendo
  stockData?: StockData | null
}
