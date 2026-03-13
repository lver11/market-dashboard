"""
Fondaction Bloomberg Snapshot Dashboard — Streamlit Page
Données: Tableau_Bord_Fondaction_Bloomberg-1.xlsx (onglet Snapshot)
Mise à jour: 2026-03-12
"""

import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Fondaction — Snapshot Marchés",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.html("""
<style>
  [data-testid="stAppViewContainer"] { background: #0B1120; }
  [data-testid="stHeader"] { background: transparent; }
  section[data-testid="stSidebar"] { background: #111827; }
  h1,h2,h3,h4,p,div,span,label { color: #F9FAFB !important; }
  .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
  div[data-testid="metric-container"] {
    background: #111827; border: 1px solid #374151;
    border-radius: 10px; padding: 16px;
  }
  .section-hdr {
    font-size:0.65rem; letter-spacing:0.18em; text-transform:uppercase;
    color:#6B7280; background:#1F2937; border-radius:4px;
    padding:4px 12px; display:inline-block;
  }
  .rule-box { border-radius:10px; padding:14px 18px; margin:4px 0; }
</style>
""")

# ── Data ──────────────────────────────────────────────────────────────────────
SCORES = {
    "Cycle HOPE":        {"score": 63, "trend": "→", "vert": 9,  "jaune": 4,  "rouge": 6,  "color": "#60A5FA"},
    "Signaux Tactiques": {"score": 50, "trend": "→", "vert": 7,  "jaune": 4,  "rouge": 7,  "color": "#F59E0B"},
    "Thèses Clés":       {"score": 71, "trend": "↑", "vert": 10, "jaune": 8,  "rouge": 3,  "color": "#10B981"},
    "Alertes Risques":   {"score": 79, "trend": "↑", "vert": 11, "jaune": 6,  "rouge": 1,  "color": "#10B981"},
    "SCORE GLOBAL":      {"score": 66, "trend": "→", "vert": 37, "jaune": 22, "rouge": 17, "color": "#FBBF24"},
}

HOPE = [
    ("H — Housing",   "Mises en chantier US (SAAR)",          "1 487k",   ">1.4M",      "↑", "Vert"),
    ("",              "Permis de construire US",               "1 376k",   ">1.5M",      "↓", "Jaune"),
    ("",              "Indice NAHB confiance constructeurs",   "36",       ">50",        "↓", "Rouge"),
    ("",              "Ventes maisons existantes (YoY%)",      "+4.09%",   ">0%",        "↑", "Jaune"),
    ("",              "Indice Case-Shiller 20 villes (YoY%)",  "1.38%",    "—",          "↓", "Jaune"),
    ("O — Orders",    "ISM Manufacturing PMI",                 "52.4",     ">50",        "↓", "Vert"),
    ("",              "ISM New Orders",                        "8",        ">50",        "↑", "Rouge"),
    ("",              "Ratio New Orders/Inventories",          "—",        ">1.0",       "↑", "Vert"),
    ("",              "PMI Manufacturier Global",              "51.9",     ">50",        "↑", "Vert"),
    ("",              "Commandes biens durables (MoM%)",       "-1.4%",    ">0%",        "↓", "Jaune"),
    ("P — Profits",   "Croissance BPA S&P 500 (YoY%)",        "+13.64%",  ">10%",       "↑", "Vert"),
    ("",              "Marge nette S&P 500",                   "3.78%",    ">11%",       "↓", "Rouge"),
    ("",              "Révisions BPA (3 mois)",                "+29.4",    ">0",         "↑", "Vert"),
    ("",              "Croissance revenus S&P 500 (YoY%)",     "-1.02%",   ">5%",        "↑", "Rouge"),
    ("E — Employment","Emplois non-agricoles (variation)",     "-92k",     "—",          "↓", "Rouge"),
    ("",              "Taux de chômage U3",                    "4.4%",     "<4.5%",      "↑", "Vert"),
    ("",              "Taux de chômage U6",                    "7.9%",     "—",          "↓", "Vert"),
    ("",              "Initial Jobless Claims (4wk avg)",      "212k",     "<250K",      "↑", "Vert"),
    ("",              "JOLTS Job Openings",                    "6 542k",   "—",          "↓", "Vert"),
]

TACTIQUE = [
    ("Valorisations", "P/E Forward S&P 500",                  "21.5x",    "26.5x trail.", "<18x",    "Jaune"),
    ("",              "P/E Forward Russell 2000",              "25.7x",    "48.7x trail.", "<15x",    "Rouge"),
    ("",              "Écart P/E (SPX - RTY)",                "-4.2x",    "-22.2x trail.","<3x",     "Vert"),
    ("",              "P/E MSCI EAFE",                         "16.2x",    "18.2x trail.", "<14x",    "Jaune"),
    ("",              "P/E MSCI EM",                           "17.3x",    "18.4x trail.", "<12x",    "Rouge"),
    ("",              "Equity Risk Premium (ERP)",             "0.42%",    "Moy. 4.5%",   ">4%",     "Rouge"),
    ("Momentum ETF",  "IWM Small Cap (1M%)",                   "-4.12%",   "YTD: +2.72%", ">+2%",    "Rouge"),
    ("",              "IVE Value (1M%)",                       "-2.74%",   "YTD: +0.43%", ">+2%",    "Rouge"),
    ("",              "EEM EM (1M%)",                          "-4.85%",   "YTD: +5.85%", ">+2%",    "Rouge"),
    ("",              "DBC Commodities (1M%)",                 "+20.38%",  "YTD: +28.18%",">+2%",    "Vert"),
    ("Crédit",        "Spread HY US (OAS)",                    "294 bps",  "Moy.5Y: 400", "<350bps", "Vert"),
    ("",              "Spread IG US (OAS)",                    "86 bps",   "Moy.5Y: 120", "<100bps", "Vert"),
    ("",              "Spread EM Souverain (YTD%)",            "-0.66%",   "1Y: +5.06%",  ">0%",     "Rouge"),
    ("",              "Ratio BB/CCC dans HY",                  "0.13x",    "Moy: 0.97x",  "<2.5x",   "Vert"),
    ("Momentum",      "RSI S&P 500 (14j)",                    "42.4",     "30j: 46.6",   "30–70",   "Vert"),
    ("",              "S&P 500 vs MA 200j",                   "+2.72%",   "vs MA50:-1.7%",">0%",    "Vert"),
    ("",              "VIX",                                   "26.09",    "Moy.1M: 23.5","<20",     "Jaune"),
    ("",              "Breadth: % actions > MA50",             "53.4%",    "1M: -1.27",   ">60%",    "Jaune"),
]

THESES = [
    ("IA — Énergie",      "Capex utilities US (YoY%)",          "8.15%",    ">10%",       "Jaune"),
    ("",                  "Prix uranium spot ($/lb)",            "$85.70",   ">$80/lb",    "Vert"),
    ("",                  "Prix gaz naturel Henry Hub",          "$3.21",    ">$3.50",     "Jaune"),
    ("IA — Puces",        "Revenus NVIDIA (YoY%)",               "+65.5%",   ">20%",       "Vert"),
    ("",                  "Ratio book-to-bill semis",            "9.57",     ">1.0",       "Vert"),
    ("IA — Infra",        "Capex hyperscalers (YTD%)",           "-6.67%",   ">+30%",      "Rouge"),
    ("",                  "Performance Vertiv/Quanta/EQIX",      "+42.4%",   ">+10% YTD",  "Vert"),
    ("IA — Apps",         "Croissance revenus cloud",            "-17.6%",   ">25%",       "Rouge"),
    ("Great Broadening",  "Performance RTY vs SPX (YTD)",        "+3.48%",   ">0%",        "Vert"),
    ("",                  "Breadth: % secteurs S&P en hausse",   "53.4%",    ">53%",       "Vert"),
    ("",                  "S&P Equal Weight vs Cap Weight",       "+3.44%",   ">0%",        "Vert"),
    ("Commodités",        "Prix cuivre ($/t LME)",               "$13 042",  ">$9 500/t",  "Vert"),
    ("",                  "Prix argent ($/oz)",                  "$86.54",   ">$28/oz",    "Vert"),
    ("",                  "Inventaires cuivre LME (t)",          "12 940",   "Déclin",     "Jaune"),
    ("",                  "Capex minières (majors)",             "+14.5%",   ">+10% YTD",  "Vert"),
    ("Stimulus Fiscal US","IWM Small Caps (YTD%)",               "+2.72%",   ">+10% YTD",  "Jaune"),
    ("",                  "XLI Industrielles US (YTD%)",         "+9.26%",   ">+10% YTD",  "Jaune"),
    ("",                  "Consumer Confidence (CB)",            "91.2",     ">100",       "Jaune"),
    ("",                  "Rendement 10Y US",                    "4.24%",    "<4.50%",     "Vert"),
    ("Santé / Biotech",   "XBI Biotech ETF (YTD%)",             "+3.65%",   ">+10% YTD",  "Jaune"),
    ("",                  "Approbations FDA (rolling 12m)",       "+1.24%",   ">+5% YTD",   "Jaune"),
]

RISQUES = [
    ("Inflation",          "CPI Core US (YoY%)",               "2.50%",     ">3.0%",    "Jaune"),
    ("",                   "PCE Core (YoY%)",                   "2.997%",    ">3.0%",    "Jaune"),
    ("",                   "Inflation anticipée 5Y5Y",           "2.18%",     ">2.5%",    "Vert"),
    ("",                   "Salaires horaires (YoY%)",          "3.8%",      ">4.0%",    "Jaune"),
    ("Taux / Yields",      "Rendement 10 ans US",               "4.24%",     ">5.0%",    "Vert"),
    ("",                   "Rendement 2 ans US",                "3.67%",     ">5.0%",    "Vert"),
    ("",                   "Spread 10Y-2Y (courbe)",            "+56.6bps",  "<-50bps",  "Vert"),
    ("",                   "Rendement réel 10Y TIPS",           "1.84%",     ">2.5%",    "Vert"),
    ("",                   "Fed Funds futures (déc 2026)",      "96.37",     "<95.50",   "Vert"),
    ("Crédit / Liquidité", "Spread TED",                        "1.17bps",   ">50bps",   "Vert"),
    ("",                   "Réserves bancaires Fed",            "$6 629B",   "<$6 000B", "Vert"),
    ("",                   "Taux défaut HY (12m)",              "2.94%",     ">500bps",  "Vert"),
    ("Géopolitique",       "Indice incertitude politique US",   "269.1",     ">200",     "Rouge"),
    ("",                   "Prix pétrole Brent",                "$98.9",     ">$100",    "Jaune"),
    ("",                   "USD Index (DXY)",                   "99.5",      ">110",     "Vert"),
    ("",                   "USD/CNY",                           "6.87",      ">7.5",     "Vert"),
    ("Canada",             "Écart taux 10Y CA-US",             "-0.75%",    "<-1.0%",   "Jaune"),
    ("",                   "CAD/USD",                           "0.7349",    "<0.70",    "Jaune"),
    ("",                   "Renouvellements hypothécaires",     "Qualitatif","—",        "Surveiller"),
    ("",                   "TSX vs S&P 500 (rel. perf.)",       "+5.46%",    "<-10%",    "Vert"),
]

# ── Helpers ───────────────────────────────────────────────────────────────────
SIG_COLOR = {"Vert": "#10B981", "Jaune": "#F59E0B", "Rouge": "#EF4444", "Surveiller": "#9CA3AF"}
SIG_EMOJI = {"Vert": "🟢", "Jaune": "🟡", "Rouge": "🔴", "Surveiller": "⚪"}


def gauge_fig(score: int, color: str, label: str) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"font": {"size": 34, "color": color}},
        title={"text": label, "font": {"size": 12, "color": "#9CA3AF"}},
        gauge={
            "axis": {"range": [0, 100], "tickfont": {"color": "#6B7280", "size": 9},
                     "tickwidth": 1, "tickcolor": "#374151"},
            "bar": {"color": color, "thickness": 0.25},
            "bgcolor": "#1F2937",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  50], "color": "rgba(239,68,68,0.08)"},
                {"range": [50, 70], "color": "rgba(245,158,11,0.08)"},
                {"range": [70,100], "color": "rgba(16,185,129,0.08)"},
            ],
            "threshold": {"line": {"color": color, "width": 3}, "thickness": 0.85, "value": score},
        },
    ))
    fig.update_layout(
        height=195, margin=dict(t=38, b=0, l=16, r=16),
        paper_bgcolor="#111827", plot_bgcolor="#111827", font_color="#F9FAFB",
    )
    return fig


def signal_bar_html(vert: int, jaune: int, rouge: int) -> str:
    total = max(vert + jaune + rouge, 1)
    pv, pj = round(vert / total * 100), round(jaune / total * 100)
    pr = 100 - pv - pj
    return f"""
    <div style="display:flex; gap:6px; align-items:center; margin-top:4px;">
      <div style="flex:1; height:7px; border-radius:4px; overflow:hidden; background:#1F2937; display:flex;">
        <div style="width:{pv}%; background:#10B981;"></div>
        <div style="width:{pj}%; background:#F59E0B;"></div>
        <div style="width:{pr}%; background:#EF4444;"></div>
      </div>
      <span style="font-size:0.68rem; color:#10B981; font-weight:700;">{vert}V</span>
      <span style="font-size:0.68rem; color:#F59E0B; font-weight:700;">{jaune}J</span>
      <span style="font-size:0.68rem; color:#EF4444; font-weight:700;">{rouge}R</span>
    </div>"""


def build_table(rows: list, headers: list) -> str:
    TH = ("background:#1F2937; color:#9CA3AF; font-size:0.68rem; "
          "letter-spacing:0.08em; text-transform:uppercase; padding:8px 12px; text-align:left;")
    TD = "padding:7px 12px; font-size:0.81rem; border-bottom:1px solid rgba(55,65,81,0.35);"
    CAT = "color:#93C5FD; font-weight:700; font-size:0.74rem;"

    html = (f'<div style="overflow-x:auto; border-radius:10px; border:1px solid #374151;">'
            f'<table style="width:100%; border-collapse:collapse; background:#111827;">'
            f'<thead><tr>{"".join(f"<th style=\"{TH}\">{h}</th>" for h in headers)}</tr></thead>'
            f'<tbody>')

    for row in rows:
        sig = row[-1]
        c = SIG_COLOR.get(sig, "#6B7280")
        bg = {"Vert":"rgba(16,185,129,0.07)","Jaune":"rgba(245,158,11,0.07)","Rouge":"rgba(239,68,68,0.07)"}.get(sig, "")
        lb = {"Vert":"3px solid #10B981","Jaune":"3px solid #F59E0B","Rouge":"3px solid #EF4444"}.get(sig,"3px solid #374151")
        html += f'<tr style="background:{bg}; border-left:{lb};">'
        for i, cell in enumerate(row):
            is_sig = i == len(row) - 1
            is_cat = i == 0 and str(cell).strip() not in ("", "—")
            val_col = (i == 2)
            if is_sig:
                html += (f'<td style="{TD}"><span style="background:{c}22; color:{c}; '
                         f'border:1px solid {c}66; border-radius:20px; padding:2px 9px; '
                         f'font-size:0.71rem; font-weight:700;">{SIG_EMOJI.get(sig,"")} {cell}</span></td>')
            elif is_cat:
                html += f'<td style="{TD} {CAT}">{cell}</td>'
            elif val_col:
                html += f'<td style="{TD} color:{c}; font-weight:700;">{cell}</td>'
            else:
                style = TD + ("color:#6B7280; font-size:0.74rem;" if i >= 3 else "")
                html += f'<td style="{style}">{cell}</td>'
        html += "</tr>"

    html += "</tbody></table></div>"
    return html


# ═══════════════════════════════════════════════════════════════
# RENDER
# ═══════════════════════════════════════════════════════════════

# Header
st.markdown("""
<div style="background:#111827; border:1px solid #1F2937; border-radius:12px;
            padding:18px 24px; margin-bottom:24px; display:flex; align-items:center; gap:16px;">
  <div style="width:42px; height:42px; border-radius:10px; flex-shrink:0;
              background:linear-gradient(135deg,#1D4ED8,#7C3AED);
              display:flex; align-items:center; justify-content:center; font-size:1.3rem;">📊</div>
  <div>
    <h2 style="margin:0; font-size:1.2rem; font-weight:800; color:#F9FAFB !important;">
      TABLEAU DE BORD FONDACTION
    </h2>
    <p style="margin:2px 0 0; font-size:0.78rem; color:#6B7280 !important;">
      Snapshot — Veille Marchés Bloomberg &nbsp;·&nbsp;
      <span style="color:#10B981;">●</span>&nbsp;Dernière mise à jour:
      <strong style="color:#F9FAFB !important;">12 mars 2026</strong>
    </p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Sommaire Exécutif ────────────────────────────────────────────────────────
st.markdown('<p class="section-hdr">Sommaire Exécutif</p>', unsafe_allow_html=True)
st.write("")

cols = st.columns(5)
for col, (name, d) in zip(cols, SCORES.items()):
    with col:
        st.plotly_chart(gauge_fig(d["score"], d["color"], name),
                        use_container_width=True, key=f"g_{name}")
        st.markdown(signal_bar_html(d["vert"], d["jaune"], d["rouge"]), unsafe_allow_html=True)
        tc = "#10B981" if d["trend"]=="↑" else ("#EF4444" if d["trend"]=="↓" else "#9CA3AF")
        st.markdown(f'<p style="text-align:center;margin-top:4px;font-size:0.85rem;color:{tc};font-weight:700;">{d["trend"]}</p>',
                    unsafe_allow_html=True)

# Global bar
tv, tj, tr = 37, 22, 17; tot = tv+tj+tr
st.markdown(f"""
<div style="background:#111827;border:1px solid #374151;border-radius:10px;
            padding:14px 20px;margin-top:8px;">
  <p style="font-size:0.62rem;letter-spacing:0.12em;text-transform:uppercase;
            color:#6B7280;margin-bottom:8px;">Répartition globale — 76 indicateurs</p>
  <div style="display:flex;align-items:center;gap:12px;">
    <div style="flex:1;height:11px;border-radius:6px;overflow:hidden;background:#1F2937;display:flex;">
      <div style="width:{round(tv/tot*100)}%;background:#10B981;"></div>
      <div style="width:{round(tj/tot*100)}%;background:#F59E0B;"></div>
      <div style="width:{round(tr/tot*100)}%;background:#EF4444;"></div>
    </div>
    <span style="color:#10B981;font-weight:700;font-size:0.82rem;">{round(tv/tot*100)}% Vert</span>
    <span style="color:#F59E0B;font-weight:700;font-size:0.82rem;">{round(tj/tot*100)}% Jaune</span>
    <span style="color:#EF4444;font-weight:700;font-size:0.82rem;">{round(tr/tot*100)}% Rouge</span>
  </div>
</div>
""", unsafe_allow_html=True)

st.write("")

# ── HOPE ─────────────────────────────────────────────────────────────────────
st.markdown('<p class="section-hdr">Indicateurs de Cycle HOPE</p>', unsafe_allow_html=True)
st.write("")
st.markdown(build_table(
    [(r[0], r[1], r[2], r[3], r[4], r[5]) for r in HOPE],
    ["Catégorie", "Indicateur", "Valeur", "Seuil", "Tend.", "Signal"]
), unsafe_allow_html=True)
st.write("")

# ── Signaux Tactiques ─────────────────────────────────────────────────────────
st.markdown('<p class="section-hdr">Signaux Tactiques</p>', unsafe_allow_html=True)
st.write("")
st.markdown(build_table(
    [(r[0], r[1], r[2], r[3], r[4], r[5]) for r in TACTIQUE],
    ["Thématique", "Indicateur", "Valeur", "Comparatif", "Cible", "Signal"]
), unsafe_allow_html=True)
st.write("")

# ── Thèses Clés ───────────────────────────────────────────────────────────────
st.markdown('<p class="section-hdr">Suivi des Thèses Clés 2026</p>', unsafe_allow_html=True)
st.write("")
st.markdown(build_table(
    [(r[0], r[1], r[2], r[3], r[4]) for r in THESES],
    ["Thèse", "Indicateur", "Valeur", "Cible", "Statut"]
), unsafe_allow_html=True)
st.write("")

# ── Alertes Risques ───────────────────────────────────────────────────────────
st.markdown('<p class="section-hdr">Alertes Risques</p>', unsafe_allow_html=True)
st.write("")
st.markdown(build_table(
    [(r[0], r[1], r[2], r[3], r[4]) for r in RISQUES],
    ["Catégorie", "Indicateur", "Valeur", "Seuil", "Signal"]
), unsafe_allow_html=True)
st.write("")

# ── Métriques + Règles ────────────────────────────────────────────────────────
cl, cr = st.columns(2, gap="medium")

with cl:
    st.markdown('<p class="section-hdr">Métriques Clés</p>', unsafe_allow_html=True)
    st.write("")
    a, b = st.columns(2)
    a.metric("VIX",                "26.09",   "+10.8% 1M",    delta_color="inverse")
    b.metric("Spread HY (OAS)",    "294 bps", "-12% 1M")
    a, b = st.columns(2)
    a.metric("ISM Manufacturing",  "52.4",    "Expansion")
    b.metric("10Y US Yield",       "4.24%",   "-0.3% 1M")
    a, b = st.columns(2)
    a.metric("Cuivre ($/t)",       "$13 042", "+8% 1M")
    b.metric("NVIDIA Rev. YoY",    "+65.5%",  "IA en force")
    a, b = st.columns(2)
    a.metric("Incert. Pol. US",    "269.1",   "⚠ Alerte",     delta_color="inverse")
    b.metric("DBC Commodities YTD","+28.2%",  "Momentum fort")

with cr:
    st.markdown('<p class="section-hdr">Règles de Décision</p>', unsafe_allow_html=True)
    st.write("")
    st.markdown("""
<div class="rule-box" style="background:rgba(16,185,129,0.07);border:1px solid rgba(16,185,129,0.3);">
  <p style="color:#10B981;font-weight:700;font-size:0.88rem;margin:0;">✅ Score &gt; 70%</p>
  <p style="color:#9CA3AF;font-size:0.78rem;margin:4px 0 0;">Maintenir / Augmenter les positions tactiques</p>
</div>
<div class="rule-box" style="background:rgba(245,158,11,0.1);border:2px solid rgba(245,158,11,0.5);">
  <p style="color:#F59E0B;font-weight:700;font-size:0.88rem;margin:0;">⚠️ Score 50–70% ← ACTUEL (66)</p>
  <p style="color:#9CA3AF;font-size:0.78rem;margin:4px 0 0;">Maintenir les positions, surveiller les évolutions</p>
</div>
<div class="rule-box" style="background:rgba(239,68,68,0.07);border:1px solid rgba(239,68,68,0.3);">
  <p style="color:#EF4444;font-weight:700;font-size:0.88rem;margin:0;">🚨 Score &lt; 50%</p>
  <p style="color:#9CA3AF;font-size:0.78rem;margin:4px 0 0;">Réduire positions tactiques, augmenter la prudence</p>
</div>
<br>
<p class="section-hdr">Matrice Risques — Probabilité / Impact</p><br>
""", unsafe_allow_html=True)
    for name, icon, note in [
        ("Inflation collante (>3%)",        "⚠️", "CPI 2.5% / PCE 3.0% — proche seuil"),
        ("Hausse yields obligataires (>5%)", "🟢", "10Y à 4.24% — 200bps de marge"),
        ("Retard productivité IA",           "🔴", "Capex hyperscalers -6.7% YTD"),
        ("Escalade guerre commerciale",       "🔴", "Incertitude politique US à 269"),
        ("Récession Canada (mur hypothéc.)", "⚠️", "CAD/USD 0.735 — renouvellements 2026"),
    ]:
        st.markdown(f"""
<div style="background:#111827;border:1px solid #1F2937;border-radius:8px;
            padding:9px 14px;margin-bottom:5px;display:flex;justify-content:space-between;align-items:center;">
  <div>
    <span style="font-size:0.82rem;font-weight:600;color:#F9FAFB;">{icon} {name}</span>
    <p style="font-size:0.7rem;color:#6B7280;margin:2px 0 0;">{note}</p>
  </div>
</div>""", unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align:center;padding:20px;color:#374151;font-size:0.73rem;margin-top:16px;">
  FONDACTION — Tableau de Bord Veille Marchés Bloomberg · Snapshot 12 mars 2026<br>
  Sources: Bloomberg Terminal · FRED · ISM · BLS · Census Bureau · NAR
</div>
""", unsafe_allow_html=True)
