"""Render output/report.html (Persian, RTL) from output/report_data.json."""
import json
import math
import sys

sys.path.insert(0, 'scripts')
from market import (BUILDER_TARGET, CAPITAL_COST, CONTINGENCY, ENGINEERING, GARDEN_MKT, LAND_MKT,  # noqa: E402
                    MONTHS, NET_TO_GROSS, OCCUPANCY, OWNER_TARGET, PERMIT_GDV, P_NEW, SALE_HAIRCUT,
                    SELLING, TARGET_PROFIT, installment_pv_factor)

D = json.load(open('output/report_data.json', encoding='utf-8'))
A = {a['asset']: a for a in D['assets']}


def clean(x):
    if isinstance(x, float):
        if math.isnan(x) or math.isinf(x):
            return None
        return round(x, 4) if abs(x) < 1e4 else round(x)
    if isinstance(x, dict):
        return {k: clean(v) for k, v in x.items()}
    if isinstance(x, list):
        return [clean(v) for v in x]
    return x


ACTIVE_KEYS = ['asset', 'name', 'loc', 'scope', 'kind', 'qate', 'block', 'area', 'karbari', 'rate_last', 'total_last',
               'first_step', 'n_listings', 'rate_first', 'rate_change', 'exp_premium', 'floors', 'far', 'footprint_m2',
               'gross_m2', 'basement_m2', 'net_m2', 'units', 'unit_size', 'p_new', 'p_src', 'p_conf', 'sale_ppm', 'gdv',
               'build_cost', 'build_cost_per_net', 'land_cost', 'total_cost', 'profit', 'margin', 'margin_stress',
               'margin_upside', 'rlv_ppm', 'owner_m2', 'builder_m2', 'owner_value', 'owner_real_share',
               'owner_real_ret_eff', 'owner_fair_share', 'builder_margin', 'max_bid_partner', 'opt_owner_real_ret_eff',
               'pes_owner_real_ret_eff', 'opt_max_bid_partner', 'pes_max_bid_partner', 'x_floors', 'x_margin',
               'x_owner_real_ret_eff', 'land_mkt', 'land_mkt_src', 'vs_land_mkt', 'garden_mkt', 'vs_garden_mkt',
               'plot_notes', 'score', 'verdict', 'koroki', 'notice', 'history', 'owner_cost_per_m2']
active = [{k: A[i].get(k) for k in ACTIVE_KEYS}
          for i in A if A[i]['status'] == 'active']
for r in active:
    vx = next((v for v in [r] if v), None)
active.sort(key=lambda r: (r['scope'] != 'city', -(r['score'] or -1), r['name']))

LOC_KEYS = ['loc', 'name', 'scope', 'district', 'assets', 'sold', 'active', 'withdrawn', 'sell_through', 'median_premium',
            'max_premium', 'avg_listings_to_sell', 'first_step', 'last_step', 'rate_first', 'rate_last',
            'new_lot_early', 'new_lot_late', 'new_lot_change', 'p_new', 'land_mkt', 'garden_mkt', 'area_total']
locs = [{k: l.get(k) for k in LOC_KEYS} for l in D['locations'] if l['scope'] != 'out']

gone = []
for i in D['gone_top'][:24]:
    a = A[i]
    gone.append({k: a.get(k) for k in ('asset', 'name', 'qate', 'area', 'status', 'last_step', 'win_step', 'paid_ref',
                                       'loc_level_now', 'paper_gain', 'max_bid_partner', 'value_gap', 'win_premium',
                                       'floors', 'p_new')})

repriced = []
for i in D['repriced']:
    a = A[i]
    if a['scope'] == 'out':
        continue
    repriced.append({k: a.get(k) for k in ('asset', 'name', 'qate', 'area', 'status', 'first_step', 'last_step',
                                           'n_listings', 'rate_first', 'rate_last', 'rate_change')})
repriced.sort(key=lambda r: r['rate_change'])

loc_index = {}
names = []
for a in D['assets']:
    if a['loc'] not in loc_index:
        loc_index[a['loc']] = len(names)
        names.append(a['name'] or a['loc'])
allrows = [[a['asset'], loc_index[a['loc']], a['qate'], a['area'], a['status'], a['first_step'], a['last_step'],
            a['n_listings'], a['rate_first'], a['rate_last'], a['win_price'], a['win_premium'], a['kind'], a['scope'],
            a['karbari'], a['block']] for a in D['assets']]

series_keys = ['emamat74', 'emamat47', 'janbaz13', 'kooshesh', 'abshar2', 'mahdieh', 'basirat', 'ansar', 'kashf',
               'chah_khase', 'razavieh', 'ghale_siah']
series = []
for k in series_keys:
    s = D['series'].get(k)
    if not s:
        # suburbs are not in D['series']; rebuild from listings
        pts = {}
        for a in D['assets']:
            if a['loc'] == k and a['kind'] == 'land':
                for h in a['history']:
                    if h['rate']:
                        pts.setdefault(h['step'], []).append(h['rate'])
        if not pts:
            continue
        s = dict(name=next(a['name'] for a in D['assets'] if a['loc'] == k),
                 pts=[[st, sorted(v)[len(v) // 2], len(v)] for st, v in sorted(pts.items())])
    series.append(dict(key=k, name=s['name'], pts=s['pts']))

suburb_rows = [ {k: a.get(k) for k in ('asset', 'name', 'loc', 'kind', 'karbari', 'qate', 'area', 'status', 'first_step',
                                       'last_step', 'n_listings', 'rate_first', 'rate_last', 'win_price', 'win_premium',
                                       'garden_mkt', 'vs_garden_mkt', 'land_mkt', 'vs_land_mkt', 'total_last')}
                for a in D['assets'] if a['scope'] in ('edge', 'town')]
suburb_rows.sort(key=lambda r: (r['status'] != 'active', r['loc'], -(r['last_step'] or 0)))

assump = dict(
    occupancy=OCCUPANCY, net_to_gross=NET_TO_GROSS, permit=PERMIT_GDV, eng=ENGINEERING, cont=CONTINGENCY,
    selling=SELLING, haircut=SALE_HAIRCUT, target=TARGET_PROFIT, owner_target=OWNER_TARGET, months=MONTHS,
    capital=CAPITAL_COST, pv=installment_pv_factor(), builder_target=BUILDER_TARGET,
)
market = dict(
    p_new=[[k, v[0], v[1], v[2]] for k, v in P_NEW.items()],
    land=[[k, v[0], v[1], v[2]] for k, v in LAND_MKT.items()],
    garden=[[k, v[0], v[1], v[2]] for k, v in GARDEN_MKT.items()],
)

T = D['totals']
payload = clean(dict(totals=T, stages=D['stages'], locs=locs, active=active, gone=gone, repriced=repriced,
                     names=names, all=allrows, series=series, suburbs=suburb_rows, assump=assump, market=market,
                     loc_names={l['loc']: l['name'] for l in D['locations']}))
data_json = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')

tpl = open('scripts/report_template.html', encoding='utf-8').read()
html = tpl.replace('/*__DATA__*/{}', data_json)
open('output/report.html', 'w', encoding='utf-8').write(html)
print('report.html', round(len(html) / 1024), 'KB', '| active', len(active), '| all', len(allrows))


# ======================= narrative (computed from the data) =======================
FA_D = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')


def f(n, d=0):
    if n is None:
        return '—'
    s = f'{n:,.{d}f}'.replace(',', '٬').replace('.', '٫')
    return s.translate(FA_D)


def m(n):
    return '—' if n is None else f(n / 1e6, 1 if n < 1e7 else 0)


def b(n):
    return '—' if n is None else f(n / 1e9, 1 if n < 1e11 else 0)


def p(x, sign=True):
    if x is None:
        return '—'
    return ('+' if sign and x > 0 else '') + f(x * 100) + '٪'


def rng(vals, fn):
    vals = [v for v in vals if v is not None]
    lo, hi = min(vals), max(vals)
    return fn(lo) if fn(lo) == fn(hi) else f'{fn(lo)} تا {fn(hi)}'


def grp(loc):
    return [r for r in active if r['loc'] == loc]


def lot_card(title, tag, tagcls, rows, body):
    dl = ''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in rows)
    return f'<div class="vcard"><span class="tag {tagcls}">{tag}</span><h3>{title}</h3><dl>{dl}</dl>{body}</div>'


cards = []
g = grp('emamat74')
corner = next((r for r in g if r['qate'] == '30'), None)
loc74 = next(l for l in D['locations'] if l['loc'] == 'emamat74')
cards.append(lot_card(
    f'امامت ۷۴ — {f(len(g))} قطعه (جلال آل‌احمد ۷۱، منطقهٔ ۱۱)', 'بهترین گزینهٔ فعال — بخرید', 'good',
    [('مساحت', rng([r['area'] for r in g], lambda v: f(v)) + ' متر، بر ۱۲ متر'),
     ('قیمت پایه', rng([r['rate_last'] for r in g], m) + ' میلیون در متر'),
     ('کل حق تقدیمی', rng([r['total_last'] for r in g], b) + ' میلیارد'),
     ('ضوابط', 'تراکم زیاد گونهٔ ۲ — ۶ طبقه روی پیلوت، تراکم ۳۶۰٪'),
     ('ساخت', rng([r['net_m2'] for r in g], f) + ' متر فروش، ' + rng([r['units'] for r in g], f) + ' واحد'),
     ('سهم ۴۰٪ شما', rng([r['owner_m2'] for r in g], f) + ' متر ≈ ' + rng([r['owner_value'] for r in g], b) + ' میلیارد'),
     ('سود سازنده با ۶۰٪', rng([r['builder_margin'] for r in g], p) + ' (حداقل لازم ۲۵٪)'),
     ('بازده واقعی شما', rng([r['owner_real_ret_eff'] for r in g], p) + ' در حدود ۳۳ ماه'),
     ('سقف پیشنهاد', f'{m(min(r["max_bid_partner"] for r in g))} میلیون در متر' + (f'؛ قطعهٔ دونبش ۳۰ تا {m(corner["max_bid_partner"])}' if corner else ''))],
    f'<p>تنها گروهی که در مشارکت ۶۰/۴۰ برای هر دو طرف سودده است. آپارتمان نوساز امامت و جلال در دیوار حدود ۲۰۰ میلیون است و تراکم ۶ طبقه سهم زمین در هر متر ساخت را پایین می‌آورد. قیمت پایهٔ همین قطعه‌ها از {m(loc74["new_lot_early"] or 0) if loc74.get("new_lot_early") else "۱۴۵"} میلیون در مرحلهٔ ۲۲ به ۱۸۰ تا ۱۹۰ میلیون رسیده و برنده‌های مرحلهٔ ۲۵ تا ۲۲٪ بالاتر از پایه پیشنهاد داده‌اند. <b>بالاتر از سقف پیشنهاد نروید</b>؛ اگر رقابت قیمت را از سقف بالاتر برد، صرف نمی‌کند.</p>'))

g = grp('emamat47')
cards.append(lot_card(
    f'امامت ۴۷ — {f(len(g))} قطعه (انتهای امامت، سمت آموزگار)', 'شدنی ولی کم‌سود', 'warn',
    [('مساحت', rng([r['area'] for r in g], f) + ' متر، دوبر روی معابر ۱۲ و ۱۸ متری'),
     ('قیمت پایه', rng([r['rate_last'] for r in g], m) + ' میلیون؛ کل ' + rng([r['total_last'] for r in g], b) + ' میلیارد'),
     ('ضوابط', 'تراکم متوسط گونهٔ ۲ — ۵ طبقه، تراکم ۳۰۰٪'),
     ('سهم ۴۰٪ شما', rng([r['owner_m2'] for r in g], f) + ' متر ≈ ' + rng([r['owner_value'] for r in g], b) + ' میلیارد'),
     ('سود سازنده', rng([r['builder_margin'] for r in g], p)),
     ('بازده واقعی شما', rng([r['owner_real_ret_eff'] for r in g], p)),
     ('سقف پیشنهاد (بازده ۱۵٪)', rng([r['max_bid_partner'] for r in g], m) + ' میلیون — کمتر از قیمت پایه')],
    '<p>سازنده با ۶۰٪ سود کافی دارد، ولی با قیمت پایهٔ فعلی سهم ۴۰٪ شما فقط کمی بیشتر از پول زمین می‌ارزد. فقط اگر بدون رقابت و با قیمت پایه برنده شوید، و هدفتان بیشتر حفظ ارزش در برابر تورم باشد تا سود، ارزش بررسی دارد.</p>'))

land_disc = [r for r in active if r['scope'] == 'city' and r.get('vs_land_mkt') is not None and r['vs_land_mkt'] <= -0.15]
if land_disc:
    rows = []
    for r in sorted(land_disc, key=lambda r: r['vs_land_mkt']):
        rows.append((f'{r["name"].split("(")[0].strip()} {r["qate"] if r["qate"] not in ("0", None) else ""}'.strip(),
                     f'{f(r["area"])} م، {m(r["rate_last"])} در برابر بازار {m(r["land_mkt"])} ({p(r["vs_land_mkt"])})، کل {b(r["total_last"])} میلیارد'))
    cards.append(lot_card('زیر قیمت بازار زمین، ولی برای ساخت نه', 'فقط برای خرید و نگهداری زمین', 'warn', rows,
                          '<p>در این قطعه‌ها قیمت پایه از آگهی‌های زمین مشابه در دیوار پایین‌تر است. ولی با قیمت آپارتمان و هزینهٔ ساخت امروز، ساخت یا مشارکت ۶۰/۴۰ سود ندارد. اگر هدف حفظ سرمایه در زمین و فروش بعدی است، با پیشنهادی نزدیک قیمت پایه مناسب‌اند. رضاشهر از مرحلهٔ ۲ هفت بار عرضه شده و نفروخته؛ دلیلش احتمالاً مبلغ کل بالای آن است. پیش از پیشنهاد، بازدید و استعلام کنید.</p>'))

avoid = {}
for r in active:
    if r['scope'] == 'city' and r.get('verdict', '') and r['verdict'].startswith('توصیه نمی‌شود'):
        avoid.setdefault(r['loc'], []).append(r)
WHY = {
    'janbaz13': 'آپارتمان نوساز جانباز و وصال فقط حدود ۸۱ میلیون است و زمین ۱۲۰ تا ۱۲۵ میلیون؛ ساخت ۳۵٪ زیان می‌دهد.',
    'abshar2': 'تراکم ۲۳۰٪ با آپارتمان حدود ۱۱۵ میلیونی؛ سازنده با ۶۰٪ زیان می‌کند و سهم منصفانهٔ مالک فقط ۱۶ تا ۱۸٪ است.',
    'mahdieh': 'بلوک ۳۴ تراکم کم (۳ طبقه) دارد؛ با قیمت حدود ۱۱۰ میلیون آپارتمان، ساخت زیان‌ده است.',
    'fakouri': '۱۳۸ متر و روبه‌روی حریم خط فشار قوی؛ قیمت ۱۳۵ میلیون برای ۳ طبقه گران است.',
    'tollab': 'قطعهٔ مثلثی با عقب‌نشینی؛ زمین ۹۰ میلیون در برابر آپارتمان حدود ۷۰ میلیون.',
    'ansar': 'قیمت پایه حدود ۳۵٪ بالاتر از آگهی‌های زمین انصار (حدود ۱۵ میلیون) است.',
    'kashf': 'آپارتمان حدود ۳۰ میلیون؛ هزینهٔ ساخت از قیمت فروش بیشتر است.',
    'kooshesh': 'بر ۱۰ متر و ۴ طبقه؛ ساخت سود ندارد.',
    'basirat': 'آپارتمان حدود ۵۸ میلیون؛ ساخت سود ندارد.',
}
arow = []
for loc, rs in avoid.items():
    arow.append((f'{rs[0]["name"].split("(")[0].strip()} ({f(len(rs))})', WHY.get(loc, 'ساخت زیان‌ده')))
cards.append(lot_card('نخرید', 'توصیه نمی‌شود', 'bad', arow,
                      '<p>در این قطعه‌ها قیمت زمین نسبت به قیمت آپارتمانی که می‌شود رویش ساخت بالاست، و قیمت پایه هم ارزان‌تر از بازار زمین نیست.</p>'))

stg = D['stages']
emi = next(l for l in D['locations'] if l['loc'] == 'emamat74')
insights = [
    f'در ۲۶ مرحله {f(T["listings"])} آگهی منتشر شده است. از این میان {f(T["assets"])} قطعهٔ یکتای مسکونی یا حومه‌ای ردیابی شد: {f(T["status"]["sold"])} فروخته شد، {f(T["status"]["withdrawn"])} بدون اعلام برنده از فهرست خارج شد، {f(T["status"].get("sold_relisted_gone", 0))} برنده داشت ولی دوباره عرضه شد، و {f(T["status"]["active"])} قطعه الان در حال عرضه است.',
    f'برنده‌ها معمولاً نزدیک قیمت پایه می‌برند: میانهٔ اضافه‌پرداخت {p(T["premium_median"], False)} است، ولی در {p(T["premium_share_over10"], False)} موارد بیش از ۱۰٪ بالاتر پیشنهاد داده شده. رقابت در کوشش، امامت ۷۴، فرامرز عباسی، طرقبه و چاه خاصه شدیدتر بوده است. {f(T["buyers"].get("حقیقی", 0))} برنده شخص حقیقی‌اند و {f(T["buyers"].get("حقوقی", 0))} برنده شرکت.',
    'سطح قیمتی که کارشناس آستان برای قطعه‌های تازه می‌گذارد در طول فصل بالا رفته است: انصار ۵۴٪، بصیرت و کشف ۴۰٪، چاه خاصه ۳۳٪، آموزگار ۳۰٪، مهدیه ۲۰٪ و آبشار ۱۸٪. یعنی هر چه زودتر بخرید، ارزان‌تر می‌خرید. در جانباز ۱۳ قطعه‌های جدید ارزان‌تر قیمت خورده‌اند (۲۰٪−)، چون بازار آپارتمان آنجا ضعیف است.',
    'اقتصاد ساخت ضعیف شده است. هزینهٔ ساخت در یک سال گذشته حدود ۷۰٪ بالا رفته (کانون انبوه‌سازان، مرداد ۱۴۰۵) و قیمت آپارتمان کمتر رشد کرده. نتیجه این است که فقط جایی که آپارتمان نوساز حدود ۱۷۵ میلیون تومان یا بیشتر است و تراکم بالاست، مشارکت ۶۰/۴۰ برای صاحب زمین بازده واقعی مثبت می‌دهد.',
    f'شرایط پرداخت همهٔ اطلاعیه‌ها: ۴۰٪ نقد و دو چک شش‌ماهه، با ۱۰٪ تخفیف برای پرداخت نقدی کامل. با هزینهٔ سرمایهٔ ۳۵٪ در سال، اقساط معادل {f((1 - installment_pv_factor()) * 100)}٪ تخفیف است، پس اقساط بهتر از نقد است. همهٔ عوارض، استعلام‌ها و هزینهٔ پروانه با خریدار است و عرصهٔ این زمین‌ها موقوفه است.',
    'در حومه، یعنی طرقبه، محور شاندیز (چاه خاصه)، رضویه، کلاته بوغا و قلعه سیاه، با قیمت‌های امروز ساخت در هیچ قطعه‌ای سودده نیست. ارزش این قطعه‌ها فقط در رشد قیمت خودِ زمین است. جزئیات در بخش حومه آمده است.',
]
verdict_html = '<div class="cards">' + ''.join(cards) + '</div><h3>یافته‌های کلیدی</h3><ul class="insights">' + ''.join(f'<li>{x}</li>' for x in insights) + '</ul>'

# ---------------- suburbs narrative ----------------
sub = {}
for r in suburb_rows:
    sub.setdefault(r['loc'], []).append(r)


def sl(loc):
    return sub.get(loc, [])


ck = [r for r in sl('chah_khase') if r['kind'] == 'land']
ck_sold = [r for r in ck if r['status'] == 'sold']
tq = sl('torghabeh')
suburbs_html = f'''
<p class="intro">کاربر خواسته بود طرقبه و شاندیز هم بررسی شود. در کل داده‌های ۲۶ مرحله <b>هیچ آگهی‌ای با نشانی «شاندیز» وجود ندارد</b>. نزدیک‌ترین قطعه‌ها به محور شاندیز «اراضی چاه خاصه» در حاشیهٔ شمال‌غرب مشهد (محدودهٔ سجادشهر و جادهٔ شهرک صنعتی توس) هستند. در دیوار هم آگهی «زمین مسکونی اراضی چاه‌خاصه شاندیز» با همین قیمت‌ها دیده می‌شود.</p>
<div class="cards">
 <div class="vcard"><span class="tag warn">رشد قوی، ساخت زیان‌ده</span><h3>چاه خاصه — محور شاندیز / سجادشهر</h3>
  <dl><dt>قطعه‌های مسکونی</dt><dd>{f(len(ck))} قطعه، عمدتاً ۱۶۸ تا ۲۴۰ متر (۸×۲۵ روی معبر ۱۲ متری)</dd>
  <dt>فروش</dt><dd>{f(len(ck_sold))} فروخته شد؛ اضافه‌پرداخت برنده {rng([r["win_premium"] for r in ck_sold], p)}</dd>
  <dt>قیمت پایه</dt><dd>از ۱۲٫۵ میلیون (مرحلهٔ ۱) به ۱۸ تا ۲۰ میلیون (مرحلهٔ ۲۶)</dd>
  <dt>بازار</dt><dd>زمین در دیوار حدود ۱۶ میلیون؛ آپارتمان شاندیز حدود ۴۴ میلیون</dd>
  <dt>فعال</dt><dd>قطعهٔ ۲۳ (۲۰۰ م، ۱۸ میلیون) و تجمیع ۱۹ تا ۲۱ (۶۰۰ م، ۲۰ میلیون)</dd></dl>
  <p>رشد قیمت این‌جا از همهٔ محله‌ها بیشتر بوده و تقاضای مصرفی (ویلاسازی) قوی است. ولی قیمت پایهٔ مرحلهٔ ۲۶ دیگر از تنها نمونهٔ دیوار ۲۳ تا ۳۷٪ بالاتر است. ساخت آپارتمان این‌جا زیان می‌دهد. برای نگهداری زمین فقط تا حدود ۱۸ میلیون ارزش دارد.</p></div>
 <div class="vcard"><span class="tag warn">بازار پرنوسان</span><h3>طرقبه و شهرک بوستان</h3>
  <dl><dt>قطعه‌ها</dt><dd>{f(len(tq))} مورد: قطعه‌های ۲۳۰ متری بوستان، زمین‌های ۳۴۰۰ تا ۴۲۰۰ متری، باغ‌ها و قطعه‌های تفریحی‌توریستی</dd>
  <dt>قطعه‌های کوچک بوستان</dt><dd>پایهٔ ۴۰ تا ۴۵ میلیون در مرحلهٔ ۴ و ۵؛ برنده تا ۵۸ میلیون (۲۹٪+)</dd>
  <dt>زمین‌های بزرگ</dt><dd>۳۸ تا ۵۵ میلیون؛ همه بدون برنده خارج شدند</dd>
  <dt>فعال</dt><dd>تفریحی‌توریستی ۱۸٬۴۲۸ متر روی بلوار ۴۵ متری امام رضا با ۳۶ میلیون، جمعاً حدود ۶۶۳ میلیارد</dd>
  <dt>بازار</dt><dd>زمین شهری حدود ۴۵ (مروارید ۴۴ تا ۴۶)؛ آپارتمان نوساز حدود ۷۴؛ باغ نغندر ۱۵ تا ۲۲</dd></dl>
  <p>قیمت پایهٔ قطعه‌های طرقبه تقریباً هم‌تراز بازار است. ساخت آپارتمان با فروش حدود ۷۴ میلیونی صرف نمی‌کند. قطعه‌های بزرگ تفریحی و آموزشی پروژهٔ سرمایه‌گذاری‌اند، نه مسکونی.</p></div>
 <div class="vcard"><span class="tag bad">فقط نگهداری</span><h3>شهرک رضویه، کلاته بوغا، قلعه سیاه</h3>
  <dl><dt>رضویه (جادهٔ سرخس)</dt><dd>قطعه‌های ۳۰۰ متری، ۱۲ تا ۱۵ میلیون؛ برنده‌ها تقریباً با قیمت پایه می‌برند؛ ۲ قطعهٔ فعال (۶۱۴ و ۶۱۵، تراکم زیاد، بر ۲۴ متری)</dd>
  <dt>کلاته بوغا</dt><dd>قطعه‌های ۲۵۰ متری، ۲۷ تا ۳۰ میلیون، تراکم متوسط؛ بیشتر بدون برنده خارج شده‌اند</dd>
  <dt>قلعه سیاه</dt><dd>قطعه‌های روستایی ۱۶۰ متری، ۳ تا ۵٫۵ میلیون؛ تقریباً همه با ۱ تا ۱۹٪ اضافه‌پرداخت فروش رفته‌اند</dd></dl>
  <p>مبلغ ورود پایین است (۱ تا ۸ میلیارد)، ولی بازار آپارتمان این‌جا هزینهٔ ساخت را پوشش نمی‌دهد.</p></div>
 <div class="vcard"><span class="tag bad">ارزان مشکوک — بازدید و استعلام الزامی</span><h3>باغ‌ها: ماریان، نغندر، جادهٔ چناران، چاه خاصه، قلعه سیاه</h3>
  <dl><dt>ماریان (محور گلبهار)</dt><dd>۱۱٬۵۲۵ م، حدود ۰٫۵ میلیون در متر (کل ۵٫۸ میلیارد)؛ ۱۳ بار عرضه و هنوز فعال</dd>
  <dt>نغندر (ییلاق طرقبه)</dt><dd>۲٬۲۹۰ م، ۲٫۵ میلیون؛ باغ در بافت نغندر ۱۵ تا ۲۲ میلیون است؛ ۷ بار عرضه و خارج شد</dd>
  <dt>چاه خاصه، جادهٔ شهرک صنعتی</dt><dd>۵۰٬۰۰۰ م، ۳٫۲ میلیون (۱۶۰ میلیارد)؛ از مرحلهٔ ۸ عرضه می‌شود</dd>
  <dt>قلعه سیاه</dt><dd>۳۱٬۴۳۰ م، ۰٫۹ میلیون (۲۸ میلیارد)؛ فعال</dd>
  <dt>جادهٔ چناران</dt><dd>۳۸٬۳۰۲ م، ۰٫۸ میلیون؛ خارج شد</dd></dl>
  <p>این باغ‌ها ۵ تا ۳۰ برابر ارزان‌تر از آگهی‌های باغ اطرافشان قیمت خورده‌اند و بارها بدون خریدار مانده‌اند. چنین فاصله‌ای معمولاً یعنی مشکل حقابه، تصرف، دسترسی، محدودیت «بهره‌برداری باغداری» یا ممنوعیت ساخت. فقط پس از بازدید، استعلام ثبتی و حقابه، و مشورت حقوقی بررسی شوند. گلبهار فقط یک مغازهٔ ۴۱ متری تجاری در مزایده داشت.</p></div>
</div>
<h3>همهٔ قطعه‌های حومه در ۲۶ مرحله</h3>'''

# ---------------- method narrative ----------------
method_html = f'''
<h3>داده</h3>
<p>همهٔ ۲۶ مرحلهٔ سال ۱۴۰۵ با مرورگر واقعی از سامانهٔ <a href="https://amlak.razavi.ir/panel/auctions" target="_blank" rel="noopener">amlak.razavi.ir</a> خوانده شد (این سامانه فقط IP ایران را می‌پذیرد): {f(T["listings"])} آگهی با شمارهٔ قطعه، بلوک، منطقه، کاربری، تراکم، نرخ پایه، حق تقدیمی، نشانی، مساحت، تاریخ و قیمت برنده. نام برنده‌ها عمداً ذخیره نشده است. اطلاعیه‌ها و کروکی‌ها (بیش از ۱۳۰۰ تصویر) هم دانلود و برای قطعه‌های فعال و مهم یکی‌یکی خوانده شد: عرض معبر، ابعاد، نبش بودن، تراکم «کم/متوسط/زیاد»، پروانه، عقب‌نشینی و شرایط پرداخت.</p>
<p>هر قطعه با ترکیب «محل + شمارهٔ قطعه + بلوک + مساحت با تلورانس ۳٪» در مراحل مختلف ردیابی شد. شماره‌گذاری‌های متفاوت یک قطعه (مثل «۲» و «۲و۶۹») و اشتباه‌های تایپی ۱۰ برابری در نرخ، جمع کل یا پیشنهاد برنده با مقایسه با میانهٔ همان محل اصلاح شد. ۱۸ آگهی مرحلهٔ ۲ به دلیل خطای سرور سایت در دسترس نبود.</p>
<h3>فرض‌های مالی (مهر ۱۴۰۵)</h3>
<ul class="insights">
<li>قیمت فروش: میانهٔ قیمت هر متر آپارتمان‌های ساخت ۱۴۰۱ به بعد در دیوار برای هر محله، با کسر ۱۰٪ برای فاصلهٔ آگهی تا معامله و سند موقوفه. جایی که نمونهٔ دیوار کم بود، از میانگین آریامرز یا بازتاب با ۱۰٪ اضافه برای نوساز بودن استفاده شد. منبع هر عدد در جزئیات هر قطعه آمده است.</li>
<li>هزینهٔ ساخت (سخت، به ازای متر ناخالص): ۳۵ میلیون در محله‌های ارزان، ۴۲ تا ۴۶ میلیون در محله‌های متوسط و ۵۰ میلیون در محله‌های بالای ۱۸۰ میلیون. این اعداد با برآورد کانون انبوه‌سازان (حدود ۶۰ میلیون همه‌چیزتمام برای ساختمان ۵ طبقه در کشور) و ۴۵ تا ۵۵ میلیون گزارش‌شده برای مشهد هم‌خوان است. پیلوت ۶۰٪ و زیرزمین ۱۲۵٪ یک طبقهٔ عادی حساب شده است.</li>
<li>عوارض پروانه ۳٫۵٪ ارزش پروژه (تعرفهٔ ۱۴۰۵ با ۴۲٪ رشد)؛ مهندسی، بیمه و انشعابات ۸٪ هزینهٔ ساخت؛ احتیاط ۵٪؛ هزینهٔ فروش ۲٪؛ هزینهٔ ثبت و انتقال زمین ۱٪.</li>
<li>اضافه‌پرداخت مورد انتظار در مزایده: میانهٔ تاریخی اضافه‌پرداخت برنده‌ها در همان محل (پیش‌فرض ۳٪).</li>
<li>سناریوها: بدبینانه با قیمت ۱۰٪− و هزینه ۱۵٪+، خوش‌بینانه با قیمت ۱۰٪+ و هزینه ۱۵٪−.</li>
</ul>
<h3>محدودیت‌ها</h3>
<ul class="insights">
<li>قیمت‌های دیوار قیمت پیشنهادی آگهی است، نه قیمت معامله. تعداد نمونه در بعضی محله‌ها کم است (سطح اطمینان هر عدد در جزئیات آمده است).</li>
<li>تراکم و تعداد طبقات از کروکی‌ها و ضوابط عمومی مشهد گرفته شده است. پیش از پیشنهاد، «اطلاعات طرح مجاز» قطعه را از شهرداری منطقه استعلام کنید. طبقهٔ مازاد هم به‌صورت سناریوی جدا محاسبه شده است.</li>
<li>عرصهٔ همهٔ این زمین‌ها موقوفهٔ آستان قدس است: اجاره‌بهای عرصه، لزوم موافقت متولی برای نقل‌وانتقال، و تخفیف بازار برای سند موقوفه.</li>
<li>این گزارش جایگزین کارشناس رسمی دادگستری، وکیل و بازدید میدانی نیست.</li>
</ul>
<h3>منابع</h3>
<ul class="insights small">
<li>سامانهٔ مزایده: <a href="https://amlak.razavi.ir/panel/auctions" target="_blank" rel="noopener">amlak.razavi.ir/panel/auctions</a></li>
<li>دیوار (آپارتمان و زمین مشهد، طرقبه، شاندیز و گلبهار، ۱۶ مهر ۱۴۰۵): <a href="https://divar.ir/s/mashhad/buy-apartment" target="_blank" rel="noopener">divar.ir</a></li>
<li>آریامرز (میانگین قیمت مناطق و محله‌های مشهد، مهر ۱۴۰۵): <a href="https://www.ariamarz.com/buy-apartment/mashhad" target="_blank" rel="noopener">ariamarz.com</a></li>
<li>بازتاب (قیمت مسکن مشهد، ۱۵ مهر ۱۴۰۵): <a href="https://baztab.ir/market/housing/mashhad/" target="_blank" rel="noopener">baztab.ir</a></li>
<li>هزینهٔ ساخت، کانون انبوه‌سازان: <a href="https://fararu.com/fa/news/989871" target="_blank" rel="noopener">فرارو، ۴ مرداد ۱۴۰۵</a></li>
<li>ضوابط تراکم و طبقات مشهد: <a href="https://mashhadfoolad.com/number-of-floors-2/" target="_blank" rel="noopener">mashhadfoolad.com</a> و <a href="https://irhyperdata.ir/sttm/" target="_blank" rel="noopener">irhyperdata.ir</a></li>
<li>تعرفهٔ عوارض ۱۴۰۵ شهرداری مشهد: <a href="https://shahraranews.ir/fa/news/390238" target="_blank" rel="noopener">شهرآرانیوز</a></li>
<li>ملک موقوفه و تفاوت قیمت: <a href="https://divar.ir/daal/real-estate-legal-tips/legal-tips-endowed-property" target="_blank" rel="noopener">دیوار — اتاق خبر</a> و <a href="https://kilid.com/mag/buy-and-rent-advice/legal-training-and-advice/2184/" target="_blank" rel="noopener">کیلید</a></li>
</ul>'''

html = open('output/report.html', encoding='utf-8').read()
html = html.replace('<!--__VERDICT__-->', verdict_html).replace('<!--__SUBURBS__-->', suburbs_html).replace('<!--__METHOD__-->', method_html)
open('output/report.html', 'w', encoding='utf-8').write(html)
print('narrative injected')
