#!/usr/bin/env python3
"""
Test script to verify Gemini API is working for stock summaries
"""
import os
import json
import requests
import time
from datetime import datetime

def load_config():
    """Load API configuration from environment or config file"""
    # First try environment variables
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')

    if not api_key:
        # Try to load from config file
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    api_key = config.get('gemini_api_key') or config.get('GEMINI_API_KEY') or config.get('GOOGLE_API_KEY')
            except Exception as e:
                print(f"Error loading config file: {e}")

        # Try .env file
        if not api_key:
            env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
            if os.path.exists(env_path):
                try:
                    with open(env_path, 'r') as f:
                        for line in f:
                            if line.startswith('GOOGLE_API_KEY='):
                                api_key = line.strip().split('=', 1)[1]
                                break
                except Exception as e:
                    print(f"Error loading .env file: {e}")

    return api_key

def test_gemini_api(prompt, model="gemini-2.5-flash"):
    """Test Gemini API with a given prompt"""
    api_key = load_config()

    if not api_key:
        return {
            'success': False,
            'error': 'API key not found',
            'details': 'Set GEMINI_API_KEY environment variable or configure in config.json'
        }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    headers = {
        'Content-Type': 'application/json',
    }

    data = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }

    start_time = time.time()

    try:
        response = requests.post(url, headers=headers, json=data)
        response_time = time.time() - start_time

        if response.status_code == 200:
            result = response.json()

            # Extract text from response
            if 'candidates' in result and len(result['candidates']) > 0:
                text = result['candidates'][0].get('content', {}).get('parts', [{}])[0].get('text', '')
                return {
                    'success': True,
                    'model': model,
                    'response_time': response_time,
                    'tokens_used': result.get('usageMetadata', {}).get('totalTokenCount', 0),
                    'text': text.strip(),
                    'full_response': result
                }
            else:
                return {
                    'success': False,
                    'error': 'No candidates in response',
                    'details': result,
                    'response_time': response_time
                }
        else:
            error_info = response.json()
            return {
                'success': False,
                'error': f'API Error ({response.status_code})',
                'details': error_info.get('error', {}).get('message', 'Unknown error'),
                'response_time': response_time,
                'status_code': response.status_code
            }

    except Exception as e:
        response_time = time.time() - start_time
        return {
            'success': False,
            'error': 'Connection error',
            'details': str(e),
            'response_time': response_time
        }

def main():
    """Main test function"""
    print("=" * 60)
    print("Gemini API Test for Stock Summaries")
    print("=" * 60)
    print(f"Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Test prompt
    test_prompt = "Generate investment summary for AAPL (Apple Inc) for 2025. Include key financial metrics, recent performance, and investment outlook. Keep it concise and factual."

    # Test both models
    models = ["gemini-2.5-flash", "gemini-2.5-pro"]

    results = {}

    for model in models:
        print(f"\n🔬 Testing {model}...")
        print("-" * 40)

        result = test_gemini_api(test_prompt, model)
        results[model] = result

        if result['success']:
            print(f"✅ Success! Response time: {result['response_time']:.2f}s")
            print(f"📊 Tokens used: {result['tokens_used']}")
            print("\n📝 Generated summary:")
            print("-" * 40)
            print(result['text'][:500] + "..." if len(result['text']) > 500 else result['text'])
        else:
            print(f"❌ Failed!")
            print(f"   Error: {result['error']}")
            print(f"   Details: {result['details']}")

        print("\n" + "=" * 60)

    # Summary report
    print("\n📋 Test Summary Report")
    print("=" * 60)

    successful_tests = sum(1 for r in results.values() if r['success'])
    total_tests = len(results)

    print(f"Total tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")

    for model, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"\n{model}: {status}")
        if not result['success']:
            print(f"   Error Code: {result.get('status_code', 'N/A')}")
            print(f"   Error Message: {result['error']}")
            print(f"   Details: {result['details']}")

    # Save detailed results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"gemini_test_results_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'test_prompt': test_prompt,
            'results': results
        }, f, indent=2)

    print(f"\n📁 Detailed results saved to: {output_file}")

    return successful_tests == total_tests

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)