---
name: update-auction
description: Refresh the local Astan Quds (amlak.razavi.ir) auction dashboard with the newest stages and winners. Use when the user says «به‌روز کن», «مزایده را به‌روز کن», «آپدیت کن» or asks for the latest auction stage.
---

# Update the auction dashboard

Project: `~/Desktop/PROJECT/amlak`. Read `HANDOFF.md` first (sections 2, 3 and 10). Reply to the user in Persian.

## 1. Fetch and rebuild
1. Run `scripts/update.sh > data/update_last.log 2>&1` in the background (5–10 min). It re-scrapes the last 3
   stored stages plus any new ones (winners are published late), parses, tracks lots, downloads new sketches,
   values every lot, reads plot-centre UTM coordinates from the sketches, builds `app/data.json`, and ends with
   the `scripts/review.py` report.
2. The site only answers an Iranian IP through a real browser (Playwright + local Chromium). If scraping fails
   with 403/timeouts, ask the user to check that v2rayN is running with Direct rules for `domain:razavi.ir`,
   `regexp:.*\.ir$`, `geoip:ir`. Never solve the ArvanCloud challenge by hand or forge cookies. Never ask the
   user to turn the VPN off completely.

## 2. Resolve the TODO list printed by review.py (active lots only)
- UNKNOWN LOCATION: add a regex rule to `RULES` and an entry to `LOC` in `scripts/locations.py`
  (scope city/edge/town/out, district, default floors).
- NO MARKET PRICE: look up new-build apartment asking prices (built 1401+) and land prices for the
  neighbourhood on Divar (browser pane; city slugs mashhad, torghabeh, shandiz, golbahar), add to `P_NEW` /
  `LAND_MKT` in `scripts/market.py` with the source text and confidence.
- SKETCH NOT REVIEWED: open the sketch (`data/img/korokiImage<kid>.*`; shrink with PIL to ~1400 px wide before
  reading), read density zone (تراکم کم/متوسط/زیاد، گونه), printed FAR, frontage, street widths, corner/two-sided,
  shape, power-line or other easements. Add a `PLOT[<kid>]` entry in `scripts/valuation.py`
  (floors over pilotis, far, shape, adj, risk, cost_mult, notes in Persian). Mashhad rules of thumb are in
  HANDOFF.md section 5.
- NO EXACT POSITION: crop the line «مختصات مرکز ملک  x:… y:… zone:40» from the sketch and read it; add
  `"<listing id>": [x, y]` to `data/coords_manual.json`. Sketches in the new designs (orange/maroon posters,
  Mahdieh "X1 Y1 ----") carry no coordinates: leave them approximate.
Then run `scripts/update.sh build` (no scraping) and re-read the review output.

## 3. Make sure the dashboard is up
`curl -s http://127.0.0.1:8765/api/version` — if it fails, start it with Bash in the background:
`.venv/bin/python -I scripts/serve.py 8765` (the preview_start launcher hangs on macOS folder permission; use Bash).
Open pages already show a banner «داده‌های تازهٔ مزایده آماده است». The user opens it with `start.command`.

## 4. Publish the online copy
Run `scripts/publish.sh` (it encrypts `app/data.json` into `docs/data.enc` with the password in
`.secrets/site_password.txt`, commits and pushes to github.com/aisamiee/amlak-dashboard; GitHub Pages serves
`docs/` at https://aisamiee.github.io/amlak-dashboard/ about a minute later). Never commit `data/`, `output/`,
`app/data.json`, `app/state/`, `.secrets/` or `HANDOFF.md` (all git-ignored: they hold bid caps, notes and the
password). Never print the site password in chat; point the user to `.secrets/site_password.txt`. To change it:
`.venv/bin/python -I scripts/build_site.py --new-password`, then publish (every device must log in again).

## 5. Report (Persian, short)
- Stage number and date, how many new lots, repriced lots, winners of the previous stage and their premium.
- Top active lots with cap price (سقف پیشنهاد), owner real return and builder margin; any verdict changes.
- Watchlist: read `app/state/user.json` (keys are asset keys = lowest listing id); report price/status changes
  of starred lots and compare with the user's own max (`myMax`, million toman/m²).
- What you added (new locations, market prices, sketch facts, coordinates) and anything still approximate.
- Update the dated line in HANDOFF.md section 10.

Never store or show winner names (only حقیقی/حقوقی). Money in the data is toman; raw site prices are rial.
