"""Market references (Mehr 1405) and development assumptions for Mashhad residential lots.

P_NEW: asking price of new-build apartments (built 1401+), toman per m2 of sellable area.
  Primary source: Divar listings scraped 1405/07/16 (median of 1401+ builds per neighborhood query).
  Fallbacks: Ariamarz neighborhood averages (Mehr 1405, all ages) x1.10 new-build premium, or Baztab.
"""

# loc -> (toman per m2, source, confidence)
P_NEW = {
    # Emamat 47 lots sit at the Amouzegar end of Emamat Blvd -> blend of Emamat (200) and Amouzegar (153)
    'emamat47':      (175e6, 'دیوار: امامت نوساز ۲۰۰ و آموزگار نوساز ۱۵۳ (قطعات در انتهای امامت سمت آموزگار)', 'high'),
    'emamat74':      (195e6, 'دیوار: امامت/جلال آل‌احمد نوساز ۱۴۰۱+ (۱۱ آگهی، میانه ۲۰۰؛ آگهی «صفر امامت+جلال» ۱۹۰)', 'high'),
    # Baharestan 15 is at the edge of Rezashahr (Kaveh/Naseri Blvd) -> below the Rezashahr median of 200
    'rezashahr':     (175e6, 'دیوار: رضاشهر نوساز میانه ۲۰۰ (۱۳۶ تا ۲۵۰)؛ برای انتهای بهارستان ۱۵ با ۱۲٪ کسر', 'medium'),
    'faramarz46':    (191e6, 'دیوار: فرامرز عباسی نوساز (۱۲ آگهی)', 'high'),
    'rahnamaei3':    (265e6, 'دیوار: راهنمایی نوساز (۷ آگهی)', 'medium'),
    'sajjad_akhavan': (260e6, 'آریامرز: سجاد ۲۳۶ × ۱٫۱ (برج نوساز)', 'medium'),
    'amouzegar':     (153e6, 'دیوار: آموزگار/سیدرضی/تربیت نوساز (۷ آگهی)', 'medium'),
    'seyedrazi65':   (175e6, 'آریامرز: سید رضی ۱۶۱ × ۱٫۱', 'medium'),
    'kouhsangi':     (180e6, 'آریامرز: پارک کوهسنگی ۱۶۴ × ۱٫۱', 'medium'),
    'jalal66':       (165e6, 'بازتاب: جلال آل احمد ۱۵۱ × ۱٫۱', 'low'),
    'kooshesh':      (140e6, 'دیوار: کوشش نوساز (۱۴ آگهی)', 'high'),
    'mahdi39':       (150e6, 'آریامرز: مهدی ۱۳۸ × ۱٫۱', 'low'),
    'fakouri':       (121e6, 'دیوار: فکوری نوساز (۵ آگهی)', 'medium'),
    'abshar2':       (115e6, 'آریامرز: آبشار ۱۰۶ × ۱٫۱ (دیوار کم‌نمونه)', 'medium'),
    'mahdieh':       (110e6, 'دیوار: بلوار مهدیه/الهیه نوساز (۱۸ آگهی)', 'high'),
    'mahdieh_apt':   (110e6, 'دیوار: بلوار مهدیه/الهیه نوساز (۱۸ آگهی)', 'high'),
    'amiriyeh':      (105e6, 'آریامرز: امیریه ۹۵ × ۱٫۱', 'medium'),
    'mousavi':       (95e6,  'آریامرز: موسوی قوچانی ۸۶٫۵ × ۱٫۱', 'medium'),
    'janbaz13':      (81e6,  'دیوار: جانباز/وصال نوساز (۱۳ آگهی)', 'high'),
    'zolfaghar':     (110e6, 'برآورد: اراضی آبکوه', 'low'),
    'abdolmotalleb': (78e6,  'دیوار: عبدالمطلب نوساز (۱۱ آگهی)', 'high'),
    'tollab':        (70e6,  'دیوار: طلاب نوساز (۱۲ آگهی)', 'high'),
    'rostami':       (70e6,  'آریامرز: شهید رستمی ۶۴٫۵ × ۱٫۱', 'medium'),
    'seyedabadi25':  (60e6,  'برآورد (محله مبهم)', 'low'),
    'sajedi':        (60e6,  'برآورد (محله مبهم)', 'low'),
    'basirat':       (58e6,  'دیوار: امیرآباد/معقول (حوالی بصیرت) + آریامرز منطقه ۶', 'medium'),
    'baghdar':       (57e6,  'آریامرز: آقا مصطفی خمینی ۵۲ × ۱٫۱', 'medium'),
    'mostafa_khomeini': (57e6, 'آریامرز: آقا مصطفی خمینی ۵۲ × ۱٫۱', 'medium'),
    'sepah64':       (52e6,  'دیوار: شهرک بهارستان/سپاه نوساز (۶ آگهی)', 'high'),
    'seyedi':        (52e6,  'دیوار: کوی سیدی نوساز (۹ آگهی)', 'high'),
    'hor41':         (55e6,  'برآورد: منطقه ۶', 'low'),
    'velayat':       (60e6,  'برآورد', 'low'),
    'yousefzadeh':   (60e6,  'برآورد', 'low'),
    'khoshsima':     (60e6,  'برآورد', 'low'),
    'pourazad':      (60e6,  'برآورد', 'low'),
    'khaghani':      (60e6,  'برآورد', 'low'),
    'dehnow':        (45e6,  'دیوار: صاحب‌الزمان/منزل‌آباد نوساز (۱۲ آگهی)', 'medium'),
    'poursina':      (47e6,  'آریامرز: پورسینا ۴۳ × ۱٫۱', 'medium'),
    'ansar':         (41e6,  'دیوار: انصار (۷ آگهی، پراکنده)', 'medium'),
    'kashf':         (30e6,  'دیوار: مهدی‌آباد (بلوار توس) (۱۱ آگهی)', 'medium'),
    'toroq':         (28e6,  'دیوار: رباط طرق (۱۰ آگهی)', 'medium'),
    'emam_ali':      (29e6,  'آریامرز: امام علی ۲۶٫۴ × ۱٫۱', 'medium'),
    'deh_gheybi':    (175e6, 'آریامرز: امام رضا ۱۶۰ × ۱٫۱', 'low'),
    # ---- suburbs (Divar city pages, 1405/07/16) ----
    'torghabeh':     (74e6,  'دیوار طرقبه: آپارتمان ساخت ۱۴۰۲+ (۵۲–۸۵، میانه ~۷۴)', 'medium'),
    'chah_khase':    (44e6,  'دیوار شاندیز: آپارتمان ساخت ۱۴۰۰+ (۴۰–۴۶ غالب؛ میانه ~۴۴) — برای محور شاندیز/سجادشهر', 'low'),
    'golbahar':      (49e6,  'دیوار گلبهار: آپارتمان ساخت ۱۴۰۲+ (۳۸–۶۶، میانه ~۴۹)', 'medium'),
    'kalate_bougha': (60e6,  'آریامرز: کوی بهمن ۶۰ (نشانی کروکی «بهمن ۴/۳۹»)', 'low'),
    'razavieh':      (28e6,  'برآورد: شهرک رضویه (داده دیوار در دسترس نبود)', 'low'),
    'ghale_siah':    (25e6,  'برآورد: روستای حاشیه', 'low'),
}

# --- development assumptions (Mehr 1405, toman) ---
OCCUPANCY = 0.60            # ground coverage
NET_TO_GROSS = 0.85         # sellable / gross residential floor area
PILOTI_COST_FACTOR = 0.60   # pilotis/parking floor priced at 60% of a typical floor
PERMIT_GDV = 0.035          # municipal permit fees (عوارض پروانه، آتش‌نشانی، قطار شهری...) ~3.5% of project value
ENGINEERING = 0.08          # design, supervision (نظام مهندسی), social-security insurance, utility connections (share of hard)
EXTRA_FLOOR_FEE = 0.25      # fee to buy one extra floor (طبقه مازاد), as a share of that floor's sale value
CONTINGENCY = 0.05          # of hard cost
SELLING = 0.02              # of GDV
LAND_TXN = 0.01             # registration / auction-hall costs on land
SALE_HAIRCUT = 0.90         # asking->transaction gap (5%) and endowment-land (موقوفه) discount (5%)
TARGET_PROFIT = 0.25        # developer's required profit on total cost (for residual land value)
OWNER_TARGET = 0.15         # landowner's minimum real return (on effective land cost) to justify the bid
MONTHS = 30                 # 6 months permit + 24 months build
CAPITAL_COST = 0.35         # nominal annual cost of capital, used only for the payment-plan comparison


PARTNER_BUILDER_SHARE = 0.60  # user's partnership split: builder 60% / landowner 40% of sellable area
BUILDER_TARGET = 0.25         # minimum profit-on-cost a builder needs to sign
PARK_GROUND_M2 = 27           # gross m2 per parking space on the pilotis floor (25 m2 + circulation)
PARK_BASEMENT_M2 = 32         # per space in basement (30 m2 + ramp share)
BASEMENT_COST_FACTOR = 1.25   # basement costs more than a typical floor (excavation, retaining walls)


def unit_size(p_new):
    """Typical new-build unit size (m2 net) the local market absorbs."""
    if p_new >= 150e6:
        return 130
    if p_new >= 90e6:
        return 115
    if p_new >= 55e6:
        return 100
    return 85


def hard_cost_per_m2(p_new):
    """Construction hard cost per gross m2 by market tier (quality follows the market)."""
    # calibrated to: national 5-storey average ~60M all-in (Kanoon Anbouhsazan, Mordad 1405) and
    # Mashhad 45-55M build cost; these are hard costs per gross m2, soft costs are added on top.
    if p_new >= 180e6:
        return 50e6
    if p_new >= 120e6:
        return 46e6
    if p_new >= 70e6:
        return 42e6
    return 35e6


def installment_pv_factor(rate=CAPITAL_COST):
    """PV of the standard plan: 40% at award + 30% at 6 months + 30% at 12 months."""
    return 0.4 + 0.3 / (1 + rate) ** 0.5 + 0.3 / (1 + rate)


# Open-market LAND asking price (زمین/کلنگی), toman per m2 of land, Divar 1405/07/16, filtered for brokers
# re-advertising auction lots and obvious mis-priced ads. Used for the sales-comparison check.
LAND_MKT = {
    'emamat47':  (170e6, 'دیوار: قطعات ۵۴۰–۵۶۵ متری داخلی امامت ۴x (۱۵۲، ۱۷۰، ۲۰۴)', 'medium'),
    'emamat74':  (182e6, 'دیوار: قطعات ۳۰۰ متری کوچه جلال/زیباشهر (۱۸۰، ۱۸۰، ۱۸۳، ۲۵۰)', 'medium'),
    'kooshesh':  (160e6, 'دیوار: کوشش (موقوفه ۱۴۴؛ ملکی ۱۶۸–۱۸۵؛ بربلوار ۲۶۰+)', 'medium'),
    'rezashahr': (190e6, 'دیوار: رضاشهر ۲۱۲–۲۹۴؛ قطعات خیلی بزرگ ~۱۷۰ (کسر حجم)', 'medium'),
    'janbaz13':  (122e6, 'دیوار: جانباز ۴۹۱–۵۰۰ متری (۱۱۸، ۱۲۲، ۱۲۵)', 'high'),
    'basirat':   (55e6,  'دیوار: امیرآباد/بلوار بصیرت ۴۲–۶۷ (موقوفه ۶۰)', 'medium'),
    'ansar':     (15e6,  'دیوار: انصار ۱۱–۲۶ (میانه ۱۴)', 'high'),
    'kashf':     (15e6,  'دیوار: مهدی‌آباد ۱۰–۲۸ (موقوفه ۱۲–۱۷)', 'medium'),
    'tollab':    (90e6,  'دیوار: طلاب ۷۸–۱۶۹ (موقوفه ۹۹)', 'medium'),
    'fakouri':   (140e6, 'دیوار: فکوری ۱۱۹–۲۲۱؛ با کسر قطعه کوچک و حریم فشار قوی', 'low'),
    'mahdieh':   (65e6,  'دیوار: بلوار مهدیه/امیریه ۴۳–۸۳ (موقوفه ۵۶)', 'medium'),
    'abshar2':   (70e6,  'دیوار: آبادگران/بلوار نماز ۶۶–۷۵ (قطعات ۱۰۰۰+ متری)', 'low'),
    # ---- suburbs ----
    'torghabeh':  (45e6, 'دیوار طرقبه: شهرک مروارید ۴۴–۴۶، ارغوان ۲۱–۵۴، جاغرق ۲۱–۲۲ (بعثت ۹۹)', 'medium'),
    'chah_khase': (16e6, 'دیوار: «زمین مسکونی اراضی چاه‌خاصه شاندیز» ۳۰۰ متر، ۱۶ (موقوفه)', 'medium'),
    'golbahar':   (18e6, 'دیوار گلبهار: زمین مسکونی ۱۰–۲۷', 'medium'),
    'shandiz':    (25e6, 'دیوار شاندیز: زمین ۱۳–۴۵ (میانه ~۲۵)', 'medium'),
}

# Garden land (باغ/زمین باغی) asking price per m2 of land, toman — only for orders of magnitude.
GARDEN_MKT = {
    'naghandar':     (18e6, 'دیوار: باغ ۲۵۰۰ متری بافت نغندر ۱۵٫۶؛ کنگ–نغندر ۵۰۰۰ متر ۲۲', 'medium'),
    'torghabeh':     (25e6, 'دیوار: زمین باغی ۱۴۱۰ متری حاشیه جاده طرقبه ۳۵؛ باغ‌های کوهساران ۳–۳۳', 'low'),
    'chah_khase':    (4e6,  'دیوار: زمین باغی کلاته برفی/شاهنامه ۲–۶؛ ۲۰۰۰ متری قابل ساخت ۱۰', 'low'),
    'chenaran_road': (4e6,  'دیوار: زمین باغی شاهنامه/ناظرآباد ۲–۶', 'low'),
    'mariyan':       (3e6,  'دیوار: زمین باغی سنددار با آب فاز ۳ گلبهار ~۱؛ باغ‌ویلا گلشن ۳۰ (با بنا)', 'low'),
    'ghale_siah':    (2e6,  'برآورد (بدون نمونهٔ مستقیم)', 'low'),
    'akhlamad':      (1e6,  'برآورد (روستای دور)', 'low'),
}
