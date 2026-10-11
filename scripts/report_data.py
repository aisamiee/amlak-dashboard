"""Aggregate everything into output/report_data.json (for the HTML report) and output/amlak_analysis.xlsx."""
import json
import re
import statistics as st
import sys
from collections import Counter, defaultdict

import pandas as pd

sys.path.insert(0, 'scripts')
from locations import LOC  # noqa: E402
from market import GARDEN_MKT, LAND_MKT, P_NEW  # noqa: E402
from jalali import today_str  # noqa: E402

ALL = json.load(open('data/all.json', encoding='utf-8'))
RES = json.load(open('data/residential_listings.json', encoding='utf-8'))
ASSETS = json.load(open('data/assets.json', encoding='utf-8'))
VAL = {v['asset']: v for v in json.load(open('data/valuation.json', encoding='utf-8'))}
LAST = max(r['step'] for r in ALL)          # latest published stage
FA_D = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')

STAGE_DATE = {}
for r in ALL:
    if r.get('date'):
        STAGE_DATE.setdefault(r['step'], Counter())[re.sub(r'^\S+,\s*', '', r['date'])] += 1
STAGE_DATE = {k: v.most_common(1)[0][0] for k, v in STAGE_DATE.items()}


def med(xs):
    xs = [x for x in xs if x is not None]
    return st.median(xs) if xs else None


# ---------------- stage summary ----------------
first_seen = defaultdict(int)
for a in ASSETS:
    first_seen[a['first_step']] += 1
stages = []
for s in range(1, LAST + 1):
    allr = [r for r in ALL if r['step'] == s]
    res = [r for r in RES if r['step'] == s]
    city_land = [r for r in res if r['scope'] == 'city' and r['kind'] == 'land' and r.get('rate_eff')]
    wins = [r for r in res if r.get('winner_price')]
    stages.append(dict(
        step=s, date=STAGE_DATE.get(s), listings=len(allr), residential=len(res),
        new_assets=first_seen.get(s, 0), sold=len(wins),
        median_premium=med([r.get('premium') for r in wins]),
        city_land_median_rate=med([r['rate_eff'] / 10 for r in city_land]),
        buyers_company=sum(1 for r in wins if r.get('buyer_type') == 'حقوقی'),
    ))

# ---------------- location summary ----------------
by_loc = defaultdict(list)
for a in ASSETS:
    if a['kind'] in ('land', 'large_parcel', 'pack', 'garden', 'mixed', 'tourism'):
        by_loc[a['loc']].append(a)
loc_rows = []
for loc, items in by_loc.items():
    meta = LOC.get(loc, {})
    kinds = ('land', 'large_parcel', 'pack') if any(a['kind'] == 'land' for a in items) else ('garden', 'mixed', 'tourism')
    lst = [r for r in RES if r['loc'] == loc and r['kind'] in kinds and r.get('rate_eff')]
    steps = sorted({r['step'] for r in lst})
    if not steps:
        continue
    f_rate = med([r['rate_eff'] for r in lst if r['step'] == steps[0]])
    l_rate = med([r['rate_eff'] for r in lst if r['step'] == steps[-1]])
    weeks = steps[-1] - steps[0]
    sold = [a for a in items if a['status'] == 'sold']
    relist = [a['n_listings'] for a in sold]
    # same-plot repricing: identical plots re-offered at a new base (pure price change, no mix effect)
    same = [(a['rate_last'] / a['rate_first']) ** (52 / max(1, a['last_step'] - a['first_step'])) - 1
            for a in items if a['n_listings'] > 1 and a['rate_first'] and a['rate_last']
            and a['last_step'] - a['first_step'] >= 3]
    # level of brand-new plots priced by Astan's appraisers: first-listing rate of plots entering in
    # the first vs the last third of the season
    entries = sorted((a['first_step'], a['rate_first']) for a in items if a['rate_first'])
    early = [r for st_, r in entries if st_ <= 9]
    late = [r for st_, r in entries if st_ >= 18]
    loc_rows.append(dict(
        loc=loc, name=meta.get('name', loc), district=meta.get('district'), scope=meta.get('scope'),
        assets=len(items), sold=len(sold), active=sum(a['status'] == 'active' for a in items),
        withdrawn=sum(a['status'] in ('withdrawn', 'sold_relisted_gone') for a in items),
        sell_through=len(sold) / len(items) if items else None,
        median_premium=med([a['win_premium'] for a in sold]),
        max_premium=max([a['win_premium'] for a in sold if a['win_premium'] is not None], default=None),
        avg_listings_to_sell=(sum(relist) / len(relist)) if relist else None,
        first_step=steps[0], last_step=steps[-1], rate_first=f_rate / 10 if f_rate else None,
        rate_last=l_rate / 10 if l_rate else None,
        rate_change=(l_rate / f_rate - 1) if f_rate and l_rate else None, weeks=weeks,
        growth_annual=((l_rate / f_rate) ** (52 / weeks) - 1) if f_rate and l_rate and weeks >= 4 else None,
        same_plot_annual=med(same), same_plot_n=len(same),
        new_lot_early=med(early) / 10 if early else None, new_lot_late=med(late) / 10 if late else None,
        new_lot_change=(med(late) / med(early) - 1) if early and late else None,
        garden_mkt=GARDEN_MKT.get(loc, (None,))[0], garden_src=GARDEN_MKT.get(loc, (None, None))[1],
        area_total=sum(a['area'] or 0 for a in items),
        p_new=P_NEW.get(loc, (None,))[0], p_src=P_NEW.get(loc, (None, None))[1],
        land_mkt=LAND_MKT.get(loc, (None,))[0],
    ))
loc_rows.sort(key=lambda x: -x['assets'])

# ---------------- asset table ----------------
STATUS_FA = {'active': f'در مزایده فعلی (مرحله {LAST})'.translate(FA_D), 'sold': 'فروخته شد', 'withdrawn': 'خارج شد بدون برنده',
             'sold_relisted_gone': 'برنده داشت، دوباره عرضه و خارج شد'}
asset_rows = []
for a in ASSETS:
    v = VAL.get(a['asset'], {})
    asset_rows.append(dict(
        asset=a['asset'], loc=a['loc'], name=a['loc_name'], scope=a['scope'], kind=a['kind'],
        qate=a['qate'], block=a['block'], area=a['area'], karbari=a['karbari'], address=a['address'],
        status=a['status'], status_fa=STATUS_FA[a['status']], first_step=a['first_step'], last_step=a['last_step'],
        n_listings=a['n_listings'], steps=a['steps'],
        rate_first=a['rate_first'] / 10 if a['rate_first'] else None,
        rate_last=a['rate_last'] / 10 if a['rate_last'] else None, rate_change=a['rate_change'],
        win_step=a['win_step'], win_price=a['win_price'] / 10 if a['win_price'] else None,
        win_premium=a['win_premium'], buyer_type=a['buyer_type'],
        total_last=(a['rate_last'] / 10 * a['area']) if a['rate_last'] and a['area'] else None,
        koroki=a['koroki'], notice=a['notice'],
        history=[dict(step=h['step'], rate=h['rate'] / 10 if h['rate'] else None,
                      win=h['win'] / 10 if h['win'] else None) for h in a['history']],
        **{k: v.get(k) for k in (
            'floors', 'far', 'occupancy', 'footprint_m2', 'gross_m2', 'net_m2', 'units', 'unit_size', 'basement_m2',
            'parking_ground', 'p_new', 'p_src', 'p_conf', 'sale_ppm', 'gdv', 'hard_ppm', 'build_cost',
            'build_cost_per_net', 'land_cost', 'total_cost', 'profit', 'margin', 'annual_return', 'rlv_ppm',
            'headroom', 'safety', 'margin_stress', 'margin_upside', 'land_share_gdv', 'breakeven_ppm',
            'owner_m2', 'builder_m2', 'owner_value', 'owner_ret', 'owner_ret_eff', 'owner_ann_eff',
            'owner_cost_per_m2', 'builder_margin', 'builder_ok', 'owner_fair_share', 'owner_real_share',
            'owner_real_ret_eff', 'owner_real_ann_eff', 'max_bid_partner', 'land_mkt', 'land_mkt_src',
            'vs_land_mkt', 'plot_notes', 'basis', 'exp_premium', 'land_rate_toman',
            'x_floors', 'x_margin', 'x_net_m2', 'x_owner_real_ret_eff', 'x_builder_margin', 'x_max_bid_partner',
            'opt_builder_margin', 'pes_builder_margin',
            'opt_owner_real_ret_eff', 'pes_owner_real_ret_eff', 'opt_max_bid_partner', 'pes_max_bid_partner',
            'opt_margin', 'pes_margin')},
        anomaly=False,
        segment=a.get('segment'),
        garden_mkt=GARDEN_MKT.get(a['loc'], (None,))[0] if a['kind'] == 'garden' else None,
        vs_garden_mkt=((a['rate_last'] / 10) / GARDEN_MKT[a['loc']][0] - 1)
        if a['kind'] == 'garden' and a['loc'] in GARDEN_MKT and a['rate_last'] else None,
    ))

# ---------------- anomalies (excluded from rankings) ----------------
for r in asset_rows:
    r['anomaly'] = bool(r.get('p_new') and r.get('rate_last') and r['rate_last'] < 0.12 * r['p_new']
                        and r['scope'] == 'city' and r['kind'] in ('land', 'large_parcel'))

# ---------------- scoring of active lots (landowner in a 60/40 partnership) ----------------
def clamp(x, lo, hi):
    return max(lo, min(hi, x))


for r in asset_rows:
    if r['status'] != 'active' or r['scope'] not in ('city', 'edge', 'town') or r.get('owner_real_ret_eff') is None or r.get('anomaly'):
        r['score'] = None
        continue
    s_partner = clamp((r['owner_real_ret_eff'] + 0.3) / 0.7, 0, 1)                 # -30%..+40% -> 0..1
    s_builder = clamp((r['builder_margin'] + 0.1) / 0.45, 0, 1)                    # -10%..+35%
    s_land = clamp((-(r['vs_land_mkt'] or 0) + 0.1) / 0.45, 0, 1)                  # +10% over .. -35% under market
    s_loc = clamp(((r['p_new'] or 0) - 30e6) / 170e6, 0, 1)                         # 30M..200M new-build price
    s_robust = clamp(((r['pes_owner_real_ret_eff'] or -1) + 1) / 1.0, 0, 1)        # downside resilience
    r['score'] = round(100 * (0.30 * s_partner + 0.20 * s_builder + 0.20 * s_land + 0.15 * s_loc + 0.15 * s_robust), 1)
    if r['builder_margin'] >= 0.25 and r['owner_real_ret_eff'] >= 0.15:
        r['verdict'] = 'مناسب مشارکت ۶۰/۴۰ — پیشنهاد خرید تا سقف تعیین‌شده'
    elif r['builder_margin'] >= 0.15 and r['owner_real_ret_eff'] >= 0:
        r['verdict'] = 'مشارکت شدنی ولی کم‌سود — فقط با قیمت نزدیک پایه'
    elif (r['vs_land_mkt'] or 0) <= -0.15:
        r['verdict'] = 'ساخت توجیه ندارد؛ ارزان‌تر از بازار زمین — فرصت خرید زمین (نگهداری/فروش)'
    else:
        r['verdict'] = 'توصیه نمی‌شود (ساخت زیان‌ده و قیمت هم‌تراز یا بالاتر از بازار)'

# current base level per location (median of the last two stages it appeared in)
cur_level = {}
for loc in {r['loc'] for r in RES}:
    lst = [r for r in RES if r['loc'] == loc and r['kind'] in ('land', 'large_parcel') and r.get('rate_eff')]
    if not lst:
        continue
    last = max(r['step'] for r in lst)
    cur_level[loc] = (med([r['rate_eff'] / 10 for r in lst if r['step'] >= last - 1]), last)

# ---------------- gone-but-valuable ----------------
gone = [r for r in asset_rows if r['status'] in ('sold', 'withdrawn', 'sold_relisted_gone') and r['scope'] == 'city'
        and r['kind'] in ('land', 'large_parcel') and r.get('max_bid_partner') is not None and not r['anomaly']]
for r in gone:
    paid = (r['win_price'] if r['status'] == 'sold' and r['win_price'] else r['rate_last'])
    r['paid_ref'] = paid
    lvl = cur_level.get(r['loc'])
    r['loc_level_now'] = lvl[0] if lvl else None
    r['loc_level_step'] = lvl[1] if lvl else None
    # paper gain: today's base level of the same location vs the price paid / last asked
    r['paper_gain'] = (lvl[0] / paid - 1) if (lvl and paid and lvl[1] > r['last_step']) else None
    r['value_gap'] = (r['max_bid_partner'] / paid - 1) if paid else None
gone.sort(key=lambda r: -((r['paper_gain'] or 0) * 0.5 + max(-1, r['value_gap'] or -1) * 0.5))

# ---------------- price-change log (unsold lots that were re-priced) ----------------
repriced = [r for r in asset_rows if r['n_listings'] > 1 and abs(r['rate_change'] or 0) > 0.001]

# per-location base-price series (median land rate per stage, toman/m2) for the main city locations
series = {}
for lr in loc_rows:
    if lr['scope'] != 'city' or lr['assets'] < 8:
        continue
    pts = []
    for st_ in range(1, LAST + 1):
        vals = [r['rate_eff'] / 10 for r in RES if r['loc'] == lr['loc'] and r['step'] == st_
                and r['kind'] in ('land', 'large_parcel') and r.get('rate_eff')]
        if vals:
            pts.append([st_, med(vals), len(vals)])
    series[lr['loc']] = dict(name=lr['name'], pts=pts)

out = dict(
    series=series,
    generated=today_str(), last_step=LAST, stage_dates=STAGE_DATE, stages=stages, locations=loc_rows,
    assets=asset_rows, gone_top=[r['asset'] for r in gone[:40]],
    repriced=[r['asset'] for r in repriced],
    totals=dict(
        listings=len(ALL), residential_listings=len(RES), assets=len(ASSETS),
        status=Counter(a['status'] for a in ASSETS), scope=Counter(a['scope'] for a in ASSETS),
        kinds=Counter(a['kind'] for a in ASSETS),
        karbari_all=Counter(r['karbari'] for r in ALL).most_common(12),
        winners=sum(1 for r in RES if r.get('winner_price')),
        buyers=Counter(r.get('buyer_type') for r in RES if r.get('winner_price')),
        premium_median=med([r.get('premium') for r in RES]),
        premium_mean=st.mean([r['premium'] for r in RES if r.get('premium') is not None]),
        premium_share_over10=sum(1 for r in RES if (r.get('premium') or 0) > 0.10) / max(1, sum(1 for r in RES if r.get('premium') is not None)),
        missing_stage2=18,
    ),
)
json.dump(out, open('output/report_data.json', 'w', encoding='utf-8'), ensure_ascii=False, default=float)

# ---------------- Excel ----------------
with pd.ExcelWriter('output/amlak_analysis.xlsx', engine='xlsxwriter') as xw:
    act = pd.DataFrame([r for r in asset_rows if r['status'] == 'active'])
    cols = ['score', 'verdict', 'name', 'qate', 'block', 'area', 'land_rate_toman', 'exp_premium', 'total_last',
            'floors', 'far', 'footprint_m2', 'gross_m2', 'basement_m2', 'net_m2', 'units', 'p_new', 'sale_ppm',
            'build_cost_per_net', 'gdv', 'land_cost', 'build_cost', 'total_cost', 'profit', 'margin',
            'owner_m2', 'builder_m2', 'owner_cost_per_m2', 'owner_ret_eff', 'builder_margin', 'owner_fair_share',
            'owner_real_share', 'owner_real_ret_eff', 'owner_real_ann_eff', 'max_bid_partner', 'rlv_ppm',
            'land_mkt', 'vs_land_mkt', 'opt_owner_real_ret_eff', 'pes_owner_real_ret_eff', 'plot_notes',
            'p_src', 'land_mkt_src', 'first_step', 'n_listings', 'rate_first', 'rate_change', 'koroki', 'notice']
    act.reindex(columns=cols).sort_values('score', ascending=False).to_excel(xw, sheet_name=f'لاتهای فعال مرحله {LAST}'.translate(FA_D), index=False)
    pd.DataFrame(asset_rows).drop(columns=['history', 'steps']).to_excel(xw, sheet_name='همه قطعات مسکونی', index=False)
    pd.DataFrame(loc_rows).to_excel(xw, sheet_name='تحلیل محله‌ها', index=False)
    pd.DataFrame(stages).to_excel(xw, sheet_name='آمار مراحل', index=False)
    pd.DataFrame([r for r in RES]).drop(columns=['fulltext', 'qtok'], errors='ignore').to_excel(xw, sheet_name='ریز آگهی‌های مسکونی', index=False)
    pd.DataFrame(ALL).drop(columns=['fulltext'], errors='ignore').to_excel(xw, sheet_name=f'همه آگهی‌ها ({LAST} مرحله)'.translate(FA_D), index=False)
print('stages', len(stages), 'locs', len(loc_rows), 'assets', len(asset_rows), 'gone', len(gone), 'repriced', len(repriced))
