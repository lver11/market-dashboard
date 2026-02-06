/**
 * US Stock Market Dashboard - Frontend Application
 * Complete JavaScript logic for interactive dashboard
 *
 * Features:
 * - Real-time market data updates
 * - Interactive stock charts with technical indicators
 * - AI-powered macro analysis
 * - Internationalization support (ko/en)
 * - Historical picks viewer
 */

// ==========================================
// GLOBAL STATE MANAGEMENT
// ==========================================

const APP_STATE = {
    // User preferences (persisted in localStorage)
    language: localStorage.getItem('preferredLanguage') || 'ko',
    model: localStorage.getItem('preferredModel') || 'gemini',
    selectedPeriod: localStorage.getItem('selectedPeriod') || '1y',

    // Current view state
    currentTicker: null,
    currentPick: null,
    enabledIndicators: JSON.parse(localStorage.getItem('enabledIndicators') || '[]'),

    // Chart instance
    chart: null,
    candlestickSeries: null,
    volumeSeries: null,

    // Indicator series references
    indicatorSeries: {
        bollingerBands: { upper: null, lower: null, middle: null },
        rsi: null,
        macd: { macd: null, signal: null, histogram: null },
        supportResistance: null
    },

    // Auto-refresh intervals
    refreshIntervals: {
        macro: null,
        prices: null
    },

    // Data cache
    cachedData: {
        smartMoney: null,
        macroAnalysis: null,
        technicalIndicators: {}
    }
};

// ==========================================
// INTERNATIONALIZATION (i18n)
// ==========================================

const I18N = {
    ko: {
        // Navigation
        'nav.dashboard': '대시보드',
        'nav.smart_money': '스마트 머니',
        'nav.macro': '마크로 분석',
        'nav.calendar': '경제 캘린더',

        // Headers
        'header.market_indices': '시장 지수',
        'header.smart_money_picks': '스마트 머니 추천 종목',
        'header.macro_analysis': '마크로 분석',
        'header.etf_flows': 'ETF 자금 흐름',
        'header.sector_heatmap': '섹터 Heatmap',
        'header.options_flow': '옵션 흐름',

        // Table columns
        'col.ticker': '티커',
        'col.name': '종목명',
        'col.price': '현재가',
        'col.change': '변동률',
        'col.score': '종합 점수',
        'col.upside': '상승 여력',
        'col.rec_date': '추천일',
        'col.ai_rec': 'AI 추천',

        // Buttons
        'btn.refresh': '새로고침',
        'btn.load_chart': '차트 보기',
        'btn.historical': '과거 데이터',
        'btn.indicators': '기술적 지표',
        'btn.period.1mo': '1개월',
        'btn.period.3mo': '3개월',
        'btn.period.6mo': '6개월',
        'btn.period.1y': '1년',
        'btn.period.2y': '2년',
        'btn.period.5y': '5년',
        'btn.period.max': '전체',

        // Indicators
        'ind.bb': '볼린저 밴드',
        'ind.rsi': 'RSI',
        'ind.macd': 'MACD',
        'ind.sr': '지지/저항',

        // Messages
        'msg.loading': '로딩 중...',
        'msg.error': '오류가 발생했습니다',
        'msg.no_data': '데이터가 없습니다',
        'msg.updating': '업데이트 중...',

        // AI Model
        'model.gemini': 'Gemini',
        'model.gpt': 'GPT',
        'model.switch': 'AI 모델 변경'
    },
    en: {
        // Navigation
        'nav.dashboard': 'Dashboard',
        'nav.smart_money': 'Smart Money',
        'nav.macro': 'Macro Analysis',
        'nav.calendar': 'Economic Calendar',

        // Headers
        'header.market_indices': 'Market Indices',
        'header.smart_money_picks': 'Smart Money Picks',
        'header.macro_analysis': 'Macro Analysis',
        'header.etf_flows': 'ETF Flows',
        'header.sector_heatmap': 'Sector Heatmap',
        'header.options_flow': 'Options Flow',

        // Table columns
        'col.ticker': 'Ticker',
        'col.name': 'Name',
        'col.price': 'Price',
        'col.change': 'Change',
        'col.score': 'Score',
        'col.upside': 'Upside',
        'col.rec_date': 'Rec Date',
        'col.ai_rec': 'AI Rec',

        // Buttons
        'btn.refresh': 'Refresh',
        'btn.load_chart': 'Load Chart',
        'btn.historical': 'Historical',
        'btn.indicators': 'Indicators',
        'btn.period.1mo': '1Mo',
        'btn.period.3mo': '3Mo',
        'btn.period.6mo': '6Mo',
        'btn.period.1y': '1Y',
        'btn.period.2y': '2Y',
        'btn.period.5y': '5Y',
        'btn.period.max': 'Max',

        // Indicators
        'ind.bb': 'Bollinger Bands',
        'ind.rsi': 'RSI',
        'ind.macd': 'MACD',
        'ind.sr': 'Support/Resistance',

        // Messages
        'msg.loading': 'Loading...',
        'msg.error': 'Error occurred',
        'msg.no_data': 'No data available',
        'msg.updating': 'Updating...',

        // AI Model
        'model.gemini': 'Gemini',
        'model.gpt': 'GPT',
        'model.switch': 'Switch AI Model'
    }
};

/**
 * Translate UI elements based on selected language
 * @param {string} lang - Language code ('ko' or 'en')
 */
function translateUI(lang) {
    APP_STATE.language = lang;
    localStorage.setItem('preferredLanguage', lang);

    // Update all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        if (I18N[lang] && I18N[lang][key]) {
            element.textContent = I18N[lang][key];
        }
    });

    // Update HTML lang attribute
    document.documentElement.lang = lang;

    // Reload macro analysis with new language
    reloadMacroAnalysis();
}

/**
 * Switch AI model for analysis
 * @param {string} model - Model name ('gemini' or 'gpt')
 */
function switchModel(model) {
    APP_STATE.model = model;
    localStorage.setItem('preferredModel', model);

    // Update UI to show active model
    document.querySelectorAll('.model-selector').forEach(btn => {
        btn.classList.remove('active', 'bg-blue-600');
        if (btn.dataset.model === model) {
            btn.classList.add('active', 'bg-blue-600');
        }
    });

    // Reload macro analysis with new model
    reloadMacroAnalysis();
}

// ==========================================
// MAIN DASHBOARD FUNCTIONS
// ==========================================

/**
 * Main dashboard data fetcher and renderer
 * Fetches data from all API endpoints in parallel and updates UI
 */
async function updateUSMarketDashboard() {
    try {
        console.log('[Dashboard] Updating dashboard data...');

        // Show loading indicator
        showLoadingIndicator();

        // Parallel fetch from multiple endpoints
        const [
            portfolioData,
            smartMoneyData,
            etfFlowsData,
            historyDatesData
        ] = await Promise.all([
            fetchWithErrorHandling('/api/us/portfolio', 'Market Indices'),
            fetchWithErrorHandling('/api/us/smart-money', 'Smart Money Picks'),
            fetchWithErrorHandling('/api/us/etf-flows', 'ETF Flows'),
            fetchWithErrorHandling('/api/us/history-dates', 'History Dates')
        ]);

        // Render each section
        if (portfolioData) {
            renderUSMarketIndices(portfolioData);
        }

        if (smartMoneyData) {
            APP_STATE.cachedData.smartMoney = smartMoneyData;
            renderUSSmartMoneyPicks(smartMoneyData);
        }

        if (etfFlowsData) {
            renderUSETFFlows(etfFlowsData);
        }

        if (historyDatesData) {
            renderHistoryDatesDropdown(historyDatesData);
        }

        // Load macro analysis separately (may take longer)
        await reloadMacroAnalysis();

        console.log('[Dashboard] Dashboard update complete');

    } catch (error) {
        console.error('[Dashboard] Error updating dashboard:', error);
        showErrorMessage(I18N[APP_STATE.language]['msg.error'] + ': ' + error.message);
    } finally {
        hideLoadingIndicator();
    }
}

/**
 * Fetch data with error handling and retry logic
 * @param {string} url - API endpoint URL
 * @param {string} description - Description of data being fetched
 * @param {number} retries - Number of retry attempts
 * @returns {Promise<Object|null>} - Fetched data or null on failure
 */
async function fetchWithErrorHandling(url, description = 'Data', retries = 3) {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`[Fetch] Error fetching ${description} (attempt ${i + 1}/${retries}):`, error);

            if (i === retries - 1) {
                // Last attempt failed
                showErrorMessage(`${description} ${I18N[APP_STATE.language]['msg.error'].toLowerCase()}`);
                return null;
            }

            // Wait before retry (exponential backoff)
            await new Promise(resolve => setTimeout(resolve, Math.pow(2, i) * 1000));
        }
    }
    return null;
}

// ==========================================
// RENDERING FUNCTIONS
// ==========================================

/**
 * Render market indices bar (S&P 500, Nasdaq, Dow Jones)
 * @param {Object} data - Portfolio data with market indices
 */
function renderUSMarketIndices(data) {
    const container = document.getElementById('market-indices-bar');
    if (!container) return;

    const indices = data.market_indices || [];

    container.innerHTML = indices.map(index => {
        const changeClass = index.change_percent >= 0 ? 'koyfin-green' : 'koyfin-red';
        const arrow = index.change_percent >= 0 ? '▲' : '▼';

        return `
            <div class="flex items-center gap-3 px-4 py-2 border-r border-[#2a2a2a]">
                <div>
                    <div class="text-xs font-medium text-gray-400">${index.name}</div>
                    <div class="text-sm font-bold text-white">${index.value.toFixed(2)}</div>
                </div>
                <div class="${changeClass} text-xs font-medium">
                    ${arrow} ${Math.abs(index.change_percent).toFixed(2)}%
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Render smart money picks table
 * @param {Object} data - Smart money data with top picks
 */
function renderUSSmartMoneyPicks(data) {
    const tableBody = document.getElementById('smart-money-table-body');
    if (!tableBody) return;

    const picks = data.top_picks || [];

    tableBody.innerHTML = picks.map((pick, index) => {
        const upsideClass = pick.upside >= 0 ? 'koyfin-green' : 'koyfin-red';
        const changeClass = pick.change_since_rec >= 0 ? 'koyfin-green' : 'koyfin-red';
        const scoreColor = getScoreColor(pick.total_score);

        // AI recommendation emoji
        const aiEmoji = getAIRecommendationEmoji(pick.ai_recommendation);

        return `
            <tr class="cursor-pointer hover:bg-[#1a1a1a] transition-colors stock-row"
                data-ticker="${pick.ticker}"
                data-index="${index}">
                <td class="font-medium text-white">
                    <div class="font-bold">${pick.ticker}</div>
                    <div class="text-xs text-gray-500">${pick.name}</div>
                </td>
                <td>
                    <div class="font-mono text-white">$${pick.current_price.toFixed(2)}</div>
                </td>
                <td class="${changeClass}">
                    ${pick.change_since_rec >= 0 ? '+' : ''}${pick.change_since_rec.toFixed(2)}%
                </td>
                <td class="${scoreColor} font-bold">
                    ${pick.total_score.toFixed(1)}
                </td>
                <td class="${upsideClass}">
                    ${pick.upside >= 0 ? '+' : ''}${pick.upside.toFixed(1)}%
                </td>
                <td class="text-xs text-gray-400">
                    ${formatDate(pick.recommendation_date)}
                </td>
                <td class="text-xs">
                    ${aiEmoji} ${pick.ai_recommendation || 'N/A'}
                </td>
            </tr>
        `;
    }).join('');

    // Attach click handlers to rows
    document.querySelectorAll('.stock-row').forEach(row => {
        row.addEventListener('click', handleStockRowClick);
    });
}

/**
 * Render macro analysis grid
 * @param {Object} data - Macro analysis data
 */
function renderUSMacroAnalysis(data) {
    const container = document.getElementById('us-macro-indicators');
    if (!container) return;

    const indicators = data.macro_indicators || {};

    // Convert object to array and add category/style info
    const indicatorArray = Object.entries(indicators).map(([name, values]) => ({
        name,
        value: values.value || 0,
        change_percent: values.change_1d || 0,
        category: getIndicatorCategory(name)
    }));

    container.innerHTML = indicatorArray.map(indicator => {
        const indicatorStyle = getMacroIndicatorStyle(indicator.category);
        const changeClass = indicator.change_percent >= 0 ? 'koyfin-green' : 'koyfin-red';

        return `
            <div class="bg-[#1a1a1a] border border-[#2a2a2a] rounded p-3 ${indicatorStyle}">
                <div class="text-xs text-gray-500 mb-1">${indicator.name}</div>
                <div class="text-lg font-bold text-white mb-1">${indicator.value}</div>
                <div class="${changeClass} text-xs">
                    ${indicator.change_percent >= 0 ? '↑' : '↓'} ${Math.abs(indicator.change_percent).toFixed(2)}%
                </div>
            </div>
        `;
    }).join('');

    // Update AI analysis text
    const aiAnalysisContainer = document.getElementById('us-macro-ai-analysis');
    if (aiAnalysisContainer && data.ai_analysis) {
        aiAnalysisContainer.innerHTML = marked.parse(data.ai_analysis);
    }
}

/**
 * Render ETF flows data
 * @param {Object} data - ETF flows data
 */
function renderUSETFFlows(data) {
    const container = document.getElementById('etf-flows-container');
    if (!container) return;

    const flows = data.etf_flows || [];

    container.innerHTML = flows.map(flow => {
        const flowClass = flow.flow >= 0 ? 'koyfin-green' : 'koyfin-red';
        const flowIcon = flow.flow >= 0 ? '↑' : '↓';

        return `
            <div class="flex items-center justify-between py-2 border-b border-[#1f1f1f]">
                <div class="flex items-center gap-2">
                    <span class="font-medium text-white">${flow.ticker}</span>
                    <span class="text-xs text-gray-500">${flow.name}</span>
                </div>
                <div class="${flowClass} text-sm font-medium">
                    ${flowIcon} $${formatMoney(Math.abs(flow.flow))}
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Render historical dates dropdown
 * @param {Object} data - History dates data
 */
function renderHistoryDatesDropdown(data) {
    const dropdown = document.getElementById('history-dates-dropdown');
    if (!dropdown) return;

    const dates = data.dates || [];

    dropdown.innerHTML = dates.map(date => `
        <option value="${date}">${formatDate(date)}</option>
    `).join('');
}

// ==========================================
// STOCK CHART FUNCTIONS
// ==========================================

/**
 * Load and display stock chart for selected ticker
 * @param {string} ticker - Stock ticker symbol
 * @param {string} period - Chart period (1mo, 3mo, 6mo, 1y, 2y, 5y, max)
 */
async function loadUSStockChart(ticker, period = APP_STATE.selectedPeriod) {
    try {
        console.log(`[Chart] Loading chart for ${ticker} (${period})`);

        APP_STATE.currentTicker = ticker;
        APP_STATE.selectedPeriod = period;
        localStorage.setItem('selectedPeriod', period);

        // Highlight selected row
        highlightSelectedRow(ticker);

        // Show loading
        showChartLoading();

        // Fetch chart data
        const data = await fetchWithErrorHandling(
            `/api/us/stock-chart/${ticker}?period=${period}`,
            'Stock Chart'
        );

        if (!data || !data.ohlc_data) {
            showErrorMessage(I18N[APP_STATE.language]['msg.no_data']);
            return;
        }

        // Destroy existing chart
        destroyChart();

        // Create new chart
        createChart(data);

        // Update chart header
        updateChartHeader(ticker, data);

        // Re-apply enabled indicators
        await reapplyIndicators(ticker);

        // Load AI summary
        loadUSAISummary(ticker);

    } catch (error) {
        console.error('[Chart] Error loading chart:', error);
        showErrorMessage(I18N[APP_STATE.language]['msg.error'] + ': ' + error.message);
    }
}

/**
 * Create Lightweight Charts instance and render candlestick data
 * @param {Object} data - Chart data with OHLC
 */
function createChart(data) {
    const chartContainer = document.getElementById('stock-chart-container');
    if (!chartContainer) return;

    // Clear container
    chartContainer.innerHTML = '<div id="main-chart" style="width: 100%; height: 100%;"></div>';

    // Create chart instance
    APP_STATE.chart = LightweightCharts.createChart(document.getElementById('main-chart'), {
        width: chartContainer.clientWidth,
        height: 500,
        layout: {
            background: { type: 'solid', color: '#121212' },
            textColor: '#e0e0e0',
        },
        grid: {
            vertLines: { color: '#2a2a2a' },
            horzLines: { color: '#2a2a2a' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
        },
        rightPriceScale: {
            borderColor: '#2a2a2a',
        },
        timeScale: {
            borderColor: '#2a2a2a',
            timeVisible: true,
            secondsVisible: false,
        },
    });

    // Create candlestick series
    APP_STATE.candlestickSeries = APP_STATE.chart.addCandlestickSeries({
        upColor: '#00E396',
        downColor: '#FF4560',
        borderVisible: false,
        wickUpColor: '#00E396',
        wickDownColor: '#FF4560',
    });

    // Add data
    APP_STATE.candlestickSeries.setData(data.ohlc_data);

    // Create volume series (separate pane)
    if (data.volume_data) {
        APP_STATE.volumeSeries = APP_STATE.chart.addHistogramSeries({
            color: '#26a69a',
            priceFormat: {
                type: 'volume',
            },
            priceScaleId: '',
        });

        APP_STATE.volumeSeries.setData(data.volume_data);

        // Scale volume to bottom
        APP_STATE.chart.priceScale('').applyOptions({
            scaleMargins: {
                top: 0.8,
                bottom: 0,
            },
        });
    }

    // Fit content
    APP_STATE.chart.timeScale().fitContent();

    // Handle resize
    window.addEventListener('resize', handleChartResize);
}

/**
 * Destroy existing chart instance
 */
function destroyChart() {
    if (APP_STATE.chart) {
        APP_STATE.chart.remove();
        APP_STATE.chart = null;
        APP_STATE.candlestickSeries = null;
        APP_STATE.volumeSeries = null;

        // Clear indicator series
        APP_STATE.indicatorSeries = {
            bollingerBands: { upper: null, lower: null, middle: null },
            rsi: null,
            macd: { macd: null, signal: null, histogram: null },
            supportResistance: null
        };
    }

    window.removeEventListener('resize', handleChartResize);
}

/**
 * Handle chart resize on window resize
 */
function handleChartResize() {
    if (APP_STATE.chart) {
        const chartContainer = document.getElementById('stock-chart-container');
        if (chartContainer) {
            APP_STATE.chart.applyOptions({
                width: chartContainer.clientWidth
            });
        }
    }
}

/**
 * Update chart header with stock info
 * @param {string} ticker - Stock ticker
 * @param {Object} data - Chart data
 */
function updateChartHeader(ticker, data) {
    const header = document.getElementById('chart-header');
    if (!header) return;

    const pick = APP_STATE.cachedData.smartMoney?.top_picks?.find(p => p.ticker === ticker);

    header.innerHTML = `
        <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
                <h2 class="text-xl font-bold text-white">${ticker}</h2>
                ${pick ? `<span class="text-gray-400">${pick.name}</span>` : ''}
                ${pick ? `<span class="px-2 py-1 bg-blue-600 text-white text-xs font-bold rounded">Score: ${pick.total_score.toFixed(1)}</span>` : ''}
            </div>
            <div class="flex items-center gap-2">
                ${renderPeriodButtons(ticker)}
            </div>
        </div>
    `;

    // Attach period button handlers
    header.querySelectorAll('.period-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const period = e.target.dataset.period;
            loadUSStockChart(ticker, period);
        });
    });
}

/**
 * Render period selector buttons
 * @param {string} ticker - Current ticker
 * @returns {string} HTML string of buttons
 */
function renderPeriodButtons(ticker) {
    const periods = ['1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'];
    const labels = {
        '1mo': I18N[APP_STATE.language]['btn.period.1mo'],
        '3mo': I18N[APP_STATE.language]['btn.period.3mo'],
        '6mo': I18N[APP_STATE.language]['btn.period.6mo'],
        '1y': I18N[APP_STATE.language]['btn.period.1y'],
        '2y': I18N[APP_STATE.language]['btn.period.2y'],
        '5y': I18N[APP_STATE.language]['btn.period.5y'],
        'max': I18N[APP_STATE.language]['btn.period.max']
    };

    return periods.map(period => {
        const isActive = period === APP_STATE.selectedPeriod;
        const activeClass = isActive ? 'bg-blue-600 text-white' : 'bg-[#1a1a1a] text-gray-400 hover:text-white';

        return `
            <button class="period-btn px-3 py-1 text-xs font-medium rounded border border-[#333] ${activeClass}"
                    data-period="${period}">
                ${labels[period]}
            </button>
        `;
    }).join('');
}

// ==========================================
// TECHNICAL INDICATORS
// ==========================================

/**
 * Toggle technical indicator overlay
 * @param {string} indicatorType - Type of indicator ('bb', 'rsi', 'macd', 'sr')
 */
async function toggleIndicator(indicatorType) {
    const index = APP_STATE.enabledIndicators.indexOf(indicatorType);
    const isEnabled = index !== -1;

    if (isEnabled) {
        // Disable indicator
        APP_STATE.enabledIndicators.splice(index, 1);
        removeIndicator(indicatorType);
    } else {
        // Enable indicator
        APP_STATE.enabledIndicators.push(indicatorType);
        await addIndicator(indicatorType);
    }

    // Save to localStorage
    localStorage.setItem('enabledIndicators', JSON.stringify(APP_STATE.enabledIndicators));

    // Update button state
    updateIndicatorButtons();
}

/**
 * Add indicator to chart
 * @param {string} indicatorType - Type of indicator
 */
async function addIndicator(indicatorType) {
    if (!APP_STATE.currentTicker) {
        showErrorMessage('Please select a stock first');
        return;
    }

    // Check if data is already cached
    if (!APP_STATE.cachedData.technicalIndicators[APP_STATE.currentTicker]) {
        await fetchTechnicalIndicators(APP_STATE.currentTicker);
    }

    const indicatorData = APP_STATE.cachedData.technicalIndicators[APP_STATE.currentTicker];
    if (!indicatorData) {
        showErrorMessage('Technical indicator data not available');
        return;
    }

    switch (indicatorType) {
        case 'bb':
            renderBollingerBands(indicatorData.bollinger_bands);
            break;
        case 'rsi':
            renderRSI(indicatorData.rsi);
            break;
        case 'macd':
            renderMACD(indicatorData.macd);
            break;
        case 'sr':
            renderSupportResistance(indicatorData.support_resistance);
            break;
    }
}

/**
 * Remove indicator from chart
 * @param {string} indicatorType - Type of indicator
 */
function removeIndicator(indicatorType) {
    if (!APP_STATE.chart) return;

    switch (indicatorType) {
        case 'bb':
            if (APP_STATE.indicatorSeries.bollingerBands.upper) {
                APP_STATE.chart.removeSeries(APP_STATE.indicatorSeries.bollingerBands.upper);
                APP_STATE.chart.removeSeries(APP_STATE.indicatorSeries.bollingerBands.lower);
                APP_STATE.chart.removeSeries(APP_STATE.indicatorSeries.bollingerBands.middle);
                APP_STATE.indicatorSeries.bollingerBands = { upper: null, lower: null, middle: null };
            }
            break;
        case 'rsi':
            if (APP_STATE.indicatorSeries.rsi) {
                APP_STATE.chart.removeSeries(APP_STATE.indicatorSeries.rsi);
                APP_STATE.indicatorSeries.rsi = null;
            }
            break;
        case 'macd':
            if (APP_STATE.indicatorSeries.macd.macd) {
                APP_STATE.chart.removeSeries(APP_STATE.indicatorSeries.macd.macd);
                APP_STATE.chart.removeSeries(APP_STATE.indicatorSeries.macd.signal);
                APP_STATE.chart.removeSeries(APP_STATE.indicatorSeries.macd.histogram);
                APP_STATE.indicatorSeries.macd = { macd: null, signal: null, histogram: null };
            }
            break;
        case 'sr':
            if (APP_STATE.indicatorSeries.supportResistance) {
                APP_STATE.indicatorSeries.supportResistance.forEach(series => {
                    APP_STATE.chart.removeSeries(series);
                });
                APP_STATE.indicatorSeries.supportResistance = null;
            }
            break;
    }
}

/**
 * Fetch technical indicators data from API
 * @param {string} ticker - Stock ticker
 */
async function fetchTechnicalIndicators(ticker) {
    const data = await fetchWithErrorHandling(
        `/api/us/technical-indicators/${ticker}`,
        'Technical Indicators'
    );

    if (data) {
        APP_STATE.cachedData.technicalIndicators[ticker] = data;
    }
}

/**
 * Re-apply all enabled indicators (e.g., after loading new chart)
 * @param {string} ticker - Stock ticker
 */
async function reapplyIndicators(ticker) {
    for (const indicatorType of APP_STATE.enabledIndicators) {
        await addIndicator(indicatorType);
    }
}

/**
 * Render Bollinger Bands on chart
 * @param {Object} data - Bollinger Bands data
 */
function renderBollingerBands(data) {
    if (!data || !APP_STATE.chart || !APP_STATE.candlestickSeries) return;

    // Upper band
    APP_STATE.indicatorSeries.bollingerBands.upper = APP_STATE.chart.addLineSeries({
        color: '#FF6B6B',
        lineWidth: 1,
        priceLineVisible: false,
    });
    APP_STATE.indicatorSeries.bollingerBands.upper.setData(data.upper);

    // Lower band
    APP_STATE.indicatorSeries.bollingerBands.lower = APP_STATE.chart.addLineSeries({
        color: '#4ECDC4',
        lineWidth: 1,
        priceLineVisible: false,
    });
    APP_STATE.indicatorSeries.bollingerBands.lower.setData(data.lower);

    // Middle band (SMA)
    APP_STATE.indicatorSeries.bollingerBands.middle = APP_STATE.chart.addLineSeries({
        color: '#95E1D3',
        lineWidth: 1,
        priceLineVisible: false,
    });
    APP_STATE.indicatorSeries.bollingerBands.middle.setData(data.middle);
}

/**
 * Render RSI indicator on separate pane
 * @param {Object} data - RSI data
 */
function renderRSI(data) {
    if (!data || !APP_STATE.chart) return;

    APP_STATE.indicatorSeries.rsi = APP_STATE.chart.addLineSeries({
        color: '#9B59B6',
        lineWidth: 2,
        priceLineVisible: false,
        priceScaleId: 'rsi',
    });

    APP_STATE.indicatorSeries.rsi.setData(data);

    // Configure RSI scale
    APP_STATE.chart.priceScale('rsi').applyOptions({
        scaleMargins: {
            top: 0.1,
            bottom: 0.8,
        },
    });
}

/**
 * Render MACD indicator on separate pane
 * @param {Object} data - MACD data with macd, signal, histogram
 */
function renderMACD(data) {
    if (!data || !APP_STATE.chart) return;

    // MACD line
    APP_STATE.indicatorSeries.macd.macd = APP_STATE.chart.addLineSeries({
        color: '#2962FF',
        lineWidth: 2,
        priceLineVisible: false,
        priceScaleId: 'macd',
    });
    APP_STATE.indicatorSeries.macd.macd.setData(data.macd);

    // Signal line
    APP_STATE.indicatorSeries.macd.signal = APP_STATE.chart.addLineSeries({
        color: '#FF6D00',
        lineWidth: 2,
        priceLineVisible: false,
        priceScaleId: 'macd',
    });
    APP_STATE.indicatorSeries.macd.signal.setData(data.signal);

    // Histogram
    APP_STATE.indicatorSeries.macd.histogram = APP_STATE.chart.addHistogramSeries({
        color: '#26a69a',
        priceFormat: {
            type: 'price',
            precision: 4,
            minMove: 0.0001,
        },
        priceScaleId: 'macd',
    });
    APP_STATE.indicatorSeries.macd.histogram.setData(data.histogram);

    // Configure MACD scale
    APP_STATE.chart.priceScale('macd').applyOptions({
        scaleMargins: {
            top: 0.5,
            bottom: 0,
        },
    });
}

/**
 * Render support/resistance levels
 * @param {Array} data - Array of support/resistance levels
 */
function renderSupportResistance(data) {
    if (!data || !APP_STATE.chart) return;

    APP_STATE.indicatorSeries.supportResistance = [];

    data.forEach((level, index) => {
        const color = level.type === 'support' ? '#00E396' : '#FF4560';

        const series = APP_STATE.chart.addLineSeries({
            color: color,
            lineWidth: 2,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            priceLineVisible: false,
        });

        // Create horizontal line at price level
        const lineData = data.map(d => ({
            time: d.time,
            value: level.price
        }));

        series.setData(lineData);
        APP_STATE.indicatorSeries.supportResistance.push(series);
    });
}

/**
 * Update indicator button states
 */
function updateIndicatorButtons() {
    document.querySelectorAll('.indicator-btn').forEach(btn => {
        const indicatorType = btn.dataset.indicator;
        const isEnabled = APP_STATE.enabledIndicators.includes(indicatorType);

        if (isEnabled) {
            btn.classList.add('bg-blue-600', 'text-white');
            btn.classList.remove('bg-[#1a1a1a]', 'text-gray-400');
        } else {
            btn.classList.remove('bg-blue-600', 'text-white');
            btn.classList.add('bg-[#1a1a1a]', 'text-gray-400');
        }
    });
}

// ==========================================
// MACRO ANALYSIS
// ==========================================

/**
 * Reload macro analysis section
 * Fetches fresh data from API and updates grid and AI text
 */
async function reloadMacroAnalysis() {
    try {
        console.log('[Macro] Reloading macro analysis...');

        const data = await fetchWithErrorHandling(
            `/api/us/macro-analysis?lang=${APP_STATE.language}&model=${APP_STATE.model}`,
            'Macro Analysis'
        );

        if (data) {
            APP_STATE.cachedData.macroAnalysis = data;
            renderUSMacroAnalysis(data);
        }

    } catch (error) {
        console.error('[Macro] Error reloading macro analysis:', error);
    }
}

/**
 * Load AI summary for specific stock
 * @param {string} ticker - Stock ticker
 */
async function loadUSAISummary(ticker) {
    try {
        const container = document.getElementById('us-ai-summary');
        if (!container) return;

        container.innerHTML = `<p class="text-gray-500">${I18N[APP_STATE.language]['msg.loading']}</p>`;

        const data = await fetchWithErrorHandling(
            `/api/us/ai-summary/${ticker}?lang=${APP_STATE.language}&model=${APP_STATE.model}`,
            'Stock AI Analysis'
        );

        if (data && data.summary) {
            container.innerHTML = marked.parse(data.summary);
        } else if (data && data.error) {
            container.innerHTML = `<p class="text-yellow-500">${data.error}</p>`;
        } else {
            container.innerHTML = `<p class="text-gray-500">${I18N[APP_STATE.language]['msg.no_data']}</p>`;
        }

    } catch (error) {
        console.error('[AI] Error loading AI summary:', error);
    }
}

// ==========================================
// REAL-TIME PRICE UPDATES
// ==========================================

/**
 * Update real-time prices for all visible stocks
 * Runs every 30 seconds
 */
async function updateRealtimePrices() {
    try {
        // Collect visible tickers
        const tickers = [];
        document.querySelectorAll('.stock-row').forEach(row => {
            const ticker = row.dataset.ticker;
            if (ticker) {
                tickers.push(ticker);
            }
        });

        if (tickers.length === 0) return;

        // Fetch batch prices
        const response = await fetch('/api/realtime-prices', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ tickers })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        // Update each stock row
        data.prices.forEach(priceUpdate => {
            updateStockPrice(priceUpdate);
        });

        // Update chart if ticker matches
        if (APP_STATE.currentTicker && APP_STATE.candlestickSeries) {
            const chartUpdate = data.prices.find(p => p.ticker === APP_STATE.currentTicker);
            if (chartUpdate) {
                updateChartLastCandle(chartUpdate);
            }
        }

    } catch (error) {
        console.error('[Prices] Error updating real-time prices:', error);
    }
}

/**
 * Update single stock price in table
 * @param {Object} priceUpdate - Price update object with ticker, price, change
 */
function updateStockPrice(priceUpdate) {
    const row = document.querySelector(`.stock-row[data-ticker="${priceUpdate.ticker}"]`);
    if (!row) return;

    const priceCell = row.querySelector('.stock-price');
    const changeCell = row.querySelector('.stock-change');

    if (priceCell) {
        const oldPrice = parseFloat(priceCell.textContent.replace('$', ''));
        const newPrice = priceUpdate.price;

        priceCell.textContent = `$${newPrice.toFixed(2)}`;

        // Flash effect
        const flashClass = newPrice > oldPrice ? 'flash-green' : 'flash-red';
        priceCell.classList.add(flashClass);
        setTimeout(() => priceCell.classList.remove(flashClass), 500);
    }

    if (changeCell) {
        const changeClass = priceUpdate.change >= 0 ? 'koyfin-green' : 'koyfin-red';
        changeCell.className = changeClass;
        changeCell.textContent = `${priceUpdate.change >= 0 ? '+' : ''}${priceUpdate.change.toFixed(2)}%`;
    }
}

/**
 * Update last candle on chart with real-time price
 * @param {Object} priceUpdate - Price update object
 */
function updateChartLastCandle(priceUpdate) {
    if (!APP_STATE.candlestickSeries) return;

    // Update last candle or create new one
    const now = Math.floor(Date.now() / 1000);
    const lastCandle = {
        time: now,
        open: priceUpdate.price,
        high: priceUpdate.price,
        low: priceUpdate.price,
        close: priceUpdate.price
    };

    APP_STATE.candlestickSeries.update(lastCandle);
}

// ==========================================
// HISTORICAL VIEW
// ==========================================

/**
 * Load historical picks view for selected date
 * @param {string} date - Date string (YYYY-MM-DD)
 */
async function loadHistoricalView(date) {
    try {
        console.log(`[History] Loading historical view for ${date}`);

        const data = await fetchWithErrorHandling(
            `/api/us/history/${date}`,
            'Historical Data'
        );

        if (!data) return;

        // Calculate returns since recommendation
        const picks = data.picks || [];
        picks.forEach(pick => {
            pick.return_since_rec = calculateReturn(pick.recommendation_price, pick.current_price);
            pick.days_since_rec = calculateDaysSince(pick.recommendation_date);
        });

        // Sort by return (best performers first)
        picks.sort((a, b) => b.return_since_rec - a.return_since_rec);

        // Render historical table
        renderHistoricalTable(date, picks);

    } catch (error) {
        console.error('[History] Error loading historical view:', error);
        showErrorMessage(I18N[APP_STATE.language]['msg.error'] + ': ' + error.message);
    }
}

/**
 * Render historical picks table
 * @param {string} date - Date string
 * @param {Array} picks - Array of historical picks
 */
function renderHistoricalTable(date, picks) {
    const tableBody = document.getElementById('historical-table-body');
    if (!tableBody) return;

    tableBody.innerHTML = picks.map(pick => {
        const returnClass = pick.return_since_rec >= 0 ? 'koyfin-green' : 'koyfin-red';

        return `
            <tr class="hover:bg-[#1a1a1a]">
                <td class="font-medium text-white">${pick.ticker}</td>
                <td class="text-gray-400">${pick.name}</td>
                <td class="text-gray-400">$${pick.recommendation_price.toFixed(2)}</td>
                <td class="text-white">$${pick.current_price.toFixed(2)}</td>
                <td class="${returnClass} font-bold">
                    ${pick.return_since_rec >= 0 ? '+' : ''}${pick.return_since_rec.toFixed(2)}%
                </td>
                <td class="text-gray-400">${pick.days_since_rec} days</td>
                <td class="text-xs text-gray-500">${formatDate(pick.recommendation_date)}</td>
            </tr>
        `;
    }).join('');
}

/**
 * Calculate return percentage
 * @param {number} entryPrice - Entry price
 * @param {number} currentPrice - Current price
 * @returns {number} Return percentage
 */
function calculateReturn(entryPrice, currentPrice) {
    return ((currentPrice - entryPrice) / entryPrice) * 100;
}

/**
 * Calculate days since recommendation date
 * @param {string} recDate - Recommendation date string
 * @returns {number} Days since
 */
function calculateDaysSince(recDate) {
    const rec = new Date(recDate);
    const now = new Date();
    const diff = now - rec;
    return Math.floor(diff / (1000 * 60 * 60 * 24));
}

// ==========================================
// EVENT HANDLERS
// ==========================================

/**
 * Handle stock row click
 * @param {Event} event - Click event
 */
function handleStockRowClick(event) {
    const row = event.currentTarget;
    const ticker = row.dataset.ticker;
    const index = parseInt(row.dataset.index);

    if (!ticker) return;

    // Get pick data from cache
    const pick = APP_STATE.cachedData.smartMoney?.top_picks?.[index];

    if (pick) {
        APP_STATE.currentPick = pick;
    }

    // Load chart
    loadUSStockChart(ticker, APP_STATE.selectedPeriod);
}

/**
 * Highlight selected row in table
 * @param {string} ticker - Stock ticker
 */
function highlightSelectedRow(ticker) {
    // Remove previous highlight
    document.querySelectorAll('.stock-row').forEach(row => {
        row.classList.remove('bg-blue-900/30');
    });

    // Add highlight to selected row
    const selectedRow = document.querySelector(`.stock-row[data-ticker="${ticker}"]`);
    if (selectedRow) {
        selectedRow.classList.add('bg-blue-900/30');
    }
}

/**
 * Setup all event listeners
 */
function setupEventListeners() {
    // Language switchers
    document.querySelectorAll('.lang-selector').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const lang = e.target.dataset.lang;
            translateUI(lang);
        });
    });

    // Model switchers
    document.querySelectorAll('.model-selector').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const model = e.target.dataset.model;
            switchModel(model);
        });
    });

    // Indicator toggles
    document.querySelectorAll('.indicator-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const indicatorType = e.target.dataset.indicator;
            toggleIndicator(indicatorType);
        });
    });

    // Refresh button
    const refreshBtn = document.getElementById('refresh-dashboard-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            updateUSMarketDashboard();
        });
    }

    // Historical dates dropdown
    const historyDropdown = document.getElementById('history-dates-dropdown');
    if (historyDropdown) {
        historyDropdown.addEventListener('change', (e) => {
            const date = e.target.value;
            if (date) {
                loadHistoricalView(date);
            }
        });
    }

    // Search box (optional)
    const searchInput = document.getElementById('stock-search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const ticker = e.target.value.toUpperCase();
                loadUSStockChart(ticker);
            }
        });
    }
}

// ==========================================
// AUTO-REFRESH
// ==========================================

/**
 * Start auto-refresh intervals
 */
function startAutoRefresh() {
    // Macro analysis: every 10 minutes
    APP_STATE.refreshIntervals.macro = setInterval(() => {
        reloadMacroAnalysis();
    }, 10 * 60 * 1000);

    // Real-time prices: every 30 seconds
    APP_STATE.refreshIntervals.prices = setInterval(() => {
        updateRealtimePrices();
    }, 30 * 1000);

    console.log('[AutoRefresh] Started (Macro: 10min, Prices: 30s)');
}

/**
 * Stop all auto-refresh intervals
 */
function stopAutoRefresh() {
    if (APP_STATE.refreshIntervals.macro) {
        clearInterval(APP_STATE.refreshIntervals.macro);
        APP_STATE.refreshIntervals.macro = null;
    }

    if (APP_STATE.refreshIntervals.prices) {
        clearInterval(APP_STATE.refreshIntervals.prices);
        APP_STATE.refreshIntervals.prices = null;
    }

    console.log('[AutoRefresh] Stopped');
}

// ==========================================
// UTILITY FUNCTIONS
// ==========================================

/**
 * Get color for score display
 * @param {number} score - Score value (0-100)
 * @returns {string} CSS class name
 */
function getScoreColor(score) {
    if (score >= 80) return 'text-green-500';
    if (score >= 60) return 'text-blue-400';
    if (score >= 40) return 'text-yellow-500';
    return 'text-red-500';
}

/**
 * Get emoji for AI recommendation
 * @param {string} recommendation - AI recommendation text
 * @returns {string} Emoji
 */
function getAIRecommendationEmoji(recommendation) {
    if (!recommendation) return '';

    const rec = recommendation.toLowerCase();
    if (rec.includes('strong buy') || rec.includes('매수')) return '🔥';
    if (rec.includes('buy') || rec.includes('buy')) return '📈';
    if (rec.includes('hold') || rec.includes('보유')) return '📊';
    return '';
}

/**
 * Get CSS style for macro indicator category
 * @param {string} category - Category name
 * @returns {string} CSS class string
 */
function getMacroIndicatorStyle(category) {
    switch (category) {
        case 'volatility':
            return 'border-purple-500/30';
        case 'crypto':
            return 'border-orange-500/30';
        case 'yields':
            return 'border-blue-500/30';
        default:
            return 'border-gray-500/30';
    }
}

/**
 * Get category for macro indicator
 * @param {string} name - Indicator name
 */
function getIndicatorCategory(name) {
    const upperName = name.toUpperCase();

    if (upperName === 'VIX') return 'volatility';
    if (upperName === 'BTC' || upperName.includes('CRYPTO')) return 'crypto';
    if (upperName.includes('YIELD') || upperName === 'DXY') return 'yields';

    return 'default';
}

/**
 * Format date string for display
 * @param {string} dateStr - Date string (YYYY-MM-DD)
 * @returns {string} Formatted date
 */
function formatDate(dateStr) {
    if (!dateStr) return 'N/A';

    const date = new Date(dateStr);
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const year = date.getFullYear();

    return `${month}/${day}/${year}`;
}

/**
 * Format money value (billions/millions)
 * @param {number} value - Numeric value
 * @returns {string} Formatted string
 */
function formatMoney(value) {
    if (Math.abs(value) >= 1e9) {
        return (value / 1e9).toFixed(2) + 'B';
    } else if (Math.abs(value) >= 1e6) {
        return (value / 1e6).toFixed(2) + 'M';
    } else {
        return value.toFixed(2);
    }
}

/**
 * Show loading indicator
 */
function showLoadingIndicator() {
    const indicator = document.getElementById('loading-indicator');
    if (indicator) {
        indicator.style.display = 'flex';
    }
}

/**
 * Hide loading indicator
 */
function hideLoadingIndicator() {
    const indicator = document.getElementById('loading-indicator');
    if (indicator) {
        indicator.style.display = 'none';
    }
}

/**
 * Show chart loading indicator
 */
function showChartLoading() {
    const chartContainer = document.getElementById('stock-chart-container');
    if (chartContainer) {
        chartContainer.innerHTML = `
            <div class="flex items-center justify-center h-full">
                <div class="text-center">
                    <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-2"></div>
                    <p class="text-gray-500 text-sm">${I18N[APP_STATE.language]['msg.loading']}</p>
                </div>
            </div>
        `;
    }
}

/**
 * Show error message to user
 * @param {string} message - Error message
 */
function showErrorMessage(message) {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-4 right-4 bg-red-600 text-white px-4 py-2 rounded shadow-lg z-50 animate-fade-in';
    toast.textContent = message;
    document.body.appendChild(toast);

    // Auto-remove after 3 seconds
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

/**
 * Show success message to user
 * @param {string} message - Success message
 */
function showSuccessMessage(message) {
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-4 right-4 bg-green-600 text-white px-4 py-2 rounded shadow-lg z-50 animate-fade-in';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// ==========================================
// INITIALIZATION
// ==========================================

/**
 * Initialize application
 */
function initApp() {
    console.log('[App] Initializing...');

    // Setup event listeners
    setupEventListeners();

    // Update indicator button states
    updateIndicatorButtons();

    // Load dashboard data
    updateUSMarketDashboard();

    // Start auto-refresh
    startAutoRefresh();

    // Apply saved language
    translateUI(APP_STATE.language);

    // Apply saved model
    switchModel(APP_STATE.model);

    console.log('[App] Initialization complete');
}

/**
 * Cleanup on page unload
 */
function cleanup() {
    stopAutoRefresh();
    destroyChart();
}

// ==========================================
// DOM READY
// ==========================================

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

// Cleanup on page unload
window.addEventListener('beforeunload', cleanup);

// ==========================================
// CREATE MARKET REPORT
// ==========================================

/**
 * Create market data report by triggering data update
 */
async function createMarketReport() {
    try {
        // Show loading message
        const message = I18N[APP_STATE.language]?.updatingData || 'Updating market data...';
        showNotification(message, 'info');

        // Call API to update data
        const response = await fetch('/api/us/update-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            showNotification(
                '✅ ' + (I18N[APP_STATE.language]?.dataUpdateStarted ||
                    'Data update started! This may take 30-40 minutes. Please check back later.'),
                'success'
            );
        } else {
            showNotification(
                '❌ ' + (I18N[APP_STATE.language]?.dataUpdateFailed ||
                    'Failed to start data update: ') + (result.error || 'Unknown error'),
                'error'
            );
        }
    } catch (error) {
        console.error('Error creating market report:', error);
        showNotification(
            '❌ ' + (I18N[APP_STATE.language]?.requestFailed ||
                'Failed to create report. Please try again.'),
            'error'
        );
    }
}

/**
 * Show notification to user
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-sm font-medium ${
        type === 'success' ? 'bg-green-600 text-white' :
        type === 'error' ? 'bg-red-600 text-white' :
        'bg-blue-600 text-white'
    }`;
    notification.textContent = message;

    // Add to DOM
    document.body.appendChild(notification);

    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// ==========================================
// EXPORT FOR TESTING
// ==========================================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        APP_STATE,
        I18N,
        translateUI,
        switchModel,
        updateUSMarketDashboard,
        loadUSStockChart,
        toggleIndicator,
        reloadMacroAnalysis,
        updateRealtimePrices,
        loadHistoricalView,
        createMarketReport
    };
}
