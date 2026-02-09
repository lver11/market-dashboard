# Z.ai API Integration Guide

**Date:** 2026-02-06
**Status:** ✅ Integration Complete | ⚠️ Account Recharge Required

## Overview

Z.ai (智谱AI / Zero One) API has been successfully integrated as the primary AI analysis provider for the US Market Dashboard.

## Current Status

### API Configuration
- ✅ **API Key**: Valid and configured in `.env`
- ✅ **Integration**: Complete
- ⚠️ **Account Status**: **Insufficient balance** (余额不足)

### Error Message
```
Status: 429
Response: {"error":{"code":"1113","message":"余额不足或无可用资源包,请充值。"}}
```

**Translation**: "Insufficient balance or no available resource package. Please recharge."

## How to Recharge Z.ai Account

1. **Visit Z.ai Platform**
   - URL: https://open.bigmodel.cn/
   - Login with your account

2. **Navigate to Billing**
   - Look for "充值" (Recharge) or "账户余额" (Account Balance)
   - Select a pricing plan that fits your needs

3. **Recharge Options**
   - Pay-as-you-go options available
   - Monthly subscriptions typically offer better rates
   - Various payment methods supported (Alipay, WeChat Pay, etc.)

4. **After Recharge**
   - API will work immediately
   - No code changes needed
   - Scripts will automatically use Z.ai as primary API

## API Details

### Endpoint
```
https://open.bigmodel.cn/api/paas/v4/chat/completions
```

### Models
- **Primary**: `glm-4-plus` (Latest, most capable)
- **Fallback**: `glm-4-0520` (Stable version)

### Pricing (Approximate)
- Check current pricing at: https://open.bigmodel.cn/#/price
- Generally competitive with OpenAI pricing
- May offer better rates for Chinese language processing

## Configuration

### .env File
```bash
# Z.ai API Key for AI Analysis
ZAI_API_KEY=d0298e340b9b40c790a9e6c7160b367c.LCdGc3DPrg7Gh30J
```

### Fallback Chain
The system uses this priority order:
1. **Z.ai** (Primary) - Currently needs recharge
2. **Gemini** (Secondary) - Currently at quota limit
3. **OpenAI** (Tertiary) - Currently at quota limit

## Usage

### Generate AI Stock Summaries
```bash
cd us_market
python ai_summary_generator.py
```

### Generate Macro Analysis
```bash
cd us_market
python macro_analyzer.py
```

Both scripts will automatically use Z.ai when the account has sufficient balance.

## Benefits of Z.ai

### Advantages
- ✅ **Cost Effective**: Competitive pricing, especially for Chinese language
- ✅ **Fast Response**: Low latency API endpoints
- ✅ **OpenAI Compatible**: Easy integration with existing code
- ✅ **Good for Korean**: Handles Korean language well

### Model Capabilities
- Strong financial analysis capabilities
- Good at summarizing market data
- Supports both Korean and English
- Fast generation speed

## Troubleshooting

### Error: "余额不足" (Insufficient Balance)
**Solution**: Recharge your account at https://open.bigmodel.cn/

### Error: "API Authentication Failed"
**Solution**: Check that `ZAI_API_KEY` in `.env` is correct

### Error: 429 Status Code
**Solution**: API rate limit or quota exceeded. Wait or upgrade plan

## Technical Implementation

### Files Modified
1. `us_market/ai_summary_generator.py`
   - Added `ZAIAnalyzer` class
   - Replaced `OpenAIAnalyzer` with `ZAIAnalyzer` in `AIStockAnalyzer`

2. `us_market/macro_analyzer.py`
   - Added `ZAIAnalyzer` class for macro analysis
   - Updated `MultiModelAnalyzer` to try Z.ai first
   - Fixed quota detection bug

### Code Example
```python
class ZAIAnalyzer:
    def __init__(self):
        self.key = os.getenv('ZAI_API_KEY')
        self.base_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        self.model = "glm-4-plus"

    def generate(self, ticker, data, news, lang='ko'):
        # Implementation details...
```

## Next Steps

1. **Recharge Z.ai Account** ⭐ **REQUIRED**
   - Visit https://open.bigmodel.cn/
   - Add balance to your account
   - Start using AI analysis immediately

2. **Test Integration**
   ```bash
   cd us_market
   python ai_summary_generator.py
   python macro_analyzer.py
   ```

3. **Verify Results**
   - Check `us_market/ai_summaries.json`
   - Check `us_market/macro_analysis.json`
   - View in dashboard at http://127.0.0.1:5001

## Alternative Solutions

If you prefer not to recharge Z.ai:

### Option 1: Use OpenAI API
- Recharge OpenAI account: https://platform.openai.com/
- Ensure `OPENAI_API_KEY` in `.env` is valid

### Option 2: Use Gemini API
- Check Google API quota: https://console.cloud.google.com/
- Ensure `GOOGLE_API_KEY` in `.env` is valid

### Option 3: Hybrid Approach
- Use different APIs for different features
- Configure fallback order in code
- Monitor usage and costs

## Support

### Z.ai Documentation
- API Docs: https://open.bigmodel.cn/dev/api
- Pricing: https://open.bigmodel.cn/#/price
- Support: Available on their platform

### Project Documentation
- GitHub: https://github.com/taewook486/DashBoard
- Issues: Report problems via GitHub Issues

## Summary

✅ **Integration**: Complete
⚠️ **Action Required**: Recharge Z.ai account
🎯 **Result**: Full AI analysis capabilities after recharge

Once you recharge your Z.ai account, the AI analysis features will work immediately without any code changes!
