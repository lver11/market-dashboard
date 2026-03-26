"""
Market Turbulence & Risk Dashboard — Streamlit Entry Point
Fetches live data via yfinance + BOC API, renders the custom HTML frontend.
Deploy on Streamlit Community Cloud: https://share.streamlit.io
"""
from __future__ import annotations
import json, logging, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

try:
    import feedparser
    import yfinance as yf
except ImportError:
    st.error("Dépendances manquantes. Lancez : pip install yfinance feedparser")
    st.stop()

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

BASE = Path(__file__).parent
TEMPLATE_DIR = BASE / "templates"

# ── Static reference data ───────────────────────────────────────────────────
MARKET_ASSETS = [
    {"group": "Equities",    "name": "S&P 500",            "ticker": "^GSPC",     "type": "index"},
    {"group": "Equities",    "name": "Nasdaq 100",          "ticker": "^NDX",      "type": "index"},
    {"group": "Equities",    "name": "Dow Jones",           "ticker": "^DJI",      "type": "index"},
    {"group": "Equities",    "name": "Russell 2000",        "ticker": "^RUT",      "type": "index"},
    {"group": "Equities",    "name": "Euro Stoxx 50",       "ticker": "^STOXX50E", "type": "index"},
    {"group": "Equities",    "name": "Nikkei 225",          "ticker": "^N225",     "type": "index"},
    {"group": "Equities",    "name": "MSCI EM (EEM)",       "ticker": "EEM",       "type": "etf"},
    {"group": "Bonds",       "name": "US 3M Yield",         "ticker": "^IRX",      "type": "bond"},
    {"group": "Bonds",       "name": "US 5Y Yield",         "ticker": "^FVX",      "type": "bond"},
    {"group": "Bonds",       "name": "US 10Y Yield",        "ticker": "^TNX",      "type": "bond"},
    {"group": "Bonds",       "name": "US 30Y Yield",        "ticker": "^TYX",      "type": "bond"},
    {"group": "Bonds",       "name": "CA 2Y Yield",         "ticker": "CA2YT=RR",  "type": "bond"},
    {"group": "Bonds",       "name": "CA 5Y Yield",         "ticker": "CA5YT=RR",  "type": "bond"},
    {"group": "Bonds",       "name": "CA 10Y Yield",        "ticker": "CA10YT=RR", "type": "bond"},
    {"group": "Bonds",       "name": "CA 30Y Yield",        "ticker": "CA30YT=RR", "type": "bond"},
    {"group": "Bonds",       "name": "Long Treasury (TLT)", "ticker": "TLT",       "type": "etf"},
    {"group": "Bonds",       "name": "High Yield (HYG)",    "ticker": "HYG",       "type": "etf"},
    {"group": "Bonds",       "name": "IG Credit (LQD)",     "ticker": "LQD",       "type": "etf"},
    {"group": "Commodities", "name": "Gold",                "ticker": "GC=F",      "type": "commodity"},
    {"group": "Commodities", "name": "WTI Oil",             "ticker": "CL=F",      "type": "commodity"},
    {"group": "Commodities", "name": "Brent Crude",         "ticker": "BZ=F",      "type": "commodity"},
    {"group": "Commodities", "name": "Silver",              "ticker": "SI=F",      "type": "commodity"},
    {"group": "Commodities", "name": "Copper",              "ticker": "HG=F",      "type": "commodity"},
    {"group": "Commodities", "name": "Natural Gas",         "ticker": "NG=F",      "type": "commodity"},
    {"group": "Commodities", "name": "Platinum",            "ticker": "PL=F",      "type": "commodity"},
    {"group": "Commodities", "name": "Corn",                "ticker": "ZC=F",      "type": "commodity"},
    {"group": "Commodities", "name": "Wheat",               "ticker": "ZW=F",      "type": "commodity"},
    {"group": "Currencies",  "name": "DXY (USD Index)",     "ticker": "DX-Y.NYB",  "type": "currency"},
    {"group": "Currencies",  "name": "EUR/USD",             "ticker": "EURUSD=X",  "type": "currency"},
    {"group": "Currencies",  "name": "USD/JPY",             "ticker": "JPY=X",     "type": "currency"},
    {"group": "Currencies",  "name": "GBP/USD",             "ticker": "GBPUSD=X",  "type": "currency"},
    {"group": "Currencies",  "name": "USD/CHF",             "ticker": "CHF=X",     "type": "currency"},
    {"group": "Currencies",  "name": "AUD/USD",             "ticker": "AUDUSD=X",  "type": "currency"},
    {"group": "Currencies",  "name": "NZD/USD",             "ticker": "NZDUSD=X",  "type": "currency"},
    {"group": "Currencies",  "name": "USD/CAD",             "ticker": "USDCAD=X",  "type": "currency"},
    {"group": "Currencies",  "name": "USD/CNY",             "ticker": "CNY=X",     "type": "currency"},
    {"group": "Currencies",  "name": "USD/MXN",             "ticker": "MXN=X",     "type": "currency"},
    {"group": "Currencies",  "name": "USD/BRL",             "ticker": "BRL=X",     "type": "currency"},
    {"group": "Crypto",      "name": "Bitcoin",             "ticker": "BTC-USD",   "type": "crypto"},
    {"group": "Crypto",      "name": "Ethereum",            "ticker": "ETH-USD",   "type": "crypto"},
    {"group": "Volatility",  "name": "VIX",                 "ticker": "^VIX",      "type": "volatility"},
    {"group": "Volatility",  "name": "MOVE (Bond Vol)",     "ticker": "^MOVE",     "type": "volatility"},
    {"group": "Risk Proxies","name": "S&P 500 ETF (SPY)",   "ticker": "SPY",       "type": "etf"},
]

NEWS_FEEDS = [
    # ── Agences internationales ──────────────────────────────────────────────
    ("Reuters Top",      "https://feeds.reuters.com/reuters/topNews"),
    ("Reuters Biz",      "https://feeds.reuters.com/reuters/businessNews"),
    ("AP Business",      "https://apnews.com/rss"),
    # ── Médias financiers US ─────────────────────────────────────────────────
    ("CNBC Markets",     "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"),
    ("CNBC Economy",     "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258"),
    ("MarketWatch",      "https://feeds.marketwatch.com/marketwatch/topstories/"),
    ("WSJ Markets",      "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"),
    ("Yahoo Finance",    "https://finance.yahoo.com/news/rssindex"),
    ("Seeking Alpha",    "https://seekingalpha.com/market_currents.xml"),
    ("Investopedia",     "https://www.investopedia.com/feedbuilder/feed/getfeed/?feedName=rss_headline"),
    ("Barron's",         "https://www.barrons.com/xml/rss/3_7623.xml"),
    # ── Via Google News (Bloomberg, FT, Economist sans paywall) ─────────────
    ("Bloomberg/GN",     "https://news.google.com/rss/search?q=bloomberg+finance+markets&hl=en-US&gl=US&ceid=US:en"),
    ("FT/GN",            "https://news.google.com/rss/search?q=financial+times+markets+economy&hl=en-US&gl=US&ceid=US:en"),
    ("Economist/GN",     "https://news.google.com/rss/search?q=economist+finance+economy+rates&hl=en-US&gl=US&ceid=US:en"),
    ("ZeroHedge/GN",     "https://news.google.com/rss/search?q=site:zerohedge.com&hl=en-US&gl=US&ceid=US:en"),
    # ── Banques centrales & institutions ────────────────────────────────────
    ("Fed Reserve",      "https://www.federalreserve.gov/feeds/press_all.xml"),
    ("BIS/GN",           "https://news.google.com/rss/search?q=bis+bank+for+international+settlements+financial+stability&hl=en-US&gl=US&ceid=US:en"),
    ("IMF Blog",         "https://www.imf.org/en/Blogs/rss"),
    # ── Canada — English ────────────────────────────────────────────────────
    ("Globe & Mail",     "https://www.theglobeandmail.com/investing/markets/rss/"),
    ("Financial Post",   "https://financialpost.com/feed/"),
    ("BNN Bloomberg",    "https://www.bnnbloomberg.ca/feed/"),
    # ── Canada — Français ───────────────────────────────────────────────────
    ("Radio-Canada Éco", "https://ici.radio-canada.ca/rss/4159"),
    ("Les Affaires",     "https://www.lesaffaires.com/rss/nouvelles-economiques/"),
    ("La Presse Aff.",   "https://www.lapresse.ca/affaires/rss"),
    # ── Crypto ──────────────────────────────────────────────────────────────
    ("CoinDesk",         "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("CoinTelegraph",    "https://cointelegraph.com/rss"),
    # ── Reddit ──────────────────────────────────────────────────────────────
    ("r/investing",      "https://www.reddit.com/r/investing/.rss"),
    ("r/stocks",         "https://www.reddit.com/r/stocks/.rss"),
    ("r/wallstreetbets", "https://www.reddit.com/r/wallstreetbets/.rss"),
    ("r/economics",      "https://www.reddit.com/r/economics/.rss"),
    ("r/geopolitics",    "https://www.reddit.com/r/geopolitics/.rss"),
    ("r/CanadaFinance",  "https://www.reddit.com/r/PersonalFinanceCanada/.rss"),
]
_REDDIT_UA = "Mozilla/5.0 (compatible; market-dashboard/1.0)"
_FEEDS_WITH_UA = {
    "r/investing", "r/stocks", "r/wallstreetbets",
    "r/economics", "r/geopolitics", "r/CanadaFinance",
}

ECONOMIC_CALENDAR = [
    {"date": "2026-03-11", "event": "CPI YoY (Feb)",           "country": "US", "importance": "critical", "forecast": "2.4%",      "previous": "3.0%",        "actual": "2.4%"},
    {"date": "2026-03-11", "event": "Core CPI YoY (Feb)",      "country": "US", "importance": "critical", "forecast": "2.5%",      "previous": "3.3%",        "actual": "2.5%"},
    {"date": "2026-03-13", "event": "Initial Jobless Claims",  "country": "US", "importance": "medium",   "forecast": None,        "previous": "242K"},
    {"date": "2026-03-13", "event": "GDP Q4 2025 (2nd Est.)",  "country": "US", "importance": "high",     "forecast": "1.4%",      "previous": "1.4%"},
    {"date": "2026-03-13", "event": "PCE Price Index YoY",     "country": "US", "importance": "critical", "forecast": None,        "previous": "2.9%"},
    {"date": "2026-03-17", "event": "US Retail Sales (Feb)",   "country": "US", "importance": "high",     "forecast": None,        "previous": "-0.2%"},
    {"date": "2026-03-17", "event": "FOMC Meeting Begins",     "country": "US", "importance": "high",     "forecast": None,        "previous": None},
    {"date": "2026-03-18", "event": "FOMC Rate Decision",      "country": "US", "importance": "critical", "forecast": "No change", "previous": "3.50-3.75%"},
    {"date": "2026-03-18", "event": "Powell Press Conference", "country": "US", "importance": "critical", "forecast": None,        "previous": None},
    {"date": "2026-03-19", "event": "BOJ Rate Decision",       "country": "JP", "importance": "high",     "forecast": None,        "previous": "0.50%"},
    {"date": "2026-03-26", "event": "Consumer Confidence",     "country": "US", "importance": "medium",   "forecast": None,        "previous": "104.1"},
    {"date": "2026-04-01", "event": "ISM Manufacturing PMI",   "country": "US", "importance": "high",     "forecast": None,        "previous": "50.3"},
    {"date": "2026-04-03", "event": "Non-Farm Payrolls (Mar)", "country": "US", "importance": "critical", "forecast": None,        "previous": "200K"},
    {"date": "2026-04-10", "event": "CPI (Mar)",               "country": "US", "importance": "critical", "forecast": None,        "previous": "2.4%"},
    {"date": "2026-04-29", "event": "FOMC Rate Decision",      "country": "US", "importance": "critical", "forecast": None,        "previous": "3.50-3.75%"},
    {"date": "2026-04-30", "event": "GDP Q1 2026 (Advance)",   "country": "US", "importance": "high",     "forecast": None,        "previous": "2.3%"},
]

GEOPOLITICAL_RISKS = [
    {"region": "Europe",      "title": "Ukraine-Russia War",            "level": "high",   "icon": "sword",          "description": "Active conflict; ceasefire talks ongoing. NATO supply lines under pressure.",        "market_impact": "Energy prices, European equities, EUR weakness"},
    {"region": "Middle East", "title": "Middle East Tensions",          "level": "high",   "icon": "flame",          "description": "Regional escalation risks; Red Sea shipping disruptions.",                         "market_impact": "Oil premium, shipping costs, global inflation"},
    {"region": "Asia Pacific","title": "Taiwan Strait / China-US",      "level": "medium", "icon": "alert-triangle", "description": "Elevated military activity; US-China strategic competition intensifying.",          "market_impact": "Tech supply chains, semiconductors, Asian equities"},
    {"region": "Americas",    "title": "US-China Trade War",            "level": "medium", "icon": "trending-down",  "description": "Tariff escalation; supply chain decoupling in critical sectors.",                 "market_impact": "Global trade, tech sector, EM currencies"},
    {"region": "Global",      "title": "Central Bank Policy Divergence","level": "medium", "icon": "bar-chart-2",    "description": "Fed vs ECB vs BOJ divergent paths creating currency volatility.",                 "market_impact": "USD strength, carry trades, EM debt"},
    {"region": "Americas",    "title": "US Fiscal Sustainability",      "level": "low",    "icon": "dollar-sign",    "description": "Debt ceiling concerns; rising deficit affecting bond market sentiment.",            "market_impact": "Treasury yields, USD long-term, sovereign ratings"},
]

CENTRAL_BANK_RATES = [
    {"flag": "🇺🇸", "name": "États-Unis",  "bank": "Fed",  "rate": "3.50–3.75%", "bias": "neutral",  "change": "=",  "next_meeting": "17-18 mars 2026"},
    {"flag": "🇪🇺", "name": "Zone Euro",   "bank": "BCE",  "rate": "2.65%",      "bias": "dovish",   "change": "↓",  "next_meeting": "17 avr. 2026"},
    {"flag": "🇨🇦", "name": "Canada",      "bank": "BdC",  "rate": "3.00%",      "bias": "dovish",   "change": "↓",  "next_meeting": "16 avr. 2026"},
    {"flag": "🇬🇧", "name": "Royaume-Uni", "bank": "BOE",  "rate": "4.50%",      "bias": "neutral",  "change": "↓",  "next_meeting": "8 mai 2026"},
    {"flag": "🇯🇵", "name": "Japon",       "bank": "BOJ",  "rate": "0.50%",      "bias": "hawkish",  "change": "↑",  "next_meeting": "19 mars 2026"},
    {"flag": "🇨🇭", "name": "Suisse",      "bank": "BNS",  "rate": "0.25%",      "bias": "neutral",  "change": "↓",  "next_meeting": "20 mars 2026"},
]

BOC_SERIES = {
    "CA2YT=RR":  "BD.CDN.2YR.DQ.YLD",
    "CA5YT=RR":  "BD.CDN.5YR.DQ.YLD",
    "CA10YT=RR": "BD.CDN.10YR.DQ.YLD",
    "CA30YT=RR": "BD.CDN.LONG.DQ.YLD",
}

YIELD_TICKERS = {"^IRX", "^FVX", "^TNX", "^TYX",
                 "CA2YT=RR", "CA5YT=RR", "CA10YT=RR", "CA30YT=RR"}

# ── Oil & LNG static data ────────────────────────────────────────────────────
OIL_LNG_ASSETS = [
    {"group": "Futures",           "name": "WTI Crude",          "ticker": "CL=F",  "type": "commodity"},
    {"group": "Futures",           "name": "Brent Crude",         "ticker": "BZ=F",  "type": "commodity"},
    {"group": "Futures",           "name": "Henry Hub Gas",       "ticker": "NG=F",  "type": "commodity"},
    {"group": "Futures",           "name": "RBOB Gasoline",       "ticker": "RB=F",  "type": "commodity"},
    {"group": "Futures",           "name": "Heating Oil",         "ticker": "HO=F",  "type": "commodity"},
    {"group": "ETFs",              "name": "Energy Sector",       "ticker": "XLE",   "type": "etf"},
    {"group": "ETFs",              "name": "Oil & Gas E&P",       "ticker": "XOP",   "type": "etf"},
    {"group": "ETFs",              "name": "Oil Services",        "ticker": "OIH",   "type": "etf"},
    {"group": "ETFs",              "name": "Natural Gas",         "ticker": "UNG",   "type": "etf"},
    {"group": "Integrated Majors", "name": "ExxonMobil",          "ticker": "XOM",   "type": "stock"},
    {"group": "Integrated Majors", "name": "Chevron",             "ticker": "CVX",   "type": "stock"},
    {"group": "Integrated Majors", "name": "Shell",               "ticker": "SHEL",  "type": "stock"},
    {"group": "Integrated Majors", "name": "TotalEnergies",       "ticker": "TTE",   "type": "stock"},
    {"group": "Integrated Majors", "name": "BP",                  "ticker": "BP",    "type": "stock"},
    {"group": "E&P",               "name": "ConocoPhillips",      "ticker": "COP",   "type": "stock"},
    {"group": "E&P",               "name": "EOG Resources",       "ticker": "EOG",   "type": "stock"},
    {"group": "E&P",               "name": "Devon Energy",        "ticker": "DVN",   "type": "stock"},
    {"group": "E&P",               "name": "Diamondback Energy",  "ticker": "FANG",  "type": "stock"},
    {"group": "Canadian Energy",   "name": "Canadian Natural",    "ticker": "CNQ",   "type": "stock"},
    {"group": "Canadian Energy",   "name": "Suncor Energy",       "ticker": "SU",    "type": "stock"},
    {"group": "Canadian Energy",   "name": "Enbridge",            "ticker": "ENB",   "type": "stock"},
    {"group": "LNG Players",       "name": "Cheniere Energy",     "ticker": "LNG",   "type": "stock"},
    {"group": "LNG Players",       "name": "New Fortress Energy", "ticker": "NFE",   "type": "stock"},
    {"group": "LNG Players",       "name": "NextDecade",          "ticker": "NEXT",  "type": "stock"},
    {"group": "LNG Players",       "name": "Golar LNG",           "ticker": "GLNG",  "type": "stock"},
    {"group": "Services",          "name": "SLB",                 "ticker": "SLB",   "type": "stock"},
    {"group": "Services",          "name": "Halliburton",         "ticker": "HAL",   "type": "stock"},
    {"group": "Services",          "name": "Baker Hughes",        "ticker": "BKR",   "type": "stock"},
    {"group": "Refiners",          "name": "Phillips 66",         "ticker": "PSX",   "type": "stock"},
    {"group": "Refiners",          "name": "Marathon Petroleum",  "ticker": "MPC",   "type": "stock"},
    {"group": "Refiners",          "name": "Valero Energy",       "ticker": "VLO",   "type": "stock"},
]

EIA_INVENTORY = {
    "report_date":   "2026-03-19",
    "crude_oil":     {"value": 437.2, "change": -2.1, "unit": "MMbbl", "label": "Crude Oil"},
    "gasoline":      {"value": 241.5, "change": +1.3, "unit": "MMbbl", "label": "Gasoline"},
    "distillates":   {"value": 117.8, "change": -0.8, "unit": "MMbbl", "label": "Distillates"},
    "cushing":       {"value":  26.4, "change": -1.2, "unit": "MMbbl", "label": "Cushing, OK"},
    "spr":           {"value": 395.2, "change":  0.0, "unit": "MMbbl", "label": "SPR"},
    "refinery_util": {"value":  87.3, "change": +0.6, "unit": "%",     "label": "Refinery Util."},
}

OPEC_DATA = {
    "report_month":            "February 2026",
    "total_production_mmbpd":  26.8,
    "opec_plus_target_mmbpd":  26.5,
    "compliance_pct":           89,
    "surplus_mmbpd":            0.3,
    "next_meeting":             "June 2026",
    "key_producers": [
        {"country": "Saudi Arabia", "flag": "SA", "production": 9.0, "quota": 9.0},
        {"country": "Russia",       "flag": "RU", "production": 9.1, "quota": 9.0},
        {"country": "UAE",          "flag": "AE", "production": 3.0, "quota": 2.9},
        {"country": "Iraq",         "flag": "IQ", "production": 4.1, "quota": 4.0},
        {"country": "Kuwait",       "flag": "KW", "production": 2.5, "quota": 2.5},
    ],
}

ENERGY_GEO_RISKS = [
    {"region": "Middle East",    "title": "Strait of Hormuz",        "level": "high",   "icon": "ship",           "description": "~20% of global oil & LNG transits this chokepoint. Iran tensions elevated.",       "market_impact": "+$8-15/bbl if closure risk escalates"},
    {"region": "Russia / Europe","title": "Russian Gas Supply",      "level": "high",   "icon": "flame",          "description": "Nord Stream offline; pipeline routes uncertain. European LNG imports at record highs.", "market_impact": "Persistent EU LNG premium vs Henry Hub"},
    {"region": "US Gulf Coast",  "title": "LNG Export Expansion",    "level": "medium", "icon": "anchor",         "description": "Sabine Pass T6, Corpus Christi T3, Plaquemines LNG underway. US share rising.",      "market_impact": "Structurally bullish Henry Hub long-term"},
    {"region": "Libya / Nigeria","title": "African Supply Disruptions","level": "medium","icon": "alert-triangle","description": "Periodic outages from political instability and pipeline sabotage.",                   "market_impact": "+$2-5/bbl on major disruption events"},
    {"region": "South America",  "title": "Venezuela / Guyana",      "level": "low",    "icon": "trending-up",    "description": "Guyana ramp-up bullish for Atlantic basin. Venezuela sanctions cap output.",          "market_impact": "Net neutral; Guyana growth offsets Venezuela"},
]

ENERGY_NEWS_FEEDS = [
    ("EIA Today",   "https://www.eia.gov/rss/todayinenergy.xml"),
    ("Reuters Biz", "https://feeds.reuters.com/reuters/businessNews"),
    ("Oil/LNG",     "https://news.google.com/rss/search?q=oil+LNG+OPEC+crude+natural+gas&hl=en-US&gl=US&ceid=US:en"),
    ("Energy Mkts", "https://news.google.com/rss/search?q=energy+market+petroleum+refinery+gasoline&hl=en-US&gl=US&ceid=US:en"),
]

# ── Data helpers ────────────────────────────────────────────────────────────
def _fetch_one(ticker):
    try:
        hist = yf.Ticker(ticker).history(period="5d", auto_adjust=True).dropna(subset=["Close"])
        if len(hist) >= 2:
            c, p = float(hist["Close"].iloc[-1]), float(hist["Close"].iloc[-2])
            ch = c - p
            return ticker, {"price": round(c, 4), "change": round(ch, 4),
                            "change_pct": round((ch / p) * 100, 2),
                            "timestamp": hist.index[-1].isoformat()}
        elif len(hist) == 1:
            c = float(hist["Close"].iloc[-1])
            return ticker, {"price": round(c, 4), "change": None,
                            "change_pct": None, "timestamp": hist.index[-1].isoformat()}
    except Exception as e:
        logger.warning(f"Error fetching {ticker}: {e}")
    return ticker, {"price": None, "change": None, "change_pct": None, "timestamp": None}


@st.cache_data(ttl=60, show_spinner=False)
def _market_data_cached():
    tickers = list({a["ticker"] for a in MARKET_ASSETS})
    result = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(_fetch_one, t): t for t in tickers}
        for f in as_completed(futures, timeout=30):
            try:
                ticker, data = f.result()
                result[ticker] = data
            except Exception as e:
                logger.warning(f"Future: {e}")
    return result


@st.cache_data(ttl=300, show_spinner=False)
def _ca_yields_cached():
    today       = datetime.now(timezone.utc).date()
    year_start  = today.replace(month=1, day=1).isoformat()
    month_start = today.replace(day=1).isoformat()
    result = {}
    for ticker, series in BOC_SERIES.items():
        try:
            url = (f"https://www.bankofcanada.ca/valet/observations/{series}/json"
                   f"?start_date={year_start}&end_date={today.isoformat()}")
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())
            obs = [o for o in data.get("observations", [])
                   if o.get(series, {}).get("v") not in (None, "")]
            if not obs:
                result[ticker] = {"price": None, "change": None, "change_pct": None,
                                   "mtd": None, "aad": None, "timestamp": None}
                continue
            latest = float(obs[-1][series]["v"])
            change = change_pct = None
            if len(obs) >= 2:
                prev = float(obs[-2][series]["v"])
                change = round(latest - prev, 3)
                change_pct = round((change / prev) * 100, 2) if prev else None
            # AAD: absolute pp change since Jan 1
            aad = round(latest - float(obs[0][series]["v"]), 2) if obs else None
            # MTD: absolute pp change since month start
            month_obs = [o for o in obs if o["d"] >= month_start]
            mtd = round(latest - float(month_obs[0][series]["v"]), 2) if month_obs else aad
            result[ticker] = {"price": round(latest, 3), "change": change,
                               "change_pct": change_pct, "mtd": mtd, "aad": aad,
                               "timestamp": obs[-1]["d"]}
        except Exception as e:
            logger.warning(f"BOC {series}: {e}")
            result[ticker] = {"price": None, "change": None, "change_pct": None,
                               "mtd": None, "aad": None, "timestamp": None}
    return result


@st.cache_data(ttl=300, show_spinner=False)
def _vix_history_cached():
    try:
        hist = yf.Ticker("^VIX").history(period="30d").dropna(subset=["Close"])
        return [{"date": str(idx.date()), "value": round(float(row["Close"]), 2)}
                for idx, row in hist.iterrows()]
    except Exception as e:
        logger.error(f"VIX history: {e}")
        return []


@st.cache_data(ttl=300, show_spinner=False)
def _news_cached():
    all_items = []
    seen_titles: set = set()

    for source, url in NEWS_FEEDS:
        try:
            headers = {"User-Agent": _REDDIT_UA} if source in _FEEDS_WITH_UA else {
                "User-Agent": "Mozilla/5.0 (compatible; MarketDashboard/2.0; +https://fondaction.com)"
            }
            feed = feedparser.parse(url, request_headers=headers)
            count = 0
            for entry in feed.entries:
                if count >= 4:
                    break
                title   = getattr(entry, "title", "").strip()
                link    = getattr(entry, "link", "#")
                summary = getattr(entry, "summary", getattr(entry, "description", ""))

                # Deduplicate by normalized title
                title_key = title.lower()[:80]
                if not title or title_key in seen_titles:
                    continue
                seen_titles.add(title_key)

                tl   = title.lower()
                tags = []

                # Geopolitical
                if any(w in tl for w in [
                    "war","conflict","attack","strike","military","nuclear",
                    "sanctions","nato","ukraine","russia","china","taiwan",
                    "iran","israel","hamas","missile","coup","troops",
                ]):
                    tags.append("geopolitical")

                # Economic / macro
                if any(w in tl for w in [
                    "inflation","rate","fed","ecb","boj","bdc","bank of canada",
                    "gdp","jobs","recession","cpi","ppi","fomc","monetary",
                    "interest rate","taux","banque centrale","emploi","pib",
                ]):
                    tags.append("economic")

                # Markets
                if any(w in tl for w in [
                    "market","stock","equity","bond","gold","oil","crypto",
                    "bitcoin","rally","sell-off","crash","bourse","marché",
                    "s&p","nasdaq","dow","tsx","vix","yield","spread",
                ]):
                    tags.append("market")

                # Crypto
                if any(w in tl for w in [
                    "bitcoin","ethereum","crypto","blockchain","defi","nft",
                    "binance","coinbase","stablecoin","altcoin","solana","btc","eth",
                ]):
                    tags.append("crypto")

                # Canada
                if any(w in tl for w in [
                    "canada","canadian","bdc","boc","tsx","loonie","ontario",
                    "québec","quebec","alberta","ottawa","trudeau","carney",
                ]) or source in {"Globe & Mail","Financial Post","BNN Bloomberg",
                                  "Radio-Canada Éco","Les Affaires","La Presse Aff.",
                                  "r/CanadaFinance"}:
                    tags.append("canada")

                all_items.append({
                    "title":     title,
                    "source":    source,
                    "url":       link,
                    "published": getattr(entry, "published", ""),
                    "summary":   (summary[:200] + "…") if len(summary) > 200 else summary,
                    "tags":      tags,
                })
                count += 1
        except Exception as e:
            logger.warning(f"Feed {source}: {e}")

    return all_items[:60]


# ── MISO: Technical helpers ──────────────────────────────────────────────────

def _calc_rsi(series, period: int = 9):
    """Wilder-smoothed RSI(period). Returns last value or None."""
    try:
        delta = series.diff().dropna()
        if len(delta) < period + 1:
            return None
        gain = delta.clip(lower=0).ewm(com=period - 1, min_periods=period).mean()
        loss = (-delta.clip(upper=0)).ewm(com=period - 1, min_periods=period).mean()
        rs   = gain / loss.replace(0, float("inf"))
        rsi  = 100.0 - (100.0 / (1.0 + rs))
        return round(float(rsi.iloc[-1]), 1)
    except Exception:
        return None


def _calc_bb_pct_b(series, period: int = 20, k: float = 2.0):
    """Bollinger %B = (price − lower) / (upper − lower). >1 = above upper band."""
    try:
        if len(series) < period:
            return None
        sma   = series.rolling(period).mean()
        std   = series.rolling(period).std(ddof=0)
        upper = float((sma + k * std).iloc[-1])
        lower = float((sma - k * std).iloc[-1])
        px    = float(series.iloc[-1])
        if upper == lower:
            return 0.5
        return round((px - lower) / (upper - lower), 3)
    except Exception:
        return None


def _calc_demark(closes):
    """Simplified DeMark Sequential: count consecutive bars where Close < Close[-4] (buy)
    or > Close[-4] (sell). Returns (setup_count, countdown_count, direction)."""
    try:
        arr = closes.values
        n   = len(arr)
        if n < 5:
            return 0, 0, "neutral"
        is_buy  = arr[-1] < arr[-5]
        is_sell = arr[-1] > arr[-5]
        count = 0
        if is_buy:
            for i in range(n - 1, max(n - 10, 3), -1):
                if arr[i] < arr[i - 4]:
                    count += 1
                else:
                    break
            return min(count, 9), 0, "buy"
        elif is_sell:
            for i in range(n - 1, max(n - 10, 3), -1):
                if arr[i] > arr[i - 4]:
                    count += 1
                else:
                    break
            return min(count, 9), 0, "sell"
        return 0, 0, "neutral"
    except Exception:
        return 0, 0, "neutral"


@st.cache_data(ttl=300, show_spinner=False)
def fetch_miso() -> dict:
    """Market Immune System Oscillator — 5 composantes, score 100 = plus survendu."""
    import math
    _empty: dict = {
        "composite": None, "status": "N/A", "color": "#64748b",
        "signal": "Données insuffisantes", "emoji": "⚪", "components": [],
    }
    try:
        spx   = yf.Ticker("^GSPC").history(period="3mo")["Close"].dropna()
        vix   = yf.Ticker("^VIX").history(period="3mo")["Close"].dropna()
        nyad  = yf.Ticker("^NYAD").history(period="3mo")["Close"].dropna()
        vix3m = yf.Ticker("^VIX3M").history(period="3mo")["Close"].dropna()
        if len(vix3m) < 2:
            vix3m = yf.Ticker("^VXMT").history(period="3mo")["Close"].dropna()
    except Exception:
        return _empty

    components: list = []

    # 1. NYSE Breadth RSI(9) — score = 100 − RSI (oversold breadth → high score)
    if len(nyad) >= 10:
        br_rsi = _calc_rsi(nyad, 9)
        if br_rsi is not None:
            components.append({
                "name": "NYSE Breadth RSI(9)", "weight": 20,
                "raw_label": f"RSI = {br_rsi}",
                "score": round(100 - br_rsi, 1),
                "desc": "Survendu (bas RSI) → score élevé",
            })

    # 2. VIX Bollinger %B — score = clamp(%B × 100, 0, 100)
    if len(vix) >= 21:
        bb = _calc_bb_pct_b(vix)
        if bb is not None:
            components.append({
                "name": "VIX Bollinger %B", "weight": 25,
                "raw_label": f"%B = {bb:.2f}",
                "score": round(min(100.0, max(0.0, bb * 100)), 1),
                "desc": "VIX > bande sup. → panique extrême",
            })

    # 3. SPX RSI(9) — score = 100 − RSI
    if len(spx) >= 10:
        spx_rsi = _calc_rsi(spx, 9)
        if spx_rsi is not None:
            components.append({
                "name": "SPX RSI(9)", "weight": 25,
                "raw_label": f"RSI = {spx_rsi}",
                "score": round(100 - spx_rsi, 1),
                "desc": "SPX survendu → rebond potentiel",
            })

    # 4. VIX Term Structure — VIX / VIX3M via sigmoid (50 at ratio=1, ~98.5 at ratio=1.93)
    if len(vix) >= 2 and len(vix3m) >= 2:
        vix_last = float(vix.iloc[-1])
        v3m_last = float(vix3m.iloc[-1])
        if v3m_last > 0:
            ratio = round(vix_last / v3m_last, 3)
            sc_ts = round(100.0 / (1.0 + math.exp(-4.5 * (ratio - 1.0))), 1)
            components.append({
                "name": "VIX Term Structure", "weight": 20,
                "raw_label": f"VIX/VIX3M = {ratio:.2f}",
                "score": sc_ts,
                "desc": "Backwardation (VIX > VIX3M) → panique",
            })

    # 5. DeMark Sequential — buy setup progress toward 9/9
    if len(spx) >= 13:
        setup, countdown, direction = _calc_demark(spx)
        if direction == "buy":
            sc_dm = round(min(100.0, (setup / 9) * 45 + (countdown / 13) * 55), 1)
        elif direction == "sell":
            sc_dm = round(max(0.0, 50 - (setup / 9) * 50), 1)
        else:
            sc_dm = 50.0
        dir_lbl = "▼ Achat" if direction == "buy" else "▲ Vente" if direction == "sell" else "→ Neutre"
        components.append({
            "name": "DeMark Sequential", "weight": 10,
            "raw_label": f"Setup: {setup}/9 · CD: {countdown}/13 ({dir_lbl})",
            "score": sc_dm,
            "desc": "Setup achat complet → zone retournement",
        })

    if not components:
        return _empty

    total_w   = sum(c["weight"] for c in components)
    composite = round(sum(c["score"] * c["weight"] for c in components) / total_w, 1)

    if composite >= 75:
        status, color, emoji = "APPROACHING OVERSOLD", "#ef4444", "🔴"
        signal = "Stress extrême — conditions de retournement haussier potentiel"
    elif composite >= 55:
        status, color, emoji = "ELEVATED STRESS", "#f59e0b", "🟡"
        signal = "Stress élevé — surveiller les signaux de retournement"
    elif composite >= 40:
        status, color, emoji = "NEUTRAL", "#94a3b8", "⚪"
        signal = "Conditions équilibrées — pas de signal directionnel fort"
    elif composite >= 25:
        status, color, emoji = "MILD OVERBOUGHT", "#3b82f6", "🔵"
        signal = "Marché solide — légère surchauffe potentielle"
    else:
        status, color, emoji = "OVERBOUGHT", "#22c55e", "🟢"
        signal = "Complacence extrême — surveiller signal retournement baissier"

    return {
        "composite": composite, "status": status, "color": color,
        "signal": signal, "emoji": emoji, "components": components,
    }


def _risk_score(market_data):
    signals = []; ws = 0.0; tw = 0.0

    def add(name, value, unit, score, label, status, weight, desc):
        nonlocal ws, tw
        signals.append({"name": name, "value": value, "unit": unit,
                         "score": round(float(score), 1), "label": label,
                         "status": status, "weight": weight, "description": desc})
        ws += float(score) * weight; tw += weight

    vix = market_data.get("^VIX", {}).get("price")
    if vix is not None:
        if   vix < 12: sc, lbl, st = 92, "Complacent",     "risk-on"
        elif vix < 15: sc, lbl, st = 80, "Low Volatility", "risk-on"
        elif vix < 18: sc, lbl, st = 65, "Normal",         "neutral"
        elif vix < 22: sc, lbl, st = 48, "Elevated",       "neutral"
        elif vix < 27: sc, lbl, st = 28, "High Fear",      "risk-off"
        elif vix < 35: sc, lbl, st = 14, "Very High Fear", "risk-off"
        else:          sc, lbl, st =  5, "Extreme Fear",   "risk-off"
        add("VIX Fear Index", vix, "", sc, lbl, st, 25, "Market volatility gauge")

    spy = market_data.get("SPY", {}).get("change_pct") or market_data.get("^GSPC", {}).get("change_pct")
    if spy is not None:
        sc = max(0.0, min(100.0, 50.0 + spy * 9.0))
        lbl, st = ("Equities Strong","risk-on") if sc>65 else ("Equities Mixed","neutral") if sc>38 else ("Equities Weak","risk-off")
        add("S&P 500 (Equities)", spy, "%", sc, lbl, st, 15, "Equity direction")

    for ticker, weight, fname in [("GC=F",12,"Gold"),("DX-Y.NYB",12,"DXY"),("TLT",12,"TLT")]:
        pct = market_data.get(ticker, {}).get("change_pct")
        if pct is not None:
            sc = max(0.0, min(100.0, 50.0 - pct * 14.0))
            lbl, st = ("Selling (risk-on)","risk-on") if sc>65 else ("Neutral","neutral") if sc>38 else ("Safe-Haven Rally","risk-off")
            add(fname, pct, "%", sc, lbl, st, weight, f"{fname} safe-haven signal")

    hyg = market_data.get("HYG", {}).get("change_pct")
    lqd = market_data.get("LQD", {}).get("change_pct")
    if hyg is not None and lqd is not None:
        sp = hyg - lqd; sc = max(0.0, min(100.0, 50.0 + sp * 18.0))
        lbl, st = ("HY Outperforming","risk-on") if sc>65 else ("Credit Neutral","neutral") if sc>38 else ("IG Outperforming","risk-off")
        add("HY vs IG Credit", round(sp,2), "% spread", sc, lbl, st, 12, "Credit spread signal")

    eem = market_data.get("EEM", {}).get("change_pct")
    if eem is not None and spy is not None:
        em = eem - spy; sc = max(0.0, min(100.0, 50.0 + em * 18.0))
        lbl, st = ("EM Outperforming","risk-on") if sc>65 else ("EM In-Line","neutral") if sc>38 else ("EM Underperforming","risk-off")
        add("EM vs Developed", round(eem,2), "%", sc, lbl, st, 12, "EM appetite signal")

    comp = round(ws / tw, 1) if tw > 0 else 50.0
    if   comp >= 72: label, color, desc = "RISK-ON",             "green", "Strong risk appetite."
    elif comp >= 58: label, color, desc = "MODERATELY RISK-ON",  "green", "Moderate risk appetite."
    elif comp >= 42: label, color, desc = "NEUTRAL",             "amber", "Mixed signals — balanced positioning recommended."
    elif comp >= 28: label, color, desc = "MODERATELY RISK-OFF", "red",   "Defensive positioning emerging."
    else:            label, color, desc = "RISK-OFF",            "red",   "Full flight-to-safety."
    return {"score": comp, "label": label, "color": color, "description": desc, "signals": signals}


@st.cache_data(ttl=60, show_spinner=False)
def _oil_data_cached() -> dict:
    tickers = list({a["ticker"] for a in OIL_LNG_ASSETS}) + ["SPY"]
    result: dict = {}
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {ex.submit(_fetch_one, t): t for t in tickers}
        for f in as_completed(futures, timeout=30):
            try:
                ticker, data = f.result()
                result[ticker] = data
            except Exception as e:
                logger.warning(f"Oil future: {e}")
    return result


@st.cache_data(ttl=300, show_spinner=False)
def _oil_history_cached() -> dict:
    result: dict = {"wti": [], "brent": [], "gas": []}
    for key, ticker in {"wti": "CL=F", "brent": "BZ=F", "gas": "NG=F"}.items():
        try:
            hist = yf.Ticker(ticker).history(period="90d", auto_adjust=True).dropna(subset=["Close"])
            result[key] = [{"date": str(idx.date()), "value": round(float(row["Close"]), 3)}
                           for idx, row in hist.iterrows()]
        except Exception as e:
            logger.error(f"Oil hist {ticker}: {e}")
    return result


@st.cache_data(ttl=300, show_spinner=False)
def _energy_news_cached() -> list:
    items: list = []
    seen: set   = set()
    for source, url in ENERGY_NEWS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                title = getattr(entry, "title", "").strip()
                key   = title.lower()[:80]
                if not title or key in seen:
                    continue
                seen.add(key)
                tl, tags = title.lower(), []
                if any(w in tl for w in ["opec","saudi","aramco","quota","cut"]):      tags.append("opec")
                if any(w in tl for w in ["lng","liquefied","natural gas","henry hub"]): tags.append("lng")
                if any(w in tl for w in ["eia","inventory","stockpile","supply"]):      tags.append("supply")
                if any(w in tl for w in ["refin","crack","gasoline","distillate"]):     tags.append("refining")
                if any(w in tl for w in ["wti","brent","crude","oil price","barrel"]):  tags.append("crude")
                summary = getattr(entry, "summary", getattr(entry, "description", ""))
                items.append({"title": title, "source": source, "url": getattr(entry, "link", "#"),
                               "published": getattr(entry, "published", ""),
                               "summary": (summary[:180] + "...") if len(summary) > 180 else summary,
                               "tags": tags})
        except Exception as e:
            logger.warning(f"Energy feed {source}: {e}")
    return items[:20]


def _calc_energy_score(raw: dict) -> dict:
    signals: list = []
    ws = tw = 0.0

    def add(name, value, unit, score, label, status, weight, desc):
        nonlocal ws, tw
        signals.append({"name": name, "value": value, "unit": unit, "score": round(float(score), 1),
                         "label": label, "status": status, "weight": weight, "description": desc})
        ws += float(score) * weight; tw += weight

    wti_pct = raw.get("CL=F", {}).get("change_pct")
    if wti_pct is not None:
        sc = max(0.0, min(100.0, 50.0 + wti_pct * 8.0))
        add("WTI Crude Oil", wti_pct, "%", sc,
            "WTI Rising" if sc>60 else ("WTI Falling" if sc<40 else "WTI Stable"),
            "bullish" if sc>60 else ("bearish" if sc<40 else "neutral"), 20, "WTI benchmark direction")

    brent_pct = raw.get("BZ=F", {}).get("change_pct")
    if brent_pct is not None:
        sc = max(0.0, min(100.0, 50.0 + brent_pct * 8.0))
        add("Brent Crude", brent_pct, "%", sc,
            "Brent Rising" if sc>60 else ("Brent Falling" if sc<40 else "Brent Stable"),
            "bullish" if sc>60 else ("bearish" if sc<40 else "neutral"), 15, "Brent global benchmark")

    ng_pct = raw.get("NG=F", {}).get("change_pct")
    if ng_pct is not None:
        sc = max(0.0, min(100.0, 50.0 + ng_pct * 7.0))
        add("Henry Hub Nat. Gas", ng_pct, "%", sc,
            "Gas Rising" if sc>60 else ("Gas Falling" if sc<40 else "Gas Stable"),
            "bullish" if sc>60 else ("bearish" if sc<40 else "neutral"), 15, "US natural gas benchmark")

    xle_pct = raw.get("XLE", {}).get("change_pct")
    if xle_pct is not None:
        sc = max(0.0, min(100.0, 50.0 + xle_pct * 9.0))
        add("Energy Sector (XLE)", xle_pct, "%", sc,
            "Energy Strong" if sc>60 else ("Energy Weak" if sc<40 else "Energy Neutral"),
            "bullish" if sc>60 else ("bearish" if sc<40 else "neutral"), 15, "Broad energy equity sentiment")

    spy_pct = raw.get("SPY", {}).get("change_pct")
    if xle_pct is not None and spy_pct is not None:
        rel = xle_pct - spy_pct; sc = max(0.0, min(100.0, 50.0 + rel * 15.0))
        add("Energy vs Market (XLE/SPY)", round(rel, 2), "% rel.", sc,
            "Energy Outperforming" if sc>60 else ("Energy Underperforming" if sc<40 else "Energy In-Line"),
            "bullish" if sc>60 else ("bearish" if sc<40 else "neutral"), 20, "Sector rotation signal")

    rbob_pct = raw.get("RB=F", {}).get("change_pct")
    if rbob_pct is not None and wti_pct is not None:
        crack = rbob_pct - wti_pct; sc = max(0.0, min(100.0, 50.0 + crack * 12.0))
        add("Crack Spread (RBOB/WTI)", round(crack, 2), "% rel.", sc,
            "Crack Widening" if sc>60 else ("Crack Narrowing" if sc<40 else "Crack Stable"),
            "bullish" if sc>60 else ("bearish" if sc<40 else "neutral"), 15, "Refinery margin proxy")

    composite = round(ws / tw, 1) if tw > 0 else 50.0
    if   composite >= 70: label, color, desc = "BULLISH",            "green", "Strong energy momentum. Oil prices rising, sector outperforming."
    elif composite >= 58: label, color, desc = "MODERATELY BULLISH", "green", "Positive energy bias. Favorable conditions for oil & gas producers."
    elif composite >= 42: label, color, desc = "NEUTRAL",            "amber", "Mixed energy signals. Range-bound prices, balanced supply/demand."
    elif composite >= 30: label, color, desc = "MODERATELY BEARISH", "red",   "Weak energy conditions. Demand concerns or oversupply building."
    else:                 label, color, desc = "BEARISH",            "red",   "Energy sector under pressure. Price decline risk elevated."
    return {"score": composite, "label": label, "color": color, "description": desc, "signals": signals}


@st.cache_data(ttl=60, show_spinner="Loading energy market data...")
def _full_oil_data() -> dict:
    raw          = _oil_data_cached()
    energy_score = _calc_energy_score(raw)
    assets = [{**a, "price": raw.get(a["ticker"], {}).get("price"),
                    "change": raw.get(a["ticker"], {}).get("change"),
                    "change_pct": raw.get(a["ticker"], {}).get("change_pct"),
                    "timestamp":  raw.get(a["ticker"], {}).get("timestamp")}
              for a in OIL_LNG_ASSETS]
    return {"energy_score": energy_score, "assets": assets,
            "eia": EIA_INVENTORY, "opec": OPEC_DATA,
            "geo_risks": ENERGY_GEO_RISKS, "news": _energy_news_cached(),
            "last_updated": datetime.now(timezone.utc).isoformat()}


@st.cache_data(ttl=300, show_spinner=False)
def _period_perf_cached() -> dict:
    """Fetch MTD and AAD (YTD) performance for all non-BOC tickers."""
    non_boc = [a["ticker"] for a in MARKET_ASSETS if a["ticker"] not in BOC_SERIES]

    def _fetch_perf(ticker):
        try:
            hist = yf.Ticker(ticker).history(period="ytd", auto_adjust=True).dropna(subset=["Close"])
            if len(hist) < 1:
                return ticker, {"mtd": None, "aad": None}
            latest = float(hist["Close"].iloc[-1])
            year_start_val = float(hist["Close"].iloc[0])
            is_yield = ticker in YIELD_TICKERS
            if is_yield:
                aad = round(latest - year_start_val, 2)
            else:
                aad = round((latest - year_start_val) / year_start_val * 100, 2) if year_start_val else None
            # MTD: filter rows from the 1st of current month
            month_start = hist.index[0].replace(
                year=datetime.now(timezone.utc).year,
                month=datetime.now(timezone.utc).month,
                day=1
            )
            month_hist = hist[hist.index >= month_start]
            if len(month_hist) >= 1:
                ms_val = float(month_hist["Close"].iloc[0])
                if is_yield:
                    mtd = round(latest - ms_val, 2)
                else:
                    mtd = round((latest - ms_val) / ms_val * 100, 2) if ms_val else None
            else:
                mtd = aad
            return ticker, {"mtd": mtd, "aad": aad}
        except Exception as e:
            logger.warning(f"Perf {ticker}: {e}")
            return ticker, {"mtd": None, "aad": None}

    result = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(_fetch_perf, t): t for t in non_boc}
        for f in as_completed(futures, timeout=45):
            try:
                tk, d = f.result()
                result[tk] = d
            except Exception as e:
                logger.warning(f"Perf future: {e}")
    return result


@st.cache_data(ttl=60, show_spinner="Chargement des données de marché…")
def _full_data():
    mkt  = _market_data_cached()
    ca   = _ca_yields_cached()
    perf = _period_perf_cached()
    mkt  = {**mkt, **ca}
    # Merge CA yield MTD/AAD into perf dict
    for tk, d in ca.items():
        perf[tk] = {"mtd": d.get("mtd"), "aad": d.get("aad")}
    risk = _risk_score(mkt)
    today = datetime.now(timezone.utc).date()
    assets = [
        {**a,
         "price":      mkt.get(a["ticker"], {}).get("price"),
         "change":     mkt.get(a["ticker"], {}).get("change"),
         "change_pct": mkt.get(a["ticker"], {}).get("change_pct"),
         "timestamp":  mkt.get(a["ticker"], {}).get("timestamp"),
         "mtd":        perf.get(a["ticker"], {}).get("mtd"),
         "aad":        perf.get(a["ticker"], {}).get("aad")}
        for a in MARKET_ASSETS
    ]
    cal = []
    for evt in sorted(ECONOMIC_CALENDAR, key=lambda x: x["date"]):
        d = datetime.strptime(evt["date"], "%Y-%m-%d").date()
        du = (d - today).days
        if -2 <= du <= 35:
            cal.append({**evt, "days_until": du, "is_today": du == 0, "is_past": du < 0})
    return {
        "risk":               risk,
        "assets":             assets,
        "news":               _news_cached(),
        "geopolitical_risks": GEOPOLITICAL_RISKS,
        "central_bank_rates": CENTRAL_BANK_RATES,
        "economic_calendar":  cal,
        "last_updated":       datetime.now(timezone.utc).isoformat(),
    }


# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Market Turbulence Dashboard — Fondaction",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
[data-testid="stAppViewContainer"] { background: #0B1120; }
[data-testid="stTabs"] > div:first-child {
    background: rgba(11,17,32,0.95);
    border-bottom: 1px solid #1F2937;
    padding: 4px 16px 0;
}
button[data-baseweb="tab"] { color: #9CA3AF !important; font-size: 0.82rem !important; }
button[data-baseweb="tab"][aria-selected="true"] {
    color: #F9FAFB !important;
    border-bottom-color: #3B82F6 !important;
}
</style>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Market Turbulence Dashboard", "🏦 Fondaction Snapshot", "🛢️ Oil & LNG"])

with tab1:
    data = _full_data()
    vix  = _vix_history_cached()
    miso = fetch_miso()
    html = (TEMPLATE_DIR / "index.html").read_text(encoding="utf-8")
    inject = (
        f'<script>'
        f'window.__PRELOAD__={json.dumps(data, default=str)};'
        f'window.__VIX_PRELOAD__={json.dumps(vix)};'
        f'</script>'
    )
    html = html.replace("</head>", inject + "</head>")
    components.html(html, height=950, scrolling=True)

    # ── MISO — Market Immune System Oscillator ───────────────────────────────
    st.markdown(
        '<div style="font-size:0.7rem;font-weight:700;color:#94a3b8;'
        'text-transform:uppercase;letter-spacing:.1em;margin:8px 0 6px;">'
        '🧬 Market Immune System Oscillator (MISO) — Indicateur de survendu composite'
        '</div>',
        unsafe_allow_html=True,
    )

    _MISO_RGB = {
        "#ef4444": "239,68,68", "#f59e0b": "245,158,11", "#94a3b8": "148,163,184",
        "#3b82f6": "59,130,246", "#22c55e": "34,197,94",
    }

    if miso.get("composite") is not None:
        mc  = miso["composite"]
        clr = miso["color"]
        rgb = _MISO_RGB.get(clr, "148,163,184")

        st.markdown(
            f'<div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-bottom:0.8rem">'
            f'<span style="font-size:2.1rem;font-weight:900;color:{clr};font-family:monospace;line-height:1">'
            f'{mc:.1f}<span style="font-size:0.85rem;color:#64748b;font-weight:400"> / 100</span></span>'
            f'<span style="background:rgba({rgb},0.12);border:1px solid rgba({rgb},0.35);color:{clr};'
            f'font-size:0.72rem;font-weight:800;padding:4px 13px;border-radius:20px;'
            f'letter-spacing:0.1em;white-space:nowrap">{miso["emoji"]} {miso["status"]}</span>'
            f'<span style="font-size:0.73rem;color:#94a3b8;font-style:italic">{miso["signal"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        n_comp    = len(miso["components"])
        miso_cols = st.columns(n_comp) if n_comp else []
        for col, comp in zip(miso_cols, miso["components"]):
            sc      = comp["score"]
            bar_clr = "#ef4444" if sc >= 70 else "#f59e0b" if sc >= 45 else "#22c55e"
            with col:
                st.markdown(
                    f'<div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:0.65rem 0.75rem;">'
                    f'<div style="font-size:0.67rem;font-weight:700;color:#e2e8f0;margin-bottom:5px;line-height:1.2">'
                    f'{comp["name"]}</div>'
                    f'<div style="display:flex;justify-content:space-between;align-items:baseline;">'
                    f'<span style="font-size:1.3rem;font-weight:900;color:{bar_clr};font-family:monospace">{sc:.1f}</span>'
                    f'<span style="font-size:0.62rem;color:#475569">/100</span></div>'
                    f'<div style="height:5px;background:#334155;border-radius:3px;margin:5px 0 5px;">'
                    f'<div style="height:5px;width:{min(sc,100):.0f}%;background:{bar_clr};'
                    f'border-radius:3px;"></div></div>'
                    f'<div style="font-size:0.63rem;color:#94a3b8;font-family:monospace;'
                    f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{comp["raw_label"]}</div>'
                    f'<div style="font-size:0.59rem;color:#475569;margin-top:2px;line-height:1.3">{comp["desc"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown(
            '<p style="font-size:0.62rem;color:#475569;margin-top:6px">'
            '📊 Score 0–100 · '
            '<span style="color:#ef4444;font-weight:700">100 = plus survendu</span> '
            '(pression max + potentiel de rebond) · '
            '<span style="color:#22c55e;font-weight:700">0 = plus suracheté</span> '
            '(complacence max) · '
            'Pondération : VIX %B 25% · SPX RSI 25% · Breadth RSI 20% · Term Structure 20% · DeMark 10% · '
            'Sources : ^GSPC · ^VIX · ^NYAD · ^VIX3M'
            '</p>',
            unsafe_allow_html=True,
        )
    else:
        st.caption("⚠️ MISO — données insuffisantes (^NYAD ou ^VIX3M non disponibles)")

with tab2:
    # ── Excel upload ────────────────────────────────────────────────────────
    st.markdown("""
    <div style="background:#111827;border:1px solid #374151;border-radius:10px;padding:16px 20px;margin-bottom:16px;">
      <p style="color:#9CA3AF;font-size:0.75rem;text-transform:uppercase;letter-spacing:.1em;margin:0 0 4px;">
        📥 Mise à jour Bloomberg
      </p>
      <p style="color:#F9FAFB;font-size:0.85rem;margin:0;">
        Téléverse un fichier Excel Bloomberg pour mettre à jour le snapshot.
      </p>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Fichier Excel Bloomberg (.xlsx)",
        type=["xlsx", "xls"],
        label_visibility="collapsed",
    )

    if uploaded is not None:
        try:
            import pandas as pd
            xl = pd.ExcelFile(uploaded)
            sheet_names = xl.sheet_names
            st.success(f"✅ Fichier chargé : **{uploaded.name}** — {len(sheet_names)} feuille(s)")

            selected = st.selectbox(
                "Sélectionner une feuille",
                sheet_names,
                label_visibility="collapsed",
            )
            df = xl.parse(selected, header=None)

            # Style the dataframe
            st.markdown(f"<p style='color:#6B7280;font-size:0.75rem;margin:8px 0 4px;'>"
                        f"Feuille : <strong style='color:#93C5FD;'>{selected}</strong> "
                        f"— {df.shape[0]} lignes × {df.shape[1]} colonnes</p>",
                        unsafe_allow_html=True)
            st.dataframe(
                df,
                use_container_width=True,
                height=400,
            )
        except Exception as e:
            st.error(f"Erreur lecture Excel : {e}")

    st.divider()

    # ── Static snapshot HTML ────────────────────────────────────────────────
    html_snap = (TEMPLATE_DIR / "fondaction_snapshot.html").read_text(encoding="utf-8")
    components.html(html_snap, height=1400, scrolling=True)

with tab3:
    oil_data = _full_oil_data()
    oil_hist = _oil_history_cached()
    html_oil = (TEMPLATE_DIR / "oil_lng.html").read_text(encoding="utf-8")
    oil_inject = (
        "<script>"
        f"window.__OIL_PRELOAD__={json.dumps(oil_data, default=str)};"
        f"window.__OIL_HISTORY_PRELOAD__={json.dumps(oil_hist)};"
        "</script>"
    )
    html_oil = html_oil.replace("</head>", oil_inject + "</head>")
    components.html(html_oil, height=1400, scrolling=True)
