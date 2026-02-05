#!/usr/bin/env python3
import sys
import subprocess
import time
import argparse
import traceback

scripts = [
    ("create_us_daily_prices.py", "Data Collection", 600),
    ("analyze_volume.py", "Volume Analysis", 600),
    ("smart_money_screener_v2.py", "Screening", 600),
    ("sector_heatmap.py", "Heatmap", 300),
    ("options_flow.py", "Options", 300),    
    ("ai_summary_generator.py", "AI summaries", 1200),
    ("final_report_generator.py", "Final Report", 60),
    ("macro_analyzer.py", "Macro Analysis", 300),
    ("macro_analyzer_gpt.py", "Macro Analysis GPT", 300),
    ("economic_calendar.py", "Calendar", 300),
    ("analyze_etf_flows.py", "ETF Flows", 600)
]

def run_script(name, desc, timeout):
    print(f"🔄 Running {desc} ({name})...")
    print(f"⏱️  Timeout: {timeout}s")
    try:
        result = subprocess.run(
            [sys.executable, name],
            timeout=timeout,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ {desc} completed successfully")
        if result.stdout:
            print(f"📤 Output: {result.stdout[:200]}")
        return True
    except subprocess.TimeoutExpired as e:
        print(f"❌ {desc} TIMED OUT after {timeout}s")
        print(f"   Script: {name}")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ {desc} FAILED with exit code {e.returncode}")
        print(f"   Script: {name}")
        if e.stdout:
            print(f"   stdout: {e.stdout[-500:]}")
        if e.stderr:
            print(f"   stderr: {e.stderr[-500:]}")
        return False
    except Exception as e:
        print(f"❌ {desc} ERROR: {type(e).__name__}: {e}")
        print(f"   Script: {name}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Update all US market data")
    parser.add_argument('--quick', action='store_true',
                       help='Skip AI-intensive scripts (AI summaries, macro analysis)')
    parser.add_argument('--scripts', nargs='*',
                       help='Specific scripts to run (default: all)')
    args = parser.parse_args()

    start = time.time()
    results = {
        'success': [],
        'failed': [],
        'skipped': []
    }

    # Filter scripts based on arguments
    scripts_to_run = scripts
    if args.scripts and len(args.scripts) > 0:
        # Run only specified scripts
        scripts_to_run = [(s, d, t) for s, d, t in scripts
                          if any(arg in s for arg in args.scripts)]

    for name, desc, timeout in scripts_to_run:
        # Skip AI scripts in quick mode
        if args.quick and "AI" in desc.upper():
            print(f"⏭️  Skipping {desc} (quick mode)")
            results['skipped'].append((name, desc))
            continue

        # Skip GPT macro analysis in quick mode
        if args.quick and "GPT" in desc.upper():
            print(f"⏭️  Skipping {desc} (quick mode)")
            results['skipped'].append((name, desc))
            continue

        success = run_script(name, desc, timeout)
        if success:
            results['success'].append((name, desc))
        else:
            results['failed'].append((name, desc))

    elapsed = (time.time() - start) / 60
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY - Total time: {elapsed:.1f} minutes")
    print(f"{'='*60}")
    print(f"✅ Success: {len(results['success'])}")
    print(f"❌ Failed:  {len(results['failed'])}")
    print(f"⏭️  Skipped: {len(results['skipped'])}")

    if results['failed']:
        print(f"\n❌ Failed scripts:")
        for name, desc in results['failed']:
            print(f"   - {desc} ({name})")
        sys.exit(1)

if __name__ == "__main__":
    main()
