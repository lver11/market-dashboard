"""
Connecteur Microsoft Graph API pour lire les SharePoint Lists de Fondaction.
Auth via Azure App Registration (client credentials flow).
"""
from __future__ import annotations

import pandas as pd
import requests
import msal
import streamlit as st

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
SCOPE = ["https://graph.microsoft.com/.default"]


@st.cache_resource
def _get_msal_app() -> msal.ConfidentialClientApplication:
    """Créer l'objet MSAL une seule fois par session (gère le renouvellement de token en interne)."""
    cfg = st.secrets["sharepoint"]
    return msal.ConfidentialClientApplication(
        client_id=cfg["client_id"],
        authority=f"https://login.microsoftonline.com/{cfg['tenant_id']}",
        client_credential=cfg["client_secret"],
    )


def _get_headers() -> dict:
    result = _get_msal_app().acquire_token_for_client(scopes=SCOPE)
    if "access_token" not in result:
        raise RuntimeError(f"Échec auth MSAL : {result.get('error_description')}")
    return {"Authorization": f"Bearer {result['access_token']}", "Accept": "application/json"}


@st.cache_data(ttl=900)
def fetch_list(list_name: str) -> pd.DataFrame:
    """Lire tous les éléments d'une SharePoint List. Cache de 15 minutes."""
    site_id = st.secrets["sharepoint"]["site_id"]
    url = f"{GRAPH_BASE}/sites/{site_id}/lists/{list_name}/items"
    params: dict = {"expand": "fields", "$top": 999}

    items: list = []
    while url:
        resp = requests.get(url, headers=_get_headers(), params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        items.extend(data.get("value", []))
        url = data.get("@odata.nextLink")
        params = {}

    if not items:
        return pd.DataFrame()

    return pd.DataFrame([item["fields"] for item in items])


def load_all() -> dict[str, pd.DataFrame]:
    """Charger toutes les listes SharePoint et retourner un dict de DataFrames."""
    list_keys = st.secrets["sharepoint"]["lists"]
    return {key: fetch_list(name) for key, name in list_keys.items()}
