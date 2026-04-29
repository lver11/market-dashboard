# CRM Gestionnaires — Plan d'implémentation

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ajouter une page CRM à l'app Streamlit existante, lisant les données depuis 7 SharePoint Lists via Microsoft Graph API, avec 5 vues (Vue globale, Fiche gestionnaire, Revues trimestrielles, Conférences, Pipeline).

**Architecture:** SharePoint Lists (saisie collaborative, zéro install) → Microsoft Graph API (auth via Azure App Registration + MSAL) → Streamlit Cloud (lecture seule, cache 15 min, nouvelle page `6_CRM_Gestionnaires.py`).

**Tech Stack:** Python 3.x, Streamlit, MSAL (`msal`), Pandas, Plotly, Microsoft Graph API REST v1.0

**Spec:** `docs/superpowers/specs/2026-04-29-crm-gestionnaires-design.md`

---

## Chunk 1 : Prérequis et configuration SharePoint

### Tâche 1 : Créer les 7 listes SharePoint (manuel — guide étape par étape)

**Aucun fichier à modifier — étapes manuelles dans le navigateur.**

- [ ] **Étape 1 : Ouvrir SharePoint**
  Aller sur `https://<votre-tenant>.sharepoint.com/sites/<votre-site>` → cliquer **Contenu du site** → **Nouvelle** → **Liste**.

- [ ] **Étape 2 : Créer la liste `ClassesActifs`**
  Colonnes :
  - `Titre` (Texte, déjà présent)
  - `Description` (Texte multiligne)

- [ ] **Étape 3 : Créer la liste `Organisations`**
  Colonnes :
  - `Titre` (Texte — nom de l'organisation)
  - `Type` (Choix : `Gestionnaire actif`, `Gestionnaire potentiel`, `Consultant`)
  - `Statut` (Choix : `Actif`, `Pipeline`, `Sous surveillance`, `Rejeté`)
  - `ClasseActif` (Lookup → liste `ClassesActifs`, colonne `Titre`)
  - `AUM` (Nombre)
  - `Region` (Choix : `Amérique du Nord`, `Europe`, `Asie`, `Global`)
  - `SiteWeb` (Lien hypertexte)
  - `Notes` (Texte multiligne)

- [ ] **Étape 4 : Créer la liste `Contacts`**
  Colonnes :
  - `Titre` (Texte — prénom + nom)
  - `Prenom` (Texte)
  - `Organisation` (Lookup → `Organisations`, colonne `Titre`)
  - `Role` (Texte)
  - `Email` (Texte)
  - `Telephone` (Texte)
  - `LinkedIn` (Lien hypertexte)

- [ ] **Étape 5 : Créer la liste `Rencontres`**
  Colonnes :
  - `Titre` (Texte — description courte de la rencontre)
  - `DateRencontre` (Date et heure)
  - `Organisation` (Lookup → `Organisations`)
  - `TypeRencontre` (Choix : `Call`, `Visite sur place`, `Conférence`, `Webinaire`, `Repas`)
  - `Auteur` (Personne ou groupe)
  - `Resume` (Texte multiligne)
  - `PointsCles` (Texte multiligne)
  - `ActionsASuivre` (Texte multiligne)
  - `ProchaineEtape` (Texte)
  - `DateProchaineEtape` (Date et heure)

- [ ] **Étape 6 : Créer la liste `RevuesTrimestrielles`**
  Colonnes :
  - `Titre` (Texte — ex. : "Nom gestionnaire — Q1 2025")
  - `Organisation` (Lookup → `Organisations`)
  - `Trimestre` (Choix : `Q1 2025`, `Q2 2025`, `Q3 2025`, `Q4 2025`, `Q1 2026`, `Q2 2026`, `Q3 2026`, `Q4 2026`)
  - `Rendement` (Nombre)
  - `Benchmark` (Nombre)
  - `TrackingError` (Nombre)
  - `ScoreProcessus` (Choix : `1`, `2`, `3`, `4`, `5`)
  - `ScoreEquipe` (Choix : `1`, `2`, `3`, `4`, `5`)
  - `ScoreMandat` (Choix : `1`, `2`, `3`, `4`, `5`)
  - `RedFlags` (Texte multiligne)
  - `PointsPositifs` (Texte multiligne)
  - `Recommandation` (Choix : `Maintenir`, `Surveiller`, `Réduire`, `Terminer`)
  - `Auteur` (Personne ou groupe)
  - `Commentaires` (Texte multiligne)

- [ ] **Étape 7 : Créer la liste `Conferences`**
  Colonnes :
  - `Titre` (Texte — nom de la conférence)
  - `DateDebut` (Date et heure)
  - `DateFin` (Date et heure)
  - `Lieu` (Texte)
  - `ClasseActif` (Lookup → `ClassesActifs`)
  - `ObservationsGlobales` (Texte multiligne)

- [ ] **Étape 8 : Créer la liste `SessionsConference`**
  Colonnes :
  - `Titre` (Texte — intervenant ou titre de la session)
  - `Conference` (Lookup → `Conferences`)
  - `Organisation` (Lookup → `Organisations`)
  - `ClasseActif` (Lookup → `ClassesActifs`)
  - `Resume` (Texte multiligne)
  - `PointsCles` (Texte multiligne)
  - `Interet` (Choix : `1`, `2`, `3`, `4`, `5`)

- [ ] **Étape 9 : Récupérer l'ID du site SharePoint**

  Dans le navigateur, aller à :
  ```
  https://<votre-tenant>.sharepoint.com/sites/<votre-site>/_api/site/id
  ```
  Ou via Graph Explorer :
  ```
  https://graph.microsoft.com/v1.0/sites/<votre-tenant>.sharepoint.com:/sites/<votre-site>
  ```
  Copier la valeur de `id` — elle sera nécessaire dans les secrets Streamlit.

---

### Tâche 2 : Demande Azure App Registration à l'IT (guide)

**Aucun fichier à modifier — demande à transmettre à l'équipe IT.**

- [ ] **Étape 1 : Transmettre ce message à ton équipe IT**

  > Bonjour,
  > 
  > Pourriez-vous créer une **Azure App Registration** dans notre tenant Azure AD avec les paramètres suivants :
  > - **Nom** : `Fondaction-CRM-Streamlit`
  > - **Type** : Application (pas de compte utilisateur)
  > - **Permissions** : `Sites.Read.All` (lecture SharePoint via Microsoft Graph API)
  > - **Type d'authentification** : Client credentials (Client ID + Client Secret)
  > 
  > Une fois créée, j'aurais besoin de :
  > - `Application (client) ID`
  > - `Directory (tenant) ID`
  > - Un `Client Secret` (valable 12 mois minimum)
  > 
  > Merci !

- [ ] **Étape 2 : Recevoir les 3 valeurs de l'IT**
  - `AZURE_CLIENT_ID`
  - `AZURE_TENANT_ID`
  - `AZURE_CLIENT_SECRET`

- [ ] **Étape 3 : Ajouter les secrets dans Streamlit Cloud**

  Sur `share.streamlit.io` → ton app → **Settings** → **Secrets**, ajouter :
  ```toml
  [sharepoint]
  client_id = "xxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx"
  tenant_id = "xxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx"
  client_secret = "votre_secret_ici"
  site_id = "votre-tenant.sharepoint.com,xxxxx,xxxxx"

  [sharepoint.lists]
  organisations = "Organisations"
  contacts = "Contacts"
  rencontres = "Rencontres"
  revues = "RevuesTrimestrielles"
  conferences = "Conferences"
  sessions = "SessionsConference"
  classes_actifs = "ClassesActifs"
  ```

---

## Chunk 2 : Connecteur SharePoint Graph API

### Tâche 3 : Ajouter `msal` aux dépendances

**Fichier à modifier :** `requirements.txt`

- [ ] **Étape 1 : Ajouter msal**

  Ajouter cette ligne à `requirements.txt` :
  ```
  msal>=1.28.0
  ```

- [ ] **Étape 2 : Vérifier localement**
  ```bash
  pip install msal
  ```
  Résultat attendu : `Successfully installed msal-x.x.x`

- [ ] **Étape 3 : Commit**
  ```bash
  git add requirements.txt
  git commit -m "feat: add msal dependency for SharePoint Graph API"
  git push
  ```

---

### Tâche 4 : Créer le module connecteur SharePoint

**Fichier à créer :** `utils/sharepoint.py`

- [ ] **Étape 1 : Créer le dossier utils si absent**
  ```bash
  mkdir -p utils
  touch utils/__init__.py
  ```

- [ ] **Étape 2 : Créer `utils/sharepoint.py`**

  ```python
  """
  Connecteur Microsoft Graph API pour lire les SharePoint Lists de Fondaction.
  Auth via Azure App Registration (client credentials flow).
  """
  from __future__ import annotations

  import streamlit as st
  import pandas as pd
  import requests
  import msal

  GRAPH_BASE = "https://graph.microsoft.com/v1.0"
  SCOPE = ["https://graph.microsoft.com/.default"]


  @st.cache_resource
  def _get_token() -> str:
      """Obtenir un token MSAL (mis en cache pour la durée de la session)."""
      cfg = st.secrets["sharepoint"]
      app = msal.ConfidentialClientApplication(
          client_id=cfg["client_id"],
          authority=f"https://login.microsoftonline.com/{cfg['tenant_id']}",
          client_credential=cfg["client_secret"],
      )
      result = app.acquire_token_for_client(scopes=SCOPE)
      if "access_token" not in result:
          raise RuntimeError(f"Échec auth MSAL : {result.get('error_description')}")
      return result["access_token"]


  def _get_headers() -> dict:
      return {"Authorization": f"Bearer {_get_token()}", "Accept": "application/json"}


  @st.cache_data(ttl=900)
  def fetch_list(list_name: str) -> pd.DataFrame:
      """
      Lire tous les éléments d'une SharePoint List et retourner un DataFrame.
      TTL de 15 minutes pour limiter les appels API.
      """
      site_id = st.secrets["sharepoint"]["site_id"]
      url = f"{GRAPH_BASE}/sites/{site_id}/lists/{list_name}/items"
      params = {"expand": "fields", "$top": 999}

      items = []
      while url:
          resp = requests.get(url, headers=_get_headers(), params=params, timeout=30)
          resp.raise_for_status()
          data = resp.json()
          items.extend(data.get("value", []))
          url = data.get("@odata.nextLink")
          params = {}  # nextLink inclut déjà les paramètres

      if not items:
          return pd.DataFrame()

      rows = [item["fields"] for item in items]
      return pd.DataFrame(rows)


  def load_all() -> dict[str, pd.DataFrame]:
      """Charger toutes les listes en parallèle et retourner un dict de DataFrames."""
      list_keys = st.secrets["sharepoint"]["lists"]
      return {key: fetch_list(name) for key, name in list_keys.items()}
  ```

- [ ] **Étape 3 : Tester manuellement le connecteur (optionnel, local)**

  Créer un fichier `.streamlit/secrets.toml` local avec tes valeurs de test, puis :
  ```bash
  streamlit run streamlit_app.py
  ```
  Vérifier dans les logs qu'aucune erreur d'authentification n'apparaît.

- [ ] **Étape 4 : Commit**
  ```bash
  git add utils/__init__.py utils/sharepoint.py
  git commit -m "feat: add SharePoint Graph API connector with MSAL auth"
  git push
  ```

---

## Chunk 3 : Page Streamlit CRM — Vue globale et Fiche gestionnaire

### Tâche 5 : Créer la page principale CRM avec onglets

**Fichier à créer :** `pages/6_CRM_Gestionnaires.py`

- [ ] **Étape 1 : Créer le squelette de la page avec les 5 onglets**

  ```python
  """
  CRM Gestionnaires — Suivi des rencontres, revues trimestrielles et conférences.
  Données lues depuis SharePoint Lists via Microsoft Graph API.
  """
  from __future__ import annotations

  import pandas as pd
  import plotly.graph_objects as go
  import plotly.express as px
  import streamlit as st
  from datetime import datetime, timedelta
  from utils.sharepoint import load_all

  st.set_page_config(
      page_title="Fondaction — CRM Gestionnaires",
      page_icon="🏛️",
      layout="wide",
      initial_sidebar_state="collapsed",
  )

  # CSS cohérent avec le reste du dashboard
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
  </style>
  """)

  st.markdown('<p class="crm-title">CRM — Suivi Gestionnaires & Conférences</p>', unsafe_allow_html=True)

  # Chargement des données
  with st.spinner("Chargement des données SharePoint..."):
      try:
          data = load_all()
      except Exception as e:
          st.error(f"Erreur de connexion SharePoint : {e}")
          st.info("Vérifiez que les secrets Streamlit (client_id, tenant_id, client_secret, site_id) sont bien configurés.")
          st.stop()

  orgs = data["organisations"]
  contacts = data["contacts"]
  rencontres = data["rencontres"]
  revues = data["revues"]
  conferences = data["conferences"]
  sessions = data["sessions"]
  classes = data["classes_actifs"]

  # Normalisation des dates
  for df, col in [(rencontres, "DateRencontre"), (revues, ""), (conferences, "DateDebut")]:
      if col and col in df.columns:
          df[col] = pd.to_datetime(df[col], errors="coerce")

  tab1, tab2, tab3, tab4, tab5 = st.tabs([
      "Vue d'ensemble",
      "Fiche gestionnaire",
      "Revues trimestrielles",
      "Conférences & Veille",
      "Pipeline",
  ])
  ```

- [ ] **Étape 2 : Implémenter l'onglet Vue d'ensemble (Tab 1)**

  Ajouter après la définition des onglets :

  ```python
  with tab1:
      st.markdown('<span class="section-hdr">VUE D\'ENSEMBLE</span>', unsafe_allow_html=True)

      now = datetime.now()
      j30 = now - timedelta(days=30)
      j90 = now - timedelta(days=90)

      # KPIs
      if "DateRencontre" in rencontres.columns:
          nb_30 = rencontres[rencontres["DateRencontre"] >= j30].shape[0]
          nb_90 = rencontres[rencontres["DateRencontre"] >= j90].shape[0]
      else:
          nb_30 = nb_90 = 0

      nb_orgs = len(orgs) if not orgs.empty else 0

      col1, col2, col3 = st.columns(3)
      with col1:
          st.markdown(f'<div class="kpi-card"><div class="kpi-val">{nb_30}</div><div class="kpi-lbl">Rencontres (30 jours)</div></div>', unsafe_allow_html=True)
      with col2:
          st.markdown(f'<div class="kpi-card"><div class="kpi-val">{nb_90}</div><div class="kpi-lbl">Rencontres (90 jours)</div></div>', unsafe_allow_html=True)
      with col3:
          st.markdown(f'<div class="kpi-card"><div class="kpi-val">{nb_orgs}</div><div class="kpi-lbl">Organisations suivies</div></div>', unsafe_allow_html=True)

      st.divider()

      # Alertes — gestionnaires sans rencontre depuis >90 jours
      st.markdown('<span class="section-hdr">ALERTES — INACTIVITÉ +90 JOURS</span>', unsafe_allow_html=True)

      actifs = orgs[orgs.get("Statut", pd.Series()) == "Actif"]["Titre"].tolist() if "Statut" in orgs.columns and "Titre" in orgs.columns else []

      if actifs and not rencontres.empty and "DateRencontre" in rencontres.columns and "Organisation" in rencontres.columns:
          derniere = rencontres.groupby("Organisation")["DateRencontre"].max()
          inactifs = [o for o in actifs if o not in derniere.index or derniere[o] < j90]
          if inactifs:
              for org in inactifs[:10]:
                  st.markdown(f'<div class="alert-card">⚠️ {org} — aucune rencontre depuis +90 jours</div>', unsafe_allow_html=True)
          else:
              st.success("Tous les gestionnaires actifs ont été rencontrés dans les 90 derniers jours.")
      else:
          st.info("Données insuffisantes pour calculer les alertes.")

      st.divider()

      # Timeline des dernières rencontres
      st.markdown('<span class="section-hdr">DERNIÈRES RENCONTRES</span>', unsafe_allow_html=True)

      if not rencontres.empty and "DateRencontre" in rencontres.columns:
          cols_afficher = [c for c in ["DateRencontre", "Titre", "Organisation", "TypeRencontre", "Auteur"] if c in rencontres.columns]
          recent = rencontres.sort_values("DateRencontre", ascending=False).head(20)[cols_afficher]
          st.dataframe(recent, use_container_width=True, hide_index=True)
      else:
          st.info("Aucune rencontre enregistrée.")
  ```

- [ ] **Étape 3 : Implémenter l'onglet Fiche gestionnaire (Tab 2)**

  ```python
  with tab2:
      st.markdown('<span class="section-hdr">FICHE GESTIONNAIRE</span>', unsafe_allow_html=True)

      if orgs.empty or "Titre" not in orgs.columns:
          st.info("Aucune organisation dans SharePoint.")
      else:
          org_choisie = st.selectbox("Sélectionner une organisation", sorted(orgs["Titre"].dropna().tolist()))

          org_row = orgs[orgs["Titre"] == org_choisie]
          if not org_row.empty:
              r = org_row.iloc[0]
              col_a, col_b, col_c = st.columns(3)
              with col_a:
                  st.metric("Type", r.get("Type", "—"))
              with col_b:
                  st.metric("Statut", r.get("Statut", "—"))
              with col_c:
                  st.metric("AUM (G$)", r.get("AUM", "—"))

              if r.get("Notes"):
                  st.markdown(f"**Notes :** {r['Notes']}")

          st.divider()

          # Historique des rencontres
          st.markdown('<span class="section-hdr">HISTORIQUE DES RENCONTRES</span>', unsafe_allow_html=True)
          if not rencontres.empty and "Organisation" in rencontres.columns:
              r_org = rencontres[rencontres["Organisation"] == org_choisie].sort_values("DateRencontre", ascending=False) if "DateRencontre" in rencontres.columns else rencontres[rencontres["Organisation"] == org_choisie]
              if r_org.empty:
                  st.info("Aucune rencontre enregistrée pour cet organisme.")
              else:
                  for _, row in r_org.iterrows():
                      with st.expander(f"{row.get('DateRencontre', '').strftime('%Y-%m-%d') if pd.notna(row.get('DateRencontre')) else '?'} — {row.get('Titre', 'Rencontre')}"):
                          st.markdown(f"**Type :** {row.get('TypeRencontre', '—')} | **Auteur :** {row.get('Auteur', '—')}")
                          if row.get("Resume"):
                              st.markdown(f"**Résumé :** {row['Resume']}")
                          if row.get("PointsCles"):
                              st.markdown(f"**Points clés :** {row['PointsCles']}")
                          if row.get("ActionsASuivre"):
                              st.markdown(f"**Actions :** {row['ActionsASuivre']}")

          st.divider()

          # Évolution des scores de revue
          st.markdown('<span class="section-hdr">ÉVOLUTION DES SCORES DE REVUE</span>', unsafe_allow_html=True)
          if not revues.empty and "Organisation" in revues.columns:
              rev_org = revues[revues["Organisation"] == org_choisie]
              score_cols = [c for c in ["ScoreProcessus", "ScoreEquipe", "ScoreMandat"] if c in rev_org.columns]
              if not rev_org.empty and score_cols and "Trimestre" in rev_org.columns:
                  rev_org = rev_org.sort_values("Trimestre")
                  fig = go.Figure()
                  colors = {"ScoreProcessus": "#60A5FA", "ScoreEquipe": "#34D399", "ScoreMandat": "#FBBF24"}
                  for col in score_cols:
                      rev_org[col] = pd.to_numeric(rev_org[col], errors="coerce")
                      fig.add_trace(go.Scatter(
                          x=rev_org["Trimestre"], y=rev_org[col],
                          name=col.replace("Score", ""), mode="lines+markers",
                          line=dict(color=colors.get(col, "#9CA3AF"), width=2),
                      ))
                  fig.update_layout(
                      paper_bgcolor="#0B1120", plot_bgcolor="#111827",
                      font_color="#F9FAFB", yaxis=dict(range=[0, 5.5]),
                      legend=dict(bgcolor="#1F2937"), margin=dict(t=20, b=20),
                  )
                  st.plotly_chart(fig, use_container_width=True)
              else:
                  st.info("Aucune revue trimestrielle enregistrée.")
  ```

- [ ] **Étape 4 : Commit**
  ```bash
  git add pages/6_CRM_Gestionnaires.py
  git commit -m "feat: add CRM page — overview and manager profile tabs"
  git push
  ```

---

## Chunk 4 : Onglets Revues, Conférences et Pipeline

### Tâche 6 : Implémenter les 3 derniers onglets

**Fichier à modifier :** `pages/6_CRM_Gestionnaires.py`

- [ ] **Étape 1 : Onglet Revues trimestrielles (Tab 3)**

  ```python
  with tab3:
      st.markdown('<span class="section-hdr">REVUES TRIMESTRIELLES</span>', unsafe_allow_html=True)

      if revues.empty:
          st.info("Aucune revue trimestrielle enregistrée.")
      else:
          trimestres = sorted(revues["Trimestre"].dropna().unique().tolist(), reverse=True) if "Trimestre" in revues.columns else []
          if trimestres:
              trim_choisi = st.selectbox("Trimestre", trimestres)
              rev_trim = revues[revues["Trimestre"] == trim_choisi].copy()
          else:
              rev_trim = revues.copy()

          # Filtre classe d'actif
          if "ClasseActif" in orgs.columns and not orgs.empty:
              classes_dispo = ["Toutes"] + sorted(orgs["ClasseActif"].dropna().unique().tolist())
              classe_filtre = st.selectbox("Classe d'actif", classes_dispo)
              if classe_filtre != "Toutes" and "Organisation" in rev_trim.columns:
                  orgs_classe = orgs[orgs["ClasseActif"] == classe_filtre]["Titre"].tolist()
                  rev_trim = rev_trim[rev_trim["Organisation"].isin(orgs_classe)]

          # Tableau comparatif
          score_cols = [c for c in ["Organisation", "Rendement", "Benchmark", "TrackingError", "ScoreProcessus", "ScoreEquipe", "ScoreMandat", "Recommandation"] if c in rev_trim.columns]
          if score_cols:
              for col in ["Rendement", "Benchmark", "TrackingError", "ScoreProcessus", "ScoreEquipe", "ScoreMandat"]:
                  if col in rev_trim.columns:
                      rev_trim[col] = pd.to_numeric(rev_trim[col], errors="coerce")

              if "Rendement" in rev_trim.columns and "Benchmark" in rev_trim.columns:
                  rev_trim["Valeur ajoutée"] = (rev_trim["Rendement"] - rev_trim["Benchmark"]).round(2)

              st.dataframe(
                  rev_trim[score_cols + (["Valeur ajoutée"] if "Valeur ajoutée" in rev_trim.columns else [])],
                  use_container_width=True, hide_index=True,
              )

          st.divider()

          # Graphique évolution des scores par gestionnaire (tous trimestres)
          st.markdown('<span class="section-hdr">ÉVOLUTION DES SCORES — TOUS GESTIONNAIRES</span>', unsafe_allow_html=True)
          score_col = st.selectbox("Score à afficher", ["ScoreProcessus", "ScoreEquipe", "ScoreMandat"], key="score_global")

          if not revues.empty and score_col in revues.columns and "Trimestre" in revues.columns and "Organisation" in revues.columns:
              rev_plot = revues[["Trimestre", "Organisation", score_col]].copy()
              rev_plot[score_col] = pd.to_numeric(rev_plot[score_col], errors="coerce")
              rev_plot = rev_plot.sort_values("Trimestre")
              fig2 = px.line(rev_plot, x="Trimestre", y=score_col, color="Organisation",
                             markers=True, template="plotly_dark")
              fig2.update_layout(paper_bgcolor="#0B1120", plot_bgcolor="#111827",
                                 font_color="#F9FAFB", yaxis=dict(range=[0, 5.5]),
                                 legend=dict(bgcolor="#1F2937"), margin=dict(t=20, b=20))
              st.plotly_chart(fig2, use_container_width=True)
  ```

- [ ] **Étape 2 : Onglet Conférences & Veille (Tab 4)**

  ```python
  with tab4:
      st.markdown('<span class="section-hdr">CONFÉRENCES & VEILLE</span>', unsafe_allow_html=True)

      if conferences.empty:
          st.info("Aucune conférence enregistrée.")
      else:
          # Filtre classe d'actif
          filtre_cols = st.columns(2)
          with filtre_cols[0]:
              if not classes.empty and "Titre" in classes.columns:
                  classe_conf = st.selectbox("Classe d'actif", ["Toutes"] + sorted(classes["Titre"].dropna().tolist()), key="conf_classe")
              else:
                  classe_conf = "Toutes"

          with filtre_cols[1]:
              if not orgs.empty and "Titre" in orgs.columns:
                  org_conf = st.selectbox("Organisation mentionnée", ["Toutes"] + sorted(orgs["Titre"].dropna().tolist()), key="conf_org")
              else:
                  org_conf = "Toutes"

          # Liste des conférences
          confs_display = conferences.sort_values("DateDebut", ascending=False) if "DateDebut" in conferences.columns else conferences
          for _, conf in confs_display.iterrows():
              date_str = conf.get("DateDebut", pd.NaT)
              date_str = date_str.strftime("%Y-%m-%d") if pd.notna(date_str) else "?"
              with st.expander(f"{date_str} — {conf.get('Titre', 'Conférence')} ({conf.get('Lieu', '?')})"):
                  if conf.get("ObservationsGlobales"):
                      st.markdown(f"**Observations :** {conf['ObservationsGlobales']}")

                  # Sessions liées
                  if not sessions.empty and "Conference" in sessions.columns:
                      sess_conf = sessions[sessions["Conference"] == conf.get("Titre", "")]

                      # Filtre
                      if classe_conf != "Toutes" and "ClasseActif" in sess_conf.columns:
                          sess_conf = sess_conf[sess_conf["ClasseActif"] == classe_conf]
                      if org_conf != "Toutes" and "Organisation" in sess_conf.columns:
                          sess_conf = sess_conf[sess_conf["Organisation"] == org_conf]

                      if not sess_conf.empty:
                          st.markdown("**Sessions :**")
                          sess_cols = [c for c in ["Titre", "Organisation", "ClasseActif", "Interet", "PointsCles"] if c in sess_conf.columns]
                          st.dataframe(sess_conf[sess_cols], use_container_width=True, hide_index=True)
  ```

- [ ] **Étape 3 : Onglet Pipeline (Tab 5)**

  ```python
  with tab5:
      st.markdown('<span class="section-hdr">PIPELINE — GESTIONNAIRES POTENTIELS</span>', unsafe_allow_html=True)

      stades = ["Identifié", "Rencontré", "Due diligence", "Décision"]

      if orgs.empty or "Statut" not in orgs.columns:
          st.info("Aucune organisation dans SharePoint.")
      else:
          potentiels = orgs[orgs["Type"] == "Gestionnaire potentiel"].copy() if "Type" in orgs.columns else pd.DataFrame()

          if potentiels.empty:
              st.info("Aucun gestionnaire potentiel dans le pipeline. Ajoutez des organisations avec le type 'Gestionnaire potentiel' dans SharePoint.")
          else:
              # Dernière rencontre par organisation
              if not rencontres.empty and "Organisation" in rencontres.columns and "DateRencontre" in rencontres.columns:
                  derniere = rencontres.groupby("Organisation")["DateRencontre"].max().reset_index()
                  derniere.columns = ["Titre", "DerniereRencontre"]
                  potentiels = potentiels.merge(derniere, on="Titre", how="left")

              cols_pipeline = [c for c in ["Titre", "Statut", "ClasseActif", "Region", "AUM", "DerniereRencontre"] if c in potentiels.columns]

              # Affichage par stade (colonnes)
              stade_cols = st.columns(len(stades))
              for i, stade in enumerate(stades):
                  with stade_cols[i]:
                      st.markdown(f"**{stade}**")
                      if "Statut" in potentiels.columns:
                          groupe = potentiels[potentiels["Statut"] == stade]
                      else:
                          groupe = pd.DataFrame()

                      if groupe.empty:
                          st.caption("—")
                      else:
                          for _, row in groupe.iterrows():
                              derniere_str = row.get("DerniereRencontre", pd.NaT)
                              if pd.notna(derniere_str):
                                  derniere_str = pd.Timestamp(derniere_str).strftime("%Y-%m-%d")
                              else:
                                  derniere_str = "Jamais"
                              st.markdown(
                                  f"""<div style="background:#1F2937;border-radius:6px;padding:10px 14px;margin:6px 0;border:1px solid #374151;">
                                  <b style="color:#F9FAFB">{row.get('Titre','?')}</b><br>
                                  <span style="color:#9CA3AF;font-size:0.75rem">{row.get('ClasseActif','?')} · {row.get('Region','?')}</span><br>
                                  <span style="color:#6B7280;font-size:0.7rem">Dernière rencontre : {derniere_str}</span>
                                  </div>""",
                                  unsafe_allow_html=True
                              )
  ```

- [ ] **Étape 4 : Commit final**
  ```bash
  git add pages/6_CRM_Gestionnaires.py
  git commit -m "feat: complete CRM page with quarterly reviews, conferences and pipeline tabs"
  git push
  ```

---

## Chunk 5 : Vérification et mise en production

### Tâche 7 : Vérification complète

- [ ] **Étape 1 : Vérifier le déploiement Streamlit Cloud**

  Après le push, attendre ~2 minutes puis ouvrir l'URL de l'app.
  La nouvelle page "CRM Gestionnaires" doit apparaître dans le menu latéral.

- [ ] **Étape 2 : Tester avec des données réelles**

  Dans SharePoint, saisir au moins :
  - 2 organisations
  - 2 rencontres (dates différentes)
  - 1 revue trimestrielle

  Recharger la page Streamlit (le cache se renouvelle toutes les 15 min, ou redémarrer l'app depuis Streamlit Cloud).

- [ ] **Étape 3 : Vérifier les 5 onglets**

  - [ ] Vue d'ensemble : KPIs affichés, alertes fonctionnelles, timeline visible
  - [ ] Fiche gestionnaire : sélecteur fonctionnel, rencontres affichées, graphique de scores visible
  - [ ] Revues trimestrielles : tableau comparatif, filtre par trimestre et classe d'actif
  - [ ] Conférences : liste dépliable, sessions liées visibles
  - [ ] Pipeline : colonnes par stade, organisations bien catégorisées

- [ ] **Étape 4 : Partager le lien avec les collègues**

  L'URL Streamlit Cloud existante suffit — la nouvelle page est accessible à tous ceux qui ont déjà accès au dashboard.

---

## Résumé des fichiers touchés

| Fichier | Action | Description |
|---|---|---|
| `requirements.txt` | Modifier | Ajouter `msal>=1.28.0` |
| `utils/__init__.py` | Créer | Package Python |
| `utils/sharepoint.py` | Créer | Connecteur Graph API + cache |
| `pages/6_CRM_Gestionnaires.py` | Créer | Page CRM — 5 onglets |

## Prérequis avant de commencer le code

1. Listes SharePoint créées (Tâche 1)
2. Azure App Registration obtenue de l'IT (Tâche 2)
3. Secrets Streamlit configurés (Tâche 2, Étape 3)
