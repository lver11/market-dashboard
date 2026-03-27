"""
Dashboard — Organisations durabilité & ODD
IQ · FSTQ · Desjardins Capital · Développement Économique Canada
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Organisations — Durabilité & ODD",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.html("""
<style>
  [data-testid="stAppViewContainer"] { background: #0B1120; }
  [data-testid="stHeader"]           { background: transparent; }
  section[data-testid="stSidebar"]   { background: #111827; }
  .block-container { padding-top:1.2rem; padding-bottom:2rem; max-width:1500px; }

  .page-title   { font-size:1.6rem; font-weight:900; color:#F9FAFB; letter-spacing:.04em; }
  .page-sub     { font-size:.75rem; color:#6B7280; margin-top:3px; }
  .section-hdr  {
    font-size:.6rem; letter-spacing:.2em; text-transform:uppercase;
    color:#9CA3AF; background:#1F2937; border-radius:4px;
    padding:3px 10px; display:inline-block; margin-bottom:8px;
  }
  .org-card {
    background:#111827; border:1px solid #1F2937; border-radius:8px;
    padding:14px 16px; margin-bottom:10px;
  }
  .org-name  { font-size:1rem; font-weight:800; color:#34D399; }
  .org-type  { font-size:.7rem; color:#9CA3AF; margin-top:2px; }
  .org-meta  { font-size:.75rem; color:#D1D5DB; margin-top:6px; }
  .org-desc  { font-size:.72rem; color:#9CA3AF; margin-top:6px; line-height:1.5; }

  .badge-e   { background:rgba(16,185,129,.15); color:#34D399;
               border:1px solid rgba(16,185,129,.3); border-radius:4px;
               padding:2px 8px; font-size:.62rem; font-weight:700;
               display:inline-block; margin:2px; }
  .badge-s   { background:rgba(59,130,246,.15); color:#93C5FD;
               border:1px solid rgba(59,130,246,.3); border-radius:4px;
               padding:2px 8px; font-size:.62rem; font-weight:700;
               display:inline-block; margin:2px; }
  .badge-g   { background:rgba(245,158,11,.15); color:#FCD34D;
               border:1px solid rgba(245,158,11,.3); border-radius:4px;
               padding:2px 8px; font-size:.62rem; font-weight:700;
               display:inline-block; margin:2px; }
  .badge-odd { background:#1E3A5F; color:#93C5FD;
               border:1px solid #2D4A7A; border-radius:12px;
               padding:2px 10px; font-size:.62rem; font-weight:600;
               display:inline-block; margin:2px; }
  .badge-odd-direct { background:rgba(16,185,129,.2); color:#34D399;
               border:1px solid rgba(16,185,129,.4); border-radius:12px;
               padding:2px 10px; font-size:.62rem; font-weight:700;
               display:inline-block; margin:2px; }
  .neq-box {
    background:#0F172A; border:1px solid #1E3A5F; border-radius:6px;
    padding:6px 12px; font-size:.7rem; color:#94A3B8; margin-top:6px;
  }
  .divider { border-top:1px solid #1F2937; margin:12px 0; }
  .note-box {
    background:#1C1917; border:1px solid #78350F; border-radius:6px;
    padding:8px 14px; font-size:.7rem; color:#D97706; margin-top:8px;
  }
  .kpi-val  { font-size:1.4rem; font-weight:900; color:#34D399; }
  .kpi-lbl  { font-size:.68rem; color:#6B7280; margin-top:2px; }
</style>
""")

# ── Données ───────────────────────────────────────────────────────────────────
ORGS = [
    {
        "id": "IQ",
        "nom": "Investissement Québec",
        "court": "IQ",
        "type": "Société d'État · Gouvernement du Québec",
        "fondation": 2011,
        "ville": "Québec (QC)",
        "adresse": "1195, av. Lavigerie, bur. 060, Québec G1V 4N3",
        "aum": "7,5 G$",
        "neq": "À vérifier — registreentreprises.gouv.qc.ca",
        "web": "investquebec.com",
        "couleur": "#3B82F6",
        "mission": (
            "Contribuer au développement économique du Québec en stimulant l'innovation, "
            "l'entrepreneuriat et la croissance de l'investissement et des exportations. "
            "Soutien via prêts, capital-actions, garanties et crédits d'impôt dans toutes les régions."
        ),
        "esg": {
            "E": ["Intégration TCFD/GIFCC", "Réduction intensité carbone portefeuille"],
            "S": ["Plan DD 2023-2028 (Agenda 2030)", "Présence dans toutes les régions QC"],
            "G": ["Questionnaire ESG obligatoire 100 % des dossiers", "Signataire Finance Montréal"],
        },
        "odds_direct": ["ODD 7", "ODD 8", "ODD 9", "ODD 13", "ODD 17"],
        "odds_indirect": ["ODD 1", "ODD 5", "ODD 10", "ODD 11", "ODD 15"],
    },
    {
        "id": "FSTQ",
        "nom": "Fonds de solidarité FTQ",
        "court": "FSTQ",
        "type": "Fonds de capital de développement · Loi spéciale, Assemblée nationale QC",
        "fondation": 1983,
        "ville": "Montréal (QC)",
        "adresse": "545, boul. Crémazie Est, bur. 200, Montréal H2M 2W4",
        "aum": "21,9 G$",
        "neq": "À vérifier — registreentreprises.gouv.qc.ca",
        "web": "fondsftq.com",
        "couleur": "#10B981",
        "mission": (
            "Fonds de capital de développement (loi spéciale) pour créer, maintenir et protéger "
            "des emplois via des investissements dans des PME de toutes les régions. "
            "Vision 2022-2027 : prospérité durable, responsable et inclusive."
        ),
        "esg": {
            "E": ["Cible 12 G$ actifs durables d'ici 2027 (9+ G$ atteints)", "Siège LEED v5 O+M Platine 2025"],
            "S": ["100 000 actions à impact employés (69 000+ réalisées)", "100 000 nouveaux actionnaires sans régime retraite"],
            "G": ["Rapport annuel lutte travail forcé (Loi S-211)", "Cadre des 6 rendements sociétaux"],
        },
        "odds_direct": ["ODD 1", "ODD 3", "ODD 4", "ODD 5", "ODD 6", "ODD 7", "ODD 8", "ODD 9", "ODD 11", "ODD 13", "ODD 15"],
        "odds_indirect": ["ODD 10"],
    },
    {
        "id": "CRCD",
        "nom": "Desjardins Capital",
        "court": "Desjardins Capital (CRCD)",
        "type": "Fonds d'investissement en capital de développement · Société publique à actionnaires",
        "fondation": 2001,
        "ville": "Montréal (QC)",
        "adresse": "2 Complexe Desjardins, bur. 1717, Montréal",
        "aum": "2,7 G$ CRCD / ~4,9 G$ total",
        "neq": "À vérifier — registreentreprises.gouv.qc.ca",
        "web": "capitalregional.com",
        "couleur": "#F59E0B",
        "mission": (
            "Injecter des capitaux dans des coopératives et des PME de toutes les régions "
            "du Québec (75 % hors Montréal/Québec). Accompagnement relève entrepreneuriale, "
            "numérique et ESG. Écosystème Desjardins vise zéro émission nette 2040."
        ),
        "esg": {
            "E": ["Zéro émission nette Desjardins 2040", "6 G$+ transition énergétique depuis 2020", "2 G$ énergies renouvelables (atteint)"],
            "S": ["Intégration ESG + accompagnement relève et numérique PME", "75 % PME hors grands centres"],
            "G": ["Ambition SBTi validée (1,5°C)", "Rapports GRI / SASB / PRB / PSI"],
        },
        "odds_direct": ["ODD 7", "ODD 8", "ODD 9", "ODD 11", "ODD 13", "ODD 17"],
        "odds_indirect": ["ODD 1", "ODD 5", "ODD 10", "ODD 12", "ODD 15"],
    },
    {
        "id": "DEC",
        "nom": "Développement économique Canada",
        "court": "DEC",
        "type": "Agence fédérale · Gouvernement du Canada · 11 bureaux régionaux au Québec",
        "fondation": 1991,
        "ville": "Montréal (QC)",
        "adresse": "800, boul. René-Lévesque O., bur. 500, Montréal H3B 1X9",
        "aum": "316,2 M$ (budget 2024-2025)",
        "neq": "S.O. — Agence fédérale (non assujettie au REQ provincial)",
        "web": "dec.canada.ca",
        "couleur": "#8B5CF6",
        "mission": (
            "Promouvoir le développement économique à long terme des régions du Québec, "
            "notamment là où la croissance est lente. Finance PME, OBNL et 67 SADC/CAE. "
            "65,4 M$ investis en projets verts en 2024-2025."
        ),
        "esg": {
            "E": ["65,4 M$ en projets verts 2024-2025", "Flotte 35 % zéro émission d'ici 2027", "Réduction GES flotte −15 % d'ici 2026-2027"],
            "S": ["Inclusion autochtone : 19,47 % valeur contractuelle 2024-2025", "Entrepreneuriat inclusif : jeunes, femmes, autochtones"],
            "G": ["Stratégie ministerielle DD 2024-2025", "Alignement ODD 8/9/10/11/12/13"],
        },
        "odds_direct": ["ODD 5", "ODD 8", "ODD 9", "ODD 10", "ODD 11", "ODD 12", "ODD 13"],
        "odds_indirect": ["ODD 3", "ODD 7", "ODD 17"],
    },
]

ODD_LABELS = {
    "ODD 1": "Pas de pauvreté", "ODD 2": "Faim zéro", "ODD 3": "Bonne santé",
    "ODD 4": "Éducation de qualité", "ODD 5": "Égalité des sexes",
    "ODD 6": "Eau propre", "ODD 7": "Énergie propre",
    "ODD 8": "Travail décent", "ODD 9": "Industrie & innovation",
    "ODD 10": "Inégalités réduites", "ODD 11": "Villes durables",
    "ODD 12": "Conso. responsable", "ODD 13": "Action climatique",
    "ODD 14": "Vie aquatique", "ODD 15": "Vie terrestre",
    "ODD 16": "Paix & justice", "ODD 17": "Partenariats",
}

ODD_COLORS = {
    "ODD 1": "#E53E3E", "ODD 3": "#38A169", "ODD 4": "#D69E2E",
    "ODD 5": "#D53F8C", "ODD 6": "#3182CE", "ODD 7": "#F6AD55",
    "ODD 8": "#744210", "ODD 9": "#C05621", "ODD 10": "#DD6B20",
    "ODD 11": "#7B341E", "ODD 12": "#276749", "ODD 13": "#22543D",
    "ODD 15": "#1A4731", "ODD 17": "#1A365D",
}

# ── En-tête ───────────────────────────────────────────────────────────────────
c1, c2 = st.columns([3, 1])
with c1:
    st.html('<div class="page-title">🌿 Organisations — Durabilité & ODD</div>')
    st.html('<div class="page-sub">IQ &nbsp;·&nbsp; FSTQ &nbsp;·&nbsp; Desjardins Capital &nbsp;·&nbsp; Développement Économique Canada &nbsp;|&nbsp; Mis à jour : 2026-03-27</div>')
with c2:
    st.download_button(
        label="⬇ Télécharger Excel",
        data=open("/Users/macbookprom1max/Library/CloudStorage/OneDrive-FONDACTION(CSN)/Documents/Claude/DashBoard/Organisations_Durabilite_ODD.xlsx", "rb").read(),
        file_name="Organisations_Durabilite_ODD.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

st.html('<div class="divider"></div>')

# ── KPIs globaux ──────────────────────────────────────────────────────────────
st.html('<span class="section-hdr">VUE D\'ENSEMBLE</span>')
k1, k2, k3, k4, k5 = st.columns(5)

all_odds_direct = set()
for o in ORGS:
    all_odds_direct.update(o["odds_direct"])

with k1:
    st.html('<div class="org-card"><div class="kpi-val">4</div><div class="kpi-lbl">Organisations</div></div>')
with k2:
    st.html('<div class="org-card"><div class="kpi-val">~33 G$</div><div class="kpi-lbl">Actifs gérés totaux</div></div>')
with k3:
    st.html(f'<div class="org-card"><div class="kpi-val">{len(all_odds_direct)}</div><div class="kpi-lbl">ODD couverts (alignement direct)</div></div>')
with k4:
    st.html('<div class="org-card"><div class="kpi-val">3</div><div class="kpi-lbl">Niveaux de gouvernance (munic. / prov. / féd.)</div></div>')
with k5:
    st.html('<div class="org-card"><div class="kpi-val">4</div><div class="kpi-lbl">Rapports ESG/DD publiés (2024)</div></div>')

st.html('<div class="divider"></div>')

# ── Onglets ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["🏢 Profils", "🎯 Matrice ODD", "📊 Comparatif ESG", "📋 Données brutes"])

# ══ TAB 1 — Profils ══════════════════════════════════════════════════════════
with tab1:
    for org in ORGS:
        with st.expander(f"**{org['nom']}** ({org['court']}) — {org['ville']}", expanded=True):
            left, right = st.columns([3, 2])

            with left:
                st.html(f'<div class="org-name" style="color:{org["couleur"]}">{org["nom"]}</div>')
                st.html(f'<div class="org-type">{org["type"]}</div>')
                st.html(f'<div class="org-meta">📍 {org["adresse"]}</div>')
                st.html(f'<div class="org-meta">🌐 {org["web"]} &nbsp;·&nbsp; 📅 Fondé en {org["fondation"]} &nbsp;·&nbsp; 💰 {org["aum"]}</div>')
                st.html(f'<div class="neq-box">🔢 <b>NEQ :</b> {org["neq"]}</div>')
                st.html(f'<div class="org-desc">{org["mission"]}</div>')

                st.html('<div style="margin-top:10px"><b style="color:#9CA3AF;font-size:.7rem">ENGAGEMENTS ESG</b></div>')
                badges_e = "".join(f'<span class="badge-e">🌱 {x}</span>' for x in org["esg"]["E"])
                badges_s = "".join(f'<span class="badge-s">👥 {x}</span>' for x in org["esg"]["S"])
                badges_g = "".join(f'<span class="badge-g">⚖️ {x}</span>' for x in org["esg"]["G"])
                st.html(f'<div style="margin-top:4px">{badges_e}{badges_s}{badges_g}</div>')

            with right:
                st.html('<div style="margin-bottom:6px"><b style="color:#9CA3AF;font-size:.7rem">ODD ALIGNÉS</b></div>')
                direct_html = "".join(
                    f'<span class="badge-odd-direct" title="{ODD_LABELS.get(o,"")}">✓ {o}</span>'
                    for o in org["odds_direct"]
                )
                indirect_html = "".join(
                    f'<span class="badge-odd" title="{ODD_LABELS.get(o,"")}">◐ {o}</span>'
                    for o in org.get("odds_indirect", [])
                )
                st.html(f'<div>{direct_html}</div><div style="margin-top:4px">{indirect_html}</div>')
                st.html('<div style="margin-top:6px;font-size:.62rem;color:#6B7280">✓ Confirmé &nbsp;·&nbsp; ◐ Indirect</div>')

                # Mini radar ESG
                categories = ["Environnement", "Social", "Gouvernance"]
                scores = [len(org["esg"]["E"]), len(org["esg"]["S"]), len(org["esg"]["G"])]
                fig_r = go.Figure(go.Scatterpolar(
                    r=scores + [scores[0]],
                    theta=categories + [categories[0]],
                    fill="toself",
                    line_color=org["couleur"],
                    fillcolor=org["couleur"] + "33",
                ))
                fig_r.update_layout(
                    polar=dict(
                        bgcolor="#0B1120",
                        radialaxis=dict(visible=True, range=[0, 5], color="#6B7280", gridcolor="#1F2937"),
                        angularaxis=dict(color="#9CA3AF", gridcolor="#1F2937"),
                    ),
                    paper_bgcolor="#111827",
                    plot_bgcolor="#111827",
                    margin=dict(l=20, r=20, t=20, b=20),
                    height=200,
                    showlegend=False,
                )
                st.plotly_chart(fig_r, use_container_width=True, key=f"radar_{org['id']}")

# ══ TAB 2 — Matrice ODD ══════════════════════════════════════════════════════
with tab2:
    st.html('<span class="section-hdr">MATRICE D\'ALIGNEMENT ODD × ORGANISATIONS</span>')

    all_odds = sorted(set(
        o for org in ORGS for o in org["odds_direct"] + org.get("odds_indirect", [])
    ), key=lambda x: int(x.split()[1]))

    rows = []
    for odd in all_odds:
        row = {"ODD": odd, "Thème": ODD_LABELS.get(odd, "")}
        for org in ORGS:
            if odd in org["odds_direct"]:
                row[org["court"]] = 2   # direct
            elif odd in org.get("odds_indirect", []):
                row[org["court"]] = 1   # indirect
            else:
                row[org["court"]] = 0
        rows.append(row)

    df_matrix = pd.DataFrame(rows)
    org_cols = [o["court"] for o in ORGS]

    # Heatmap
    z_vals = df_matrix[org_cols].values
    y_labels = [f"{r['ODD']} — {r['Thème']}" for _, r in df_matrix.iterrows()]
    x_labels = [o["nom"] for o in ORGS]

    colorscale = [
        [0.0, "#1F2937"],
        [0.5, "#FEF3C7"],
        [1.0, "#D1FAE5"],
    ]

    fig_hm = go.Figure(go.Heatmap(
        z=z_vals,
        x=x_labels,
        y=y_labels,
        colorscale=colorscale,
        zmin=0, zmax=2,
        text=[["✓" if v == 2 else ("◐" if v == 1 else "—") for v in row] for row in z_vals],
        texttemplate="%{text}",
        textfont={"size": 14, "color": "white"},
        showscale=False,
        hoverongaps=False,
        hovertemplate="%{y}<br>%{x}<br>%{text}<extra></extra>",
    ))
    fig_hm.update_layout(
        paper_bgcolor="#0B1120",
        plot_bgcolor="#0B1120",
        font=dict(color="#9CA3AF", family="Arial"),
        margin=dict(l=220, r=20, t=30, b=80),
        height=520,
        xaxis=dict(tickfont=dict(size=11, color="#D1D5DB"), side="top"),
        yaxis=dict(tickfont=dict(size=10, color="#9CA3AF"), autorange="reversed"),
    )
    st.plotly_chart(fig_hm, use_container_width=True)

    st.html('<div style="font-size:.7rem;color:#6B7280;margin-top:-10px">✓ = Alignement confirmé (rapports officiels) &nbsp;·&nbsp; ◐ = Alignement indirect / sectoriel &nbsp;·&nbsp; — = Non documenté</div>')

    # Barchart nombre ODD par org
    st.html('<div class="divider"></div>')
    st.html('<span class="section-hdr">ODD COUVERTS PAR ORGANISATION</span>')
    bar_data = {
        "Organisation": [o["nom"] for o in ORGS],
        "Direct": [len(o["odds_direct"]) for o in ORGS],
        "Indirect": [len(o.get("odds_indirect", [])) for o in ORGS],
        "Couleur": [o["couleur"] for o in ORGS],
    }
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        name="Direct (confirmé)",
        x=bar_data["Organisation"],
        y=bar_data["Direct"],
        marker_color=[o["couleur"] for o in ORGS],
        text=bar_data["Direct"],
        textposition="inside",
        textfont=dict(color="white", size=13, family="Arial"),
    ))
    fig_bar.add_trace(go.Bar(
        name="Indirect / sectoriel",
        x=bar_data["Organisation"],
        y=bar_data["Indirect"],
        marker_color=["#374151"] * 4,
        text=bar_data["Indirect"],
        textposition="inside",
        textfont=dict(color="#9CA3AF", size=11, family="Arial"),
    ))
    fig_bar.update_layout(
        barmode="stack",
        paper_bgcolor="#0B1120",
        plot_bgcolor="#0B1120",
        font=dict(color="#9CA3AF", family="Arial"),
        legend=dict(
            bgcolor="#111827", bordercolor="#1F2937", borderwidth=1,
            font=dict(color="#D1D5DB", size=11),
        ),
        margin=dict(l=20, r=20, t=10, b=20),
        height=280,
        xaxis=dict(gridcolor="#1F2937", tickfont=dict(color="#D1D5DB")),
        yaxis=dict(gridcolor="#1F2937", tickfont=dict(color="#6B7280"), title="Nombre ODD"),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ══ TAB 3 — Comparatif ESG ═══════════════════════════════════════════════════
with tab3:
    st.html('<span class="section-hdr">COMPARATIF ENGAGEMENTS ESG</span>')

    col_a, col_b = st.columns(2)

    # Radar multi-org
    with col_a:
        st.html('<div style="font-size:.75rem;color:#9CA3AF;margin-bottom:6px">PROFIL ESG PAR ORGANISATION</div>')
        cats = ["Environnement", "Social", "Gouvernance"]
        fig_multi = go.Figure()
        for org in ORGS:
            scores = [len(org["esg"]["E"]), len(org["esg"]["S"]), len(org["esg"]["G"])]
            fig_multi.add_trace(go.Scatterpolar(
                r=scores + [scores[0]],
                theta=cats + [cats[0]],
                name=org["court"],
                line_color=org["couleur"],
                fillcolor=org["couleur"] + "22",
                fill="toself",
            ))
        fig_multi.update_layout(
            polar=dict(
                bgcolor="#0B1120",
                radialaxis=dict(visible=True, range=[0, 5], color="#6B7280", gridcolor="#1F2937"),
                angularaxis=dict(color="#9CA3AF", gridcolor="#1F2937"),
            ),
            paper_bgcolor="#111827",
            legend=dict(bgcolor="#111827", font=dict(color="#D1D5DB", size=10)),
            margin=dict(l=40, r=40, t=40, b=40),
            height=320,
            font=dict(family="Arial"),
        )
        st.plotly_chart(fig_multi, use_container_width=True)

    # Actifs sous gestion
    with col_b:
        st.html('<div style="font-size:.75rem;color:#9CA3AF;margin-bottom:6px">ACTIFS GÉRÉS (G$)</div>')
        aum_vals = [7.5, 21.9, 4.9, 0.316]
        aum_labels = ["IQ", "FSTQ", "Desjardins Capital", "DEC"]
        aum_colors = [o["couleur"] for o in ORGS]
        fig_pie = go.Figure(go.Pie(
            labels=aum_labels,
            values=aum_vals,
            marker_colors=aum_colors,
            textinfo="label+percent",
            textfont=dict(size=12, color="white", family="Arial"),
            hole=0.45,
            hovertemplate="%{label}<br>%{value} G$<br>%{percent}<extra></extra>",
        ))
        fig_pie.add_annotation(
            text="~34,6 G$<br><span style='font-size:10px;color:#6B7280'>total</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=13, color="#34D399", family="Arial"),
        )
        fig_pie.update_layout(
            paper_bgcolor="#111827",
            font=dict(family="Arial", color="#9CA3AF"),
            legend=dict(bgcolor="#111827", font=dict(color="#D1D5DB", size=10)),
            margin=dict(l=10, r=10, t=10, b=10),
            height=320,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Tableau engagements ESG détaillés
    st.html('<div class="divider"></div>')
    st.html('<span class="section-hdr">ENGAGEMENTS DÉTAILLÉS</span>')

    esg_flat = []
    for org in ORGS:
        for cat, items in org["esg"].items():
            for item in items:
                esg_flat.append({
                    "Organisation": org["court"],
                    "Catégorie": cat,
                    "Engagement": item,
                })
    df_esg = pd.DataFrame(esg_flat)

    cat_filter = st.multiselect(
        "Filtrer par catégorie ESG",
        options=["Environnement", "Social", "Gouvernance"],
        default=["Environnement", "Social", "Gouvernance"],
        key="cat_filter",
    )
    org_filter = st.multiselect(
        "Filtrer par organisation",
        options=[o["court"] for o in ORGS],
        default=[o["court"] for o in ORGS],
        key="org_filter",
    )
    df_show = df_esg[df_esg["Catégorie"].isin(cat_filter) & df_esg["Organisation"].isin(org_filter)]
    st.dataframe(
        df_show.reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Organisation": st.column_config.TextColumn(width=140),
            "Catégorie":    st.column_config.TextColumn(width=120),
            "Engagement":   st.column_config.TextColumn(width=600),
        },
    )

# ══ TAB 4 — Données brutes ════════════════════════════════════════════════════
with tab4:
    st.html('<span class="section-hdr">DONNÉES DE RÉFÉRENCE</span>')

    df_raw = pd.DataFrame([{
        "Acronyme":     o["court"],
        "Organisation": o["nom"],
        "Type":         o["type"],
        "Ville":        o["ville"],
        "Fondation":    o["fondation"],
        "Actif géré":   o["aum"],
        "NEQ":          o["neq"],
        "Site web":     o["web"],
        "ODD directs":  ", ".join(o["odds_direct"]),
        "Nb ODD directs": len(o["odds_direct"]),
    } for o in ORGS])

    st.dataframe(df_raw, use_container_width=True, hide_index=True)

    st.html('<div class="note-box">⚠️ <b>Note sur les NEQ :</b> Les numéros d\'entreprise du Québec (NEQ) de IQ, FSTQ et CRCD sont disponibles sur <b>registreentreprises.gouv.qc.ca</b> (recherche par nom exact). DEC est une agence fédérale non assujettie au registre provincial.</div>')
    st.html('<div style="margin-top:12px;font-size:.68rem;color:#4B5563">Sources : Registre des entreprises du Québec · investquebec.com · fondsftq.com · capitalregional.com · desjardins.com · dec.canada.ca · Rapports ESG/DD 2024-2025</div>')
