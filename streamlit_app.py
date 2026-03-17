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
    {"group": "Commodities", "name": "Silver",              "ticker": "SI=F",      "type": "commodity"},
    {"group": "Currencies",  "name": "DXY (USD Index)",     "ticker": "DX-Y.NYB",  "type": "currency"},
    {"group": "Currencies",  "name": "EUR/USD",             "ticker": "EURUSD=X",  "type": "currency"},
    {"group": "Currencies",  "name": "USD/JPY",             "ticker": "JPY=X",     "type": "currency"},
    {"group": "Currencies",  "name": "USD/CHF",             "ticker": "CHFUSD=X",  "type": "currency"},
    {"group": "Currencies",  "name": "USD/CAD",             "ticker": "USDCAD=X",  "type": "currency"},
    {"group": "Crypto",      "name": "Bitcoin",             "ticker": "BTC-USD",   "type": "crypto"},
    {"group": "Crypto",      "name": "Ethereum",            "ticker": "ETH-USD",   "type": "crypto"},
    {"group": "Volatility",  "name": "VIX",                 "ticker": "^VIX",      "type": "volatility"},
    {"group": "Risk Proxies","name": "S&P 500 ETF (SPY)",   "ticker": "SPY",       "type": "etf"},
]

NEWS_FEEDS = [
    ("Reuters Top",      "https://feeds.reuters.com/reuters/topNews"),
    ("Reuters Biz",      "https://feeds.reuters.com/reuters/businessNews"),
    ("AP Top News",      "https://apnews.com/rss"),
    ("CNBC Markets",     "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"),
    ("Bloomberg/GN",     "https://news.google.com/rss/search?q=bloomberg+finance+market&hl=en-US&gl=US&ceid=US:en"),
    ("r/investing",      "https://www.reddit.com/r/investing/.rss"),
    ("r/wallstreetbets", "https://www.reddit.com/r/wallstreetbets/.rss"),
    ("r/economics",      "https://www.reddit.com/r/economics/.rss"),
    ("r/geopolitics",    "https://www.reddit.com/r/geopolitics/.rss"),
]
_REDDIT_UA = "Mozilla/5.0 (compatible; market-dashboard/1.0)"
_FEEDS_WITH_UA = {"r/investing", "r/wallstreetbets", "r/economics", "r/geopolitics"}

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
    today = datetime.now(timezone.utc).date()
    year_start = today.replace(month=1, day=1).isoformat()
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
                result[ticker] = {"price": None, "change": None, "change_pct": None, "timestamp": None}
                continue
            latest = float(obs[-1][series]["v"])
            change = change_pct = None
            if len(obs) >= 2:
                prev = float(obs[-2][series]["v"])
                change = round(latest - prev, 3)
                change_pct = round((change / prev) * 100, 2) if prev else None
            result[ticker] = {"price": round(latest, 3), "change": change,
                               "change_pct": change_pct, "timestamp": obs[-1]["d"]}
        except Exception as e:
            logger.warning(f"BOC {series}: {e}")
            result[ticker] = {"price": None, "change": None, "change_pct": None, "timestamp": None}
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
    for source, url in NEWS_FEEDS:
        try:
            headers = {"User-Agent": _REDDIT_UA} if source in _FEEDS_WITH_UA else {}
            feed = feedparser.parse(url, request_headers=headers)
            for entry in feed.entries[:6]:
                title   = getattr(entry, "title", "")
                link    = getattr(entry, "link", "#")
                summary = getattr(entry, "summary", getattr(entry, "description", ""))
                tl = title.lower(); tags = []
                if any(w in tl for w in ["war","conflict","attack","strike","military","nuclear",
                                          "sanctions","nato","ukraine","russia","china","taiwan",
                                          "iran","israel","hamas"]): tags.append("geopolitical")
                if any(w in tl for w in ["inflation","rate","fed","ecb","boj","central bank",
                                          "gdp","jobs","recession","cpi","ppi","fomc"]): tags.append("economic")
                if any(w in tl for w in ["market","stock","equity","bond","gold","oil","crypto",
                                          "bitcoin","rally","sell-off","crash"]): tags.append("market")
                all_items.append({"title": title, "source": source, "url": link,
                                   "published": getattr(entry, "published", ""),
                                   "summary": (summary[:180] + "...") if len(summary) > 180 else summary,
                                   "tags": tags})
        except Exception as e:
            logger.warning(f"Feed {source}: {e}")
    return all_items[:24]


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


@st.cache_data(ttl=60, show_spinner="Chargement des données de marché…")
def _full_data():
    mkt  = _market_data_cached()
    ca   = _ca_yields_cached()
    mkt  = {**mkt, **ca}
    risk = _risk_score(mkt)
    today = datetime.now(timezone.utc).date()
    assets = [
        {**a,
         "price":      mkt.get(a["ticker"], {}).get("price"),
         "change":     mkt.get(a["ticker"], {}).get("change"),
         "change_pct": mkt.get(a["ticker"], {}).get("change_pct"),
         "timestamp":  mkt.get(a["ticker"], {}).get("timestamp")}
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

tab1, tab2 = st.tabs(["📊 Market Turbulence Dashboard", "🏦 Fondaction Snapshot"])

with tab1:
    data = _full_data()
    vix  = _vix_history_cached()
    html = (TEMPLATE_DIR / "index.html").read_text(encoding="utf-8")
    inject = (
        f'<script>'
        f'window.__PRELOAD__={json.dumps(data, default=str)};'
        f'window.__VIX_PRELOAD__={json.dumps(vix)};'
        f'</script>'
    )
    html = html.replace("</head>", inject + "</head>")
    components.html(html, height=950, scrolling=True)

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
