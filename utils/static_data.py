"""
Static reference data shared by streamlit_app.py, pages/2_Oil_LNG.py and app.py.

Everything here is entered by hand (live prices come from yfinance / Bank of Canada).
Update this single file when refreshing the dashboard.

Last refresh: 2026-11-12
Sources: Federal Reserve, ECB, Bank of Canada, Bank of England, Bank of Japan, SNB,
BLS, BEA, EIA Weekly Petroleum Status Report, OPEC (press releases + MOMR).
"""

DATA_AS_OF = "2026-11-12"

# ── Economic calendar ─────────────────────────────────────────────────────────
# The dashboard only shows events from 2 days ago to 35 days ahead.
ECONOMIC_CALENDAR = [
    {"date": "2026-11-06", "event": "Non-Farm Payrolls (Oct)",         "country": "US", "importance": "critical", "forecast": "65K",       "previous": "60K",             "actual": "165K"},
    {"date": "2026-11-06", "event": "Unemployment Rate (Oct)",         "country": "US", "importance": "high",     "forecast": "4.2%",      "previous": "4.2%",            "actual": "4.1%"},
    {"date": "2026-11-10", "event": "CPI MoM (Oct)",                   "country": "US", "importance": "critical", "forecast": "0.3%",      "previous": "0.6%",            "actual": "0.4%"},
    {"date": "2026-11-10", "event": "Core CPI MoM (Oct)",              "country": "US", "importance": "critical", "forecast": "0.2%",      "previous": "0.3%",            "actual": "0.3%"},
    {"date": "2026-11-12", "event": "EIA Crude Inventories",           "country": "US", "importance": "medium",   "forecast": "-1.1M",     "previous": "-0.9M",           "actual": "+4.7M"},
    {"date": "2026-11-13", "event": "PPI (Oct)",                       "country": "US", "importance": "high",     "forecast": None,        "previous": None},
    {"date": "2026-11-17", "event": "US Retail Sales (Oct)",           "country": "US", "importance": "high",     "forecast": None,        "previous": None},
    {"date": "2026-11-18", "event": "FOMC Minutes (Oct)",              "country": "US", "importance": "high",     "forecast": None,        "previous": None},
    {"date": "2026-11-25", "event": "PCE Price Index (Oct)",           "country": "US", "importance": "critical", "forecast": None,        "previous": "3.6% a/a"},
    {"date": "2026-11-25", "event": "GDP Q3 2026 (2nd Est.)",          "country": "US", "importance": "high",     "forecast": None,        "previous": None},
    {"date": "2026-11-29", "event": "OPEC+ Ministerial (quotas 2027)", "country": "OPEC", "importance": "high",   "forecast": None,        "previous": None},
    {"date": "2026-12-01", "event": "ISM Manufacturing PMI (Nov)",     "country": "US", "importance": "high",     "forecast": None,        "previous": "55.5"},
    {"date": "2026-12-04", "event": "Non-Farm Payrolls (Nov)",         "country": "US", "importance": "critical", "forecast": None,        "previous": "165K"},
    {"date": "2026-12-09", "event": "BoC Rate Decision",               "country": "CA", "importance": "critical", "forecast": None,        "previous": "2.50%"},
    {"date": "2026-12-09", "event": "FOMC Rate Decision + SEP",        "country": "US", "importance": "critical", "forecast": None,        "previous": "3.75-4.00%"},
    {"date": "2026-12-10", "event": "CPI (Nov) — retour du a/a",       "country": "US", "importance": "critical", "forecast": None,        "previous": "3.7% a/a (sept.)"},
    {"date": "2026-12-10", "event": "SNB Rate Decision",               "country": "CH", "importance": "high",     "forecast": None,        "previous": "0.00%"},
    {"date": "2026-12-17", "event": "ECB Rate Decision + projections", "country": "EU", "importance": "critical", "forecast": None,        "previous": "2.50% (dépôt)"},
    {"date": "2026-12-17", "event": "BoE Rate Decision",               "country": "GB", "importance": "critical", "forecast": None,        "previous": "4.00%"},
    {"date": "2026-12-18", "event": "BOJ Rate Decision",               "country": "JP", "importance": "high",     "forecast": None,        "previous": "1.25%"},
]

# ── Geopolitical risks (main page) ────────────────────────────────────────────
GEOPOLITICAL_RISKS = [
    {"region": "Moyen-Orient", "title": "Guerre US/Israël–Iran & Hormuz",     "level": "high",   "icon": "flame",
     "description": "Conflit depuis le 28 fév. 2026; cessez-le-feu fragiles. Pourparlers via le Qatar; flux du Golfe en reprise mais attaques sporadiques sur des pétroliers.",
     "market_impact": "Prime de risque pétrole, inflation mondiale, taux longs"},
    {"region": "Mer Rouge",    "title": "Houthis / Bab al-Mandeb",            "level": "high",   "icon": "alert-triangle",
     "description": "Attaques houthies sur la mer Rouge et l'Arabie saoudite; la route de contournement de Yanbu est menacée.",
     "market_impact": "Fret, assurance maritime, exportations saoudiennes"},
    {"region": "Europe",       "title": "Guerre Ukraine–Russie",              "level": "high",   "icon": "sword",
     "description": "Pourparlers trilatéraux à Abou Dhabi (10-11 nov.), les premiers depuis février. Frappes longue portée sur les infrastructures énergétiques.",
     "market_impact": "Énergie, raffinage russe, actions européennes"},
    {"region": "Global",       "title": "Resserrement monétaire synchronisé", "level": "medium", "icon": "bar-chart-2",
     "description": "Hausses en 2026 : Fed, BCE, BdC, BoE et BoJ. Inflation US autour de 4 % a/a, zone euro à 4.0 % en oct.",
     "market_impact": "Taux longs, valorisations, devises"},
    {"region": "Amériques",    "title": "Soutenabilité budgétaire US",        "level": "medium", "icon": "dollar-sign",
     "description": "Dette fédérale ~40 T$; 10 ans US à 5.28 % fin sept. (plus haut depuis 2007). Midterms : gouvernement divisé.",
     "market_impact": "Prime de terme, USD long terme, notations souveraines"},
    {"region": "Amériques",    "title": "Tarifs US & contre-tarifs",          "level": "medium", "icon": "trending-down",
     "description": "Nouveaux tarifs américains et contre-tarifs canadiens; pression sur les coûts et les attentes d'inflation.",
     "market_impact": "Commerce mondial, marges, CAD"},
]

# ── Central bank policy rates ─────────────────────────────────────────────────
# change = direction of the last move.
CENTRAL_BANK_RATES = [
    {"flag": "🇺🇸", "name": "États-Unis",  "bank": "Fed", "rate": "3.75–4.00%",   "bias": "hawkish", "change": "↑", "next_meeting": "8-9 déc. 2026"},
    {"flag": "🇪🇺", "name": "Zone Euro",   "bank": "BCE", "rate": "2.50% (dépôt)", "bias": "hawkish", "change": "↑", "next_meeting": "17 déc. 2026"},
    {"flag": "🇨🇦", "name": "Canada",      "bank": "BdC", "rate": "2.50%",        "bias": "hawkish", "change": "↑", "next_meeting": "9 déc. 2026"},
    {"flag": "🇬🇧", "name": "Royaume-Uni", "bank": "BOE", "rate": "4.00%",        "bias": "hawkish", "change": "↑", "next_meeting": "17 déc. 2026"},
    {"flag": "🇯🇵", "name": "Japon",       "bank": "BOJ", "rate": "1.25%",        "bias": "hawkish", "change": "↑", "next_meeting": "18 déc. 2026"},
    {"flag": "🇨🇭", "name": "Suisse",      "bank": "BNS", "rate": "0.00%",        "bias": "neutral", "change": "=", "next_meeting": "10 déc. 2026"},
]

# ── EIA weekly petroleum status (week ending report_date) ─────────────────────
# value None = level not published in the source used; the change is still shown.
EIA_INVENTORY = {
    "report_date":   "2026-11-06",
    "crude_oil":     {"value": 414.4, "change": +4.7, "unit": "MMbbl", "label": "Crude Oil"},
    "gasoline":      {"value": 210.8, "change": +1.8, "unit": "MMbbl", "label": "Gasoline"},
    "distillates":   {"value": 103.3, "change": +4.1, "unit": "MMbbl", "label": "Distillates"},
    "cushing":       {"value": None,  "change": +0.1, "unit": "MMbbl", "label": "Cushing, OK"},
    "spr":           {"value": 279.5, "change": -2.6, "unit": "MMbbl", "label": "SPR"},
    "refinery_util": {"value":  95.2, "change": +0.7, "unit": "%",     "label": "Refinery Util."},
}

# ── OPEC+ ─────────────────────────────────────────────────────────────────────
# Quotas = "required production" for Nov.–Dec. 2026 of the seven core members.
# Per-country output is omitted: the war makes quotas largely theoretical.
OPEC_DATA = {
    "report_month":            "Oct. 2026 (MOMR nov.)",
    "total_production_mmbpd":  43.02,   # whole OPEC+ crude output, October 2026
    "opec_plus_target_mmbpd":  None,
    "compliance_pct":          None,
    "surplus_mmbpd":           None,
    "next_meeting":            "29 nov. 2026 (ministérielle, quotas 2027)",
    "note":                    "Quotas en grande partie théoriques : les exportations du Golfe restent perturbées par la guerre (Hormuz).",
    "key_producers": [
        {"country": "Saudi Arabia", "flag": "SA", "production": None, "quota": 10.5},
        {"country": "Russia",       "flag": "RU", "production": None, "quota": 9.9},
        {"country": "Iraq",         "flag": "IQ", "production": None, "quota": 4.4},
        {"country": "Kuwait",       "flag": "KW", "production": None, "quota": 2.7},
        {"country": "Kazakhstan",   "flag": "KZ", "production": None, "quota": 1.6},
    ],
}

# ── Energy geopolitical risks (Oil & LNG page) ────────────────────────────────
ENERGY_GEO_RISKS = [
    {"region": "Middle East",     "title": "Strait of Hormuz",          "level": "high",   "icon": "ship",
     "description": "Iran contrôle le passage depuis fév. 2026. Les exportations du Golfe reprennent sous escorte, mais des pétroliers sont encore attaqués.",
     "market_impact": "Brent très sensible aux pourparlers US–Iran (-16 % la semaine du 2 nov.)"},
    {"region": "Red Sea",         "title": "Bab al-Mandeb / Houthis",   "level": "high",   "icon": "alert-triangle",
     "description": "Les Houthis menacent la mer Rouge et Yanbu, principale route de contournement saoudienne.",
     "market_impact": "Fret et assurance; risque sur les exportations saoudiennes"},
    {"region": "Russia / Europe", "title": "Frappes sur le raffinage russe", "level": "medium", "icon": "flame",
     "description": "Capacité de raffinage russe réduite d'environ 30 % depuis fin oct. (drones ukrainiens). Pourparlers de paix à Abou Dhabi.",
     "market_impact": "Marges diesel élevées; exportations de produits russes"},
    {"region": "US Gulf Coast",   "title": "LNG Export Expansion",      "level": "medium", "icon": "anchor",
     "description": "Nouvelles capacités d'exportation de GNL américain; part de marché US en hausse.",
     "market_impact": "Structurellement haussier pour Henry Hub"},
    {"region": "United States",   "title": "Production US record",      "level": "low",    "icon": "trending-up",
     "description": "Production de brut record à 14,01 mb/j (sem. du 6 nov.); utilisation des raffineries à 95 %.",
     "market_impact": "Tempère la prime de risque; exportations US en hausse"},
    {"region": "Libya / Nigeria", "title": "African Supply Disruptions", "level": "medium", "icon": "alert-triangle",
     "description": "Interruptions périodiques liées à l'instabilité politique et au sabotage d'oléoducs.",
     "market_impact": "+2-5 $/b lors d'interruptions majeures"},
]
