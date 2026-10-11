"""Developer feasibility (residual land value) for every tracked residential land asset in Mashhad.

Input : data/assets.json
Output: data/valuation.json
All money in toman unless the key ends with _rial.
"""
import json
import re
import sys

sys.path.insert(0, 'scripts')
from locations import LOC  # noqa: E402
from market import (BASEMENT_COST_FACTOR, BUILDER_TARGET, CONTINGENCY, LAND_TXN, MONTHS,  # noqa: E402
                    NET_TO_GROSS, OCCUPANCY, P_NEW, PARK_BASEMENT_M2, PARK_GROUND_M2,
                    PARTNER_BUILDER_SHARE, PILOTI_COST_FACTOR, SALE_HAIRCUT, SELLING, PERMIT_GDV, ENGINEERING,
                    EXTRA_FLOOR_FEE,
                    TARGET_PROFIT, OWNER_TARGET, hard_cost_per_m2, installment_pv_factor, unit_size, LAND_MKT)

# Plot facts read from the auction sketches (کروکی) and notices, keyed by sketch image id of the latest listing.
# floors: permitted floors over pilotis; far: explicit FAR when printed; shape: usable-area factor;
# adj: sale-price adjustment for plot qualities; notes shown in the report.
PLOT = {
    # Emamat 74 batch (stage 26): "مسکونی تراکم زیاد گونه ۲", 12 m frontage, 14-20 m planned streets
    **{k: dict(floors=6, notes='تراکم زیاد گونه ۲ (۶ طبقه)، بر ۱۲ متر روی معبر طرح ۱۴ تا ۲۰ متری')
       for k in (11802, 11803, 11805, 11806, 11807, 11808, 11809, 11810, 11811, 11812, 11813)},
    11801: dict(floors=6, notes='تراکم زیاد گونه ۲؛ بر ۱۲ متر روی دوربرگردان معبر ۱۴ و کوچه ۶ متری'),
    11804: dict(floors=6, adj=0.04, notes='دونبش (۱۴ و ۱۲ متری طرح)، تراکم زیاد گونه ۲ — جلال آل‌احمد ۷۱'),
    # Emamat 47 batch: "تراکم متوسط گونه ۲", 15 m frontage, two frontages (12 m + 18/19 m planned)
    11818: dict(floors=5, adj=0.03, notes='دوبر (۱۲ و ۱۸ متری طرح)، مجاور بوستان مادر و کودک، تراکم متوسط گونه ۲'),
    11819: dict(floors=5, adj=0.03, notes='سه‌بر (۱۲ و ۱۸ متری + کوچه ۶)، مجاور بوستان، تراکم متوسط گونه ۲'),
    11816: dict(floors=5, adj=0.02, notes='دوبر (۱۲ و ۱۹ متری)، تراکم متوسط گونه ۲، نیمه‌محصور'),
    11814: dict(floors=5, adj=0.02, notes='دوبر، تراکم متوسط گونه ۲'),
    11815: dict(floors=5, adj=0.02, notes='دوبر، تراکم متوسط گونه ۲'),
    11817: dict(floors=5, adj=0.02, notes='دوبر، تراکم متوسط گونه ۲'),
    # Janbaz 13 (Vesal), district 2, "تراکم متوسط گونه ۱"
    11820: dict(floors=5, notes='تجمیع دو قطعه ۲۲×۲۲ روی معبر ۱۵ متری، تراکم متوسط'),
    11821: dict(floors=4, notes='۲۲×۲۲ روی معبر ۱۰ متری، تراکم متوسط گونه ۱'),
    11822: dict(floors=4, notes='۲۲×۲۲، تراکم متوسط (عرض معبر نامشخص)'),
    11791: dict(floors=4, notes='بر ۱۰ متر × عمق ۳۳ روی معبر ۱۰ متری (اراضی معجونی)'),
    # Abshar 2, district 8: FAR 230% printed on sketch
    11797: dict(far=2.30, notes='۲۳×۳۵ روی خیابان ۱۴ متری، تراکم ۲۳۰٪'),
    11798: dict(far=2.30, notes='۲۳×۳۵ روی خیابان ۱۴ متری، تراکم ۲۳۰٪'),
    11800: dict(far=2.30, adj=0.03, notes='دونبش (۱۸ و ۲۰ متری)، مجاور پارکینگ، تراکم ۲۳۰٪'),
    11799: dict(far=2.30, risk=0.10, notes='۴۶×۳۴ با دسترسی از سمت پارکینگ به خیابان ۲۰ متری؛ کاربری قانونی «نامشخص» در کروکی'),
    11845: dict(floors=4, notes='۲۰۱۷ م، چهاربر (۸، ۶ و دو ممر ۱۲ متری)، طرح تفصیلی جنوب‌غرب: تراکم متوسط گونه ۱ — امکان ۵ طبقه با تجمیع/تشویقی'),
    11833: dict(floors=4, shape=0.85, notes='مثلثی روی بلوار ۴۵ متری مهدیه + کوچه ۶ متری؛ تراکم نامشخص'),
    11830: dict(floors=3, notes='۱۲×۲۲ روی دوربرگردان؛ تراکم کم'),
    11832: dict(floors=3, notes='بلوک ۳۴؛ تراکم کم'),
    11834: dict(floors=3, notes='بلوک ۳۴؛ تراکم کم'),
    11835: dict(floors=3, notes='۱۲×۲۵ روی خیابان ۱۲ متری؛ تراکم کم'),
    11831: dict(floors=4, notes='۱۲×۲۴ روی دوربرگردان ۱۸ متری؛ تراکم درج نشده'),
    11843: dict(floors=4, adj=0.03, notes='دونبش (۱۰ و ۱۲ متری)، روبه‌روی فضای سبز، تراکم متوسط گونه ۱ (بلوار حر)'),
    11842: dict(floors=4, notes='۱۰×۲۵ روی خیابان ۱۰ متری، تراکم متوسط'),
    11840: dict(floors=4, notes='۱۰×۲۰ روی خیابان ۲۰ متری، تراکم متوسط گونه ۲ (تیپ ۳)'),
    11841: dict(floors=4, notes='۱۰×۲۰، تراکم متوسط گونه ۲'),
    11789: dict(floors=3, notes='۸×۲۳ روی خیابان ۱۰ متری'),
    11790: dict(floors=3, notes='۸×۲۳ روی خیابان ۱۰ متری'),
    11795: dict(floors=4, notes='اراضی کشف'),
    11796: dict(floors=4, notes='اراضی کشف'),
    11786: dict(floors=3, adj=-0.07, notes='۱۳۸ م (۱۰٫۵×۱۳)، روبه‌روی حریم خط فشار قوی؛ قطعه کوچک'),
    11785: dict(floors=4, shape=0.85, notes='مثلثی (۲۱۳ و ۲۱۴) روی معابر ۱۰ و ۱۵ متری با عقب‌نشینی'),
    # ---- suburbs (active, stage 26) ----
    11774: dict(floors=3, notes='سه قطعهٔ ۸×۲۵ تجمیعی روی خیابان ۱۲ متری (چاه خاصه)'),
    11778: dict(floors=3, notes='۸×۲۵ روی خیابان ۱۲ متری (چاه خاصه)'),
    11847: dict(floors=4, notes='۱۰٫۵×۲۴ روی خیابان ۱۲ متری طرح؛ مسکونی تراکم متوسط (نشانی کروکی: بهمن ۴/۳۹)'),
    11836: dict(floors=4, notes='۱۵×۲۰ روی خیابان ۲۴ متری؛ طرح تفصیلی شهرک رضویه، تراکم زیاد'),
    11837: dict(floors=4, notes='۱۵×۲۰ روی خیابان ۲۴ متری؛ طرح تفصیلی شهرک رضویه، تراکم زیاد'),
    11775: dict(floors=2, notes='سه قطعهٔ تجمیعی روی خیابان ۱۲ متری (روستای قلعه سیاه)'),
    11788: dict(floors=2, notes='روستای قلعه سیاه'),
    # ---- stage 27 (1405/07/19) ----
    11881: dict(floors=6, notes='۱۲×۲۴٫۸ روی خیابان ۲۰ متری، تراکم زیاد گونه ۲ (۶ طبقه)'),
    11882: dict(floors=6, notes='۱۲×۲۴٫۸ روی خیابان ۲۰ متری، تراکم زیاد گونه ۲ (۶ طبقه)'),
    11877: dict(floors=5, adj=0.03, notes='۱۵×۳۶ دوبر (خیابان ۳۵ متری و ۱۲ متری طرح)، نزدیک بوستان مادر و کودک، تراکم متوسط گونه ۲'),
    11878: dict(floors=5, adj=0.03, notes='۱۵×۳۶ دوبر (خیابان ۳۵ متری و ۱۲ متری طرح)، نزدیک بوستان مادر و کودک، تراکم متوسط گونه ۲'),
    11875: dict(floors=5, adj=0.02, notes='۱۵×۳۴ دوبر (خیابان ۱۸ متری طرح و دوربرگردان)، تراکم متوسط گونه ۲'),
    11918: dict(floors=4, notes='۹٫۵×۲۷ روی خیابان ۱۰ متری، تراکم متوسط گونه ۱ (تیپ ۳)'),
    11917: dict(floors=4, notes='۹٫۵×۲۷ روی خیابان ۱۰ متری، تراکم متوسط گونه ۱ (تیپ ۳)'),
    11916: dict(floors=4, notes='دونبش (۱۰ و ۱۲ متری) با پخ؛ روبه‌روی گرمخانه؛ تراکم متوسط گونه ۱'),
    11915: dict(floors=4, notes='دونبش (۱۰ و ۱۲ متری) با پخ؛ روبه‌روی گرمخانه و کاربری مذهبی؛ تراکم متوسط گونه ۱'),
    11889: dict(floors=4, adj=0.03, notes='۶۴۳ م سه‌بر (خیابان ۲۵، ۱۸ و ۶ متری + دوربرگردان)؛ تراکم درج نشده'),
    11891: dict(floors=3, notes='۱۲×۲۵ روی خیابان ۱۲ متری؛ تراکم درج نشده، قطعهٔ ۱۲ همین بلوک (۳۱) تراکم کم دارد'),
    11893: dict(floors=3, notes='۱۲×۲۵ روی خیابان ۱۴ متری؛ تراکم درج نشده، قطعهٔ ۱۲ همین بلوک (۳۱) تراکم کم دارد'),
    11892: dict(floors=3, adj=0.03, risk=0.03, notes='دونبش (۱۲ و ۱۴ متری)؛ بلوک ۳۱ تراکم کم؛ اصلاحات اراضی: استعلام گردد'),
    11894: dict(floors=3, adj=0.03, notes='دونبش (۱۴ و ۱۴ متری) با پخ؛ تراکم کم (درج در کروکی)'),
    11890: dict(floors=4, notes='۱۲×۲۶ روی دوربرگردان خیابان ۱۲ متری، نزدیک بلوار مهدیه؛ تراکم درج نشده'),
    11888: dict(floors=4, adj=0.03, risk=0.03, notes='دونبش (۱۸ و ۱۴ متری) با پخ؛ تراکم درج نشده؛ اصلاحات اراضی: استعلام گردد'),
    11913: dict(far=2.30, notes='۱۶۷۲ م روی دوربرگردان خیابان ۱۴ متری و ممر ۶ متری مشرف به فضای سبز؛ تراکم ۲۳۰٪'),
    11911: dict(far=2.30, risk=0.03, notes='۲۴×۴۱ روی خیابان ۱۴ متری؛ تراکم ۲۳۰٪؛ اصلاحات اراضی: استعلام گردد'),
    11899: dict(floors=4, notes='تجمیع دو قطعه ۲۲×۲۲٫۷ روی خیابان ۱۰ متری، تراکم متوسط گونه ۱ تیپ ۱'),
    11895: dict(floors=4, notes='تجمیع دو قطعه ۲۲×۲۲٫۴ روی خیابان ۱۰ متری، تراکم متوسط گونه ۱ تیپ ۱'),
    11896: dict(floors=4, notes='تجمیع دو قطعه ۲۲×۲۲٫۵ روی خیابان ۱۰ متری، تراکم متوسط گونه ۱ تیپ ۱'),
    11897: dict(floors=4, notes='تجمیع دو قطعه ۲۲×۲۲٫۵ روی خیابان ۱۰ متری، تراکم متوسط گونه ۱ تیپ ۱'),
    11898: dict(floors=4, notes='تجمیع دو قطعه ۲۲×۲۲٫۶ روی خیابان ۱۰ متری، تراکم متوسط گونه ۱ تیپ ۱'),
    11923: dict(floors=4, risk=0.03, notes='۱۵×۲۰ روی خیابان ۲۴ متری؛ طرح تفصیلی شهرک رضویه فاز ۲، تراکم متوسط؛ اصلاحات اراضی: استعلام گردد'),
    11921: dict(floors=4, notes='۱۵×۲۰ روی خیابان ۲۴ متری؛ طرح تفصیلی شهرک رضویه فاز ۲، تراکم زیاد'),
    11922: dict(floors=4, notes='۱۵×۲۰ روی خیابان ۲۴ متری؛ طرح تفصیلی شهرک رضویه فاز ۲، تراکم زیاد'),
    11924: dict(floors=4, notes='۱۵×۲۰ روی خیابان ۱۲ متری؛ طرح تفصیلی شهرک رضویه فاز ۲، تراکم متوسط'),
    11855: dict(floors=3, notes='۸×۲۵ روی خیابان ۱۲ متری (چاه خاصه)؛ شرط پرداخت این قطعه ۵۰٪ نقد + دو چک'),
    11856: dict(floors=3, notes='۸×۲۵ روی خیابان ۱۲ متری (چاه خاصه)؛ شرط پرداخت این قطعه ۵۰٪ نقد + دو چک'),
    11870: dict(floors=3, shape=0.52, risk=0.15,
                notes='۸×۲۷٫۷ روی خیابان ۱۲ متری؛ ۱۰۵ متر از ۲۲۰ متر در مسیر معبر است (فقط حدود ۱۱۵ متر قابل استفاده)؛ واگذاری خام و بدون مجوز جهاد کشاورزی'),
    # Sajjad / Akhavan-e Sales 4: permit in hand, FAR 750% (notice), mixed commercial-residential tower
    10691: dict(far=7.5, floors=27, cost_mult=1.35, net_ratio=0.78,
                notes='دارای پروانه برج تجاری‌مسکونی ۲۷ طبقه، تراکم ۷۵۰٪ (طبق اطلاعیه)؛ هزینه برج +۳۵٪ و راندمان ۷۸٪'),
}

DEFAULT_FLOORS = 4


def plot_facts(a):
    m = re.search(r'korokiImage(\d+)', a.get('koroki') or '')
    kid = int(m.group(1)) if m else None
    # facts are keyed by the sketch id of the listing that was reviewed; a relisted plot gets a new sketch id,
    # so look through all listing ids of the asset (newest first)
    hit = next((i for i in [kid] + sorted((i for i in a['ids'] if i), reverse=True) if i in PLOT), None)
    f = dict(PLOT.get(hit, {}))
    meta = LOC.get(a['loc'], {})
    if 'floors' not in f and 'far' not in f:
        fl = meta.get('floors') or DEFAULT_FLOORS
        if (a['area'] or 0) < 200:
            fl = min(fl, 3)                      # small plots cannot park/serve more units
        f['floors'] = fl
    return kid, f


def appraise(area, rate_toman, loc, facts, premium=0.0, extra_floor=False, cost_k=1.0, price_k=1.0):
    """Physical program + two business models for one plot at a given land price per m2 (toman).

    Physical program (Mashhad medium/high density residential):
      footprint = area x occupancy (60%) x shape factor; floors over pilotis from the sketch / zoning;
      gross residential = footprint x floors (or area x printed FAR); sellable net = 85% of gross;
      units = net / typical unit size; parking 1 space per unit -> pilotis capacity, else a basement.
    A) self-develop: buyer pays land + all construction.
    B) partnership: buyer contributes the land only; builder pays construction, permits and fees,
       sellable area split 60% builder / 40% landowner (the user's terms).
    """
    p_new, p_src, p_conf = P_NEW[loc]
    shape = facts.get('shape', 1.0)
    if facts.get('far'):
        far = facts['far']
        floors = facts.get('floors') or max(1, round(far / OCCUPANCY))
    else:
        floors = facts['floors']
        far = OCCUPANCY * floors
    if extra_floor:
        floors += 1
        far += OCCUPANCY
    footprint = area * OCCUPANCY * shape
    gross = area * far * shape
    net = gross * facts.get('net_ratio', NET_TO_GROSS)
    usize = unit_size(p_new)
    units = max(floors, round(net / usize))
    ground_spaces = int(footprint // PARK_GROUND_M2)
    need_basement = units > ground_spaces
    basement = (units - ground_spaces) * PARK_BASEMENT_M2 if need_basement else 0.0
    basement = min(basement, area * 0.9) if need_basement else 0.0

    sale_ppm = p_new * SALE_HAIRCUT * (1 + facts.get('adj', 0.0)) * price_k
    gdv = net * sale_ppm
    hc = hard_cost_per_m2(p_new) * cost_k * facts.get('cost_mult', 1.0)
    hard = (gross + footprint * PILOTI_COST_FACTOR + basement * BASEMENT_COST_FACTOR) * hc
    extra_fee = (area * OCCUPANCY * shape * NET_TO_GROSS * sale_ppm * EXTRA_FLOOR_FEE) if extra_floor else 0.0
    soft = gdv * PERMIT_GDV + hard * ENGINEERING + extra_fee
    cont = hard * CONTINGENCY
    sell = gdv * SELLING
    build_cost = hard + soft + cont                    # everything except land and selling
    land = area * rate_toman * (1 + premium) * (1 + LAND_TXN)
    total = land + build_cost + sell
    profit = gdv - total
    margin = profit / total if total else None
    land_max = gdv / (1 + TARGET_PROFIT) - (build_cost + sell)
    rlv = land_max / (area * (1 + LAND_TXN)) if area else None
    breakeven_ppm = total / net if net else None
    years = MONTHS / 12

    def stress(price_k, cost_k):
        g = gdv * price_k
        t = land + build_cost * cost_k + g * SELLING
        return (g - t) / t

    # ---- B) partnership 60/40 ----
    bs = PARTNER_BUILDER_SHARE
    owner_m2, builder_m2 = net * (1 - bs), net * bs
    owner_value = owner_m2 * sale_ppm
    owner_cost = land
    owner_ret = owner_value / owner_cost - 1 if owner_cost else None
    p_years = (MONTHS + 3) / 12                        # +3 months to sign a builder
    owner_ann = (1 + owner_ret) ** (1 / p_years) - 1 if owner_ret is not None and owner_ret > -1 else None
    owner_cost_per_m2 = owner_cost / owner_m2 if owner_m2 else None   # what each received m2 costs the owner
    pv = installment_pv_factor()
    owner_cost_eff = owner_cost * pv                   # 40% now + 2 interest-free 6-month cheques
    owner_ret_eff = owner_value / owner_cost_eff - 1 if owner_cost_eff else None
    owner_ann_eff = (1 + owner_ret_eff) ** (1 / p_years) - 1 if owner_ret_eff is not None and owner_ret_eff > -1 else None
    builder_rev = builder_m2 * sale_ppm
    builder_cost = build_cost + builder_rev * SELLING
    builder_margin = builder_rev / builder_cost - 1 if builder_cost else None
    # builder share that gives the builder exactly its target margin -> fair owner share
    bs_needed = (build_cost * (1 + BUILDER_TARGET)) / (gdv * (1 - (1 + BUILDER_TARGET) * SELLING)) if gdv else None
    owner_fair = 1 - bs_needed if bs_needed is not None else None
    owner_fair_value = net * max(0.0, owner_fair or 0) * sale_ppm
    owner_fair_ret = owner_fair_value / owner_cost - 1 if owner_cost else None
    # realistic owner share: 40% if a builder still earns its target at 60/40, else the fair share
    owner_real_share = min(1 - bs, max(0.0, owner_fair)) if owner_fair is not None else 0.0
    owner_real_value = net * owner_real_share * sale_ppm
    owner_real_ret_eff = owner_real_value / owner_cost_eff - 1 if owner_cost_eff else None
    owner_real_ann_eff = ((1 + owner_real_ret_eff) ** (1 / p_years) - 1
                          if owner_real_ret_eff is not None and owner_real_ret_eff > -1 else None)
    # maximum sensible bid per m2 of land (toman) for a landowner who wants OWNER_TARGET at the realistic share
    max_bid_partner = owner_real_value / ((1 + OWNER_TARGET) * pv * (1 + LAND_TXN) * area) if area else None
    max_bid_dev = rlv * 1.0 if rlv else None

    return dict(
        p_new=p_new, p_src=p_src, p_conf=p_conf,
        occupancy=OCCUPANCY, floors=floors, far=round(far * shape, 2), shape=shape,
        footprint_m2=round(footprint), gross_m2=round(gross), net_m2=round(net),
        unit_size=usize, units=units, parking_ground=ground_spaces,
        basement_m2=round(basement), need_basement=need_basement,
        sale_ppm=sale_ppm, gdv=gdv, hard_ppm=hc, hard=hard, soft=soft + cont, selling=sell,
        build_cost=build_cost, build_cost_per_net=build_cost / net if net else None,
        land_cost=land, total_cost=total, profit=profit, margin=margin,
        annual_return=((1 + margin) ** (1 / years) - 1) if margin is not None and margin > -1 else None,
        rlv_ppm=rlv, headroom=(rlv / (rate_toman * (1 + premium)) - 1) if rate_toman else None,
        land_share_gdv=land / gdv if gdv else None,
        land_per_net_m2=land / net if net else None,
        breakeven_ppm=breakeven_ppm, safety=(sale_ppm / breakeven_ppm - 1) if breakeven_ppm else None,
        margin_stress=stress(0.90, 1.15), margin_upside=stress(1.10, 0.90),
        # partnership
        owner_m2=round(owner_m2), builder_m2=round(builder_m2), owner_units=owner_m2 / usize,
        owner_value=owner_value, owner_ret=owner_ret, owner_ann=owner_ann,
        owner_cost_eff=owner_cost_eff, owner_ret_eff=owner_ret_eff, owner_ann_eff=owner_ann_eff,
        owner_cost_per_m2=owner_cost_per_m2,
        owner_discount_to_market=(1 - owner_cost_per_m2 / sale_ppm) if owner_cost_per_m2 else None,
        builder_rev=builder_rev, builder_cost=builder_cost, builder_margin=builder_margin,
        builder_ok=(builder_margin is not None and builder_margin >= BUILDER_TARGET),
        owner_fair_share=owner_fair, owner_fair_ret=owner_fair_ret,
        owner_real_share=owner_real_share, owner_real_value=owner_real_value,
        owner_real_ret_eff=owner_real_ret_eff, owner_real_ann_eff=owner_real_ann_eff,
        max_bid_partner=max_bid_partner, max_bid_dev=max_bid_dev,
    )


assets = json.load(open('data/assets.json', encoding='utf-8'))

# expected auction premium per location from the published winners (median), default 3%
prem_by_loc = {}
for a in assets:
    if a.get('win_premium') is not None:
        prem_by_loc.setdefault(a['loc'], []).append(a['win_premium'])
EXP_PREM = {k: sorted(v)[len(v) // 2] for k, v in prem_by_loc.items() if len(v) >= 3}

out = []
for a in assets:
    if a['scope'] not in ('city', 'edge', 'town') or a['kind'] not in ('land', 'large_parcel') or a['loc'] not in P_NEW:
        continue
    if not a['area'] or not a['rate_last']:
        continue
    kid, facts = plot_facts(a)
    exp_prem = EXP_PREM.get(a['loc'], 0.03)
    if a['status'] == 'active':
        basis, rate_rial, prem = 'قیمت پایه فعلی + اضافه‌پرداخت مورد انتظار', a['rate_last'], exp_prem
    elif a['status'] == 'sold':
        basis, rate_rial, prem = 'قیمت پرداختی برنده', a['win_price'], 0.0
    else:
        basis, rate_rial, prem = 'آخرین قیمت پایه', a['rate_last'], 0.0
    v = appraise(a['area'], rate_rial / 10, a['loc'], facts, prem)
    vx = appraise(a['area'], rate_rial / 10, a['loc'], facts, prem, extra_floor=True)
    for k in ('floors', 'net_m2', 'units', 'margin', 'headroom', 'rlv_ppm', 'owner_m2', 'owner_ret',
              'owner_ann', 'owner_cost_per_m2', 'builder_margin', 'owner_fair_share', 'profit', 'gdv',
              'owner_real_share', 'owner_real_ret_eff', 'owner_real_ann_eff', 'max_bid_partner', 'far',
              'gross_m2', 'basement_m2'):
        v['x_' + k] = vx[k]
    vo = appraise(a['area'], rate_rial / 10, a['loc'], facts, prem, cost_k=0.85, price_k=1.10)
    vp = appraise(a['area'], rate_rial / 10, a['loc'], facts, prem, cost_k=1.15, price_k=0.90)
    for k in ('margin', 'builder_margin', 'owner_real_share', 'owner_real_ret_eff', 'max_bid_partner', 'rlv_ppm'):
        v['opt_' + k] = vo[k]
        v['pes_' + k] = vp[k]
    # same plot valued at today's base level of its location (for lots that left the auction)
    lm = LAND_MKT.get(a['loc'])
    if lm:
        paid = rate_rial / 10 * (1 + prem)
        v.update(land_mkt=lm[0], land_mkt_src=lm[1], land_mkt_conf=lm[2], vs_land_mkt=paid / lm[0] - 1)
    v.update(asset=a['asset'], koroki_id=kid, basis=basis, exp_premium=prem,
             land_rate_toman=rate_rial / 10, plot_notes=facts.get('notes', ''),
             risk_extra=facts.get('risk', 0.0), facts=facts, in_plot=bool(set(a['ids']) & set(PLOT)))
    out.append(v)

json.dump(out, open('data/valuation.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('valued', len(out), '| expected premium by loc:', {k: round(v, 3) for k, v in EXP_PREM.items()})
print('installment PV factor @35%:', round(installment_pv_factor(), 3))
