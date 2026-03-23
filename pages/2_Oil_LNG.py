"""
Oil & LNG Ecosystem Dashboard — Streamlit Page
Real-time energy market data: crude oil, natural gas, LNG, energy equities.
Deploy on Streamlit Community Cloud: https://share.streamlit.io
"""
from __future__ import annotations
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

try:
    import feedparser
    import yfinance as yf
except ImportError:
    st.error("Missing dependencies. Run: pip install yfinance feedparser")
    st.stop()

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

BASE         = Path(__file__).parent.parent
TEMPLATE_DIR = BASE / "templates"

# ── Oil & LNG Assets ─────────────────────────────────────────────────────────
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
    "report_date":    "2026-03-19",
    "crude_oil":      {"value": 437.2, "change": -2.1, "unit": "MMbbl", "label": "Crude Oil"},
    "gasoline":       {"value": 241.5, "change": +1.3, "unit": "MMbbl", "label": "Gasoline"},
    "distillates":    {"value": 117.8, "change": -0.8, "unit": "MMbbl", "label": "Distillates"},
    "cushing":        {"value":  26.4, "change": -1.2, "unit": "MMbbl", "label": "Cushing, OK"},
    "spr":            {"value": 395.2, "change":  0.0, "unit": "MMbbl", "label": "SPR"},
    "refinery_util":  {"value":  87.3, "change": +0.6, "unit": "%",     "label": "Refinery Util."},
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
    {"region": "Middle East",    "title": "Strait of Hormuz",       "level": "high",   "icon": "ship",           "description": "~20% of global oil & LNG transits this chokepoint daily. Iran tensions remain elevated.", "market_impact": "+$8-15/bbl if closure risk escalates"},
    {"region": "Russia / Europe","title": "Russian Gas Supply",     "level": "high",   "icon": "flame",          "description": "Nord Stream offline; remaining pipeline routes uncertain. European LNG imports at record highs.", "market_impact": "Persistent EU LNG premium vs US Henry Hub"},
    {"region": "US Gulf Coast",  "title": "LNG Export Expansion",   "level": "medium", "icon": "anchor",         "description": "Sabine Pass T6, Corpus Christi T3, Plaquemines LNG underway. US market share rising globally.", "market_impact": "Structurally bullish Henry Hub long-term demand"},
    {"region": "Libya / Nigeria","title": "African Supply Disruptions","level": "medium","icon": "alert-triangle","description": "Periodic production outages from political instability and pipeline sabotage.", "market_impact": "+$2-5/bbl on major disruption events"},
    {"region": "South America",  "title": "Venezuela / Guyana",     "level": "low",    "icon": "trending-up",    "description": "Guyana ramp-up is bullish for Atlantic basin supply. Venezuela sanctions cap output.", "market_impact": "Net neutral; Guyana growth offsets Venezuela shortfall"},
]

ENERGY_NEWS_FEEDS = [
    ("EIA Today",   "https://www.eia.gov/rss/todayinenergy.xml"),
    ("Reuters Biz", "https://feeds.reuters.com/reuters/businessNews"),
    ("Oil/LNG",     "https://news.google.com/rss/search?q=oil+LNG+OPEC+crude+natural+gas&hl=en-US&gl=US&ceid=US:en"),
    ("Energy Mkts", "https://news.google.com/rss/search?q=energy+market+petroleum+refinery+gasoline&hl=en-US&gl=US&ceid=US:en"),
]


# ── Data helpers ──────────────────────────────────────────────────────────────
def _fetch_one(ticker: str) -> tuple[str, dict]:
    try:
        hist = yf.Ticker(ticker).history(period="5d", auto_adjust=True).dropna(subset=["Close"])
        if len(hist) >= 2:
            c, p = float(hist["Close"].iloc[-1]), float(hist["Close"].iloc[-2])
            ch   = c - p
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
def _oil_data_cached() -> dict:
    tickers = list({a["ticker"] for a in OIL_LNG_ASSETS})
    result  = {}
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
def _oil_history_cached() -> dict:
    result  = {"wti": [], "brent": [], "gas": []}
    mapping = {"wti": "CL=F", "brent": "BZ=F", "gas": "NG=F"}
    for key, ticker in mapping.items():
        try:
            hist = yf.Ticker(ticker).history(period="90d", auto_adjust=True).dropna(subset=["Close"])
            result[key] = [
                {"date": str(idx.date()), "value": round(float(row["Close"]), 3)}
                for idx, row in hist.iterrows()
            ]
        except Exception as e:
            logger.error(f"Oil history {ticker}: {e}")
    return result


@st.cache_data(ttl=300, show_spinner=False)
def _energy_news_cached(max_items: int = 20) -> list[dict]:
    all_items: list = []
    seen: set = set()
    for source, url in ENERGY_NEWS_FEEDS:
        try:
            feed  = feedparser.parse(url)
            count = 0
            for entry in feed.entries:
                if count >= 5:
                    break
                title   = getattr(entry, "title", "").strip()
                link    = getattr(entry, "link", "#")
                summary = getattr(entry, "summary", getattr(entry, "description", ""))
                key     = title.lower()[:80]
                if not title or key in seen:
                    continue
                seen.add(key)
                tl   = title.lower()
                tags = []
                if any(w in tl for w in ["opec", "saudi", "aramco", "quota", "cut"]):
                    tags.append("opec")
                if any(w in tl for w in ["lng", "liquefied", "natural gas", "henry hub", "ttf"]):
                    tags.append("lng")
                if any(w in tl for w in ["eia", "inventory", "stockpile", "supply", "demand"]):
                    tags.append("supply")
                if any(w in tl for w in ["refin", "crack", "gasoline", "distillate", "diesel"]):
                    tags.append("refining")
                if any(w in tl for w in ["wti", "brent", "crude", "oil price", "barrel"]):
                    tags.append("crude")
                all_items.append({
                    "title":     title,
                    "source":    source,
                    "url":       link,
                    "published": getattr(entry, "published", ""),
                    "summary":   (summary[:180] + "...") if len(summary) > 180 else summary,
                    "tags":      tags,
                })
                count += 1
        except Exception as e:
            logger.warning(f"Energy feed {source}: {e}")
    return all_items[:max_items]


def _calculate_energy_score(oil_data: dict) -> dict:
    signals: list = []
    ws = 0.0
    tw = 0.0

    def add(name, value, unit, score, label, status, weight, desc):
        nonlocal ws, tw
        signals.append({"name": name, "value": value, "unit": unit,
                         "score": round(float(score), 1), "label": label,
                         "status": status, "weight": weight, "description": desc})
        ws += float(score) * weight
        tw += weight

    wti_pct = oil_data.get("CL=F", {}).get("change_pct")
    if wti_pct is not None:
        sc  = max(0.0, min(100.0, 50.0 + wti_pct * 8.0))
        lbl = "WTI Rising" if sc > 60 else ("WTI Falling" if sc < 40 else "WTI Stable")
        st_ = "bullish"   if sc > 60 else ("bearish"     if sc < 40 else "neutral")
        add("WTI Crude Oil", wti_pct, "%", sc, lbl, st_, 20, "WTI benchmark direction")

    brent_pct = oil_data.get("BZ=F", {}).get("change_pct")
    if brent_pct is not None:
        sc  = max(0.0, min(100.0, 50.0 + brent_pct * 8.0))
        lbl = "Brent Rising" if sc > 60 else ("Brent Falling" if sc < 40 else "Brent Stable")
        st_ = "bullish"      if sc > 60 else ("bearish"       if sc < 40 else "neutral")
        add("Brent Crude", brent_pct, "%", sc, lbl, st_, 15, "Brent global benchmark")

    ng_pct = oil_data.get("NG=F", {}).get("change_pct")
    if ng_pct is not None:
        sc  = max(0.0, min(100.0, 50.0 + ng_pct * 7.0))
        lbl = "Gas Rising" if sc > 60 else ("Gas Falling" if sc < 40 else "Gas Stable")
        st_ = "bullish"    if sc > 60 else ("bearish"     if sc < 40 else "neutral")
        add("Henry Hub Nat. Gas", ng_pct, "%", sc, lbl, st_, 15, "US natural gas benchmark")

    xle_pct = oil_data.get("XLE", {}).get("change_pct")
    if xle_pct is not None:
        sc  = max(0.0, min(100.0, 50.0 + xle_pct * 9.0))
        lbl = "Energy Strong" if sc > 60 else ("Energy Weak" if sc < 40 else "Energy Neutral")
        st_ = "bullish"       if sc > 60 else ("bearish"     if sc < 40 else "neutral")
        add("Energy Sector (XLE)", xle_pct, "%", sc, lbl, st_, 15, "Broad energy equity sentiment")

    spy_pct = oil_data.get("SPY", {}).get("change_pct")
    if xle_pct is not None and spy_pct is not None:
        rel = xle_pct - spy_pct
        sc  = max(0.0, min(100.0, 50.0 + rel * 15.0))
        lbl = "Energy Outperforming" if sc > 60 else ("Energy Underperforming" if sc < 40 else "Energy In-Line")
        st_ = "bullish"              if sc > 60 else ("bearish"                if sc < 40 else "neutral")
        add("Energy vs Market (XLE/SPY)", round(rel, 2), "% rel.", sc, lbl, st_, 20, "Sector rotation signal")

    rbob_pct = oil_data.get("RB=F", {}).get("change_pct")
    if rbob_pct is not None and wti_pct is not None:
        crack = rbob_pct - wti_pct
        sc    = max(0.0, min(100.0, 50.0 + crack * 12.0))
        lbl   = "Crack Widening" if sc > 60 else ("Crack Narrowing" if sc < 40 else "Crack Stable")
        st_   = "bullish"        if sc > 60 else ("bearish"         if sc < 40 else "neutral")
        add("Crack Spread (RBOB/WTI)", round(crack, 2), "% rel.", sc, lbl, st_, 15, "Refinery margin proxy")

    composite = round(ws / tw, 1) if tw > 0 else 50.0
    if   composite >= 70: label, color, desc = "BULLISH",            "green", "Strong energy market momentum. Oil prices rising, sector outperforming."
    elif composite >= 58: label, color, desc = "MODERATELY BULLISH", "green", "Positive energy market bias. Favorable conditions for oil & gas producers."
    elif composite >= 42: label, color, desc = "NEUTRAL",            "amber", "Mixed energy signals. Range-bound oil prices, balanced supply/demand."
    elif composite >= 30: label, color, desc = "MODERATELY BEARISH", "red",   "Weak energy conditions. Demand concerns or oversupply pressures building."
    else:                 label, color, desc = "BEARISH",            "red",   "Energy sector under significant pressure. Price decline risk elevated."
    return {"score": composite, "label": label, "color": color, "description": desc, "signals": signals}


@st.cache_data(ttl=60, show_spinner="Loading energy market data...")
def _full_oil_data() -> dict:
    # Also fetch SPY to compute XLE/SPY relative
    oil_tickers = list({a["ticker"] for a in OIL_LNG_ASSETS}) + ["SPY"]
    raw: dict   = {}
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {ex.submit(_fetch_one, t): t for t in oil_tickers}
        for f in as_completed(futures, timeout=30):
            try:
                ticker, data = f.result()
                raw[ticker]  = data
            except Exception as e:
                logger.warning(f"Future: {e}")

    energy_score = _calculate_energy_score(raw)
    assets = [
        {**a,
         "price":      raw.get(a["ticker"], {}).get("price"),
         "change":     raw.get(a["ticker"], {}).get("change"),
         "change_pct": raw.get(a["ticker"], {}).get("change_pct"),
         "timestamp":  raw.get(a["ticker"], {}).get("timestamp")}
        for a in OIL_LNG_ASSETS
    ]
    return {
        "energy_score": energy_score,
        "assets":       assets,
        "eia":          EIA_INVENTORY,
        "opec":         OPEC_DATA,
        "geo_risks":    ENERGY_GEO_RISKS,
        "news":         _energy_news_cached(),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Oil & LNG Ecosystem Dashboard",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
[data-testid="stAppViewContainer"] { background: #0B1120; }
</style>
""", unsafe_allow_html=True)

# ── Fetch data ────────────────────────────────────────────────────────────────
data    = _full_oil_data()
history = _oil_history_cached()

# ── Load & inject template ───────────────────────────────────────────────────
html = (TEMPLATE_DIR / "oil_lng.html").read_text(encoding="utf-8")

inject = (
    "<script>"
    f"window.__OIL_PRELOAD__={json.dumps(data, default=str)};"
    f"window.__OIL_HISTORY_PRELOAD__={json.dumps(history)};"
    "</script>"
)
html = html.replace("</head>", inject + "</head>")

components.html(html, height=1400, scrolling=True)
