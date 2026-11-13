"""
Rebuild data/fondaction_snapshot.json from free public sources.

Replaces the Bloomberg-linked workbook (Tableau_Bord_Fondaction_Bloomberg.xlsx):
same indicators, same Vert/Jaune/Rouge rules, same scoring
(score = (verts + 0.5 x jaunes) / total, global = average of the 4 categories).

Sources: FRED (St. Louis Fed), Yahoo Finance (yfinance), Bank of Canada Valet,
Statistics Canada WDS. Indicators without a free source are read from
data/snapshot_manual.json (edit that file to update them).

If a source fails, the indicator keeps its previous value from the existing JSON
and is flagged as not refreshed — the run never wipes data.

Run:  python scripts/update_snapshot.py
"""
from __future__ import annotations

import io
import json
import logging
import math
import os
import sys
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "fondaction_snapshot.json"
MANUAL = ROOT / "data" / "snapshot_manual.json"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("snapshot")
UA = {"User-Agent": "Mozilla/5.0 (market-dashboard snapshot updater)"}
TODAY = date.today()


# ── Fetch helpers ─────────────────────────────────────────────────────────────
def _get(url: str, data: bytes | None = None, headers: dict | None = None, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


_fred_cache: dict[str, pd.Series] = {}

# fred.stlouisfed.org refuses connections from GitHub-hosted runners; the official
# API (api.stlouisfed.org) works with a free key stored as the FRED_API_KEY secret.
# Without a key, a few series fall back to keyless official sources (BLS, Treasury).
FRED_API_KEY = os.environ.get("FRED_API_KEY", "").strip()

BLS_IDS = {  # FRED id -> BLS series id (BLS public API v1, no key)
    "UNRATE": "LNS14000000", "U6RATE": "LNS13327709", "PAYEMS": "CES0000000001",
    "CES0500000003": "CES0500000003", "JTSJOL": "JTS000000000000000JOL", "CPILFESL": "CUSR0000SA0L1E",
}
TREASURY = {  # FRED id -> (Treasury curve type, column)
    "DGS10": ("daily_treasury_yield_curve", "10 Yr"), "DGS2": ("daily_treasury_yield_curve", "2 Yr"),
    "DFII10": ("daily_treasury_real_yield_curve", "10 YR"),
}


def _fred_api(series_id: str) -> pd.Series:
    url = ("https://api.stlouisfed.org/fred/series/observations?file_type=json&observation_start=2015-01-01"
           f"&series_id={series_id}&api_key={FRED_API_KEY}")
    obs = json.loads(_get(url))["observations"]
    return pd.Series({pd.Timestamp(o["date"]): pd.to_numeric(o["value"], errors="coerce") for o in obs}).dropna()


def _fred_csv(series_id: str) -> pd.Series:
    raw = _get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}", timeout=15)
    df = pd.read_csv(io.BytesIO(raw))
    s = pd.to_numeric(df.iloc[:, 1], errors="coerce")
    s.index = pd.to_datetime(df.iloc[:, 0])
    return s.dropna()


_bls_cache: dict[str, pd.Series] = {}


def _bls(series_id: str) -> pd.Series:
    if not _bls_cache:
        body = json.dumps({"seriesid": list(BLS_IDS.values()), "startyear": str(TODAY.year - 2),
                           "endyear": str(TODAY.year)}).encode()
        j = json.loads(_get("https://api.bls.gov/publicAPI/v1/timeseries/data/", data=body,
                            headers={"Content-Type": "application/json"}))
        for ser in j["Results"]["series"]:
            pts = {pd.Timestamp(int(d["year"]), int(d["period"][1:]), 1): pd.to_numeric(d["value"], errors="coerce")
                   for d in ser["data"] if d["period"].startswith("M") and d["period"] != "M13"}
            _bls_cache[ser["seriesID"]] = pd.Series(pts, dtype=float).dropna().sort_index()
    return _bls_cache[series_id]


def _treasury(kind: str, col: str) -> pd.Series:
    frames = []
    for y in (TODAY.year - 1, TODAY.year):
        url = ("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
               f"daily-treasury-rates.csv/{y}/all?type={kind}&field_tdr_date_value={y}&page&_format=csv")
        frames.append(pd.read_csv(io.BytesIO(_get(url))))
    df = pd.concat(frames)
    cols = {c.lower(): c for c in df.columns}
    s = pd.to_numeric(df[cols[col.lower()]], errors="coerce")
    s.index = pd.to_datetime(df["Date"])
    return s.dropna().sort_index()


def fred(series_id: str) -> pd.Series:
    """Full history of a FRED series, with keyless fallbacks for a few series."""
    if series_id in _fred_cache:
        return _fred_cache[series_id]
    errors = []
    attempts = []
    if FRED_API_KEY:
        attempts.append(("FRED API", lambda: _fred_api(series_id)))
    if series_id in BLS_IDS:
        attempts.append(("BLS", lambda: _bls(BLS_IDS[series_id])))
    if series_id in TREASURY:
        attempts.append(("Treasury", lambda: _treasury(*TREASURY[series_id])))
    if series_id == "T10Y2Y":
        attempts.append(("Treasury", lambda: (_treasury(*TREASURY["DGS10"]) - _treasury(*TREASURY["DGS2"])).dropna()))
    if not FRED_API_KEY:
        attempts.append(("FRED csv", lambda: _fred_csv(series_id)))
    for name, fn in attempts:
        try:
            s = fn()
            if len(s):
                _fred_cache[series_id] = s
                return s
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{name}: {exc}")
    raise RuntimeError(f"{series_id} indisponible ({'; '.join(errors) or 'aucune source'})")


_boc_cache: dict[str, pd.Series] = {}


def boc(series: str) -> pd.Series:
    """Bank of Canada Valet series (last ~2 years)."""
    if series not in _boc_cache:
        j = json.loads(_get(f"https://www.bankofcanada.ca/valet/observations/{series}/json?recent=520"))
        obs = [(o["d"], o.get(series, {}).get("v")) for o in j["observations"]]
        s = pd.Series({pd.Timestamp(d): float(v) for d, v in obs if v not in (None, "")}).sort_index()
        _boc_cache[series] = s
    return _boc_cache[series]


_sc_cache: dict[int, pd.Series] = {}


def statcan(vector: int, n: int = 30) -> pd.Series:
    """Statistics Canada vector (latest n periods)."""
    if vector not in _sc_cache:
        body = json.dumps([{"vectorId": vector, "latestN": n}]).encode()
        j = json.loads(_get(
            "https://www150.statcan.gc.ca/t1/wds/rest/getDataFromVectorsAndLatestNPeriods",
            data=body, headers={"Content-Type": "application/json"}))
        pts = j[0]["object"]["vectorDataPoint"]
        s = pd.Series({pd.Timestamp(p["refPer"]): float(p["value"]) for p in pts if p.get("value") is not None})
        _sc_cache[vector] = s.sort_index()
    return _sc_cache[vector]


YAHOO_TICKERS = [
    "^GSPC", "^RUT", "^VIX", "^SOX", "^GSPTSE", "DX-Y.NYB", "CNY=X", "CAD=X", "BZ=F", "NG=F", "HG=F", "SI=F",
    "ZQ=F", "SPY", "RSP", "IWM", "IVE", "EEM", "DBC", "EMB", "XLU", "XLI", "XBI", "IBB", "WCLD", "PICK",
    "AMZN", "GOOG", "MSFT", "META", "VRT", "PWR", "EQIX", "NVDA", "XRE.TO", "ZEB.TO", "XEG.TO", "XMA.TO",
]
_px: pd.DataFrame | None = None


def px() -> pd.DataFrame:
    """Adjusted daily closes for all Yahoo tickers (one batched download)."""
    global _px
    if _px is None:
        import yfinance as yf
        start = date(TODAY.year - 2, 1, 1).isoformat()
        df = yf.download(YAHOO_TICKERS, start=start, auto_adjust=True, progress=False, threads=True)
        _px = df["Close"].ffill()
    return _px


def ycol(t: str) -> pd.Series:
    s = px()[t].dropna()
    if s.empty:
        raise ValueError(f"no Yahoo data for {t}")
    return s


def last(s: pd.Series) -> float:
    return float(s.dropna().iloc[-1])


def ytd(t: str) -> float:
    s = ycol(t)
    base = s[s.index < pd.Timestamp(TODAY.year, 1, 1)]
    return (last(s) / float(base.iloc[-1]) - 1) * 100


def chg_1m(t: str) -> float:
    s = ycol(t)
    return (last(s) / float(s.iloc[-22]) - 1) * 100


def chg_1y(t: str) -> float:
    s = ycol(t)
    return (last(s) / float(s.iloc[-253]) - 1) * 100


def rsi(s: pd.Series, n: int) -> float:
    d = s.diff().dropna()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return float(100 - 100 / (1 + up.iloc[-1] / dn.iloc[-1]))


def trend_of(series: pd.Series | None) -> str:
    """↑ / ↓ / → comparing the latest observation with the previous one
    (about 1 month back for daily data)."""
    if series is None or len(series.dropna()) < 2:
        return "→"
    s = series.dropna()
    step = 21 if (s.index[-1] - s.index[-2]).days <= 4 else 1
    if len(s) <= step:
        return "→"
    a, b = float(s.iloc[-1]), float(s.iloc[-1 - step])
    return "↑" if a > b else "↓" if a < b else "→"


def asof(s: pd.Series) -> str:
    return s.dropna().index[-1].date().isoformat()


# ── Signal rules (identical to the workbook formulas) ─────────────────────────
def hi(v, green, yellow):
    """Vert if v > green, Jaune if v >= yellow, else Rouge."""
    return "Vert" if v > green else "Jaune" if v >= yellow else "Rouge"


def lo(v, green, yellow):
    """Vert if v < green, Jaune if v <= yellow, else Rouge."""
    return "Vert" if v < green else "Jaune" if v <= yellow else "Rouge"


def risk_hi(v, red, yellow):
    """Rouge if v > red, Jaune if v >= yellow, else Vert (risk sheet style)."""
    return "Rouge" if v > red else "Jaune" if v >= yellow else "Vert"


def risk_lo(v, red, yellow):
    """Rouge if v < red, Jaune if v <= yellow, else Vert."""
    return "Rouge" if v < red else "Jaune" if v <= yellow else "Vert"


def band(v, lo_g, hi_g, lo_y, hi_y):
    if lo_g <= v <= hi_g:
        return "Vert"
    if lo_y <= v < lo_g or hi_g < v <= hi_y:
        return "Jaune"
    return "Rouge"


# ── Indicator definitions ─────────────────────────────────────────────────────
# Each fetch() returns dict(value, [comp], [series for trend], src, asof).
MAN: dict = {}


def manual(key):
    m = MAN[key]
    return {"value": float(m["value"]), "src": m.get("src", "saisie manuelle"), "asof": m.get("asof", ""),
            "manual": True}


def F(series_id, transform=None, label=None):
    def _f():
        s = fred(series_id)
        t = transform(s) if transform else s
        return {"value": float(t.dropna().iloc[-1]), "series": t, "src": f"FRED {label or series_id}",
                "asof": asof(t)}
    return _f


HOPE = [
    ("H - Housing", "Mises en chantier US (SAAR)", ">1.4M", F("HOUST"), lambda v: hi(v, 1400, 1200),
     "Census Bureau, mensuel (milliers)"),
    ("H - Housing", "Permis de construire US", ">1.5M", F("PERMIT"), lambda v: hi(v, 1450, 1250),
     "Census Bureau, mensuel (milliers)"),
    ("H - Housing", "Indice NAHB confiance constructeurs", ">50", lambda: manual("nahb"),
     lambda v: hi(v, 50, 40), "NAHB, mensuel"),
    ("H - Housing", "Ventes maisons existantes (M, SAAR)", ">4.5M",
     F("EXHOSLUSM495S", lambda s: s / 1e6), lambda v: hi(v, 4.5, 3.8), "NAR, mensuel (millions)"),
    ("H - Housing", "Indice Case-Shiller 20 villes (YoY%)", "2-6%", lambda: _yoy_fred("SPCS20RSA"),
     lambda v: band(v, 2, 6, 0, 8), "S&P, mensuel avec délai"),
    ("O - Orders", "ISM Manufacturing PMI", ">50", lambda: manual("ism_pmi"), lambda v: hi(v, 50, 48),
     "ISM, 1er jour ouvrable du mois"),
    ("O - Orders", "ISM New Orders", ">50", lambda: manual("ism_new_orders"), lambda v: hi(v, 52, 48),
     "ISM, composante clé"),
    ("O - Orders", "Ratio New Orders/Inventories", ">1.0",
     lambda: {"value": MAN["ism_new_orders"]["value"] / MAN["ism_inventories"]["value"],
              "src": "ISM (saisie manuelle)", "asof": MAN["ism_new_orders"].get("asof", ""), "manual": True},
     lambda v: "Vert" if v > 1.05 else "Jaune" if v >= 0.95 else "Rouge", "New Orders / Inventories"),
    ("O - Orders", "PMI Manufacturier Global", ">50", lambda: manual("global_pmi"), lambda v: hi(v, 50, 48),
     "S&P Global/JPM"),
    ("O - Orders", "Commandes biens durables (MoM%)", ">0%",
     F("DGORDER", lambda s: s.pct_change() * 100), lambda v: hi(v, 0, -2), "Census Bureau"),
    ("P - Profits", "Croissance BPA S&P 500 (YoY%)", ">10%", lambda: manual("spx_eps_growth"),
     lambda v: hi(v, 10, 0), "Consensus BPA forward vs 12 mois"),
    ("P - Profits", "Earnings Yield S&P 500", ">5%", lambda: _earn_yield(), lambda v: hi(v, 5, 3.5),
     "100 / P/E trailing du S&P 500"),
    ("P - Profits", "Révisions BPA (3 mois)", ">0", lambda: manual("cesi"), lambda v: hi(v, 0, -5),
     "Citi Economic Surprise Index"),
    ("P - Profits", "Performance S&P 500 (YTD%)", ">0%",
     lambda: {"value": ytd("^GSPC"), "series": ycol("^GSPC"), "src": "Yahoo ^GSPC", "asof": asof(ycol("^GSPC"))},
     lambda v: hi(v, 5, 0), "S&P 500, rendement YTD"),
    ("E - Employment", "Emplois non-agricoles (variation, k)", ">150k", F("PAYEMS", lambda s: s.diff()),
     lambda v: hi(v, 150, 50), "BLS, 1er vendredi du mois"),
    ("E - Employment", "Taux de chômage U3", "<4.5%", F("UNRATE"), lambda v: lo(v, 4.5, 5.5), "BLS"),
    ("E - Employment", "Taux de chômage U6", "<8%", F("U6RATE"), lambda v: lo(v, 8, 10), "BLS, mesure élargie"),
    ("E - Employment", "Initial Jobless Claims (4wk avg, k)", "<250K", F("IC4WSA", lambda s: s / 1000),
     lambda v: lo(v, 220, 280), "DOL, hebdomadaire"),
    ("E - Employment", "JOLTS Job Openings (M)", ">8M", F("JTSJOL", lambda s: s / 1000),
     lambda v: hi(v, 8, 6), "BLS, avec délai (millions)"),
]


def _yoy_fred(sid):
    s = fred(sid)
    y = (s / s.shift(12) - 1) * 100
    return {"value": float(y.dropna().iloc[-1]), "series": y, "src": f"FRED {sid}", "asof": asof(y)}


_info_cache: dict = {}


def _info(t: str) -> dict:
    if t not in _info_cache:
        import yfinance as yf
        _info_cache[t] = yf.Ticker(t).info or {}
    return _info_cache[t]


def _earn_yield():
    # Trailing P/E of SPY from Yahoo; earnings yield = 100 / P/E
    pe = _info("SPY").get("trailingPE")
    if not pe:
        raise ValueError("SPY trailingPE unavailable")
    return {"value": 100 / float(pe), "src": "Yahoo SPY P/E trailing", "asof": TODAY.isoformat(),
            "trail_pe": float(pe)}


def _ypack(t, fn=ytd, comp=None, label=None):
    def _f():
        out = {"value": fn(t), "series": ycol(t), "src": f"Yahoo {label or t}", "asof": asof(ycol(t))}
        if comp:
            out["comp"] = comp(t)
        return out
    return _f


def _avg_ytd(ts):
    def _f():
        return {"value": sum(ytd(t) for t in ts) / len(ts), "src": "Yahoo " + "/".join(ts),
                "asof": asof(ycol(ts[0]))}
    return _f


def _diff_ytd(a, b, plus=0.0):
    def _f():
        return {"value": ytd(a) - ytd(b) + plus, "comp": chg_1m(a) - chg_1m(b),
                "src": f"Yahoo {a} - {b}", "asof": asof(ycol(a))}
    return _f


def _spy_trail_pe():
    try:
        return _earn_yield()["trail_pe"]
    except Exception:  # noqa: BLE001
        return None


def _spx_tech():
    s = ycol("^GSPC")
    return s


TACT = [
    ("VALORISATIONS", "P/E Forward S&P 500", "<18x",
     lambda: {**manual("spx_fwd_pe"), "comp": _spy_trail_pe()}, lambda v: lo(v, 18, 22)),
    ("VALORISATIONS", "P/E Forward S&P 600", "<20x",
     lambda: {**manual("sml_fwd_pe"), "comp": MAN["sml_trail_pe"]["value"]}, lambda v: lo(v, 20, 25)),
    ("VALORISATIONS", "Écart P/E (SPX - S&P600)", "<5x (abs)",
     lambda: {"value": MAN["spx_fwd_pe"]["value"] - MAN["sml_fwd_pe"]["value"], "src": "Calculé",
              "asof": MAN["spx_fwd_pe"].get("asof", ""), "manual": True},
     lambda v: "Vert" if abs(v) < 5 else "Jaune" if abs(v) <= 8 else "Rouge"),
    ("VALORISATIONS", "P/E MSCI EAFE", "<14x",
     lambda: {**manual("eafe_fwd_pe"), "comp": MAN["eafe_trail_pe"]["value"]}, lambda v: lo(v, 14, 17)),
    ("VALORISATIONS", "P/E MSCI EM", "<12x",
     lambda: {**manual("em_fwd_pe"), "comp": MAN["em_trail_pe"]["value"]}, lambda v: lo(v, 12, 15)),
    ("VALORISATIONS", "Equity Risk Premium (ERP)", ">2.5%",
     lambda: {"value": 100 / MAN["spx_fwd_pe"]["value"] - last(fred("DGS10")), "comp": 2.0,
              "src": "1/P/E fwd - 10 ans (FRED DGS10)", "asof": asof(fred("DGS10"))},
     lambda v: hi(v, 2.5, 1.5)),
    ("MOMENTUM ETF", "Momentum Small Cap (IWM) 1M%", ">+2%", _ypack("IWM", chg_1m, ytd), lambda v: hi(v, 2, -2)),
    ("MOMENTUM ETF", "Momentum Value (IVE) 1M%", ">+2%", _ypack("IVE", chg_1m, ytd), lambda v: hi(v, 2, -2)),
    ("MOMENTUM ETF", "Momentum EM (EEM) 1M%", ">+2%", _ypack("EEM", chg_1m, ytd), lambda v: hi(v, 2, -2)),
    ("MOMENTUM ETF", "Momentum Commodities (DBC) 1M%", ">+2%", _ypack("DBC", chg_1m, ytd), lambda v: hi(v, 2, -2)),
    ("CRÉDIT", "Spread HY US (OAS, bps)", "<350 bps",
     lambda: _oas("BAMLH0A0HYM2"), lambda v: lo(v, 350, 500)),
    ("CRÉDIT", "Spread IG US (OAS, bps)", "<100 bps",
     lambda: _oas("BAMLC0A0CM"), lambda v: lo(v, 100, 150)),
    ("CRÉDIT", "Performance dette EM (EMB YTD)", ">0% YTD", _ypack("EMB", ytd, chg_1y), lambda v: hi(v, 2, 0)),
    ("CRÉDIT", "Ratio spread BB/HY total", "<0.6x",
     lambda: {"value": last(fred("BAMLH0A1HYBB")) / last(fred("BAMLH0A0HYM2")), "src": "FRED ICE BofA BB / HY",
              "asof": asof(fred("BAMLH0A1HYBB"))},
     lambda v: lo(v, 0.6, 0.8)),
    ("MOMENTUM", "RSI S&P 500 (14 jours)", "30-70",
     lambda: {"value": rsi(_spx_tech(), 14), "comp": rsi(_spx_tech(), 30), "src": "Calculé (Yahoo ^GSPC)",
              "asof": asof(_spx_tech())},
     lambda v: band(v, 30, 70, 20.0001, 79.9999)),
    ("MOMENTUM", "S&P 500 vs MA 200 jours", ">0%",
     lambda: {"value": (last(_spx_tech()) / float(_spx_tech().iloc[-200:].mean()) - 1) * 100,
              "comp": (last(_spx_tech()) / float(_spx_tech().iloc[-50:].mean()) - 1) * 100,
              "src": "Calculé (Yahoo ^GSPC)", "asof": asof(_spx_tech())},
     lambda v: hi(v, 0, -5)),
    ("MOMENTUM", "VIX", "<20", _ypack("^VIX", lambda t: last(ycol(t)), chg_1m), lambda v: lo(v, 20, 30)),
    ("MOMENTUM", "Breadth: RSP vs SPY (+50, proxy)", ">60", _diff_ytd("RSP", "SPY", 50), lambda v: hi(v, 60, 40)),
]


def _oas(sid):
    s = fred(sid) * 100
    m1 = s[s.index <= s.index[-1] - pd.DateOffset(months=1)]
    return {"value": last(s), "comp": (last(s) / float(m1.iloc[-1]) - 1) * 100, "series": s,
            "src": f"FRED {sid}", "asof": asof(s)}


def _nvda_growth():
    g = _info("NVDA").get("revenueGrowth")
    if g is None:
        raise ValueError("NVDA revenueGrowth unavailable")
    return {"value": float(g) * 100, "src": "Yahoo NVDA (trimestre, a/a)", "asof": TODAY.isoformat()}


def _px_last(t, mult=1.0, label=None):
    def _f():
        s = ycol(t) * mult
        return {"value": last(s), "series": s, "src": f"Yahoo {label or t}", "asof": asof(s)}
    return _f


THESES = [
    ("IA - COUCHE 1: ÉNERGIE", "Utilities US (XLU YTD%)", ">10%", _ypack("XLU"), lambda v: hi(v, 10, 5)),
    ("IA - COUCHE 1: ÉNERGIE", "Prix uranium spot ($/lb)", ">$80/lb", lambda: manual("uranium"),
     lambda v: hi(v, 80, 60)),
    ("IA - COUCHE 1: ÉNERGIE", "Prix gaz naturel Henry Hub", ">$3.50/MMBtu", _px_last("NG=F"),
     lambda v: hi(v, 3.5, 2.5)),
    ("IA - COUCHE 2: PUCES", "Revenus NVIDIA (YoY%)", ">20%", _nvda_growth, lambda v: hi(v, 20, 10)),
    ("IA - COUCHE 2: PUCES", "Performance SOX Index (semi) YTD%", ">0%", _ypack("^SOX"), lambda v: hi(v, 10, 0)),
    ("IA - COUCHE 3: INFRASTRUCTURE", "Perf. hyperscalers (AMZN/GOOG/MSFT/META YTD%)", ">+10% YTD",
     _avg_ytd(["AMZN", "GOOG", "MSFT", "META"]), lambda v: hi(v, 10, 0)),
    ("IA - COUCHE 3: INFRASTRUCTURE", "Performance Vertiv/Quanta/EQIX", ">+10% YTD",
     _avg_ytd(["VRT", "PWR", "EQIX"]), lambda v: hi(v, 10, 0)),
    ("IA - COUCHE 5: APPLICATIONS", "Performance Cloud ETF (WCLD YTD%)", ">+10% YTD", _ypack("WCLD"),
     lambda v: hi(v, 10, 0)),
    ("GREAT BROADENING", "Performance relative RTY vs SPX (YTD)", ">0%", _diff_ytd("^RUT", "^GSPC"),
     lambda v: hi(v, 0, -5)),
    ("GREAT BROADENING", "Breadth: RSP vs SPY (+50, proxy)", ">53 (proxy)", _diff_ytd("RSP", "SPY", 50),
     lambda v: hi(v, 53, 47)),
    ("GREAT BROADENING", "Performance S&P Equal Weight vs Cap Weight", ">0%", _diff_ytd("RSP", "SPY"),
     lambda v: hi(v, 0, -3)),
    ("COMMODITÉS - RARETÉ", "Prix cuivre ($/tonne, COMEX)", ">$9,500/t", _px_last("HG=F", 2204.62, "HG=F x 2204.62"),
     lambda v: hi(v, 9500, 7700)),
    ("COMMODITÉS - RARETÉ", "Prix argent ($/oz)", ">$50/oz", _px_last("SI=F"), lambda v: hi(v, 50, 35)),
    ("COMMODITÉS - RARETÉ", "Inventaires cuivre LME (tonnes)", "Déclin", lambda: manual("lme_cu_stocks"),
     lambda v: (lambda c: "Vert" if c < -5 else "Jaune" if c <= 5 else "Rouge")(
         float(MAN["lme_cu_stocks"].get("chg_1m_pct", 0)))),
    ("COMMODITÉS - RARETÉ", "Mines diversifiées (PICK YTD)", ">+10% YTD", _ypack("PICK"), lambda v: hi(v, 10, 0)),
    ("STIMULUS FISCAL US", "Performance small caps US (IWM YTD)", ">+10% YTD", _ypack("IWM"), lambda v: hi(v, 10, 0)),
    ("STIMULUS FISCAL US", "Performance industrielles US (XLI YTD)", ">+10% YTD", _ypack("XLI"),
     lambda v: hi(v, 10, 0)),
    ("STIMULUS FISCAL US", "Consumer Confidence (Conference Board)", ">100", lambda: manual("conf_board"),
     lambda v: hi(v, 100, 80)),
    ("STIMULUS FISCAL US", "Rendement 10Y US (coût du stimulus)", "<4.50%", F("DGS10"), lambda v: lo(v, 4.5, 5)),
    ("SANTÉ / BIOTECH", "Performance XBI (Biotech ETF)", ">+10% YTD", _ypack("XBI"), lambda v: hi(v, 10, 0)),
    ("SANTÉ / BIOTECH", "Biotech large cap (IBB YTD, proxy FDA)", ">+5% YTD", _ypack("IBB"), lambda v: hi(v, 5, 0)),
]


def _tsx_rel():
    return {"value": ytd("^GSPTSE") - ytd("^GSPC"), "src": "Yahoo ^GSPTSE - ^GSPC", "asof": asof(ycol("^GSPTSE"))}


def _ca_us_10y():
    ca, us = boc("BD.CDN.10YR.DQ.YLD"), fred("DGS10")
    return {"value": last(ca) - last(us), "src": "BdC Valet + FRED DGS10", "asof": asof(ca)}


def _cadusd():
    s = 1 / ycol("CAD=X")
    return {"value": last(s), "series": s, "src": "Yahoo CAD=X", "asof": asof(s)}


def _ted():
    cp, tb = fred("DCPF3M"), fred("DTB3")
    j = pd.concat([cp, tb], axis=1).dropna()
    return {"value": float((j.iloc[-1, 0] - j.iloc[-1, 1]) * 100), "src": "FRED DCPF3M - DTB3 (bps)",
            "asof": j.index[-1].date().isoformat()}


def _ff_futures():
    try:
        s = ycol("ZQ=F")
        return {"value": last(s), "series": s, "src": "Yahoo ZQ=F", "asof": asof(s)}
    except Exception:  # noqa: BLE001 — fall back to 100 - effective fed funds
        s = 100 - fred("DFF")
        return {"value": last(s), "series": s, "src": "100 - FRED DFF", "asof": asof(s)}


RISQUES = [
    ("INFLATION", "CPI Core US (YoY%)", ">3.0%", lambda: _yoy_fred("CPILFESL"), lambda v: risk_hi(v, 3, 2.5),
     "Fed target 2%"),
    ("INFLATION", "PCE Core (YoY%)", ">3.0%", lambda: _yoy_fred("PCEPILFE"), lambda v: risk_hi(v, 3, 2.5),
     "Mesure préférée Fed"),
    ("INFLATION", "Inflation anticipée 5Y5Y", ">2.5%", F("T5YIFR"), lambda v: risk_hi(v, 2.5, 2.3),
     "Anticipations long terme"),
    ("INFLATION", "Salaires horaires (YoY%)", ">4.0%", lambda: _yoy_fred("CES0500000003"),
     lambda v: risk_hi(v, 4, 3.5), "Pression salariale"),
    ("TAUX / YIELDS", "Rendement 10 ans US", ">5.0%", F("DGS10"), lambda v: risk_hi(v, 5, 4.5), "Bond vigilantes"),
    ("TAUX / YIELDS", "Rendement 2 ans US", ">5.0%", F("DGS2"), lambda v: risk_hi(v, 5, 4.5), "Attentes Fed"),
    ("TAUX / YIELDS", "Spread 10Y-2Y (courbe, bps)", "<-50bps", F("T10Y2Y", lambda s: s * 100),
     lambda v: risk_lo(v, -50, 0), "Inversion = risque récession"),
    ("TAUX / YIELDS", "Rendement réel 10Y TIPS", ">2.5%", F("DFII10"), lambda v: risk_hi(v, 2.5, 2),
     "Coût réel du capital"),
    ("TAUX / YIELDS", "Fed Funds futures (front month)", "<95.50", _ff_futures,
     lambda v: "Rouge" if v < 95 else "Jaune" if v <= 95.5 else "Vert", "Trajectoire anticipée"),
    ("CRÉDIT / LIQUIDITÉ", "Spread papier commercial 3M - T-bill (bps)", ">50bps", _ted,
     lambda v: risk_hi(v, 50, 30), "Stress de financement court terme (remplace le TED)"),
    ("CRÉDIT / LIQUIDITÉ", "Bilan de la Fed (M$)", "<6,000,000", F("WALCL"),
     lambda v: "Rouge" if v < 5_500_000 else "Jaune" if v <= 6_000_000 else "Vert", "Liquidité système"),
    ("CRÉDIT / LIQUIDITÉ", "Spread HY US OAS (%)", ">5.0 (500 bps)", F("BAMLH0A0HYM2"),
     lambda v: risk_hi(v, 5, 4), "Proxy stress crédit"),
    ("GÉOPOLITIQUE", "VIX (Volatilité implicite US)", ">30", _px_last("^VIX"), lambda v: risk_hi(v, 30, 20),
     "Volatilité implicite"),
    ("GÉOPOLITIQUE", "Prix pétrole Brent", ">$80", _px_last("BZ=F"), lambda v: risk_hi(v, 100, 80), "Choc pétrolier"),
    ("GÉOPOLITIQUE", "USD Index (DXY)", ">110", _px_last("DX-Y.NYB", label="DXY"), lambda v: risk_hi(v, 110, 103),
     "Force dollar"),
    ("GÉOPOLITIQUE", "USD/CNY", ">7.5", _px_last("CNY=X"), lambda v: risk_hi(v, 7.5, 7.2), "Tensions Chine"),
    ("CANADA", "Écart taux 10Y CA-US", "<-1.0%", _ca_us_10y, lambda v: risk_lo(v, -1, -0.5),
     "Divergence politique monétaire"),
    ("CANADA", "CAD/USD", "<0.70", _cadusd, lambda v: risk_lo(v, 0.70, 0.74), "Faiblesse dollar canadien"),
    ("CANADA", "Renouvellements hypothécaires 2026", "Qualitatif",
     lambda: {"value": "Risque élevé", "src": "Interne", "asof": "", "manual": True}, lambda v: "Jaune",
     "Mur hypothécaire 2025-2026. ~$300Mds de renouvellements à taux plus élevés."),
    ("CANADA", "Indice TSX vs S&P 500 (rel perf)", "<-10%", _tsx_rel, lambda v: risk_lo(v, -10, 0),
     "Sous-performance Canada"),
]


def _sc_yoy(vector, label, monthly=True):
    def _f():
        s = statcan(vector, 30)
        y = (s / s.shift(12 if monthly else 4) - 1) * 100
        return {"value": float(y.dropna().iloc[-1]), "series": y, "src": f"StatCan {label}", "asof": asof(y)}
    return _f


def _sc_level(vector, label, transform=None):
    def _f():
        s = statcan(vector, 30)
        s = transform(s) if transform else s
        return {"value": float(s.dropna().iloc[-1]), "series": s, "src": f"StatCan {label}", "asof": asof(s)}
    return _f


def _boc_last(series, label=None):
    def _f():
        s = boc(series)
        return {"value": last(s), "series": s, "src": f"BdC {label or series}", "asof": asof(s)}
    return _f


def _boc_minus_fed():
    b, f_ = boc("V39079"), fred("DFEDTARU")
    return {"value": last(b) - last(f_), "src": "BdC V39079 - FRED DFEDTARU", "asof": asof(b)}


def _tsx_level():
    s = ycol("^GSPTSE")
    return {"value": last(s), "series": s, "src": "Yahoo ^GSPTSE", "asof": asof(s),
            "above_ma200": last(s) > float(s.iloc[-200:].mean())}


CANADA = [
    ("CROISSANCE", "PIB réel Canada (YoY%)", ">1.5%", _sc_yoy(62305752, "PIB réel (v62305752)", monthly=False),
     lambda v: "Vert" if v > 1.5 else "Jaune" if v > 0 else "Rouge", "StatCan, trimestriel"),
    ("CROISSANCE", "Indice avancé (Conference Board CA)", ">0%", lambda: manual("ca_lei"),
     lambda v: "Vert" if v > 0 else "Rouge", "Indicateur avancé 6 mois"),
    ("CROISSANCE", "Ventes au détail (YoY%)", ">2%", _sc_yoy(52367097, "Commerce de détail (v52367097)"),
     lambda v: "Vert" if v > 2 else "Jaune" if v > 0 else "Rouge", "StatCan, mensuel"),
    ("INFLATION / BoC", "CPI Canada (YoY%)", "<2.5%", _sc_yoy(41690973, "IPC (v41690973)"),
     lambda v: "Vert" if v < 2.5 else "Jaune" if v < 3 else "Rouge", "Cible BoC 2% (fourchette 1-3%)"),
    ("INFLATION / BoC", "CPI Core médian (YoY%)", "<2.5%", _boc_last("CPI_MEDIAN", "IPC-méd"),
     lambda v: "Vert" if v < 2.5 else "Jaune" if v < 3 else "Rouge", "Mesure préférée BoC"),
    ("INFLATION / BoC", "Taux directeur BoC", "<3.0%", _boc_last("V39079", "taux directeur"),
     lambda v: "Vert" if v < 3 else "Jaune" if v < 4 else "Rouge", "Banque du Canada"),
    ("INFLATION / BoC", "Spread BoC - Fed Funds", ">-1.5%", _boc_minus_fed,
     lambda v: "Vert" if v > -1.5 else "Jaune" if v > -2 else "Rouge", "Divergence politique monétaire = pression CAD"),
    ("EMPLOI", "Taux de chômage CA", "<6.5%", _sc_level(2062815, "EPA (v2062815)"),
     lambda v: "Vert" if v < 6.5 else "Jaune" if v < 7 else "Rouge", "StatCan, mensuel"),
    ("EMPLOI", "Création d'emplois (variation mensuelle, k)", ">+25k",
     _sc_level(2062811, "EPA (v2062811)", lambda s: s.diff()),
     lambda v: "Vert" if v > 25 else "Jaune" if v > 0 else "Rouge", "Enquête sur la population active"),
    ("TAUX / FX", "Rendement 10Y Canada", "<4.0%", _boc_last("BD.CDN.10YR.DQ.YLD", "10 ans"),
     lambda v: "Vert" if v < 4 else "Jaune" if v < 4.5 else "Rouge", "GoC 10-year benchmark"),
    ("TAUX / FX", "Rendement 2Y Canada", "<3.5%", _boc_last("BD.CDN.2YR.DQ.YLD", "2 ans"),
     lambda v: "Vert" if v < 3.5 else "Jaune" if v < 4 else "Rouge", "Sensible aux décisions BoC"),
    ("TAUX / FX", "Spread 10Y CA-US", ">-1.0%", _ca_us_10y,
     lambda v: "Vert" if v > -1 else "Jaune" if v > -1.25 else "Rouge", "Écart yields, indicateur de pression CAD"),
    ("TAUX / FX", "CAD/USD", ">0.72", _cadusd,
     lambda v: "Vert" if v > 0.72 else "Jaune" if v > 0.7 else "Rouge", "Faiblesse CAD pression sur importations"),
    ("LOGEMENT", "S&P/TSX REIT (XRE YTD%) - proxy logement", ">0%", _ypack("XRE.TO"),
     lambda v: "Vert" if v > 5 else "Jaune" if v > 0 else "Rouge", "iShares XRE"),
    ("LOGEMENT", "Mises en chantier CA (k SAAR)", ">220k", _sc_level(52300157, "SCHL (v52300157)"),
     lambda v: "Vert" if v > 220 else "Jaune" if v > 200 else "Rouge", "SCHL, mensuel"),
    ("LOGEMENT", "Renouvellements hypothécaires 2025-2026", "Qualitatif",
     lambda: {"value": "~$300Mds", "src": "Interne", "asof": "", "manual": True}, lambda v: "Rouge",
     "Mur hypothécaire: renouvellements à taux plus élevés"),
    ("COMMERCE", "Balance commerciale CA ($CAD Mds)", ">0",
     _sc_level(87008955, "commerce (v87008955)", lambda s: s / 1000),
     lambda v: "Vert" if v > 0 else "Jaune" if v > -2 else "Rouge", "StatCan, mensuel. Exposition tarifs US."),
    ("COMMERCE", "Prix pétrole WCS (Western Canadian Select)", ">$55", lambda: manual("wcs"),
     lambda v: "Vert" if v > 55 else "Jaune" if v > 40 else "Rouge", "Clé pour secteur énergie + dollar canadien"),
    ("MARCHÉS CA", "TSX Composite (niveau)", "Au-dessus MA200", _tsx_level,
     lambda v: "Vert" if _STATE.get("tsx_above_ma200", True) else "Jaune", "S&P/TSX Composite"),
    ("MARCHÉS CA", "TSX Composite (YTD%)", ">5%", _ypack("^GSPTSE"),
     lambda v: "Vert" if v > 5 else "Jaune" if v > 0 else "Rouge", "Performance YTD"),
    ("MARCHÉS CA", "P/E Forward TSX", "<16x", lambda: manual("tsx_fwd_pe"),
     lambda v: "Vert" if v < 16 else "Jaune" if v < 18 else "Rouge", "Valorisation relative TSX"),
    ("MARCHÉS CA", "Perf TSX vs S&P 500 (YTD)", ">-5%", _tsx_rel,
     lambda v: "Vert" if v > -5 else "Jaune" if v > -10 else "Rouge", "Surperformance/sous-perf relative"),
    ("MARCHÉS CA", "Perf Banques CA (ZEB YTD)", ">0%", _ypack("ZEB.TO"),
     lambda v: "Vert" if v > 0 else "Rouge", "BMO Equal Weight Banks (proxy S&P/TSX Banks)"),
    ("MARCHÉS CA", "Perf Énergie CA (XEG YTD)", ">0%", _ypack("XEG.TO"),
     lambda v: "Vert" if v > 0 else "Rouge", "iShares S&P/TSX Capped Energy"),
    ("MARCHÉS CA", "Perf Matériaux CA (XMA YTD)", ">0%", _ypack("XMA.TO"),
     lambda v: "Vert" if v > 0 else "Rouge", "iShares S&P/TSX Capped Materials"),
]

_STATE: dict = {}


# ── Formatting (same as the Snapshot page) ────────────────────────────────────
def fmt_val(v) -> str:
    if isinstance(v, str):
        return v
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    f = float(v)
    if abs(f) >= 1_000:
        return f"{int(round(f)):,}".replace(",", " ")
    if abs(f) >= 100:
        return f"{f:.1f}"
    if abs(f) >= 10:
        return f"{f:.2f}"
    return f"{f:.3f}".rstrip("0").rstrip(".")


def _src_note(res: dict, stale: bool) -> str:
    bits = [res.get("src", "")]
    if res.get("asof"):
        bits.append(f"au {res['asof']}")
    if stale:
        bits.append("⚠ non rafraîchi")
    return " · ".join(b for b in bits if b)


def _previous_rows(prev: dict, group: str) -> dict:
    out = {}
    for rows in prev.get(group, {}).values():
        for r in rows:
            out[r["ind"]] = r
    return out


def evaluate(defs, group: str, prev: dict, kind: str) -> dict:
    """Run every indicator of a section; keep the previous row when a fetch fails."""
    old = _previous_rows(prev, group)
    out: dict = {}
    for d in defs:
        cat, ind, seuil, fetch, rule = d[:5]
        note = d[5] if len(d) > 5 else ""
        try:
            res = fetch()
            v = res["value"]
            if isinstance(v, float) and math.isnan(v):
                raise ValueError("NaN")
            if ind.startswith("TSX Composite (niveau)"):
                _STATE["tsx_above_ma200"] = res.get("above_ma200", True)
            sig = rule(v)
            stale = False
        except Exception as exc:  # noqa: BLE001
            log.warning("%s / %s: %s", group, ind, exc)
            if ind in old:
                row = dict(old[ind])
                row["src"] = ((row.get("src") or "") + (" · ⚠ non rafraîchi" if "non rafraîchi" not in
                                                        (row.get("src") or "") else "")).lstrip(" ·")
            else:  # keep the indicator visible, excluded from the counts
                sig_key = "statut" if kind == "theses" else "signal"
                row = {"ind": ind, "val": "n.d.", sig_key: "—", "src": "⚠ non rafraîchi (source indisponible)"}
                row.update({"hope": {"seuil": seuil, "tend": "→", "note": note},
                            "tact": {"comp": "—", "cible": seuil, "impl": ""},
                            "theses": {"cible": seuil, "note": note}}.get(kind, {"seuil": seuil, "comm": note}))
            out.setdefault(cat, []).append(row)
            continue
        trend = trend_of(res.get("series"))
        src = _src_note(res, stale)
        if kind == "hope":
            row = {"ind": ind, "val": fmt_val(v), "seuil": seuil, "signal": sig, "tend": trend, "note": note,
                   "src": src}
        elif kind == "tact":
            comp = res.get("comp")
            impl = f"{fmt_val(v)} vs {fmt_val(comp)}" if comp is not None else ""
            row = {"ind": ind, "val": fmt_val(v), "comp": fmt_val(comp) if comp is not None else "—",
                   "cible": seuil, "signal": sig, "impl": impl, "src": src}
        elif kind == "theses":
            row = {"ind": ind, "val": fmt_val(v), "cible": seuil, "statut": sig, "note": note, "src": src}
        else:  # risques / canada
            row = {"ind": ind, "val": fmt_val(v), "seuil": seuil, "signal": sig, "comm": note, "src": src}
        if res.get("manual"):
            row["manual"] = True
        out.setdefault(cat, []).append(row)
    return out


def counts(groups: dict, key: str) -> tuple[int, int, int]:
    rows = [r for v in groups.values() for r in v]
    return (sum(r[key] == "Vert" for r in rows), sum(r[key] == "Jaune" for r in rows),
            sum(r[key] == "Rouge" for r in rows))


def score(v, j, r) -> int:
    n = v + j + r
    return int(math.floor((v + 0.5 * j) / n * 100 + 0.5)) if n else 0


def arrow(s: int) -> str:
    return "↑" if s >= 70 else "→" if s >= 40 else "↓"


def main() -> int:
    global MAN
    MAN = json.loads(MANUAL.read_text(encoding="utf-8"))
    prev = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}

    hope = evaluate(HOPE, "hope", prev, "hope")
    tact = evaluate(TACT, "tact", prev, "tact")
    theses = evaluate(THESES, "theses", prev, "theses")
    risques = evaluate(RISQUES, "risques", prev, "risques")
    canada = evaluate(CANADA, "canada", prev, "canada")

    cats = [("Cycle HOPE", hope, "signal", "#60A5FA"), ("Signaux Tactiques", tact, "signal", "#F59E0B"),
            ("Thèses Clés", theses, "statut", "#34D399"), ("Alertes Risques", risques, "signal", "#F87171")]
    scorecard = []
    for name, groups, key, color in cats:
        v, j, r = counts(groups, key)
        s = score(v, j, r)
        scorecard.append({"cat": name, "score": s, "trend": arrow(s), "vert": v, "jaune": j, "rouge": r,
                          "color": color})
    cv, cj, cr = counts(canada, "signal")
    cs = score(cv, cj, cr)
    scorecard.append({"cat": "Canada", "score": cs, "trend": arrow(cs), "vert": cv, "jaune": cj, "rouge": cr,
                      "color": "#EF4444"})
    g = int(math.floor(sum(x["score"] for x in scorecard[:4]) / 4 + 0.5))
    scorecard.append({"cat": "SCORE GLOBAL", "score": g, "trend": arrow(g), "vert": None, "jaune": None,
                      "rouge": None, "color": "#A78BFA"})

    matrice = [{**m, "score": m["prob"] * m["impact"]} for m in MAN.get("matrice", [])]

    n_total = sum(len(v) for grp in (hope, tact, theses, risques, canada) for v in grp.values())
    n_manual = sum(1 for grp in (hope, tact, theses, risques, canada) for v in grp.values() for r in v
                   if r.get("manual"))
    n_stale = sum(1 for grp in (hope, tact, theses, risques, canada) for v in grp.values() for r in v
                  if "non rafraîchi" in r.get("src", ""))

    out = {
        "source": "Sources web gratuites (FRED, Yahoo Finance, Banque du Canada, StatCan)",
        "date": TODAY.isoformat(),
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "stats": {"total": n_total, "manual": n_manual, "stale": n_stale},
        "score": scorecard, "hope": hope, "tact": tact, "theses": theses, "risques": risques,
        "canada": canada, "matrice": matrice,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    log.info("Scores: %s", ", ".join(f"{s['cat']} {s['score']}" for s in scorecard))
    log.info("%d indicateurs · %d manuels · %d non rafraîchis", n_total, n_manual, n_stale)
    return 0


if __name__ == "__main__":
    sys.exit(main())
