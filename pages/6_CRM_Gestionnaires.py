"""
CRM Gestionnaires — Suivi des rencontres, revues trimestrielles et conférences.
Données lues depuis SharePoint Lists via Microsoft Graph API (cache 15 min).
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.sharepoint import load_all

st.set_page_config(
    page_title="Fondaction — CRM Gestionnaires",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.html("""
<style>
  [data-testid="stAppViewContainer"] { background: #0B1120; }
  [data-testid="stHeader"] { background: transparent; }
  section[data-testid="stSidebar"] { background: #111827; }
  .block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1500px; }

  .crm-title { font-size:1.4rem; font-weight:800; color:#F9FAFB; letter-spacing:0.04em; }
  .section-hdr {
    font-size:0.6rem; letter-spacing:0.2em; text-transform:uppercase;
    color:#9CA3AF; background:#1F2937; border-radius:4px;
    padding:3px 10px; display:inline-block; margin-bottom:8px;
  }
  .kpi-card {
    background:#1F2937; border-radius:8px; padding:16px 20px;
    border:1px solid #374151; text-align:center;
  }
  .kpi-val { font-size:2rem; font-weight:800; color:#60A5FA; }
  .kpi-lbl { font-size:0.75rem; color:#9CA3AF; margin-top:4px; }
  .alert-card {
    background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3);
    border-radius:6px; padding:8px 14px; margin:4px 0;
    color:#FCA5A5; font-size:0.85rem;
  }
  .pipeline-card {
    background:#1F2937; border-radius:6px; padding:10px 14px;
    margin:6px 0; border:1px solid #374151;
  }
</style>
""")

st.markdown('<p class="crm-title">CRM — Suivi Gestionnaires & Conférences</p>', unsafe_allow_html=True)

# ── Chargement des données ────────────────────────────────────────────────────
with st.spinner("Chargement des données SharePoint..."):
    try:
        data = load_all()
    except Exception as e:
        st.error(f"Erreur de connexion SharePoint : {e}")
        st.info(
            "Vérifiez que les secrets Streamlit sont configurés : "
            "`client_id`, `tenant_id`, `client_secret`, `site_id` dans `[sharepoint]`."
        )
        st.stop()

orgs        = data["organisations"]
contacts    = data["contacts"]
rencontres  = data["rencontres"]
revues      = data["revues"]
conferences = data["conferences"]
sessions    = data["sessions"]
classes     = data["classes_actifs"]

# Normalisation des dates
for df, col in [(rencontres, "DateRencontre"), (conferences, "DateDebut")]:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")

# ── Onglets ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Vue d'ensemble",
    "Fiche gestionnaire",
    "Revues trimestrielles",
    "Conférences & Veille",
    "Pipeline",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Vue d'ensemble
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<span class="section-hdr">VUE D\'ENSEMBLE</span>', unsafe_allow_html=True)

    now = datetime.now()
    j30 = now - timedelta(days=30)
    j90 = now - timedelta(days=90)

    nb_30 = nb_90 = 0
    if "DateRencontre" in rencontres.columns:
        nb_30 = int(rencontres[rencontres["DateRencontre"] >= j30].shape[0])
        nb_90 = int(rencontres[rencontres["DateRencontre"] >= j90].shape[0])

    nb_orgs = len(orgs) if not orgs.empty else 0

    c1, c2, c3 = st.columns(3)
    for col, val, lbl in [
        (c1, nb_30,  "Rencontres (30 jours)"),
        (c2, nb_90,  "Rencontres (90 jours)"),
        (c3, nb_orgs, "Organisations suivies"),
    ]:
        col.markdown(
            f'<div class="kpi-card"><div class="kpi-val">{val}</div>'
            f'<div class="kpi-lbl">{lbl}</div></div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # Alertes inactivité
    st.markdown('<span class="section-hdr">ALERTES — INACTIVITÉ +90 JOURS</span>', unsafe_allow_html=True)

    actifs: list[str] = []
    if "Statut" in orgs.columns and "Titre" in orgs.columns:
        actifs = orgs[orgs["Statut"] == "Actif"]["Titre"].dropna().tolist()

    if actifs and not rencontres.empty and "DateRencontre" in rencontres.columns and "Organisation" in rencontres.columns:
        derniere = rencontres.groupby("Organisation")["DateRencontre"].max()
        inactifs = [o for o in actifs if o not in derniere.index or derniere[o] < j90]
        if inactifs:
            for org in inactifs[:15]:
                st.markdown(
                    f'<div class="alert-card">⚠️ {org} — aucune rencontre depuis +90 jours</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.success("Tous les gestionnaires actifs ont été rencontrés dans les 90 derniers jours.")
    else:
        st.info("Données insuffisantes pour calculer les alertes.")

    st.divider()

    # Timeline des dernières rencontres
    st.markdown('<span class="section-hdr">DERNIÈRES RENCONTRES</span>', unsafe_allow_html=True)

    if not rencontres.empty and "DateRencontre" in rencontres.columns:
        cols_aff = [c for c in ["DateRencontre", "Titre", "Organisation", "TypeRencontre", "Auteur"] if c in rencontres.columns]
        st.dataframe(
            rencontres.sort_values("DateRencontre", ascending=False).head(20)[cols_aff],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Aucune rencontre enregistrée.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Fiche gestionnaire
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<span class="section-hdr">FICHE GESTIONNAIRE</span>', unsafe_allow_html=True)

    if orgs.empty or "Titre" not in orgs.columns:
        st.info("Aucune organisation dans SharePoint.")
    else:
        org_choisie = st.selectbox(
            "Sélectionner une organisation",
            sorted(orgs["Titre"].dropna().tolist()),
        )

        org_row = orgs[orgs["Titre"] == org_choisie]
        if not org_row.empty:
            r = org_row.iloc[0]
            ca, cb, cc = st.columns(3)
            ca.metric("Type",      r.get("Type",   "—"))
            cb.metric("Statut",    r.get("Statut", "—"))
            cc.metric("AUM (G$)",  r.get("AUM",    "—"))
            if r.get("Notes"):
                st.markdown(f"**Notes :** {r['Notes']}")

        st.divider()

        # Historique rencontres
        st.markdown('<span class="section-hdr">HISTORIQUE DES RENCONTRES</span>', unsafe_allow_html=True)

        if not rencontres.empty and "Organisation" in rencontres.columns:
            r_org = rencontres[rencontres["Organisation"] == org_choisie].copy()
            if "DateRencontre" in r_org.columns:
                r_org = r_org.sort_values("DateRencontre", ascending=False)

            if r_org.empty:
                st.info("Aucune rencontre enregistrée pour cette organisation.")
            else:
                for _, row in r_org.iterrows():
                    date_val = row.get("DateRencontre")
                    date_str = date_val.strftime("%Y-%m-%d") if pd.notna(date_val) else "?"
                    with st.expander(f"{date_str} — {row.get('Titre', 'Rencontre')}"):
                        st.markdown(
                            f"**Type :** {row.get('TypeRencontre', '—')}  |  "
                            f"**Auteur :** {row.get('Auteur', '—')}"
                        )
                        for champ, label in [("Resume", "Résumé"), ("PointsCles", "Points clés"), ("ActionsASuivre", "Actions")]:
                            if row.get(champ):
                                st.markdown(f"**{label} :** {row[champ]}")
        else:
            st.info("Aucune rencontre enregistrée.")

        st.divider()

        # Évolution des scores
        st.markdown('<span class="section-hdr">ÉVOLUTION DES SCORES DE REVUE</span>', unsafe_allow_html=True)

        if not revues.empty and "Organisation" in revues.columns:
            rev_org = revues[revues["Organisation"] == org_choisie].copy()
            score_cols = [c for c in ["ScoreProcessus", "ScoreEquipe", "ScoreMandat"] if c in rev_org.columns]

            if not rev_org.empty and score_cols and "Trimestre" in rev_org.columns:
                rev_org = rev_org.sort_values("Trimestre")
                fig = go.Figure()
                colors = {"ScoreProcessus": "#60A5FA", "ScoreEquipe": "#34D399", "ScoreMandat": "#FBBF24"}
                for col in score_cols:
                    rev_org[col] = pd.to_numeric(rev_org[col], errors="coerce")
                    fig.add_trace(go.Scatter(
                        x=rev_org["Trimestre"],
                        y=rev_org[col],
                        name=col.replace("Score", ""),
                        mode="lines+markers",
                        line=dict(color=colors.get(col, "#9CA3AF"), width=2),
                    ))
                fig.update_layout(
                    paper_bgcolor="#0B1120", plot_bgcolor="#111827",
                    font_color="#F9FAFB", yaxis=dict(range=[0, 5.5]),
                    legend=dict(bgcolor="#1F2937"), margin=dict(t=20, b=20),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Aucune revue trimestrielle enregistrée pour cette organisation.")
        else:
            st.info("Aucune revue trimestrielle enregistrée.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Revues trimestrielles
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<span class="section-hdr">REVUES TRIMESTRIELLES</span>', unsafe_allow_html=True)

    if revues.empty:
        st.info("Aucune revue trimestrielle enregistrée.")
    else:
        fc1, fc2 = st.columns(2)

        # Filtre trimestre
        with fc1:
            trimestres = sorted(revues["Trimestre"].dropna().unique().tolist(), reverse=True) if "Trimestre" in revues.columns else []
            trim_choisi = st.selectbox("Trimestre", trimestres) if trimestres else None

        # Filtre classe d'actif
        with fc2:
            classe_filtre = "Toutes"
            if "ClasseActif" in orgs.columns and not orgs.empty:
                classes_dispo = ["Toutes"] + sorted(orgs["ClasseActif"].dropna().unique().tolist())
                classe_filtre = st.selectbox("Classe d'actif", classes_dispo, key="rev_classe")

        rev_trim = revues.copy()
        if trim_choisi and "Trimestre" in rev_trim.columns:
            rev_trim = rev_trim[rev_trim["Trimestre"] == trim_choisi]
        if classe_filtre != "Toutes" and "Organisation" in rev_trim.columns and "Titre" in orgs.columns:
            orgs_classe = orgs[orgs["ClasseActif"] == classe_filtre]["Titre"].tolist()
            rev_trim = rev_trim[rev_trim["Organisation"].isin(orgs_classe)]

        # Colonnes numériques
        for col in ["Rendement", "Benchmark", "TrackingError", "ScoreProcessus", "ScoreEquipe", "ScoreMandat"]:
            if col in rev_trim.columns:
                rev_trim[col] = pd.to_numeric(rev_trim[col], errors="coerce")

        if "Rendement" in rev_trim.columns and "Benchmark" in rev_trim.columns:
            rev_trim["Valeur ajoutée"] = (rev_trim["Rendement"] - rev_trim["Benchmark"]).round(2)

        afficher = [c for c in [
            "Organisation", "Rendement", "Benchmark", "Valeur ajoutée",
            "TrackingError", "ScoreProcessus", "ScoreEquipe", "ScoreMandat", "Recommandation",
        ] if c in rev_trim.columns]

        if afficher:
            st.dataframe(rev_trim[afficher], use_container_width=True, hide_index=True)

        st.divider()

        # Graphique évolution tous gestionnaires
        st.markdown('<span class="section-hdr">ÉVOLUTION DES SCORES — TOUS GESTIONNAIRES</span>', unsafe_allow_html=True)

        score_col = st.selectbox(
            "Score à afficher",
            [c for c in ["ScoreProcessus", "ScoreEquipe", "ScoreMandat"] if c in revues.columns],
            key="score_global",
        )

        if score_col and "Trimestre" in revues.columns and "Organisation" in revues.columns:
            rev_plot = revues[["Trimestre", "Organisation", score_col]].copy()
            rev_plot[score_col] = pd.to_numeric(rev_plot[score_col], errors="coerce")
            rev_plot = rev_plot.dropna().sort_values("Trimestre")
            fig2 = px.line(
                rev_plot, x="Trimestre", y=score_col,
                color="Organisation", markers=True, template="plotly_dark",
            )
            fig2.update_layout(
                paper_bgcolor="#0B1120", plot_bgcolor="#111827",
                font_color="#F9FAFB", yaxis=dict(range=[0, 5.5]),
                legend=dict(bgcolor="#1F2937"), margin=dict(t=20, b=20),
            )
            st.plotly_chart(fig2, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Conférences & Veille
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<span class="section-hdr">CONFÉRENCES & VEILLE</span>', unsafe_allow_html=True)

    if conferences.empty:
        st.info("Aucune conférence enregistrée.")
    else:
        f1, f2 = st.columns(2)
        with f1:
            classe_conf = "Toutes"
            if not classes.empty and "Titre" in classes.columns:
                classe_conf = st.selectbox(
                    "Classe d'actif",
                    ["Toutes"] + sorted(classes["Titre"].dropna().tolist()),
                    key="conf_classe",
                )
        with f2:
            org_conf = "Toutes"
            if not orgs.empty and "Titre" in orgs.columns:
                org_conf = st.selectbox(
                    "Organisation mentionnée",
                    ["Toutes"] + sorted(orgs["Titre"].dropna().tolist()),
                    key="conf_org",
                )

        confs_display = (
            conferences.sort_values("DateDebut", ascending=False)
            if "DateDebut" in conferences.columns
            else conferences
        )

        for _, conf in confs_display.iterrows():
            date_val = conf.get("DateDebut")
            date_str = date_val.strftime("%Y-%m-%d") if pd.notna(date_val) else "?"
            with st.expander(f"{date_str} — {conf.get('Titre', 'Conférence')} ({conf.get('Lieu', '?')})"):
                if conf.get("ObservationsGlobales"):
                    st.markdown(f"**Observations :** {conf['ObservationsGlobales']}")

                if not sessions.empty and "Conference" in sessions.columns:
                    sess_conf = sessions[sessions["Conference"] == conf.get("Titre", "")].copy()

                    if classe_conf != "Toutes" and "ClasseActif" in sess_conf.columns:
                        sess_conf = sess_conf[sess_conf["ClasseActif"] == classe_conf]
                    if org_conf != "Toutes" and "Organisation" in sess_conf.columns:
                        sess_conf = sess_conf[sess_conf["Organisation"] == org_conf]

                    if not sess_conf.empty:
                        st.markdown("**Sessions :**")
                        sess_cols = [c for c in ["Titre", "Organisation", "ClasseActif", "Interet", "PointsCles"] if c in sess_conf.columns]
                        st.dataframe(sess_conf[sess_cols], use_container_width=True, hide_index=True)
                    else:
                        st.caption("Aucune session correspondant aux filtres.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — Pipeline
# ═══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<span class="section-hdr">PIPELINE — GESTIONNAIRES POTENTIELS</span>', unsafe_allow_html=True)

    STADES = ["Identifié", "Rencontré", "Due diligence", "Décision"]

    if orgs.empty or "Type" not in orgs.columns:
        st.info("Aucune organisation dans SharePoint.")
    else:
        potentiels = orgs[orgs["Type"] == "Gestionnaire potentiel"].copy()

        if potentiels.empty:
            st.info(
                "Aucun gestionnaire potentiel dans le pipeline. "
                "Ajoutez des organisations avec le type 'Gestionnaire potentiel' dans SharePoint."
            )
        else:
            # Joindre la dernière date de rencontre
            if not rencontres.empty and "Organisation" in rencontres.columns and "DateRencontre" in rencontres.columns:
                derniere = (
                    rencontres.groupby("Organisation")["DateRencontre"]
                    .max()
                    .reset_index()
                    .rename(columns={"Organisation": "Titre", "DateRencontre": "DerniereRencontre"})
                )
                potentiels = potentiels.merge(derniere, on="Titre", how="left")

            stade_cols = st.columns(len(STADES))
            for i, stade in enumerate(STADES):
                with stade_cols[i]:
                    st.markdown(f"**{stade}**")
                    groupe = potentiels[potentiels.get("Statut", pd.Series()) == stade] if "Statut" in potentiels.columns else pd.DataFrame()

                    if groupe.empty:
                        st.caption("—")
                    else:
                        for _, row in groupe.iterrows():
                            dern = row.get("DerniereRencontre", pd.NaT)
                            dern_str = pd.Timestamp(dern).strftime("%Y-%m-%d") if pd.notna(dern) else "Jamais"
                            st.markdown(
                                f'<div class="pipeline-card">'
                                f'<b style="color:#F9FAFB">{row.get("Titre", "?")}</b><br>'
                                f'<span style="color:#9CA3AF;font-size:0.75rem">'
                                f'{row.get("ClasseActif", "?")}&nbsp;·&nbsp;{row.get("Region", "?")}</span><br>'
                                f'<span style="color:#6B7280;font-size:0.7rem">Dernière rencontre : {dern_str}</span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
