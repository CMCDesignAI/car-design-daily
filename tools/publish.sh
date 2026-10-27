#!/usr/bin/env bash
# Daily publish: rebuild all pages (car + AI), commit, push to main → GitHub Pages redeploys.
# Usage: ./tools/publish.sh "Issue 002 · 2026-10-09"
set -euo pipefail
cd "$(dirname "$0")/.."
SITE_URL="$(cat .site-url)"
python3 tools/build.py --site-url "$SITE_URL"
python3 tools/build_ai.py --site-url "$SITE_URL"
python3 tools/check_ai_img.py   # stops publish if any AI img src points to a missing file
git add -A
git commit -m "${1:-Publish $(date -u +%F)}" || echo "nothing to commit"
git pull --rebase origin main
git push origin main
echo "Pushed. Verify in ~1 min: $SITE_URL/  and  $SITE_URL/ai/"
