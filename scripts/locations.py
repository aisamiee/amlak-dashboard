"""Canonical location table for residential auction lots (Mashhad focus).

Each rule: (regex on normalized address, canonical key).
LOC holds metadata per canonical key:
  name      display name
  district  Mashhad municipal district (from notices / ariamarz), or None
  scope     'city' (inside Mashhad), 'edge' (Mashhad fringe / villages inside county),
            'town' (separate town) or 'out' (other city)
  apt       reference new-ish apartment price, toman per m2 (Mehr 1405)
  apt_src   source of apt
  floors    default permitted floors over pilotis (medium density unless noted)
"""
import re

RULES = [
    (r'سجاد.*اخوان', 'sajjad_akhavan'),
    (r'مهدیه\s*۵۹|مهدیه.*واحد|آپارتمان مهدی', 'mahdieh_apt'),
    (r'مهدیه|مهذیه|مهر مادر', 'mahdieh'),
    (r'مهدی\s*ا?آباد|مهدی اباد|کشف', 'kashf'),
    (r'مهدی\s*۳', 'mahdi39'),
    (r'جانباز', 'janbaz13'),
    (r'^امامت$', 'emamat74'),
    (r'امامت\s*۷۴', 'emamat74'),
    (r'امامت', 'emamat47'),
    (r'بصیرت', 'basirat'),
    (r'چاه\s*خاصه', 'chah_khase'),
    (r'انصار', 'ansar'),
    (r'رضوی', 'razavieh'),
    (r'کلاته\s*بوغا', 'kalate_bougha'),
    (r'آبشار|میدان جهاد', 'abshar2'),
    (r'پراکنده|^پک$', 'pack_misc'),
    (r'قلعه سیاه', 'ghale_siah'),
    (r'صید\s*آبادی', 'seyedabadi25'),
    (r'سرخس', 'sarakhs'),
    (r'امام علی', 'emam_ali'),
    (r'دهنو', 'dehnow'),
    (r'راهنمایی', 'rahnamaei3'),
    (r'کوشش|معجونی', 'kooshesh'),
    (r'ساجدی|احمدی', 'sajedi'),
    (r'سپاه', 'sepah64'),
    (r'آموزگار', 'amouzegar'),
    (r'فرامرز', 'faramarz46'),
    (r'طلاب', 'tollab'),
    (r'طرقبه|شهرک بوستان|^بوستان', 'torghabeh'),
    (r'شاندیز', 'shandiz'),
    (r'ماریان', 'mariyan'),
    (r'نغندر', 'naghandar'),
    (r'چناران', 'chenaran_road'),
    (r'گلبهار', 'golbahar'),
    (r'^شهرک صنعتی$|جاده شهرک صنعتی', 'chah_khase'),   # same parcel: «چاه خاصه جاده شهرک صنعتی»
    (r'قزوین', 'qazvin'),
    (r'طرق', 'toroq'),
    (r'سیدی|قائم', 'seyedi'),
    (r'بهارستان|رضاشهر', 'rezashahr'),
    (r'زاک', 'zak'),
    (r'امیریه', 'amiriyeh'),
    (r'پور\s*سینا', 'poursina'),
    (r'ذولفقار|ذوالفقار', 'zolfaghar'),
    (r'یوسف\s*زاده', 'yousefzadeh'),
    (r'خوش\s*سیما', 'khoshsima'),
    (r'عبدالمطلب', 'abdolmotalleb'),
    (r'جلال', 'jalal66'),
    (r'موسوی قوچانی', 'mousavi'),
    (r'ولایت', 'velayat'),
    (r'کوی مصطفی خمینی', 'mostafa_khomeini'),
    (r'کوهسنگی', 'kouhsangi'),
    (r'پورآزاد', 'pourazad'),
    (r'رستمی', 'rostami'),
    (r'ده غیبی', 'deh_gheybi'),
    (r'خاقانی', 'khaghani'),
    (r'حر\s*۷۰', 'ansar'),
    (r'حر|بسکابادی', 'hor41'),
    (r'فکوری', 'fakouri'),
    (r'سید رضی', 'seyedrazi65'),
    (r'کنه بیست', 'kenebist'),
    (r'اخلمد', 'akhlamad'),
    (r'تربت', 'torbat'),
    (r'نیشابور|ازلاعات', 'neyshabur'),
    (r'باغدار', 'baghdar'),
    (r'پک ۲۲ قطعه ای آموزگار', 'amouzegar'),
]

LOC = {
    # ---- inside Mashhad ----
    'sajjad_akhavan': dict(name='بلوار سجاد نبش اخوان ثالث ۴', district=1, scope='city', apt=236.1e6, apt_src='آریامرز: سجاد', floors=27),
    'janbaz13':  dict(name='جانباز ۱۳ (اراضی آبکوه)', district=2, scope='city', apt=134.7e6, apt_src='آریامرز: فرامرز عباسی شرقی (هم‌جوار)', floors=5),
    'emamat47':  dict(name='امامت ۴۷ (آبکوه)', district=11, scope='city', apt=154.9e6, apt_src='بازتاب: امامت', floors=5),
    'emamat74':  dict(name='امامت ۷۴ (آبکوه)', district=11, scope='city', apt=154.9e6, apt_src='بازتاب: امامت', floors=5),
    'rahnamaei3': dict(name='راهنمایی ۳', district=1, scope='city', apt=151.9e6, apt_src='آریامرز: راهنمایی', floors=5),
    'kooshesh':  dict(name='کوشش ۵۲ و ۵۴ (اراضی معجونی)', district=8, scope='city', apt=147.6e6, apt_src='آریامرز: کوشش', floors=4),
    'rezashahr': dict(name='رضاشهر - بهارستان (اراضی ذکریا)', district=9, scope='city', apt=147.2e6, apt_src='آریامرز: رضاشهر', floors=5),
    'abshar2':   dict(name='آبشار ۲ / میدان جهاد', district=8, scope='city', apt=105.8e6, apt_src='آریامرز: آبشار', floors=5),
    'mahdieh':   dict(name='بلوار مهدیه (اراضی منزل‌آباد)', district=12, scope='city', apt=95.0e6, apt_src='آریامرز: الهیه/امیریه (هم‌جوار) + نرخ آپارتمان مهدیه ۵۹ آستان', floors=4),
    'mahdieh_apt': dict(name='آپارتمان مهدیه ۵۹', district=12, scope='city', apt=95.0e6, apt_src='آریامرز: الهیه/امیریه', floors=None),
    'amouzegar': dict(name='آموزگار', district=11, scope='city', apt=138.6e6, apt_src='آریامرز: میانگین منطقه ۱۱', floors=5),
    'faramarz46': dict(name='فرامرز عباسی ۴۶', district=2, scope='city', apt=134.7e6, apt_src='آریامرز: فرامرز عباسی شرقی', floors=5),
    'mahdi39':   dict(name='مهدی ۳۹', district=2, scope='city', apt=138.1e6, apt_src='آریامرز: مهدی', floors=4),
    'mousavi':   dict(name='موسوی قوچانی', district=2, scope='city', apt=86.5e6, apt_src='آریامرز: موسوی قوچانی', floors=5),
    'abdolmotalleb': dict(name='عبدالمطلب ۳۵ و ۳۷', district=2, scope='city', apt=72.1e6, apt_src='آریامرز: حضرت عبدالمطلب', floors=4),
    'fakouri':   dict(name='بین فکوری ۹۴ و ۹۶', district=2, scope='city', apt=84.4e6, apt_src='آریامرز: آیت‌الله عبادی (هم‌جوار)', floors=4),
    'jalal66':   dict(name='جلال آل احمد ۶۶', district=2, scope='city', apt=151.0e6, apt_src='بازتاب: جلال آل احمد', floors=4),
    'seyedrazi65': dict(name='سید رضی ۶۵', district=11, scope='city', apt=160.9e6, apt_src='آریامرز: سید رضی', floors=5),
    'kouhsangi': dict(name='کوهسنگی ۳۸', district=8, scope='city', apt=163.7e6, apt_src='آریامرز: پارک کوهسنگی', floors=5),
    'amiriyeh':  dict(name='امیریه', district=12, scope='city', apt=95.3e6, apt_src='آریامرز: امیریه', floors=4),
    'tollab':    dict(name='طلاب (اراضی محرابخان)', district=4, scope='city', apt=70.1e6, apt_src='آریامرز: طلاب (بازتاب ۵۸٫۲)', floors=4),
    'sepah64':   dict(name='بلوار سپاه ۶۴ (اراضی طرق)', district=7, scope='city', apt=64.1e6, apt_src='آریامرز: قائم (هم‌جوار)', floors=4),
    'seyedi':    dict(name='سیدی / قائم', district=7, scope='city', apt=60.0e6, apt_src='آریامرز: سیدی ۵۵٫۶ / قائم ۶۴٫۱', floors=4),
    'toroq':     dict(name='شهرک طرق (کشاورز ۷)', district=7, scope='city', apt=45.8e6, apt_src='آریامرز: طرق', floors=4),
    'baghdar':   dict(name='کوی مصطفی خمینی - باغدار ۸', district=6, scope='city', apt=51.9e6, apt_src='آریامرز: آقا مصطفی خمینی', floors=4),
    'mostafa_khomeini': dict(name='کوی مصطفی خمینی', district=6, scope='city', apt=51.9e6, apt_src='آریامرز: آقا مصطفی خمینی', floors=4),
    'rostami':   dict(name='رستمی', district=6, scope='city', apt=64.5e6, apt_src='آریامرز: شهید رستمی', floors=4),
    'poursina':  dict(name='پورسینا ۲', district=6, scope='city', apt=42.9e6, apt_src='آریامرز: پورسینا', floors=4),
    'hor41':     dict(name='حر ۴۱ / بسکابادی ۲۸', district=6, scope='city', apt=50.0e6, apt_src='برآورد: میانگین محلات منطقه ۶ (رستمی/پورسینا)', floors=4),
    'ansar':     dict(name='شهرک انصار (حر ۷۰)', district=6, scope='city', apt=29.3e6, apt_src='آریامرز: انصار', floors=4),
    'basirat':   dict(name='بلوار بصیرت (حر)', district=6, scope='city', apt=35.0e6, apt_src='برآورد: بین انصار ۲۹٫۳ و پورسینا ۴۲٫۹', floors=4),
    'kashf':     dict(name='مهدی‌آباد کشف', district=6, scope='city', apt=32.7e6, apt_src='آریامرز: مهدی‌آباد', floors=4),
    'emam_ali':  dict(name='حاشیه بلوار امام علی (ع)', district=10, scope='city', apt=26.4e6, apt_src='آریامرز: امام علی', floors=4),
    'dehnow':    dict(name='دهنو - صاحب‌الزمان (اراضی بیلدر)', district=12, scope='city', apt=60.0e6, apt_src='برآورد محافظه‌کارانه حاشیه منطقه ۱۲', floors=4),
    'seyedabadi25': dict(name='صیدآبادی ۲۵', district=None, scope='city', apt=60.0e6, apt_src='برآورد (محله نامشخص)', floors=4),
    'sajedi':    dict(name='ساجدی - احمدی ۹', district=None, scope='city', apt=60.0e6, apt_src='برآورد (محله نامشخص)', floors=4),
    'zolfaghar': dict(name='ذوالفقار ۶ (اراضی آبکوه)', district=None, scope='city', apt=120.0e6, apt_src='برآورد: اراضی آبکوه', floors=5),
    'yousefzadeh': dict(name='یوسف‌زاده ۶ و ۸', district=None, scope='city', apt=60.0e6, apt_src='برآورد', floors=4),
    'khoshsima': dict(name='خوش‌سیما ۵', district=None, scope='city', apt=60.0e6, apt_src='برآورد', floors=4),
    'velayat':   dict(name='ولایت ۱', district=None, scope='city', apt=60.0e6, apt_src='برآورد', floors=4),
    'pourazad':  dict(name='پورآزاد ۹', district=None, scope='city', apt=60.0e6, apt_src='برآورد', floors=4),
    'khaghani':  dict(name='خاقانی ۱۷', district=None, scope='city', apt=60.0e6, apt_src='برآورد', floors=4),
    'deh_gheybi': dict(name='ده غیبی (امام رضا ۴ و ۶)', district='ثامن', scope='city', apt=160.0e6, apt_src='آریامرز: امام رضا', floors=4),
    'pack_misc': dict(name='پک/قطعات پراکنده (چند محله)', district=None, scope='city', apt=None, apt_src='نامشخص', floors=None),
    # ---- Mashhad fringe / villages ----
    'chah_khase': dict(name='چاه خاصه (حاشیهٔ شمال‌غرب مشهد؛ سجادشهر / جادهٔ شهرک صنعتی توس، محور شاندیز)', district=None, scope='edge', apt=None, apt_src='حاشیه — دیوار: «اراضی چاه‌خاصه شاندیز» در سجادشهر', floors=3),
    'ghale_siah': dict(name='قلعه سیاه', district=None, scope='edge', apt=None, apt_src='روستای حاشیه', floors=2),
    'kalate_bougha': dict(name='کلاته بوغا (۲۲ بهمن)', district=None, scope='edge', apt=None, apt_src='حاشیه', floors=3),
    'kenebist':  dict(name='کنه بیست', district=6, scope='edge', apt=26.6e6, apt_src='آریامرز: کنه بیست', floors=3),
    'zak':       dict(name='روستای زاک', district=None, scope='edge', apt=None, apt_src='روستا', floors=2),
    'akhlamad':  dict(name='اخلمد', district=None, scope='edge', apt=None, apt_src='روستا', floors=2),
    # ---- separate towns ----
    'razavieh':  dict(name='شهرک رضویه (جاده سرخس)', district=None, scope='town', apt=None, apt_src='شهر مستقل', floors=3),
    'torghabeh': dict(name='طرقبه (شهر) و شهرک بوستان', district=None, scope='town', apt=None, apt_src='شهر مستقل — دیوار طرقبه', floors=3),
    'shandiz':   dict(name='شاندیز', district=None, scope='town', apt=None, apt_src='شهر مستقل — دیوار شاندیز', floors=3),
    'mariyan':   dict(name='روستای ماریان (بعد از مجتمع باغات پردیس، محور گلبهار)', district=None, scope='edge', apt=None, apt_src='روستا', floors=None),
    'naghandar': dict(name='روستای نغندر (ییلاق طرقبه)', district=None, scope='edge', apt=None, apt_src='روستا', floors=None),
    'chenaran_road': dict(name='جادهٔ چناران (جنب خانه‌سازی)', district=None, scope='edge', apt=None, apt_src='حاشیه', floors=None),
    'golbahar':  dict(name='شهر گلبهار', district=None, scope='town', apt=None, apt_src='شهر جدید گلبهار', floors=4),
    'sanati_garden': dict(name='جادهٔ شهرک صنعتی (باغ)', district=None, scope='edge', apt=None, apt_src='حاشیه', floors=None),
    'qazvin':    dict(name='قزوین', district=None, scope='out', apt=None, apt_src='استان دیگر', floors=None),
    'sarakhs':   dict(name='سرخس', district=None, scope='out', apt=None, apt_src='شهر دیگر', floors=None),
    'torbat':    dict(name='تربت حیدریه', district=None, scope='out', apt=None, apt_src='شهر دیگر', floors=None),
    'neyshabur': dict(name='نیشابور', district=None, scope='out', apt=None, apt_src='شهر دیگر', floors=None),
}

FA = str.maketrans('٠١٢٣٤٥٦٧٨٩0123456789يك', '۰۱۲۳۴۵۶۷۸۹۰۱۲۳۴۵۶۷۸۹یک')


def norm(s):
    s = (s or '').translate(FA)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def canon(address):
    a = norm(address)
    for pat, key in RULES:
        if re.search(pat, a):
            return key
    return None
