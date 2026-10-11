"""Parse raw auction HTML pages into a flat table (all.csv / all.json)."""
import glob
import json
import os
import re
import sys

from bs4 import BeautifulSoup

RAW = sys.argv[1]
OUT = sys.argv[2]

FA = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')


def num(s):
    if s is None:
        return None
    s = s.translate(FA).replace(',', '').replace('ریال', '').replace('٫', '.').strip()
    m = re.search(r'-?\d+(?:\.\d+)?', s)
    return float(m.group()) if m else None


LABELS = {
    'قطعه': 'qate', 'بلوک': 'block', 'منطقه': 'mantaqe', 'نوع کاربری': 'karbari',
    'تراکم': 'tarakom', 'نرخ مصوب (هر متر مربع)': 'rate_raw', 'حق تقدیمی': 'total_raw',
    'سال': 'year', 'مرحله': 'step_label', 'آدرس': 'address_raw',
}

rows = []
for f in sorted(glob.glob(os.path.join(RAW, 's*_p*.html'))):
    m = re.search(r's(\d+)_p(\d+)', f)
    step, page = int(m.group(1)), int(m.group(2))
    soup = BeautifulSoup(open(f, encoding='utf-8').read(), 'lxml')
    cards = soup.select('div.col-md-12.mb-3.border.px-0')
    for pos, c in enumerate(cards):
        r = {'step': step, 'page': page, 'pos': pos}
        img = c.select_one('a.thumbnail img')
        r['koroki'] = img.get('full-size') if img else None
        ids = re.findall(r'(?:koroki|etelaeie)Image(\d+)', str(c))
        r['id'] = int(ids[0]) if ids else None
        for lab in c.select('div.col-auto.px-0'):
            k = lab.get_text(' ', strip=True).rstrip(':').strip()
            sib = lab.find_next_sibling('div')
            if k in LABELS and sib is not None:
                r[LABELS[k]] = sib.get_text(' ', strip=True)
        ann = [a for a in c.find_all('a') if 'اطلاعیه' in a.get_text()]
        r['notice'] = ann[0].get('href') if ann else None
        w = c.find(attrs={'winner-price': True})
        if w is not None:
            r['winner_price_raw'] = w.get('winner-price')
            first = (w.get('winner-name') or '').strip()
            r['buyer_type'] = 'حقوقی' if first == 'شرکت' or 'شرکت' in (w.get('winner-family') or '') else 'حقیقی'
        # date + any other trailing text
        txt = c.get_text(' ', strip=True)
        dm = re.search(r'(شنبه|یکشنبه|دوشنبه|سه‌شنبه|سه شنبه|چهارشنبه|پنج‌شنبه|پنجشنبه|جمعه)\s*,\s*\d+\s+\S+\s+\d+', txt)
        r['date'] = dm.group(0) if dm else None
        r['fulltext'] = txt
        # derived
        r['rate'] = num(r.get('rate_raw'))
        r['total'] = num(r.get('total_raw'))
        addr = r.get('address_raw') or ''
        am = re.search(r'\(\s*مساحت\s*:\s*([^)]+)\)', addr)
        r['area'] = num(am.group(1)) if am else None
        r['address'] = re.sub(r'\(\s*مساحت[^)]*\)', '', addr).strip()
        r['winner_price'] = num(r.get('winner_price_raw'))
        rows.append(r)

json.dump(rows, open(os.path.join(OUT, 'all.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('rows', len(rows))
