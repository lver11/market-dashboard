#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Stock Summary Generator
Generates investment summaries using OpenAI GPT-4o Mini
"""

import os
import json
import logging
import time
import requests
import pandas as pd
from datetime import datetime
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsCollector:
    def get_news(self, ticker: str):
        # Simplified for brevity - uses Google News RSS
        news = []
        try:
            import xml.etree.ElementTree as ET
            url = f"https://news.google.com/rss/search?q={ticker}+stock&hl=en-US&gl=US&ceid=US:en"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall('.//item')[:3]:
                    news.append({'title': item.find('title').text, 'published': item.find('pubDate').text})
        except (ET.ParseError, requests.RequestException):
            pass
        return news

class ZAIAnalyzer:
    """Z.ai (Zero One) API Analyzer - Coding Plan"""
    def __init__(self):
        self.key = os.getenv('ZAI_API_KEY')
        # Z.ai Coding Plan base URL
        self.base_url = "https://api.z.ai/api/coding/paas/v4"
        self.model = "glm-4-plus"  # Z.ai's latest model
        self.min_request_interval = 2  # Minimum seconds between requests

    def generate(self, ticker, data, news, lang='ko'):
        if not self.key:
            return "No Z.ai API Key"

        news_txt = "\n".join([n['title'] for n in news]) if news else "최근 뉴스 없음"
        score_info = f"Score: {data.get('composite_score')}/100, Quant: {data.get('grade')}"

        system_prompt = "You are an expert financial analyst providing stock investment summaries."

        if lang == 'ko':
            user_prompt = f"""종목: {ticker}
정보: {score_info}
뉴스: {news_txt}
요청: 3-4문장으로 투자 의견 요약 (수급, 펀더멘털, 전략). 이모지 사용하지 말고 간결하게 작성."""
        else:
            user_prompt = f"""Stock: {ticker}
Info: {score_info}
News: {news_txt}
Req: 3-4 sentence investment summary. No emojis, be concise."""

        try:
            # Construct full URL
            url = f"{self.base_url}/chat/completions"

            headers = {
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }

            logger.info(f"Calling Z.ai API for {ticker}...")
            resp = requests.post(url, headers=headers, json=payload, timeout=30)

            if resp.status_code == 200:
                result = resp.json()
                if 'choices' in result and len(result['choices']) > 0:
                    summary = result['choices'][0]['message']['content'].strip()
                    logger.info(f"Z.ai API success for {ticker}")
                    time.sleep(self.min_request_interval)  # Rate limit protection
                    return summary
                else:
                    logger.error(f"Z.ai API unexpected response format: {result}")
                    return "API Response Format Error"
            elif resp.status_code == 429:
                logger.warning("Z.ai API rate limit reached. Waiting 5 seconds...")
                time.sleep(5)  # Wait for rate limit to reset
                # Retry once after rate limit
                resp = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
                if resp.status_code == 200:
                    result = resp.json()
                    if 'choices' in result and len(result['choices']) > 0:
                        summary = result['choices'][0]['message']['content'].strip()
                        logger.info(f"Z.ai API retry success for {ticker}")
                        time.sleep(self.min_request_interval)
                        return summary
                logger.warning("Z.ai API rate limit retry also failed")
                return "Rate Limit - Try again later"
            elif resp.status_code == 401:
                logger.error("Z.ai API authentication failed. Check API key.")
                return "API Authentication Failed"
            else:
                logger.error(f"Z.ai API error: {resp.status_code} - {resp.text}")
                return f"API Error ({resp.status_code})"

        except requests.RequestException as e:
            logger.error(f"Z.ai API request failed: {e}")
            return "Network Error"
        except (KeyError, ValueError) as e:
            logger.error(f"Z.ai API response parsing failed: {e}")
            return "Response Parsing Error"

        return "Analysis Failed"

class GeminiAnalyzer:
    """Gemini API Analyzer for stock summaries"""

    def __init__(self):
        self.key = os.getenv('GOOGLE_API_KEY')
        # Try multiple model options
        self.models = [
            "gemini-2.5-flash",  # Primary: Fast
            "gemini-2.5-pro",     # Fallback: Capable
            "gemini-1.5-flash"    # Last resort
        ]

    def generate(self, ticker, data, news, lang='ko'):
        if not self.key:
            return "No Gemini API Key"

        news_txt = "\n".join([n['title'] for n in news]) if news else "최근 뉴스 없음"
        score_info = f"Score: {data.get('composite_score')}/100, Quant: {data.get('grade')}"

        if lang == 'ko':
            user_prompt = f"""종목: {ticker}
정보: {score_info}
뉴스: {news_txt}
요청: 3-4문장으로 투자 의견 요약 (수급, 펀더멘털, 전략). 이모지 사용하지 말고 간결하게 작성."""
        else:
            user_prompt = f"""Stock: {ticker}
Info: {score_info}
News: {news_txt}
Req: 3-4 sentence investment summary. No emojis, be concise."""

        # Try each model until one works
        for model in self.models:
            try:
                logger.info(f"Trying Gemini model: {model}")

                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.key}"

                payload = {
                    "contents": [{
                        "parts": [{"text": user_prompt}]
                    }],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 2000  # Increased for longer summaries
                    }
                }

                resp = requests.post(url, json=payload, timeout=30)

                if resp.status_code == 200:
                    result = resp.json()
                    if 'candidates' in result and len(result['candidates']) > 0:
                        content = result['candidates'][0]['content']['parts'][0]['text'].strip()
                        logger.info(f"Successfully generated summary using {model}")
                        time.sleep(2)  # Rate limit protection
                        return content
                    else:
                        logger.warning(f"No candidates in response from {model}")
                        continue
                else:
                    logger.warning(f"{model} returned status {resp.status_code}: {resp.text[:200]}")
                    continue

            except requests.RequestException as e:
                logger.warning(f"Request error with {model}: {e}")
                continue
            except (KeyError, IndexError) as e:
                logger.warning(f"Response parsing error with {model}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error with {model}: {type(e).__name__}: {e}")
                continue

        logger.error("All Gemini models failed")
        return "Analysis Failed"

class OpenAIAnalyzer:
    def __init__(self):
        self.key = os.getenv('OPENAI_API_KEY')
        self.model = "gpt-4o-mini"

    def generate(self, ticker, data, news, lang='ko'):
        if not self.key:
            return "No API Key"

        news_txt = "\n".join([n['title'] for n in news])
        score_info = f"Score: {data.get('composite_score')}/100, Quant: {data.get('grade')}"

        system_prompt = "You are an expert financial analyst providing stock investment summaries."

        if lang == 'ko':
            user_prompt = f"""종목: {ticker}
정보: {score_info}
뉴스: {news_txt}
요청: 3-4문장으로 투자 의견 요약 (수급, 펀더멘털, 전략). 이모지 X."""
        else:
            user_prompt = f"""Stock: {ticker}
Info: {score_info}
News: {news_txt}
Req: 3-4 sentence investment summary. No emojis."""

        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                result = resp.json()
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content'].strip()
            elif resp.status_code == 429:
                logger.warning("OpenAI API quota exceeded. Please check your plan and billing details.")
                return "API Quota Exceeded"
            else:
                logger.error(f"OpenAI API error: {resp.status_code} - {resp.text}")
        except (requests.RequestException, KeyError, ValueError) as e:
            logger.error(f"OpenAI API request failed: {e}")

        return "Analysis Failed"

class AIStockAnalyzer:
    def __init__(self, data_dir='.'):
        self.data_dir = data_dir
        self.output = os.path.join(data_dir, 'ai_summaries.json')
        # Priority: Gemini -> Z.ai -> OpenAI
        if os.getenv('GOOGLE_API_KEY'):
            self.gen = GeminiAnalyzer()
            self.fallback1 = ZAIAnalyzer() if os.getenv('ZAI_API_KEY') else None
            self.fallback2 = OpenAIAnalyzer() if os.getenv('OPENAI_API_KEY') else None
            logger.info("Using Gemini API for analysis (with fallbacks)")
        elif os.getenv('ZAI_API_KEY'):
            self.gen = ZAIAnalyzer()
            self.fallback1 = None
            self.fallback2 = OpenAIAnalyzer() if os.getenv('OPENAI_API_KEY') else None
            logger.info("Using Z.ai API for analysis")
        else:
            self.gen = OpenAIAnalyzer()
            self.fallback1 = None
            self.fallback2 = None
            logger.info("Using OpenAI API for analysis")
        self.news = NewsCollector()

    def run(self, top_n=20):
        csv = os.path.join(self.data_dir, 'smart_money_picks_v2.csv')
        if not os.path.exists(csv):
            return

        df = pd.read_csv(csv).head(top_n)
        results = {}

        # Load existing
        if os.path.exists(self.output):
            try:
                with open(self.output, 'r', encoding='utf-8') as f:
                    results = json.load(f)
            except (UnicodeDecodeError, json.JSONDecodeError):
                logger.warning("Existing JSON file corrupted, creating new one")
                results = {}

        for _, row in tqdm(df.iterrows(), total=len(df)):
            ticker = row['ticker']
            if ticker in results and results[ticker].get('summary') != 'Analysis Failed':
                continue  # Skip if already has good summary

            news = self.news.get_news(ticker)

            # Try primary analyzer
            summary_ko = self.gen.generate(ticker, row.to_dict(), news, 'ko')
            summary_en = self.gen.generate(ticker, row.to_dict(), news, 'en')

            # If primary failed, try fallback1 (if exists)
            if 'Failed' in summary_ko or 'API' in summary_ko:
                if self.fallback1:
                    logger.warning(f"Primary failed for {ticker}, trying fallback1...")
                    summary_ko = self.fallback1.generate(ticker, row.to_dict(), news, 'ko')
                    summary_en = self.fallback1.generate(ticker, row.to_dict(), news, 'en')

            # If fallback1 also failed, try fallback2 (if exists)
            if 'Failed' in summary_ko or 'API' in summary_ko:
                if self.fallback2:
                    logger.warning(f"Fallback1 failed for {ticker}, trying fallback2...")
                    summary_ko = self.fallback2.generate(ticker, row.to_dict(), news, 'ko')
                    summary_en = self.fallback2.generate(ticker, row.to_dict(), news, 'en')

            results[ticker] = {
                'summary': summary_ko,
                'summary_ko': summary_ko,
                'summary_en': summary_en,
                'updated': datetime.now().isoformat()
            }
            time.sleep(1) # Rate limit

        with open(self.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(results)} summaries")

if __name__ == "__main__":
    AIStockAnalyzer().run()
