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
from zoneinfo import ZoneInfo
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
    {"group": "Commodities", "name": "WTI Oil",          "ticker": "CL=F",     },
    {"group": "Commodities", "name": "Brent Crude",      "ticker": "BZ=F",     },
    {"group": "Commodities", "name": "Silver",           "ticker": "SI=F",     },
    {"group": "Commodities", "name": "Cuivre",           "ticker": "HG=F",     },
    {"group": "Commodities", "name": "Gaz Naturel",      "ticker": "NG=F",     },
    {"group": "Commodities", "name": "Platine",          "ticker": "PL=F",     },
    {"group": "Commodities", "name": "Maïs",             "ticker": "ZC=F",     },
    {"group": "Commodities", "name": "Blé",              "ticker": "ZW=F",     },
    {"group": "Currencies",  "name": "DXY (USD Index)",   "ticker": "DX-Y.NYB", },
    {"group": "Currencies",  "name": "EUR/USD",           "ticker": "EURUSD=X", },
    {"group": "Currencies",  "name": "GBP/USD",           "ticker": "GBPUSD=X", },
    {"group": "Currencies",  "name": "USD/JPY",           "ticker": "JPY=X",    },
    {"group": "Currencies",  "name": "USD/CHF",           "ticker": "CHF=X",    },
    {"group": "Currencies",  "name": "USD/CAD",           "ticker": "USDCAD=X", },
    {"group": "Currencies",  "name": "AUD/USD",           "ticker": "AUDUSD=X", },
    {"group": "Currencies",  "name": "NZD/USD",           "ticker": "NZDUSD=X", },
    {"group": "Currencies",  "name": "USD/CNY",           "ticker": "CNY=X",    },
    {"group": "Currencies",  "name": "USD/MXN",           "ticker": "MXN=X",    },
    {"group": "Currencies",  "name": "USD/BRL",           "ticker": "BRL=X",    },
    {"group": "Crypto",      "name": "Bitcoin",           "ticker": "BTC-USD",  },
    {"group": "Crypto",      "name": "Ethereum",          "ticker": "ETH-USD",  },
    {"group": "Volatility",  "name": "VIX",               "ticker": "^VIX",     },
    {"group": "Volatility",  "name": "MOVE (Vol. Oblig.)","ticker": "^MOVE",    },
    {"group": "Risk Proxy",  "name": "SPY",               "ticker": "SPY",      },
    # S&P 500 Sectors (SPDR ETFs)
    {"group": "S&P Secteurs", "name": "Technologie",          "ticker": "XLK",  },
    {"group": "S&P Secteurs", "name": "Finance",              "ticker": "XLF",  },
    {"group": "S&P Secteurs", "name": "Santé",                "ticker": "XLV",  },
    {"group": "S&P Secteurs", "name": "Consomm. discr.",      "ticker": "XLY",  "short": "Conso.Disc."},
    {"group": "S&P Secteurs", "name": "Consomm. de base",     "ticker": "XLP",  "short": "Conso.Base"},
    {"group": "S&P Secteurs", "name": "Énergie",              "ticker": "XLE",  },
    {"group": "S&P Secteurs", "name": "Industrie",            "ticker": "XLI",  },
    {"group": "S&P Secteurs", "name": "Matériaux",            "ticker": "XLB",  },
    {"group": "S&P Secteurs", "name": "Immobilier",           "ticker": "XLRE", },
    {"group": "S&P Secteurs", "name": "Services collectifs",  "ticker": "XLU",  },
    {"group": "S&P Secteurs", "name": "Communication",        "ticker": "XLC",  },
]


NEWS_FEEDS = [
    # ── Wire services ──────────────────────────────────────────────────────
    {"name": "Reuters Top",        "url": "https://feeds.reuters.com/reuters/topNews",                                                                    "type": "wire",       "ua": False},
    {"name": "Reuters Biz",        "url": "https://feeds.reuters.com/reuters/businessNews",                                                               "type": "wire",       "ua": False},
    {"name": "AP News",            "url": "https://apnews.com/rss",                                                                                       "type": "wire",       "ua": False},
    # ── Finance media ──────────────────────────────────────────────────────
    {"name": "CNBC Markets",       "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",                         "type": "media",      "ua": False},
    {"name": "Bloomberg/GN",       "url": "https://news.google.com/rss/search?q=bloomberg+finance+market&hl=en-US&gl=US&ceid=US:en",                      "type": "media",      "ua": False},
    # ── Reddit finance communities (User-Agent required) ───────────────────
    {"name": "r/investing",        "url": "https://www.reddit.com/r/investing/.rss",                                                                      "type": "reddit",     "ua": True},
    {"name": "r/wallstreetbets",   "url": "https://www.reddit.com/r/wallstreetbets/.rss",                                                                 "type": "reddit",     "ua": True},
    {"name": "r/economics",        "url": "https://www.reddit.com/r/economics/.rss",                                                                      "type": "reddit",     "ua": True},
    {"name": "r/geopolitics",      "url": "https://www.reddit.com/r/geopolitics/.rss",                                                                    "type": "reddit",     "ua": True},
    {"name": "r/stocks",           "url": "https://www.reddit.com/r/stocks/.rss",                                                                         "type": "reddit",     "ua": True},
    {"name": "r/worldnews",        "url": "https://www.reddit.com/r/worldnews/.rss",                                                                      "type": "reddit",     "ua": True},
    {"name": "r/CanadianInvestor", "url": "https://www.reddit.com/r/CanadianInvestor/.rss",                                                               "type": "reddit",     "ua": True},
    # ── Substack newsletters (ua:True → browser UA required to pass Cloudflare) ──
    {"name": "Apricitas Econ",     "url": "https://apricitas.substack.com/feed",                                                                          "type": "newsletter", "ua": True},
    {"name": "Chartbook",          "url": "https://adamtooze.substack.com/feed",                                                                          "type": "newsletter", "ua": True},
    {"name": "Noahpinion",         "url": "https://noahpinion.substack.com/feed",                                                                         "type": "newsletter", "ua": True},
    {"name": "No Mercy/No Malice", "url": "https://scottgalloway.substack.com/feed",                                                                      "type": "newsletter", "ua": True},
    {"name": "Calculated Risk",    "url": "https://www.calculatedriskblog.com/feeds/posts/default",                                                       "type": "newsletter", "ua": False},
]

# User-Agent — browser-like to pass Cloudflare/Substack checks
_SCRAPER_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# X/Twitter: public Nitter instances (tried in order; first success wins)
_NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.1d4.us",
]
_X_ACCOUNTS = [
    ("X: @FederalReserve", "FederalReserve"),
    ("X: @WSJ",             "WSJ"),
    ("X: @charliebilello",  "charliebilello"),
    ("X: @financialtimes",  "FinancialTimes"),
]

ECONOMIC_CALENDAR = [
    # ── États-Unis ────────────────────────────────────────────────────────────
    {"date": "2026-03-06", "event": "Non-Farm Payrolls (févr.)",      "country": "🇺🇸", "importance": "critical", "forecast": "200K",   "previous": "256K"},
    {"date": "2026-03-06", "event": "Taux de chômage (févr.)",        "country": "🇺🇸", "importance": "high",     "forecast": "4.1%",   "previous": "4.0%"},
    {"date": "2026-03-06", "event": "Décision taux BCE",              "country": "🇪🇺", "importance": "critical", "forecast": "Hold",   "previous": "2.65%"},
    {"date": "2026-03-07", "event": "Michigan Consumer Confidence",   "country": "🇺🇸", "importance": "medium",   "forecast": None,     "previous": "64.7"},
    {"date": "2026-03-11", "event": "JOLTS Job Openings (janv.)",     "country": "🇺🇸", "importance": "medium",   "forecast": None,     "previous": "7.6M"},
    {"date": "2026-03-11", "event": "IPC a/a (févr.)",                "country": "🇺🇸", "importance": "critical", "forecast": "2.4%",   "previous": "3.0%", "actual": "2.4%"},
    {"date": "2026-03-11", "event": "IPC core a/a (févr.)",           "country": "🇺🇸", "importance": "critical", "forecast": "2.5%",   "previous": "3.3%", "actual": "2.5%"},
    {"date": "2026-03-13", "event": "Jobless Claims",                 "country": "🇺🇸", "importance": "medium",   "forecast": None,     "previous": "242K"},
    {"date": "2026-03-13", "event": "PIB Q4 2025 (2e estimation)",    "country": "🇺🇸", "importance": "high",     "forecast": "1.4%",   "previous": "1.4%"},
    {"date": "2026-03-13", "event": "PCE Price Index a/a (janv.)",    "country": "🇺🇸", "importance": "critical", "forecast": None,     "previous": "2.9%"},
    {"date": "2026-03-13", "event": "Revenus et dépenses (janv.)",    "country": "🇺🇸", "importance": "medium",   "forecast": None,     "previous": None},
    {"date": "2026-03-17", "event": "Ventes au détail (févr.)",       "country": "🇺🇸", "importance": "high",     "forecast": None,     "previous": "-0.2%"},
    {"date": "2026-03-18", "event": "IPP (févr.)",                    "country": "🇺🇸", "importance": "medium",   "forecast": None,     "previous": "3.5%"},
    {"date": "2026-03-15", "event": "Production industrielle Chine",  "country": "🇨🇳", "importance": "medium",   "forecast": None,     "previous": "6.2%"},
    {"date": "2026-03-17", "event": "NY Fed Manufacturing",           "country": "🇺🇸", "importance": "medium",   "forecast": None,     "previous": "5.7"},
    {"date": "2026-03-17", "event": "Début réunion FOMC",             "country": "🇺🇸", "importance": "high",     "forecast": None,     "previous": None},
    {"date": "2026-03-18", "event": "Décision taux FOMC",             "country": "🇺🇸", "importance": "critical", "forecast": "Hold",   "previous": "3.50-3.75%"},
    {"date": "2026-03-18", "event": "Conférence de presse Powell",    "country": "🇺🇸", "importance": "critical", "forecast": None,     "previous": None},
    {"date": "2026-03-18", "event": "FOMC Dot Plot / Projections",    "country": "🇺🇸", "importance": "high",     "forecast": None,     "previous": None},
    {"date": "2026-03-19", "event": "Décision taux BOJ",              "country": "🇯🇵", "importance": "high",     "forecast": None,     "previous": "0.50%"},
    {"date": "2026-03-20", "event": "Philadelphia Fed Index",         "country": "🇺🇸", "importance": "medium",   "forecast": None,     "previous": "18.1"},
    {"date": "2026-03-26", "event": "Consumer Confidence (CB)",       "country": "🇺🇸", "importance": "medium",   "forecast": None,     "previous": "104.1"},
    {"date": "2026-03-26", "event": "Durable Goods Orders (févr.)",    "country": "🇺🇸", "importance": "medium",   "forecast": None,     "previous": "3.1%"},
    {"date": "2026-04-01", "event": "ISM Manufacturing PMI (mars)",   "country": "🇺🇸", "importance": "high",     "forecast": None,     "previous": "50.3"},
    {"date": "2026-04-03", "event": "Non-Farm Payrolls (mars)",       "country": "🇺🇸", "importance": "critical", "forecast": None,     "previous": "200K"},
    {"date": "2026-04-10", "event": "IPC (mars)",                     "country": "🇺🇸", "importance": "critical", "forecast": None,     "previous": "2.4%"},
    {"date": "2026-04-16", "event": "PIB Chine T1 2026",              "country": "🇨🇳", "importance": "high",     "forecast": None,     "previous": "5.0%"},
    {"date": "2026-04-29", "event": "Décision taux FOMC",             "country": "🇺🇸", "importance": "critical", "forecast": None,     "previous": "3.50-3.75%"},
    {"date": "2026-04-30", "event": "PIB T1 2026 (avance)",           "country": "🇺🇸", "importance": "high",     "forecast": None,     "previous": "2.3%"},
    # ── Canada ────────────────────────────────────────────────────────────────
    {"date": "2026-03-06", "event": "Rapport sur l'emploi (févr.)",   "country": "🇨🇦", "importance": "critical", "forecast": "+25K",   "previous": "+76.0K"},
    {"date": "2026-03-06", "event": "Taux de chômage (févr.)",        "country": "🇨🇦", "importance": "high",     "forecast": "7.0%",   "previous": "6.6%"},
    {"date": "2026-03-11", "event": "Mises en chantier (févr.)",      "country": "🇨🇦", "importance": "medium",   "forecast": None,     "previous": "231K"},
    {"date": "2026-03-18", "event": "IPC a/a (févr.)",                "country": "🇨🇦", "importance": "critical", "forecast": "2.0%",   "previous": "1.8%"},
    {"date": "2026-03-20", "event": "Ventes au détail (janv.)",       "country": "🇨🇦", "importance": "high",     "forecast": None,     "previous": "+2.6%"},
    {"date": "2026-03-27", "event": "PIB mensuel (janv.)",            "country": "🇨🇦", "importance": "high",     "forecast": "+0.3%",  "previous": "-0.2%"},
    {"date": "2026-04-03", "event": "Rapport sur l'emploi (mars)",    "country": "🇨🇦", "importance": "critical", "forecast": None,     "previous": "+25K"},
    {"date": "2026-04-16", "event": "Décision taux BdC",              "country": "🇨🇦", "importance": "critical", "forecast": "Baisse", "previous": "3.00%"},
    {"date": "2026-04-17", "event": "IPC a/a (mars)",                 "country": "🇨🇦", "importance": "critical", "forecast": None,     "previous": "2.0%"},
    {"date": "2026-04-24", "event": "Ventes au détail (févr.)",       "country": "🇨🇦", "importance": "high",     "forecast": None,     "previous": None},
    {"date": "2026-05-01", "event": "PIB mensuel (févr.)",            "country": "🇨🇦", "importance": "high",     "forecast": None,     "previous": "+0.3%"},
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

# Tickers representing yield levels: MTD/YTD = absolute change in pp (e.g. +0.20%),
# NOT a price return.  20 bps = +0.20 pp displayed as "+0.20%".
YIELD_TICKERS = {"^IRX", "^FVX", "^TNX", "^TYX",
                 "CA2YT=RR", "CA5YT=RR", "CA10YT=RR", "CA30YT=RR"}

CENTRAL_BANK_CONFIG = [
    {
        "flag": "🇺🇸", "name": "États-Unis",  "bank": "Fed",  "bank_key": "fed",
        "bias": "dovish",  "next_meeting": "6-7 mai",
        "fallback_rate": "3.75–4.00%", "fallback_change": "↓",
    },
    {
        "flag": "🇪🇺", "name": "Zone Euro",   "bank": "BCE",  "bank_key": "ecb",
        "bias": "dovish",  "next_meeting": "17 avr.",
        "fallback_rate": "2.65%",      "fallback_change": "↓",
    },
    {
        "flag": "🇨🇦", "name": "Canada",      "bank": "BdC",  "bank_key": "boc",
        "bias": "dovish",  "next_meeting": "16 avr.",
        "fallback_rate": "3.00%",      "fallback_change": "↓",
    },
    {
        "flag": "🇬🇧", "name": "Royaume-Uni", "bank": "BOE",  "bank_key": "boe",
        "bias": "neutral", "next_meeting": "8 mai",
        "fallback_rate": "4.50%",      "fallback_change": "↓",
    },
    {
        "flag": "🇯🇵", "name": "Japon",       "bank": "BOJ",  "bank_key": "boj",
        "bias": "hawkish", "next_meeting": "30 avr.",
        "fallback_rate": "0.50%",      "fallback_change": "↑",
    },
    {
        "flag": "🇨🇭", "name": "Suisse",      "bank": "BNS",  "bank_key": "snb",
        "bias": "neutral", "next_meeting": "19 juin",
        "fallback_rate": "0.25%",      "fallback_change": "↓",
    },
]

# ─── TradingView Ticker Map ────────────────────────────────────────────────────
# Maps Yahoo Finance ticker  →  TradingView "EXCHANGE:SYMBOL" notation.
# Screener (america / forex / crypto) is inferred from the exchange prefix.
# Tickers absent from this map fall through to the Yahoo Finance path.
TV_TICKER_MAP: dict[str, str] = {
    # ── Commodity futures ─────────────────────────────────────────────────────
    "GC=F":  "COMEX:GC1!",
    "CL=F":  "NYMEX:CL1!",
    "NG=F":  "NYMEX:NG1!",
    "BZ=F":  "NYMEX:BB1!",   # Brent crude
    "SI=F":  "COMEX:SI1!",
    "HG=F":  "COMEX:HG1!",
    "PL=F":  "NYMEX:PL1!",
    "ZC=F":  "CBOT:ZC1!",
    "ZW=F":  "CBOT:ZW1!",
    # ── US Indices ────────────────────────────────────────────────────────────
    "^GSPC":     "TVC:SPX",
    "^NDX":      "NASDAQ:NDX",
    "^DJI":      "TVC:DJI",
    "^RUT":      "TVC:RUT",
    "^STOXX50E": "TVC:STOXX50E",
    "^N225":     "TVC:NI225",
    "^VIX":      "TVC:VIX",
    "^MOVE":     "TVC:MOVE",
    # ── US Treasury yields ────────────────────────────────────────────────────
    "^IRX": "TVC:IRX",
    "^FVX": "TVC:FVX",
    "^TNX": "TVC:TNX",
    "^TYX": "TVC:TYX",
    # ── DXY & Forex ───────────────────────────────────────────────────────────
    "DX-Y.NYB": "TVC:DXY",
    "EURUSD=X": "FX:EURUSD",
    "GBPUSD=X": "FX:GBPUSD",
    "JPY=X":    "FX:USDJPY",
    "CHF=X":    "FX:USDCHF",
    "USDCAD=X": "FX:USDCAD",
    "AUDUSD=X": "FX:AUDUSD",
    "NZDUSD=X": "FX:NZDUSD",
    "CNY=X":    "FX_IDC:USDCNY",
    "MXN=X":    "FX:USDMXN",
    "BRL=X":    "FX:USDBRL",
    # ── Crypto ────────────────────────────────────────────────────────────────
    "BTC-USD": "COINBASE:BTCUSD",
    "ETH-USD": "COINBASE:ETHUSD",
    # ── US ETFs & Risk proxy ──────────────────────────────────────────────────
    "EEM":  "AMEX:EEM",
    "TLT":  "AMEX:TLT",
    "HYG":  "AMEX:HYG",
    "LQD":  "AMEX:LQD",
    "SPY":  "AMEX:SPY",
    "XLK":  "AMEX:XLK",
    "XLF":  "AMEX:XLF",
    "XLV":  "AMEX:XLV",
    "XLY":  "AMEX:XLY",
    "XLP":  "AMEX:XLP",
    "XLE":  "AMEX:XLE",
    "XLI":  "AMEX:XLI",
    "XLB":  "AMEX:XLB",
    "XLRE": "AMEX:XLRE",
    "XLU":  "AMEX:XLU",
    "XLC":  "AMEX:XLC",
    # ── MISO indicator series ─────────────────────────────────────────────────
    "^NYAD":  "NYSE:NYAD",
    "^VIX3M": "CBOE:VIX3M",
    "^VXMT":  "CBOE:VXMT",
}

_TV_FOREX_EXCHANGES  = {"FX", "FX_IDC", "OANDA", "FOREXCOM", "PEPPERSTONE"}
_TV_CRYPTO_EXCHANGES = {"COINBASE", "BINANCE", "KRAKEN", "BYBIT", "BITFINEX"}


def _tv_screener(full_sym: str) -> str:
    """Infer TradingView screener from 'EXCHANGE:SYMBOL' notation."""
    exchange = full_sym.split(":")[0].upper()
    if exchange in _TV_FOREX_EXCHANGES:
        return "forex"
    if exchange in _TV_CRYPTO_EXCHANGES:
        return "crypto"
    return "america"


def _fetch_tv_batch(yf_tickers: list[str]) -> dict[str, dict]:
    """Batch-fetch prices + daily changes from TradingView scanner API.

    Groups tickers by screener and issues one POST per screener (typically
    2 calls: "america" + "forex"), returning a dict keyed by Yahoo Finance
    ticker.  Tickers with no mapping, null values, or HTTP errors are omitted
    so the caller can fall back to Yahoo Finance.

    TradingView `change` = daily % change (e.g. 1.5 → +1.5 %).
    TradingView `change_abs` = absolute daily change (signed).
    Both fields already reference the correct previous session close
    regardless of pre-market / regular / after-hours state.
    """
    mapped = [(yf, TV_TICKER_MAP[yf]) for yf in yf_tickers if yf in TV_TICKER_MAP]
    if not mapped:
        return {}

    # Group by screener
    by_screener: dict[str, list[tuple[str, str]]] = {}
    for yf_ticker, tv_sym in mapped:
        by_screener.setdefault(_tv_screener(tv_sym), []).append((yf_ticker, tv_sym))

    result: dict[str, dict] = {}
    headers = {
        "Content-Type": "application/json",
        "User-Agent":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin":       "https://www.tradingview.com",
        "Referer":      "https://www.tradingview.com/",
    }

    for screener, items in by_screener.items():
        tv_syms = [tv for _, tv in items]
        yf_by_tv = {tv: yf for yf, tv in items}

        payload = _json.dumps({
            "symbols": {"tickers": tv_syms, "query": {"types": []}},
            "columns": ["close", "change_abs", "change"],
        }).encode("utf-8")

        try:
            req = urllib.request.Request(
                f"https://scanner.tradingview.com/{screener}/scan",
                data=payload,
                headers=headers,
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = _json.loads(resp.read().decode("utf-8"))

            for row in data.get("data", []):
                tv_sym   = row.get("s", "")
                yf_tick  = yf_by_tv.get(tv_sym)
                if yf_tick is None:
                    continue
                d = row.get("d", [None, None, None])
                try:
                    price      = float(d[0]) if d[0] is not None else None
                    change_abs = float(d[1]) if d[1] is not None else None
                    change_pct = float(d[2]) if d[2] is not None else None
                    if price and price > 0:
                        result[yf_tick] = {
                            "price":      round(price, 4),
                            "change":     round(change_abs, 4) if change_abs is not None else None,
                            "change_pct": round(change_pct, 2) if change_pct is not None else None,
                        }
                except (TypeError, ValueError, IndexError):
                    pass

        except Exception as e:
            logger.warning(f"TradingView fetch failed (screener={screener}): {e}")

    return result


# ─── TradingView historical data (tvDatafeed) ─────────────────────────────────
# tvDatafeed uses TradingView's WebSocket API with an anonymous session.
# Delayed data (≈15 min) is available without login; sufficient for charts.

_tvdf_instance: Any = None   # lazy-initialized singleton


def _get_tvdf() -> Any:
    """Return a lazy-initialized TvDatafeed instance, or None on failure."""
    global _tvdf_instance
    if _tvdf_instance is None:
        try:
            from tvDatafeed import TvDatafeed  # type: ignore[import]
            _tvdf_instance = TvDatafeed()       # anonymous session
        except Exception as e:
            logger.warning(f"tvDatafeed init failed: {e}")
    return _tvdf_instance


def _fetch_tv_hist_df(tv_full_sym: str, n_bars: int) -> pd.DataFrame:
    """Fetch daily OHLCV from TradingView via tvDatafeed.

    Returns a DataFrame with yfinance-style column names (Open/High/Low/Close/Volume)
    and a DatetimeIndex, or an empty DataFrame on any failure.
    """
    if not tv_full_sym or ":" not in tv_full_sym:
        return pd.DataFrame()
    try:
        from tvDatafeed import Interval as TvInterval  # type: ignore[import]
        exchange, symbol = tv_full_sym.split(":", 1)
        tvdf = _get_tvdf()
        if tvdf is None:
            return pd.DataFrame()
        df = tvdf.get_hist(
            symbol=symbol,
            exchange=exchange,
            interval=TvInterval.in_daily,
            n_bars=n_bars,
        )
        if df is None or df.empty:
            return pd.DataFrame()
        # tvDatafeed returns lowercase columns; normalize to yfinance-style
        rename = {c: c.capitalize()
                  for c in df.columns
                  if c.lower() in {"open", "high", "low", "close", "volume"}}
        return df.rename(columns=rename)
    except Exception as e:
        logger.warning(f"tvDatafeed history failed for {tv_full_sym}: {e}")
        return pd.DataFrame()


def _yf_hist_close(yf_ticker: str, period: str) -> pd.Series:
    """Yahoo Finance fallback: return Close series for a ticker."""
    try:
        return yf.Ticker(yf_ticker).history(period=period)["Close"].dropna()
    except Exception:
        return pd.Series(dtype=float)


def _tv_or_yf_close(yf_ticker: str, period: str, n_bars: int) -> pd.Series:
    """TV-first, Yahoo-fallback Close series helper for historical computations."""
    tv_sym = TV_TICKER_MAP.get(yf_ticker, "")
    df = _fetch_tv_hist_df(tv_sym, n_bars) if tv_sym else pd.DataFrame()
    if not df.empty and "Close" in df.columns:
        return df["Close"].dropna()
    return _yf_hist_close(yf_ticker, period)


# ─── TradingView period-performance (scanner Perf columns) ────────────────────
def _fetch_tv_perf_batch(yf_tickers: list[str]) -> dict[str, dict]:
    """Fetch YTD and 1M performance directly from TradingView scanner.

    TV `Perf.YTD` = % change since Jan 1 (already in %).
    TV `Perf.1M`  = rolling-30-day % change (≈ MTD).

    For YIELD_TICKERS the absolute pp-change is back-computed:
        pp = close − close / (1 + perf/100)
    so that "+0.45 pp" is returned instead of "+11.25 %".
    """
    mapped = [(yf, TV_TICKER_MAP[yf]) for yf in yf_tickers if yf in TV_TICKER_MAP]
    if not mapped:
        return {}

    by_screener: dict[str, list[tuple[str, str]]] = {}
    for yf_ticker, tv_sym in mapped:
        by_screener.setdefault(_tv_screener(tv_sym), []).append((yf_ticker, tv_sym))

    result: dict[str, dict] = {}
    headers = {
        "Content-Type": "application/json",
        "User-Agent":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin":       "https://www.tradingview.com",
        "Referer":      "https://www.tradingview.com/",
    }

    for screener, items in by_screener.items():
        tv_syms  = [tv for _, tv in items]
        yf_by_tv = {tv: yf for yf, tv in items}

        payload = _json.dumps({
            "symbols": {"tickers": tv_syms, "query": {"types": []}},
            "columns": ["close", "Perf.YTD", "Perf.1M"],
        }).encode("utf-8")

        try:
            req = urllib.request.Request(
                f"https://scanner.tradingview.com/{screener}/scan",
                data=payload,
                headers=headers,
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = _json.loads(resp.read().decode("utf-8"))

            for row in data.get("data", []):
                tv_sym  = row.get("s", "")
                yf_tick = yf_by_tv.get(tv_sym)
                if yf_tick is None:
                    continue
                d = row.get("d", [None, None, None])
                try:
                    close    = float(d[0]) if d[0] is not None else None
                    perf_ytd = float(d[1]) if d[1] is not None else None
                    perf_1m  = float(d[2]) if d[2] is not None else None
                    if close is None or perf_ytd is None:
                        continue
                    if yf_tick in YIELD_TICKERS:
                        # Back-compute absolute pp change from % change + current level
                        ytd_pp = round(close - close / (1 + perf_ytd / 100), 2)
                        mtd_pp = (round(close - close / (1 + perf_1m / 100), 2)
                                  if perf_1m is not None else ytd_pp)
                        result[yf_tick] = {"ytd": ytd_pp, "mtd": mtd_pp}
                    else:
                        result[yf_tick] = {
                            "ytd": round(perf_ytd, 2),
                            "mtd": round(perf_1m, 2) if perf_1m is not None else round(perf_ytd, 2),
                        }
                except (TypeError, ValueError, IndexError):
                    pass

        except Exception as e:
            logger.warning(f"TradingView perf fetch failed (screener={screener}): {e}")

    return result


# ─── Data Fetching (cached 60s) ───────────────────────────────────────────────
def _fetch_one(ticker: str) -> tuple[str, dict]:
    """Fetch current price and daily change for a single ticker.

    Priority chain (highest → lowest):
    0. fast_info._data  regularMarketPrice + regularMarketChange   (Yahoo's own value)
    1. fast_info.last_price + fast_info.previous_close / regular_market_previous_close
    2. t.info  regularMarketPrice + regularMarketPreviousClose      (v10 quoteSummary)
    3. history weekday-search fallback                              (last resort)

    Tier 0 rationale:
    The chart API (v8/finance/chart) meta section always contains regularMarketChange
    — the exact absolute daily change Yahoo Finance displays on its quote pages.
    It is pre-computed server-side and is immune to ALL session-boundary and
    timezone issues that plague self-computed (current − prev_close) approaches
    for CME futures, forex, and exotic instruments.
    """
    try:
        t = yf.Ticker(ticker)

        def _safe(attr: str) -> float | None:
            """Return a positive, finite float from a fast_info property, or None."""
            try:
                v = getattr(t.fast_info, attr)
                f = float(v)
                return f if (f > 0 and pd.notna(f)) else None
            except Exception:
                return None

        def _meta(key: str) -> float | None:
            """Return a finite float from fast_info._data (allows negatives), or None."""
            try:
                v = t.fast_info._data.get(key)
                if v is None:
                    return None
                f = float(v)
                return f if pd.notna(f) else None
            except Exception:
                return None

        def _meta_ts(key: str) -> int:
            """Return a Unix timestamp int from fast_info._data, or 0."""
            try:
                v = t.fast_info._data.get(key)
                return int(v) if v is not None else 0
            except Exception:
                return 0

        # ── Tier 0: fast_info._data — session-aware, timestamp-ranked ────────
        # Yahoo Finance's chart API populates three session buckets in meta:
        #   regularMarket*  – last regular-session price (stale in pre-market)
        #   preMarket*      – pre-market quote (4am–9:30am ET for equities)
        #   postMarket*     – after-hours quote (4pm–8pm ET for equities)
        # Each bucket has its own *Time Unix timestamp.  We pick the bucket
        # with the MOST RECENT timestamp, so:
        #   • Equities pre-market  → preMarket bucket   (vs yesterday's close)
        #   • Equities regular hrs → regularMarket       (vs yesterday's close)
        #   • Equities after hours → postMarket          (vs today's close)
        #   • 24h futures          → regularMarket wins  (always freshest)
        # The *Change field in each bucket is already relative to the correct
        # "16:00 previous session close" for that session type.
        _sessions = [
            ("regularMarketPrice",  "regularMarketChange",  "regularMarketTime"),
            ("preMarketPrice",      "preMarketChange",      "preMarketTime"),
            ("postMarketPrice",     "postMarketChange",     "postMarketTime"),
        ]
        candidates = []
        for price_key, change_key, ts_key in _sessions:
            price  = _meta(price_key)
            change = _meta(change_key)
            ts     = _meta_ts(ts_key)
            if price and price > 0 and change is not None and ts > 0:
                prev_impl = price - change
                if prev_impl > 0:
                    candidates.append((ts, price, change, prev_impl))

        if candidates:
            _, best_price, best_change, best_prev = max(candidates,
                                                        key=lambda x: x[0])
            chg_pct = round((best_change / best_prev) * 100, 2)
            return ticker, {"price":      round(best_price, 4),
                            "change":     round(best_change, 4),
                            "change_pct": chg_pct}

        # ── Tier 1: fast_info properties — previous_close ────────────────────
        current    = _safe("last_price")
        prev_close = (_safe("previous_close")
                      or _safe("regular_market_previous_close"))

        if current and prev_close:
            change  = current - prev_close
            chg_pct = round((change / prev_close) * 100, 2)
            return ticker, {"price": round(current, 4),
                            "change": round(change, 4),
                            "change_pct": chg_pct}

        # ── Tier 2: t.info — Yahoo Finance v10/quoteSummary ──────────────────
        if current is None or prev_close is None:
            try:
                info = t.info
                def _info_float(key: str) -> float | None:
                    v = info.get(key)
                    if v is None:
                        return None
                    try:
                        f = float(v)
                        return f if (f > 0 and pd.notna(f)) else None
                    except (ValueError, TypeError):
                        return None

                if current is None:
                    current = (_info_float("regularMarketPrice")
                               or _info_float("currentPrice"))
                if prev_close is None:
                    prev_close = (_info_float("regularMarketPreviousClose")
                                  or _info_float("previousClose"))
            except Exception:
                pass

        if current and prev_close:
            change  = current - prev_close
            chg_pct = round((change / prev_close) * 100, 2)
            return ticker, {"price": round(current, 4),
                            "change": round(change, 4),
                            "change_pct": chg_pct}

        # ── Tier 3: History fallback ──────────────────────────────────────────
        hist = t.history(period="5d", auto_adjust=True).dropna(subset=["Close"])
        hist = hist[hist["Close"] > 0]

        if len(hist) < 1:
            return ticker, {"price": None, "change": None, "change_pct": None}

        current = current or float(hist["Close"].iloc[-1])

        if prev_close is None:
            # Search backwards for the last weekday bar, skipping Sunday CME
            # partial sessions (CME reopens Sun 17:00–18:00 ET).
            for i in range(len(hist) - 2, -1, -1):
                ts = hist.index[i]
                bar_date = (ts.date() if ts.tzinfo is None
                            else ts.tz_convert("UTC").date())
                if bar_date.weekday() < 5:        # 0=Mon … 4=Fri
                    prev_close = float(hist["Close"].iloc[i])
                    break
            if prev_close is None:
                if len(hist) >= 2:
                    prev_close = float(hist["Close"].iloc[-2])
                else:
                    return ticker, {"price": round(current, 4),
                                    "change": None, "change_pct": None}

        change  = current - prev_close
        chg_pct = round((change / prev_close) * 100, 2)
        return ticker, {"price": round(current, 4),
                        "change": round(change, 4),
                        "change_pct": chg_pct}

    except Exception as e:
        logger.warning(f"Error fetching {ticker}: {e}")
    return ticker, {"price": None, "change": None, "change_pct": None}


@st.cache_data(ttl=60, show_spinner=False)
def fetch_market_data() -> dict:
    tickers = list({a["ticker"] for a in MARKET_ASSETS})

    # Step 1 – TradingView batch (1-2 HTTP calls, best data quality)
    result = _fetch_tv_batch(tickers)

    # Step 2 – Yahoo Finance fallback for tickers TV missed
    missing = [t for t in tickers if t not in result]
    if missing:
        with ThreadPoolExecutor(max_workers=10) as ex:
            for future in as_completed(
                {ex.submit(_fetch_one, t): t for t in missing}, timeout=25
            ):
                try:
                    ticker, data = future.result()
                    result[ticker] = data
                except Exception:
                    pass
    return result


@st.cache_data(ttl=300, show_spinner=False)
def get_vix_history() -> list[dict]:
    try:
        # TradingView first (tvDatafeed), Yahoo Finance fallback
        closes = _tv_or_yf_close("^VIX", "30d", 35)
        return [{"date": str(idx.date()), "value": round(float(v), 2)}
                for idx, v in closes.items()]
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
            # YTD: absolute change in percentage points (e.g. 4.70 - 4.50 = +0.20 pp)
            ytd = round(latest - float(obs[0][series]["v"]), 2) if len(obs) >= 2 else None
            # MTD: absolute change in pp since 1st of current month
            month_obs = [o for o in obs if o["d"] >= month_start]
            mtd = None
            if month_obs:
                first = float(month_obs[0][series]["v"])
                mtd = round(latest - first, 2) if first is not None else None

            result[ticker] = {"price": round(latest, 3), "change": change, "change_pct": change_pct,
                               "mtd": mtd, "ytd": ytd}
        except Exception as e:
            logger.warning(f"BOC fetch error {series}: {e}")
            result[ticker] = {"price": None, "change": None, "change_pct": None, "mtd": None, "ytd": None}
    return result


@st.cache_data(ttl=300, show_spinner=False)
def fetch_period_performance() -> dict:
    """Fetch MTD and YTD % for all tickers (cached 5 min).

    Primary source: TradingView scanner Perf.YTD + Perf.1M columns.
      YTD  = Perf.YTD  (from Jan 1, in %)
      MTD  = Perf.1M   (rolling 30 days ≈ calendar MTD, in %)
      For YIELD_TICKERS the scanner percentage is back-computed to pp-change.

    Fallback (tickers with no TV mapping, e.g. CA yields): Yahoo Finance
    1-year history with strict calendar-boundary close-to-close convention.
    """
    tickers = list({a["ticker"] for a in MARKET_ASSETS})

    # ── Step 1: TradingView scanner (Perf.YTD + Perf.1M) ─────────────────────
    result = _fetch_tv_perf_batch(tickers)

    # ── Step 2: Yahoo Finance fallback for TV misses ───────────────────────────
    missing = [t for t in tickers if t not in result]
    if missing:
        now_utc = datetime.now(timezone.utc)
        _z = dict(hour=0, minute=0, second=0, microsecond=0)
        year_boundary  = now_utc.replace(month=1, day=1, **_z)
        month_boundary = now_utc.replace(day=1,          **_z)

        def _fetch_perf_yf(ticker: str) -> tuple[str, dict]:
            try:
                hist = (yf.Ticker(ticker)
                        .history(period="1y", auto_adjust=True)
                        .dropna(subset=["Close"]))
                hist = hist[hist["Close"] > 0]
                if len(hist) < 2:
                    return ticker, {"mtd": None, "ytd": None}
                latest   = float(hist["Close"].iloc[-1])
                is_yield = ticker in YIELD_TICKERS
                idx_utc = (hist.index.tz_convert("UTC") if hist.index.tz is not None
                           else hist.index.tz_localize("UTC"))

                def _last_close_before(boundary: datetime) -> Optional[float]:
                    pre = hist[idx_utc < pd.Timestamp(boundary)]
                    return float(pre["Close"].iloc[-1]) if len(pre) > 0 else None

                def _perf(start: float) -> float:
                    return round(latest - start, 2) if is_yield \
                        else round((latest - start) / start * 100, 2)

                ytd_start = _last_close_before(year_boundary) or float(hist["Close"].iloc[0])
                mtd_start = _last_close_before(month_boundary)
                return ticker, {
                    "ytd": _perf(ytd_start),
                    "mtd": _perf(mtd_start) if mtd_start is not None else _perf(ytd_start),
                }
            except Exception as e:
                logger.warning(f"Perf fetch error {ticker}: {e}")
                return ticker, {"mtd": None, "ytd": None}

        with ThreadPoolExecutor(max_workers=10) as ex:
            for future in as_completed(
                {ex.submit(_fetch_perf_yf, t): t for t in missing}, timeout=35
            ):
                try:
                    tk, data = future.result()
                    result[tk] = data
                except Exception:
                    pass
    return result



@st.cache_data(ttl=3600, show_spinner=False)
def fetch_cb_rates() -> dict:
    """Fetch central bank policy rates from free public APIs (1-hour cache).

    Returns dict keyed by bank_key →
        {"rate_str": "X.XX%", "change": "↑/↓/=", "live": True}
    Falls back gracefully – missing keys trigger static fallback in _build_cb_display().
    APIs used (all free, no authentication required except FRED):
        ECB  – data-api.ecb.europa.eu (Deposit Facility Rate)
        BOC  – bankofcanada.ca/valet   (Overnight Rate Target V122530)
        FRED – api.stlouisfed.org      (Fed, BOE, BOJ, SNB) – needs FRED_API_KEY env var
    """
    import os
    import urllib.request
    import json as _json

    results: dict = {}

    def _get_json(url: str, timeout: int = 8):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return _json.loads(r.read().decode())
        except Exception as exc:
            logger.warning(f"CB API error [{url}]: {exc}")
            return None

    def _chg(curr: float, prev) -> str:
        if prev is None or curr is None:
            return "="
        diff = curr - prev
        if diff > 0.01:
            return "↑"
        if diff < -0.01:
            return "↓"
        return "="

    def _fmt(rate: float) -> str:
        return f"{rate:.2f}%"

    # ── ECB Deposit Facility Rate ──────────────────────────────────────────────
    try:
        url = (
            "https://data-api.ecb.europa.eu/service/data/FM/"
            "B.U2.EUR.4F.KR.DFR.LEV"
            "?format=jsondata&detail=dataonly&lastNObservations=2"
        )
        data = _get_json(url)
        if data:
            obs = data["dataSets"][0]["series"]["0:0:0:0:0:0"]["observations"]
            sorted_keys = sorted(obs.keys(), key=int)
            curr_v = float(obs[sorted_keys[-1]][0])
            prev_v = float(obs[sorted_keys[-2]][0]) if len(sorted_keys) >= 2 else None
            results["ecb"] = {"rate_str": _fmt(curr_v), "change": _chg(curr_v, prev_v), "live": True}
    except Exception as exc:
        logger.warning(f"ECB parse error: {exc}")

    # ── Bank of Canada overnight rate target (V122530) ─────────────────────────
    try:
        url = (
            "https://www.bankofcanada.ca/valet/observations/"
            "V122530/json?order_dir=desc&limit=2"
        )
        data = _get_json(url)
        if data:
            obs = data.get("observations", [])
            if obs:
                curr_v = float(obs[0]["V122530"]["v"])
                prev_v = float(obs[1]["V122530"]["v"]) if len(obs) >= 2 else None
                results["boc"] = {"rate_str": _fmt(curr_v), "change": _chg(curr_v, prev_v), "live": True}
    except Exception as exc:
        logger.warning(f"BOC parse error: {exc}")

    # ── FRED – Fed, BOE, BOJ, SNB ──────────────────────────────────────────────
    fred_key = os.environ.get("FRED_API_KEY", "")
    if fred_key:
        def _fred(series_id: str):
            url = (
                f"https://api.stlouisfed.org/fred/series/observations"
                f"?series_id={series_id}&api_key={fred_key}"
                f"&sort_order=desc&limit=2&file_type=json"
            )
            d = _get_json(url)
            if d and d.get("observations"):
                def _v(o): return float(o["value"]) if o.get("value") not in (".", None) else None
                obs = d["observations"]
                return _v(obs[0]), (_v(obs[1]) if len(obs) >= 2 else None)
            return None, None

        # Fed – mid-point of upper (DFEDTARU) and lower (DFEDTARL) bounds
        try:
            cu, pu = _fred("DFEDTARU")
            cl, pl = _fred("DFEDTARL")
            if cu is not None and cl is not None:
                curr_v = (cu + cl) / 2
                prev_v = ((pu + pl) / 2) if (pu is not None and pl is not None) else None
                lo, hi = min(cl, cu), max(cl, cu)
                results["fed"] = {
                    "rate_str": f"{lo:.2f}–{hi:.2f}%",
                    "change": _chg(curr_v, prev_v),
                    "live": True,
                }
        except Exception as exc:
            logger.warning(f"FRED Fed error: {exc}")

        # BOE (Bank Rate Monthly – BOERUKM)
        try:
            curr_v, prev_v = _fred("BOERUKM")
            if curr_v is not None:
                results["boe"] = {"rate_str": _fmt(curr_v), "change": _chg(curr_v, prev_v), "live": True}
        except Exception as exc:
            logger.warning(f"FRED BOE error: {exc}")

        # BOJ (IRSTJPN)
        try:
            curr_v, prev_v = _fred("IRSTJPN")
            if curr_v is not None:
                results["boj"] = {"rate_str": _fmt(curr_v), "change": _chg(curr_v, prev_v), "live": True}
        except Exception as exc:
            logger.warning(f"FRED BOJ error: {exc}")

        # SNB (IRSTSNB)
        try:
            curr_v, prev_v = _fred("IRSTSNB")
            if curr_v is not None:
                results["snb"] = {"rate_str": _fmt(curr_v), "change": _chg(curr_v, prev_v), "live": True}
        except Exception as exc:
            logger.warning(f"FRED SNB error: {exc}")

    return results


def _build_cb_display(live: dict) -> list[dict]:
    """Merge CENTRAL_BANK_CONFIG with live API data; fall back to static values."""
    display = []
    for cfg in CENTRAL_BANK_CONFIG:
        key = cfg["bank_key"]
        entry = dict(cfg)
        live_data = live.get(key)
        if live_data:
            entry["rate"]    = live_data["rate_str"]
            entry["change"]  = live_data["change"]
            entry["is_live"] = True
        else:
            entry["rate"]    = cfg["fallback_rate"]
            entry["change"]  = cfg["fallback_change"]
            entry["is_live"] = False
        display.append(entry)
    return display


@st.cache_data(ttl=600, show_spinner=False)
def fetch_asset_history_1y(ticker: str) -> pd.DataFrame:
    """Fetch 1-year OHLC + volume history for a single ticker (10-min cache)."""
    try:
        # TradingView first (tvDatafeed), Yahoo Finance fallback
        tv_sym = TV_TICKER_MAP.get(ticker, "")
        df = _fetch_tv_hist_df(tv_sym, 365) if tv_sym else pd.DataFrame()
        if df.empty:
            df = yf.Ticker(ticker).history(period="1y", auto_adjust=True)
        return df.dropna(subset=["Close"]) if not df.empty else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def _classify_tags(title: str) -> list[str]:
    """Return topic tags for a news headline."""
    tl = title.lower()
    tags: list[str] = []
    if any(w in tl for w in ["war", "conflict", "attack", "military", "nuclear",
                               "sanctions", "nato", "ukraine", "russia", "china",
                               "taiwan", "iran", "israel", "geopolit", "coup"]):
        tags.append("geo")
    if any(w in tl for w in ["inflation", "rate", "fed", "ecb", "boj", "gdp",
                               "jobs", "recession", "cpi", "fomc", "pce",
                               "unemployment", "tariff", "trade", "deficit"]):
        tags.append("eco")
    if any(w in tl for w in ["market", "stock", "equity", "bond", "gold", "oil",
                               "crypto", "bitcoin", "rally", "crash", "nasdaq",
                               "dow", "s&p", "vix", "yield", "dollar"]):
        tags.append("mkt")
    return tags


def _fetch_feed_safe(url: str, ua: Optional[str] = None, timeout: int = 8) -> list:
    """Fetch RSS via urllib with timeout; returns feedparser entries list."""
    try:
        headers = {"User-Agent": ua or "Mozilla/5.0 (market-dashboard/1.0)"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read()
        return feedparser.parse(content).entries
    except Exception:
        return []


def _fetch_nitter_feeds() -> list[dict]:
    """Pull X/Twitter timelines via public Nitter instances (best-effort)."""
    items: list[dict] = []
    for display, username in _X_ACCOUNTS:
        for instance in _NITTER_INSTANCES:
            entries = _fetch_feed_safe(
                f"{instance}/{username}/rss", ua=_SCRAPER_UA, timeout=5
            )
            if entries:
                for e in entries[:3]:
                    title = getattr(e, "title", "")
                    items.append({
                        "title":       title,
                        "source":      display,
                        "url":         getattr(e, "link", "#"),
                        "tags":        _classify_tags(title),
                        "source_type": "social",
                    })
                break  # first working instance is enough
    return items


@st.cache_data(ttl=300, show_spinner=False)
def fetch_news() -> list[dict]:
    items: list[dict] = []
    for feed in NEWS_FEEDS:
        entries = _fetch_feed_safe(
            feed["url"], ua=_SCRAPER_UA if feed["ua"] else None
        )
        for e in entries[:5]:
            title = getattr(e, "title", "")
            items.append({
                "title":       title,
                "source":      feed["name"],
                "url":         getattr(e, "link", "#"),
                "tags":        _classify_tags(title),
                "source_type": feed["type"],
            })
    # X / Twitter via Nitter (best-effort; may return nothing if all instances down)
    items.extend(_fetch_nitter_feeds())
    return items[:50]


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


# ─── MISO: Technical helpers ───────────────────────────────────────────────────
def _calc_rsi(series: pd.Series, period: int = 9) -> Optional[float]:
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


def _calc_bb_pct_b(series: pd.Series, period: int = 20, k: float = 2.0) -> Optional[float]:
    """Bollinger %B = (price − lower) / (upper − lower).  >1 = above upper band."""
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


def _calc_demark(closes: pd.Series) -> tuple[int, int, str]:
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
    """Market Immune System Oscillator — 5 composantes, 100 = plus survendu."""
    import math
    _empty: dict = {
        "composite": None, "status": "N/A", "color": "#64748b",
        "signal": "Données insuffisantes", "emoji": "⚪", "components": [],
    }
    try:
        # TradingView first (tvDatafeed), Yahoo Finance fallback for each series
        spx   = _tv_or_yf_close("^GSPC",  "3mo", 70)
        vix   = _tv_or_yf_close("^VIX",   "3mo", 70)
        nyad  = _tv_or_yf_close("^NYAD",  "3mo", 70)
        vix3m = _tv_or_yf_close("^VIX3M", "3mo", 70)
        if len(vix3m) < 2:
            vix3m = _tv_or_yf_close("^VXMT", "3mo", 70)
    except Exception:
        return _empty

    components: list[dict] = []

    # 1. NYSE Breadth RSI(9) — score = 100 − RSI  (oversold breadth → high score)
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
        vix_last  = float(vix.iloc[-1])
        v3m_last  = float(vix3m.iloc[-1])
        if v3m_last > 0:
            ratio = round(vix_last / v3m_last, 3)
            sc_ts = round(100.0 / (1.0 + math.exp(-4.5 * (ratio - 1.0))), 1)
            components.append({
                "name": "VIX Term Structure", "weight": 20,
                "raw_label": f"VIX/VIX3M = {ratio:.2f}",
                "score": sc_ts,
                "desc": "Backwardation (VIX > VIX3M) → panique",
            })

    # 5. DeMark Sequential — buy setup progress toward 9/9 (then countdown toward 13)
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


# ─── Plotly 1-Year Asset Chart ────────────────────────────────────────────────
def make_asset_chart(ticker: str, name: str) -> go.Figure:
    """Candlestick + volume + MA20/MA50 chart for 1 year of data."""
    hist = fetch_asset_history_1y(ticker)
    if hist.empty:
        return go.Figure()

    has_ohlc   = all(c in hist.columns for c in ("Open", "High", "Low"))
    has_volume = "Volume" in hist.columns and hist["Volume"].sum() > 0
    price_dom  = [0.22, 1.0] if has_volume else [0.0, 1.0]

    fig = go.Figure()

    # ── Price: candlestick or line ───────────────────────────────────────────
    if has_ohlc:
        fig.add_trace(go.Candlestick(
            x=hist.index,
            open=hist["Open"], high=hist["High"],
            low=hist["Low"],   close=hist["Close"],
            name=name,
            increasing_line_color="#22c55e",
            decreasing_line_color="#ef4444",
            increasing_fillcolor="rgba(34,197,94,0.22)",
            decreasing_fillcolor="rgba(239,68,68,0.22)",
            showlegend=False,
        ))
    else:
        fig.add_trace(go.Scatter(
            x=hist.index, y=hist["Close"],
            mode="lines", name=name,
            line=dict(color="#3b82f6", width=2),
            showlegend=False,
        ))

    # ── MA20 ────────────────────────────────────────────────────────────────
    ma20 = hist["Close"].rolling(20).mean()
    fig.add_trace(go.Scatter(
        x=hist.index, y=ma20, name="MA 20",
        line=dict(color="#f59e0b", width=1.5, dash="dot"),
        hovertemplate="%{y:.3f}<extra>MA20</extra>",
    ))

    # ── MA50 ────────────────────────────────────────────────────────────────
    ma50 = hist["Close"].rolling(50).mean()
    fig.add_trace(go.Scatter(
        x=hist.index, y=ma50, name="MA 50",
        line=dict(color="#a78bfa", width=1.5, dash="dot"),
        hovertemplate="%{y:.3f}<extra>MA50</extra>",
    ))

    # ── Volume bars ──────────────────────────────────────────────────────────
    if has_volume:
        open_col = hist["Open"] if has_ohlc else hist["Close"]
        vol_clrs = [
            "rgba(34,197,94,0.35)" if c >= o else "rgba(239,68,68,0.35)"
            for c, o in zip(hist["Close"], open_col)
        ]
        fig.add_trace(go.Bar(
            x=hist.index, y=hist["Volume"],
            marker_color=vol_clrs, yaxis="y2",
            hovertemplate="%{y:,.0f}<extra>Volume</extra>",
            showlegend=False,
        ))

    # ── Layout ──────────────────────────────────────────────────────────────
    layout_kwargs: dict = dict(
        height=400,
        margin=dict(t=35, b=10, l=60, r=20),
        paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
        font={"color": "#94a3b8", "size": 11},
        xaxis=dict(
            showgrid=False, color="#475569",
            rangeslider=dict(visible=False),
            rangeselector=dict(
                buttons=[
                    dict(count=1,  label="1M",  step="month", stepmode="backward"),
                    dict(count=3,  label="3M",  step="month", stepmode="backward"),
                    dict(count=6,  label="6M",  step="month", stepmode="backward"),
                    dict(step="all", label="1A"),
                ],
                bgcolor="#1e293b", activecolor="#334155",
                font=dict(color="#94a3b8", size=11),
            ),
        ),
        yaxis=dict(
            showgrid=True, gridcolor="#1e293b", color="#475569",
            domain=price_dom,
        ),
        showlegend=True,
        legend=dict(
            bgcolor="rgba(0,0,0,0)", font=dict(size=11),
            orientation="h", x=1, xanchor="right", y=1.04,
        ),
        xaxis_rangeslider_visible=False,
    )
    if has_volume:
        layout_kwargs["yaxis2"] = dict(
            showgrid=False, color="#334155",
            domain=[0.0, 0.18],
            tickformat=".2s",
        )

    fig.update_layout(**layout_kwargs)
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


def _heat_label(asset: dict) -> str:
    """Return a short, distinct label for a heatmap tile.

    Priority rules (first match wins):
    1. Explicit ``short`` field on the asset dict
    2. Ticker inside parentheses  – "MSCI EM (EEM)"  → "EEM"
    3. Last word is all-caps 2-4 char ticker (≥3-word name)
                                  – "Long Treasury TLT" → "TLT"
                                  – "High Yield HYG"    → "HYG"
                                  – "IG Credit LQD"     → "LQD"
    4. Short country/index prefix + maturity (next token starts with alnum)
                                  – "US 10Y Yield"  → "US 10Y"
                                  – "CA 2Y Yield"   → "CA 2Y"
                                  – "WTI Oil"        → "WTI Oil"
    5. First word (default)
    """
    if "short" in asset:
        return asset["short"]

    name  = asset["name"]
    words = name.split()

    # Rule 2 – ticker in parentheses
    if "(" in name and ")" in name:
        inner = name[name.index("(") + 1 : name.index(")")]
        if " " not in inner and len(inner) <= 5:
            return inner

    # Rule 3 – last word all-caps short ticker
    if len(words) >= 3 and words[-1].isupper() and 2 <= len(words[-1]) <= 4:
        return words[-1]

    # Rule 4 – country/index prefix  (≤3-char all-caps) + next maturity/word
    if (len(words) >= 2
            and len(words[0]) <= 3
            and words[0].isupper()
            and words[1][0].isalnum()):
        return f"{words[0]} {words[1]}"

    # Rule 5 – default: first word
    return words[0]


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
    miso         = fetch_miso()
    cb_live_rates = fetch_cb_rates()
    period_perf  = fetch_period_performance()
    # Inject CA MTD/YTD into period_perf
    for _tk, _d in ca_yields.items():
        period_perf[_tk] = {"mtd": _d.get("mtd"), "ytd": _d.get("ytd")}

risk = calculate_risk_score(market_data)
now  = datetime.now(ZoneInfo("America/Montreal"))

# ─── Header ───────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown(
        f'<h2 style="margin:0;color:#e2e8f0;font-size:1.4rem;">🌊 Market Turbulence Dashboard</h2>'
        f'<p style="margin:0;color:#64748b;font-size:0.75rem;">Risk-On / Risk-Off Monitor &nbsp;·&nbsp; '
        f'<span class="live-dot"></span> Live &nbsp;·&nbsp; '
        f'Mis à jour {now.strftime("%H:%M:%S")} {now.strftime("%Z")}</p>',
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

# ─── ROW 1b: Market Immune System Oscillator ──────────────────────────────────
st.markdown("")
st.markdown('<div class="section-title">🧬 Market Immune System Oscillator (MISO) — Indicateur de survendu composite</div>', unsafe_allow_html=True)

_MISO_RGB = {
    "#ef4444": "239,68,68", "#f59e0b": "245,158,11", "#94a3b8": "148,163,184",
    "#3b82f6": "59,130,246", "#22c55e": "34,197,94",
}

if miso.get("composite") is not None:
    mc   = miso["composite"]
    clr  = miso["color"]
    rgb  = _MISO_RGB.get(clr, "148,163,184")

    # ── Composite score + status badge
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

    # ── 5 component cards
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
                f'<div style="height:5px;width:{min(sc, 100):.0f}%;background:{bar_clr};'
                f'border-radius:3px;transition:width 0.6s"></div></div>'
                f'<div style="font-size:0.63rem;color:#94a3b8;font-family:monospace;'
                f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{comp["raw_label"]}</div>'
                f'<div style="font-size:0.59rem;color:#475569;margin-top:2px;line-height:1.3">{comp["desc"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── Legend
    st.markdown(
        '<p style="font-size:0.62rem;color:#475569;margin-top:6px">'
        '📊 Score 0–100 · '
        '<span style="color:#ef4444;font-weight:700">100 = plus survendu</span> '
        '(pression max + potentiel de rebond) · '
        '<span style="color:#22c55e;font-weight:700">0 = plus suracheté</span> '
        '(complacence max) · '
        'Pondération: VIX %B 25% · SPX RSI 25% · Breadth 20% · Term Structure 20% · DeMark 10% · '
        'Sources: ^GSPC · ^VIX · ^NYAD · ^VIX3M · DeMark propriétaire simplifié'
        '</p>',
        unsafe_allow_html=True,
    )
else:
    st.caption("⚠️ MISO — données insuffisantes (^NYAD ou ^VIX3M non disponibles via TradingView ni Yahoo Finance)")

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
            short_name = _heat_label(asset)
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
    arrow_color = {"↑": "#ef4444", "↓": "#22c55e", "=": "#94a3b8"}

    cb_html = ""
    cb_display = _build_cb_display(cb_live_rates)
    for cb in cb_display:
        bc = bias_color[cb["bias"]]
        bl = bias_label[cb["bias"]]
        cc = arrow_color[cb["change"]]
        live_badge = (
            '<span style="font-size:0.58rem;color:#22c55e;font-weight:700;margin-left:5px">● LIVE</span>'
            if cb.get("is_live")
            else '<span style="font-size:0.58rem;color:#475569;margin-left:5px">📌</span>'
        )
        cb_html += f"""
        <div class="signal-card" style="margin-bottom:0.3rem">
          <div class="signal-row">
            <span class="sig-name">{cb['flag']} {cb['name']} <span style="color:#64748b;font-weight:400">({cb['bank']})</span>{live_badge}</span>
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

def _num_style(v) -> str:
    """Return inline CSS color+font for a numeric cell."""
    if v is None or not isinstance(v, (int, float)) or v != v:
        return "color:#94a3b8;font-family:monospace"
    if v > 0:
        return "color:#22c55e;font-weight:700;font-family:monospace"
    if v < 0:
        return "color:#ef4444;font-weight:700;font-family:monospace"
    return "color:#94a3b8;font-family:monospace"

def _sig_style(sig: str) -> str:
    if "▲" in sig: return "color:#22c55e;font-weight:600"
    if "▼" in sig: return "color:#ef4444;font-weight:600"
    return "color:#94a3b8"

tbl_rows = ""
for _, row in df.iterrows():
    prix_str = fmt_price(row["Prix"], 2) if row["Prix"] else "—"
    tbl_rows += (
        f'<tr>'
        f'<td style="font-weight:600;color:#e2e8f0">{row["Actif"]}</td>'
        f'<td><span style="font-size:0.6rem;background:#0f172a;border:1px solid #334155;'
        f'padding:1px 6px;border-radius:4px;color:#64748b">{row["Groupe"]}</span></td>'
        f'<td style="font-family:monospace;color:#475569;font-size:0.72rem">{row["Ticker"]}</td>'
        f'<td style="font-family:monospace;color:#cbd5e1">{prix_str}</td>'
        f'<td style="{_num_style(row["Jour"])}">{fmt_val(row["Jour"])}</td>'
        f'<td style="{_num_style(row["MTD"])}">{fmt_val(row["MTD"])}</td>'
        f'<td style="{_num_style(row["YTD"])}">{fmt_val(row["YTD"])}</td>'
        f'<td style="{_sig_style(str(row["Signal"]))}">{row["Signal"]}</td>'
        f'</tr>'
    )

st.markdown(f"""
<style>
  .mkt-tbl {{ width:100%; border-collapse:collapse; font-size:0.78rem; }}
  .mkt-tbl th {{
    background:#1e293b; color:#64748b; font-weight:700; text-align:left;
    padding:8px 10px; border-bottom:2px solid #334155;
    font-size:0.64rem; text-transform:uppercase; letter-spacing:0.07em;
    position:sticky; top:0; z-index:1;
  }}
  .mkt-tbl td {{ padding:5px 10px; border-bottom:1px solid #1e293b; }}
  .mkt-tbl tr:hover td {{ background:rgba(255,255,255,0.04); }}
</style>
<div style="overflow-x:auto;max-height:540px;overflow-y:auto;
            border:1px solid #334155;border-radius:8px;background:#0f172a">
  <table class="mkt-tbl">
    <thead><tr>
      <th>Actif</th><th>Groupe</th><th>Ticker</th>
      <th>Prix</th><th>Jour %</th><th>MTD&nbsp;(%&nbsp;/&nbsp;pp)</th>
      <th>YTD&nbsp;(%&nbsp;/&nbsp;pp)</th><th>Signal</th>
    </tr></thead>
    <tbody>{tbl_rows}</tbody>
  </table>
</div>
""", unsafe_allow_html=True)

# ─── ROW 3b: 1-Year Asset Chart ───────────────────────────────────────────────
st.markdown("")
st.markdown('<div class="section-title">📊 Graphique historique — Cliquez sur un actif</div>', unsafe_allow_html=True)

# Build selector list from currently displayed rows
_chart_opts = [
    (f"{row['Actif']}  ({row['Ticker']})", row["Ticker"], row["Actif"])
    for _, row in df.iterrows()
    if row.get("Prix") is not None
]

if _chart_opts:
    # ── Selector + quick stats ───────────────────────────────────────────────
    _csel_col, _cinfo_col = st.columns([2, 3])

    with _csel_col:
        _chart_sel_label = st.selectbox(
            "Actif à afficher :",
            [o[0] for o in _chart_opts],
            key="chart_asset_sel",
        )

    _sel_map    = {o[0]: (o[1], o[2]) for o in _chart_opts}
    _sel_ticker, _sel_name = _sel_map.get(_chart_sel_label, (_chart_opts[0][1], _chart_opts[0][2]))
    _td_sel  = market_data.get(_sel_ticker, {})
    _pp_sel  = period_perf.get(_sel_ticker, {})
    _pr_sel  = _td_sel.get("price")
    _pct_sel = _td_sel.get("change_pct")
    _ytd_sel = _pp_sel.get("ytd")
    _mtd_sel = _pp_sel.get("mtd")
    _c_day   = "#22c55e" if (_pct_sel or 0) > 0 else "#ef4444" if (_pct_sel or 0) < 0 else "#94a3b8"
    _c_mtd   = "#22c55e" if (_mtd_sel or 0) > 0 else "#ef4444" if (_mtd_sel or 0) < 0 else "#94a3b8"
    _c_ytd   = "#22c55e" if (_ytd_sel or 0) > 0 else "#ef4444" if (_ytd_sel or 0) < 0 else "#94a3b8"

    with _cinfo_col:
        st.markdown(
            f'<div style="display:flex;gap:24px;align-items:flex-end;padding:6px 0 4px">'
            f'<div><div style="font-size:0.62rem;color:#64748b;margin-bottom:2px">Prix</div>'
            f'<div style="font-size:1.15rem;font-weight:800;font-family:monospace;color:#e2e8f0">'
            f'{fmt_price(_pr_sel) if _pr_sel else "—"}</div></div>'
            f'<div><div style="font-size:0.62rem;color:#64748b;margin-bottom:2px">Jour</div>'
            f'<div style="font-size:1rem;font-weight:700;font-family:monospace;color:{_c_day}">'
            f'{fmt_pct(_pct_sel)}</div></div>'
            f'<div><div style="font-size:0.62rem;color:#64748b;margin-bottom:2px">MTD</div>'
            f'<div style="font-size:1rem;font-weight:700;font-family:monospace;color:{_c_mtd}">'
            f'{fmt_val(_mtd_sel)}</div></div>'
            f'<div><div style="font-size:0.62rem;color:#64748b;margin-bottom:2px">YTD</div>'
            f'<div style="font-size:1rem;font-weight:700;font-family:monospace;color:{_c_ytd}">'
            f'{fmt_val(_ytd_sel)}</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Chart ────────────────────────────────────────────────────────────────
    _fig_asset = make_asset_chart(_sel_ticker, _sel_name)
    if _fig_asset.data:
        st.plotly_chart(
            _fig_asset, use_container_width=True,
            config={"displayModeBar": True, "modeBarButtonsToRemove": ["lasso2d", "select2d"]},
        )
    else:
        st.info(f"Données historiques non disponibles pour {_sel_name} ({_sel_ticker})", icon="⚠️")
else:
    st.caption("Aucun actif disponible dans le groupe sélectionné.")

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

nf1, nf2 = st.columns([1.3, 2])
with nf1:
    src_filter = st.radio(
        "Source:",
        ["Toutes", "Wire", "Médias", "Reddit", "Newsletter", "X"],
        horizontal=True, key="src_filter",
    )
with nf2:
    tag_filter = st.radio(
        "Thème:",
        ["Tous", "Géopolitique", "Économie", "Marchés"],
        horizontal=True, key="news_filter",
    )

src_type_map  = {"Wire": "wire", "Médias": "media", "Reddit": "reddit",
                 "Newsletter": "newsletter", "X": "social"}
tag_map       = {"Géopolitique": "geo", "Économie": "eco", "Marchés": "mkt"}
src_filtered  = (news_items if src_filter == "Toutes"
                 else [n for n in news_items if n.get("source_type") == src_type_map.get(src_filter)])
filtered_news = (src_filtered if tag_filter == "Tous"
                 else [n for n in src_filtered if tag_map.get(tag_filter, "") in n.get("tags", [])])

tag_html_map = {
    "geo": '<span class="news-tag tag-geo">Géopolitique</span>',
    "eco": '<span class="news-tag tag-eco">Économie</span>',
    "mkt": '<span class="news-tag tag-mkt">Marchés</span>',
}
src_badge_map = {
    "wire":       '<span class="news-tag" style="background:rgba(59,130,246,0.1);color:#60a5fa;border:1px solid rgba(59,130,246,0.2)">Wire</span>',
    "media":      '<span class="news-tag" style="background:rgba(139,92,246,0.1);color:#a78bfa;border:1px solid rgba(139,92,246,0.2)">Médias</span>',
    "reddit":     '<span class="news-tag" style="background:rgba(249,115,22,0.1);color:#fb923c;border:1px solid rgba(249,115,22,0.2)">Reddit</span>',
    "newsletter": '<span class="news-tag" style="background:rgba(16,185,129,0.1);color:#34d399;border:1px solid rgba(16,185,129,0.2)">Newsletter</span>',
    "social":     '<span class="news-tag" style="background:rgba(14,165,233,0.1);color:#38bdf8;border:1px solid rgba(14,165,233,0.2)">X</span>',
}

nc1, nc2, nc3 = st.columns(3)
cols_cycle = [nc1, nc2, nc3]
for i, item in enumerate(filtered_news[:24]):
    tags_html  = "".join(tag_html_map.get(t, "") for t in item.get("tags", []))
    src_badge  = src_badge_map.get(item.get("source_type", ""), "")
    with cols_cycle[i % 3]:
        st.markdown(
            f'<a href="{item["url"]}" target="_blank" style="text-decoration:none">'
            f'<div class="news-card">'
            f'<div class="news-title">{item["title"]}</div>'
            f'<div class="news-meta"><span style="color:#3b82f6">{item["source"]}</span>'
            f' {src_badge} {tags_html}</div>'
            f'</div></a>',
            unsafe_allow_html=True,
        )

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<p style="font-size:0.65rem;color:#475569;text-align:center">'
    'Données: TradingView (primaire) · Yahoo Finance (fallback) · Actualités: Reuters, AP, CNBC, Bloomberg/GN · '
    'Reddit (r/investing, r/wallstreetbets, r/economics, r/geopolitics, r/stocks, r/worldnews, r/CanadianInvestor) · '
    'Substack (Apricitas, Chartbook, Noahpinion, No Mercy/No Malice) · Calculated Risk · X via Nitter · '
    'Actualisation automatique toutes les 60 secondes · '
    'Score Risk-On/Off: modèle composite 7 signaux pondérés · '
    'À des fins informatives uniquement — pas un conseil en investissement.'
    '</p>',
    unsafe_allow_html=True,
)
