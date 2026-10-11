#!/bin/zsh
# Refresh the auction dashboard.
#   scripts/update.sh            fetch new stages + rebuild everything
#   scripts/update.sh build      rebuild only (after editing locations.py / market.py / valuation.py / coords_manual.json)
# Needs an Iranian IP for amlak.razavi.ir (v2rayN rules: domain:razavi.ir, regexp:.*\.ir$, geoip:ir -> Direct).
set -e
cd "$(dirname "$0")/.."
py() { .venv/bin/python -I "$@"; }

if [[ "$1" != "build" ]]; then
  last=$(ls data/raw/s*_p01.html 2>/dev/null | sed -E 's/.*s([0-9]+)_p01.html/\1/' | sort -n | tail -1)
  from=$(( ${last:-4} > 3 ? ${last:-4} - 3 : 1 ))      # re-read the last few stages: winners are published late
  echo "== scraping stages >= $from (last stored: ${last:-none})"
  node scripts/scrape.js data/raw $from
  echo "== parsing"
  py scripts/parse.py data/raw data
  py scripts/track.py
  py scripts/img_urls.py > data/img_urls_new.txt
  n=$(wc -l < data/img_urls_new.txt | tr -d ' ')
  if [[ "$n" != "0" ]]; then echo "== downloading $n sketches"; node scripts/fetch_imgs.js data/img data/img_urls_new.txt; fi
else
  py scripts/track.py
fi

echo "== valuation"
py scripts/valuation.py
py scripts/report_data.py
echo "== sketch coordinates"
py scripts/kroki_coords.py extract
py scripts/kroki_coords.py read
py scripts/geo.py
echo "== dashboard data"
py scripts/build_app.py
echo
py scripts/review.py
