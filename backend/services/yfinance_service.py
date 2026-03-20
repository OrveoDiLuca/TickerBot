import yfinance as yf


def get_fundamentals(ticker: str) -> dict:
    """
    Obtiene métricas financieras estructuradas desde yfinance.
    Fuente autoritativa para todos los números: ingresos, márgenes, ratios, EPS, deuda.
    """
    t = yf.Ticker(ticker)
    info = t.info or {}

    # --- Ingresos y crecimiento ---
    revenue = info.get("totalRevenue")
    revenue_growth = info.get("revenueGrowth")  # YoY como decimal, ej: 0.0645
    earnings_growth = info.get("earningsGrowth")

    # Ingresos del año anterior desde el income statement
    try:
        fin = t.financials  # columnas = fechas, filas = métricas
        if fin is not None and not fin.empty and fin.shape[1] >= 2:
            rev_row = fin.loc["Total Revenue"] if "Total Revenue" in fin.index else None
            revenue_prev = float(rev_row.iloc[1]) if rev_row is not None else None
        else:
            revenue_prev = None
    except Exception:
        revenue_prev = None

    # --- Rentabilidad ---
    gross_margin = info.get("grossMargins")
    operating_margin = info.get("operatingMargins")
    net_margin = info.get("profitMargins")
    roe = info.get("returnOnEquity")
    roa = info.get("returnOnAssets")
    ebitda = info.get("ebitda")

    # --- EPS ---
    eps_trailing = info.get("trailingEps")
    eps_forward = info.get("forwardEps")

    # --- Salud financiera ---
    total_debt = info.get("totalDebt")
    cash = info.get("totalCash")
    net_debt = (total_debt - cash) if (total_debt and cash) else None
    current_ratio = info.get("currentRatio")
    free_cash_flow = info.get("freeCashflow")
    debt_to_equity = info.get("debtToEquity")

    # --- Ratios de valoración ---
    pe_trailing = info.get("trailingPE")
    pe_forward = info.get("forwardPE")
    pb = info.get("priceToBook")
    ev_ebitda = info.get("enterpriseToEbitda")
    market_cap = info.get("marketCap")
    enterprise_value = info.get("enterpriseValue")

    def fmt_pct(v):
        return f"{v * 100:.2f}%" if v is not None else "N/D"

    def fmt_usd(v, scale="M"):
        if v is None:
            return "N/D"
        if scale == "B":
            return f"${v / 1e9:.2f}B"
        if scale == "M":
            return f"${v / 1e6:.2f}M"
        return f"${v:,.0f}"

    def fmt_x(v):
        return f"{v:.2f}x" if v is not None else "N/D"

    def fmt_num(v):
        return f"{v:.2f}" if v is not None else "N/D"

    summary = f"""
== MÉTRICAS FINANCIERAS (yfinance) ==

[Ingresos y Crecimiento]
- Ingresos totales (TTM): {fmt_usd(revenue, 'B') if revenue and revenue > 1e9 else fmt_usd(revenue, 'M')}
- Ingresos año anterior: {fmt_usd(revenue_prev, 'B') if revenue_prev and revenue_prev > 1e9 else fmt_usd(revenue_prev, 'M')}
- Crecimiento de ingresos YoY: {fmt_pct(revenue_growth)}
- Crecimiento de utilidades YoY: {fmt_pct(earnings_growth)}
- EBITDA: {fmt_usd(ebitda, 'B') if ebitda and ebitda > 1e9 else fmt_usd(ebitda, 'M')}

[EPS]
- EPS trailing (TTM): {fmt_num(eps_trailing)}
- EPS forward (estimado): {fmt_num(eps_forward)}

[Rentabilidad]
- Margen bruto: {fmt_pct(gross_margin)}
- Margen operativo: {fmt_pct(operating_margin)}
- Margen neto: {fmt_pct(net_margin)}
- ROE: {fmt_pct(roe)}
- ROA: {fmt_pct(roa)}

[Salud Financiera]
- Deuda total: {fmt_usd(total_debt, 'B') if total_debt and total_debt > 1e9 else fmt_usd(total_debt, 'M')}
- Efectivo y equivalentes: {fmt_usd(cash, 'B') if cash and cash > 1e9 else fmt_usd(cash, 'M')}
- Deuda neta: {fmt_usd(net_debt, 'B') if net_debt and abs(net_debt) > 1e9 else fmt_usd(net_debt, 'M')}
- Ratio corriente: {fmt_num(current_ratio)}
- Deuda/Patrimonio: {fmt_num(debt_to_equity)}
- Free cash flow: {fmt_usd(free_cash_flow, 'B') if free_cash_flow and abs(free_cash_flow) > 1e9 else fmt_usd(free_cash_flow, 'M')}

[Ratios de Valoración]
- P/E trailing: {fmt_x(pe_trailing)}
- P/E forward: {fmt_x(pe_forward)}
- P/B: {fmt_x(pb)}
- EV/EBITDA: {fmt_x(ev_ebitda)}
- Capitalización de mercado: {fmt_usd(market_cap, 'B')}
- Valor empresa (EV): {fmt_usd(enterprise_value, 'B')}
"""
    return {"summary": summary.strip(), "raw": info}
