"""Build per-asset history of residential lots across all auction stages.

Input : data/all.json (parsed listings)
Output: data/residential_listings.json  (one row per listing, enriched)
        data/assets.json                (one row per tracked asset, with history)
"""
import json
import re
import sys
from collections import defaultdict

sys.path.insert(0, 'scripts')
from locations import LOC, canon, norm  # noqa: E402

LAST_STEP = max(r["step"] for r in json.load(open("data/all.json", encoding="utf-8")))  # latest published stage
FA = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')


def num(s):
    if s is None:
        return None
    m = re.search(r'\d+(?:\.\d+)?', str(s).translate(FA).replace(',', ''))
    return float(m.group()) if m else None


def qtokens(q):
    toks = re.findall(r'\d+', (q or '').translate(FA))
    toks = [int(t) for t in toks]
    return tuple(sorted(set(t for t in toks if t != 0)))


def blk(b):
    b = (b or '').translate(FA).strip()
    return None if b in ('', '0', '-', '*', '--') else b


def kind(r):
    k, a = r['karbari'] or '', norm(r['address'])
    if r.get('segment') == 'suburb_other':
        if re.search('باغ|زراعی|کشاورزی', k):
            return 'garden'
        if re.search('تفریحی|توریست', k):
            return 'tourism'
        return 'mixed'
    q = norm(r.get('qate'))
    if ('آپارتمان' in k or 'واحد' in a or 'طبقه' in q or re.search(r'ط\s*\d', q)
            or r['loc'] in ('mahdieh_apt', 'rahnamaei3')):
        return 'apartment'
    if 'پک' in a or r['loc'] == 'pack_misc':
        return 'pack'
    if (r['area'] or 0) >= 5000:
        return 'large_parcel'
    return 'land'


SUBURB_USES = r'باغ|مختلط|تفریحی|توریست|مسکونی|آپارتمان|زراعی|کشاورزی'
_all = json.load(open('data/all.json', encoding='utf-8'))
rows = []
for r in _all:
    k = r.get('karbari') or ''
    if re.search('مسکونی|آپارتمان', k):
        r['segment'] = 'residential'
        rows.append(r)
    elif LOC.get(canon(r['address']), {}).get('scope') in ('edge', 'town') and re.search(SUBURB_USES, k) \
            and not re.search('صنعتی|انبار|پرورش|اجاره', k):
        r['segment'] = 'suburb_other'      # gardens, mixed-use, tourism plots around Mashhad (Torqabeh, ...)
        rows.append(r)

# manual corrections verified against the notices / neighbouring stages
MANUAL_FIX = {
    9881: {'area': 8910.41},   # Torqabeh Imam Khomeini 4: area typed as 891.41 (same parcel as 8910.41)
}
for r in rows:
    if r.get('id') in MANUAL_FIX:
        r.update(MANUAL_FIX[r['id']])
        r['area_fixed'] = True

for r in rows:
    r['loc'] = canon(r['address'])
    meta = LOC.get(r['loc'], {})
    r['scope'] = meta.get('scope')
    # area: explicit, else from "(۵۹۳.۲)" in the address, else total/rate
    if not r.get('area'):
        m = re.search(r'\(\s*([\d۰-۹.٫]+)\s*\)', r['address_raw'] or '')
        if m:
            r['area'] = num(m.group(1).replace('٫', '.'))
    if not r.get('area') and r.get('rate') and r.get('total'):
        r['area'] = round(r['total'] / r['rate'], 2)
    r['rate_printed'] = r.get('rate') or 0
    if r['rate_printed'] > 5e10 and r.get('area'):      # the lot's total price was typed into the rate field
        r['rate_printed'] = r['rate_printed'] / r['area']
    if r['rate_printed'] and r['rate_printed'] < 1e6:   # garbage (e.g. 275 rial)
        r['rate_printed'] = 0
    r['rate_derived'] = (r['total'] / r['area']) if (r.get('total') and r.get('area')) else None
    if r['rate_derived'] and r['rate_derived'] < 1e6:
        r['rate_derived'] = None

# effective base rate per m2 (rial): when printed rate and total/area disagree (typos of 10x are common),
# pick the candidate closest (log-distance) to the median printed rate of the same location in nearby stages.
import math  # noqa: E402
by_loc = defaultdict(list)
for r in rows:
    if r['rate_printed']:
        by_loc[r['loc']].append((r['step'], r['rate_printed']))


def loc_median(loc, step):
    vals = sorted(v for s_, v in by_loc[loc] if abs(s_ - step) <= 4) or sorted(v for _, v in by_loc[loc])
    return vals[len(vals) // 2] if vals else None


for r in rows:
    p_, d_ = r['rate_printed'], r['rate_derived']
    r['rate_flag'] = ''
    if p_ and d_ and abs(p_ - d_) / max(p_, d_) > 0.02:
        # the winning bid is the best anchor (it sits a few % above the true base); else the location median
        ref = r.get('winner_price') or loc_median(r['loc'], r['step'])
        r['rate_eff'] = min((p_, d_), key=lambda v: abs(math.log(v / ref))) if ref else d_
        r['rate_flag'] = 'printed_rate_typo' if r['rate_eff'] == d_ else 'total_typo'
    else:
        r['rate_eff'] = p_ or d_

for r in rows:
    r['qtok'] = qtokens(r.get('qate'))
    r['blk'] = blk(r.get('block'))
    r['kind'] = kind(r)
    wp = r.get('winner_price')
    r['win_flag'] = ''
    if wp and r['rate_eff']:
        if wp / r['rate_eff'] > 50 and r.get('area'):          # total price entered instead of per-m2
            wp = wp / r['area']; r['win_flag'] = 'win_total_converted'
        elif 8 < wp / r['rate_eff'] < 13:                      # one extra digit typed in the bid
            wp = wp / 10; r['win_flag'] = 'win_x10_fixed'
        prem = wp / r['rate_eff'] - 1
        if not (-0.05 <= prem <= 0.8):
            r['win_flag'] = 'win_anomaly'
        r['winner_price'] = wp
        r['premium'] = prem if r['win_flag'] != 'win_anomaly' else None
    else:
        r['premium'] = None

# ---------------- asset matching ----------------
# 1) bucket by (loc, plot-number tokens); 2) inside a bucket, cluster by block and area (+/-3%)
buckets = defaultdict(list)
for i, r in enumerate(rows):
    key = (r['loc'], r['qtok'] if r['qtok'] else ('A', round(r['area'] or 0)))
    buckets[key].append(i)

assets = []


def close(a, b, tol=0.03):
    return a and b and abs(a - b) / max(a, b) <= tol


for key, idxs in buckets.items():
    clusters = []  # each: dict(blk, area, members)
    # records with an explicit block first, so block-less ones can attach to them
    for i in sorted(idxs, key=lambda i: (rows[i]['blk'] is None, rows[i]['step'])):
        r = rows[i]
        cand = [c for c in clusters if close(c['area'], r['area']) and
                (r['blk'] is None or c['blk'] is None or c['blk'] == r['blk'])]
        # never put two listings of the same stage into one asset
        cand = [c for c in cand if r['step'] not in {rows[j]['step'] for j in c['members']}]
        if cand:
            c = cand[0]
            c['members'].append(i)
            if c['blk'] is None and r['blk']:
                c['blk'] = r['blk']
        else:
            clusters.append(dict(blk=r['blk'], area=r['area'], members=[i]))
    for c in clusters:
        c['loc'], c['qtok'] = rows[c['members'][0]]['loc'], rows[c['members'][0]]['qtok']
        assets.append(c)

# 3) merge clusters of the same plot whose numbering was written differently between stages
#    (e.g. "2" vs "2و69", block "9" vs "90", plot number missing): same location, area within 1%,
#    plot tokens equal / empty / subset, and no stage in common.
def same_plot(a, b):
    if a['loc'] != b['loc'] or not close(a['area'], b['area'], 0.01):
        return False
    ta, tb = set(a['qtok']), set(b['qtok'])
    if not (ta == tb or not ta or not tb or ta <= tb or tb <= ta):
        return False
    sa = {rows[i]['step'] for i in a['members']}
    sb = {rows[i]['step'] for i in b['members']}
    return not (sa & sb)


merged = True
while merged:
    merged = False
    for i in range(len(assets)):
        for j in range(i + 1, len(assets)):
            a, b = assets[i], assets[j]
            if a['qtok'] == b['qtok'] and (a['blk'] == b['blk']):
                continue  # already separated deliberately by area clustering
            if same_plot(a, b):
                # only merge when the match is unambiguous for b
                rivals = [k for k, c in enumerate(assets) if k not in (i, j) and same_plot(c, b)]
                if rivals:
                    continue
                a['members'] += b['members']
                a['qtok'] = a['qtok'] if len(a['qtok']) >= len(b['qtok']) else b['qtok']
                a['blk'] = a['blk'] or b['blk']
                assets.pop(j)
                merged = True
                break
        if merged:
            break

out_assets = []
for n, c in enumerate(assets):
    ms = sorted(c['members'], key=lambda i: rows[i]['step'])
    L = [rows[i] for i in ms]
    for r in L:
        r['asset'] = n
    steps = [r['step'] for r in L]
    win = [r for r in L if r.get('winner_price')]
    first_win = win[0] if win else None
    after_win = [r for r in L if first_win and r['step'] > first_win['step']]
    last = L[-1]
    if last['step'] == LAST_STEP and not last.get('winner_price'):
        status = 'active'           # on offer in the latest stage
    elif last.get('winner_price'):
        status = 'sold'
    elif first_win:
        status = 'sold_relisted_gone'
    else:
        status = 'withdrawn'        # left the list without a published winner
    rates = [r['rate_eff'] for r in L if r['rate_eff']]
    lw = win[-1] if win else None
    out_assets.append(dict(
        asset=n, loc=L[0]['loc'], loc_name=LOC.get(L[0]['loc'], {}).get('name'),
        scope=L[0]['scope'], kind=L[0]['kind'],
        qate=last.get('qate'), block=c['blk'], area=c['area'],
        address=last['address'], karbari=last['karbari'], segment=L[0].get('segment'),
        first_step=steps[0], last_step=steps[-1], n_listings=len(L), steps=steps,
        rate_first=rates[0] if rates else None, rate_last=rates[-1] if rates else None,
        rate_change=(rates[-1] / rates[0] - 1) if len(rates) > 1 and rates[0] else 0.0,
        n_wins=len(win), relisted_after_win=bool(after_win),
        win_step=lw['step'] if lw else None, win_price=lw['winner_price'] if lw else None,
        win_premium=lw['premium'] if lw else None, buyer_type=lw.get('buyer_type') if lw else None,
        status=status, ids=[r['id'] for r in L],
        koroki=last.get('koroki'), notice=next((r['notice'] for r in reversed(L) if r.get('notice')), None),
        history=[dict(step=r['step'], id=r['id'], rate=r['rate_eff'], total=r['total'],
                      win=r.get('winner_price'), prem=r.get('premium'), flag=r['rate_flag']) for r in L],
    ))

json.dump(rows, open('data/residential_listings.json', 'w', encoding='utf-8'), ensure_ascii=False, default=str)
json.dump(out_assets, open('data/assets.json', 'w', encoding='utf-8'), ensure_ascii=False, default=str)

from collections import Counter  # noqa: E402
print('listings', len(rows), 'assets', len(out_assets))
print('status', Counter(a['status'] for a in out_assets))
print('kind', Counter(a['kind'] for a in out_assets))
print('scope', Counter(a['scope'] for a in out_assets))
print('rate flags', Counter(r['rate_flag'] for r in rows))
