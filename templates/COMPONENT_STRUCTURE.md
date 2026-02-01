# templates/index.html Component Structure Guide

## File Overview
- **File**: `templates/index.html`
- **Size**: 114KB (2,356 lines)
- **Language**: HTML5 with embedded CSS and JavaScript
- **Primary Language**: Korean (with English support)

---

## HTML Structure Breakdown

### 1. HEAD Section (Lines 1-153)
```html
<head>
    - Meta tags (charset, viewport)
    - Title: "Korean Market - AI Stock Analysis"
    - CDN Libraries:
        • Tailwind CSS
        • Lightweight Charts (v3.8.0)
        • Chart.js
        • ApexCharts
        • Marked.js (Markdown parser)
        • Font Awesome (v6.4.0)
    - Custom CSS:
        • Inter font family
        • Dark theme (#121212 background)
        • Custom scrollbar styling
        • Koyfin-style color scheme
        • Responsive utilities
        • Animation classes
</head>
```

### 2. BODY Structure (Lines 154-2356)

#### A. Header/Navigation (Lines 154-207)
```html
- Main header with title
- Tab navigation system:
    • KR Market tab (content-kr-market)
    • US Market tab (content-us-market) [DEFAULT]
    • Economic Calendar tab (content-economic-calendar)
    • Analysis tab (content-analysis)
- Auto-refresh indicator
- Last update timestamp
```

#### B. KR Market Content (Lines 208-378) - Hidden by Default
```html
<div id="content-kr-market">
    Components:
    1. Market Indices Container (6 columns)
    2. Summary Chart Section
    3. Historical Date Selector
    4. Holdings Table
    5. Style Box (9-box matrix: Large/Mid/Small x Value/Core/Growth)
    6. Wave Analysis
    7. S/D Analysis
</div>
```

#### C. US Market Content (Lines 380-608) - DEFAULT VISIBLE
```html
<div id="content-us-market">

    1. Market Indices Section (Lines 382-403)
       - Container: us-market-indices-container
       - Grid: 6 columns (responsive)
       - 11 Major Indices:
         • Dow Jones, S&P 500, NASDAQ, Russell 2000, VIX
         • Gold, Oil, Bitcoin, 10Y Treasury, Dollar Index, USD/KRW
       - Language toggle: KO/EN

    2. Stock Chart Section (Lines 405-481)
       - Chart container: us-stock-chart
       - Period buttons: 1M, 3M, 6M, 1Y, ALL
       - Grade display
       - Technical indicator toggles: BB, S/R, RSI, MACD
       - RSI sub-chart: us-rsi-chart (hidden by default)
       - MACD sub-chart: us-macd-chart (hidden by default)

    3. Sector Heatmap (Lines 457-469)
       - Container: us-sector-heatmap
       - Library: ApexCharts Treemap
       - 11 S&P Sectors
       - Date display: us-heatmap-date

    4. AI Summary Box (Lines 471-480)
       - Container: us-ai-summary
       - Model toggle: Gemini/GPT-5.2
       - Updated timestamp: us-ai-updated
       - Markdown rendering with marked.js

    5. Smart Money Picks Table (Lines 483-519)
       - Container: us-smart-money-table
       - Historical date selector: us-history-date-select
       - Columns: Rank, Ticker, Sector, Score, AI Recommendation, Prices, Change, Upside
       - Summary: us-smart-money-summary

    6. ETF Flows Section (Lines 521-556)
       - Inflows container: us-etf-inflows
       - Outflows container: us-etf-outflows
       - AI analysis button: us-etf-ai-btn
       - AI container: us-etf-ai-container
       - Sentiment display: us-etf-sentiment
       - 24 ETFs tracked

    7. Options Flow Section (Lines 558-569)
       - Container: us-options-flow
       - Grid: 5 columns
       - Timestamp: us-options-timestamp

    8. Macro Analysis Section (Lines 571-607)
       - Indicators grid: us-macro-indicators
       - Grid: 10 columns (responsive)
       - 30+ Indicators (Interest Rates, Inflation, GDP, Unemployment, PMI, etc.)
       - AI analysis: us-macro-ai-analysis
       - Model label: macro-model-label
       - Timestamp: us-macro-timestamp
       - Model toggle: model-toggle (Gemini/GPT-5.2)
</div>
```

#### D. Economic Calendar Content (Lines 610-639) - Hidden by Default
```html
<div id="content-economic-calendar">
    Components:
    1. Weekly Economic Calendar
       - Container: us-calendar-events
       - Range display: us-calendar-range
       - Expand/Collapse buttons
    2. Future performance charts placeholder
</div>
```

#### E. Analysis Content (Lines 641-879) - Hidden by Default
```html
<div id="content-analysis">
    Components:
    1. Chart Section (8 columns)
       - Ticker name: analysis-ticker-name
       - Ticker code: analysis-ticker-code
       - Grade: analysis-grade
       - Score: analysis-score
       - Chart container: analysis-chart-container

    2. Metrics Side Panel (4 columns)
       - Wave Stage: analysis-wave
       - Supply/Demand: analysis-sd
       - Performance metrics
       - Technical indicators

    3. Technical Analysis Table
    4. Fair Value Analysis
</div>
```

#### F. JavaScript Section (Lines 880-2353)
```javascript
// Global State
- currentTab: 'us-market' (default)
- currentChartTicker: null
- currentChartPeriod: '1y' (default)
- currentLanguage: 'ko' (default)
- currentModel: 'gemini' (default)
- indicatorsEnabled: { bb, sr, rsi, macd }

// Major Functions
1. Tab Switching - switchTab(tabName)
2. Market Indices - loadUSMarketIndices(), loadKRMarketIndices()
3. Smart Money Picks - loadUSSmartMoneyPicks(), loadKRHoldings()
4. Stock Chart - loadStockChart(ticker, period), renderCandlestickChart()
5. Technical Indicators - calculateBollingerBands(), calculateRSI(), calculateMACD()
6. AI Analysis - loadAISummary(ticker, lang, model), loadMacroAnalysis(lang, model)
7. ETF Flows - loadETFFlows(), renderInflowsOutflows()
8. Sector Heatmap - loadSectorHeatmap(), renderTreemap()
9. Economic Calendar - loadEconomicCalendar(), renderCalendarEvents()
10. Real-time Updates - updateRealtimePrices() (every 60 seconds)

// Event Listeners
- Tab clicks, Stock row clicks, Period button clicks
- Indicator toggle clicks, Language/Model switcher clicks
- Historical date selector change
```

---

## Key Features

### 1. Color Coding (Korean Convention)
- **Red (#ef4444)**: Up/Positive
- **Green (#22c55e)**: Down/Negative
- **Gray (#6b7280)**: Neutral
- **Blue (#3b82f6)**: Info/Links
- **Purple (#a855f7)**: AI/Advanced

### 2. Responsive Breakpoints
- **Mobile**: < 768px (stack columns)
- **Tablet**: 768px - 1024px (2-3 columns)
- **Desktop**: > 1024px (full grid)

### 3. Data Refresh Intervals
- **Prices**: 60 seconds
- **Macro**: 10 minutes (600 seconds)
- **ETF Flows**: Daily
- **Options Flow**: Hourly

### 4. Storage (localStorage)
- `selectedLanguage`: 'ko' or 'en'
- `selectedModel`: 'gemini' or 'gpt'
- `lastTab`: 'us-market', 'kr-market', 'economic-calendar', 'analysis'

---

## API Endpoints Used

### Backend API Calls (Python Flask)
```
GET  /api/us/indices          - US market indices
GET  /api/us/smart-money      - Smart money picks
GET  /api/us/chart/{ticker}   - Stock chart data
GET  /api/us/ai-summary       - AI analysis
GET  /api/us/etf-flows        - ETF fund flows
GET  /api/us/options-flow     - Options flow
GET  /api/us/macro            - Macro indicators
GET  /api/us/heatmap          - Sector heatmap
GET  /api/us/calendar         - Economic calendar
GET  /api/us/realtime         - Real-time prices

GET  /api/kr/indices          - KR market indices
GET  /api/kr/holdings         - KR holdings
GET  /api/kr/style-box        - Style box data
GET  /api/kr/wave-sd          - Wave & S/D analysis
```

---

## CSS Classes Reference

### Background Colors
- `bg-[#121212]` - Main background
- `bg-[#1a1a1a]` - Panel background
- `bg-[#2a2a2a]` - Border/background darker
- `bg-gray-900` - Alternative dark
- `bg-gray-800` - Card background

### Text Colors
- `text-white` - Primary text
- `text-gray-300` - Secondary text
- `text-gray-400` - Muted text
- `text-gray-500` - Placeholder text
- `text-red-400` - Up/Korean positive
- `text-green-400` - Down/Korean negative
- `text-blue-400` - Links/info
- `text-purple-400` - AI/Advanced

### Borders
- `border-[#2a2a2a]` - Default border
- `border-gray-700` - Divider
- `border-gray-800` - Card border
- `border-purple-800/50` - AI section border

### Utilities
- `rounded` - 4px border radius
- `rounded-lg` - 8px border radius
- `rounded-full` - Pill shape
- `animate-pulse` - Loading animation
- `transition-colors` - Smooth color transition
- `hover:bg-*` - Hover states

---

## Browser Compatibility

- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Mobile**: iOS Safari 14+, Chrome Android 90+
- **Features Required**:
  - ES6 JavaScript
  - CSS Grid
  - Flexbox
  - LocalStorage
  - Fetch API
  - WebSocket (optional)

---

## Performance Considerations

### Optimizations
1. **Lazy Loading**: Charts load on demand
2. **Debouncing**: Search input debounced by 300ms
3. **Throttling**: Resize events throttled to 100ms
4. **Caching**: API responses cached for 60 seconds
5. **Virtual Scrolling**: For large tables (future)

### Bundle Size
- HTML: 114KB (uncompressed)
- CDN Libraries: ~500KB (total, gzipped)
- First Load: ~200KB (with compression)

---

## Troubleshooting

### Common Issues

1. **Charts Not Loading**
   - Check console for errors
   - Verify Lightweight Charts library loaded
   - Check API endpoint availability

2. **Real-time Updates Not Working**
   - Check browser console for fetch errors
   - Verify CORS settings on backend
   - Check network connectivity

3. **Language Switcher Not Persisting**
   - Check if localStorage is enabled
   - Clear browser cache and retry
   - Check for browser privacy settings

4. **AI Analysis Not Showing**
   - Verify API key configuration
   - Check model selection (Gemini/GPT)
   - Verify backend AI service is running

---

## Development Notes

### File Organization
- All CSS in `<style>` tag (lines 23-153)
- All JS in `<script>` tag (lines 880-2353)
- No external CSS/JS files required
- Single-file deployment

### Testing
- Open directly in browser for testing
- Use Python HTTP server: `python -m http.server 8000`
- Or use Flask backend: `python app.py`

### Deployment
- Copy to Flask `templates/` directory
- Ensure static files served from `/static/`
- Configure Flask route for `/`

---

**End of Component Structure Guide**
