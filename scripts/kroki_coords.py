"""Read the plot-centre UTM coordinates printed on every auction sketch (کروکی): "x:۷۲۷۹۲۳ y:۴۰۲۵۰۶۷ zone:۴۰".

Pipeline (no network):
  1. Apple Vision (tools/ocr) finds the text line containing "zone" and its box on each sketch.
  2. The line is cropped from the full-resolution scan, binarised and cut into glyphs by column projection.
     x has 6 digits and y has 7: the last 6 glyphs of the first long word and the last 7 of the second.
  3. Each digit glyph is classified by nearest neighbour against labelled templates (data/coords/templates.npz),
     built once from glyph clusters labelled by hand (see `label` below).

  python scripts/kroki_coords.py extract     # 1+2 -> data/coords/glyphs.npz (cached per image)
  python scripts/kroki_coords.py sheet       # cluster glyphs -> data/coords/sheet_*.png for labelling
  python scripts/kroki_coords.py label '{"0":"۴",...}'   # cluster -> digit, writes templates.npz
  python scripts/kroki_coords.py read        # classify -> data/coords.json  {image_id: {x, y, conf}}
"""
import glob
import json
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

OCR = 'tools/ocr'
OUT = 'data/coords'
GLY = os.path.join(OUT, 'glyphs.npz')
TPL = os.path.join(OUT, 'templates.npz')
G = 28  # glyph bitmap size
os.makedirs(OUT, exist_ok=True)


def image_ids():
    """Every listing id of every tracked asset, newest first within an asset."""
    A = json.load(open('data/assets.json', encoding='utf-8'))
    ids = []
    for a in A:
        ids += sorted((i for i in a['ids'] if i is not None), reverse=True)
    return ids


def find_line(lines):
    for x in lines:
        t = x['t'].lower()
        if re.search(r'z[o0][nmb]e|one\s*:', t) or (re.search(r'\bx\s*[:;]', t) and re.search(r'\by\s*[:;]', t)):
            return x
    for x in lines:
        if re.search(r'y\s*[:;]\s*[f4F]', x['t']):
            return x
    return None


def segments(mask):
    cols = mask.sum(0) > 0
    segs, s = [], None
    for i, c in enumerate(cols):
        if c and s is None:
            s = i
        if not c and s is not None:
            segs.append([s, i]); s = None
    if s is not None:
        segs.append([s, len(cols)])
    merged = []
    for sg in segs:                                   # glue pieces of one glyph split by a 1-2 px gap
        if merged and sg[0] - merged[-1][1] <= 2:
            merged[-1][1] = sg[1]
        else:
            merged.append(sg)
    return merged


def glyph_vec(mask, s, e, band_h):
    sub = mask[:, s:e]
    rows = np.where(sub.any(1))[0]
    if not len(rows):
        return None, None
    g = sub[rows[0]:rows[-1] + 1]
    h, w = g.shape
    side = max(h, w)
    canvas = np.zeros((side, side), bool)
    canvas[(side - h) // 2:(side - h) // 2 + h, (side - w) // 2:(side - w) // 2 + w] = g
    im = Image.fromarray((canvas * 255).astype(np.uint8)).resize((G, G), Image.BILINEAR)
    v = np.asarray(im, np.float32) / 255.0
    geo = np.array([h / band_h, w / band_h, rows[0] / band_h], np.float32)
    return v, geo


def cut(img_path, box):
    im = Image.open(img_path).convert('L')
    x, y, w, h = box
    mx, my = int(h * 1.6), int(h * 0.45)
    crop = im.crop((max(0, x - mx), max(0, y - my), min(im.width, x + w + mx), min(im.height, y + h + my)))
    scale = 90 / max(8, h)
    crop = crop.resize((max(1, int(crop.width * scale)), max(1, int(crop.height * scale))), Image.LANCZOS)
    a = np.asarray(crop, np.float32)
    thr = min(170, (a.max() + np.percentile(a, 5)) / 2)
    mask = a < thr
    rule = mask.mean(1) > 0.45                         # horizontal rules of the sketch frame
    mask[rule] = False
    inked = mask.sum(1) > 0
    # text band: grow from the centre row of the Vision box until an empty run or a rule
    c = min(len(inked) - 1, max(0, int((y - max(0, y - my) + h / 2) * scale)))
    if not inked[c]:
        near = [i for i in range(max(0, c - 15), min(len(inked), c + 16)) if inked[i]]
        if not near:
            return None
        c = min(near, key=lambda i: abs(i - c))
    b0 = c
    while b0 > 0 and not rule[b0 - 1] and (inked[b0 - 1] or (b0 > 2 and inked[b0 - 2] and not rule[b0 - 2])):
        b0 -= 1
    b1 = c + 1
    while b1 < len(inked) and not rule[b1] and (inked[b1] or (b1 + 1 < len(inked) and inked[b1 + 1] and not rule[b1 + 1])):
        b1 += 1
    band = mask[b0:b1]
    bh = b1 - b0
    segs = segments(band)
    if len(segs) < 12:
        return None
    hts = []
    for s_, e_ in segs:
        r_ = np.where(band[:, s_:e_].any(1))[0]
        hts.append(r_[-1] - r_[0] + 1)
    mh = float(np.median(hts))                         # typical glyph height
    keep = [i for i, (s_, e_) in enumerate(segs) if not ((e_ - s_) < 0.25 * mh and hts[i] > 1.35 * mh)]   # | bars
    segs = [segs[i] for i in keep]
    gaps = [segs[i + 1][0] - segs[i][1] for i in range(len(segs) - 1)]
    thr_gap = max(0.75 * mh, 2.5 * float(np.median(gaps)))
    words, cur = [], [segs[0]]
    for i in range(1, len(segs)):
        if gaps[i - 1] > thr_gap:
            words.append(cur); cur = []
        cur.append(segs[i])
    words.append(cur)

    def is_colon(sg):
        s_, e_ = sg
        if (e_ - s_) > 0.45 * mh:
            return False
        r_ = band[:, s_:e_].any(1)
        runs = np.diff(np.concatenate([[0], r_.astype(int), [0]]))
        return (runs == 1).sum() == 2                  # two separate dots stacked

    def digits_of(word, n):
        ci = [i for i, sg in enumerate(word) if is_colon(sg)]
        d = [list(sg) for sg in (word[ci[0] + 1:] if ci else word[-n:])]
        guard = 0
        while len(d) < n and d and guard < 4:          # touching digits: split the widest glyph at its thinnest column
            guard += 1
            j = max(range(len(d)), key=lambda i: d[i][1] - d[i][0])
            s_, e_ = d[j]
            prof = band[:, s_:e_].sum(0)
            lo, hi = int((e_ - s_) * 0.3), int((e_ - s_) * 0.7)
            if hi <= lo:
                break
            m_ = s_ + lo + int(np.argmin(prof[lo:hi]))
            d[j:j + 1] = [[s_, m_], [m_ + 1, e_]]
        return d[-n:] if len(d) >= n else None

    cand = [w_ for w_ in words if len(w_) >= 5]
    if len(cand) < 2:
        return None
    wx = digits_of(cand[0], 6)
    wy = digits_of(cand[1], 7)
    if not wx or not wy:
        return None
    out = []
    for word in (wx, wy):
        vs = []
        for s_, e_ in word:
            v, geo = glyph_vec(band, s_, e_, mh)
            if v is None:
                return None
            vs.append((v, geo))
        out.append(vs)
    return out, crop


def extract():
    cache = dict(np.load(GLY, allow_pickle=True)) if os.path.exists(GLY) else {}
    done = set(cache.get('ids', np.array([])).tolist())
    todo = []
    for i in image_ids():
        if i in done:
            continue
        f = glob.glob(f'data/img/korokiImage{i}.*')
        if f:
            todo.append((i, f[0]))
    print('to extract', len(todo))
    recs = list(cache.get('recs', np.array([], dtype=object)))
    ids = list(done)
    for k in range(0, len(todo), 40):
        batch = todo[k:k + 40]
        lines = {}
        # pass 1: whole sheet; pass 2: left half only (Vision downsamples big sheets and can miss the small line)
        for frac in ('1.0', '0.5'):
            need = [f for _, f in batch if not (f in lines and find_line(lines[f].get('lines', [])))]
            if not need:
                break
            res = subprocess.run([OCR, 'en-US', frac] + need, capture_output=True, text=True)
            for ln in res.stdout.splitlines():
                try:
                    d = json.loads(ln)
                except Exception:
                    continue
                if find_line(d.get('lines', [])) or d['file'] not in lines:
                    lines[d['file']] = d
        for i, f in batch:
            ids.append(i)
            d = lines.get(f)
            hit = find_line(d.get('lines', [])) if d else None
            if not hit:
                recs.append(dict(id=i, ok=False, why='line not found')); continue
            try:
                r = cut(f, hit['b'])
            except Exception as e:
                r = None
            if not r:
                recs.append(dict(id=i, ok=False, why='segmentation', vision=hit['t'])); continue
            (gx, gy), crop = r
            recs.append(dict(id=i, ok=True, vision=hit['t'], box=hit['b'],
                             gx=np.stack([v for v, _ in gx]), gy=np.stack([v for v, _ in gy]),
                             qx=np.stack([q for _, q in gx]), qy=np.stack([q for _, q in gy])))
        print(k + len(batch), '/', len(todo), 'ok', sum(1 for r in recs if r['ok']))
    np.savez_compressed(GLY, ids=np.array(ids), recs=np.array(recs, dtype=object))


def all_glyphs():
    d = np.load(GLY, allow_pickle=True)
    vecs, meta = [], []
    for r in d['recs']:
        if not r['ok']:
            continue
        for which in ('x', 'y'):
            for j, (v, q) in enumerate(zip(r['g' + which], r['q' + which])):
                vecs.append(np.concatenate([v.ravel(), q * 4]))
                meta.append((r['id'], which, j))
    return np.array(vecs, np.float32), meta


def kmeans(X, k, iters=40, seed=1):
    rng = np.random.default_rng(seed)
    C = X[rng.choice(len(X), k, replace=False)]
    for _ in range(iters):
        d = ((X[:, None, :] - C[None]) ** 2).sum(-1)
        lab = d.argmin(1)
        for j in range(k):
            if (lab == j).any():
                C[j] = X[lab == j].mean(0)
    return lab, C


def sheet(k=30):
    X, meta = all_glyphs()
    lab, C = kmeans(X, k)
    np.savez_compressed(os.path.join(OUT, 'clusters.npz'), lab=lab, C=C)
    cell, per = 40, 14
    img = Image.new('L', (60 + per * cell, k * cell), 255)
    dr = ImageDraw.Draw(img)
    rng = np.random.default_rng(0)
    for j in range(k):
        idx = np.where(lab == j)[0]
        dr.text((4, j * cell + 12), f'{j}:{len(idx)}', fill=0)
        for n, i in enumerate(rng.choice(idx, min(per, len(idx)), replace=False) if len(idx) else []):
            g = (255 - X[i][:G * G].reshape(G, G) * 255).astype(np.uint8)
            img.paste(Image.fromarray(g).resize((34, 34)), (60 + n * cell, j * cell + 3))
    img.save(os.path.join(OUT, 'sheet.png'))
    print('clusters', np.bincount(lab, minlength=k).tolist())


FA = '۰۱۲۳۴۵۶۷۸۹'


def label(mapping):
    """mapping: {cluster: digit char or '?'} -> templates = all glyphs of confidently labelled clusters."""
    X, meta = all_glyphs()
    lab = np.load(os.path.join(OUT, 'clusters.npz'))['lab']
    cls = FA + 'X'                                    # X = not a digit (rules, stray text)
    keep = [i for i in range(len(X)) if mapping.get(str(lab[i]), '?') in cls]
    y = np.array([cls.index(mapping[str(lab[i])]) for i in keep])
    np.savez_compressed(TPL, X=X[keep], y=y)
    print('templates', len(keep), np.bincount(y, minlength=11).tolist())


def read(full=False):
    X, meta = all_glyphs()
    prev = {}
    if not full and os.path.exists('data/coords_raw.json') and os.path.getmtime('data/coords_raw.json') > os.path.getmtime(TPL):
        prev = json.load(open('data/coords_raw.json'))      # incremental: classify only sketches not read yet
        keep = [n for n, m_ in enumerate(meta) if str(m_[0]) not in prev]
        X, meta = X[keep], [meta[n] for n in keep]
    t = np.load(TPL)
    TX, Ty = t['X'], t['y']
    digits, confs = [], []
    for i in range(0, len(X), 512):
        d = ((X[i:i + 512, None, :] - TX[None]) ** 2).sum(-1)
        order = d.argsort(1)[:, :7]
        for row, o in zip(d, order):
            votes = np.bincount(Ty[o], minlength=11)
            best = votes.argmax()
            # margin: nearest template of another digit vs nearest of the chosen digit
            dbest = row[Ty == best].min()
            dother = row[Ty != best].min()
            digits.append(best); confs.append(float(dother / max(dbest, 1e-6)))
    out = {}
    for (iid, which, j), dg, cf in zip(meta, digits, confs):
        o = out.setdefault(str(iid), {'x': ['?'] * 6, 'y': ['?'] * 7, 'cx': [0] * 6, 'cy': [0] * 7})
        o[which][j] = str(dg) if dg < 10 else '?'
        o['c' + which][j] = round(cf, 2)
    res = dict(prev)
    for iid, o in out.items():
        sx, sy = ''.join(o['x']), ''.join(o['y'])
        if '?' in sx + sy:
            res[iid] = dict(x=None, y=None, conf=0, valid=False, raw=sx + '/' + sy)
            continue
        x, y = int(sx), int(sy)
        conf = min(o['cx'] + o['cy'])
        valid = 600000 <= x <= 800000 and 3950000 <= y <= 4100000
        res[iid] = dict(x=x, y=y, conf=conf, valid=valid)
    json.dump(res, open('data/coords_raw.json', 'w'), indent=0)
    v = [r for r in res.values() if r['valid']]
    print('read', len(res), 'valid range', len(v), 'low-conf(<1.3)', sum(1 for r in v if r['conf'] < 1.3))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'extract':
        extract()
    elif cmd == 'sheet':
        sheet(int(sys.argv[2]) if len(sys.argv) > 2 else 30)
    elif cmd == 'label':
        label(json.loads(sys.argv[2]))
    elif cmd == 'read':
        read(full=len(sys.argv) > 2 and sys.argv[2] == 'full')
