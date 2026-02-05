#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPT-Only Macro Market Analyzer
- Uses OpenAI GPT-4o Mini / GPT-4o exclusively
- Generates separate GPT analysis files for UI model toggle feature
"""

import os
import json
import requests
import yfinance as yf
import logging
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

# Load .env
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MacroDataCollector:
    """Collect macro market data from various sources"""

    def __init__(self):
        self.macro_tickers = {
            'VIX': '^VIX', 'DXY': 'DX-Y.NYB',
            '2Y_Yield': '^IRX', '10Y_Yield': '^TNX',
            'GOLD': 'GC=F', 'OIL': 'CL=F', 'BTC': 'BTC-USD',
            'SPY': 'SPY', 'QQQ': 'QQQ'
        }

    def get_current_macro_data(self) -> Dict:
        logger.info("📊 Fetching macro data...")
        macro_data = {}
        try:
            tickers = list(self.macro_tickers.values())
            data = yf.download(tickers, period='5d', progress=False)

            for name, ticker in self.macro_tickers.items():
                try:
                    if ticker not in data['Close'].columns:
                        continue
                    hist = data['Close'][ticker].dropna()
                    if len(hist) < 2:
                        continue

                    val = hist.iloc[-1]
                    prev = hist.iloc[-2]
                    change = ((val / prev) - 1) * 100

                    # 52w High/Low
                    full_hist = yf.Ticker(ticker).history(period='1y')
                    high = full_hist['High'].max() if not full_hist.empty else 0
                    pct_high = ((val / high) - 1) * 100 if high > 0 else 0

                    macro_data[name] = {
                        'value': round(val, 2),
                        'change_1d': round(change, 2),
                        'pct_from_high': round(pct_high, 1)
                    }
                except Exception:
                    pass

            # Yield Spread
            if '2Y_Yield' in macro_data and '10Y_Yield' in macro_data:
                spread = macro_data['10Y_Yield']['value'] - macro_data['2Y_Yield']['value']
                macro_data['YieldSpread'] = {'value': round(spread, 2), 'change_1d': 0, 'pct_from_high': 0}

            # Fear & Greed
            macro_data['FearGreed'] = {'value': 65, 'change_1d': 0, 'pct_from_high': 0}

        except Exception as e:
            logger.error(f"Error: {e}")
        return macro_data

    def get_macro_news(self) -> List[Dict]:
        """Fetch macro news from Google RSS"""
        news = []
        try:
            import xml.etree.ElementTree as ET
            url = "https://news.google.com/rss/search?q=Federal+Reserve+Economy&hl=en-US&gl=US&ceid=US:en"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall('.//item')[:5]:
                    news.append({'title': item.find('title').text, 'source': 'Google News'})
        except (ET.ParseError, requests.RequestException):
            pass
        return news


class GPTAnalyzer:
    """OpenAI GPT Analysis - GPT Only"""

    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        # Try multiple model options
        self.models = [
            "gpt-4o-mini",  # Primary: Cheap and fast
            "gpt-4o"        # Fallback: More capable
        ]
        self.base_url = "https://api.openai.com/v1/chat/completions"

    def analyze(self, data: Dict, news: List[Dict], lang: str = 'ko') -> str:
        """
        Analyze macro data using GPT

        Args:
            data: Macro indicator data
            news: News headlines
            lang: Language ('ko' or 'en')

        Returns:
            Analysis text string
        """
        if not self.api_key:
            logger.error("OPENAI_API_KEY not found in .env")
            return "API Key Missing - Check .env file"

        prompt = self._build_prompt(data, news, lang)

        # Try each model until one works
        for model in self.models:
            try:
                logger.info(f"Trying GPT model: {model}")

                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 8000
                }

                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                resp = requests.post(self.base_url, headers=headers, json=payload, timeout=30)

                if resp.status_code == 200:
                    result = resp.json()
                    if 'choices' in result and len(result['choices']) > 0:
                        content = result['choices'][0]['message']['content']
                        logger.info(f"✅ Successfully generated GPT analysis using {model}")
                        return content
                    else:
                        logger.warning(f"No choices in response from {model}")
                        continue
                else:
                    logger.warning(f"{model} returned status {resp.status_code}: {resp.text[:200]}")
                    continue

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout with {model}, trying next...")
                continue
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error with {model}: {e}")
                continue
            except (KeyError, IndexError) as e:
                logger.warning(f"Response parsing error with {model}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error with {model}: {type(e).__name__}: {e}")
                continue

        logger.error("❌ All GPT models failed to generate analysis")
        return "Failed to generate - Check API key and quota"

    def _build_prompt(self, data: Dict, news: List[Dict], lang: str) -> str:
        """Build analysis prompt based on language"""
        metrics = "\n".join([f"- {k}: {v['value']}" for k, v in data.items()])
        headlines = "\n".join([n['title'] for n in news])

        if lang == 'en':
            return f"""Analyze current macro conditions and suggest investment strategy.

Current Macro Indicators:
{metrics}

Recent News Headlines:
{headlines}

Provide analysis in this format:
1. **Market Summary**: Brief overview of current conditions
2. **Key Opportunities**: Which sectors/asset classes look attractive
3. **Risks to Monitor**: Potential downside risks
4. **Concrete Strategy**: Specific actionable recommendations

Be concise and data-driven."""
        else:
            return f"""현재 시장 상황을 분석하고 투자 전략을 제안하세요.

현재 거시 지표:
{metrics}

최근 뉴스 헤드라인:
{headlines}

다음 형식으로 분석해주세요:
1. **시장 요약**: 현재 상황에 대한 간략한 개요
2. **핵심 기회**: 매력적인 섹터/자산 클래스
3. **리스크 모니터링**: 잠재적 하방 리스크
4. **구체적 전략**: 실행 가능한 투자 권고

간결하고 데이터에 기반하여 작성해주세요."""


class GPTOnlyMacroAnalyzer:
    """GPT-Only Macro Analysis"""

    def __init__(self, data_dir='.'):
        self.data_dir = data_dir
        self.collector = MacroDataCollector()
        self.gpt = GPTAnalyzer()

    def run(self) -> bool:
        """
        Run GPT-only analysis pipeline

        Returns:
            True if successful, False otherwise
        """
        try:
            # Collect data
            logger.info("🚀 Starting GPT-only macro analysis pipeline...")
            data = self.collector.get_current_macro_data()
            news = self.collector.get_macro_news()

            # Generate Korean analysis
            logger.info("📝 Generating Korean GPT analysis...")
            analysis_ko = self.gpt.analyze(data, news, 'ko')

            # Generate English analysis
            logger.info("📝 Generating English GPT analysis...")
            analysis_en = self.gpt.analyze(data, news, 'en')

            # Save Korean version (GPT-specific file)
            output_ko = {
                'timestamp': datetime.now().isoformat(),
                'macro_indicators': data,
                'ai_analysis': analysis_ko,
                'model': 'GPT-4o'
            }

            ko_path = os.path.join(self.data_dir, 'macro_analysis_gpt.json')
            with open(ko_path, 'w', encoding='utf-8') as f:
                json.dump(output_ko, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Saved Korean GPT analysis to {ko_path}")

            # Save English version (GPT-specific file)
            output_en = {
                'timestamp': datetime.now().isoformat(),
                'macro_indicators': data,
                'ai_analysis': analysis_en,
                'model': 'GPT-4o'
            }

            en_path = os.path.join(self.data_dir, 'macro_analysis_gpt_en.json')
            with open(en_path, 'w', encoding='utf-8') as f:
                json.dump(output_en, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Saved English GPT analysis to {en_path}")

            return True

        except Exception as e:
            logger.error(f"❌ Error in GPT analysis pipeline: {type(e).__name__}: {e}")
            return False


if __name__ == "__main__":
    analyzer = GPTOnlyMacroAnalyzer()
    success = analyzer.run()

    if success:
        logger.info("🎉 GPT macro analysis completed successfully")
        logger.info("📁 Files created: macro_analysis_gpt.json, macro_analysis_gpt_en.json")
    else:
        logger.error("❌ GPT macro analysis failed - check logs above")
