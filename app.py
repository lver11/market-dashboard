#!/usr/bin/env python3
"""
Market Turbulence & Risk Dashboard
Live risk-on/off indicator with multi-asset market data aggregation.
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Optional

import feedparser
import yfinance as yf
from flask import Flask, jsonify, render_template

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ─── In-memory cache ──────────────────────────────────────────────────────────
_cache: dict[str, Any] = {}
_cache_ts: dict[str, float] = {}


def get_cached(key: str, ttl: int = 60) -> Optional[Any]:
    if key in _cache and time.time() - _cache_ts.get(key, 0) < ttl:
        return _cache[key]
    return None


def set_cached(key: str, value: Any) -> None:
    _cache[key] = value
    _cache_ts[key] = time.time()


# ─── Market Assets Configuration ──────────────────────────────────────────────
MARKET_ASSETS = [
    # Equities
    {"group": "Equities",    "name": "S&P 500",           "ticker": "^GSPC",     "type": "index"},
    {"group": "Equities",    "name": "Nasdaq 100",         "ticker": "^NDX",      "type": "index"},
    {"group": "Equities",    "name": "Dow Jones",          "ticker": "^DJI",      "type": "index"},
    {"group": "Equities",    "name": "Russell 2000",       "ticker": "^RUT",      "type": "index"},
    {"group": "Equities",    "name": "Euro Stoxx 50",      "ticker": "^STOXX50E", "type": "index"},
    {"group": "Equities",    "name": "Nikkei 225",         "ticker": "^N225",     "type": "index"},
    {"group": "Equities",    "name": "MSCI EM (EEM)",      "ticker": "EEM",       "type": "etf"},
    # Bonds / Rates
    {"group": "Bonds",       "name": "US 10Y Yield",       "ticker": "^TNX",      "type": "bond"},
    {"group": "Bonds",       "name": "US 2Y Yield",        "ticker": "^IRX",      "type": "bond"},
    {"group": "Bonds",       "name": "Long Treasury (TLT)","ticker": "TLT",       "type": "etf"},
    {"group": "Bonds",       "name": "High Yield (HYG)",   "ticker": "HYG",       "type": "etf"},
    {"group": "Bonds",       "name": "IG Credit (LQD)",    "ticker": "LQD",       "type": "etf"},
    # Commodities
    {"group": "Commodities", "name": "Gold",               "ticker": "GC=F",      "type": "commodity"},
    {"group": "Commodities", "name": "WTI Oil",            "ticker": "CL=F",      "type": "commodity"},
    {"group": "Commodities", "name": "Silver",             "ticker": "SI=F",      "type": "commodity"},
    # Currencies
    {"group": "Currencies",  "name": "DXY (USD Index)",    "ticker": "DX-Y.NYB",  "type": "currency"},
    {"group": "Currencies",  "name": "EUR/USD",            "ticker": "EURUSD=X",  "type": "currency"},
    {"group": "Currencies",  "name": "USD/JPY",            "ticker": "JPY=X",     "type": "currency"},
    {"group": "Currencies",  "name": "USD/CHF",            "ticker": "CHFUSD=X",  "type": "currency"},
    # Crypto
    {"group": "Crypto",      "name": "Bitcoin",            "ticker": "BTC-USD",   "type": "crypto"},
    {"group": "Crypto",      "name": "Ethereum",           "ticker": "ETH-USD",   "type": "crypto"},
    # Volatility
    {"group": "Volatility",  "name": "VIX",                "ticker": "^VIX",      "type": "volatility"},
    # Risk proxies
    {"group": "Risk Proxies","name": "S&P 500 ETF (SPY)",  "ticker": "SPY",       "type": "etf"},
]

# ─── News Feeds ───────────────────────────────────────────────────────────────
NEWS_FEEDS = [
    ("Reuters Top",    "https://feeds.reuters.com/reuters/topNews"),
    ("Reuters Biz",    "https://feeds.reuters.com/reuters/businessNews"),
    ("BBC Business",   "https://feeds.bbci.co.uk/news/business/rss.xml"),
    ("BBC World",      "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("AP Top News",    "https://apnews.com/rss"),
]

# ─── Economic Calendar (Q1-Q2 2026) ──────────────────────────────────────────
ECONOMIC_CALENDAR = [
    # === MARCH 2026 ===
    {"date": "2026-03-06", "event": "Non-Farm Payrolls (Feb)",      "country": "US", "importance": "critical",
     "forecast": "200K", "previous": "256K"},
    {"date": "2026-03-06", "event": "Unemployment Rate (Feb)",       "country": "US", "importance": "high",
     "forecast": "4.1%", "previous": "4.0%"},
    {"date": "2026-03-06", "event": "ECB Rate Decision",             "country": "EU", "importance": "critical",
     "forecast": "Hold", "previous": "2.65%"},
    {"date": "2026-03-07", "event": "Michigan Consumer Confidence",  "country": "US", "importance": "medium",
     "forecast": None, "previous": "64.7"},
    {"date": "2026-03-11", "event": "JOLTS Job Openings (Jan)",      "country": "US", "importance": "medium",
     "forecast": None, "previous": "7.6M"},
    {"date": "2026-03-12", "event": "CPI YoY (Feb)",                 "country": "US", "importance": "critical",
     "forecast": "2.8%", "previous": "3.0%"},
    {"date": "2026-03-12", "event": "Core CPI YoY (Feb)",            "country": "US", "importance": "critical",
     "forecast": "3.2%", "previous": "3.3%"},
    {"date": "2026-03-13", "event": "PPI (Feb)",                     "country": "US", "importance": "medium",
     "forecast": None, "previous": "3.5%"},
    {"date": "2026-03-13", "event": "Initial Jobless Claims",        "country": "US", "importance": "medium",
     "forecast": None, "previous": "242K"},
    {"date": "2026-03-14", "event": "US Retail Sales (Feb)",         "country": "US", "importance": "high",
     "forecast": None, "previous": "-0.9%"},
    {"date": "2026-03-15", "event": "China Industrial Production",   "country": "CN", "importance": "medium",
     "forecast": None, "previous": "6.2%"},
    {"date": "2026-03-15", "event": "China Retail Sales",            "country": "CN", "importance": "medium",
     "forecast": None, "previous": "3.7%"},
    {"date": "2026-03-17", "event": "NY Fed Manufacturing",          "country": "US", "importance": "medium",
     "forecast": None, "previous": "5.7"},
    {"date": "2026-03-18", "event": "FOMC Meeting Begins",           "country": "US", "importance": "high",
     "forecast": None, "previous": None},
    {"date": "2026-03-19", "event": "FOMC Rate Decision",            "country": "US", "importance": "critical",
     "forecast": "No change", "previous": "4.25-4.50%"},
    {"date": "2026-03-19", "event": "Powell Press Conference",       "country": "US", "importance": "critical",
     "forecast": None, "previous": None},
    {"date": "2026-03-19", "event": "BOJ Rate Decision",             "country": "JP", "importance": "high",
     "forecast": None, "previous": "0.50%"},
    {"date": "2026-03-19", "event": "FOMC Dot Plot / Projections",   "country": "US", "importance": "high",
     "forecast": None, "previous": None},
    {"date": "2026-03-20", "event": "Philadelphia Fed Index",        "country": "US", "importance": "medium",
     "forecast": None, "previous": "18.1"},
    {"date": "2026-03-21", "event": "Michigan Consumer Confidence (Final)", "country": "US", "importance": "medium",
     "forecast": None, "previous": None},
    {"date": "2026-03-25", "event": "S&P/Case-Shiller Home Prices", "country": "US", "importance": "low",
     "forecast": None, "previous": None},
    {"date": "2026-03-26", "event": "Consumer Confidence (CB)",      "country": "US", "importance": "medium",
     "forecast": None, "previous": "104.1"},
    {"date": "2026-03-27", "event": "GDP Q4 2025 (Final)",           "country": "US", "importance": "high",
     "forecast": "2.3%", "previous": "2.3%"},
    {"date": "2026-03-27", "event": "Durable Goods Orders",          "country": "US", "importance": "medium",
     "forecast": None, "previous": "3.1%"},
    {"date": "2026-03-28", "event": "PCE Price Index YoY (Feb)",     "country": "US", "importance": "critical",
     "forecast": "2.5%", "previous": "2.6%"},
    {"date": "2026-03-28", "event": "Personal Income & Spending",    "country": "US", "importance": "medium",
     "forecast": None, "previous": None},
    # === APRIL 2026 ===
    {"date": "2026-04-01", "event": "ISM Manufacturing PMI (Mar)",   "country": "US", "importance": "high",
     "forecast": None, "previous": "50.3"},
    {"date": "2026-04-02", "event": "JOLTS Job Openings (Feb)",      "country": "US", "importance": "medium",
     "forecast": None, "previous": None},
    {"date": "2026-04-03", "event": "Non-Farm Payrolls (Mar)",       "country": "US", "importance": "critical",
     "forecast": None, "previous": "200K"},
    {"date": "2026-04-03", "event": "Unemployment Rate (Mar)",       "country": "US", "importance": "high",
     "forecast": None, "previous": "4.1%"},
    {"date": "2026-04-10", "event": "CPI (Mar)",                     "country": "US", "importance": "critical",
     "forecast": None, "previous": "2.8%"},
    {"date": "2026-04-16", "event": "China GDP Q1 2026",             "country": "CN", "importance": "high",
     "forecast": None, "previous": "5.0%"},
    {"date": "2026-04-29", "event": "FOMC Rate Decision",            "country": "US", "importance": "critical",
     "forecast": None, "previous": "4.25-4.50%"},
    {"date": "2026-04-30", "event": "GDP Q1 2026 (Advance)",         "country": "US", "importance": "high",
     "forecast": None, "previous": "2.3%"},
]

# ─── Geopolitical Risk Monitor ────────────────────────────────────────────────
GEOPOLITICAL_RISKS = [
    {
        "region": "Europe",
        "title": "Ukraine-Russia War",
        "level": "high",
        "icon": "sword",
        "description": "Active conflict; ceasefire talks ongoing. NATO supply lines under pressure.",
        "market_impact": "Energy prices, European equities, EUR weakness",
    },
    {
        "region": "Middle East",
        "title": "Middle East Tensions",
        "level": "high",
        "icon": "flame",
        "description": "Regional escalation risks; Red Sea shipping disruptions affecting supply chains.",
        "market_impact": "Oil premium, shipping costs, global inflation",
    },
    {
        "region": "Asia Pacific",
        "title": "Taiwan Strait / China-US",
        "level": "medium",
        "icon": "alert-triangle",
        "description": "Elevated military activity; US-China strategic competition intensifying.",
        "market_impact": "Tech supply chains, semiconductors, Asian equities",
    },
    {
        "region": "Americas",
        "title": "US-China Trade War",
        "level": "medium",
        "icon": "trending-down",
        "description": "Tariff escalation; supply chain decoupling in critical sectors.",
        "market_impact": "Global trade, tech sector, EM currencies",
    },
    {
        "region": "Global",
        "title": "Central Bank Policy Divergence",
        "level": "medium",
        "icon": "bar-chart-2",
        "description": "Fed vs ECB vs BOJ divergent paths creating currency volatility.",
        "market_impact": "USD strength, carry trades, EM debt",
    },
    {
        "region": "Americas",
        "title": "US Fiscal Sustainability",
        "level": "low",
        "icon": "dollar-sign",
        "description": "Debt ceiling concerns; rising deficit affecting bond market sentiment.",
        "market_impact": "Treasury yields, USD long-term, sovereign ratings",
    },
]


# ─── Data Fetching ────────────────────────────────────────────────────────────
def _fetch_one(ticker: str) -> tuple[str, dict]:
    """Fetch single ticker data from Yahoo Finance."""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d", auto_adjust=True)
        hist = hist.dropna(subset=["Close"])
        if len(hist) >= 2:
            current = float(hist["Close"].iloc[-1])
            previous = float(hist["Close"].iloc[-2])
            change = current - previous
            change_pct = (change / previous) * 100
            return ticker, {
                "price": round(current, 4),
                "change": round(change, 4),
                "change_pct": round(change_pct, 2),
                "timestamp": hist.index[-1].isoformat(),
            }
        elif len(hist) == 1:
            current = float(hist["Close"].iloc[-1])
            return ticker, {
                "price": round(current, 4),
                "change": None,
                "change_pct": None,
                "timestamp": hist.index[-1].isoformat(),
            }
    except Exception as e:
        logger.warning(f"Error fetching {ticker}: {e}")
    return ticker, {"price": None, "change": None, "change_pct": None, "timestamp": None}


def fetch_market_data() -> dict:
    """Fetch all market data in parallel (cached 60s)."""
    cached = get_cached("market_data", ttl=60)
    if cached:
        return cached

    tickers_list = list({a["ticker"] for a in MARKET_ASSETS})
    result = {}

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(_fetch_one, ticker): ticker for ticker in tickers_list}
        for future in as_completed(futures, timeout=25):
            try:
                ticker, data = future.result()
                result[ticker] = data
            except Exception as e:
                logger.warning(f"Future error: {e}")

    set_cached("market_data", result)
    return result


def get_vix_history() -> list[dict]:
    """Get 30-day VIX history for sparkline chart (cached 5 min)."""
    cached = get_cached("vix_history", ttl=300)
    if cached:
        return cached
    try:
        t = yf.Ticker("^VIX")
        hist = t.history(period="30d")
        hist = hist.dropna(subset=["Close"])
        data = [
            {"date": str(idx.date()), "value": round(float(row["Close"]), 2)}
            for idx, row in hist.iterrows()
        ]
        set_cached("vix_history", data)
        return data
    except Exception as e:
        logger.error(f"VIX history error: {e}")
        return []


def fetch_news(max_items: int = 24) -> list[dict]:
    """Fetch news from RSS feeds (cached 5 min)."""
    cached = get_cached("news", ttl=300)
    if cached:
        return cached

    all_items = []
    for source, url in NEWS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:6]:
                title = getattr(entry, "title", "")
                link = getattr(entry, "link", "#")
                published = getattr(entry, "published", "")
                summary = getattr(entry, "summary", getattr(entry, "description", ""))

                title_lower = title.lower()
                tags = []
                if any(w in title_lower for w in [
                    "war", "conflict", "attack", "strike", "military",
                    "nuclear", "sanctions", "nato", "ukraine", "russia",
                    "china", "taiwan", "iran", "israel", "hamas",
                ]):
                    tags.append("geopolitical")
                if any(w in title_lower for w in [
                    "inflation", "rate", "fed", "ecb", "boj", "central bank",
                    "gdp", "jobs", "recession", "cpi", "ppi", "fomc",
                ]):
                    tags.append("economic")
                if any(w in title_lower for w in [
                    "market", "stock", "equity", "bond", "gold", "oil",
                    "crypto", "bitcoin", "rally", "sell-off", "crash",
                ]):
                    tags.append("market")

                all_items.append({
                    "title": title,
                    "source": source,
                    "url": link,
                    "published": published,
                    "summary": (summary[:180] + "...") if len(summary) > 180 else summary,
                    "tags": tags,
                })
        except Exception as e:
            logger.warning(f"Feed {source} failed: {e}")

    result = all_items[:max_items]
    set_cached("news", result)
    return result


# ─── Risk Score Calculation ───────────────────────────────────────────────────
def calculate_risk_score(market_data: dict) -> dict:
    """
    Composite risk-on/off score: 0 = extreme risk-off, 100 = extreme risk-on.

    Signals & weights:
      VIX level          25% — fear gauge
      S&P 500 daily      15% — equity direction
      Gold daily         12% — safe-haven demand
      USD (DXY) daily    12% — dollar flight-to-safety
      HY vs IG credit    12% — credit risk appetite
      EM vs S&P          12% — risk appetite breadth
      Long Treasury      12% — bond flight-to-safety
    """
    signals = []
    weighted_sum = 0.0
    total_weight = 0.0

    def add_signal(name, value, unit, score, label, status, weight, description):
        nonlocal weighted_sum, total_weight
        signals.append({
            "name": name,
            "value": value,
            "unit": unit,
            "score": round(float(score), 1),
            "label": label,
            "status": status,
            "weight": weight,
            "description": description,
        })
        weighted_sum += float(score) * weight
        total_weight += weight

    # ── 1. VIX (25%) ──────────────────────────────────────────────────────────
    vix = market_data.get("^VIX", {}).get("price")
    if vix is not None:
        if vix < 12:
            sc, lbl, st = 92, "Complacent", "risk-on"
        elif vix < 15:
            sc, lbl, st = 80, "Low Volatility", "risk-on"
        elif vix < 18:
            sc, lbl, st = 65, "Normal", "neutral"
        elif vix < 22:
            sc, lbl, st = 48, "Elevated", "neutral"
        elif vix < 27:
            sc, lbl, st = 28, "High Fear", "risk-off"
        elif vix < 35:
            sc, lbl, st = 14, "Very High Fear", "risk-off"
        else:
            sc, lbl, st = 5, "Extreme Fear", "risk-off"
        add_signal("VIX Fear Index", vix, "", sc, lbl, st, 25,
                   "Market volatility gauge — higher VIX = more risk-off")

    # ── 2. S&P 500 daily return (15%) ────────────────────────────────────────
    spy_pct = market_data.get("SPY", {}).get("change_pct")
    if spy_pct is None:
        spy_pct = market_data.get("^GSPC", {}).get("change_pct")
    if spy_pct is not None:
        sc = max(0.0, min(100.0, 50.0 + spy_pct * 9.0))
        if sc > 65:
            lbl, st = "Equities Strong", "risk-on"
        elif sc > 38:
            lbl, st = "Equities Mixed", "neutral"
        else:
            lbl, st = "Equities Weak", "risk-off"
        add_signal("S&P 500 (Equities)", spy_pct, "%", sc, lbl, st, 15,
                   "Equity direction — rising markets = risk-on")

    # ── 3. Gold daily return (12%) ────────────────────────────────────────────
    gold_pct = market_data.get("GC=F", {}).get("change_pct")
    if gold_pct is not None:
        sc = max(0.0, min(100.0, 50.0 - gold_pct * 14.0))
        if sc > 65:
            lbl, st = "Gold Selling (risk-on)", "risk-on"
        elif sc > 38:
            lbl, st = "Gold Neutral", "neutral"
        else:
            lbl, st = "Gold Safe-Haven Demand", "risk-off"
        add_signal("Gold (Safe Haven)", gold_pct, "%", sc, lbl, st, 12,
                   "Safe-haven demand — gold rising = risk-off")

    # ── 4. DXY daily return (12%) ─────────────────────────────────────────────
    dxy_pct = market_data.get("DX-Y.NYB", {}).get("change_pct")
    if dxy_pct is not None:
        sc = max(0.0, min(100.0, 50.0 - dxy_pct * 14.0))
        if sc > 65:
            lbl, st = "USD Weakening (risk-on)", "risk-on"
        elif sc > 38:
            lbl, st = "USD Stable", "neutral"
        else:
            lbl, st = "USD Strengthening (risk-off)", "risk-off"
        add_signal("USD Strength (DXY)", dxy_pct, "%", sc, lbl, st, 12,
                   "Dollar strength — USD rising = flight-to-safety")

    # ── 5. HY vs IG Credit spread (12%) ──────────────────────────────────────
    hyg_pct = market_data.get("HYG", {}).get("change_pct")
    lqd_pct = market_data.get("LQD", {}).get("change_pct")
    if hyg_pct is not None and lqd_pct is not None:
        spread = hyg_pct - lqd_pct
        sc = max(0.0, min(100.0, 50.0 + spread * 18.0))
        if sc > 65:
            lbl, st = "HY Outperforming (credit rally)", "risk-on"
        elif sc > 38:
            lbl, st = "Credit Neutral", "neutral"
        else:
            lbl, st = "IG Outperforming (credit stress)", "risk-off"
        add_signal("HY vs IG Credit", round(spread, 2), "% spread", sc, lbl, st, 12,
                   "High yield vs investment grade — HY outperforming = risk appetite")

    # ── 6. EM vs S&P relative performance (12%) ──────────────────────────────
    eem_pct = market_data.get("EEM", {}).get("change_pct")
    sp_pct = market_data.get("SPY", {}).get("change_pct") or market_data.get("^GSPC", {}).get("change_pct")
    if eem_pct is not None and sp_pct is not None:
        em_vs_sp = eem_pct - sp_pct
        sc = max(0.0, min(100.0, 50.0 + em_vs_sp * 18.0))
        if sc > 65:
            lbl, st = "EM Outperforming (global appetite)", "risk-on"
        elif sc > 38:
            lbl, st = "EM In-Line", "neutral"
        else:
            lbl, st = "EM Underperforming (risk-off)", "risk-off"
        add_signal("EM vs Developed Markets", round(eem_pct, 2), "%", sc, lbl, st, 12,
                   "EM outperformance = broad global risk appetite")

    # ── 7. Long Treasury (TLT) performance (12%) ─────────────────────────────
    tlt_pct = market_data.get("TLT", {}).get("change_pct")
    if tlt_pct is not None:
        sc = max(0.0, min(100.0, 50.0 - tlt_pct * 14.0))
        if sc > 65:
            lbl, st = "Bonds Selling (risk-on)", "risk-on"
        elif sc > 38:
            lbl, st = "Bonds Neutral", "neutral"
        else:
            lbl, st = "Bond Rally (flight-to-safety)", "risk-off"
        add_signal("Long-Term Treasuries", tlt_pct, "%", sc, lbl, st, 12,
                   "Treasury bond demand — bonds rallying = risk-off")

    # ── Composite score ───────────────────────────────────────────────────────
    composite = round(weighted_sum / total_weight, 1) if total_weight > 0 else 50.0

    if composite >= 72:
        label, color = "RISK-ON", "green"
        desc = "Strong risk appetite — markets favor equities, credit, EM, high-beta assets. Reduce defensive holdings."
    elif composite >= 58:
        label, color = "MODERATELY RISK-ON", "green"
        desc = "Moderate risk appetite — positive bias with selective caution. Slight overweight equities."
    elif composite >= 42:
        label, color = "NEUTRAL", "amber"
        desc = "Mixed signals — balanced positioning recommended. No clear directional bias."
    elif composite >= 28:
        label, color = "MODERATELY RISK-OFF", "red"
        desc = "Defensive positioning emerging — consider trimming risk, adding gold/USD/quality bonds."
    else:
        label, color = "RISK-OFF", "red"
        desc = "Full flight-to-safety — overweight USD, gold, short-duration treasuries, defensive sectors."

    return {
        "score": composite,
        "label": label,
        "color": color,
        "description": desc,
        "signals": signals,
    }


# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/data")
def api_data():
    """Main API: returns risk score, market data, calendar, news."""
    market_data = fetch_market_data()
    risk = calculate_risk_score(market_data)

    # Enrich assets with live prices
    assets_with_data = []
    for asset in MARKET_ASSETS:
        td = market_data.get(asset["ticker"], {})
        assets_with_data.append({
            **asset,
            "price": td.get("price"),
            "change": td.get("change"),
            "change_pct": td.get("change_pct"),
            "timestamp": td.get("timestamp"),
        })

    # Economic calendar: show events from -2d to +35d
    today = datetime.now(timezone.utc).date()
    calendar = []
    for evt in sorted(ECONOMIC_CALENDAR, key=lambda x: x["date"]):
        event_date = datetime.strptime(evt["date"], "%Y-%m-%d").date()
        days_until = (event_date - today).days
        if -2 <= days_until <= 35:
            calendar.append({
                **evt,
                "days_until": days_until,
                "is_today": days_until == 0,
                "is_past": days_until < 0,
            })

    return jsonify({
        "risk": risk,
        "assets": assets_with_data,
        "news": fetch_news(),
        "geopolitical_risks": GEOPOLITICAL_RISKS,
        "economic_calendar": calendar,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    })


@app.route("/api/vix-history")
def api_vix_history():
    return jsonify(get_vix_history())


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=False, port=port, host="0.0.0.0")
