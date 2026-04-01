"""
TD Sequential Monitor — DeMark (Page Streamlit)
Algorithme complet : Setup (1→9) + Countdown (1→13) + Perfected Setup
Source : Yahoo Finance via yfinance
"""
from __future__ import annotations

import warnings
warnings.filterwarnings("ignore")

import io
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="TD Sequential — DeMark",
    page_icon="🔵",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.html("""
<style>
  [data-testid="stAppViewContainer"] { background: #0D1B2A; }
  [data-testid="stHeader"]           { background: transparent; }
  section[data-testid="stSidebar"]   { background: #111827; }
  .block-container { padding-top:1.2rem; padding-bottom:2rem; max-width:1600px; }

  .page-title { font-size:1.5rem; font-weight:900; color:#F9FAFB; letter-spacing:.04em; }
  .page-sub   { font-size:.75rem; color:#6B7280; margin-top:3px; }

  .section-hdr {
    font-size:.6rem; letter-spacing:.2em; text-transform:uppercase;
    color:#9CA3AF; background:#1F2937; border-radius:4px;
    padding:3px 10px; display:inline-block; margin-bottom:8px;
  }

  /* Signal badges */
  .sig-buy  { background:rgba(0,230,118,.15); color:#00E676;
              border:1px solid rgba(0,230,118,.35); border-radius:4px;
              padding:3px 10px; font-size:.68rem; font-weight:700;
              display:inline-block; white-space:nowrap; }
  .sig-sell { background:rgba(255,82,82,.15); color:#FF5252;
              border:1px solid rgba(255,82,82,.35); border-radius:4px;
              padding:3px 10px; font-size:.68rem; font-weight:700;
              display:inline-block; white-space:nowrap; }
  .sig-warn { background:rgba(255,215,64,.15); color:#FFD740;
              border:1px solid rgba(255,215,64,.35); border-radius:4px;
              padding:3px 10px; font-size:.68rem; font-weight:700;
              display:inline-block; white-space:nowrap; }
  .sig-neut { background:rgba(107,114,128,.15); color:#9CA3AF;
              border:1px solid rgba(107,114,128,.25); border-radius:4px;
              padding:3px 10px; font-size:.68rem; font-weight:700;
              display:inline-block; white-space:nowrap; }

  .card {
    background:#111827; border:1px solid #1F2937; border-radius:10px;
    padding:14px 16px; margin-bottom:8px;
  }
  .ticker-name  { font-size:.72rem; color:#6B7280; }
  .ticker-price { font-size:1.15rem; font-weight:800; color:#F9FAFB; font-family:monospace; }
  .ticker-chg-up   { font-size:.78rem; font-weight:700; color:#34D399; }
  .ticker-chg-down { font-size:.78rem; font-weight:700; color:#F87171; }
  .bar-bg { background:#1F2937; border-radius:4px; height:6px; width:100%; }
  .bar-fill-buy  { background:linear-gradient(90deg,#065F46,#00E676); border-radius:4px; height:6px; }
  .bar-fill-sell { background:linear-gradient(90deg,#7F1D1D,#FF5252); border-radius:4px; height:6px; }
  .bar-fill-warn { background:linear-gradient(90deg,#78350F,#FFD740); border-radius:4px; height:6px; }
</style>
""")

# ── Tickers disponibles ───────────────────────────────────────────────────────
ALL_TICKERS: dict[str, str] = {
    "S&P 500":       "^GSPC",
    "Nasdaq 100":    "^NDX",
    "Russell 2000":  "^RUT",
    "Euro Stoxx 50": "^STOXX50E",
    "Nikkei 225":    "^N225",
    "Gold":          "GC=F",
    "WTI Crude":     "CL=F",
    "EUR/USD":       "EURUSD=X",
    "USD/CAD":       "CAD=X",
    "TLT (US 20Y)":  "TLT",
    "HYG (HY)":      "HYG",
    "VIX":           "^VIX",
}

# ── Algorithme TD Sequential (DeMark complet) ─────────────────────────────────
def td_sequential(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule le TD Sequential DeMark complet.
    Setup (1→9)     : Close[i] < Close[i-4] (buy) ou > (sell), 9 consécutifs
    Countdown (1→13): Close[i] ≤ Low[i-2] (buy) ou ≥ High[i-2] (sell)
    Perfected       : Low[bar8/9] ≤ min(Low[bar6,bar7]) pour buy
    """
    c = df["Close"].values.astype(float)
    h = df["High"].values.astype(float)
    lo = df["Low"].values.astype(float)
    n = len(c)

    sc = np.zeros(n, int)    # setup count (1–9)
    sd = np.zeros(n, int)    # setup direction  +1=buy  -1=sell
    pf = np.zeros(n, bool)   # perfected setup
    cc = np.zeros(n, int)    # countdown count (1–13)
    cd = np.zeros(n, int)    # countdown direction

    # ── Setup ─────────────────────────────────────────────────────────────────
    buy_s = sell_s = 0
    for i in range(4, n):
        if   c[i] < c[i - 4]: buy_s += 1; sell_s = 0
        elif c[i] > c[i - 4]: sell_s += 1; buy_s = 0
        else:                  buy_s = sell_s = 0

        if buy_s > 0:
            sc[i] = min(buy_s, 9); sd[i] = 1
            if buy_s == 9:
                ref = min(lo[i - 2], lo[i - 3])
                pf[i] = lo[i] <= ref or lo[i - 1] <= ref
        elif sell_s > 0:
            sc[i] = min(sell_s, 9); sd[i] = -1
            if sell_s == 9:
                ref = max(h[i - 2], h[i - 3])
                pf[i] = h[i] >= ref or h[i - 1] >= ref

    # ── Countdown ─────────────────────────────────────────────────────────────
    in_b = in_s = False
    b_cd = s_cd = 0
    for i in range(2, n):
        if sc[i] == 9:
            if sd[i] == 1:  in_b = True;  in_s = False; b_cd = 0
            else:           in_s = True;  in_b = False; s_cd = 0

        if in_b:
            if c[i] <= lo[i - 2]: b_cd = min(b_cd + 1, 13)
            cc[i] = b_cd; cd[i] = 1
            if b_cd >= 13: in_b = False
        elif in_s:
            if c[i] >= h[i - 2]: s_cd = min(s_cd + 1, 13)
            cc[i] = s_cd; cd[i] = -1
            if s_cd >= 13: in_s = False

    out = df.copy()
    out["sc"] = sc; out["sd"] = sd; out["pf"] = pf
    out["cc"] = cc; out["cd"] = cd
    return out


def signal_label(sc: int, sd: int, cc: int, cd: int, pf: bool) -> tuple[str, str]:
    """Retourne (label_html, type) pour affichage badge."""
    if cc >= 13:
        lbl  = "✅ ACHETER" if cd == 1 else "🔴 VENDRE"
        kind = "buy" if cd == 1 else "sell"
    elif sc >= 9:
        lbl  = "⚠ Watch Buy" if sd == 1 else "⚠ Watch Sell"
        kind = "warn"
    elif sc >= 7:
        lbl  = f"⏳ Setup {sc}/9 {'Buy' if sd==1 else 'Sell'}"
        kind = "warn"
    elif sc > 0:
        lbl  = f"Setup {sc}/9 {'Buy' if sd==1 else 'Sell'}"
        kind = "neut"
    else:
        lbl  = "— Attente"
        kind = "neut"
    return lbl, kind


@st.cache_data(ttl=300, show_spinner=False)
def fetch(yahoo_ticker: str, period: str = "6mo") -> pd.DataFrame | None:
    try:
        df = yf.Ticker(yahoo_ticker).history(period=period, interval="1d", auto_adjust=True)
        if df.empty:
            return None
        return td_sequential(df)
    except Exception:
        return None


def build_chart(df: pd.DataFrame, label: str) -> go.Figure:
    """Graphique chandelier + annotations Setup/Countdown."""
    fig = go.Figure()

    # Bougies
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        name=label,
        increasing_line_color="#00E676", increasing_fillcolor="rgba(0,230,118,.25)",
        decreasing_line_color="#FF5252", decreasing_fillcolor="rgba(255,82,82,.25)",
        line_width=1,
    ))

    # Numéros Setup (en vert/rouge)
    for i in range(len(df)):
        row = df.iloc[i]
        sc_v, sd_v = int(row["sc"]), int(row["sd"])
        cc_v, cd_v = int(row["cc"]), int(row["cd"])
        price = float(row["Close"])

        if sc_v > 0:
            color = "#00E676" if sd_v == 1 else "#FF5252"
            fig.add_annotation(
                x=df.index[i], y=price,
                text=str(sc_v),
                showarrow=False,
                font={"size": 8, "color": color, "family": "Calibri"},
                yshift=14 if sd_v == 1 else -14,
            )
        elif cc_v > 0:
            color = "#FFD740" if cd_v == 1 else "#FF9800"
            fig.add_annotation(
                x=df.index[i], y=price,
                text=f"c{cc_v}",
                showarrow=False,
                font={"size": 7, "color": color, "family": "Calibri"},
                yshift=20 if cd_v == 1 else -20,
            )

    fig.update_layout(
        paper_bgcolor="#0D1B2A", plot_bgcolor="#0D1B2A",
        font={"color": "#9CA3AF", "family": "Calibri"},
        xaxis={"rangeslider": {"visible": False}, "gridcolor": "#1F2937",
               "showgrid": True, "linecolor": "#1F2937"},
        yaxis={"gridcolor": "#1F2937", "showgrid": True, "linecolor": "#1F2937"},
        margin={"t": 30, "b": 20, "l": 50, "r": 20},
        height=340,
        showlegend=False,
    )
    return fig


def excel_report(results: dict) -> bytes:
    """Génère un rapport Excel en mémoire."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        rows = []
        for name, (df, close_v, chg) in results.items():
            last = df.iloc[-1]
            sc_v, sd_v = int(last["sc"]), int(last["sd"])
            cc_v, cd_v = int(last["cc"]), int(last["cd"])
            pf_v = bool(last["pf"])
            lbl, _ = signal_label(sc_v, sd_v, cc_v, cd_v, pf_v)
            rows.append({
                "Instrument":   name,
                "Dernier prix": round(close_v, 4),
                "Var % (1j)":   round(chg, 2),
                "Setup (1→9)":  sc_v if sc_v > 0 else "",
                "Direction":    "Buy" if sd_v == 1 else "Sell" if sd_v == -1 else "—",
                "Countdown (1→13)": cc_v if cc_v > 0 else "",
                "Perfected":    "✔" if pf_v and sc_v >= 9 else "—",
                "Signal":       lbl.replace("✅ ", "").replace("🔴 ", "").replace("⚠ ", "").replace("⏳ ", ""),
                "Mise à jour":  pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
            })
        pd.DataFrame(rows).to_excel(writer, index=False, sheet_name="TD Sequential")
    return output.getvalue()


# ── Interface ─────────────────────────────────────────────────────────────────
st.html("""
<div class="page-title">🔵 TD Sequential — DeMark</div>
<div class="page-sub">Setup (1→9) · Countdown (1→13) · Perfected Setup · Source : Yahoo Finance</div>
""")

# Sélection tickers + période
col_sel, col_per, col_spacer = st.columns([3, 1, 4])
with col_sel:
    selected = st.multiselect(
        "Instruments",
        options=list(ALL_TICKERS.keys()),
        default=["S&P 500", "Nasdaq 100", "Gold", "WTI Crude", "EUR/USD", "TLT (US 20Y)"],
        label_visibility="collapsed",
    )
with col_per:
    period = st.selectbox(
        "Période", ["3mo", "6mo", "1y", "2y"],
        index=1, label_visibility="collapsed"
    )

if not selected:
    st.info("Sélectionnez au moins un instrument.")
    st.stop()

# ── Chargement données ─────────────────────────────────────────────────────────
results: dict[str, tuple[pd.DataFrame, float, float]] = {}
with st.spinner("Chargement des données Yahoo Finance…"):
    for name in selected:
        ticker = ALL_TICKERS[name]
        df = fetch(ticker, period)
        if df is None or len(df) < 5:
            continue
        close_v = float(df["Close"].iloc[-1])
        close_prev = float(df["Close"].iloc[-2]) if len(df) > 1 else close_v
        chg = (close_v - close_prev) / close_prev * 100
        results[name] = (df, close_v, chg)

if not results:
    st.error("Aucune donnée disponible. Réessayez dans quelques instants.")
    st.stop()

# ── Tableau de bord — cartes signaux ─────────────────────────────────────────
st.html('<div class="section-hdr">TABLEAU DE BORD</div>')

cols = st.columns(min(len(results), 4))
for i, (name, (df, close_v, chg)) in enumerate(results.items()):
    last = df.iloc[-1]
    sc_v, sd_v = int(last["sc"]), int(last["sd"])
    cc_v, cd_v = int(last["cc"]), int(last["cd"])
    pf_v = bool(last["pf"])
    lbl, kind = signal_label(sc_v, sd_v, cc_v, cd_v, pf_v)

    # Barre de progression Setup
    pct_setup = int(sc_v / 9 * 100) if sc_v > 0 else 0
    pct_cd    = int(cc_v / 13 * 100) if cc_v > 0 else 0
    bar_class = "bar-fill-buy" if sd_v == 1 else "bar-fill-sell" if sd_v == -1 else "bar-fill-warn"
    chg_class = "ticker-chg-up" if chg >= 0 else "ticker-chg-down"
    chg_sign  = "+" if chg >= 0 else ""
    badge_class = f"sig-{kind}"
    perf_badge = ' <span style="color:#FFD740;font-size:.62rem">✔ Perfected</span>' if pf_v and sc_v >= 9 else ""

    with cols[i % 4]:
        st.html(f"""
        <div class="card">
          <div class="ticker-name">{name}</div>
          <div style="display:flex;align-items:baseline;gap:8px;margin:4px 0">
            <span class="ticker-price">{close_v:,.4f}</span>
            <span class="{chg_class}">{chg_sign}{chg:.2f}%</span>
          </div>
          <div style="margin:8px 0">
            <span class="{badge_class}">{lbl}</span>{perf_badge}
          </div>
          <div style="margin-top:10px">
            <div style="display:flex;justify-content:space-between;font-size:.62rem;color:#6B7280;margin-bottom:3px">
              <span>Setup {sc_v}/9</span>
              <span>Countdown {cc_v}/13</span>
            </div>
            <div class="bar-bg"><div class="{bar_class}" style="width:{pct_setup}%"></div></div>
            <div style="height:4px"></div>
            <div class="bar-bg"><div class="bar-fill-warn" style="width:{pct_cd}%"></div></div>
          </div>
        </div>
        """)

# ── Graphiques chandelier ─────────────────────────────────────────────────────
st.html('<div class="section-hdr" style="margin-top:16px">GRAPHIQUES — SETUP & COUNTDOWN</div>')

chart_items = list(results.items())
for row_start in range(0, len(chart_items), 2):
    chunk = chart_items[row_start:row_start + 2]
    gcols = st.columns(len(chunk))
    for j, (name, (df, _, _)) in enumerate(chunk):
        with gcols[j]:
            st.plotly_chart(build_chart(df, name), use_container_width=True, key=f"chart_{name}")

# ── Tableau récapitulatif ─────────────────────────────────────────────────────
st.html('<div class="section-hdr" style="margin-top:8px">RÉCAPITULATIF</div>')

table_rows = []
for name, (df, close_v, chg) in results.items():
    last = df.iloc[-1]
    sc_v, sd_v = int(last["sc"]), int(last["sd"])
    cc_v, cd_v = int(last["cc"]), int(last["cd"])
    pf_v = bool(last["pf"])
    lbl, _ = signal_label(sc_v, sd_v, cc_v, cd_v, pf_v)
    table_rows.append({
        "Instrument":     name,
        "Prix":           f"{close_v:,.4f}",
        "Var %":          f"{'+'if chg>=0 else ''}{chg:.2f}%",
        "Setup (1→9)":    str(sc_v) if sc_v > 0 else "—",
        "Dir. Setup":     "↓ Buy" if sd_v == 1 else "↑ Sell" if sd_v == -1 else "—",
        "Countdown":      str(cc_v) if cc_v > 0 else "—",
        "Perfected":      "✔" if pf_v and sc_v >= 9 else "—",
        "Signal global":  lbl,
    })

st.dataframe(
    pd.DataFrame(table_rows),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Var %": st.column_config.TextColumn(),
        "Signal global": st.column_config.TextColumn(),
    },
)

# ── Légende algo ──────────────────────────────────────────────────────────────
with st.expander("📖 Algorithme DeMark TD Sequential"):
    st.markdown("""
**Setup (1 → 9)**
- **Buy Setup** : 9 barres consécutives où `Close[i] < Close[i-4]`
- **Sell Setup** : 9 barres consécutives où `Close[i] > Close[i-4]`

**Countdown (1 → 13)** *(démarre après un Setup complet)*
- **Buy Countdown** : `Close[i] ≤ Low[i-2]` — compter jusqu'à 13
- **Sell Countdown** : `Close[i] ≥ High[i-2]` — compter jusqu'à 13

**Perfected Setup**
- **Buy** : `Low[barre 8 ou 9] ≤ min(Low[barre 6], Low[barre 7])`
- **Sell** : `High[barre 8 ou 9] ≥ max(High[barre 6], High[barre 7])`

**Signaux**
| État | Signification |
|------|---------------|
| ✅ ACHETER | Countdown Buy = 13 (signal complet) |
| 🔴 VENDRE  | Countdown Sell = 13 (signal complet) |
| ⚠ Watch   | Setup = 9, countdown en cours |
| ⏳ Setup   | Setup en progression (7–8 barres) |
""")

# ── Export Excel ──────────────────────────────────────────────────────────────
st.download_button(
    label="⬇ Télécharger Excel",
    data=excel_report(results),
    file_name=f"TD_Sequential_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=False,
)
