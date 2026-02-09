#!/bin/bash
echo "🧪 API Testing Report - DashBoard"
echo "=================================="
echo ""

# Test all endpoints (corrected based on flask_app.py)
endpoints=(
  "/"                                     # Main page
  "/api/us/portfolio"                     # Portfolio endpoint
  "/api/us/smart-money"                    # Smart Money Screener
  "/api/us/etf-flows"                     # ETF Flows
  "/api/us/stock-chart/AAPL"              # Stock Chart (with sample ticker)
  "/api/us/sector-heatmap"                 # Sector Heatmap
  "/api/us/options-flow"                    # Options Flow
  "/api/us/macro-analysis"                 # Macro Analysis
  "/api/us/ai-summary/FITB"               # AI Summary (with existing ticker)
  "/api/us/technical-indicators/AAPL"       # Technical Indicators (with sample ticker)
  "/api/us/calendar"                        # Economic Calendar
  "/api/us/indices"                        # Market Indices
  "/api/us/history-dates"                   # History Dates (will return empty)
  # "/api/us/history/2026-02-04"            # History Data (disabled - no history directory)
)

passed=0
failed=0
errors=()

for endpoint in "${endpoints[@]}"; do
  echo "Testing: $endpoint"
  response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 "http://localhost:5001$endpoint")

  if [ "$response" = "200" ]; then
    echo "  ✅ PASS (HTTP $response)"
    ((passed++))
  else
    echo "  ❌ FAIL (HTTP $response)"
    ((failed++))
    errors+=("$endpoint")
  fi
  echo ""
done

echo "=================================="
echo "Results: $passed passed, $failed failed"
echo "Total: $((passed + failed)) tests"

if [ $failed -gt 0 ]; then
  echo ""
  echo "Failed endpoints:"
  for err in "${errors[@]}"; do
    echo "  - $err"
  done
  echo ""
  echo "Checking server logs for errors..."
  tail -20 server.log 2>/dev/null || echo "No server.log found"
  exit 1
else
  echo ""
  echo "🎉 All tests passed!"
  exit 0
fi
