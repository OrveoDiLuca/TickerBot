
type HeaderCardProps = {
    ticker: string, 
    name: string | null, 
    exchange: string | null, 
    logo: string | null, 
    quote: any, 
    isPositive: boolean, 
    changeColor: string
}


export default function HeaderCard({ticker,name,exchange,logo,quote,isPositive,changeColor}: HeaderCardProps) {
  return (
    <div className="flex items-center justify-between px-5 pt-5 pb-4">
        <div className="flex items-center gap-3">
          {logo ? (
            <img
              src={logo}
              alt={name ?? ticker}
              className="w-12 h-12 rounded-xl object-contain"
              style={{ backgroundColor: '#fff', padding: '5px' }}
            />
          ) : (
            <div
              className="w-12 h-12 rounded-xl flex items-center justify-center text-sm font-bold"
              style={{ backgroundColor: 'rgba(43,108,238,0.2)', color: '#2b6cee' }}
            >
              {ticker.slice(0, 2)}
            </div>
          )}
          <div>
            <div className="text-white font-semibold text-base leading-tight">
              {name ?? ticker}
            </div>
            <div className="text-xs mt-0.5" style={{ color: '#64748b' }}>
              {ticker}{exchange ? ` · ${exchange}` : ''}
            </div>
          </div>
        </div>

        {quote && (
          <div className="text-right">
            <div className="text-white font-bold text-2xl">${quote.c.toFixed(2)}</div>
            <div className="flex items-center justify-end gap-1 mt-0.5">
              <span className="text-sm font-semibold" style={{ color: changeColor }}>
                {isPositive ? '▲' : '▼'} {Math.abs(quote.dp).toFixed(2)}%
              </span>
              <span className="text-sm" style={{ color: '#64748b' }}>
                ({isPositive ? '+' : ''}{quote.d.toFixed(2)})
              </span>
            </div>
          </div>
        )}
      </div>
  )
}
