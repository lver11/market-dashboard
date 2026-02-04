# 🎯 DashBoard - Smart Money Market Analysis System

**Advanced US Stock Market Analysis Platform with AI-Powered Insights**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

---

## 📊 Features

### 🎯 Smart Money Screening (6-Factor Analysis)
- **Supply/Demand Analysis (25%)**: Volume accumulation patterns
- **Institutional Support (20%)**: 13F holdings tracking
- **Technical Indicators (20%)**: RSI, MACD, Bollinger Bands
- **Fundamental Analysis (15%)**: P/E, PEG ratios
- **Analyst Ratings (10%)**: Wall Street consensus
- **Relative Strength (10%)**: Performance vs S&P 500

### 📈 Real-Time Market Data
- **746,233** price records across **492 US stocks**
- 30-second live price updates
- Interactive candlestick charts with technical overlays
- Support/Resistance level detection

### 🤖 AI-Powered Analysis
- **Google Gemini 3.0**: Macro economic analysis
- **OpenAI GPT-5.2**: Market insights and summaries
- Multi-language support (Korean/English)

### 🔬 Technical Analysis
- RSI (14-period)
- MACD (12, 26, 9)
- Bollinger Bands (20, 2)
- Support/Resistance with 2% clustering

### 📊 Market Visualizations
- 11 major indices tracking
- Sector heatmap (11 sectors)
- ETF flows analysis (24 ETFs)
- Options flow monitoring
- Economic calendar integration

---

## 🚀 Live Demo

Deployed on Vercel: **[Coming Soon]**

Local: **http://localhost:5001**

---

## 🛠️ Installation

### Prerequisites
- Python 3.10 or higher
- pip package manager
- Google Gemini API Key (optional, for AI features)
- OpenAI API Key (optional, for AI features)

### Setup Steps

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/DashBoard.git
cd DashBoard
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
FRED_API_KEY=your_fred_api_key_here
DATA_DIR=./us_market/data
```

4. **Run data collection scripts** (optional)
```bash
cd us_market
python update_all.py
```

5. **Start the Flask server**
```bash
python flask_app.py
```

6. **Open in browser**
```
http://localhost:5001
```

---

## 📁 Project Structure

```
DashBoard/
├── flask_app.py              # Flask REST API (734 lines, 13 endpoints)
├── requirements.txt          # Python dependencies
├── vercel.json              # Vercel deployment config
├── .env.example             # Environment variables template
│
├── templates/
│   └── index.html           # Frontend UI (2,356 lines)
│
├── static/
│   ├── js/
│   │   └── app.js           # Frontend logic (1,583 lines)
│   └── css/
│       └── custom.css       # Dark theme styling
│
├── us_market/
│   ├── update_all.py        # Master data collection script
│   ├── create_us_daily_prices.py    # Price data collection
│   ├── analyze_volume.py    # Volume analysis
│   ├── analyze_13f.py       # Institutional holdings
│   ├── analyze_etf_flows.py # ETF flows analysis
│   ├── smart_money_screener_v2.py   # 6-factor screening
│   ├── sector_heatmap.py    # Sector performance
│   ├── options_flow.py      # Options flow monitoring
│   ├── macro_analyzer.py    # Macro economic analysis
│   ├── ai_summary_generator.py   # AI insights
│   ├── economic_calendar.py # Economic events
│   └── data/                # CSV data files (gitignored)
│
└── docs/
    ├── PART1_Data_Collection.md
    ├── PART2_Analysis_Screening.md
    ├── PART3_AI_Analysis.md
    ├── PART4_Web_Server.md
    ├── PART5_Frontend_UI.md
    └── PART6_Frontend_Logic.md
```

---

## 🔌 API Endpoints

### Market Data
- `GET /api/us/indices` - Major indices data
- `GET /api/us/stocks` - Stock list with smart money scores
- `GET /api/us/stock/<ticker>` - Individual stock data
- `GET /api/us/technical-indicators/<ticker>` - Technical analysis

### Analysis
- `GET /api/us/heatmap` - Sector heatmap data
- `GET /api/us/etf-flows` - ETF flows data
- `GET /api/us/options-flow` - Options flow data

### AI Features
- `GET /api/us/macro-analysis` - AI macro analysis
- `GET /api/us/ai-summary/<ticker>` - AI stock summary
- `GET /api/us/calendar` - Economic calendar

---

## 📊 Top Smart Money Picks (Current)

| Rank | Ticker | Grade | Score | Price |
|------|--------|-------|-------|-------|
| 1 | FITB | 🌟 A (Strong Buy) | 78.8 | $50.22 |
| 2 | FDX | 🌟 A (Strong Buy) | 78.0 | $322.25 |
| 3 | PPG | 🌟 A (Strong Buy) | 76.6 | $115.63 |
| 4 | NOC | 🌟 A (Strong Buy) | 76.6 | $692.26 |
| 5 | CMCSA | 🌟 A (Strong Buy) | 76.5 | $29.75 |

---

## 🎨 UI Components

1. **Market Indices Bar** - Real-time tracking of 11 major indices
2. **Macro Analysis Grid** - 30+ macro economic indicators
3. **Smart Money Picks Table** - Top 20 screened stocks
4. **Stock Chart Panel** - Interactive candlestick charts
5. **AI Summary Box** - AI-powered investment insights
6. **ETF Flow Section** - 24 ETF capital flows
7. **Sector Heatmap** - Visual sector performance
8. **Economic Calendar** - Upcoming economic events

---

## 🔧 Technology Stack

### Backend
- **Flask** - REST API framework
- **yfinance** - Market data provider
- **pandas** - Data processing
- **numpy** - Numerical computing

### Frontend
- **Tailwind CSS** - Utility-first styling
- **Lightweight Charts** - Candlestick charts
- **Chart.js** - Data visualization
- **ApexCharts** - Heatmap visualization
- **jQuery** - DOM manipulation

### AI/ML
- **Google Gemini 3.0** - Macro analysis
- **OpenAI GPT-5.2** - Stock summaries

### Deployment
- **Vercel** - Serverless hosting
- **GitHub** - Version control

---

## 📝 License

This project is licensed under the MIT License.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

---

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

## ⭐ Star History

If you find this project helpful, please consider giving it a star!

---

**Built with ❤️ for smart investors**

