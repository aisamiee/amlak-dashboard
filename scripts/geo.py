"""Plot positions for the dashboard map.

Input : data/coords_raw.json (UTM readings per sketch, from kroki_coords.py), data/coords_manual.json (optional
        hand corrections {listing_id: [x, y]}), data/assets.json
Output: data/geo.json  {asset_index: {lat, lon, x, y, approx, n, agree}}

Per asset the readings of all its sketches are pooled; the coordinate printed most often wins. A reading far
(> 6 km) from the median of its location is treated as a misread. Assets without a usable reading get the
median position of their location, marked approximate.
"""
import json
import math
import os
import statistics as st
from collections import Counter, defaultdict

ZONE = 40


def utm_to_latlon(x, y, zone=ZONE):
    a, f, k0 = 6378137.0, 1 / 298.257223563, 0.9996
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)
    x -= 500000.0
    m = y / k0
    mu = m / (a * (1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256))
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    p1 = (mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * math.sin(2 * mu) + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * math.sin(4 * mu)
          + (151 * e1 ** 3 / 96) * math.sin(6 * mu) + (1097 * e1 ** 4 / 512) * math.sin(8 * mu))
    n1 = a / math.sqrt(1 - e2 * math.sin(p1) ** 2)
    t1 = math.tan(p1) ** 2
    c1 = ep2 * math.cos(p1) ** 2
    r1 = a * (1 - e2) / (1 - e2 * math.sin(p1) ** 2) ** 1.5
    d = x / (n1 * k0)
    lat = p1 - (n1 * math.tan(p1) / r1) * (d ** 2 / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 ** 2 - 9 * ep2) * d ** 4 / 24
                                            + (61 + 90 * t1 + 298 * c1 + 45 * t1 ** 2 - 252 * ep2 - 3 * c1 ** 2) * d ** 6 / 720)
    lon = (d - (1 + 2 * t1 + c1) * d ** 3 / 6 + (5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * ep2 + 24 * t1 ** 2) * d ** 5 / 120) / math.cos(p1)
    return math.degrees(lat), (zone - 1) * 6 - 180 + 3 + math.degrees(lon)


def build():
    raw = json.load(open('data/coords_raw.json'))
    manual = json.load(open('data/coords_manual.json')) if os.path.exists('data/coords_manual.json') else {}
    assets = json.load(open('data/assets.json', encoding='utf-8'))
    per = {}
    for a in assets:
        reads = []
        for i in a['ids']:
            if i is None:
                continue
            if manual.get(str(i)):
                reads += [tuple(manual[str(i)])] * 5          # a hand correction outvotes machine readings
            r = raw.get(str(i))
            if r and r.get('valid'):
                reads.append((r['x'], r['y']))
        per[a['asset']] = reads
    # first pass: the most frequent reading per asset
    best = {}
    for k, reads in per.items():
        if reads:
            (xy, n), = Counter(reads).most_common(1)
            best[k] = (xy, n, len(reads))
    # location medians to catch misreads (one wrong digit moves a plot by kilometres)
    by_loc = defaultdict(list)
    for a in assets:
        if a['asset'] in best:
            by_loc[a['loc']].append(best[a['asset']][0])
    med = {loc: (st.median(p[0] for p in pts), st.median(p[1] for p in pts)) for loc, pts in by_loc.items() if len(pts) >= 3}
    out, dropped = {}, 0
    for a in assets:
        k = a['asset']
        cands = Counter(per.get(k, []))
        chosen = None
        for xy, n in cands.most_common():
            m = med.get(a['loc'])
            if m is None or math.hypot(xy[0] - m[0], xy[1] - m[1]) < 6000:
                chosen = (xy, n)
                break
        if chosen is None and cands:
            dropped += 1
        if chosen:
            (x, y), n = chosen
            lat, lon = utm_to_latlon(x, y)
            out[k] = dict(lat=round(lat, 6), lon=round(lon, 6), x=x, y=y, approx=False, n=n, of=sum(cands.values()))
    # approximate positions: location median of exact plots, spread on a small ring so markers do not stack
    exact_loc = defaultdict(list)
    for a in assets:
        if a['asset'] in out:
            exact_loc[a['loc']].append(out[a['asset']])
    ring = defaultdict(int)
    for a in assets:
        if a['asset'] in out or not exact_loc.get(a['loc']):
            continue
        pts = exact_loc[a['loc']]
        x = st.median(p['x'] for p in pts)
        y = st.median(p['y'] for p in pts)
        j = ring[a['loc']]
        ring[a['loc']] += 1
        ang, rad = j * 2.39996, 40 + 18 * math.sqrt(j)          # golden-angle spiral, metres
        x, y = x + rad * math.cos(ang), y + rad * math.sin(ang)
        lat, lon = utm_to_latlon(x, y)
        out[a['asset']] = dict(lat=round(lat, 6), lon=round(lon, 6), x=round(x), y=round(y), approx=True, n=0, of=0)
    json.dump(out, open('data/geo.json', 'w'), indent=0)
    ex = sum(1 for v in out.values() if not v['approx'])
    print(f'geo: {len(assets)} assets, exact {ex}, approximate {len(out) - ex}, none {len(assets) - len(out)}, '
          f'misread-dropped {dropped}')


if __name__ == '__main__':
    lat, lon = utm_to_latlon(727423, 4025067)
    print('check (Emamat 74 lot 30):', round(lat, 5), round(lon, 5))
    build()
