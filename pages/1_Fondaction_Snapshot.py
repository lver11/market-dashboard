"""
Fondaction Bloomberg Snapshot Dashboard — Page Streamlit
Source: Tableau_Bord_Fondaction_Bloomberg-3.xlsx (onglet Snapshot)
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
</style>
""")

# ── Data ──────────────────────────────────────────────────────────────────────

SCORECARD = [
    {"cat": "Cycle HOPE",        "score": 63, "trend": "→", "vert": 10, "jaune": 4,  "rouge": 5,  "color": "#60A5FA"},
    {"cat": "Signaux Tactiques", "score": 50, "trend": "→", "vert": 7,  "jaune": 4,  "rouge": 7,  "color": "#F59E0B"},
    {"cat": "Thèses Clés",       "score": 71, "trend": "↑", "vert": 11, "jaune": 8,  "rouge": 2,  "color": "#34D399"},
    {"cat": "Alertes Risques",   "score": 79, "trend": "↑", "vert": 12, "jaune": 6,  "rouge": 1,  "color": "#F87171"},
    {"cat": "SCORE GLOBAL",      "score": 66, "trend": "→", "vert": None, "jaune": None, "rouge": None, "color": "#A78BFA"},
]

HOPE_DATA = {
    "H — Housing": [
        {"ind": "Mises en chantier US (SAAR)",         "val": "1 487", "seuil": ">1.4M",    "signal": "Vert",  "tend": "↑", "note": "Census Bureau, mensuel"},
        {"ind": "Permis de construire US",              "val": "1 376", "seuil": ">1.5M",    "signal": "Jaune", "tend": "↓", "note": "Census Bureau, mensuel"},
        {"ind": "Indice NAHB confiance constructeurs",  "val": "36",    "seuil": ">50",      "signal": "Rouge", "tend": "↓", "note": "NAHB, mensuel"},
        {"ind": "Ventes maisons existantes (YoY%)",     "val": "+4.1%", "seuil": ">0%",      "signal": "Jaune", "tend": "↑", "note": "NAR, mensuel"},
        {"ind": "Case-Shiller 20 villes (YoY%)",        "val": "+1.4%", "seuil": "—",        "signal": "Jaune", "tend": "↓", "note": "S&P, mensuel avec délai"},
    ],
    "O — Orders": [
        {"ind": "ISM Manufacturing PMI",                "val": "52.4",  "seuil": ">50",      "signal": "Vert",  "tend": "↓", "note": "ISM, 1er jour ouvrable du mois"},
        {"ind": "ISM New Orders",                       "val": "8",     "seuil": ">50",      "signal": "Rouge", "tend": "↑", "note": "ISM, composante clé"},
        {"ind": "Ratio New Orders/Inventories",         "val": "—",     "seuil": ">1.0",     "signal": "Vert",  "tend": "↑", "note": "NAPMNOI/NAPMII (calculé)"},
        {"ind": "PMI Manufacturier Global",             "val": "51.9",  "seuil": ">50",      "signal": "Vert",  "tend": "↑", "note": "S&P Global/JPM"},
        {"ind": "Commandes biens durables (MoM%)",      "val": "−1.4%", "seuil": ">0%",      "signal": "Jaune", "tend": "↓", "note": "Census Bureau"},
    ],
    "P — Profits": [
        {"ind": "Croissance BPA S&P 500 (YoY%)",        "val": "+13.6%","seuil": ">10%",     "signal": "Vert",  "tend": "↑", "note": "Bloomberg consensus"},
        {"ind": "Marge nette S&P 500 (proxy Earn.Yld)", "val": "3.78",  "seuil": ">11%",     "signal": "Rouge", "tend": "↓", "note": "Proxy: EARN_YLD Bloomberg"},
        {"ind": "Révisions BPA (3 mois)",               "val": "+29.4", "seuil": ">0",       "signal": "Vert",  "tend": "↑", "note": "Bloomberg, net révisions"},
        {"ind": "Croissance revenus S&P 500 (YoY%)",    "val": "−1.0%", "seuil": ">5%",      "signal": "Rouge", "tend": "↑", "note": "Proxy: SPX YTD %"},
    ],
    "E — Employment": [
        {"ind": "Emplois non-agricoles (variation)",    "val": "−92K",  "seuil": "—",        "signal": "Rouge", "tend": "↓", "note": "BLS, 1er vendredi du mois"},
        {"ind": "Taux de chômage U3",                   "val": "4.4%",  "seuil": "<4.5%",    "signal": "Vert",  "tend": "↑", "note": "BLS"},
        {"ind": "Taux de chômage U6",                   "val": "7.9%",  "seuil": "—",        "signal": "Vert",  "tend": "↓", "note": "BLS, mesure élargie"},
        {"ind": "Initial Jobless Claims (4wk avg)",     "val": "212K",  "seuil": "<250K",    "signal": "Vert",  "tend": "↑", "note": "DOL, hebdomadaire"},
        {"ind": "JOLTS Job Openings",                   "val": "6 542K","seuil": "—",        "signal": "Vert",  "tend": "↓", "note": "BLS, avec délai"},
    ],
}

TACTIQUE_DATA = {
    "Valorisations": [
        {"ind": "P/E Forward S&P 500",              "val": "21.5x",  "comp": "26.5x trailing", "cible": "<18x",      "signal": "Jaune", "impl": "21x fwd vs 26x trailing — marge de sécurité faible"},
        {"ind": "P/E Forward Russell 2000",         "val": "25.7x",  "comp": "48.7x trailing", "cible": "<15x",      "signal": "Rouge", "impl": "26x fwd vs 49x trailing — vulnérable si BPA déçoit"},
        {"ind": "Écart P/E (SPX − RTY)",            "val": "−4.2x",  "comp": "−22.2x",         "cible": "<3x",       "signal": "Vert",  "impl": "SPX moins cher que RTY fwd: rare, favorise large caps"},
        {"ind": "P/E MSCI EAFE",                    "val": "16.2x",  "comp": "18.2x trailing", "cible": "<14x",      "signal": "Jaune", "impl": "Décote ~25% vs SPX, opportunité relative ex-US"},
        {"ind": "P/E MSCI EM",                      "val": "17.3x",  "comp": "18.4x trailing", "cible": "<12x",      "signal": "Rouge", "impl": "Plus cher qu'historique EM (~12x), sélectivité requise"},
        {"ind": "Equity Risk Premium (ERP)",        "val": "0.42%",  "comp": "moy. 4.5%",      "cible": ">4%",       "signal": "Rouge", "impl": "ERP 0.4% vs moy. 4.5% — actions non rémunérées"},
    ],
    "Momentum ETF": [
        {"ind": "IWM (Small Cap) 1M%",              "val": "−4.1%",  "comp": "+2.7% YTD",      "cible": ">+2%",      "signal": "Rouge", "impl": "Prise de profit CT, tendance YTD intacte"},
        {"ind": "IVE (Value) 1M%",                  "val": "−2.7%",  "comp": "+0.4% YTD",      "cible": ">+2%",      "signal": "Rouge", "impl": "Rotation value en pause, pas de conviction"},
        {"ind": "EEM (EM) 1M%",                     "val": "−4.8%",  "comp": "+5.8% YTD",      "cible": ">+2%",      "signal": "Rouge", "impl": "Correction CT, flux YTD encore positifs"},
        {"ind": "DBC (Commodités) 1M%",             "val": "+20.4%", "comp": "+28.2% YTD",     "cible": ">+2%",      "signal": "Vert",  "impl": "Forte accélération, thèse rareté validée"},
    ],
    "Crédit": [
        {"ind": "Spread HY US (OAS)",               "val": "294 bps","comp": "moy. 5Y ~400",   "cible": "<350 bps",  "signal": "Vert",  "impl": "+12% 1M — sous moy. 5Y, crédit sain"},
        {"ind": "Spread IG US (OAS)",               "val": "86 bps", "comp": "moy. 5Y ~120",   "cible": "<100 bps",  "signal": "Vert",  "impl": "+15% 1M — stress modéré, pas d'alerte"},
        {"ind": "Spread EM Souverain (EMB YTD)",    "val": "−0.7%",  "comp": "+5.1% 1Y",       "cible": ">0% YTD",   "signal": "Rouge", "impl": "EMB négatif YTD — dette EM sous pression CT"},
        {"ind": "Ratio BB/CCC dans HY",             "val": "0.13x",  "comp": "moy. 0.97x",     "cible": "<2.5x",     "signal": "Vert",  "impl": "Forte compression qualité dans le HY"},
    ],
    "Momentum Technique": [
        {"ind": "RSI S&P 500 (14 jours)",           "val": "42.4",   "comp": "30j: 46.6",      "cible": "30–70",     "signal": "Vert",  "impl": "Zone neutre-basse, pas de signal extrême"},
        {"ind": "S&P 500 vs MA 200 jours",          "val": "+2.7%",  "comp": "−1.7% vs MA50",  "cible": ">0%",       "signal": "Vert",  "impl": "Tendance LT haussière, CT fragile vs MA50"},
        {"ind": "VIX",                              "val": "26.1",   "comp": "moy. 23.5",      "cible": "<20",       "signal": "Jaune", "impl": "+23% 1M — couverture recommandée"},
        {"ind": "Breadth: % actions > MA50",        "val": "53.4%",  "comp": "−1.3% sur 1M",   "cible": ">60%",      "signal": "Jaune", "impl": "Participation se rétrécit — surveiller si <47%"},
    ],
}

THESES_DATA = {
    "IA — Couche 1: Énergie": [
        {"ind": "Capex utilities US (YoY%)",               "val": "+8.2%",    "cible": ">10%",         "statut": "Jaune", "note": ""},
        {"ind": "Prix uranium spot ($/lb)",                "val": "$85.7",    "cible": ">$80/lb",      "statut": "Vert",  "note": "Proxy: URA ETF ou Cameco"},
        {"ind": "Prix gaz naturel Henry Hub ($/MMBtu)",    "val": "$3.21",    "cible": ">$3.50",       "statut": "Jaune", "note": "Coût énergie data centers"},
    ],
    "IA — Couche 2: Puces": [
        {"ind": "Revenus NVIDIA (YoY%)",                   "val": "+65.5%",   "cible": ">20%",         "statut": "Vert",  "note": "Earnings trimestriels"},
        {"ind": "Ratio book-to-bill semiconducteurs",      "val": "9.57x",    "cible": ">1.0",         "statut": "Vert",  "note": "SIA data"},
    ],
    "IA — Couche 3: Infrastructure": [
        {"ind": "Capex hyperscalers AMZN+GOOG+MSFT+META", "val": "−6.7% YTD","cible": ">+30% YTD",   "statut": "Rouge", "note": "Guidance trimestrielle"},
        {"ind": "Performance Vertiv/Quanta/EQIX",          "val": "+42.4% YTD","cible": ">+10% YTD",  "statut": "Vert",  "note": "Bénéficiaires directs"},
    ],
    "IA — Couche 5: Applications": [
        {"ind": "Croissance revenus cloud (AWS+Azure+GCP)","val": "−17.6%",   "cible": ">25%",         "statut": "Rouge", "note": "Adoption entreprise"},
    ],
    "Great Broadening": [
        {"ind": "Performance relative RTY vs SPX (YTD)",   "val": "+3.5%",    "cible": ">0%",          "statut": "Vert",  "note": "Rotation small caps"},
        {"ind": "Breadth: % secteurs S&P en hausse",       "val": "53.4%",    "cible": ">53% (proxy)", "statut": "Vert",  "note": "RSP−SPY+50. >53 = participation large"},
        {"ind": "S&P Equal Weight vs Cap Weight (YTD)",    "val": "+3.4%",    "cible": ">0%",          "statut": "Vert",  "note": "RSP vs SPY"},
    ],
    "Commodités — Rareté": [
        {"ind": "Prix cuivre ($/tonne LME)",               "val": "$13 042",  "cible": ">$9 500/t",    "statut": "Vert",  "note": "LMCADS03. >$9 500 favorable"},
        {"ind": "Prix argent ($/oz)",                      "val": "$86.5",    "cible": ">$28/oz",      "statut": "Vert",  "note": "Demande industrielle"},
        {"ind": "Inventaires cuivre LME (tonnes)",         "val": "12 940",   "cible": "Déclin",       "statut": "Jaune", "note": "Niveau stocks critiques"},
        {"ind": "Capex minières majors (YTD%)",            "val": "+14.5%",   "cible": ">+10% YTD",    "statut": "Vert",  "note": "Sous-investissement chronique"},
    ],
    "Stimulus Fiscal US": [
        {"ind": "Performance IWM (Small Caps YTD)",        "val": "+2.7%",    "cible": ">+10% YTD",    "statut": "Jaune", "note": "Small caps domestiques = 1ers bénéficiaires"},
        {"ind": "Performance XLI (Industrielles YTD)",     "val": "+9.3%",    "cible": ">+10% YTD",    "statut": "Jaune", "note": "Exposition infra / dépenses gouv."},
        {"ind": "Consumer Confidence (Conference Board)",  "val": "91.2",     "cible": ">100",          "statut": "Jaune", "note": "Effet richesse stimulus sur ménages"},
        {"ind": "Rendement 10Y US",                        "val": "4.24%",    "cible": "<4.50%",        "statut": "Vert",  "note": "Risque crowding out si >5%"},
    ],
    "Santé / Biotech": [
        {"ind": "Performance XBI (Biotech ETF YTD)",       "val": "+3.6%",    "cible": ">+10% YTD",    "statut": "Jaune", "note": "Thèse IA + Drug discovery"},
        {"ind": "Approbations FDA (proxy IBB YTD%)",       "val": "+1.2%",    "cible": ">+5% YTD",     "statut": "Jaune", "note": "Proxy: IBB ETF YTD%. >5% favorable"},
    ],
}

RISQUES_DATA = {
    "Inflation": [
        {"ind": "CPI Core US (YoY%)",               "val": "2.5%",     "seuil": ">3.0%",      "signal": "Jaune", "comm": "Fed target 2%"},
        {"ind": "PCE Core (YoY%)",                  "val": "3.00%",    "seuil": ">3.0%",      "signal": "Jaune", "comm": "Mesure préférée Fed"},
        {"ind": "Inflation anticipée 5Y5Y",         "val": "2.18%",    "seuil": ">2.5%",      "signal": "Vert",  "comm": "Anticipations long terme"},
        {"ind": "Salaires horaires (YoY%)",         "val": "3.8%",     "seuil": ">4.0%",      "signal": "Jaune", "comm": "Pression salariale"},
    ],
    "Taux / Yields": [
        {"ind": "Rendement 10 ans US",              "val": "4.24%",    "seuil": ">5.0%",      "signal": "Vert",  "comm": "Bond vigilantes"},
        {"ind": "Rendement 2 ans US",               "val": "3.67%",    "seuil": ">5.0%",      "signal": "Vert",  "comm": "Attentes Fed"},
        {"ind": "Spread 10Y−2Y (courbe)",           "val": "+56.6 bp", "seuil": "<−50 bps",   "signal": "Vert",  "comm": "Inversion = risque récession"},
        {"ind": "Rendement réel 10Y TIPS",          "val": "1.84%",    "seuil": ">2.5%",      "signal": "Vert",  "comm": "Coût réel du capital"},
        {"ind": "Fed Funds futures déc 2026",       "val": "96.37",    "seuil": "<95.50",     "signal": "Vert",  "comm": "Trajectoire anticipée"},
    ],
    "Crédit / Liquidité": [
        {"ind": "Spread TED",                       "val": "1.17%",    "seuil": ">50 bps",    "signal": "Vert",  "comm": "Stress interbancaire"},
        {"ind": "Réserves bancaires Fed ($M)",      "val": "6 628 894","seuil": "<6 000 000", "signal": "Vert",  "comm": "Liquidité système"},
        {"ind": "Taux défaut HY (12m trailing)",    "val": "2.94%",    "seuil": ">500 bps",   "signal": "Vert",  "comm": "Stress crédit"},
    ],
    "Géopolitique": [
        {"ind": "Indice incertitude politique US",  "val": "269.1",    "seuil": ">200",       "signal": "Rouge", "comm": "Baker-Bloom-Davis"},
        {"ind": "Prix pétrole Brent ($/bbl)",       "val": "$98.9",    "seuil": ">$100",      "signal": "Jaune", "comm": "Choc pétrolier"},
        {"ind": "USD Index (DXY)",                  "val": "99.5",     "seuil": ">110",       "signal": "Vert",  "comm": "Force dollar"},
        {"ind": "USD/CNY",                          "val": "6.87",     "seuil": ">7.5",       "signal": "Vert",  "comm": "Tensions Chine"},
    ],
    "Canada": [
        {"ind": "Écart taux 10Y CA−US",             "val": "−0.75%",   "seuil": "<−1.0%",    "signal": "Jaune", "comm": "Divergence politique monétaire"},
        {"ind": "CAD/USD",                          "val": "0.735",    "seuil": "<0.70",     "signal": "Jaune", "comm": "Faiblesse dollar canadien"},
        {"ind": "Renouvellements hypothécaires 2026","val": "—",       "seuil": "Qualitatif","signal": "—",     "comm": "Mur hypothécaire à surveiller"},
        {"ind": "Indice TSX vs S&P 500 (rel perf)", "val": "+5.5%",   "seuil": "<−10%",     "signal": "Vert",  "comm": "Sous-performance Canada"},
    ],
}

MATRICE = [
    "Inflation collante (>3%)",
    "Hausse yields obligataires (>5%)",
    "Retard productivité IA",
    "Escalade guerre commerciale",
    "Récession Canada (mur hypothécaire)",
]

# ── Helpers ───────────────────────────────────────────────────────────────────
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

# ── Header ────────────────────────────────────────────────────────────────────
st.html("""
<div style="display:flex;align-items:center;justify-content:space-between;
            border-bottom:1px solid #1F2937;padding-bottom:12px;margin-bottom:16px;">
  <div>
    <div class="snap-title">📊 TABLEAU DE BORD FONDACTION</div>
    <div class="snap-sub">Snapshot Veille Marchés Bloomberg &nbsp;·&nbsp;
      <span style="color:#10B981;">●</span>&nbsp;Dernière mise à jour:
      <strong style="color:#F9FAFB;">12 mars 2026</strong>
    </div>
  </div>
  <div style="font-size:0.7rem;color:#6B7280;text-align:right;">
    Source: Tableau_Bord_Fondaction_Bloomberg-3.xlsx
  </div>
</div>
""")

# ── Scorecard Global ──────────────────────────────────────────────────────────
st.html('<p class="section-hdr">Scorecard Global — 77 indicateurs</p>')
cols = st.columns(5)
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

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🏗️  HOPE — Cycle (63/100)",
    "📈  Signaux Tactiques (50/100)",
    "💡  Thèses Clés (71/100)",
    "⚠️  Alertes Risques (79/100)",
])

# ── TAB 1 : HOPE ─────────────────────────────────────────────────────────────
with tab1:
    st.html('<p class="section-hdr">19 indicateurs — 10 Verts · 4 Jaunes · 5 Rouges</p>')
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
              <span class="ind-note">{r["note"]}</span>
            </div>"""
        st.html(html)

# ── TAB 2 : SIGNAUX TACTIQUES ─────────────────────────────────────────────────
with tab2:
    st.html('<p class="section-hdr">18 indicateurs — 7 Verts · 4 Jaunes · 7 Rouges</p>')
    col_a, col_b = st.columns(2)
    for i, (section, rows) in enumerate(TACTIQUE_DATA.items()):
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
                    color:#374151;font-size:0.7rem;">{r["impl"]}</span>
                </div>"""
            st.html(html)

# ── TAB 3 : THÈSES ───────────────────────────────────────────────────────────
with tab3:
    st.html('<p class="section-hdr">21 indicateurs — 11 Verts · 8 Jaunes · 2 Rouges</p>')
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
                  <span class="ind-note" style="flex:2.5;">{r["note"]}</span>
                </div>"""
            st.html(html)

# ── TAB 4 : ALERTES RISQUES ──────────────────────────────────────────────────
with tab4:
    st.html('<p class="section-hdr">19 indicateurs — 12 Verts · 6 Jaunes · 1 Rouge</p>')
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
                  <span class="ind-note" style="flex:2;text-align:left;">{r["comm"]}</span>
                </div>"""
            st.html(html)

    # Matrice probabilité / impact
    st.html("""
    <div class="subsec-hdr" style="margin-top:20px;flex:100%;">
      Matrice Probabilité × Impact — À remplir lors de la revue mensuelle
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
    for risque in MATRICE:
        mat_html += f"""
        <div class="ind-row">
          <span class="ind-name" style="flex:4;">{risque}</span>
          <span class="mat-val" style="color:#1F2937;">—</span>
          <span class="mat-val" style="color:#1F2937;">—</span>
          <span class="mat-val" style="color:#1F2937;">—</span>
          <span style="flex:3;font-size:0.65rem;color:#1F2937;font-style:italic;">À remplir</span>
        </div>"""
    st.html(mat_html)
