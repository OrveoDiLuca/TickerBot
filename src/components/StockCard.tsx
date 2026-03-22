import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts'
import type { StockData } from '../types'
import HeaderCard from './HeaderCard'
import { buildChartData } from '../helpers/functions'
import type { ChartPoint } from '../types'

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean
  payload?: { value: number; payload: ChartPoint }[]
}) {
  if (!active || !payload?.length) return null
  const { time, price } = payload[0].payload
  return (
    <div
      className="rounded-xl px-3 py-2 text-sm shadow-xl"
      style={{ backgroundColor: '#1a2436', border: '1px solid #2b6cee', color: '#e2e8f0' }}
    >
      <div className="font-semibold" style={{ color: '#2b6cee' }}>${price.toFixed(2)}</div>
      <div className="text-xs mt-0.5" style={{ color: '#64748b' }}>{time}</div>
    </div>
  )
}

function SuperChart({
  timestamps,
  closes,
  isPositive,
}: {
  timestamps: number[]
  closes: number[]
  isPositive: boolean
}) {
  const data = buildChartData(timestamps, closes)
  const color = isPositive ? '#22c55e' : '#ef4444'
  const gradId = isPositive ? 'superchart-green' : 'superchart-red'

  const min = Math.min(...closes)
  const max = Math.max(...closes)
  const padding = (max - min) * 0.1 || 1

  // Show ~5 evenly-spaced ticks on x-axis
  const step = Math.max(1, Math.floor(data.length / 4))
  const xTicks = data.filter((_, i) => i % step === 0 || i === data.length - 1).map((d) => d.time)

  return (
    <ResponsiveContainer width="100%" height={180}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.3} />
            <stop offset="100%" stopColor={color} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e2a40" vertical={false} />
        <XAxis
          dataKey="time"
          ticks={xTicks}
          tick={{ fill: '#475569', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          domain={[min - padding, max + padding]}
          tick={{ fill: '#475569', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v) => `$${v.toFixed(0)}`}
          width={52}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#2b6cee', strokeWidth: 1, strokeDasharray: '4 4' }} />
        <Area
          type="monotone"
          dataKey="price"
          stroke={color}
          strokeWidth={2.5}
          fill={`url(#${gradId})`}
          dot={false}
          activeDot={{ r: 4, fill: color, stroke: '#101622', strokeWidth: 2 }}
          isAnimationActive={true}
          animationDuration={800}
          animationEasing="ease-out"
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

export default function StockCard({ data }: { data: StockData }) {
  const { ticker, name, exchange, logo, chart, news, quote } = data //Aplicamos un destructuring para acceder a las propiedades del objeto data de tipo StockData. 
  const isPositive = (quote?.dp ?? 0) >= 0
  const changeColor = isPositive ? '#22c55e' : '#ef4444'

  return (
    <div
      className="rounded-2xl overflow-hidden mt-3 w-full"
      style={{ backgroundColor: '#101622', border: '1px solid #222f47' }}
    >
      {/* Header */}
      <HeaderCard
        ticker={ticker}
        name={name}
        exchange={exchange}
        logo={logo}
        quote={quote}
        isPositive={isPositive}
        changeColor={changeColor}
      />

      {/* Superchart */}
      {chart && chart.closes.length > 1 && (
        <div className="px-2 pb-3">
          <SuperChart
            timestamps={chart.timestamps}
            closes={chart.closes}
            isPositive={isPositive}
          />
        </div>
      )}

      {/* Noticias */}
      {news.length > 0 && (
        <div style={{ borderTop: '1px solid #222f47' }}>
          <div className="px-5 py-3 flex flex-col gap-3">
            <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: '#475569' }}>
              Últimas noticias
            </p>
            <div className="flex flex-col gap-3 overflow-y-auto max-h-52 pr-1">
            {news.slice(0, 8).map((item, i) => (
              <a
                key={i}
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex flex-col gap-0.5 group"
              >
                <span
                  className="text-sm leading-snug group-hover:text-blue-400 transition-colors"
                  style={{ color: '#e2e8f0' }}
                >
                  {item.headline}
                </span>
                <span className="text-xs" style={{ color: '#475569' }}>
                  {item.source}
                  {item.datetime
                    ? ` · ${new Date(item.datetime * 1000).toLocaleDateString('es-ES', {
                        day: 'numeric',
                        month: 'short',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}`
                    : ''}
                </span>
              </a>
            ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
