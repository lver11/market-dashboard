#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Macro Market Analyzer
- Collects macro indicators (VIX, Yields, Commodities, etc.)
- Uses Gemini 2.5 Flash (primary) with OpenAI GPT-4o Mini fallback
- Supports multi-model analysis with automatic fallback logic
"""

import os
import json
import time
import requests
import yfinance as yf
import logging
from datetime import datetime
from typing import Dict, List, Optional
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

            # Fear & Greed (Simulated if scrape fails)
            macro_data['FearGreed'] = {'value': 65, 'change_1d': 0, 'pct_from_high': 0}  # Placeholder

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

    def get_historical_patterns(self) -> List[Dict]:
        return [
            {
                'event': 'Fed Pivot Signal (2023)',
                'conditions': 'VIX declining, Yields peaking',
                'outcome': {'SPY_3m': '+15%', 'best_sectors': ['Tech', 'Comm']}
            }
        ]


class GeminiAnalyzer:
    """Gemini Analysis"""

    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        # Try multiple model options for better availability/cost
        self.models = [
            "gemini-2.5-flash",  # Primary: Fast
            "gemini-2.5-pro"     # Fallback: Capable
        ]
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    def analyze(self, data: Dict, news: List[Dict], patterns: List[Dict], lang: str = 'ko') -> str:
        """
        Analyze macro data using Gemini

        Args:
            data: Macro indicator data
            news: News headlines
            patterns: Historical patterns
            lang: Language ('ko' or 'en')

        Returns:
            Analysis text string
        """
        if not self.api_key:
            logger.error("GOOGLE_API_KEY not found in .env")
            return "API Key Missing - Check .env file"

        prompt = self._build_prompt(data, news, patterns, lang)

        # Try each model until one works
        for model in self.models:
            try:
                logger.info(f"Trying Gemini model: {model}")

                url = self.base_url.format(model=model, api_key=self.api_key)

                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 8000
                    }
                }

                resp = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=30)

                if resp.status_code == 200:
                    result = resp.json()
                    if 'candidates' in result and len(result['candidates']) > 0:
                        content = result['candidates'][0]['content']['parts'][0]['text']
                        logger.info(f"Successfully generated analysis using {model}")
                        return content
                    else:
                        logger.warning(f"No candidates in response from {model}")
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

        logger.error("All Gemini models failed to generate analysis")
        return "Failed to generate - Check API key and quota"

    def _build_prompt(self, data: Dict, news: List[Dict], patterns: List[Dict], lang: str) -> str:
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

class ZAIAnalyzer:
    """Z.ai (Zero One) Analysis - Coding Plan"""

    def __init__(self):
        self.api_key = os.getenv('ZAI_API_KEY')
        # Z.ai Coding Plan base URL
        self.models = [
            "glm-4-plus",   # Primary: Most capable (only model available)
        ]
        self.base_url = "https://api.z.ai/api/coding/paas/v4"
        self.min_request_interval = 2  # Seconds between requests to avoid rate limit

    def analyze(self, data: Dict, news: List[Dict], patterns: List[Dict], lang: str = 'ko') -> str:
        """
        Analyze macro data using Z.ai

        Args:
            data: Macro indicator data
            news: News headlines
            patterns: Historical patterns
            lang: Language ('ko' or 'en')

        Returns:
            Analysis text string
        """
        if not self.api_key:
            logger.error("ZAI_API_KEY not found in .env")
            return "API Key Missing - Check .env file"

        prompt = self._build_prompt(data, news, patterns, lang)

        # Try each model until one works
        for model in self.models:
            try:
                logger.info(f"Trying Z.ai model: {model}")

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

                # Construct full URL
                url = f"{self.base_url}/chat/completions"
                resp = requests.post(url, headers=headers, json=payload, timeout=30)

                if resp.status_code == 200:
                    result = resp.json()
                    if 'choices' in result and len(result['choices']) > 0:
                        content = result['choices'][0]['message']['content']
                        logger.info(f"Successfully generated analysis using Z.ai {model}")
                        time.sleep(self.min_request_interval)  # Rate limit protection
                        return content
                    else:
                        logger.warning(f"No choices in response from Z.ai {model}")
                        continue
                elif resp.status_code == 401:
                    logger.error("Z.ai authentication failed. Check API key.")
                    return "API Authentication Failed"
                elif resp.status_code == 429:
                    logger.warning("Z.ai API rate limit reached. Waiting 5 seconds...")
                    time.sleep(5)  # Wait for rate limit to reset
                    # Retry once after rate limit
                    resp = requests.post(url, headers=headers, json=payload, timeout=30)
                    if resp.status_code == 200:
                        result = resp.json()
                        if 'choices' in result and len(result['choices']) > 0:
                            content = result['choices'][0]['message']['content']
                            logger.info(f"Z.ai retry successful with {model}")
                            time.sleep(self.min_request_interval)
                            return content
                    logger.warning("Z.ai rate limit retry also failed")
                    return "Rate Limit - Try again later"
                else:
                    logger.warning(f"Z.ai {model} returned status {resp.status_code}: {resp.text[:200]}")
                    continue

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout with Z.ai {model}, trying next...")
                continue
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error with Z.ai {model}: {e}")
                continue
            except (KeyError, IndexError) as e:
                logger.warning(f"Response parsing error with Z.ai {model}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error with Z.ai {model}: {type(e).__name__}: {e}")
                continue

        logger.error("All Z.ai models failed to generate analysis")
        return "Failed to generate - Check API key and quota"

    def _build_prompt(self, data: Dict, news: List[Dict], patterns: List[Dict], lang: str) -> str:
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

Be specific and data-driven."""
        else:
            return f"""현재 마크로 경제 상황을 분석하고 투자 전략을 제시해주세요.

현재 마크로 지표:
{metrics}

최근 뉴스 헤드라인:
{headlines}

다음 형식으로 분석을 제공해주세요:
1. **시장 요약**: 현재 상황에 대한 간단한 개요
2. **주요 기회**: 매력적인 섹터/자산 클래스
3. **모니터링 필요 리스크**: 잠재적 하방 리스크
4. **구체적 전략**: 실행 가능한 구체적 권장사항

구체적이고 데이터 기반으로 작성해주세요."""


class OpenAIAnalyzer:
    """OpenAI Analysis fallback"""

    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        # Try multiple model options for better availability/cost
        self.models = [
            "gpt-4o-mini",  # Primary: Cheap and fast
            "gpt-4o"        # Fallback: More capable
        ]
        self.base_url = "https://api.openai.com/v1/chat/completions"

    def analyze(self, data: Dict, news: List[Dict], patterns: List[Dict], lang: str = 'ko') -> str:
        """
        Analyze macro data using OpenAI

        Args:
            data: Macro indicator data
            news: News headlines
            patterns: Historical patterns
            lang: Language ('ko' or 'en')

        Returns:
            Analysis text string
        """
        if not self.api_key:
            logger.error("OPENAI_API_KEY not found in .env")
            return "API Key Missing - Check .env file"

        prompt = self._build_prompt(data, news, patterns, lang)

        # Try each model until one works
        for model in self.models:
            try:
                logger.info(f"Trying OpenAI model: {model}")

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
                        logger.info(f"Successfully generated analysis using {model}")
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

        logger.error("All OpenAI models failed to generate analysis")
        return "Failed to generate - Check API key and quota"

    def _build_prompt(self, data: Dict, news: List[Dict], patterns: List[Dict], lang: str) -> str:
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


class MultiModelAnalyzer:
    """Multi-model macro analysis with Z.ai primary, Gemini/OpenAI fallback"""

    def __init__(self, data_dir='.'):
        self.data_dir = data_dir
        self.collector = MacroDataCollector()
        self.zai = ZAIAnalyzer()  # Try first (new Z.ai API)
        self.gemini = GeminiAnalyzer()  # Second
        self.openai = OpenAIAnalyzer()  # Final fallback

    def analyze_with_fallback(self, data: Dict, news: List[Dict], patterns: List[Dict], lang: str = 'ko') -> tuple:
        """
        Analyze with Z.ai first, fallback to Gemini, then OpenAI

        Args:
            data: Macro indicator data
            news: News headlines
            patterns: Historical patterns
            lang: Language ('ko' or 'en')

        Returns:
            tuple: (analysis_text, used_model)
        """
        # Try Z.ai first
        logger.info("Attempting Z.ai analysis...")
        result = self.zai.analyze(data, news, patterns, lang)
        if "Failed to generate" not in result and "API Key Missing" not in result and "API Authentication Failed" not in result and "API Quota Exceeded" not in result:
            logger.info("Z.ai analysis successful")
            return result, "Z.ai"

        # Fallback to Gemini
        logger.warning("Z.ai failed, trying Gemini fallback...")
        result = self.gemini.analyze(data, news, patterns, lang)
        if "Failed to generate" not in result and "API Key Missing" not in result:
            logger.info("Gemini fallback successful")
            return result, "Gemini"

        # Final fallback to OpenAI
        logger.warning("Gemini failed, trying OpenAI fallback...")
        result = self.openai.analyze(data, news, patterns, lang)
        if "Failed to generate" not in result and "API Key Missing" not in result:
            logger.info("OpenAI fallback successful")
            return result, "OpenAI"

        logger.error("All models (Z.ai, Gemini, OpenAI) failed")
        return result, "Failed"

    def run(self) -> bool:
        """
        Run the analysis pipeline with fallback logic

        Returns:
            True if successful, False otherwise
        """
        try:
            # Collect data
            logger.info("Starting macro analysis pipeline...")
            data = self.collector.get_current_macro_data()
            news = self.collector.get_macro_news()
            patterns = self.collector.get_historical_patterns()

            # Analysis with fallback
            logger.info("Generating Korean analysis...")
            analysis_ko, model_ko = self.analyze_with_fallback(data, news, patterns, 'ko')

            logger.info("Generating English analysis...")
            analysis_en, model_en = self.analyze_with_fallback(data, news, patterns, 'en')

            # Save Korean version
            output_ko = {
                'timestamp': datetime.now().isoformat(),
                'macro_indicators': data,
                'ai_analysis': analysis_ko,
                'model': model_ko
            }

            ko_path = os.path.join(self.data_dir, 'macro_analysis.json')
            with open(ko_path, 'w', encoding='utf-8') as f:
                json.dump(output_ko, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved Korean analysis to {ko_path} (Model: {model_ko})")

            # Save English version
            output_en = {
                'timestamp': datetime.now().isoformat(),
                'macro_indicators': data,
                'ai_analysis': analysis_en,
                'model': model_en
            }

            en_path = os.path.join(self.data_dir, 'macro_analysis_en.json')
            with open(en_path, 'w', encoding='utf-8') as f:
                json.dump(output_en, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved English analysis to {en_path} (Model: {model_en})")

            return True

        except Exception as e:
            logger.error(f"Error in analysis pipeline: {type(e).__name__}: {e}")
            return False


if __name__ == "__main__":
    analyzer = MultiModelAnalyzer()
    success = analyzer.run()

    if success:
        logger.info("Macro analysis completed successfully")
    else:
        logger.error("Macro analysis failed - check logs above")
