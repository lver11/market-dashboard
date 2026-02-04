#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
US ETF Fund Flow Analysis
Analyzes 24 major ETFs and generates AI insights using Gemini 3.0
"""

import os
import pandas as pd
import yfinance as yf
import logging
from datetime import datetime
from typing import Dict
from tqdm import tqdm
import json
import requests

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ETFFlowAnalyzer:
    """Analyze ETF fund flows to detect smart money movement"""

    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.output_file = os.path.join(data_dir, 'us_etf_flows.csv')
        self.ai_output_file = os.path.join(data_dir, 'etf_flow_analysis.json')

        # ETF tickers with categories
        self.etf_tickers = {
            # Broad Market
            'SPY': {'name': 'SPDR S&P 500', 'category': 'Broad Market'},
            'QQQ': {'name': 'Invesco QQQ', 'category': 'Broad Market'},
            'IWM': {'name': 'iShares Russell 2000', 'category': 'Broad Market'},
            'DIA': {'name': 'SPDR Dow Jones', 'category': 'Broad Market'},
            'VTI': {'name': 'Vanguard Total Stock', 'category': 'Broad Market'},
            'VOO': {'name': 'Vanguard S&P 500', 'category': 'Broad Market'},

            # Sectors
            'XLK': {'name': 'Technology', 'category': 'Sector'},
            'XLF': {'name': 'Financial', 'category': 'Sector'},
            'XLV': {'name': 'Healthcare', 'category': 'Sector'},
            'XLE': {'name': 'Energy', 'category': 'Sector'},
            'XLY': {'name': 'Consumer Disc.', 'category': 'Sector'},
            'XLP': {'name': 'Consumer Staples', 'category': 'Sector'},
            'XLI': {'name': 'Industrials', 'category': 'Sector'},
            'XLB': {'name': 'Materials', 'category': 'Sector'},
            'XLU': {'name': 'Utilities', 'category': 'Sector'},
            'XLRE': {'name': 'Real Estate', 'category': 'Sector'},
            'XLC': {'name': 'Comm. Services', 'category': 'Sector'},

            # Themes
            'GLD': {'name': 'Gold SPDR', 'category': 'Commodity'},
            'SLV': {'name': 'Silver iShares', 'category': 'Commodity'},
            'USO': {'name': 'US Oil Fund', 'category': 'Commodity'},
            'TLT': {'name': '20+ Yr Treasury', 'category': 'Fixed Income'},
            'IEF': {'name': '7-10 Yr Treasury', 'category': 'Fixed Income'},
            'HYG': {'name': 'High Yield Corp', 'category': 'Fixed Income'},
            'LQD': {'name': 'Inv. Grade Corp', 'category': 'Fixed Income'},
            'JNK': {'name': 'High Yield Bond', 'category': 'Fixed Income'},
        }

    def calculate_flow_proxy(self, ticker: str, hist: pd.DataFrame) -> Dict:
        """
        Calculate fund flow proxy using OBV, Volume, Price Momentum
        Real ETF AUM data requires paid Bloomberg API
        """
        if len(hist) < 20:
            return {}

        # Calculate OBV
        obv = [0]
        for i in range(1, len(hist)):
            if hist['Close'].iloc[i] > hist['Close'].iloc[i-1]:
                obv.append(obv[-1] + hist['Volume'].iloc[i])
            elif hist['Close'].iloc[i] < hist['Close'].iloc[i-1]:
                obv.append(obv[-1] - hist['Volume'].iloc[i])
            else:
                obv.append(obv[-1])

        # Volume ratio (recent 5d vs 20d)
        vol_5d = hist['Volume'].tail(5).mean()
        vol_20d = hist['Volume'].tail(20).mean()
        vol_ratio = vol_5d / vol_20d if vol_20d > 0 else 1

        # Price momentum (20-day)
        price_momentum = (hist['Close'].iloc[-1] / hist['Close'].iloc[-20] - 1) * 100

        # Flow score (0-100)
        score = 50

        # OBV trend
        obv_change = (obv[-1] - obv[-20]) / abs(obv[-20]) * 100 if obv[-20] != 0 else 0
        if obv_change > 10:
            score += 20
        elif obv_change > 5:
            score += 10
        elif obv_change < -10:
            score -= 20
        elif obv_change < -5:
            score -= 10

        # Volume ratio
        if vol_ratio > 1.5:
            score += 15
        elif vol_ratio > 1.2:
            score += 8
        elif vol_ratio < 0.7:
            score -= 10

        # Price momentum
        if price_momentum > 5:
            score += 15
        elif price_momentum > 2:
            score += 8
        elif price_momentum < -5:
            score -= 15
        elif price_momentum < -2:
            score -= 8

        score = max(0, min(100, score))

        # Determine flow status
        if score >= 70:
            status = "Strong Inflow"
        elif score >= 55:
            status = "Inflow"
        elif score >= 45:
            status = "Neutral"
        elif score >= 30:
            status = "Outflow"
        else:
            status = "Strong Outflow"

        return {
            'ticker': ticker,
            'current_price': round(hist['Close'].iloc[-1], 2),
            'change_1d': round((hist['Close'].iloc[-1] / hist['Close'].iloc[-2] - 1) * 100, 2) if len(hist) >= 2 else 0,
            'volume_ratio': round(vol_ratio, 2),
            'obv_change_20d': round(obv_change, 2),
            'price_momentum_20d': round(price_momentum, 2),
            'flow_score': round(score, 1),
            'flow_status': status
        }

    def run_analysis(self):
        """Run ETF flow analysis for all tickers"""
        logger.info("🚀 Starting ETF Flow Analysis...")

        results = []
        failed_tickers = []

        for ticker, info in tqdm(self.etf_tickers.items(), desc="Analyzing ETFs"):
            try:
                etf = yf.Ticker(ticker)
                hist = etf.history(period="3mo")

                if hist.empty or len(hist) < 20:
                    failed_tickers.append(ticker)
                    continue

                flow_data = self.calculate_flow_proxy(ticker, hist)
                flow_data['name'] = info['name']
                flow_data['category'] = info['category']
                results.append(flow_data)

            except Exception as e:
                logger.debug(f"Error analyzing {ticker}: {e}")
                failed_tickers.append(ticker)

        # Create DataFrame
        results_df = pd.DataFrame(results)

        # Save results
        results_df.to_csv(self.output_file, index=False)
        logger.info(f"✅ ETF analysis complete! Saved to {self.output_file}")

        if failed_tickers:
            logger.warning(f"Failed tickers: {failed_tickers}")

        return results_df

    def generate_ai_analysis(self, results_df: pd.DataFrame):
        """Generate AI insights using Gemini 3.0"""
        from dotenv import load_dotenv
        load_dotenv()

        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            logger.warning("GOOGLE_API_KEY not found. Skipping AI analysis.")
            return

        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-preview:generateContent"

        # Prepare summary data
        broad_market = results_df[results_df['category'] == 'Broad Market']
        sectors = results_df[results_df['category'] == 'Sector']

        # Build prompt
        prompt = f"""Analyze current ETF fund flow patterns and provide investment insights.

Broad Market ETFs:
{broad_market[['ticker', 'flow_status', 'flow_score']].to_string(index=False)}

Top Sector ETFs by Flow Score:
{sectors.nlargest(5, 'flow_score')[['ticker', 'flow_status', 'flow_score']].to_string(index=False)}

Provide analysis in Korean with these sections:
1. Overall Market Sentiment (Risk On/Off)
2. Sectors with strongest inflows (investment opportunities)
3. Sectors with outflows (areas of caution)
4. Strategic recommendations for investors"""

        try:
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1500}
            }
            resp = requests.post(f"{url}?key={api_key}", json=payload, timeout=60)

            if resp.status_code == 200:
                ai_analysis = resp.json()['candidates'][0]['content']['parts'][0]['text']

                # Save AI analysis
                output = {
                    'timestamp': datetime.now().isoformat(),
                    'ai_analysis': ai_analysis
                }
                with open(self.ai_output_file, 'w', encoding='utf-8') as f:
                    json.dump(output, f, ensure_ascii=False, indent=2)

                logger.info("✅ AI analysis saved to etf_flow_analysis.json")
                print(f"\n🤖 Gemini 3.0 ETF Flow Analysis:\n{ai_analysis}\n")

            else:
                logger.error(f"API request failed: {resp.status_code}")

        except Exception as e:
            logger.error(f"Error generating AI analysis: {e}")

    def run(self, generate_ai: bool = True):
        """Main execution"""
        results_df = self.run_analysis()

        if generate_ai:
            self.generate_ai_analysis(results_df)


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='US ETF Flow Analysis')
    parser.add_argument('--no-ai', action='store_true', help='Skip AI analysis')
    args = parser.parse_args()

    analyzer = ETFFlowAnalyzer()
    analyzer.run(generate_ai=not args.no_ai)


if __name__ == "__main__":
    main()
