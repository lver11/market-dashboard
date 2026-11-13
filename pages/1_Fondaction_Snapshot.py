"""
Fondaction Bloomberg Snapshot Dashboard — Page Streamlit
Supporte le chargement dynamique via upload Excel (onglet Snapshot).
"""

import io
from pathlib import Path
import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Fondaction — Snapshot Marchés",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.html("""
<style>
  [data-testid="stAppViewContainer"] { background: #0B1120; }
  [data-testid="stHeader"] { background: transparent; }
  section[data-testid="stSidebar"] { background: #111827; }
  .block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1500px; }

  .snap-title { font-size:1.4rem; font-weight:800; color:#F9FAFB; letter-spacing:0.04em; }
  .snap-sub   { font-size:0.75rem; color:#6B7280; margin-top:2px; }

  .section-hdr {
    font-size:0.6rem; letter-spacing:0.2em; text-transform:uppercase;
    color:#9CA3AF; background:#1F2937; border-radius:4px;
    padding:3px 10px; display:inline-block; margin-bottom:8px;
  }

  .sig-vert  { background:rgba(16,185,129,0.15); color:#34D399;
               border:1px solid rgba(16,185,129,0.3); border-radius:4px;
               padding:2px 8px; font-size:0.65rem; font-weight:700;
               display:inline-block; white-space:nowrap; }
  .sig-jaune { background:rgba(245,158,11,0.15); color:#FBBF24;
               border:1px solid rgba(245,158,11,0.3); border-radius:4px;
               padding:2px 8px; font-size:0.65rem; font-weight:700;
               display:inline-block; white-space:nowrap; }
  .sig-rouge { background:rgba(239,68,68,0.15); color:#F87171;
               border:1px solid rgba(239,68,68,0.3); border-radius:4px;
               padding:2px 8px; font-size:0.65rem; font-weight:700;
               display:inline-block; white-space:nowrap; }
  .sig-neut  { background:rgba(107,114,128,0.15); color:#9CA3AF;
               border:1px solid rgba(107,114,128,0.3); border-radius:4px;
               padding:2px 8px; font-size:0.65rem; font-weight:700;
               display:inline-block; white-space:nowrap; }

  .ind-row {
    background:#111827; border:1px solid #1F2937; border-radius:8px;
    padding:10px 14px; margin-bottom:6px;
    display:flex; align-items:center; gap:12px;
  }
  .ind-name  { flex:3; font-size:0.78rem; color:#E5E7EB; font-weight:500; }
  .ind-val   { flex:1.2; font-size:0.82rem; font-family:monospace;
               font-weight:700; color:#F9FAFB; text-align:right; }
  .ind-seuil { flex:1.2; font-size:0.7rem; color:#6B7280; text-align:right; }
  .ind-note  { flex:3; font-size:0.65rem; color:#4B5563; font-style:italic; }
  .ind-tend  { font-size:1rem; min-width:18px; text-align:center; }
  .tend-up   { color:#34D399; }
  .tend-dn   { color:#F87171; }
  .tend-flat { color:#9CA3AF; }

  .subsec-hdr {
    font-size:0.62rem; letter-spacing:0.15em; text-transform:uppercase;
    color:#6B7280; padding:6px 0 4px; border-bottom:1px solid #1F2937;
    margin:14px 0 8px;
  }

  .mat-val { flex:1; font-size:0.8rem; font-family:monospace;
             color:#9CA3AF; text-align:center; }
  .mat-score-0 { color:#1F2937; }
  .mat-score-hi { color:#F87171; font-weight:700; }
  .mat-score-med { color:#FBBF24; font-weight:700; }
  .mat-score-lo { color:#34D399; font-weight:700; }

</style>
""")

# ── Helpers ───────────────────────────────────────────────────────────────────
def safe_str(v) -> str:
    if isinstance(v, float) and pd.isna(v):
        return ""
    s = str(v).strip()
    return "" if s == "nan" else s


def fmt_val(v) -> str:
    s = safe_str(v)
    if not s:
        return "—"
    try:
        f = float(s)
        if abs(f) >= 10_000:
            return f"{int(round(f)):,}".replace(",", "\u202f")
        elif abs(f) >= 1_000:
            return f"{int(round(f)):,}".replace(",", "\u202f")
        elif abs(f) >= 100:
            return f"{f:.1f}"
        elif abs(f) >= 10:
            return f"{f:.2f}"
        else:
            return f"{f:.3f}".rstrip("0").rstrip(".")
    except ValueError:
        return s


def src_tag(r: dict) -> str:
    """Small source / freshness line under an indicator's note (web-updated snapshots)."""
    src = r.get("src")
    if not src:
        return ""
    color = "#B45309" if ("non rafraîchi" in src or r.get("manual")) else "#374151"
    label = "✍ " if r.get("manual") else ""
    return f'<br><span style="font-size:0.58rem;color:{color};font-style:normal;">{label}{src}</span>'


def sig_badge(s: str) -> str:
    labels = {"Vert": "✓ VERT", "Jaune": "⚠ JAUNE", "Rouge": "✕ ROUGE"}
    classes = {"Vert": "sig-vert", "Jaune": "sig-jaune", "Rouge": "sig-rouge"}
    return f'<span class="{classes.get(s, "sig-neut")}">{labels.get(s, s)}</span>'


def tend_cls(t: str) -> str:
    return {"↑": "tend-up", "↓": "tend-dn"}.get(t, "tend-flat")


def gauge_fig(score: int, color: str, label: str) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": label, "font": {"size": 11, "color": "#9CA3AF"}},
        number={"font": {"size": 26, "color": color, "family": "monospace"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#374151",
                     "tickfont": {"color": "#6B7280", "size": 9}},
            "bar": {"color": color, "thickness": 0.28},
            "bgcolor": "#1F2937",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  40], "color": "rgba(239,68,68,0.08)"},
                {"range": [40, 65], "color": "rgba(245,158,11,0.08)"},
                {"range": [65,100], "color": "rgba(16,185,129,0.08)"},
            ],
            "threshold": {"line": {"color": color, "width": 2}, "value": score},
        },
    ))
    fig.update_layout(
        height=180, margin=dict(t=40, b=0, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#E5E7EB"},
    )
    return fig


# ── Excel Parser ───────────────────────────────────────────────────────────────
# Sections of the "Snapshot" sheet are located by their header text (column B),
# so rows can be added or removed in the workbook without breaking the parser.
_SECTION_KEYS = {
    "sommaire": "SOMMAIRE",
    "hope":     "INDICATEURS DE CYCLE",
    "tact":     "SIGNAUX TACTIQUES",
    "theses":   "SUIVI DES TH",
    "risques":  "ALERTES RISQUES",
    "canada":   "INDICATEURS CANADA",
    "matrice":  "MATRICE PROBABILIT",
}


def _find_sections(df) -> dict:
    """Return {key: (first_data_row, last_data_row)} for each section found."""
    starts = {}
    for ri in range(len(df)):
        cell = safe_str(df.iloc[ri, 1]).upper()
        if not cell:
            continue
        for key, needle in _SECTION_KEYS.items():
            if key not in starts and needle in cell and ("═" in cell or key == "matrice"):
                starts[key] = ri
    ordered = sorted(starts.items(), key=lambda kv: kv[1])
    bounds = {}
    for i, (key, hdr) in enumerate(ordered):
        stop = ordered[i + 1][1] - 1 if i + 1 < len(ordered) else len(df) - 1
        bounds[key] = (hdr + 2, stop)  # skip header + column-title rows
    return bounds


def _grouped_rows(df, bounds, builder) -> dict:
    """Group rows under the category in column B (carried down when blank)."""
    out: dict = {}
    if not bounds:
        return out
    current = None
    for ri in range(bounds[0], bounds[1] + 1):
        row = df.iloc[ri]
        cat, ind = safe_str(row[1]), safe_str(row[2])
        if not ind:
            continue
        if cat:
            current = cat
        if current:
            out.setdefault(current, []).append(builder(row, ind))
    return out


def _counts(groups: dict, key: str = "signal") -> tuple[int, int, int]:
    rows = [r for v in groups.values() for r in v]
    return (sum(r[key] == "Vert" for r in rows),
            sum(r[key] == "Jaune" for r in rows),
            sum(r[key] == "Rouge" for r in rows))


def _int(v, default=0) -> int:
    try:
        return int(float(safe_str(v)))
    except (TypeError, ValueError):
        return default


def parse_snapshot(file_bytes: bytes):
    df = pd.read_excel(io.BytesIO(file_bytes), sheet_name="Snapshot", header=None)
    sec = _find_sections(df)
    missing = [k for k in ("sommaire", "hope", "tact", "theses", "risques") if k not in sec]
    if missing:
        raise ValueError(f"sections introuvables dans l'onglet Snapshot : {', '.join(missing)}")

    # Date
    date_str = "—"
    for ri in range(0, 4):
        cell = safe_str(df.iloc[ri, 1])
        if "mise" in cell.lower() and ":" in cell:
            date_str = cell.split(":", 1)[-1].strip()
            break

    # Scorecard — scores, trends and signal counts come straight from the workbook
    colors = {"Cycle HOPE": "#60A5FA", "Signaux Tactiques": "#F59E0B", "Thèses Clés": "#34D399",
              "Alertes Risques": "#F87171", "SCORE GLOBAL": "#A78BFA"}
    scorecard = []
    a, b = sec["sommaire"]
    for ri in range(a, b + 1):
        row = df.iloc[ri]
        cat = safe_str(row[1])
        if cat not in colors:
            continue
        has_counts = safe_str(row[4]) != ""
        scorecard.append({
            "cat": cat, "score": _int(row[2]), "trend": safe_str(row[3]) or "→",
            "vert":  _int(row[4]) if has_counts else None,
            "jaune": _int(row[5]) if has_counts else None,
            "rouge": _int(row[6]) if has_counts else None,
            "color": colors[cat],
        })

    hope_data = _grouped_rows(df, sec.get("hope"), lambda r, ind: {
        "ind": ind, "val": fmt_val(r[3]), "seuil": safe_str(r[4]) or "—",
        "signal": safe_str(r[5]) or "—", "tend": safe_str(r[6]) or "→", "note": safe_str(r[7])})

    tact_data = _grouped_rows(df, sec.get("tact"), lambda r, ind: {
        "ind": ind, "val": fmt_val(r[3]), "comp": fmt_val(r[4]), "cible": safe_str(r[5]) or "—",
        "signal": safe_str(r[6]) or "—", "impl": safe_str(r[7])})

    theses_data = _grouped_rows(df, sec.get("theses"), lambda r, ind: {
        "ind": ind, "val": fmt_val(r[3]), "cible": safe_str(r[4]) or "—",
        "statut": safe_str(r[5]) or "—", "note": safe_str(r[6])})

    def _risk(r, ind):
        sig = safe_str(r[5])
        return {"ind": ind, "val": fmt_val(r[3]), "seuil": safe_str(r[4]) or "—",
                "signal": sig if sig in ("Vert", "Jaune", "Rouge") else "—", "comm": safe_str(r[6])}

    risques_data = _grouped_rows(df, sec.get("risques"), _risk)

    # Canada: dedicated section when present (newer workbooks), otherwise the
    # CANADA rows of the risk section (older workbooks).
    if "canada" in sec:
        def _ca(r, ind):
            sig = safe_str(r[5])
            note = safe_str(r[7])
            tend = safe_str(r[6])
            return {"ind": ind, "val": fmt_val(r[3]), "seuil": safe_str(r[4]) or "—",
                    "signal": sig if sig in ("Vert", "Jaune", "Rouge") else "—",
                    "comm": f"{tend} {note}".strip() if tend and tend != "→" else note}
        canada_data = _grouped_rows(df, sec["canada"], _ca)
    else:
        canada_data = {k: v for k, v in risques_data.items() if k.upper() == "CANADA"}
        risques_data = {k: v for k, v in risques_data.items() if k.upper() != "CANADA"}

    # Fill counts that the workbook does not provide
    for sc_row, groups, key in ((0, hope_data, "signal"), (1, tact_data, "signal"),
                                (2, theses_data, "statut"), (3, risques_data, "signal")):
        if sc_row < len(scorecard) and scorecard[sc_row]["vert"] is None:
            scorecard[sc_row]["vert"], scorecard[sc_row]["jaune"], scorecard[sc_row]["rouge"] = \
                _counts(groups, key)

    ca_v, ca_j, ca_r = _counts(canada_data)
    total_ca = ca_v + ca_j + ca_r
    ca_score = int((ca_v + 0.5 * ca_j) / total_ca * 100) if total_ca else 0
    insert_at = next((i for i, s_ in enumerate(scorecard) if s_["cat"] == "SCORE GLOBAL"), len(scorecard))
    scorecard.insert(insert_at, {
        "cat": "Canada", "score": ca_score, "trend": "→",
        "vert": ca_v, "jaune": ca_j, "rouge": ca_r, "color": "#EF4444",
    })

    # Matrice probabilité / impact
    matrice = []
    if "matrice" in sec:
        a, b = sec["matrice"]
        for ri in range(a, b + 1):
            row = df.iloc[ri]
            risque = safe_str(row[1])
            if not risque:
                continue
            matrice.append({"risque": risque, "prob": _int(row[2]), "impact": _int(row[3]),
                            "score": _int(row[4]), "plan": safe_str(row[5])})

    return date_str, scorecard, hope_data, tact_data, theses_data, risques_data, canada_data, matrice


# ── Fallback hardcoded data ────────────────────────────────────────────────────
_SCORECARD_DEFAULT = [
    {"cat": "Cycle HOPE",        "score": 63, "trend": "→", "vert": 10, "jaune": 4,  "rouge": 5,  "color": "#60A5FA"},
    {"cat": "Signaux Tactiques", "score": 50, "trend": "→", "vert": 7,  "jaune": 4,  "rouge": 7,  "color": "#F59E0B"},
    {"cat": "Thèses Clés",       "score": 71, "trend": "↑", "vert": 11, "jaune": 8,  "rouge": 2,  "color": "#34D399"},
    {"cat": "Alertes Risques",   "score": 79, "trend": "↑", "vert": 12, "jaune": 6,  "rouge": 1,  "color": "#F87171"},
    {"cat": "Canada",            "score": 50, "trend": "→", "vert": 1,  "jaune": 2,  "rouge": 0,  "color": "#EF4444"},
    {"cat": "SCORE GLOBAL",      "score": 66, "trend": "→", "vert": None, "jaune": None, "rouge": None, "color": "#A78BFA"},
]

_HOPE_DEFAULT = {
    "H - Housing": [
        {"ind": "Mises en chantier US (SAAR)",         "val": "1\u202f487", "seuil": ">1.4M",  "signal": "Vert",  "tend": "↑", "note": "Census Bureau, mensuel"},
        {"ind": "Permis de construire US",              "val": "1\u202f376", "seuil": ">1.5M",  "signal": "Jaune", "tend": "↓", "note": "Census Bureau, mensuel"},
        {"ind": "Indice NAHB confiance constructeurs",  "val": "36",    "seuil": ">50",    "signal": "Rouge", "tend": "↓", "note": "NAHB, mensuel"},
        {"ind": "Ventes maisons existantes (YoY%)",     "val": "4.09",  "seuil": ">0%",    "signal": "Jaune", "tend": "↑", "note": "NAR, mensuel"},
        {"ind": "Case-Shiller 20 villes (YoY%)",        "val": "1.38",  "seuil": "—",      "signal": "Jaune", "tend": "↓", "note": "S&P, mensuel avec délai"},
    ],
    "O - Orders": [
        {"ind": "ISM Manufacturing PMI",                "val": "52.4",  "seuil": ">50",    "signal": "Vert",  "tend": "↓", "note": "ISM, 1er jour ouvrable du mois"},
        {"ind": "ISM New Orders",                       "val": "8",     "seuil": ">50",    "signal": "Rouge", "tend": "↑", "note": "ISM, composante clé"},
        {"ind": "Ratio New Orders/Inventories",         "val": "—",     "seuil": ">1.0",   "signal": "Vert",  "tend": "↑", "note": "NAPMNOI/NAPMII"},
        {"ind": "PMI Manufacturier Global",             "val": "51.9",  "seuil": ">50",    "signal": "Vert",  "tend": "↑", "note": "S&P Global/JPM"},
        {"ind": "Commandes biens durables (MoM%)",      "val": "−1.4",  "seuil": ">0%",    "signal": "Jaune", "tend": "↓", "note": "Census Bureau"},
    ],
    "P - Profits": [
        {"ind": "Croissance BPA S&P 500 (YoY%)",        "val": "13.64", "seuil": ">10%",   "signal": "Vert",  "tend": "↑", "note": "Bloomberg consensus"},
        {"ind": "Marge nette S&P 500",                  "val": "3.78",  "seuil": ">11%",   "signal": "Rouge", "tend": "↓", "note": "Proxy: Earnings Yield"},
        {"ind": "Révisions BPA (3 mois)",               "val": "29.4",  "seuil": ">0",     "signal": "Vert",  "tend": "↑", "note": "Bloomberg, net révisions"},
        {"ind": "Croissance revenus S&P 500 (YoY%)",    "val": "−1.02", "seuil": ">5%",    "signal": "Rouge", "tend": "↑", "note": "Proxy: SPX YTD %"},
    ],
    "E - Employment": [
        {"ind": "Emplois non-agricoles (variation)",    "val": "−92",   "seuil": "—",      "signal": "Rouge", "tend": "↓", "note": "BLS, 1er vendredi du mois"},
        {"ind": "Taux de chômage U3",                   "val": "4.4",   "seuil": "<4.5%",  "signal": "Vert",  "tend": "↑", "note": "BLS"},
        {"ind": "Taux de chômage U6",                   "val": "7.9",   "seuil": "—",      "signal": "Vert",  "tend": "↓", "note": "BLS, mesure élargie"},
        {"ind": "Initial Jobless Claims (4wk avg)",     "val": "212",   "seuil": "<250K",  "signal": "Vert",  "tend": "↑", "note": "DOL, hebdomadaire"},
        {"ind": "JOLTS Job Openings",                   "val": "6\u202f542", "seuil": "—", "signal": "Vert",  "tend": "↓", "note": "BLS, avec délai"},
    ],
}

_TACT_DEFAULT = {
    "VALORISATIONS": [
        {"ind": "P/E Forward S&P 500",              "val": "21.47", "comp": "26.49", "cible": "<18x",     "signal": "Jaune", "impl": "21x fwd vs 26x trailing — marge de sécurité faible"},
        {"ind": "P/E Forward Russell 2000",         "val": "25.67", "comp": "48.72", "cible": "<15x",     "signal": "Rouge", "impl": "26x fwd vs 49x trailing — vulnérable si BPA déçoit"},
        {"ind": "Écart P/E (SPX − RTY)",            "val": "−4.20", "comp": "−22.23","cible": "<3x",      "signal": "Vert",  "impl": "SPX moins cher que RTY fwd: rare, favorise large caps"},
        {"ind": "P/E MSCI EAFE",                    "val": "16.20", "comp": "18.24", "cible": "<14x",     "signal": "Jaune", "impl": "Décote ~25% vs SPX, opportunité relative ex-US"},
        {"ind": "P/E MSCI EM",                      "val": "17.25", "comp": "18.42", "cible": "<12x",     "signal": "Rouge", "impl": "Plus cher qu'historique EM (~12x), sélectivité requise"},
        {"ind": "Equity Risk Premium (ERP)",        "val": "0.416", "comp": "4.5",   "cible": ">4%",      "signal": "Rouge", "impl": "ERP 0.4% vs moy. 4.5% — actions non rémunérées"},
    ],
    "MOMENTUM ETF": [
        {"ind": "IWM (Small Cap) 1M%",              "val": "−4.12", "comp": "+2.72", "cible": ">+2%",     "signal": "Rouge", "impl": "Prise de profit CT, tendance YTD intacte"},
        {"ind": "IVE (Value) 1M%",                  "val": "−2.74", "comp": "+0.43", "cible": ">+2%",     "signal": "Rouge", "impl": "Rotation value en pause, pas de conviction"},
        {"ind": "EEM (EM) 1M%",                     "val": "−4.85", "comp": "+5.85", "cible": ">+2%",     "signal": "Rouge", "impl": "Correction CT, flux YTD encore positifs"},
        {"ind": "DBC (Commodités) 1M%",             "val": "+20.38","comp": "+28.18","cible": ">+2%",      "signal": "Vert",  "impl": "Forte accélération, thèse rareté validée"},
    ],
    "CRÉDIT": [
        {"ind": "Spread HY US (OAS)",               "val": "2.94",  "comp": "11.79", "cible": "<350 bps", "signal": "Vert",  "impl": "294 bps, +12% 1M — sous moy. 5Y, crédit sain"},
        {"ind": "Spread IG US (OAS)",               "val": "0.86",  "comp": "14.67", "cible": "<100 bps", "signal": "Vert",  "impl": "86 bps, +15% 1M — stress modéré, pas d'alerte"},
        {"ind": "Spread EM Souverain",              "val": "−0.66", "comp": "+5.06", "cible": ">0% YTD",  "signal": "Rouge", "impl": "EMB négatif YTD — dette EM sous pression CT"},
        {"ind": "Ratio BB/CCC dans HY",             "val": "0.133", "comp": "0.969", "cible": "<2.5x",    "signal": "Vert",  "impl": "Forte compression qualité dans le HY"},
    ],
    "MOMENTUM": [
        {"ind": "RSI S&P 500 (14 jours)",           "val": "42.40", "comp": "46.56", "cible": "30–70",    "signal": "Vert",  "impl": "Zone neutre-basse, pas de signal extrême"},
        {"ind": "S&P 500 vs MA 200 jours",          "val": "+2.72", "comp": "−1.72", "cible": ">0%",      "signal": "Vert",  "impl": "Tendance LT haussière, CT fragile vs MA50"},
        {"ind": "VIX",                              "val": "26.09", "comp": "23.49", "cible": "<20",      "signal": "Jaune", "impl": "+23% 1M — couverture recommandée"},
        {"ind": "Breadth: % actions > MA50",        "val": "53.44", "comp": "−1.27", "cible": ">60%",     "signal": "Jaune", "impl": "Participation se rétrécit — surveiller si <47%"},
    ],
}

_THESES_DEFAULT = {
    "IA - COUCHE 1: ÉNERGIE": [
        {"ind": "Capex utilities US (YoY%)",               "val": "8.15",  "cible": ">10%",       "statut": "Jaune", "note": ""},
        {"ind": "Prix uranium spot ($/lb)",                "val": "85.7",  "cible": ">$80/lb",    "statut": "Vert",  "note": "Proxy: URA ETF ou Cameco"},
        {"ind": "Prix gaz naturel Henry Hub",              "val": "3.21",  "cible": ">$3.50",     "statut": "Jaune", "note": "Coût énergie data centers"},
    ],
    "IA - COUCHE 2: PUCES": [
        {"ind": "Revenus NVIDIA (YoY%)",                   "val": "65.47", "cible": ">20%",       "statut": "Vert",  "note": "Earnings trimestriels"},
        {"ind": "Ratio book-to-bill semiconducteurs",      "val": "9.57",  "cible": ">1.0",       "statut": "Vert",  "note": "SIA data"},
    ],
    "IA - COUCHE 3: INFRASTRUCTURE": [
        {"ind": "Capex hyperscalers (AMZN+GOOG+MSFT+META)","val": "−6.67","cible": ">+30% YTD",  "statut": "Rouge", "note": "Guidance trimestrielle"},
        {"ind": "Performance Vertiv/Quanta/EQIX",          "val": "42.38", "cible": ">+10% YTD",  "statut": "Vert",  "note": "Bénéficiaires directs"},
    ],
    "IA - COUCHE 5: APPLICATIONS": [
        {"ind": "Croissance revenus cloud (AWS+Azure+GCP)","val": "−17.64","cible": ">25%",       "statut": "Rouge", "note": "Adoption entreprise"},
    ],
    "GREAT BROADENING": [
        {"ind": "Performance relative RTY vs SPX (YTD)",   "val": "3.48",  "cible": ">0%",        "statut": "Vert",  "note": "Rotation small caps"},
        {"ind": "Breadth: % secteurs S&P en hausse",       "val": "53.44", "cible": ">53% (proxy)","statut": "Vert",  "note": "RSP−SPY+50. >53 = participation large"},
        {"ind": "S&P Equal Weight vs Cap Weight (YTD)",    "val": "3.44",  "cible": ">0%",        "statut": "Vert",  "note": "RSP vs SPY"},
    ],
    "COMMODITÉS - RARETÉ": [
        {"ind": "Prix cuivre ($/tonne LME)",               "val": "13\u202f042","cible": ">$9 500/t",  "statut": "Vert",  "note": ">$9 500 favorable"},
        {"ind": "Prix argent ($/oz)",                      "val": "86.54", "cible": ">$28/oz",    "statut": "Vert",  "note": "Demande industrielle"},
        {"ind": "Inventaires cuivre LME (tonnes)",         "val": "12\u202f940","cible": "Déclin",     "statut": "Jaune", "note": "Niveau stocks critiques"},
        {"ind": "Capex minières (majors)",                 "val": "14.49", "cible": ">+10% YTD",  "statut": "Vert",  "note": "Sous-investissement chronique"},
    ],
    "STIMULUS FISCAL US": [
        {"ind": "Performance small caps US (IWM YTD)",     "val": "2.72",  "cible": ">+10% YTD",  "statut": "Jaune", "note": "Small caps domestiques = 1ers bénéficiaires"},
        {"ind": "Performance industrielles US (XLI YTD)", "val": "9.26",  "cible": ">+10% YTD",  "statut": "Jaune", "note": "Exposition infra / dépenses gouvernementales"},
        {"ind": "Consumer Confidence (Conference Board)",  "val": "91.2",  "cible": ">100",        "statut": "Jaune", "note": "Effet richesse stimulus sur ménages"},
        {"ind": "Rendement 10Y US",                        "val": "4.24",  "cible": "<4.50%",      "statut": "Vert",  "note": "Risque crowding out si >5%"},
    ],
    "SANTÉ / BIOTECH": [
        {"ind": "Performance XBI (Biotech ETF)",           "val": "3.65",  "cible": ">+10% YTD",  "statut": "Jaune", "note": "Thèse IA + Drug discovery"},
        {"ind": "Approbations FDA (rolling 12m)",          "val": "1.24",  "cible": ">+5% YTD",   "statut": "Jaune", "note": "Proxy: IBB ETF YTD%"},
    ],
}

_RISQUES_DEFAULT = {
    "INFLATION": [
        {"ind": "CPI Core US (YoY%)",               "val": "2.5",   "seuil": ">3.0%",     "signal": "Jaune", "comm": "Fed target 2%"},
        {"ind": "PCE Core (YoY%)",                  "val": "3.00",  "seuil": ">3.0%",     "signal": "Jaune", "comm": "Mesure préférée Fed"},
        {"ind": "Inflation anticipée 5Y5Y",         "val": "2.18",  "seuil": ">2.5%",     "signal": "Vert",  "comm": "Anticipations long terme"},
        {"ind": "Salaires horaires (YoY%)",         "val": "3.8",   "seuil": ">4.0%",     "signal": "Jaune", "comm": "Pression salariale"},
    ],
    "TAUX / YIELDS": [
        {"ind": "Rendement 10 ans US",              "val": "4.24",  "seuil": ">5.0%",     "signal": "Vert",  "comm": "Bond vigilantes"},
        {"ind": "Rendement 2 ans US",               "val": "3.67",  "seuil": ">5.0%",     "signal": "Vert",  "comm": "Attentes Fed"},
        {"ind": "Spread 10Y−2Y (courbe)",           "val": "56.56", "seuil": "<−50bps",   "signal": "Vert",  "comm": "Inversion = risque récession"},
        {"ind": "Rendement réel 10Y TIPS",          "val": "1.84",  "seuil": ">2.5%",     "signal": "Vert",  "comm": "Coût réel du capital"},
        {"ind": "Fed Funds futures (dec 2026)",     "val": "96.37", "seuil": "<95.50",    "signal": "Vert",  "comm": "Trajectoire anticipée"},
    ],
    "CRÉDIT / LIQUIDITÉ": [
        {"ind": "Spread TED",                       "val": "1.17",  "seuil": ">50bps",    "signal": "Vert",  "comm": "Stress interbancaire"},
        {"ind": "Réserves bancaires Fed",           "val": "6\u202f628\u202f894","seuil": "<6 000 000","signal": "Vert","comm": "Liquidité système"},
        {"ind": "Taux défaut HY (12m trailing)",    "val": "2.94",  "seuil": ">500 bps",  "signal": "Vert",  "comm": "Stress crédit"},
    ],
    "GÉOPOLITIQUE": [
        {"ind": "Indice incertitude politique US",  "val": "269.1", "seuil": ">200",      "signal": "Rouge", "comm": "Baker-Bloom-Davis"},
        {"ind": "Prix pétrole Brent ($/bbl)",       "val": "98.9",  "seuil": ">$100",     "signal": "Jaune", "comm": "Choc pétrolier"},
        {"ind": "USD Index (DXY)",                  "val": "99.51", "seuil": ">110",      "signal": "Vert",  "comm": "Force dollar"},
        {"ind": "USD/CNY",                          "val": "6.87",  "seuil": ">7.5",      "signal": "Vert",  "comm": "Tensions Chine"},
    ],
}

_CANADA_DEFAULT = {
    "CANADA": [
        {"ind": "Écart taux 10Y CA−US",              "val": "−0.75", "seuil": "<−1.0%",   "signal": "Jaune", "comm": "Divergence politique monétaire"},
        {"ind": "CAD/USD",                           "val": "0.735", "seuil": "<0.70",     "signal": "Jaune", "comm": "Faiblesse dollar canadien"},
        {"ind": "Renouvellements hypothécaires 2026","val": "—",     "seuil": "Qualitatif","signal": "—",     "comm": "Mur hypothécaire à surveiller"},
        {"ind": "Indice TSX vs S&P 500 (rel perf)",  "val": "5.46",  "seuil": "<−10%",    "signal": "Vert",  "comm": "Sous-performance Canada"},
    ],
}

_MATRICE_DEFAULT = [
    {"risque": "Inflation collante (>3%)",             "prob": 0, "impact": 0, "score": 0, "plan": ""},
    {"risque": "Hausse yields obligataires (>5%)",     "prob": 0, "impact": 0, "score": 0, "plan": ""},
    {"risque": "Retard productivité IA",               "prob": 0, "impact": 0, "score": 0, "plan": ""},
    {"risque": "Escalade guerre commerciale",          "prob": 0, "impact": 0, "score": 0, "plan": ""},
    {"risque": "Récession Canada (mur hypothécaire)",  "prob": 0, "impact": 0, "score": 0, "plan": ""},
]

# ── Sidebar — Upload ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📁 Mise à jour des données")
    st.markdown(
        "<span style='font-size:0.75rem;color:#6B7280;'>"
        "Glissez votre fichier Bloomberg mis à jour pour rafraîchir tous les indicateurs."
        "</span>",
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader(
        "Fichier Excel (.xlsx)",
        type=["xlsx"],
        help="Doit contenir l'onglet 'Snapshot' (Tableau_Bord_Fondaction_Bloomberg.xlsx)",
    )
    if uploaded:
        raw = uploaded.read()
        # Seulement re-parser si le fichier a changé (comparaison par taille)
        if raw != st.session_state.get("snap_file"):
            st.session_state["snap_file"] = raw
            st.session_state["snap_name"] = uploaded.name
            st.session_state["snap_error"] = None
            st.rerun()  # Force un re-render complet de la page
        st.success(f"✓ {uploaded.name}")
    elif "snap_name" in st.session_state:
        st.info(f"📄 En mémoire : {st.session_state['snap_name']}")
    else:
        st.caption("Aucun fichier chargé — snapshot embarqué (dernier fichier Bloomberg publié).")

    # Afficher erreur de parsing si elle existe
    if st.session_state.get("snap_error"):
        st.error(f"⚠️ Erreur : {st.session_state['snap_error']}")

    st.markdown("---")
    st.markdown(
        "<span style='font-size:0.65rem;color:#4B5563;'>"
        "L'onglet Snapshot de votre fichier Excel est parsé automatiquement.<br>"
        "Sauvegardez le fichier avant l'upload."
        "</span>",
        unsafe_allow_html=True,
    )

# ── Load data (uploaded or fallback) ─────────────────────────────────────────
_parse_ok = False
if "snap_file" in st.session_state:
    try:
        date_str, SCORECARD, HOPE_DATA, TACT_DATA, THESES_DATA, RISQUES_DATA, CANADA_DATA, MATRICE = \
            parse_snapshot(st.session_state["snap_file"])
        data_src = st.session_state.get("snap_name", "fichier uploadé")
        st.session_state["snap_error"] = None
        _parse_ok = True
    except Exception as exc:
        err_msg = str(exc)
        st.session_state["snap_error"] = err_msg
        st.error(f"⚠️ Erreur de lecture du fichier — vérifiez que l'onglet **Snapshot** existe : `{err_msg}`")
        date_str, SCORECARD, HOPE_DATA, TACT_DATA, THESES_DATA = \
            "12 mars 2026", _SCORECARD_DEFAULT, _HOPE_DEFAULT, _TACT_DEFAULT, _THESES_DEFAULT
        RISQUES_DATA, CANADA_DATA, MATRICE = _RISQUES_DEFAULT, _CANADA_DEFAULT, _MATRICE_DEFAULT
        data_src = "fallback (erreur de lecture)"

_BUNDLED = Path(__file__).resolve().parent.parent / "data" / "fondaction_snapshot.json"
if not _parse_ok and "snap_file" not in st.session_state and _BUNDLED.exists():
    try:
        _b = json.loads(_BUNDLED.read_text(encoding="utf-8"))
        date_str, SCORECARD, HOPE_DATA, TACT_DATA = _b["date"], _b["score"], _b["hope"], _b["tact"]
        THESES_DATA, RISQUES_DATA, CANADA_DATA, MATRICE = _b["theses"], _b["risques"], _b["canada"], _b["matrice"]
        data_src = _b.get("source", "data/fondaction_snapshot.json")
        if _b.get("generated_utc"):
            _st = _b.get("stats", {})
            data_src += f"<br>Généré {_b['generated_utc']} · {_st.get('manual', 0)} saisies manuelles"
            if _st.get("stale"):
                data_src += f" · ⚠ {_st['stale']} non rafraîchis"
        _parse_ok = True
    except Exception as exc:  # fall back to the hard-coded March 2026 snapshot
        st.warning(f"Snapshot embarqué illisible ({exc}) — affichage des données du 12 mars 2026.")

if not _parse_ok and "snap_file" not in st.session_state:
    date_str = "12 mars 2026"
    SCORECARD = _SCORECARD_DEFAULT
    HOPE_DATA = _HOPE_DEFAULT
    TACT_DATA = _TACT_DEFAULT
    THESES_DATA = _THESES_DEFAULT
    RISQUES_DATA = _RISQUES_DEFAULT
    CANADA_DATA = _CANADA_DEFAULT
    MATRICE = _MATRICE_DEFAULT
    data_src = "Tableau_Bord_Fondaction_Bloomberg-3.xlsx"

# ── Header ────────────────────────────────────────────────────────────────────
st.html(f"""
<div style="display:flex;align-items:center;justify-content:space-between;
            border-bottom:1px solid #1F2937;padding-bottom:12px;margin-bottom:16px;">
  <div>
    <div class="snap-title">📊 TABLEAU DE BORD FONDACTION</div>
    <div class="snap-sub">Snapshot Veille Marchés &nbsp;·&nbsp;
      <span style="color:#10B981;">●</span>&nbsp;Dernière mise à jour:
      <strong style="color:#F9FAFB;">{date_str}</strong>
    </div>
  </div>
  <div style="font-size:0.7rem;color:#6B7280;text-align:right;">
    Source: {data_src}<br>
    <span style="color:#374151;">← Sidebar pour mettre à jour</span>
  </div>
</div>
""")

# ── Scorecard Global ──────────────────────────────────────────────────────────
total_ind = (sum(len(v) for v in HOPE_DATA.values()) +
             sum(len(v) for v in TACT_DATA.values()) +
             sum(len(v) for v in THESES_DATA.values()) +
             sum(len(v) for v in RISQUES_DATA.values()) +
             sum(len(v) for v in CANADA_DATA.values()))

st.html(f'<p class="section-hdr">Scorecard Global — {total_ind} indicateurs</p>')
cols = st.columns(6)
for col, d in zip(cols, SCORECARD):
    with col:
        st.plotly_chart(gauge_fig(d["score"], d["color"], d["cat"]),
                        use_container_width=True, key=f"g_{d['cat']}")
        if d["vert"] is not None:
            sig_html = (
                f'<span class="sig-vert">✓ {d["vert"]}</span>&nbsp;'
                f'<span class="sig-jaune">⚠ {d["jaune"]}</span>&nbsp;'
                f'<span class="sig-rouge">✕ {d["rouge"]}</span>'
            )
        else:
            tc = {"→": "#FBBF24", "↑": "#34D399", "↓": "#F87171"}.get(d["trend"], "#9CA3AF")
            sig_html = (
                f'<span style="color:{tc};font-size:1rem;">{d["trend"]}</span>'
                f'<span style="color:#6B7280;font-size:0.7rem;"> Tendance</span>'
            )
        st.html(f'<div style="text-align:center;margin-top:-8px;">{sig_html}</div>')

st.html('<hr style="border:none;border-top:1px solid #1F2937;margin:8px 0 16px;">')

# ── Dynamic tab labels ────────────────────────────────────────────────────────
sc = {d["cat"]: d for d in SCORECARD}
h_s  = sc.get("Cycle HOPE", {}).get("score", 63)
t_s  = sc.get("Signaux Tactiques", {}).get("score", 50)
th_s = sc.get("Thèses Clés", {}).get("score", 71)
r_s  = sc.get("Alertes Risques", {}).get("score", 79)
ca_s = sc.get("Canada", {}).get("score", 50)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    f"🏗️  HOPE — Cycle ({h_s}/100)",
    f"📈  Signaux Tactiques ({t_s}/100)",
    f"💡  Thèses Clés ({th_s}/100)",
    f"⚠️  Alertes Risques ({r_s}/100)",
    f"🍁  Canada ({ca_s}/100)",
])

# ── TAB 1 : HOPE ─────────────────────────────────────────────────────────────
with tab1:
    hope_all = [r for rows in HOPE_DATA.values() for r in rows]
    hv = sum(1 for r in hope_all if r["signal"] == "Vert")
    hj = sum(1 for r in hope_all if r["signal"] == "Jaune")
    hr = sum(1 for r in hope_all if r["signal"] == "Rouge")
    st.html(f'<p class="section-hdr">{len(hope_all)} indicateurs — {hv} Verts · {hj} Jaunes · {hr} Rouges</p>')
    for section, rows in HOPE_DATA.items():
        st.html(f'<div class="subsec-hdr">{section}</div>')
        html = ""
        for r in rows:
            tc = tend_cls(r["tend"])
            html += f"""
            <div class="ind-row">
              <span class="ind-name">{r["ind"]}</span>
              <span class="ind-val">{r["val"]}</span>
              <span class="ind-seuil">{r["seuil"]}</span>
              {sig_badge(r["signal"])}
              <span class="ind-tend {tc}">{r["tend"]}</span>
              <span class="ind-note">{r["note"]}{src_tag(r)}</span>
            </div>"""
        st.html(html)

# ── TAB 2 : SIGNAUX TACTIQUES ─────────────────────────────────────────────────
with tab2:
    tact_all = [r for rows in TACT_DATA.values() for r in rows]
    tv = sum(1 for r in tact_all if r["signal"] == "Vert")
    tj = sum(1 for r in tact_all if r["signal"] == "Jaune")
    tr_ = sum(1 for r in tact_all if r["signal"] == "Rouge")
    st.html(f'<p class="section-hdr">{len(tact_all)} indicateurs — {tv} Verts · {tj} Jaunes · {tr_} Rouges</p>')
    col_a, col_b = st.columns(2)
    for i, (section, rows) in enumerate(TACT_DATA.items()):
        col = col_a if i % 2 == 0 else col_b
        with col:
            st.html(f'<div class="subsec-hdr">{section}</div>')
            html = ""
            for r in rows:
                html += f"""
                <div class="ind-row" style="flex-wrap:wrap;gap:8px;">
                  <span class="ind-name" style="flex:2;">{r["ind"]}</span>
                  <span class="ind-val">{r["val"]}</span>
                  <span class="ind-seuil">{r["cible"]}</span>
                  {sig_badge(r["signal"])}
                  <span class="ind-note" style="flex:100%;padding-top:4px;
                    color:#374151;font-size:0.7rem;">{r["impl"]}{src_tag(r)}</span>
                </div>"""
            st.html(html)

# ── TAB 3 : THÈSES ───────────────────────────────────────────────────────────
with tab3:
    theses_all = [r for rows in THESES_DATA.values() for r in rows]
    thv = sum(1 for r in theses_all if r["statut"] == "Vert")
    thj = sum(1 for r in theses_all if r["statut"] == "Jaune")
    thr = sum(1 for r in theses_all if r["statut"] == "Rouge")
    st.html(f'<p class="section-hdr">{len(theses_all)} indicateurs — {thv} Verts · {thj} Jaunes · {thr} Rouges</p>')
    col_a, col_b = st.columns(2)
    for i, (section, rows) in enumerate(THESES_DATA.items()):
        col = col_a if i % 2 == 0 else col_b
        with col:
            st.html(f'<div class="subsec-hdr">{section}</div>')
            html = ""
            for r in rows:
                html += f"""
                <div class="ind-row">
                  <span class="ind-name" style="flex:2.5;">{r["ind"]}</span>
                  <span class="ind-val">{r["val"]}</span>
                  <span class="ind-seuil">{r["cible"]}</span>
                  {sig_badge(r["statut"])}
                  <span class="ind-note" style="flex:2.5;">{r["note"]}{src_tag(r)}</span>
                </div>"""
            st.html(html)

# ── TAB 4 : ALERTES RISQUES ──────────────────────────────────────────────────
with tab4:
    risques_all = [r for rows in RISQUES_DATA.values() for r in rows]
    rv = sum(1 for r in risques_all if r["signal"] == "Vert")
    rj = sum(1 for r in risques_all if r["signal"] == "Jaune")
    rr = sum(1 for r in risques_all if r["signal"] == "Rouge")
    st.html(f'<p class="section-hdr">{len(risques_all)} indicateurs — {rv} Verts · {rj} Jaunes · {rr} Rouges</p>')
    col_a, col_b = st.columns(2)
    for i, (section, rows) in enumerate(RISQUES_DATA.items()):
        col = col_a if i % 2 == 0 else col_b
        with col:
            st.html(f'<div class="subsec-hdr">{section}</div>')
            html = ""
            for r in rows:
                html += f"""
                <div class="ind-row">
                  <span class="ind-name">{r["ind"]}</span>
                  <span class="ind-val">{r["val"]}</span>
                  <span class="ind-seuil">{r["seuil"]}</span>
                  {sig_badge(r["signal"])}
                  <span class="ind-note" style="flex:2;text-align:left;">{r["comm"]}{src_tag(r)}</span>
                </div>"""
            st.html(html)

    # Matrice probabilité / impact
    st.html("""
    <div class="subsec-hdr" style="margin-top:20px;">
      Matrice Probabilité × Impact
    </div>""")
    mat_html = """
    <div class="ind-row" style="background:#0F172A;font-size:0.62rem;
         color:#4B5563;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;">
      <span style="flex:4;">Risque</span>
      <span class="mat-val">Prob. (1-5)</span>
      <span class="mat-val">Impact (1-5)</span>
      <span class="mat-val">Score</span>
      <span style="flex:3;font-size:0.62rem;">Plan de contingence</span>
    </div>"""
    for m in MATRICE:
        p_disp = str(m["prob"])   if m["prob"]   > 0 else "—"
        i_disp = str(m["impact"]) if m["impact"] > 0 else "—"
        s_val  = m["score"]
        if s_val >= 16:
            s_cls, s_disp = "mat-score-hi",  str(s_val)
        elif s_val >= 9:
            s_cls, s_disp = "mat-score-med", str(s_val)
        elif s_val > 0:
            s_cls, s_disp = "mat-score-lo",  str(s_val)
        else:
            s_cls, s_disp = "mat-score-0",   "—"
        plan_disp = m["plan"] if m["plan"] else "<em style='color:#1F2937;'>À remplir</em>"
        mat_html += f"""
        <div class="ind-row">
          <span class="ind-name" style="flex:4;">{m["risque"]}</span>
          <span class="mat-val {s_cls if p_disp != '—' else 'mat-score-0'}">{p_disp}</span>
          <span class="mat-val {s_cls if i_disp != '—' else 'mat-score-0'}">{i_disp}</span>
          <span class="mat-val {s_cls}">{s_disp}</span>
          <span style="flex:3;font-size:0.65rem;color:#6B7280;">{plan_disp}</span>
        </div>"""
    st.html(mat_html)

# ── TAB 5 : CANADA ───────────────────────────────────────────────────────────
with tab5:
    ca_all = [r for rows in CANADA_DATA.values() for r in rows]
    ca_v_t = sum(1 for r in ca_all if r["signal"] == "Vert")
    ca_j_t = sum(1 for r in ca_all if r["signal"] == "Jaune")
    ca_r_t = sum(1 for r in ca_all if r["signal"] == "Rouge")
    st.html(f'<p class="section-hdr">{len(ca_all)} indicateurs — {ca_v_t} Verts · {ca_j_t} Jaunes · {ca_r_t} Rouges</p>')
    for section, rows in CANADA_DATA.items():
        st.html(f'<div class="subsec-hdr">{section}</div>')
        html = ""
        for r in rows:
            html += f"""
            <div class="ind-row">
              <span class="ind-name">{r["ind"]}</span>
              <span class="ind-val">{r["val"]}</span>
              <span class="ind-seuil">{r["seuil"]}</span>
              {sig_badge(r["signal"])}
              <span class="ind-note" style="flex:2;text-align:left;">{r["comm"]}{src_tag(r)}</span>
            </div>"""
        st.html(html)
