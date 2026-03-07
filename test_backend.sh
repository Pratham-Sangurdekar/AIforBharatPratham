#!/usr/bin/env bash
# test_backend.sh — Quick smoke tests for ENGAUGE backend API
# Usage:  chmod +x test_backend.sh && ./test_backend.sh

set -uo pipefail

API="http://localhost:8000/api"
PASS=0
FAIL=0

green() { printf '\033[32m%s\033[0m\n' "$*"; }
red()   { printf '\033[31m%s\033[0m\n' "$*"; }

check() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    green "  ✓ $name"
    PASS=$((PASS + 1))
  else
    red "  ✗ $name"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== ENGAUGE Backend Smoke Tests ==="
echo ""

# 1. Health / root (health endpoint is at root, not under /api)
echo "▸ Health"
check "GET  /health" curl -sf "http://localhost:8000/health"

# 2. Analyze (text-only)
echo "▸ Analyze"
ANALYZE_RESP=$(curl -sf -X POST "$API/analyze" \
  -F "text=This is a secret AI trick nobody talks about — and it changes everything" \
  -F "platform=twitter")
check "POST /api/analyze returns JSON"       test -n "$ANALYZE_RESP"
check "Response contains virality_score"     echo "$ANALYZE_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'virality_score' in d"
check "Response contains score_breakdown"    echo "$ANALYZE_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'score_breakdown' in d"
check "Response contains content_dna"        echo "$ANALYZE_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'content_dna' in d"
check "Response contains optimized_variants" echo "$ANALYZE_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'optimized_variants' in d"

# 3. Caching — second identical request should be fast and return same result
echo "▸ Caching"
ANALYZE_RESP2=$(curl -sf -X POST "$API/analyze" \
  -F "text=This is a secret AI trick nobody talks about — and it changes everything" \
  -F "platform=twitter")
check "Cached response matches original" \
  python3 -c "
import json, sys
a=json.loads('''$ANALYZE_RESP''')
b=json.loads('''$ANALYZE_RESP2''')
assert a.get('virality_score') == b.get('virality_score'), 'Scores differ'
"

# 4. History
echo "▸ History"
check "GET  /api/history"                    curl -sf "$API/history"
check "GET  /api/history?sort=score_desc"    curl -sf "$API/history?sort=score_desc"

# 5. Metrics
echo "▸ Metrics"
METRICS=$(curl -sf "$API/metrics")
check "GET  /api/metrics returns JSON"       test -n "$METRICS"
check "Metrics contains average_score"       echo "$METRICS" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'average_score' in d"
check "Metrics contains score_distribution"  echo "$METRICS" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'score_distribution' in d"

# 6. Trends
echo "▸ Trends"
check "GET  /api/trends"                     curl -sf "$API/trends"

# 7. Profile
echo "▸ Profile"
check "GET  /api/profile"                    curl -sf "$API/profile"

# 8. Gallery
echo "▸ Gallery"
check "GET  /api/gallery"                    curl -sf "$API/gallery"

echo ""
echo "==================================="
echo "  Results:  $PASS passed, $FAIL failed"
echo "==================================="
[ "$FAIL" -eq 0 ] && green "All tests passed!" || red "Some tests failed."
exit "$FAIL"
