"""Build the local dashboard: app/data.json, sketch thumbnails (app/img) and an update snapshot.

Inputs : output/report_data.json, data/assets.json, data/valuation.json, scripts/market.py
Outputs: app/data.json, app/img/k<sketch-id>.webp, data/snapshots/<date>_s<step>.json
Run after report_data.py. Money in toman.
"""
import datetime
import glob
import hashlib
import json
import os
import re
import statistics as st
import sys

from PIL import Image

sys.path.insert(0, 'scripts')
import market as M  # noqa: E402
from jalali import FA_DIGITS, MONTHS, today_fa, today_str  # noqa: E402
from locations import LOC  # noqa: E402

R = json.load(open('output/report_data.json', encoding='utf-8'))
RAW = {a['asset']: a for a in json.load(open('data/assets.json', encoding='utf-8'))}
VAL = {v['asset']: v for v in json.load(open('data/valuation.json', encoding='utf-8'))}
GEO = json.load(open('data/geo.json')) if os.path.exists('data/geo.json') else {}     # from scripts/geo.py
LAST = R['last_step']
STEPS = sorted(int(s) for s in R['stage_dates'])
PREV = max([s for s in STEPS if s < LAST], default=None)
IMG_SRC, IMG_OUT, SNAP_DIR = 'data/img', 'app/img', 'data/snapshots'
os.makedirs(IMG_OUT, exist_ok=True)
os.makedirs(SNAP_DIR, exist_ok=True)


def short(name):
    return re.split(r'\s*\(', name or '')[0].strip()


def stage_date(s):
    """'12 مهر 05' -> '۱۲ مهر ۱۴۰۵'"""
    d = R['stage_dates'].get(str(s))
    if not d:
        return None
    m = re.match(r'(\d+)\s+(\S+)\s+(\d+)', d)
    return f'{int(m.group(1))} {m.group(2)} 14{m.group(3)}'.translate(FA_DIGITS) if m else d


def kid_of(url):
    m = re.search(r'korokiImage(\d+)', url or '')
    return int(m.group(1)) if m else None


VCLASS = [('مناسب مشارکت', 'buy'), ('مشارکت شدنی', 'thin'), ('ساخت توجیه ندارد', 'hold'), ('توصیه نمی‌شود', 'avoid')]


def vclass(v):
    for pre, c in VCLASS:
        if v and v.startswith(pre):
            return c
    return None


# ---------------- sketch thumbnails ----------------
def thumb(kid):
    if not kid:
        return None
    out = os.path.join(IMG_OUT, f'k{kid}.webp')
    if os.path.exists(out):
        return f'img/k{kid}.webp'
    src = next(iter(glob.glob(os.path.join(IMG_SRC, f'korokiImage{kid}.*'))), None)
    if not src:
        return None
    try:
        im = Image.open(src)
        im = im.convert('L') if im.mode in ('L', 'LA', '1', 'P') else im.convert('RGB')
        im.thumbnail((1500, 1500))
        im.save(out, 'WEBP', quality=74, method=5)
        return f'img/k{kid}.webp'
    except Exception as e:  # unreadable source image
        print('thumb fail', kid, e)
        return None


# ---------------- asset rows ----------------
VAL_KEYS = ('floors', 'far', 'occupancy', 'footprint_m2', 'gross_m2', 'net_m2', 'units', 'unit_size', 'basement_m2',
            'parking_ground', 'p_new', 'p_src', 'p_conf', 'sale_ppm', 'gdv', 'hard_ppm', 'build_cost',
            'build_cost_per_net', 'land_cost', 'total_cost', 'profit', 'margin', 'annual_return', 'rlv_ppm',
            'safety', 'margin_stress', 'margin_upside', 'breakeven_ppm', 'owner_m2', 'builder_m2', 'owner_units',
            'owner_value', 'owner_cost_eff', 'owner_ret_eff', 'owner_cost_per_m2', 'builder_margin',
            'owner_fair_share', 'owner_real_share', 'owner_real_value', 'owner_real_ret_eff', 'owner_real_ann_eff',
            'max_bid_partner', 'land_mkt', 'land_mkt_src', 'land_mkt_conf', 'vs_land_mkt', 'plot_notes', 'basis',
            'exp_premium', 'land_rate_toman', 'facts', 'in_plot', 'risk_extra',
            'x_floors', 'x_net_m2', 'x_owner_real_ret_eff', 'x_builder_margin', 'x_max_bid_partner', 'x_margin',
            'opt_builder_margin', 'pes_builder_margin', 'opt_owner_real_ret_eff', 'pes_owner_real_ret_eff',
            'opt_max_bid_partner', 'pes_max_bid_partner', 'opt_margin', 'pes_margin')

def asset_key(raw):
    """Stable key across rebuilds: the lowest listing id (sketch image id) of the asset."""
    ids = [i for i in raw['ids'] if i is not None]
    if ids:
        return min(ids)
    sig = f"{raw['loc']}|{raw['qate']}|{raw['block']}|{round(raw['area'] or 0)}|{raw['first_step']}"
    return -int(hashlib.sha1(sig.encode()).hexdigest()[:7], 16)       # no image id: negative synthetic key


assets, key_of = [], {}
for r in R['assets']:
    raw = RAW[r['asset']]
    k = asset_key(raw)
    key_of[r['asset']] = k
    v = VAL.get(r['asset'])
    kid = (v or {}).get('koroki_id') or kid_of(r['koroki'])
    hist = [[h['step'], h['rate'] / 10 if h['rate'] else None, h['win'] / 10 if h['win'] else None, h['prem']]
            for h in raw['history']]
    row = dict(
        k=k, ids=raw['ids'], loc=r['loc'], scope=r['scope'], kind=r['kind'], seg=r['segment'],
        qate=r['qate'], block=r['block'], area=r['area'], karbari=r['karbari'], address=r['address'],
        status=r['status'], first=r['first_step'], last=r['last_step'], n=r['n_listings'], steps=r['steps'],
        rf=r['rate_first'], rl=r['rate_last'], rch=r['rate_change'], total=r['total_last'],
        wstep=r['win_step'], wprice=r['win_price'], wprem=r['win_premium'], buyer=r['buyer_type'],
        hist=hist, kid=kid, img=thumb(kid), kroki=r['koroki'], notice=r['notice'],
        verdict=r.get('verdict'), vc=vclass(r.get('verdict')), score=r.get('score'), anomaly=r.get('anomaly'),
        paper_gain=r.get('paper_gain'), value_gap=r.get('value_gap'), paid_ref=r.get('paid_ref'),
        loc_level_now=r.get('loc_level_now'), garden_mkt=r.get('garden_mkt'), vs_garden_mkt=r.get('vs_garden_mkt'),
        v={kk: v.get(kk) for kk in VAL_KEYS} if v else None,
        geo=GEO.get(str(r['asset'])),
    )
    if row['status'] == 'active' and not row['vc']:
        row['vc'] = 'na'
    assets.append(row)
by_k = {a['k']: a for a in assets}

# ---------------- what changed between the last two stages ----------------
def rate_at(a, s):
    return next((h[1] for h in a['hist'] if h[0] == s), None)


stage_diff = dict(step=LAST, prev=PREV, new=[], repriced=[], carried=[], sold_prev=[], left_prev=[])
for a in assets:
    if LAST in a['steps']:
        if a['first'] == LAST:
            stage_diff['new'].append(a['k'])
        else:
            stage_diff['carried'].append(a['k'])
            before = [h for h in a['hist'] if h[0] < LAST and h[1]]
            now = rate_at(a, LAST)
            if before and now and abs(now / before[-1][1] - 1) > 0.001:
                stage_diff['repriced'].append(dict(k=a['k'], frm=before[-1][1], to=now, step=before[-1][0]))
    if PREV and PREV in a['steps'] and LAST not in a['steps']:
        won = next((h for h in a['hist'] if h[0] == PREV and h[2]), None)
        if won:
            stage_diff['sold_prev'].append(dict(k=a['k'], price=won[2], prem=won[3]))
        else:
            stage_diff['left_prev'].append(a['k'])

# ---------------- snapshot + changes since the previous update ----------------
snap = {str(a['k']): dict(st=a['status'], rl=a['rl'], wp=a['wprice'], vc=a['vc'],
                          mb=(a['v'] or {}).get('max_bid_partner'), last=a['last']) for a in assets}
snap_hash = hashlib.sha1(json.dumps(snap, sort_keys=True).encode()).hexdigest()
prev_snaps = []
for f in sorted(glob.glob(os.path.join(SNAP_DIR, '*.json'))):
    try:
        prev_snaps.append((f, json.load(open(f, encoding='utf-8'))))
    except Exception:
        pass
now = datetime.datetime.now()
# snapshots written earlier today for the same stage belong to this update session (e.g. before the sketches
# were reviewed): they are replaced, never used as the baseline
same_session = [f for f, s in prev_snaps if s['meta'].get('step') == LAST and s['meta'].get('date') == today_fa(now)]
prev_snaps = [(f, s) for f, s in prev_snaps if f not in same_session]
baseline = next((s for f, s in reversed(prev_snaps) if s['meta']['hash'] != snap_hash), None)
if not prev_snaps or prev_snaps[-1][1]['meta']['hash'] != snap_hash:
    for f in same_session:
        os.remove(f)
    fn = os.path.join(SNAP_DIR, f"{today_str(now).replace('/', '-')}_{now:%H%M}_s{LAST:02d}.json")
    json.dump(dict(meta=dict(hash=snap_hash, date=today_fa(now), step=LAST, at=now.isoformat(timespec='minutes')),
                   assets=snap), open(fn, 'w', encoding='utf-8'), ensure_ascii=False)

changes = None
if baseline:
    old, ch = baseline['assets'], []
    for k, s in snap.items():
        o = old.get(k)
        if o is None:
            ch.append(dict(k=int(k), t='new'))
            continue
        if o['st'] != s['st']:
            ch.append(dict(k=int(k), t='status', frm=o['st'], to=s['st'], price=s['wp']))
        elif s['st'] == 'active' and o['rl'] and s['rl'] and abs(s['rl'] / o['rl'] - 1) > 0.001:
            ch.append(dict(k=int(k), t='price', frm=o['rl'], to=s['rl']))
        if o.get('vc') and s.get('vc') and o['vc'] != s['vc']:
            ch.append(dict(k=int(k), t='verdict', frm=o['vc'], to=s['vc']))
        if o.get('mb') and s.get('mb') and s['st'] == 'active' and abs(s['mb'] / o['mb'] - 1) > 0.02:
            ch.append(dict(k=int(k), t='maxbid', frm=o['mb'], to=s['mb']))
    changes = dict(since=baseline['meta']['date'], since_step=baseline['meta']['step'], items=ch)

# ---------------- locations, series, stages ----------------
prem_by_loc = {}
for a in RAW.values():
    if a.get('win_premium') is not None:
        prem_by_loc.setdefault(a['loc'], []).append(a['win_premium'])
exp_prem = {k: sorted(v)[len(v) // 2] for k, v in prem_by_loc.items() if len(v) >= 3}
locs = {}
for key, meta in LOC.items():
    p = M.P_NEW.get(key)
    lm = M.LAND_MKT.get(key)
    gm = M.GARDEN_MKT.get(key)
    locs[key] = dict(name=meta.get('name'), short=short(meta.get('name')), district=meta.get('district'),
                     scope=meta.get('scope'), floors=meta.get('floors'),
                     p_new=p[0] if p else None, p_src=p[1] if p else None, p_conf=p[2] if p else None,
                     land=lm[0] if lm else None, land_src=lm[1] if lm else None, land_conf=lm[2] if lm else None,
                     garden=gm[0] if gm else None, garden_src=gm[1] if gm else None,
                     exp_prem=exp_prem.get(key, 0.03))
loc_rows = R['locations']
for lr in loc_rows:
    lr['short'] = short(lr['name'])
stages = R['stages']
for s in stages:
    s['date_fa'] = stage_date(s['step'])

params = dict(
    OCCUPANCY=M.OCCUPANCY, NET_TO_GROSS=M.NET_TO_GROSS, PILOTI_COST_FACTOR=M.PILOTI_COST_FACTOR,
    PERMIT_GDV=M.PERMIT_GDV, ENGINEERING=M.ENGINEERING, EXTRA_FLOOR_FEE=M.EXTRA_FLOOR_FEE,
    CONTINGENCY=M.CONTINGENCY, SELLING=M.SELLING, LAND_TXN=M.LAND_TXN, SALE_HAIRCUT=M.SALE_HAIRCUT,
    TARGET_PROFIT=M.TARGET_PROFIT, OWNER_TARGET=M.OWNER_TARGET, MONTHS=M.MONTHS, CAPITAL_COST=M.CAPITAL_COST,
    PARTNER_BUILDER_SHARE=M.PARTNER_BUILDER_SHARE, BUILDER_TARGET=M.BUILDER_TARGET,
    PARK_GROUND_M2=M.PARK_GROUND_M2, PARK_BASEMENT_M2=M.PARK_BASEMENT_M2,
    BASEMENT_COST_FACTOR=M.BASEMENT_COST_FACTOR, PV=M.installment_pv_factor(),
)

wins = [a['wprem'] for a in assets if a['wprem'] is not None]
now = datetime.datetime.now()
data = dict(
    meta=dict(updated=today_fa(now), updated_iso=now.isoformat(timespec='minutes'), last_step=LAST,
              last_date=stage_date(LAST), prev_step=PREV, prev_date=stage_date(PREV) if PREV else None,
              first_date=stage_date(STEPS[0]), n_stages=len(STEPS), months=MONTHS, missing_stage2=18),
    totals=R['totals'], params=params, locs=locs, loc_rows=loc_rows, stages=stages, series=R['series'],
    assets=assets, gone_top=[key_of[i] for i in R['gone_top']], repriced=[key_of[i] for i in R['repriced']],
    stage_diff=stage_diff, changes=changes,
    premium=dict(median=st.median(wins) if wins else None, n=len(wins)),
)


def tidy(x):
    if isinstance(x, float):
        if x != x:
            return None
        return round(x) if abs(x) >= 1000 else round(x, 6) if 30 < abs(x) < 70 else round(x, 4)
    if isinstance(x, dict):
        return {k: tidy(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [tidy(v) for v in x]
    return x


json.dump(tidy(data), open('app/data.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
n_img = sum(1 for a in assets if a['img'])
print(f"app/data.json: {len(assets)} assets, step {LAST} ({stage_date(LAST)}), images {n_img}, "
      f"new {len(stage_diff['new'])}, repriced {len(stage_diff['repriced'])}, sold_prev {len(stage_diff['sold_prev'])}, "
      f"left_prev {len(stage_diff['left_prev'])}, changes {len(changes['items']) if changes else '-'}")
