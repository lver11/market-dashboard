#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sector Performance Heatmap Data Collector
"""

import os
import json
import yfinance as yf
from datetime import datetime
from typing import Dict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SectorHeatmapCollector:
    """Collect sector ETF performance data for heatmap visualization"""

    def __init__(self):
        # Sector ETFs with full names
        self.sector_etfs = {
            'XLK': {'name': 'Technology', 'color': '#4A90A4'},
            'XLF': {'name': 'Financials', 'color': '#6B8E23'},
            'XLV': {'name': 'Healthcare', 'color': '#FF69B4'},
            'XLE': {'name': 'Energy', 'color': '#FF6347'},
            'XLY': {'name': 'Consumer Disc.', 'color': '#FFD700'},
            'XLP': {'name': 'Consumer Staples', 'color': '#98D8C8'},
            'XLI': {'name': 'Industrials', 'color': '#DDA0DD'},
            'XLB': {'name': 'Materials', 'color': '#F0E68C'},
            'XLU': {'name': 'Utilities', 'color': '#87CEEB'},
            'XLRE': {'name': 'Real Estate', 'color': '#CD853F'},
            'XLC': {'name': 'Comm. Services', 'color': '#9370DB'},
        }

        # Sector stocks for detail map
        self.sector_stocks = {
             'Technology': ['AAPL', 'MSFT', 'NVDA', 'AVGO', 'ORCL', 'CRM', 'AMD', 'ADBE'],
             'Financials': ['BRK-B', 'JPM', 'V', 'MA', 'BAC', 'WFC', 'GS', 'MS'],
        }

    def get_full_market_map(self, period: str = '5d') -> Dict:
        """Get full market map data (Sectors -> Stocks) for Treemap"""
        logger.info(f"📊 Fetching full market map data ({period})...")

        all_tickers = []
        ticker_to_sector = {}
        for sector, stocks in self.sector_stocks.items():
            all_tickers.extend(stocks)
            for stock in stocks:
                ticker_to_sector[stock] = sector

        try:
            # Download data individually to avoid yfinance MultiIndex issues
            data_dict = {}
            for ticker in all_tickers:
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period=period)
                    if not hist.empty:
                        data_dict[ticker] = hist
                except Exception as e:
                    logger.warning(f"Failed to fetch {ticker}: {e}")
                    continue

            if not data_dict:
                return {'error': 'No data fetched'}

            market_map = {name: [] for name in self.sector_stocks.keys()}

            for ticker, hist in data_dict.items():
                try:
                    if len(hist) < 2:
                        continue

                    current = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    change = ((current / prev) - 1) * 100

                    # Weight by Volume * Price (Activity proxy)
                    vol = hist['Volume'].iloc[-1] if 'Volume' in hist.columns else 100000
                    weight = current * vol

                    sector = ticker_to_sector.get(ticker, 'Unknown')
                    if sector in market_map:
                        market_map[sector].append({
                            'x': ticker,
                            'y': round(weight, 0),
                            'price': round(current, 2),
                            'change': round(change, 2),
                            'color': self._get_color(change)
                        })
                except Exception as e:
                    logger.warning(f"Error processing {ticker}: {e}")
                    continue

            series = []
            for sector_name, stocks in market_map.items():
                if stocks:
                    stocks.sort(key=lambda x: x['y'], reverse=True)
                    series.append({'name': sector_name, 'data': stocks})

            series.sort(key=lambda s: sum(i['y'] for i in s['data']), reverse=True)

            return {
                'timestamp': datetime.now().isoformat(),
                'period': period,
                'series': series
            }

        except Exception as e:
            logger.error(f"Error: {e}")
            return {'error': str(e)}

    def _get_color(self, change: float) -> str:
        if change >= 3:
            return '#00C853'
        elif change >= 1:
            return '#4CAF50'
        elif change >= 0:
            return '#81C784'
        elif change >= -1:
            return '#EF9A9A'
        elif change >= -3:
            return '#F44336'
        else:
            return '#B71C1C'

    def save_data(self, output_dir: str = '.'):
        data = self.get_full_market_map('5d')
        output_file = os.path.join(output_dir, 'sector_heatmap.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Saved to {output_file}")


if __name__ == "__main__":
    SectorHeatmapCollector().save_data()
