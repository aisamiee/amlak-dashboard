"""After an update: what changed, and which active lots still need a human (Claude) look.

  .venv/bin/python -I scripts/review.py
Prints the stage diff, changes since the previous snapshot, the watchlist (app/state/user.json) and a TODO list:
  - address not matched to a location           -> add a rule in scripts/locations.py (RULES + LOC)
  - location without a new-build price           -> add P_NEW (and LAND_MKT) in scripts/market.py
  - sketch not reviewed (default floors used)    -> read the sketch, add a PLOT entry in scripts/valuation.py
  - no exact position                            -> read "x: y:" on the sketch, add to data/coords_manual.json
"""
import json
import os
import sys

sys.path.insert(0, 'scripts')
from market import P_NEW  # noqa: E402

D = json.load(open('app/data.json', encoding='utf-8'))
by_k = {a['k']: a for a in D['assets']}
by_id = {i: a for a in D['assets'] for i in a['ids'] if i}
m, sd = D['meta'], D['stage_diff']
VC = {'buy': 'مناسب مشارکت', 'thin': 'کم‌سود', 'hold': 'فقط خرید زمین', 'avoid': 'توصیه نمی‌شود', 'na': 'ارزیابی نشده'}


def name(a):
    return f"{(D['locs'].get(a['loc']) or {}).get('short') or a['loc'] or a['address']} قطعه {a['qate']} ({round(a['area'] or 0)} م)"


def mil(x):
    return f'{x / 1e6:,.1f}' if x else '—'


print(f"== stage {m['last_step']} ({m['last_date']}), previous {m['prev_step']}; data updated {m['updated']}")
print(f"new lots {len(sd['new'])}, carried {len(sd['carried'])}, repriced {len(sd['repriced'])}, "
      f"sold in prev stage {len(sd['sold_prev'])}, left without winner {len(sd['left_prev'])}")
act = [a for a in D['assets'] if a['status'] == 'active']
print('active by verdict:', {VC[v]: sum(1 for a in act if a['vc'] == v) for v in VC})
best = sorted((a for a in act if a.get('score') is not None and not a.get('anomaly')), key=lambda a: -a['score'])[:8]
print('\n-- top active lots')
for a in best:
    v = a['v']
    print(f"  {a['score']:5.1f}  {name(a)}  base {mil(a['rl'])}  cap {mil(v['max_bid_partner'])}  "
          f"owner {v['owner_real_ret_eff']:.0%}  builder {v['builder_margin']:.0%}  [{VC[a['vc']]}]")

ch = D.get('changes')
if ch:
    print(f"\n-- changes since {ch['since']} (stage {ch['since_step']}): {len(ch['items'])}")
    for c in ch['items'][:40]:
        a = by_k.get(c['k'])
        print(f"  {c['t']:8s} {name(a)}  {c.get('frm', '')} -> {c.get('to', '')}")

st_path = 'app/state/user.json'
if os.path.exists(st_path):
    items = json.load(open(st_path, encoding='utf-8')).get('items', {})
    if items:
        print('\n-- watchlist')
        for k, w in items.items():
            a = by_k.get(int(k)) or by_id.get(int(k))
            if not a:
                print('  (missing asset)', k); continue
            snap = w.get('snap') or {}
            print(f"  {name(a)}: {a['status']} base {mil(a['rl'])} (at star {mil(snap.get('rl'))}) "
                  f"cap {mil((a['v'] or {}).get('max_bid_partner'))} my-max {w.get('myMax')} note: {(w.get('note') or '')[:60]}")

MANUAL = json.load(open('data/coords_manual.json')) if os.path.exists('data/coords_manual.json') else {}
print('\n-- TODO for active lots')
todo = 0
for a in act:
    need = []
    if not a['loc']:
        need.append('UNKNOWN LOCATION (locations.py)')
    elif a['loc'] not in P_NEW and a['kind'] in ('land', 'large_parcel'):
        need.append('NO MARKET PRICE (market.py P_NEW/LAND_MKT)')
    if a['v'] and not a['v'].get('in_plot'):
        need.append('SKETCH NOT REVIEWED (valuation.py PLOT)')
    no_coords_on_sketch = any(str(i) in MANUAL and MANUAL[str(i)] is None for i in a['ids'] if i)
    if (not a.get('geo') or a['geo'].get('approx')) and not no_coords_on_sketch:
        need.append('NO EXACT POSITION (coords_manual.json)')
    if need:
        todo += 1
        print(f"  k={a['k']} kid={a['kid']} {name(a)} [{a['address']}] -> {'; '.join(need)}  img: data/img/korokiImage{a['kid']}.*")
print(f'  {todo} lots need attention')
