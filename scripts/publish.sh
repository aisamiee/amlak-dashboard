#!/bin/zsh
# Publish the dashboard online: encrypt app/data.json into docs/ and push to GitHub (Pages serves docs/).
#   scripts/publish.sh ["commit message"]
set -e
cd "$(dirname "$0")/.."
.venv/bin/python -I scripts/build_site.py
step=$(.venv/bin/python -I -c "import json;m=json.load(open('app/data.json'))['meta'];print(m['last_step'])")
msg=${1:-"Update dashboard data: stage $step"}
git add -A
if git diff --cached --quiet; then echo "nothing to publish"; exit 0; fi
git commit -q -m "$msg" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push -q origin main
echo "published: https://aisamiee.github.io/amlak-dashboard/ (Pages rebuild takes ~1 min)"
