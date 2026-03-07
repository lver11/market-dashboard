"""
Market Turbulence & Risk Dashboard — Streamlit Edition
Live risk-on/off indicator with multi-asset market data aggregation.
"""

from __future__ import annotations

import json as _json
import logging
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Optional

import feedparser
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Market Risk Dashboard",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Hide Streamlit branding */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 1rem; padding-bottom: 1rem; max-width: 1400px; }

  /* Metric cards */
  [data-testid="metric-container"] {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 0.75rem 1rem;
  }

  /* Risk banner */
  .risk-banner {
    text-align: center;
    padding: 0.5rem 1.5rem;
    border-radius: 10px;
    font-weight: 800;
    font-size: 1.4rem;
    letter-spacing: 0.05em;
    margin-bottom: 0.5rem;
  }
  .risk-on  { background: rgba(34,197,94,0.15);  color: #22c55e; border: 1px solid rgba(34,197,94,0.3); }
  .risk-off { background: rgba(239,68,68,0.15);  color: #ef4444; border: 1px solid rgba(239,68,68,0.3); }
  .neutral  { background: rgba(245,158,11,0.15); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3); }

  /* Section title */
  .section-title {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #64748b;
    margin-bottom: 0.5rem;
    margin-top: 0.25rem;
  }

  /* Signal card */
  .signal-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 0.6rem 0.75rem;
    margin-bottom: 0.4rem;
  }
  .signal-row { display: flex; justify-content: space-between; align-items: center; }
  .sig-name  { font-size: 0.78rem; font-weight: 600; color: #e2e8f0; }
  .sig-val   { font-size: 0.75rem; font-family: monospace; font-weight: 700; }
  .sig-label { font-size: 0.68rem; color: #94a3b8; }
  .sig-bar-bg { height: 3px; background: #334155; border-radius: 2px; margin-top: 4px; }
  .sig-bar   { height: 3px; border-radius: 2px; transition: width 0.5s; }
  .sig-weight { font-size: 0.6rem; color: #475569; margin-top: 2px; }

  /* Calendar row */
  .cal-row {
    padding: 0.4rem 0.5rem;
    border-radius: 6px;
    margin-bottom: 0.3rem;
    border-left: 3px solid transparent;
  }
  .cal-today   { background: rgba(245,158,11,0.1); border-left-color: #f59e0b; }
  .cal-upcoming { background: #1e293b; border-left-color: #334155; }
  .cal-past    { background: rgba(100,116,139,0.05); border-left-color: #1e293b; opacity: 0.6; }
  .cal-name  { font-size: 0.78rem; font-weight: 600; color: #e2e8f0; }
  .cal-meta  { font-size: 0.65rem; color: #64748b; margin-top: 2px; }
  .badge { font-size: 0.6rem; padding: 1px 5px; border-radius: 4px; font-weight: 600; display: inline-block; }
  .badge-critical { background: rgba(239,68,68,0.2); color: #ef4444; }
  .badge-high     { background: rgba(249,115,22,0.2); color: #fb923c; }
  .badge-medium   { background: rgba(245,158,11,0.2); color: #fbbf24; }
  .badge-low      { background: rgba(100,116,139,0.2); color: #94a3b8; }

  /* Geo card */
  .geo-card { padding: 0.6rem 0.75rem; border-radius: 8px; margin-bottom: 0.4rem; }
  .geo-high   { background: rgba(239,68,68,0.1);  border-left: 3px solid #ef4444; }
  .geo-medium { background: rgba(245,158,11,0.1); border-left: 3px solid #f59e0b; }
  .geo-low    { background: rgba(34,197,94,0.1);  border-left: 3px solid #22c55e; }
  .geo-title { font-size: 0.78rem; font-weight: 600; color: #e2e8f0; }
  .geo-desc  { font-size: 0.68rem; color: #94a3b8; margin-top: 2px; }
  .geo-impact { font-size: 0.63rem; color: #64748b; margin-top: 3px; }

  /* News card */
  .news-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 0.65rem 0.75rem;
    margin-bottom: 0.4rem;
  }
  .news-title { font-size: 0.8rem; font-weight: 600; color: #e2e8f0; line-height: 1.3; }
  .news-meta  { font-size: 0.65rem; color: #64748b; margin-top: 4px; }
  .news-tag { font-size: 0.6rem; padding: 1px 5px; border-radius: 4px; display: inline-block; margin-right: 3px; }
  .tag-geo { background: rgba(239,68,68,0.15); color: #fca5a5; }
  .tag-eco { background: rgba(59,130,246,0.15); color: #93c5fd; }
  .tag-mkt { background: rgba(34,197,94,0.15);  color: #86efac; }

  /* Ticker */
  .ticker { font-size: 0.75rem; font-family: monospace; background: #0f172a; padding: 4px 8px; border-radius: 6px; border: 1px solid #1e293b; }
  .pos { color: #22c55e; } .neg { color: #ef4444; } .flat { color: #94a3b8; }

  /* Live dot */
  .live-dot { display: inline-block; width: 7px; height: 7px; background: #22c55e; border-radius: 50%; animation: pulse 2s infinite; vertical-align: middle; }
  @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(0.8)} }

  /* Stale override */
  div[data-stale="true"] { opacity: 1 !important; }
</style>
""", unsafe_allow_html=True)

# ─── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ─── Assets Config ────────────────────────────────────────────────────────────
MARKET_ASSETS = [
    {"group": "Equities",    "name": "S&P 500",          "ticker": "^GSPC",    },
    {"group": "Equities",    "name": "Nasdaq 100",        "ticker": "^NDX",     },
    {"group": "Equities",    "name": "Dow Jones",         "ticker": "^DJI",     },
    {"group": "Equities",    "name": "Russell 2000",      "ticker": "^RUT",     },
    {"group": "Equities",    "name": "Euro Stoxx 50",     "ticker": "^STOXX50E",},
    {"group": "Equities",    "name": "Nikkei 225",        "ticker": "^N225",    },
    {"group": "Equities",    "name": "MSCI EM (EEM)",     "ticker": "EEM",      },
    # US Yields
    {"group": "Bonds",       "name": "US 3M Yield",       "ticker": "^IRX",     },
    {"group": "Bonds",       "name": "US 5Y Yield",       "ticker": "^FVX",     },
    {"group": "Bonds",       "name": "US 10Y Yield",      "ticker": "^TNX",     },
    {"group": "Bonds",       "name": "US 30Y Yield",      "ticker": "^TYX",     },
    # Canadian Yields
    {"group": "Bonds",       "name": "CA 2Y Yield",       "ticker": "CA2YT=RR", },
    {"group": "Bonds",       "name": "CA 5Y Yield",       "ticker": "CA5YT=RR", },
    {"group": "Bonds",       "name": "CA 10Y Yield",      "ticker": "CA10YT=RR",},
    {"group": "Bonds",       "name": "CA 30Y Yield",      "ticker": "CA30YT=RR",},
    # Bond ETFs
    {"group": "Bonds",       "name": "Long Treasury TLT", "ticker": "TLT",      },
    {"group": "Bonds",       "name": "High Yield HYG",    "ticker": "HYG",      },
    {"group": "Bonds",       "name": "IG Credit LQD",     "ticker": "LQD",      },
    {"group": "Commodities", "name": "Gold",              "ticker": "GC=F",     },
    {"group": "Commodities", "name": "WTI Oil",           "ticker": "CL=F",     },
    {"group": "Commodities", "name": "Silver",            "ticker": "SI=F",     },
    {"group": "Currencies",  "name": "DXY (USD Index)",   "ticker": "DX-Y.NYB", },
    {"group": "Currencies",  "name": "EUR/USD",           "ticker": "EURUSD=X", },
    {"group": "Currencies",  "name": "USD/JPY",           "ticker": "JPY=X",    },
    {"group": "Currencies",  "name": "USD/CAD",           "ticker": "USDCAD=X", },
    {"group": "Crypto",      "name": "Bitcoin",           "ticker": "BTC-USD",  },
    {"group": "Crypto",      "name": "Ethereum",          "ticker": "ETH-USD",  },
    {"group": "Volatility",  "name": "VIX",               "ticker": "^VIX",     },
    {"group": "Risk Proxy",  "name": "SPY",               "ticker": "SPY",      },
]

NEWS_FEEDS = [
    # Wire services
    ("Reuters Top",   "https://feeds.reuters.com/reuters/topNews"),
    ("Reuters Biz",   "https://feeds.reuters.com/reuters/businessNews"),
    ("AP News",       "https://apnews.com/rss"),
    # Finance media
    ("CNBC Markets",  "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"),
    ("Bloomberg/GN",  "https://news.google.com/rss/search?q=bloomberg+finance+market&hl=en-US&gl=US&ceid=US:en"),
    # Reddit finance communities (User-Agent required)
    ("r/investing",       "https://www.reddit.com/r/investing/.rss"),
    ("r/wallstreetbets",  "https://www.reddit.com/r/wallstreetbets/.rss"),
    ("r/economics",       "https://www.reddit.com/r/economics/.rss"),
    ("r/geopolitics",     "https://www.reddit.com/r/geopolitics/.rss"),
]

# Feeds that require a User-Agent header (Reddit blocks default scrapers)
_REDDIT_USER_AGENT = "Mozilla/5.0 (compatible; market-dashboard/1.0; +https://github.com/lver11/market-dashboard)"
_FEEDS_NEEDING_UA  = {"r/investing", "r/wallstreetbets", "r/economics", "r/geopolitics"}

ECONOMIC_CALENDAR = [
    {"date": "2026-03-06", "event": "Non-Farm Payrolls (Feb)",       "country": "🇺🇸", "importance": "critical", "forecast": "200K",   "previous": "256K"},
    {"date": "2026-03-06", "event": "Unemployment Rate (Feb)",        "country": "🇺🇸", "importance": "high",     "forecast": "4.1%",   "previous": "4.0%"},
    {"date": "2026-03-06", "event": "ECB Rate Decision",              "country": "🇪🇺", "importance": "critical", "forecast": "Hold",   "previous": "2.65%"},
    {"date": "2026-03-07", "event": "Michigan Consumer Confidence",   "country": "🇺🇸", "importance": "medium",   "forecast": None,     "previous": "64.7"},
    {"date": "2026-03-11", "event": "JOLTS Job Openings (Jan)",       "country": "🇺🇸", "importance": "medium",   "forecast": None,     "previous": "7.6M"},
    {"date": "2026-03-12", "event": "CPI YoY (Feb)",                  "country": "🇺🇸", "importance": "critical", "forecast": "2.8%",   "previous": "3.0%"},
    {"date": "2026-03-12", "event": "Core CPI YoY (Feb)",             "country": "🇺🇸", "importance": "critical", "forecast": "3.2%",   "previous": "3.3%"},
    {"date": "2026-03-13", "event": "PPI (Feb)",                      "country": "🇺🇸", "importance": "medium",   "forecast": None,     "previous": "3.5%"},
    {"date": "2026-03-14", "event": "Retail Sales (Feb)",             "country": "🇺🇸", "importance": "high",     "forecast": None,     "previous": "-0.9%"},
    {"date": "2026-03-15", "event": "China Industrial Production",    "country": "🇨🇳", "importance": "medium",   "forecast": None,     "previous": "6.2%"},
    {"date": "2026-03-17", "event": "NY Fed Manufacturing",           "country": "🇺🇸", "importance": "medium",   "forecast": None,     "previous": "5.7"},
    {"date": "2026-03-18", "event": "FOMC Meeting Begins",            "country": "🇺🇸", "importance": "high",     "forecast": None,     "previous": None},
    {"date": "2026-03-19", "event": "FOMC Rate Decision",             "country": "🇺🇸", "importance": "critical", "forecast": "Hold",   "previous": "4.25-4.50%"},
    {"date": "2026-03-19", "event": "Powell Press Conference",        "country": "🇺🇸", "importance": "critical", "forecast": None,     "previous": None},
    {"date": "2026-03-19", "event": "BOJ Rate Decision",              "country": "🇯🇵", "importance": "high",     "forecast": None,     "previous": "0.50%"},
    {"date": "2026-03-20", "event": "Philadelphia Fed Index",         "country": "🇺🇸", "importance": "medium",   "forecast": None,     "previous": "18.1"},
    {"date": "2026-03-26", "event": "Consumer Confidence (CB)",       "country": "🇺🇸", "importance": "medium",   "forecast": None,     "previous": "104.1"},
    {"date": "2026-03-27", "event": "GDP Q4 2025 (Final)",            "country": "🇺🇸", "importance": "high",     "forecast": "2.3%",   "previous": "2.3%"},
    {"date": "2026-03-28", "event": "PCE Price Index YoY (Feb)",      "country": "🇺🇸", "importance": "critical", "forecast": "2.5%",   "previous": "2.6%"},
    {"date": "2026-04-01", "event": "ISM Manufacturing PMI (Mar)",    "country": "🇺🇸", "importance": "high",     "forecast": None,     "previous": "50.3"},
    {"date": "2026-04-03", "event": "Non-Farm Payrolls (Mar)",        "country": "🇺🇸", "importance": "critical", "forecast": None,     "previous": "200K"},
    {"date": "2026-04-10", "event": "CPI (Mar)",                      "country": "🇺🇸", "importance": "critical", "forecast": None,     "previous": "2.8%"},
    {"date": "2026-04-16", "event": "China GDP Q1 2026",              "country": "🇨🇳", "importance": "high",     "forecast": None,     "previous": "5.0%"},
    {"date": "2026-04-29", "event": "FOMC Rate Decision",             "country": "🇺🇸", "importance": "critical", "forecast": None,     "previous": "4.25-4.50%"},
    {"date": "2026-04-30", "event": "GDP Q1 2026 (Advance)",          "country": "🇺🇸", "importance": "high",     "forecast": None,     "previous": "2.3%"},
]

GEOPOLITICAL_RISKS = [
    {"region": "Europe",       "title": "Ukraine-Russia War",           "level": "high",   "description": "Active conflict; ceasefire talks ongoing. NATO supply lines under pressure.",         "impact": "Energy prices, European equities, EUR"},
    {"region": "Middle East",  "title": "Middle East Tensions",         "level": "high",   "description": "Regional escalation; Red Sea shipping disruptions affecting supply chains.",          "impact": "Oil premium, shipping costs, inflation"},
    {"region": "Asia Pacific", "title": "Taiwan Strait / China-US",     "level": "medium", "description": "Elevated military activity; US-China strategic competition intensifying.",            "impact": "Tech supply chains, semis, Asian equities"},
    {"region": "Americas",     "title": "US-China Trade War",           "level": "medium", "description": "Tariff escalation; supply chain decoupling in critical sectors.",                     "impact": "Global trade, tech sector, EM currencies"},
    {"region": "Global",       "title": "Central Bank Policy Divergence","level": "medium","description": "Fed vs ECB vs BOJ divergent paths creating currency volatility.",                    "impact": "USD strength, carry trades, EM debt"},
    {"region": "Americas",     "title": "US Fiscal Sustainability",      "level": "low",   "description": "Debt ceiling concerns; rising deficit affecting bond market sentiment.",               "impact": "Treasury yields, USD long-term"},
]

# Bank of Canada Valet API series IDs for government bond benchmark yields
BOC_SERIES = {
    "CA2YT=RR":  "BD.CDN.2YR.DQ.YLD",
    "CA5YT=RR":  "BD.CDN.5YR.DQ.YLD",
    "CA10YT=RR": "BD.CDN.10YR.DQ.YLD",
    "CA30YT=RR": "BD.CDN.LONG.DQ.YLD",
}

CENTRAL_BANK_RATES = [
    {"flag": "🇺🇸", "name": "États-Unis",  "bank": "Fed",  "rate": "4.25–4.50%", "bias": "neutral",  "change": "=",  "next_meeting": "18-19 mars"},
    {"flag": "🇪🇺", "name": "Zone Euro",   "bank": "BCE",  "rate": "2.65%",      "bias": "dovish",   "change": "↓",  "next_meeting": "17 avr."},
    {"flag": "🇨🇦", "name": "Canada",      "bank": "BdC",  "rate": "3.00%",      "bias": "dovish",   "change": "↓",  "next_meeting": "16 avr."},
    {"flag": "🇬🇧", "name": "Royaume-Uni", "bank": "BOE",  "rate": "4.50%",      "bias": "neutral",  "change": "↓",  "next_meeting": "8 mai"},
    {"flag": "🇯🇵", "name": "Japon",       "bank": "BOJ",  "rate": "0.50%",      "bias": "hawkish",  "change": "↑",  "next_meeting": "19 mars"},
    {"flag": "🇨🇭", "name": "Suisse",      "bank": "BNS",  "rate": "0.25%",      "bias": "neutral",  "change": "↓",  "next_meeting": "20 mars"},
]

# ─── Data Fetching (cached 60s) ───────────────────────────────────────────────
def _fetch_one(ticker: str) -> tuple[str, dict]:
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d", auto_adjust=True)
        hist = hist.dropna(subset=["Close"])
        if len(hist) >= 2:
            current  = float(hist["Close"].iloc[-1])
            previous = float(hist["Close"].iloc[-2])
            change   = current - previous
            chg_pct  = (change / previous) * 100
            return ticker, {"price": round(current, 4), "change": round(change, 4), "change_pct": round(chg_pct, 2)}
        elif len(hist) == 1:
            current = float(hist["Close"].iloc[-1])
            return ticker, {"price": round(current, 4), "change": None, "change_pct": None}
    except Exception as e:
        logger.warning(f"Error fetching {ticker}: {e}")
    return ticker, {"price": None, "change": None, "change_pct": None}


@st.cache_data(ttl=60, show_spinner=False)
def fetch_market_data() -> dict:
    tickers = list({a["ticker"] for a in MARKET_ASSETS})
    result = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        for future in as_completed({ex.submit(_fetch_one, t): t for t in tickers}, timeout=25):
            try:
                ticker, data = future.result()
                result[ticker] = data
            except Exception:
                pass
    return result


@st.cache_data(ttl=300, show_spinner=False)
def get_vix_history() -> list[dict]:
    try:
        hist = yf.Ticker("^VIX").history(period="30d").dropna(subset=["Close"])
        return [{"date": str(idx.date()), "value": round(float(r["Close"]), 2)} for idx, r in hist.iterrows()]
    except Exception:
        return []


@st.cache_data(ttl=300, show_spinner=False)
def fetch_ca_bond_yields() -> dict:
    """Fetch Canadian government bond yields from Bank of Canada Valet API (free, no key)."""
    today      = datetime.now(timezone.utc).date()
    year_start = today.replace(month=1, day=1).isoformat()
    month_start = today.replace(day=1).isoformat()
    result: dict = {}

    for ticker, series in BOC_SERIES.items():
        try:
            url = (f"https://www.bankofcanada.ca/valet/observations/{series}/json"
                   f"?start_date={year_start}&end_date={today.isoformat()}")
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = _json.loads(resp.read())
            obs = [o for o in data.get("observations", [])
                   if o.get(series, {}).get("v") not in (None, "")]
            if not obs:
                result[ticker] = {"price": None, "change": None, "change_pct": None, "mtd": None, "ytd": None}
                continue

            latest = float(obs[-1][series]["v"])
            # Day change vs previous observation
            change = change_pct = None
            if len(obs) >= 2:
                prev = float(obs[-2][series]["v"])
                change = round(latest - prev, 3)
                change_pct = round((change / prev) * 100, 2) if prev else None
            # YTD: first obs of year
            ytd = round((latest - float(obs[0][series]["v"])) / float(obs[0][series]["v"]) * 100, 2) if len(obs) >= 2 else None
            # MTD: first obs on or after 1st of current month
            month_obs = [o for o in obs if o["d"] >= month_start]
            mtd = None
            if month_obs:
                first = float(month_obs[0][series]["v"])
                mtd = round((latest - first) / first * 100, 2) if first else None

            result[ticker] = {"price": round(latest, 3), "change": change, "change_pct": change_pct,
                               "mtd": mtd, "ytd": ytd}
        except Exception as e:
            logger.warning(f"BOC fetch error {series}: {e}")
            result[ticker] = {"price": None, "change": None, "change_pct": None, "mtd": None, "ytd": None}
    return result


@st.cache_data(ttl=300, show_spinner=False)
def fetch_period_performance() -> dict:
    """Fetch MTD and YTD % for all tickers (cached 5 min)."""
    tickers = list({a["ticker"] for a in MARKET_ASSETS})

    def _fetch_perf(ticker: str) -> tuple[str, dict]:
        try:
            hist = yf.Ticker(ticker).history(period="ytd", auto_adjust=True).dropna(subset=["Close"])
            if len(hist) < 2:
                return ticker, {"mtd": None, "ytd": None}
            latest = float(hist["Close"].iloc[-1])
            # YTD: first available price of the current year
            ytd_start = float(hist["Close"].iloc[0])
            ytd = round((latest - ytd_start) / ytd_start * 100, 2)
            # MTD: first available price on or after the 1st of the current month
            month_start = datetime.now(timezone.utc).replace(day=1).date()
            month_hist = hist[[d.date() >= month_start for d in hist.index]]
            if len(month_hist) >= 1:
                mtd_start = float(month_hist["Close"].iloc[0])
                mtd = round((latest - mtd_start) / mtd_start * 100, 2)
            else:
                mtd = ytd  # fallback: month started same as year start
            return ticker, {"mtd": mtd, "ytd": ytd}
        except Exception as e:
            logger.warning(f"Perf fetch error {ticker}: {e}")
            return ticker, {"mtd": None, "ytd": None}

    result: dict = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        for future in as_completed({ex.submit(_fetch_perf, t): t for t in tickers}, timeout=35):
            try:
                tk, data = future.result()
                result[tk] = data
            except Exception:
                pass
    return result


@st.cache_data(ttl=300, show_spinner=False)
def fetch_news() -> list[dict]:
    items = []
    for source, url in NEWS_FEEDS:
        try:
            req_headers = {"User-Agent": _REDDIT_USER_AGENT} if source in _FEEDS_NEEDING_UA else {}
            feed = feedparser.parse(url, request_headers=req_headers)
            for e in feed.entries[:5]:
                title = getattr(e, "title", "")
                tl = title.lower()
                tags = []
                if any(w in tl for w in ["war","conflict","attack","military","nuclear","sanctions","nato","ukraine","russia","china","taiwan","iran","israel"]):
                    tags.append("geo")
                if any(w in tl for w in ["inflation","rate","fed","ecb","boj","gdp","jobs","recession","cpi","fomc"]):
                    tags.append("eco")
                if any(w in tl for w in ["market","stock","equity","bond","gold","oil","crypto","bitcoin","rally","crash"]):
                    tags.append("mkt")
                items.append({"title": title, "source": source, "url": getattr(e, "link", "#"), "tags": tags})
        except Exception:
            pass
    return items[:24]


# ─── Risk Score ───────────────────────────────────────────────────────────────
def calculate_risk_score(md: dict) -> dict:
    signals, weighted_sum, total_weight = [], 0.0, 0.0

    def add(name, value, unit, score, label, status, weight, desc):
        nonlocal weighted_sum, total_weight
        signals.append({"name": name, "value": value, "unit": unit,
                         "score": round(float(score), 1), "label": label,
                         "status": status, "weight": weight, "description": desc})
        weighted_sum += float(score) * weight
        total_weight += weight

    # VIX (25%)
    vix = md.get("^VIX", {}).get("price")
    if vix:
        sc = 92 if vix<12 else 80 if vix<15 else 65 if vix<18 else 48 if vix<22 else 28 if vix<27 else 14 if vix<35 else 5
        lb = "Complacent" if vix<12 else "Low Vol" if vix<15 else "Normal" if vix<18 else "Elevated" if vix<22 else "High Fear" if vix<27 else "Very High" if vix<35 else "Extreme"
        st_ = "risk-on" if sc>60 else "neutral" if sc>40 else "risk-off"
        add("VIX Fear Index", vix, "", sc, lb, st_, 25, "Market fear gauge")

    # S&P / SPY (15%)
    spy_pct = md.get("SPY", {}).get("change_pct") or md.get("^GSPC", {}).get("change_pct")
    if spy_pct is not None:
        sc = max(0, min(100, 50 + spy_pct * 9))
        lb = "Equities Strong" if sc>65 else "Mixed" if sc>38 else "Equities Weak"
        st_ = "risk-on" if sc>65 else "neutral" if sc>38 else "risk-off"
        add("S&P 500", spy_pct, "%", sc, lb, st_, 15, "Equity direction")

    # Gold (12%)
    gold_pct = md.get("GC=F", {}).get("change_pct")
    if gold_pct is not None:
        sc = max(0, min(100, 50 - gold_pct * 14))
        lb = "Gold Selling" if sc>65 else "Gold Neutral" if sc>38 else "Safe-Haven Buy"
        st_ = "risk-on" if sc>65 else "neutral" if sc>38 else "risk-off"
        add("Gold (Safe Haven)", gold_pct, "%", sc, lb, st_, 12, "Safe-haven demand")

    # DXY (12%)
    dxy_pct = md.get("DX-Y.NYB", {}).get("change_pct")
    if dxy_pct is not None:
        sc = max(0, min(100, 50 - dxy_pct * 14))
        lb = "USD Weakening" if sc>65 else "USD Stable" if sc>38 else "USD Strengthening"
        st_ = "risk-on" if sc>65 else "neutral" if sc>38 else "risk-off"
        add("USD Strength (DXY)", dxy_pct, "%", sc, lb, st_, 12, "Dollar flight-to-safety")

    # HY vs IG (12%)
    hyg = md.get("HYG", {}).get("change_pct")
    lqd = md.get("LQD", {}).get("change_pct")
    if hyg is not None and lqd is not None:
        spread = hyg - lqd
        sc = max(0, min(100, 50 + spread * 18))
        lb = "HY Outperforming" if sc>65 else "Credit Neutral" if sc>38 else "IG Outperforming"
        st_ = "risk-on" if sc>65 else "neutral" if sc>38 else "risk-off"
        add("HY vs IG Credit", round(spread, 2), "% spread", sc, lb, st_, 12, "Credit risk appetite")

    # EM vs S&P (12%)
    eem = md.get("EEM", {}).get("change_pct")
    sp  = spy_pct
    if eem is not None and sp is not None:
        diff = eem - sp
        sc = max(0, min(100, 50 + diff * 18))
        lb = "EM Outperforming" if sc>65 else "EM In-Line" if sc>38 else "EM Underperforming"
        st_ = "risk-on" if sc>65 else "neutral" if sc>38 else "risk-off"
        add("EM vs Developed", round(eem, 2), "%", sc, lb, st_, 12, "Global risk breadth")

    # TLT (12%)
    tlt = md.get("TLT", {}).get("change_pct")
    if tlt is not None:
        sc = max(0, min(100, 50 - tlt * 14))
        lb = "Bonds Selling" if sc>65 else "Bonds Neutral" if sc>38 else "Bond Rally"
        st_ = "risk-on" if sc>65 else "neutral" if sc>38 else "risk-off"
        add("Long Treasuries (TLT)", tlt, "%", sc, lb, st_, 12, "Flight-to-safety bonds")

    comp = round(weighted_sum / total_weight, 1) if total_weight > 0 else 50.0

    if comp >= 72:
        label, color = "RISK-ON 🟢", "green"
        desc = "Forte appétence au risque — surpondérer actions, crédit, actifs à bêta élevé."
    elif comp >= 58:
        label, color = "MODÉRÉMENT RISK-ON", "green"
        desc = "Biais positif modéré — légère surpondération actions."
    elif comp >= 42:
        label, color = "NEUTRE ⚖️", "amber"
        desc = "Signaux mixtes — positionnement équilibré recommandé."
    elif comp >= 28:
        label, color = "MODÉRÉMENT RISK-OFF", "red"
        desc = "Positionnement défensif — réduire le risque, ajouter or/USD/obligations."
    else:
        label, color = "RISK-OFF 🔴", "red"
        desc = "Fuite vers la sécurité — surpondérer USD, or, bons du Trésor court terme."

    return {"score": comp, "label": label, "color": color, "description": desc, "signals": signals}


# ─── Plotly Gauge ─────────────────────────────────────────────────────────────
def make_gauge(score: float, color: str) -> go.Figure:
    gauge_color = "#22c55e" if color == "green" else "#ef4444" if color == "red" else "#f59e0b"
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        number={"suffix": "/100", "font": {"size": 36, "color": gauge_color}},
        domain={"x": [0, 1], "y": [0, 1]},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#475569",
                     "tickfont": {"color": "#64748b", "size": 10}},
            "bar":  {"color": gauge_color, "thickness": 0.25},
            "bgcolor": "#0f172a",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  30], "color": "rgba(239,68,68,0.15)"},
                {"range": [30, 70], "color": "rgba(245,158,11,0.12)"},
                {"range": [70,100], "color": "rgba(34,197,94,0.15)"},
            ],
            "threshold": {
                "line":      {"color": "white", "width": 3},
                "thickness": 0.8,
                "value":     score,
            },
        },
    ))
    fig.update_layout(
        height=220,
        margin=dict(t=10, b=10, l=20, r=20),
        paper_bgcolor="#0f172a",
        font={"color": "#e2e8f0"},
        annotations=[dict(
            text="RISK SCORE",
            x=0.5, y=0.1,
            showarrow=False,
            font={"size": 11, "color": "#64748b"},
            xanchor="center",
        )],
    )
    return fig


# ─── Plotly VIX Chart ─────────────────────────────────────────────────────────
def make_vix_chart(vix_data: list[dict]) -> go.Figure:
    if not vix_data:
        return go.Figure()
    dates  = [d["date"]  for d in vix_data]
    values = [d["value"] for d in vix_data]

    colors = ["#ef4444" if v > 25 else "#f59e0b" if v > 15 else "#22c55e" for v in values]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=values,
        mode="lines+markers",
        line=dict(width=2, color="#f59e0b"),
        marker=dict(size=4, color=colors),
        fill="tozeroy",
        fillcolor="rgba(245,158,11,0.06)",
        hovertemplate="<b>VIX: %{y:.2f}</b><br>%{x}<extra></extra>",
    ))
    # Fear zone lines
    fig.add_hline(y=15, line_dash="dash", line_color="rgba(34,197,94,0.5)",  line_width=1, annotation_text="15 Calme",  annotation_position="left")
    fig.add_hline(y=25, line_dash="dash", line_color="rgba(239,68,68,0.5)",  line_width=1, annotation_text="25 Peur",   annotation_position="left")

    fig.update_layout(
        height=200,
        margin=dict(t=10, b=10, l=50, r=20),
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        font={"color": "#94a3b8", "size": 11},
        xaxis=dict(showgrid=False, color="#475569"),
        yaxis=dict(showgrid=True, gridcolor="#1e293b", color="#475569"),
        showlegend=False,
    )
    return fig


# ─── Helpers ──────────────────────────────────────────────────────────────────
def fmt_price(v, decimals=2):
    if v is None: return "—"
    if isinstance(v, float) and v != v: return "—"  # NaN guard
    return f"{v:,.{decimals}f}"

def fmt_pct(v):
    if v is None: return "—"
    sign = "+" if v > 0 else ""
    return f"{sign}{v:.2f}%"

def change_color(v):
    if v is None: return "#94a3b8"
    return "#22c55e" if v > 0 else "#ef4444" if v < 0 else "#94a3b8"

def heat_bg(pct):
    if pct is None: return "#334155"
    t = max(0, min(1, abs(pct) / 4))
    if pct >= 0:
        return f"rgba(34,197,94,{0.1 + t*0.4})"
    else:
        return f"rgba(239,68,68,{0.1 + t*0.4})"


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════════════════════

# Auto-refresh every 60 seconds
st_autorefresh(interval=60_000, key="auto_refresh")

# ─── Fetch data ───────────────────────────────────────────────────────────────
with st.spinner("Chargement des données de marché..."):
    market_data  = fetch_market_data()
    ca_yields    = fetch_ca_bond_yields()
    # Inject BOC data into market_data (overrides the nan yfinance returns for CAxxYT=RR)
    market_data.update(ca_yields)
    vix_history  = get_vix_history()
    news_items   = fetch_news()
    period_perf  = fetch_period_performance()
    # Inject CA MTD/YTD into period_perf
    for _tk, _d in ca_yields.items():
        period_perf[_tk] = {"mtd": _d.get("mtd"), "ytd": _d.get("ytd")}

risk = calculate_risk_score(market_data)
now  = datetime.now(timezone.utc)

# ─── Header ───────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown(
        f'<h2 style="margin:0;color:#e2e8f0;font-size:1.4rem;">🌊 Market Turbulence Dashboard</h2>'
        f'<p style="margin:0;color:#64748b;font-size:0.75rem;">Risk-On / Risk-Off Monitor &nbsp;·&nbsp; '
        f'<span class="live-dot"></span> Live &nbsp;·&nbsp; '
        f'Mis à jour {now.strftime("%H:%M:%S")} UTC</p>',
        unsafe_allow_html=True,
    )
with col_h2:
    vix_now = market_data.get("^VIX", {}).get("price")
    sp_pct  = market_data.get("^GSPC", {}).get("change_pct")
    gold_pct = market_data.get("GC=F", {}).get("change_pct")
    mini_html = (
        f'<div class="ticker">'
        f'VIX <span style="color:{change_color(vix_now if vix_now else 0)}">{fmt_price(vix_now)}</span> &nbsp;|&nbsp; '
        f'S&P <span style="color:{change_color(sp_pct)}">{fmt_pct(sp_pct)}</span> &nbsp;|&nbsp; '
        f'Gold <span style="color:{change_color(gold_pct)}">{fmt_pct(gold_pct)}</span>'
        f'</div>'
    )
    st.markdown(mini_html, unsafe_allow_html=True)

st.divider()

# ─── ROW 1: Gauge + Signals ───────────────────────────────────────────────────
col_gauge, col_signals = st.columns([1, 2])

with col_gauge:
    banner_cls = "risk-on" if risk["color"] == "green" else "risk-off" if risk["color"] == "red" else "neutral"
    st.markdown(f'<div class="risk-banner {banner_cls}">{risk["label"]}</div>', unsafe_allow_html=True)
    st.plotly_chart(make_gauge(risk["score"], risk["color"]), use_container_width=True, config={"displayModeBar": False})
    st.markdown(f'<p style="font-size:0.75rem;color:#94a3b8;text-align:center;margin-top:-10px">{risk["description"]}</p>', unsafe_allow_html=True)

with col_signals:
    st.markdown('<div class="section-title">📡 Signaux composites — 7 indicateurs</div>', unsafe_allow_html=True)
    sig_col1, sig_col2 = st.columns(2)
    for i, sig in enumerate(risk["signals"]):
        col = sig_col1 if i % 2 == 0 else sig_col2
        sc   = sig["score"]
        bar_color = "#22c55e" if sig["status"] == "risk-on" else "#ef4444" if sig["status"] == "risk-off" else "#f59e0b"
        val_str = f"{sig['value']:.2f}{sig['unit']}" if isinstance(sig["value"], float) else f"{sig['value']}{sig['unit']}"
        with col:
            st.markdown(f"""
            <div class="signal-card">
              <div class="signal-row">
                <span class="sig-name">{sig['name']}</span>
                <span class="sig-val" style="color:{bar_color}">{val_str}</span>
              </div>
              <div class="signal-row">
                <span class="sig-label">{sig['label']}</span>
                <span class="sig-label" style="color:{bar_color};font-weight:700">{sc}/100</span>
              </div>
              <div class="sig-bar-bg"><div class="sig-bar" style="width:{sc}%;background:{bar_color}"></div></div>
              <div class="sig-weight">Poids: {sig['weight']}% · {sig['description']}</div>
            </div>""", unsafe_allow_html=True)

# ─── ROW 2: VIX Chart + Heatmap ──────────────────────────────────────────────
st.markdown("")
col_vix, col_heat = st.columns(2)

with col_vix:
    st.markdown('<div class="section-title">📈 VIX — Historique 30 jours</div>', unsafe_allow_html=True)
    st.plotly_chart(make_vix_chart(vix_history), use_container_width=True, config={"displayModeBar": False})

with col_heat:
    st.markdown('<div class="section-title">🔥 Heatmap des actifs — Performance du jour</div>', unsafe_allow_html=True)
    heat_assets = [a for a in MARKET_ASSETS if a["group"] != "Risk Proxy" and market_data.get(a["ticker"], {}).get("change_pct") is not None]
    cols_per_row = 5
    for row_start in range(0, len(heat_assets), cols_per_row):
        row_assets = heat_assets[row_start: row_start + cols_per_row]
        cols = st.columns(len(row_assets))
        for col, asset in zip(cols, row_assets):
            td = market_data.get(asset["ticker"], {})
            pct = td.get("change_pct")
            bg  = heat_bg(pct)
            txt_color = "#22c55e" if (pct or 0) > 0 else "#ef4444" if (pct or 0) < 0 else "#94a3b8"
            short_name = asset["name"].split(" ")[0]
            with col:
                st.markdown(
                    f'<div style="background:{bg};border-radius:6px;padding:6px 4px;text-align:center;margin-bottom:4px">'
                    f'<div style="font-size:0.65rem;color:#94a3b8;font-weight:600">{short_name}</div>'
                    f'<div style="font-size:0.72rem;font-weight:700;color:{txt_color};font-family:monospace">{fmt_pct(pct)}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

# ─── ROW 3: Interest Rates ────────────────────────────────────────────────────
st.markdown("")
col_curve, col_cb = st.columns(2)

with col_curve:
    st.markdown('<div class="section-title">📈 Courbe des taux — US vs Canada</div>', unsafe_allow_html=True)

    # US curve: 3M · 5A · 10A · 30A
    us_maturities = [("3M", "^IRX"), ("5A", "^FVX"), ("10A", "^TNX"), ("30A", "^TYX")]
    us_pts = [(lbl, market_data.get(tk, {}).get("price")) for lbl, tk in us_maturities]
    us_pts = [(lbl, v) for lbl, v in us_pts if v is not None]

    # Canada curve: 2A · 5A · 10A · 30A
    ca_maturities = [("2A", "CA2YT=RR"), ("5A", "CA5YT=RR"), ("10A", "CA10YT=RR"), ("30A", "CA30YT=RR")]
    ca_pts = [(lbl, market_data.get(tk, {}).get("price")) for lbl, tk in ca_maturities]
    ca_pts = [(lbl, v) for lbl, v in ca_pts if v is not None]

    if us_pts or ca_pts:
        fig_curve = go.Figure()

        if us_pts:
            us_vals = [v for _, v in us_pts]
            us_inverted = len(us_vals) >= 2 and us_vals[0] > us_vals[-1]
            us_color = "#ef4444" if us_inverted else "#3b82f6"
            fig_curve.add_trace(go.Scatter(
                x=[lbl for lbl, _ in us_pts], y=us_vals,
                name="🇺🇸 US",
                mode="lines+markers",
                line=dict(width=2.5, color=us_color),
                marker=dict(size=7),
                fill="tozeroy",
                fillcolor=f"rgba(59,130,246,0.05)",
                hovertemplate="<b>US %{x}: %{y:.2f}%</b><extra></extra>",
            ))
            if us_inverted:
                fig_curve.add_annotation(
                    text="⚠️ US inversée",
                    x=0.02, y=0.95, xref="paper", yref="paper",
                    showarrow=False, font=dict(color="#ef4444", size=10),
                    bgcolor="rgba(239,68,68,0.1)", bordercolor="#ef4444",
                    borderwidth=1, borderpad=3,
                )

        if ca_pts:
            ca_vals = [v for _, v in ca_pts]
            ca_inverted = len(ca_vals) >= 2 and ca_vals[0] > ca_vals[-1]
            ca_color = "#f97316" if ca_inverted else "#22d3ee"
            fig_curve.add_trace(go.Scatter(
                x=[lbl for lbl, _ in ca_pts], y=ca_vals,
                name="🇨🇦 CA",
                mode="lines+markers",
                line=dict(width=2.5, color=ca_color, dash="dot"),
                marker=dict(size=7),
                hovertemplate="<b>CA %{x}: %{y:.2f}%</b><extra></extra>",
            ))
            if ca_inverted:
                fig_curve.add_annotation(
                    text="⚠️ CA inversée",
                    x=0.98, y=0.95, xref="paper", yref="paper", xanchor="right",
                    showarrow=False, font=dict(color="#f97316", size=10),
                    bgcolor="rgba(249,115,22,0.1)", bordercolor="#f97316",
                    borderwidth=1, borderpad=3,
                )

        fig_curve.update_layout(
            height=220,
            margin=dict(t=10, b=10, l=45, r=20),
            paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
            font={"color": "#94a3b8", "size": 11},
            xaxis=dict(showgrid=False, color="#475569", categoryorder="array",
                       categoryarray=["3M","2A","5A","10A","30A"]),
            yaxis=dict(showgrid=True, gridcolor="#1e293b", color="#475569",
                       tickformat=".2f", ticksuffix="%"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11),
                        orientation="h", x=0.5, xanchor="center", y=1.08),
            showlegend=True,
        )
        st.plotly_chart(fig_curve, use_container_width=True, config={"displayModeBar": False})

        # Spreads résumé
        t10_us = market_data.get("^TNX",      {}).get("price")
        t10_ca = market_data.get("CA10YT=RR", {}).get("price")
        t3m_us = market_data.get("^IRX",      {}).get("price")
        parts = []
        if t10_us and t3m_us:
            sp_us = round(t10_us - t3m_us, 2)
            sc_us = "#ef4444" if sp_us < 0 else "#22c55e"
            parts.append(f'🇺🇸 10A–3M: <span style="color:{sc_us};font-weight:700">{sp_us:+.2f}%</span>')
        if t10_us and t10_ca:
            sp_ca = round(t10_us - t10_ca, 2)
            sc_ca = "#ef4444" if sp_ca < -0.3 else "#22c55e"
            parts.append(f'US–CA 10A: <span style="color:{sc_ca};font-weight:700">{sp_ca:+.2f}%</span>')
        if parts:
            st.markdown(
                f'<p style="font-size:0.72rem;color:#94a3b8;text-align:center;margin-top:-8px">'
                + " &nbsp;·&nbsp; ".join(parts) + "</p>",
                unsafe_allow_html=True,
            )
    else:
        st.info("Données de taux non disponibles")

with col_cb:
    st.markdown('<div class="section-title">🏦 Taux directeurs — Banques centrales</div>', unsafe_allow_html=True)
    bias_color = {"hawkish": "#ef4444", "dovish": "#22c55e", "neutral": "#f59e0b"}
    bias_label = {"hawkish": "Restrictif 🦅", "dovish": "Accommodant 🕊️", "neutral": "Neutre ⚖️"}
    change_color = {"↑": "#ef4444", "↓": "#22c55e", "=": "#94a3b8"}

    cb_html = ""
    for cb in CENTRAL_BANK_RATES:
        bc = bias_color[cb["bias"]]
        bl = bias_label[cb["bias"]]
        cc = change_color[cb["change"]]
        cb_html += f"""
        <div class="signal-card" style="margin-bottom:0.3rem">
          <div class="signal-row">
            <span class="sig-name">{cb['flag']} {cb['name']} <span style="color:#64748b;font-weight:400">({cb['bank']})</span></span>
            <span style="font-size:1rem;font-family:monospace;font-weight:800;color:#e2e8f0">{cb['rate']}
              <span style="color:{cc};font-size:0.85rem">{cb['change']}</span>
            </span>
          </div>
          <div class="signal-row">
            <span style="font-size:0.66rem;color:{bc};font-weight:600">{bl}</span>
            <span style="font-size:0.63rem;color:#475569">Prochain: {cb['next_meeting']}</span>
          </div>
        </div>"""
    st.markdown(cb_html, unsafe_allow_html=True)

# ─── ROW 4: Market Table ──────────────────────────────────────────────────────
st.markdown("")
st.markdown('<div class="section-title">📋 Tableau de marché complet</div>', unsafe_allow_html=True)

groups = ["Tous"] + sorted({a["group"] for a in MARKET_ASSETS if a["group"] != "Risk Proxy"})
selected_group = st.radio("Filtrer par:", groups, horizontal=True, label_visibility="collapsed")

rows = []
for a in MARKET_ASSETS:
    if a["group"] == "Risk Proxy":
        continue
    if selected_group != "Tous" and a["group"] != selected_group:
        continue
    td   = market_data.get(a["ticker"], {})
    pp   = period_perf.get(a["ticker"], {})
    pct  = td.get("change_pct")
    mtd  = pp.get("mtd")
    ytd  = pp.get("ytd")
    rows.append({
        "Actif":  a["name"],
        "Groupe": a["group"],
        "Ticker": a["ticker"],
        "Prix":   td.get("price"),
        "Jour":   pct,
        "MTD":    mtd,
        "YTD":    ytd,
        "Signal": "▲ Forte" if (pct or 0) > 1 else "▲ Hausse" if (pct or 0) > 0.2 else "▼ Forte" if (pct or 0) < -1 else "▼ Baisse" if (pct or 0) < -0.2 else "▸ Stable" if pct is not None else "—",
    })

df = pd.DataFrame(rows)

def color_pct(val):
    if val is None or (not isinstance(val, float)):
        return "color: #94a3b8"
    return "color: #22c55e; font-weight:600" if val > 0 else "color: #ef4444; font-weight:600" if val < 0 else "color: #94a3b8"

def fmt_val(val):
    if val is None: return "—"
    if isinstance(val, float):
        if val != val: return "—"  # NaN guard
        return f"{val:+.2f}%" if abs(val) < 100 else f"{val:.4f}"
    return str(val)

display_df = df.copy()
display_df["Prix"]   = display_df["Prix"].apply(lambda v: fmt_price(v, 2) if v else "—")
display_df["Jour"]   = display_df["Jour"].apply(fmt_val)
display_df["MTD"]    = display_df["MTD"].apply(fmt_val)
display_df["YTD"]    = display_df["YTD"].apply(fmt_val)

st.dataframe(
    display_df[["Actif", "Groupe", "Ticker", "Prix", "Jour", "MTD", "YTD", "Signal"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Actif":  st.column_config.TextColumn("Actif",  width="medium"),
        "Prix":   st.column_config.TextColumn("Prix",   width="small"),
        "Jour":   st.column_config.TextColumn("Jour %", width="small"),
        "MTD":    st.column_config.TextColumn("MTD %",  width="small"),
        "YTD":    st.column_config.TextColumn("YTD %",  width="small"),
        "Signal": st.column_config.TextColumn("Signal", width="small"),
    },
)

# ─── ROW 4: Calendar + Geopolitical ──────────────────────────────────────────
st.markdown("")
col_cal, col_geo = st.columns(2)

with col_cal:
    st.markdown('<div class="section-title">📅 Calendrier économique — 35 prochains jours</div>', unsafe_allow_html=True)
    today = datetime.now(timezone.utc).date()
    cal_html = ""
    for ev in sorted(ECONOMIC_CALENDAR, key=lambda x: x["date"]):
        ev_date    = datetime.strptime(ev["date"], "%Y-%m-%d").date()
        days_until = (ev_date - today).days
        if not (-2 <= days_until <= 35):
            continue
        row_cls  = "cal-today" if days_until == 0 else "cal-past" if days_until < 0 else "cal-upcoming"
        badge    = f'badge-{ev["importance"]}'
        days_str = "AUJOURD'HUI" if days_until == 0 else f"{abs(days_until)}j passé" if days_until < 0 else f"dans {days_until}j"
        fc       = f" · Prévu: <b>{ev['forecast']}</b>" if ev.get("forecast") else ""
        prev     = f" · Préc: {ev['previous']}" if ev.get("previous") else ""
        cal_html += f"""
        <div class="cal-row {row_cls}">
          <div class="cal-name">{ev['country']} {ev['event']} <span class="badge {badge}">{ev['importance'].upper()}</span></div>
          <div class="cal-meta">{ev['date']} · {days_str}{fc}{prev}</div>
        </div>"""
    st.markdown(f'<div style="max-height:380px;overflow-y:auto">{cal_html}</div>', unsafe_allow_html=True)

with col_geo:
    st.markdown('<div class="section-title">🌍 Moniteur géopolitique</div>', unsafe_allow_html=True)
    geo_html = ""
    level_label = {"high": "ÉLEVÉ", "medium": "MOYEN", "low": "FAIBLE"}
    level_color = {"high": "#ef4444", "medium": "#f59e0b", "low": "#22c55e"}
    for r in GEOPOLITICAL_RISKS:
        lc = level_color[r["level"]]
        geo_html += f"""
        <div class="geo-card geo-{r['level']}">
          <div class="geo-title">{r['title']} <span style="color:{lc};font-size:0.65rem;font-weight:700">{level_label[r['level']]}</span> <span style="font-size:0.65rem;color:#64748b">{r['region']}</span></div>
          <div class="geo-desc">{r['description']}</div>
          <div class="geo-impact">📊 Impact: {r['impact']}</div>
        </div>"""
    st.markdown(geo_html, unsafe_allow_html=True)

# ─── ROW 5: News ──────────────────────────────────────────────────────────────
st.markdown("")
st.markdown('<div class="section-title">📰 Fil d\'actualités — Marchés &amp; Géopolitique</div>', unsafe_allow_html=True)

tag_filter = st.radio("Filtre:", ["Tous", "Géopolitique", "Économie", "Marchés"], horizontal=True, label_visibility="collapsed", key="news_filter")
tag_map = {"Géopolitique": "geo", "Économie": "eco", "Marchés": "mkt"}
filtered_news = news_items if tag_filter == "Tous" else [n for n in news_items if tag_map.get(tag_filter, "") in n.get("tags", [])]

tag_html_map = {
    "geo": '<span class="news-tag tag-geo">Géopolitique</span>',
    "eco": '<span class="news-tag tag-eco">Économie</span>',
    "mkt": '<span class="news-tag tag-mkt">Marchés</span>',
}

nc1, nc2, nc3 = st.columns(3)
cols_cycle = [nc1, nc2, nc3]
for i, item in enumerate(filtered_news[:18]):
    tags_html = "".join(tag_html_map.get(t, "") for t in item.get("tags", []))
    with cols_cycle[i % 3]:
        st.markdown(
            f'<a href="{item["url"]}" target="_blank" style="text-decoration:none">'
            f'<div class="news-card">'
            f'<div class="news-title">{item["title"]}</div>'
            f'<div class="news-meta"><span style="color:#3b82f6">{item["source"]}</span> {tags_html}</div>'
            f'</div></a>',
            unsafe_allow_html=True,
        )

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<p style="font-size:0.65rem;color:#475569;text-align:center">'
    'Données: Yahoo Finance · Actualités: Reuters, AP, CNBC, Bloomberg (Google News), Reddit (r/investing, r/wallstreetbets, r/economics, r/geopolitics) · '
    'Actualisation automatique toutes les 60 secondes · '
    'Score Risk-On/Off: modèle composite 7 signaux pondérés · '
    'À des fins informatives uniquement — pas un conseil en investissement.'
    '</p>',
    unsafe_allow_html=True,
)
