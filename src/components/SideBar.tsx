
const Sidebar = () => {
  return (
    <aside
      className="w-64 flex flex-col h-full rounded-2xl overflow-hidden shrink-0"
      style={{ backgroundColor: '#151d2e', border: '1px solid #222f47' }}
    >
      {/* Logo */}
      <div className="p-5 flex items-center gap-3">
        <div
          className="p-2 rounded-xl flex items-center justify-center"
          style={{ backgroundColor: '#2b6cee' }}
        >
          <svg className="w-5 h-5 text-white fill-current" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17.93V18c0-.55-.45-1-1-1s-1 .45-1 1v1.93C7.06 19.48 4.52 16.94 4.07 13H6c.55 0 1-.45 1-1s-.45-1-1-1H4.07C4.52 7.06 7.06 4.52 11 4.07V6c0 .55.45 1 1 1s1-.45 1-1V4.07C16.94 4.52 19.48 7.06 19.93 11H18c-.55 0-1 .45-1 1s.45 1 1 1h1.93c-.45 3.94-2.99 6.48-6.93 6.93z" />
          </svg>
        </div>
        <div>
          <h1 className="text-white text-sm font-bold leading-none">TickerBot</h1>
        </div>
      </div>

      {/* New Analysis Button */}
      <div className="px-4 pb-4">
        <button
          className="w-full text-white font-semibold py-2.5 px-4 rounded-xl flex items-center justify-center gap-2 text-sm transition-opacity hover:opacity-90"
          style={{ backgroundColor: '#2b6cee' }}
        >
          <span className="text-lg leading-none">+</span>
          New Analysis
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 space-y-1">
        {/* Recent Insights */}
        <p className="text-xs font-bold uppercase tracking-widest px-3 mb-2" style={{ color: '#64748b' }}>
          Recent Insights
        </p>
        <a
          href="#"
          className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors"
          style={{ backgroundColor: 'rgba(43,108,238,0.15)', color: '#2b6cee' }}
        >
          <ChatIcon />
          <span className="truncate">Apple AAPL Analysis</span>
        </a>
        <a
          href="#"
          className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors hover:bg-white/5"
          style={{ color: '#64748b' }}
        >
          <ChatIcon />
          <span className="truncate">Crypto Market Pulse</span>
        </a>
        <a
          href="#"
          className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors hover:bg-white/5"
          style={{ color: '#64748b' }}
        >
          <ChatIcon />
          <span className="truncate">Nvidia Earnings Strategy</span>
        </a>

        {/* Tools */}
        <p className="text-xs font-bold uppercase tracking-widest px-3 pt-5 mb-2" style={{ color: '#64748b' }}>
          Tools
        </p>
        <a href="#" className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-colors hover:bg-white/5" style={{ color: '#64748b' }}>
          <ChartIcon />
          <span>Market Analysis</span>
        </a>
        <a href="#" className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-colors hover:bg-white/5" style={{ color: '#64748b' }}>
          <BriefcaseIcon />
          <span>Portfolio Management</span>
        </a>
        <a href="#" className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-colors hover:bg-white/5" style={{ color: '#64748b' }}>
          <StarIcon />
          <span>Watchlist</span>
        </a>
      </nav>

      {/* Bottom Section */}
      <div className="p-4 mt-auto" style={{ borderTop: '1px solid #222f47' }}>
        <a href="#" className="flex items-center gap-3 px-3 py-2 rounded-xl text-sm transition-colors hover:bg-white/5 mb-3" style={{ color: '#64748b' }}>
          <SettingsIcon />
          <span>Settings</span>
        </a>
        <div
          className="flex items-center gap-3 p-3 rounded-xl"
          style={{ backgroundColor: 'rgba(255,255,255,0.04)', border: '1px solid #222f47' }}
        >
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0"
            style={{ backgroundColor: '#1e2a40', border: '1px solid #334155' }}
          >
            JD
          </div>
          <div className="overflow-hidden">
            <p className="text-xs font-semibold text-white truncate">John Dorsey</p>
            <p className="text-[10px] truncate" style={{ color: '#64748b' }}>Pro Account</p>
          </div>
        </div>
      </div>
    </aside>
  )
}

// Icons
const ChatIcon = () => (
  <svg className="w-4 h-4 shrink-0 fill-current" viewBox="0 0 24 24">
    <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
  </svg>
)
const ChartIcon = () => (
  <svg className="w-4 h-4 shrink-0 fill-current" viewBox="0 0 24 24">
    <path d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z"/>
  </svg>
)
const BriefcaseIcon = () => (
  <svg className="w-4 h-4 shrink-0 fill-current" viewBox="0 0 24 24">
    <path d="M20 6h-2.18c.07-.44.18-.86.18-1.3C18 3.1 16.9 2 15.5 2h-7C7.1 2 6 3.1 6 4.7c0 .44.11.86.18 1.3H4c-1.1 0-2 .9-2 2v11c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm-7.5 12H8v-2h4.5v2zm0-4H8v-2h4.5v2zm3-8h-7C8.22 6 8 5.79 8 4.7 8 4.22 8.22 4 8.5 4h7c.28 0 .5.22.5.7 0 1.09-.22 1.3-.5 1.3z"/>
  </svg>
)
const StarIcon = () => (
  <svg className="w-4 h-4 shrink-0 fill-current" viewBox="0 0 24 24">
    <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/>
  </svg>
)
const SettingsIcon = () => (
  <svg className="w-4 h-4 shrink-0 fill-current" viewBox="0 0 24 24">
    <path d="M19.14,12.94c0.04-0.3,0.06-0.61,0.06-0.94c0-0.32-0.02-0.64-0.07-0.94l2.03-1.58c0.18-0.14,0.23-0.41,0.12-0.61 l-1.92-3.32c-0.12-0.22-0.37-0.29-0.59-0.22l-2.39,0.96c-0.5-0.38-1.03-0.7-1.62-0.94L14.4,2.81c-0.04-0.24-0.24-0.41-0.48-0.41 h-3.84c-0.24,0-0.43,0.17-0.47,0.41L9.25,5.35C8.66,5.59,8.12,5.92,7.63,6.29L5.24,5.33c-0.22-0.08-0.47,0-0.59,0.22L2.74,8.87 C2.62,9.08,2.66,9.34,2.86,9.48l2.03,1.58C4.84,11.36,4.8,11.69,4.8,12s0.02,0.64,0.07,0.94l-2.03,1.58 c-0.18,0.14-0.23,0.41-0.12,0.61l1.92,3.32c0.12,0.22,0.37,0.29,0.59,0.22l2.39-0.96c0.5,0.38,1.03,0.7,1.62,0.94l0.36,2.54 c0.05,0.24,0.24,0.41,0.48,0.41h3.84c0.24,0,0.44-0.17,0.47-0.41l0.36-2.54c0.59-0.24,1.13-0.56,1.62-0.94l2.39,0.96 c0.22,0.08,0.47,0,0.59-0.22l1.92-3.32c0.12-0.22,0.07-0.47-0.12-0.61L19.14,12.94z M12,15.6c-1.98,0-3.6-1.62-3.6-3.6 s1.62-3.6,3.6-3.6s3.6,1.62,3.6,3.6S13.98,15.6,12,15.6z"/>
  </svg>
)

export default Sidebar
