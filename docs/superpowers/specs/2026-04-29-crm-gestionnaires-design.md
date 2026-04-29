# Design : CRM Suivi Gestionnaires & Conférences — Fondaction

**Date :** 2026-04-29
**Statut :** Approuvé
**Architecture :** SharePoint Lists (saisie collaborative) + Streamlit (visualisation)

---

## Contexte

Fondaction a besoin d'un système de suivi permettant à toute l'équipe de :
- Consigner les rencontres avec gestionnaires (portefeuille + potentiels) et consultants
- Documenter les revues trimestrielles des gestionnaires actifs (due diligence allégée)
- Répertorier les conférences et leurs sessions individuelles
- Visualiser l'activité et les tendances via le dashboard Streamlit existant

**Contraintes :** Pas de droits d'administration sur les postes, suite Office 365 disponible, Streamlit Cloud déjà déployé.

---

## Architecture

```
SAISIE (navigateur, zéro install)
  └── SharePoint Lists (Office 365)
        ↓ Microsoft Graph API (lecture, cache 15 min)
VISUALISATION
  └── Streamlit Cloud (app existante, nouvelle page CRM)
```

---

## Entités SharePoint (7 listes)

### 1. Organisations
| Champ | Type | Notes |
|---|---|---|
| Nom | Texte | Nom du gestionnaire ou consultant |
| Type | Choix | Gestionnaire actif / Gestionnaire potentiel / Consultant |
| Statut | Choix | Actif / Pipeline / Sous surveillance / Rejeté |
| Classe d'actif principale | Lookup → Classes d'actifs | |
| AUM (G$) | Nombre | |
| Région | Choix | Amérique du Nord / Europe / Asie / Global |
| Site web | Lien | |
| Notes générales | Texte long | |

### 2. Contacts
| Champ | Type | Notes |
|---|---|---|
| Prénom | Texte | |
| Nom | Texte | |
| Organisation | Lookup → Organisations | |
| Rôle | Texte | ex. : Gérant de portefeuille, IR |
| Email | Email | |
| Téléphone | Texte | |
| LinkedIn | Lien | |

### 3. Rencontres
| Champ | Type | Notes |
|---|---|---|
| Date | Date | |
| Organisation(s) | Lookup → Organisations | Multi-valeur |
| Contact(s) | Lookup → Contacts | Multi-valeur |
| Type | Choix | Call / Visite sur place / Conférence / Webinaire / Repas |
| Auteur | Personne | Collègue ayant saisi la note |
| Résumé | Texte long | Narration libre |
| Points clés | Texte long | 3-5 bullets |
| Actions à suivre | Texte long | |
| Prochaine étape | Texte | |
| Date prochaine étape | Date | |

### 4. Revues trimestrielles
| Champ | Type | Notes |
|---|---|---|
| Organisation | Lookup → Organisations | |
| Trimestre | Choix | Q1 2025, Q2 2025, ... |
| Rendement (%) | Nombre | |
| Benchmark (%) | Nombre | |
| Valeur ajoutée (%) | Calculé | Rendement - Benchmark |
| Tracking error | Nombre | |
| Score processus | Choix | 1 à 5 |
| Score équipe | Choix | 1 à 5 |
| Score respect du mandat | Choix | 1 à 5 |
| Red flags | Texte long | |
| Points positifs | Texte long | |
| Recommandation | Choix | Maintenir / Surveiller / Réduire / Terminer |
| Auteur | Personne | |
| Commentaires narratifs | Texte long | |

### 5. Conférences
| Champ | Type | Notes |
|---|---|---|
| Nom | Texte | |
| Date début | Date | |
| Date fin | Date | |
| Lieu | Texte | |
| Classe d'actif principale | Lookup → Classes d'actifs | |
| Participants Fondaction | Personne (multi) | |
| Observations globales | Texte long | |

### 6. Sessions de conférence
| Champ | Type | Notes |
|---|---|---|
| Conférence | Lookup → Conférences | |
| Titre / Intervenant | Texte | |
| Organisation | Lookup → Organisations | |
| Classe d'actif | Lookup → Classes d'actifs | Multi-valeur |
| Résumé | Texte long | |
| Points clés | Texte long | |
| Intérêt (1-5) | Choix | |

### 7. Classes d'actifs
| Champ | Type |
|---|---|
| Nom | Texte |
| Description | Texte long |

---

## Dashboard Streamlit (5 pages)

### Page 1 — Vue d'ensemble
- KPIs : rencontres 30j / 90j, gestionnaires inactifs +90j
- Timeline des dernières rencontres (toute l'équipe)
- Carte de chaleur : fréquence des rencontres par organisation

### Page 2 — Fiche gestionnaire
- Sélecteur organisation → fiche complète
- Historique chronologique des rencontres
- Évolution des scores de revue trimestrielle (graphique)
- Actions ouvertes

### Page 3 — Revues trimestrielles
- Tableau comparatif par trimestre
- Évolution des scores dans le temps par gestionnaire
- Filtre par classe d'actif et recommandation

### Page 4 — Conférences & Veille
- Liste des conférences avec sessions liées
- Filtre par classe d'actif ou organisation
- Vue "par thème" : sessions regroupées par classe d'actif

### Page 5 — Pipeline
- Tableau des gestionnaires potentiels par stade
- Stades : Identifié → Rencontré → Due diligence → Décision
- Dernière interaction + prochaine étape

---

## Flux technique

### Authentification
- Azure App Registration (unique, demande à l'IT)
- Permissions requises : `Sites.Read.All` (lecture SharePoint)
- Credentials stockés dans Streamlit Secrets : `client_id`, `client_secret`, `tenant_id`

### Intégration Streamlit ↔ SharePoint
- Bibliothèque : `msal` (Microsoft Authentication Library) + appels REST Graph API
- Cache : `@st.cache_data(ttl=900)` — rafraîchissement toutes les 15 minutes
- Lecture seule depuis Streamlit (la saisie reste dans SharePoint)

### Déploiement
- Nouvelle page `pages/6_CRM_Gestionnaires.py` dans l'app existante
- Commit + push → déploiement automatique sur Streamlit Cloud

---

## Setup initial (une seule fois)

| Étape | Responsable | Durée estimée |
|---|---|---|
| Créer les 7 listes SharePoint | Utilisateur | ~1h |
| Demander Azure App Registration à l'IT | Utilisateur + IT | 15-30 min |
| Configurer Streamlit Secrets | Utilisateur | 5 min |
| Développer et déployer la page Streamlit | Développement | ~1 journée |
