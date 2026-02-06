import os
import json
import pandas as pd
import numpy as np
import yfinance as yf
from flask import Flask, render_template, jsonify, request
import traceback
from datetime import datetime

app = Flask(__name__)

# Try to import ta library for technical indicators
try:
    from ta.momentum import RSIIndicator
    from ta.trend import MACD
    from ta.volatility import BollingerBands

    TA_AVAILABLE = True
    print("✅ ta library available for technical indicators")
except ImportError:
    TA_AVAILABLE = False
    print("⚠️  ta library not available, using manual calculations")

# Sector mapping
SECTOR_MAP = {
    "AAPL": "Tech",
    "MSFT": "Tech",
    "NVDA": "Tech",
    "AVGO": "Tech",
    "ORCL": "Tech",
    "CRM": "Tech",
    "AMD": "Tech",
    "ADBE": "Tech",
    "CSCO": "Tech",
    "INTC": "Tech",
    "JPM": "Fin",
    "BAC": "Fin",
    "WFC": "Fin",
    "GS": "Fin",
    "MS": "Fin",
    "V": "Fin",
    "MA": "Fin",
    "BRK-B": "Fin",
    "BLK": "Fin",
    "SCHW": "Fin",
    "LLY": "Health",
    "UNH": "Health",
    "JNJ": "Health",
    "ABBV": "Health",
    "MRK": "Health",
    "PFE": "Health",
    "TMO": "Health",
    "ABT": "Health",
    "BMY": "Health",
    "AMGN": "Health",
    "XOM": "Energy",
    "CVX": "Energy",
    "COP": "Energy",
    "SLB": "Energy",
    "EOG": "Energy",
    "AMZN": "Cons",
    "TSLA": "Cons",
    "HD": "Cons",
    "MCD": "Cons",
    "NKE": "Cons",
    "WMT": "Staple",
    "PG": "Staple",
    "COST": "Staple",
    "KO": "Staple",
    "PEP": "Staple",
    "CAT": "Indust",
    "GE": "Indust",
    "HON": "Indust",
    "BA": "Indust",
    "UPS": "Indust",
    "LIN": "Mater",
    "APD": "Mater",
    "SHW": "Mater",
    "FCX": "Mater",
    "DOW": "Mater",
    "NEE": "Util",
    "SO": "Util",
    "DUK": "Util",
    "CEG": "Util",
    "SRE": "Util",
    "PLD": "REIT",
    "AMT": "REIT",
    "EQIX": "REIT",
    "SPG": "REIT",
    "O": "REIT",
    "META": "Comm",
    "GOOGL": "Comm",
    "NFLX": "Comm",
    "DIS": "Comm",
    "VZ": "Comm",
    "GOOG": "Comm",
    "CMCSA": "Comm",
    "TMUS": "Comm",
    "CHTR": "Comm",
}

SECTOR_CACHE_FILE = "sector_cache.json"


def _load_sector_cache():
    try:
        if os.path.exists(SECTOR_CACHE_FILE):
            with open(SECTOR_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError, OSError):
        pass
    return {}


def _save_sector_cache(cache):
    try:
        with open(SECTOR_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving sector cache: {e}")


_sector_cache = _load_sector_cache()


def get_sector(ticker):
    global _sector_cache
    if ticker in SECTOR_MAP:
        return SECTOR_MAP[ticker]
    if ticker in _sector_cache:
        return _sector_cache[ticker]
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        sector = info.get("sector", "")
        sector_map = {
            "Technology": "Tech",
            "Information Technology": "Tech",
            "Healthcare": "Health",
            "Health Care": "Health",
            "Financials": "Fin",
            "Financial Services": "Fin",
            "Consumer Discretionary": "Cons",
            "Consumer Cyclical": "Cons",
            "Consumer Staples": "Staple",
            "Consumer Defensive": "Staple",
            "Energy": "Energy",
            "Industrials": "Indust",
            "Materials": "Mater",
            "Basic Materials": "Mater",
            "Utilities": "Util",
            "Real Estate": "REIT",
            "Communication Services": "Comm",
        }
        short_sector = sector_map.get(sector, sector[:5] if sector else "-")
        _sector_cache[ticker] = short_sector
        _save_sector_cache(_sector_cache)
        return short_sector
    except Exception:
        _sector_cache[ticker] = "-"
        _save_sector_cache(_sector_cache)
        return "-"


# =============================================================================
# TECHNICAL INDICATOR CALCULATION FUNCTIONS
# =============================================================================


def calculate_rsi_manual(prices, period=14):
    """Calculate RSI manually using Wilder's RSI formula"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd_manual(prices, window_slow=26, window_fast=12, window_sign=9):
    """Calculate MACD manually"""
    exp1 = prices.ewm(span=window_fast, adjust=False).mean()
    exp2 = prices.ewm(span=window_slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=window_sign, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_bollinger_bands_manual(prices, window=20, num_std=2):
    """Calculate Bollinger Bands manually"""
    sma = prices.rolling(window=window).mean()
    std = prices.rolling(window=window).std()
    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)
    return upper_band, sma, lower_band


def detect_support_resistance(df, window=10, cluster_pct=0.02):
    """
    Detect support and resistance levels using local minima/maxima

    Args:
        df: DataFrame with 'High' and 'Low' columns
        window: Window size for finding local extrema (default: 10 periods)
        cluster_pct: Threshold for clustering levels (default: 2%)

    Returns:
        tuple: (list of support levels, list of resistance levels)
    """
    supports = []
    resistances = []

    high = df["High"].values
    low = df["Low"].values

    # Find local minima (support) and maxima (resistance)
    for i in range(window, len(df) - window):
        # Check for local minimum (support)
        if low[i] == np.min(low[i - window : i + window + 1]):
            supports.append(float(low[i]))

        # Check for local maximum (resistance)
        if high[i] == np.max(high[i - window : i + window + 1]):
            resistances.append(float(high[i]))

    # Cluster levels within threshold
    def cluster_levels(levels):
        if not levels:
            return []

        levels = sorted(levels)
        clusters = []
        current_cluster = [levels[0]]

        for level in levels[1:]:
            if (level - current_cluster[0]) / current_cluster[0] <= cluster_pct:
                current_cluster.append(level)
            else:
                # Average the cluster and add to results
                clusters.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [level]

        # Add the last cluster
        if current_cluster:
            clusters.append(sum(current_cluster) / len(current_cluster))

        # Return top 5 most recent (highest) levels
        return [round(c, 2) for c in clusters[-5:]]

    return cluster_levels(supports), cluster_levels(resistances)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/us/portfolio")
def get_us_portfolio_data():
    try:
        market_indices = []
        indices_map = {
            "^DJI": "Dow Jones",
            "^GSPC": "S&P 500",
            "^IXIC": "NASDAQ",
            "^RUT": "Russell 2000",
            "^VIX": "VIX",
            "GC=F": "Gold",
            "CL=F": "Crude Oil",
            "BTC-USD": "Bitcoin",
            "^TNX": "10Y Treasury",
            "DX-Y.NYB": "Dollar Index",
            "KRW=X": "USD/KRW",
        }
        for ticker, name in indices_map.items():
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="5d")
                if not hist.empty and len(hist) >= 2:
                    current_val = float(hist["Close"].iloc[-1])
                    prev_val = float(hist["Close"].iloc[-2])
                    change = current_val - prev_val
                    change_pct = (change / prev_val) * 100
                    market_indices.append(
                        {
                            "name": name,
                            "price": f"{current_val:,.2f}",
                            "change": f"{change:,.2f}",
                            "change_pct": round(change_pct, 2),
                            "color": "green" if change >= 0 else "red",
                        }
                    )
            except Exception:
                pass

        return jsonify(
            {"market_indices": market_indices, "top_holdings": [], "style_box": {}}
        )
    except Exception as e:
        print(f"Error getting US portfolio data: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/us/smart-money")
def get_us_smart_money():
    try:
        import json

        current_file = "us_market/smart_money_current.json"
        if os.path.exists(current_file):
            with open(current_file, "r", encoding="utf-8") as f:
                snapshot = json.load(f)
            tickers = [p["ticker"] for p in snapshot["picks"]]
            current_prices = {}
            for ticker in tickers:
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period="5d")
                    if not hist.empty:
                        current_prices[ticker] = round(float(hist["Close"].iloc[-1]), 2)
                except Exception:
                    pass

            picks_with_perf = []
            for pick in snapshot["picks"]:
                ticker = pick["ticker"]
                price_at_rec = pick.get("price_at_analysis", 0) or 0
                current_price = (
                    current_prices.get(ticker, price_at_rec) or price_at_rec or 0
                )
                import math

                if isinstance(price_at_rec, float) and math.isnan(price_at_rec):
                    price_at_rec = 0
                if isinstance(current_price, float) and math.isnan(current_price):
                    current_price = price_at_rec
                if price_at_rec > 0:
                    change_pct = ((current_price / price_at_rec) - 1) * 100
                else:
                    change_pct = 0
                if isinstance(change_pct, float) and math.isnan(change_pct):
                    change_pct = 0

                picks_with_perf.append(
                    {
                        **pick,
                        "sector": get_sector(ticker),
                        "current_price": current_price,
                        "price_at_rec": price_at_rec,
                        "change_since_rec": round(change_pct, 2),
                    }
                )

            return jsonify(
                {
                    "analysis_date": snapshot.get("analysis_date", ""),
                    "analysis_timestamp": snapshot.get("analysis_timestamp", ""),
                    "top_picks": picks_with_perf,
                    "summary": {
                        "total_analyzed": len(picks_with_perf),
                        "avg_score": round(
                            sum(
                                p.get("final_score", p.get("composite_score", 0))
                                for p in picks_with_perf
                            )
                            / len(picks_with_perf),
                            1,
                        )
                        if picks_with_perf
                        else 0,
                    },
                }
            )
        else:
            csv_path = "us_market/data/smart_money_picks_v2.csv"
            if not os.path.exists(csv_path):
                csv_path = "us_market/smart_money_picks_v2.csv"
            if not os.path.exists(csv_path):
                return jsonify(
                    {"error": "Smart money picks not found. Run screener first."}
                ), 404

            df = pd.read_csv(csv_path)
            tickers = df["ticker"].head(20).tolist()
            current_prices = {}
            try:
                price_data = yf.download(tickers, period="1d", progress=False)
                if (
                    price_data is not None
                    and not price_data.empty
                    and "Close" in price_data
                ):
                    closes = price_data["Close"]
                    for ticker in tickers:
                        try:
                            if (
                                isinstance(closes, pd.DataFrame)
                                and ticker in closes.columns
                            ):
                                val = closes[ticker].iloc[-1]
                            elif (
                                isinstance(closes, pd.Series) and closes.name == ticker
                            ):
                                val = closes.iloc[-1]
                            else:
                                val = 0
                            current_prices[ticker] = (
                                round(float(val), 2) if not pd.isna(val) else 0
                            )
                        except Exception:
                            pass
            except Exception:
                pass

            top_picks = []
            for _, row in df.head(20).iterrows():
                ticker = row["ticker"]
                rec_price = row.get("current_price", 0) or 0
                cur_price = current_prices.get(ticker, rec_price) or rec_price
                if rec_price > 0:
                    change_pct = ((cur_price / rec_price) - 1) * 100
                else:
                    change_pct = 0

                top_picks.append(
                    {
                        "ticker": ticker,
                        "name": row.get("name", ticker),
                        "sector": get_sector(ticker),
                        "final_score": row.get(
                            "smart_money_score", row.get("composite_score", 0)
                        ),
                        "current_price": cur_price,
                        "price_at_rec": rec_price,
                        "change_since_rec": round(change_pct, 2),
                        "category": row.get("category", "N/A"),
                        "volume_stage": row.get("volume_stage", "N/A"),
                        "insider_score": row.get("insider_score", 0),
                        "avg_surprise": row.get("avg_surprise", 0),
                    }
                )

            return jsonify(
                {
                    "top_picks": top_picks,
                    "summary": {
                        "total_analyzed": len(df),
                        "avg_score": round(
                            df["smart_money_score"].mean()
                            if "smart_money_score" in df.columns
                            else 0,
                            1,
                        ),
                    },
                }
            )
    except Exception as e:
        print(f"Error getting smart money picks: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/us/etf-flows")
def get_us_etf_flows():
    try:
        import json

        csv_path = "us_market/data/us_etf_flows.csv"
        if not os.path.exists(csv_path):
            csv_path = "us_market/us_etf_flows.csv"
        if not os.path.exists(csv_path):
            return jsonify(
                {"error": "ETF flows not found. Run analyze_etf_flows.py first."}
            ), 404

        df = pd.read_csv(csv_path)
        broad_market = df[df["category"] == "Broad Market"]
        broad_score = (
            round(broad_market["flow_score"].mean(), 1)
            if not broad_market.empty
            else 50
        )

        sector_flows = df[df["category"] == "Sector"].to_dict(orient="records")
        top_inflows = df.nlargest(5, "flow_score").to_dict(orient="records")
        top_outflows = df.nsmallest(5, "flow_score").to_dict(orient="records")

        ai_analysis_text = ""
        ai_path = "us_market/etf_flow_analysis.json"
        if os.path.exists(ai_path):
            with open(ai_path, "r", encoding="utf-8") as f:
                ai_data = json.load(f)
                ai_analysis_text = ai_data.get("ai_analysis", "")

        return jsonify(
            {
                "market_sentiment_score": broad_score,
                "sector_flows": sector_flows,
                "top_inflows": top_inflows,
                "top_outflows": top_outflows,
                "all_etfs": df.to_dict(orient="records"),
                "ai_analysis": ai_analysis_text,
            }
        )
    except Exception as e:
        print(f"Error getting ETF flows: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/us/stock-chart/<ticker>")
def get_us_stock_chart(ticker):
    try:
        period = request.args.get("period", "1y")
        valid_periods = ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"]
        if period not in valid_periods:
            period = "1y"

        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        if hist.empty:
            return jsonify({"error": f"No data found for {ticker}"}), 404

        candles = []
        for date, row in hist.iterrows():
            candles.append(
                {
                    "time": int(date.timestamp()),
                    "open": round(row["Open"], 2),
                    "high": round(row["High"], 2),
                    "low": round(row["Low"], 2),
                    "close": round(row["Close"], 2),
                }
            )

        return jsonify({"ticker": ticker, "period": period, "candles": candles})
    except Exception as e:
        print(f"Error getting US stock chart for {ticker}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/us/history-dates")
def get_us_history_dates():
    try:
        history_dir = "us_market/history"
        if not os.path.exists(history_dir):
            return jsonify({"dates": []})

        dates = []
        for f in os.listdir(history_dir):
            if f.startswith("picks_") and f.endswith(".json"):
                date_str = f[6:-5]
                dates.append(date_str)

        dates.sort(reverse=True)
        return jsonify({"dates": dates, "count": len(dates)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/us/history/<date>")
def get_us_history_by_date(date):
    try:
        import json
        import math

        history_file = f"us_market/history/picks_{date}.json"

        if not os.path.exists(history_file):
            return jsonify({"error": f"No analysis found for {date}"}), 404

        with open(history_file, "r", encoding="utf-8") as f:
            snapshot = json.load(f)

        tickers = [p["ticker"] for p in snapshot["picks"]]
        current_prices = {}
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="5d")
                if not hist.empty:
                    current_prices[ticker] = round(float(hist["Close"].iloc[-1]), 2)
            except Exception:
                pass

        picks_with_perf = []
        for pick in snapshot["picks"]:
            ticker = pick["ticker"]
            price_at_rec = pick.get("price_at_analysis", 0) or 0
            current_price = (
                current_prices.get(ticker, price_at_rec) or price_at_rec or 0
            )

            if isinstance(price_at_rec, float) and math.isnan(price_at_rec):
                price_at_rec = 0
            if isinstance(current_price, float) and math.isnan(current_price):
                current_price = price_at_rec
            if price_at_rec > 0:
                change_pct = ((current_price / price_at_rec) - 1) * 100
            else:
                change_pct = 0
            if isinstance(change_pct, float) and math.isnan(change_pct):
                change_pct = 0

            picks_with_perf.append(
                {
                    **pick,
                    "sector": get_sector(ticker),
                    "current_price": current_price,
                    "price_at_rec": price_at_rec,
                    "change_since_rec": round(change_pct, 2),
                }
            )

        changes = [
            p["change_since_rec"] for p in picks_with_perf if p["price_at_rec"] > 0
        ]
        avg_perf = round(sum(changes) / len(changes), 2) if changes else 0

        return jsonify(
            {
                "analysis_date": snapshot.get("analysis_date", date),
                "analysis_timestamp": snapshot.get("analysis_timestamp", ""),
                "top_picks": picks_with_perf,
                "summary": {"total": len(picks_with_perf), "avg_performance": avg_perf},
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/us/macro-analysis")
def get_us_macro_analysis():
    try:
        import json

        lang = request.args.get("lang", "ko")
        model = request.args.get("model", "gemini")

        macro_indicators = {}

        if model == "gpt":
            if lang == "en":
                analysis_path = "us_market/macro_analysis_gpt_en.json"
            else:
                analysis_path = "us_market/macro_analysis_gpt.json"
            if not os.path.exists(analysis_path):
                if lang == "en":
                    analysis_path = "us_market/macro_analysis_en.json"
                else:
                    analysis_path = "us_market/macro_analysis.json"
        else:
            if lang == "en":
                analysis_path = "us_market/macro_analysis_en.json"
            else:
                analysis_path = "us_market/macro_analysis.json"

        if not os.path.exists(analysis_path):
            analysis_path = "us_market/macro_analysis.json"

        ai_analysis_default = "AI 분석을 로드할 수 없습니다. macro_analyzer.py를 실행하세요."
        if os.path.exists(analysis_path):
            with open(analysis_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
                ai_analysis = cached.get("ai_analysis", ai_analysis_default)
                macro_indicators = cached.get("macro_indicators", {})

        # Replace error messages with user-friendly fallback
        error_messages = [
            "Failed to generate - Check API key and quota",
            "Failed to generate",
            "API Quota Exceeded",
            "API Error",
        ]

        if ai_analysis in error_messages or not ai_analysis or ai_analysis.strip() == "":
            ai_analysis = ai_analysis_default

        for name, ticker in {
            "VIX": "^VIX",
            "SPY": "SPY",
            "QQQ": "QQQ",
            "BTC": "BTC-USD",
            "GOLD": "GC=F",
        }.items():
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="5d")
                if not hist.empty and len(hist) >= 2:
                    current = float(hist["Close"].iloc[-1])
                    prev = float(hist["Close"].iloc[-2])
                    change = current - prev
                    change_pct = (change / prev) * 100 if prev != 0 else 0
                    macro_indicators[name] = {
                        "current": round(current, 2),
                        "change_1d": round(change_pct, 2),
                    }
            except Exception:
                pass

        return jsonify(
            {
                "macro_indicators": macro_indicators,
                "ai_analysis": ai_analysis,
                "model": model,
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/us/sector-heatmap")
def get_us_sector_heatmap():
    try:
        import json

        heatmap_path = "us_market/sector_heatmap.json"
        if not os.path.exists(heatmap_path):
            return jsonify({"error": "Sector heatmap data not found"})

        with open(heatmap_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/us/options-flow")
def get_us_options_flow():
    try:
        import json

        flow_path = "us_market/options_flow.json"
        if not os.path.exists(flow_path):
            return jsonify({"error": "Options flow data not found"})

        with open(flow_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/us/indices")
def get_us_indices():
    """Get major US market indices data"""
    try:
        indices_map = [
            ("^GSPC", "S&P 500"),
            ("^IXIC", "NASDAQ"),
            ("^DJI", "Dow Jones"),
            ("^RUT", "Russell 2000"),
        ]

        indices_data = []

        for symbol, name in indices_map:
            try:
                stock = yf.Ticker(symbol)
                hist = stock.history(period="5d")

                if not hist.empty and len(hist) >= 2:
                    current_price = float(hist["Close"].iloc[-1])
                    prev_price = float(hist["Close"].iloc[-2])
                    change = current_price - prev_price
                    change_pct = (change / prev_price) * 100 if prev_price != 0 else 0

                    indices_data.append(
                        {
                            "name": name,
                            "symbol": symbol,
                            "price": round(current_price, 2),
                            "change": round(change_pct, 2),
                        }
                    )
                else:
                    # Fallback values if no data available
                    indices_data.append(
                        {"name": name, "symbol": symbol, "price": 0, "change": 0}
                    )
            except Exception as e:
                print(f"Error fetching data for {symbol}: {e}")
                # Fallback values if error occurs
                indices_data.append(
                    {"name": name, "symbol": symbol, "price": 0, "change": 0}
                )

        return jsonify({"indices": indices_data})

    except Exception as e:
        print(f"Error getting US indices data: {e}")
        return jsonify({"error": str(e)}), 500


# =============================================================================
# NEW ENDPOINTS ADDED
# =============================================================================


@app.route("/api/us/calendar")
def get_us_calendar():
    """Get Weekly Economic Calendar"""
    try:
        import json

        calendar_path = "us_market/weekly_calendar.json"

        if not os.path.exists(calendar_path):
            return jsonify(
                {
                    "events": [],
                    "message": "Calendar data not available. Run economic calendar generator first.",
                }
            ), 404

        with open(calendar_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return jsonify(data)

    except Exception as e:
        print(f"Error loading calendar data: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/us/ai-summary/<ticker>")
def get_us_ai_summary(ticker):
    """Get AI-generated summary for a US stock"""
    try:
        import json

        # Get language preference (ko or en)
        lang = request.args.get("lang", "ko")

        if lang not in ["ko", "en"]:
            lang = "ko"

        # Load AI summaries
        summary_path = "us_market/ai_summaries.json"

        if not os.path.exists(summary_path):
            return jsonify(
                {"error": "AI summaries not found. Run ai_summary_generator.py first."}
            ), 404

        with open(summary_path, "r", encoding="utf-8") as f:
            summaries = json.load(f)

        if ticker not in summaries:
            return jsonify({"error": f"Summary not found for {ticker}"}), 404

        summary_data = summaries[ticker]

        # Get summary in requested language (fallback to Korean if English not available)
        if lang == "en":
            summary = summary_data.get("summary_en", summary_data.get("summary_ko", ""))
        else:
            summary = summary_data.get("summary_ko", summary_data.get("summary_en", ""))

        # Replace error messages with user-friendly fallback
        error_messages = [
            "API Quota Exceeded",
            "Failed to generate - Check API key and quota",
            "Failed to generate",
            "API Error",
        ]

        if summary in error_messages or not summary or summary.strip() == "":
            if lang == "en":
                summary = """### 📊 Stock Analysis Not Available

AI-powered analysis is currently unavailable due to API limitations.

**What you can still see:**
- Real-time price charts
- Technical indicators (RSI, MACD, Bollinger Bands)
- Volume analysis and smart money flows

**To enable AI analysis:**
1. Check API key configuration in `.env` file
2. Verify API quota is available
3. Run `python us_market/ai_summary_generator.py` to generate summaries
"""
            else:
                summary = """### 📊 AI 분석 임시 중단

API 할당량 문제로 AI 분석 기능을 현재 사용할 수 없습니다.

**현재 이용 가능한 기능:**
- 실시간 가격 차트
- 기술적 지표 (RSI, MACD, 볼린저 밴드)
- 거래량 분석 및 스마트 머니 흐름

**AI 분석 재개 방법:**
1. `.env` 파일에서 API 키 설정 확인
2. API 할당량 여부 확인
3. `python us_market/ai_summary_generator.py` 실행하여 요약 생성
"""

        return jsonify(
            {
                "ticker": ticker,
                "summary": summary,
                "lang": lang,
                "news_count": summary_data.get("news_count", 0),
                "updated": summary_data.get("updated", ""),
                "sentiment": summary_data.get("sentiment", "N/A"),
            }
        )

    except Exception as e:
        print(f"Error getting AI summary for {ticker}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/us/technical-indicators/<ticker>")
def get_technical_indicators(ticker):
    """
    Get technical indicators for a US stock

    Calculations:
    - RSI (14-period): Using Wilder's RSI formula
    - MACD (12, 26, 9): MACD line, Signal line, Histogram
    - Bollinger Bands (20-period, 2 std dev): Upper, Middle, Lower bands
    - Support/Resistance: Local minima/maxima detection with 2% clustering
    """
    try:
        # Get period parameter
        period = request.args.get("period", "1y")
        valid_periods = ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"]
        if period not in valid_periods:
            period = "1y"

        # Fetch historical data
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        if hist.empty:
            return jsonify({"error": f"No data found for {ticker}"}), 404

        df = hist.copy()
        close = df["Close"]
        df["High"]
        df["Low"]

        # Calculate RSI
        if TA_AVAILABLE:
            rsi_indicator = RSIIndicator(close=close, window=14)
            rsi = rsi_indicator.rsi()
        else:
            rsi = calculate_rsi_manual(close, period=14)

        # Calculate MACD
        if TA_AVAILABLE:
            macd_obj = MACD(close=close, window_slow=26, window_fast=12, window_sign=9)
            macd_line = macd_obj.macd()
            signal_line = macd_obj.macd_signal()
            macd_histogram = macd_obj.macd_diff()
        else:
            macd_line, signal_line, macd_histogram = calculate_macd_manual(close)

        # Calculate Bollinger Bands
        if TA_AVAILABLE:
            bb = BollingerBands(close=close, window=20, window_dev=2)
            bb_upper = bb.bollinger_hband()
            bb_middle = bb.bollinger_mavg()
            bb_lower = bb.bollinger_lband()
        else:
            bb_upper, bb_middle, bb_lower = calculate_bollinger_bands_manual(close)

        # Detect Support and Resistance levels
        supports, resistances = detect_support_resistance(
            df, window=10, cluster_pct=0.02
        )

        # Prepare time series data for response
        def make_series(dates, values):
            """Convert pandas series to list of dicts with timestamp"""
            result = []
            for date, val in zip(dates, values):
                if pd.notna(val):
                    result.append(
                        {"time": int(date.timestamp()), "value": round(float(val), 2)}
                    )
            return result

        # Build response
        response = {
            "ticker": ticker,
            "period": period,
            "rsi": make_series(df.index, rsi),
            "macd": {
                "macd_line": make_series(df.index, macd_line),
                "signal_line": make_series(df.index, signal_line),
                "histogram": make_series(df.index, macd_histogram),
            },
            "bollinger": {
                "upper": make_series(df.index, bb_upper),
                "middle": make_series(df.index, bb_middle),
                "lower": make_series(df.index, bb_lower),
            },
            "support_resistance": {"support": supports, "resistance": resistances},
        }

        return jsonify(response)

    except Exception as e:
        print(f"Error getting technical indicators for {ticker}: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/us/update-data", methods=["POST"])
def update_market_data():
    """Trigger market data update (for 'Create Report' button)"""
    try:
        import os
        import subprocess

        # Run update_all.py script
        script_path = os.path.join(
            os.path.dirname(__file__), "us_market", "update_all.py"
        )

        if not os.path.exists(script_path):
            return jsonify({"success": False, "error": "Update script not found"}), 404

        # Run script in background (non-blocking)
        subprocess.Popen(
            ["python", script_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )

        return jsonify(
            {
                "success": True,
                "message": "Data update started in background. This may take 30-40 minutes to complete.",
                "note": "For faster updates, please use GitHub Actions or run scripts locally.",
                "status": "started",
                "script": script_path
            }
        )

    except Exception as e:
        print(f"Error starting data update: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    print(f"🚀 Flask Server Starting on port {port}...")
    app.run(debug=debug_mode, host="0.0.0.0", port=port, use_reloader=False)
