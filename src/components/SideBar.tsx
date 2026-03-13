
const Sidebar = () => {
  return (
    <aside
      className="w-64 flex flex-col h-full rounded-2xl overflow-hidden shrink-0"
      style={{ backgroundColor: '#151d2e', border: '1px solid #222f47' }}
    >
      {/* Logo */}
      <div className="p-5 flex items-center gap-3">
        <img src="/Gemini_Generated_Image_xe23zpxe23zpxe23.png" alt="TickerBot logo" className="w-20 h-10 object-contain rounded-xl" />
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
        {/* Recent Insights */}

      {/* Bottom Section */}
    </aside>
  )
}

export default Sidebar