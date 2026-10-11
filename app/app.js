/* Auction dashboard — single-page app over app/data.json (built by scripts/build_app.py).
   Personal state (watchlist, notes, bids) lives on the local server: GET/PUT /api/state. */
'use strict';

/* ================= helpers ================= */
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const NF = {};
const nf = (d, extra = {}) => { const key = d + JSON.stringify(extra); return NF[key] || (NF[key] = new Intl.NumberFormat('fa-IR', { maximumFractionDigits: d, ...extra })); };
const ok = x => x != null && isFinite(x);
const fa = (x, d = 0) => ok(x) ? nf(d).format(x) : '—';
const mil = x => ok(x) ? fa(x / 1e6, Math.abs(x) < 1e8 ? 1 : 0) : '—';          // toman -> million
const bil = x => ok(x) ? fa(x / 1e9, Math.abs(x) < 1e11 ? 1 : 0) : '—';          // toman -> billion
const pct = (x, sign = false, d = 0) => ok(x) ? nf(d, { style: 'percent', signDisplay: sign ? 'exceptZero' : 'auto' }).format(x) : '—';
const m2 = x => ok(x) ? fa(Math.round(x)) : '—';
const sum = xs => xs.reduce((s, x) => s + (ok(x) ? x : 0), 0);
const median = xs => { const v = xs.filter(ok).sort((a, b) => a - b); if (!v.length) return null; const m = v.length >> 1; return v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2; };
const clsSign = x => !ok(x) ? '' : x > 0.0005 ? 'up' : x < -0.0005 ? 'down' : '';
const toEn = s => String(s ?? '').replace(/[۰-۹]/g, d => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d)).replace(/[٠-٩]/g, d => '٠١٢٣٤٥٦٧٨٩'.indexOf(d));
const norm = s => toEn(s).replace(/ي/g, 'ی').replace(/ك/g, 'ک').replace(/‌/g, ' ').toLowerCase();
const debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };
const store = { get(k, d) { try { const v = localStorage.getItem('amlak-' + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem('amlak-' + k, JSON.stringify(v)); } catch (e) { /* storage unavailable */ } } };
const cssv = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();

const ICON = {
  grid: '<rect x="3.5" y="3.5" width="7" height="7" rx="1.6"/><rect x="13.5" y="3.5" width="7" height="7" rx="1.6"/><rect x="3.5" y="13.5" width="7" height="7" rx="1.6"/><rect x="13.5" y="13.5" width="7" height="7" rx="1.6"/>',
  target: '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r=".8"/>',
  map: '<path d="M9 4.5 3.5 6.5v13l5.5-2 6 2 5.5-2v-13l-5.5 2z"/><path d="M9 4.5v13M15 6.5v13"/>',
  calc: '<rect x="5" y="3" width="14" height="18" rx="2.2"/><path d="M8.5 7h7M8.5 11.5h.01M12 11.5h.01M15.5 11.5h.01M8.5 15h.01M12 15h.01M15.5 15v3M8.5 18h.01M12 18h.01"/>',
  chart: '<path d="M4 4v16h16"/><path d="m7.5 14.5 3.5-4.5 3 3 5-6.5"/>',
  archive: '<rect x="3" y="4" width="18" height="5" rx="1.2"/><path d="M5 9v9.5A1.5 1.5 0 0 0 6.5 20h11a1.5 1.5 0 0 0 1.5-1.5V9M10 13h4"/>',
  star: '<path d="m12 3.6 2.6 5.3 5.8.85-4.2 4.1 1 5.8L12 16.9l-5.2 2.75 1-5.8-4.2-4.1 5.8-.85z"/>',
  book: '<path d="M5 4.5A1.5 1.5 0 0 1 6.5 3H19v15H6.5A1.5 1.5 0 0 0 5 19.5z"/><path d="M5 19.5A1.5 1.5 0 0 0 6.5 21H19v-3M9 7h6"/>',
  close: '<path d="M6 6l12 12M18 6 6 18"/>',
  ext: '<path d="M14 4h6v6M20 4l-8.5 8.5M18 14v4.5a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 4 18.5v-11A1.5 1.5 0 0 1 5.5 6H10"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M4.6 4.6 6 6M18 18l1.4 1.4M2.5 12h2M19.5 12h2M4.6 19.4 6 18M18 6l1.4-1.4"/>',
  moon: '<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/>',
  auto: '<circle cx="12" cy="12" r="8.5"/><path d="M12 3.5v17a8.5 8.5 0 0 0 0-17z" fill="currentColor"/>',
  pin: '<path d="M12 21s-6.5-6-6.5-11a6.5 6.5 0 0 1 13 0c0 5-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.4"/>',
  up: '<path d="M12 19V5M6 11l6-6 6 6"/>', down: '<path d="M12 5v14M6 13l6 6 6-6"/>', plus: '<path d="M12 5v14M5 12h14"/>',
  tag: '<path d="M3.5 12.5V4.5a1 1 0 0 1 1-1h8l8 8-9 9z"/><circle cx="8" cy="8" r="1.3"/>',
};
const ic = (n, cls = '') => `<svg viewBox="0 0 24 24" class="${cls}" aria-hidden="true">${ICON[n]}</svg>`;

/* ================= labels ================= */
const VC = {
  buy: { t: 'مناسب مشارکت', d: 'سود سازنده دست‌کم ۲۵٪ و بازده واقعی مالک دست‌کم ۱۵٪؛ تا سقف پیشنهاد بخرید.' },
  thin: { t: 'کم‌سود', d: 'مشارکت شدنی است ولی بازده مالک پایین است؛ فقط با قیمت نزدیک پایه.' },
  hold: { t: 'فقط خرید زمین', d: 'ساخت به‌صرفه نیست، ولی قیمت دست‌کم ۱۵٪ زیر بازار زمین است (نگهداری یا فروش زمین).' },
  avoid: { t: 'توصیه نمی‌شود', d: 'ساخت زیان‌ده است و قیمت هم‌تراز یا بالاتر از بازار زمین است.' },
  na: { t: 'ارزیابی نشده', d: 'آپارتمان، باغ، پک یا محلی بدون قیمت بازار؛ مدل ساخت روی آن اجرا نشده است.' },
};
const ST = { active: 'در حال عرضه', sold: 'فروخته‌شده', withdrawn: 'خارج‌شده بدون برنده', sold_relisted_gone: 'برنده داشت، خارج شد' };
const KIND = { land: 'زمین', large_parcel: 'قطعهٔ بزرگ', apartment: 'آپارتمان', pack: 'پک', garden: 'باغ/زراعی', mixed: 'مختلط', tourism: 'تفریحی‌توریستی' };
const SCOPE = { city: 'شهر مشهد', edge: 'حاشیهٔ مشهد', town: 'شهرهای اطراف', out: 'خارج از مشهد' };
const OUTCOME = ['', 'در حال بررسی', 'بازدید شد', 'پیشنهاد دادم', 'برنده شدم', 'برنده نشدم', 'منصرف شدم'];
const CONF = { high: 'اطمینان بالا', medium: 'اطمینان متوسط', low: 'اطمینان کم' };
const vpill = vc => vc ? `<span class="pill ${vc}">${VC[vc].t}</span>` : '';
const spill = st => `<span class="pill ${st}">${ST[st] || st}</span>`;
const tomanM2 = x => ok(x) ? `متری ${fa(Math.round(x))} تومان` : '';
const isSold = a => !!a.wprice && (a.status === 'sold' || a.status === 'sold_relisted_gone');
// status tag: a sold lot carries its winning price per m² in full toman, e.g. «فروخته شد · متری ۲۱۰٬۰۰۰٬۰۰۰ تومان»
const stagText = a => isSold(a) ? `${a.status === 'sold' ? 'فروخته شد' : 'برنده داشت'} · ${tomanM2(a.wprice)}` : (ST[a.status] || a.status);
const stag = a => isSold(a)
  ? `<span class="pill sold" title="مرحلهٔ ${fa(a.wstep)} · ${pct(a.wprem, true, 1)} بالای قیمت پایه${a.buyer ? ' · خریدار ' + esc(a.buyer) : ''}">${stagText(a)}</span>`
  : spill(a.status);

/* ================= state ================= */
const S = { D: null, st: { items: {} }, view: null, arg: null, sort: store.get('sort', {}), f: store.get('filters', {}), page: {}, lotK: null, maps: {}, tab: {} };
const VIEWS = [
  { id: 'overview', t: 'نمای کلی', icon: 'grid', g: 'پایش' },
  { id: 'lots', t: 'فرصت‌های فعال', icon: 'target', g: 'پایش', badge: () => S.D.active.length },
  { id: 'map', t: 'نقشهٔ قطعه‌ها', icon: 'map', g: 'پایش' },
  { id: 'calc', t: 'ماشین‌حساب مشارکت', icon: 'calc', g: 'تحلیل' },
  { id: 'market', t: 'بازار و محله‌ها', icon: 'chart', g: 'تحلیل' },
  { id: 'archive', t: 'بایگانی قطعه‌ها', icon: 'archive', g: 'تحلیل' },
  { id: 'watch', t: 'پیگیری من', icon: 'star', g: 'شخصی', badge: () => watched().length || '' },
  { id: 'method', t: 'روش و فرض‌ها', icon: 'book', g: 'شخصی' },
];

function W(k) { return S.st.items[String(k)] || null; }
function watched() { return Object.entries(S.st.items).map(([k, w]) => ({ a: assetFor(+k), w, k: +k })).filter(x => x.a && (x.w.star || x.w.note || x.w.myBid || x.w.myMax || x.w.outcome)); }
function assetFor(k) { return S.D.byK.get(k) || S.D.byId.get(k) || null; }
async function putW(k, obj) {
  if (obj) S.st.items[String(k)] = obj; else delete S.st.items[String(k)];
  if (S.local) { store.set('state', S.st); return true; }     // online copy: notes stay on this device
  try {
    const r = await fetch('api/state/' + k, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(obj) });
    if (!r.ok) throw new Error(r.status);
    return true;
  } catch (e) { toast('ذخیره نشد: سرور داشبورد در دسترس نیست. start.command را اجرا کنید.'); return false; }
}
function toggleStar(k) {
  const a = assetFor(k); if (!a) return;
  const cur = W(a.k);
  if (cur && cur.star) {
    const keep = cur.note || cur.myBid || cur.myMax || cur.outcome;
    putW(a.k, keep ? { ...cur, star: false } : null);
  } else {
    putW(a.k, { ...(cur || {}), star: true, at: S.D.meta.updated,
      snap: { rl: a.rl, st: a.status, vc: a.vc, mb: a.v ? a.v.max_bid_partner : null, step: a.last } });
  }
  $$(`[data-star="${a.k}"]`).forEach(b => b.classList.toggle('on', !!(W(a.k) || {}).star));
  renderNav();
  if (S.view === 'watch') show('watch');
}
const starBtn = a => `<button class="star ${(W(a.k) || {}).star ? 'on' : ''}" data-star="${a.k}" title="دنبال کردن" aria-label="دنبال کردن">${ic('star')}</button>`;

let toastT;
function toast(msg) {
  let el = $('#toast');
  if (!el) { el = document.createElement('div'); el.id = 'toast'; el.style.cssText = 'position:fixed;bottom:18px;left:50%;transform:translateX(-50%);background:var(--ink);color:var(--bg);padding:9px 16px;border-radius:10px;z-index:99;font-size:13px;box-shadow:var(--shadow)'; document.body.append(el); }
  el.textContent = msg; el.hidden = false; clearTimeout(toastT); toastT = setTimeout(() => { el.hidden = true; }, 3800);
}

/* ================= boot ================= */
/* ---------- data: plain on the Mac (scripts/serve.py), encrypted on the online copy (docs/data.enc) ---------- */
const b64d = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));
const b64e = buf => btoa(String.fromCharCode(...new Uint8Array(buf)));
async function deriveKey(pw, enc) {
  const base = await crypto.subtle.importKey('raw', new TextEncoder().encode(pw), 'PBKDF2', false, ['deriveKey']);
  return crypto.subtle.deriveKey({ name: 'PBKDF2', salt: b64d(enc.salt), iterations: enc.iter, hash: 'SHA-256' },
    base, { name: 'AES-GCM', length: 256 }, true, ['decrypt']);
}
const importRaw = k => crypto.subtle.importKey('raw', b64d(k), 'AES-GCM', true, ['decrypt']);
async function decryptData(enc, key) {
  const pt = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: b64d(enc.iv) }, key, b64d(enc.ct));
  const text = enc.z === 'gzip' ? await new Response(new Blob([pt]).stream().pipeThrough(new DecompressionStream('gzip'))).text()
    : new TextDecoder().decode(pt);
  return JSON.parse(text);
}
function unlock(enc) {
  return new Promise(resolve => {
    const el = document.createElement('div');
    el.className = 'lock';
    el.innerHTML = `<form class="lock-card" id="lockForm" autocomplete="on">
      <div class="brand-mark"><svg viewBox="0 0 32 32"><path d="M7 24 11 7l14 4-3 13z" fill="none" stroke="#7fd1b0" stroke-width="2.2" stroke-linejoin="round"/><circle cx="16" cy="16" r="2.6" fill="#dcab52"/></svg></div>
      <h2>مزایدهٔ املاک رضوی</h2>
      <p>داده‌های این داشبورد رمزگذاری شده‌اند. برای دیدن آن‌ها رمز را وارد کنید.</p>
      <input type="text" name="username" value="amlak" autocomplete="username" hidden>
      <input id="lockPw" class="inp" type="password" name="password" autocomplete="current-password" placeholder="رمز" dir="ltr" required>
      <label class="check"><input id="lockRem" type="checkbox" checked> روی این دستگاه به خاطر بسپار</label>
      <button class="btn primary" id="lockBtn" type="submit">باز کردن داشبورد</button>
      <div class="lock-err" id="lockErr" hidden>رمز درست نیست. دوباره امتحان کنید.</div></form>`;
    document.body.append(el);
    setTimeout(() => $('#lockPw').focus(), 50);
    $('#lockForm').addEventListener('submit', async e => {
      e.preventDefault();
      const btn = $('#lockBtn');
      btn.disabled = true; btn.textContent = 'در حال باز کردن…'; $('#lockErr').hidden = true;
      try {
        const key = await deriveKey($('#lockPw').value.trim(), enc);
        const d = await decryptData(enc, key);
        if ($('#lockRem').checked) store.set('key', { salt: enc.salt, k: b64e(await crypto.subtle.exportKey('raw', key)) });
        el.remove();
        resolve(d);
      } catch (err) {
        $('#lockErr').hidden = false; btn.disabled = false; btn.textContent = 'باز کردن داشبورد';
      }
    });
  });
}
async function loadData() {
  const r = await fetch('data.json', { cache: 'no-store' }).catch(() => null);
  if (r && r.ok) return r.json();
  const er = await fetch('data.enc', { cache: 'no-store' });
  if (!er.ok) throw new Error('data.enc ' + er.status);
  const enc = await er.json();
  S.enc = true;
  const saved = store.get('key', null);
  if (saved && saved.salt === enc.salt) {
    try { return await decryptData(enc, await importRaw(saved.k)); } catch (e) { /* password changed: ask again */ }
  }
  return unlock(enc);
}
async function loadState() {
  try {
    const r = await fetch('api/state', { cache: 'no-store' });
    if (r.ok) { const j = await r.json(); if (j && j.items) return j; }
  } catch (e) { /* no local server */ }
  S.local = true;                                      // online copy: personal state in this browser only
  const st = store.get('state', null);
  return st && st.items ? st : { items: {} };
}
const origUrl = a => S.local ? a.kroki : 'orig/' + a.kid;

async function boot() {
  const [d, st] = await Promise.all([loadData(), loadState()]);
  S.st = st;
  prep(d);
  S.D = d;
  renderRail();
  window.addEventListener('hashchange', route);
  route();
  pollVersion();
}

function prep(D) {
  D.byK = new Map(); D.byId = new Map();
  for (const a of D.assets) {
    D.byK.set(a.k, a);
    for (const id of a.ids) if (id != null) D.byId.set(id, a);
    a.L = D.locs[a.loc] || { short: a.loc || 'محل نامشخص', name: a.loc || 'محل نامشخص' };
    a.title = `${a.L.short} · قطعهٔ ${a.qate || '—'}`;
    a.bid = a.status === 'active' && a.rl ? a.rl * (1 + ((a.v && a.v.exp_premium) || 0)) : null;
    a.room = a.v && a.v.max_bid_partner && a.rl ? a.v.max_bid_partner / a.rl - 1 : null;     // headroom of the cap over today's base
    a.q = norm([a.L.name, a.L.short, a.qate, a.block, a.address, a.karbari, a.k, ...a.ids].join(' '));
  }
  D.active = D.assets.filter(a => a.status === 'active');
  D.stageDate = Object.fromEntries(D.stages.map(s => [s.step, s.date_fa]));
}

let verMtime = null;
function pollVersion() {
  const tick = async () => {
    try {
      let mt;
      if (S.local) {
        const h = await fetch(S.enc ? 'data.enc' : 'data.json', { method: 'HEAD', cache: 'no-store' });
        mt = h.headers.get('etag') || h.headers.get('last-modified');
      } else {
        mt = (await (await fetch('api/version', { cache: 'no-store' })).json()).mtime;
      }
      const v = { mtime: mt };
      if (verMtime == null) verMtime = v.mtime;
      else if (v.mtime && v.mtime !== verMtime) {
        $('#bannerSlot').innerHTML = `<div class="view" style="padding-bottom:0"><div class="banner"><span>داده‌های تازهٔ مزایده آماده است.</span><button type="button" onclick="location.reload()">نمایش داده‌های جدید</button></div></div>`;
        return;
      }
    } catch (e) { /* server offline */ }
    setTimeout(tick, S.local ? 60000 : 20000);
  };
  tick();
}

/* ================= shell ================= */
function renderRail() {
  renderNav();
  const m = S.D.meta;
  $('#fresh').innerHTML = `<div><span class="dot"></span><b>مرحلهٔ ${fa(m.last_step)}</b> · ${esc(m.last_date)}</div>
    <div>${fa(m.n_stages)} مرحله از ${esc(m.first_date)}</div>
    <div>به‌روزرسانی: ${esc(m.updated)}</div>
    <div class="hint">${S.local ? 'نسخهٔ آنلاین؛ داده با هر «مزایده را به‌روز کن» از مک شما منتشر می‌شود.' : 'برای دادهٔ تازه به Claude بگویید: «مزایده را به‌روز کن»'}</div>
    ${S.enc ? '<button class="theme-btn" type="button" id="lockNow" style="margin-top:8px">قفل کردن این دستگاه</button>' : ''}`;
  const ln = $('#lockNow');
  if (ln) ln.addEventListener('click', () => { try { localStorage.removeItem('amlak-key'); } catch (e) { /* ignore */ } location.reload(); });
  renderThemeBtn();
}
function renderNav() {
  let html = '', g = '';
  for (const v of VIEWS) {
    if (v.g !== g) { g = v.g; html += `<div class="nav-label">${g}</div>`; }
    const b = v.badge ? v.badge() : '';
    html += `<a href="#${v.id}" class="${S.view === v.id ? 'on' : ''}" data-nav="${v.id}">${ic(v.icon)}<span>${v.t}</span>${b !== '' && b != null ? `<span class="badge">${fa(b)}</span>` : ''}</a>`;
  }
  $('#nav').innerHTML = html;
}
function renderThemeBtn() {
  const t = document.documentElement.dataset.theme || 'auto';
  const lbl = { auto: 'پوسته: خودکار', light: 'پوسته: روشن', dark: 'پوسته: تیره' }[t];
  $('#themeBtn').innerHTML = ic(t === 'dark' ? 'moon' : t === 'light' ? 'sun' : 'auto') + lbl;
}
$('#themeBtn').addEventListener('click', () => {
  const cur = document.documentElement.dataset.theme || 'auto';
  const next = { auto: 'light', light: 'dark', dark: 'auto' }[cur];
  if (next === 'auto') delete document.documentElement.dataset.theme; else document.documentElement.dataset.theme = next;
  try { if (next === 'auto') localStorage.removeItem('amlak-theme'); else localStorage.setItem('amlak-theme', next); } catch (e) { /* ignore */ }
  renderThemeBtn();
  if (S.view) show(S.view, S.arg, true);
  if (S.lotK != null) openLot(S.lotK, true);
});

function route() {
  const h = decodeURIComponent(location.hash.slice(1)) || 'overview';
  const lm = h.match(/^lot-(-?\d+)$/);
  if (lm) { if (!S.view) show('overview'); openLot(+lm[1]); return; }
  closeLot(true);
  const cm = h.match(/^calc-(-?\d+)$/);
  if (cm) return show('calc', +cm[1]);
  const lc = h.match(/^archive-(.+)$/);
  if (lc) { S.f.archive = { ...(S.f.archive || {}), loc: lc[1], preset: 'all', status: '' }; return show('archive'); }
  show(VIEWS.some(v => v.id === h) ? h : 'overview');
}

const SUBS = {
  overview: () => `مرحلهٔ ${fa(S.D.meta.last_step)} · ${S.D.meta.last_date} · خلاصهٔ تصمیم و تحولات`,
  lots: () => `${fa(S.D.active.length)} قطعهٔ مسکونی در حال عرضه · مرتب‌شده بر اساس امتیاز سرمایه‌گذاری`,
  map: () => 'موقعیت دقیق قطعه‌ها از مختصات UTM چاپ‌شده روی کروکی',
  calc: () => 'مدل مشارکت در ساخت با فرض‌های قابل تغییر؛ نتیجه همان لحظه حساب می‌شود',
  market: () => 'روند قیمت پایه، کارنامهٔ محله‌ها و آمار هر مرحله',
  archive: () => `همهٔ ${fa(S.D.assets.length)} قطعهٔ ردیابی‌شده در ${fa(S.D.meta.n_stages)} مرحله`,
  watch: () => 'قطعه‌هایی که دنبال می‌کنید، با یادداشت‌ها و پیشنهادهای شما',
  method: () => 'فرمول‌ها، فرض‌ها، منابع قیمت و محدودیت‌ها',
};
function show(view, arg = null, keepScroll = false) {
  const changed = view !== S.view;
  for (const k in S.maps) { if (k !== 'lot') { try { S.maps[k].remove(); } catch (e) { /* ignore */ } delete S.maps[k]; } }
  S.view = view; S.arg = arg;
  renderNav();
  const v = VIEWS.find(x => x.id === view);
  $('#vTitle').textContent = v.t;
  $('#vSub').textContent = SUBS[view]();
  const el = $('#view');
  el.innerHTML = R[view](arg);
  if (AFTER[view]) AFTER[view](arg);
  if (changed && !keepScroll) window.scrollTo(0, 0);
}

/* ================= tables ================= */
function table(id, cols, rows, opt = {}) {
  const s = S.sort[id] || opt.sort || {};
  const col = cols.find(c => c.k === s.k);
  if (col) {
    const val = col.v || (r => r[col.k]);
    rows = [...rows].sort((a, b) => {
      const x = val(a), y = val(b);
      if (x == null && y == null) return 0; if (x == null) return 1; if (y == null) return -1;
      return (typeof x === 'string' ? x.localeCompare(y, 'fa') : x - y) * (s.d === 'asc' ? 1 : -1);
    });
  }
  const total = rows.length;
  let pager = '';
  if (opt.pageSize && total > opt.pageSize) {
    const pages = Math.ceil(total / opt.pageSize);
    const p = Math.min(S.page[id] || 0, pages - 1);
    rows = rows.slice(p * opt.pageSize, (p + 1) * opt.pageSize);
    pager = `<div class="pager"><span>${fa(p * opt.pageSize + 1)} تا ${fa(Math.min(total, (p + 1) * opt.pageSize))} از ${fa(total)}</span>
      <span class="chips"><button class="chip" data-page="${id}" data-p="${p - 1}" ${p === 0 ? 'disabled' : ''}>قبلی</button>
      <button class="chip" data-page="${id}" data-p="${p + 1}" ${p >= pages - 1 ? 'disabled' : ''}>بعدی</button></span></div>`;
  }
  const head = cols.map(c => {
    const sortable = c.sort !== false;
    const on = s.k === c.k;
    return `<th class="${c.n ? 'n' : ''} ${sortable ? 'sort' : ''} ${on ? 'sorted' : ''}" ${sortable ? `data-sort="${id}" data-k="${c.k}"` : ''} title="${esc(c.tip || '')}">${c.t}${sortable ? `<span class="arr">${on ? (s.d === 'asc' ? '▲' : '▼') : '▾'}</span>` : ''}</th>`;
  }).join('');
  const body = rows.length ? rows.map(r => `<tr class="${opt.click === false ? '' : 'click'}" ${opt.click === false ? '' : `data-open="${r.k}"`}>${cols.map(c => `<td class="${c.n ? 'n' : ''} ${c.cls || ''}">${c.f ? c.f(r) : esc(r[c.k])}</td>`).join('')}</tr>`).join('')
    : `<tr><td colspan="${cols.length}"><div class="empty">${opt.empty || 'موردی با این فیلترها پیدا نشد.'}</div></td></tr>`;
  return `<div class="tbl-wrap" ${opt.maxH ? `style="max-height:${opt.maxH}px"` : ''}><table class="tbl" id="t-${id}"><thead><tr>${head}</tr></thead><tbody>${body}</tbody>${opt.foot || ''}</table></div>${pager}`;
}
const lotCell = a => `<td class="lot"></td>` && `<b>${esc(a.L.short)}</b> <span class="muted">· قطعهٔ ${esc(a.qate || '—')}</span><span class="sub">${a.block ? `بلوک ${esc(a.block)} · ` : ''}${KIND[a.kind] || ''} · ${SCOPE[a.scope] || ''}</span>`;
const barPct = (x, scale = 0.5) => ok(x) ? `<span class="bar-cell"><span class="${clsSign(x)}">${pct(x, true)}</span><i class="${x < 0 ? 'neg' : ''}" style="width:${Math.min(60, Math.abs(x) / scale * 60)}px"></i></span>` : '—';

/* ================= charts ================= */
function niceTicks(lo, hi, n = 4) {
  if (!(hi > lo)) { hi = lo + 1; }
  const span = hi - lo, step0 = span / n, mag = Math.pow(10, Math.floor(Math.log10(step0)));
  const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => span / s <= n + 0.5) || 10 * mag;
  const out = []; for (let v = Math.ceil(lo / step) * step; v <= hi + step * 1e-9; v += step) out.push(v);
  return out;
}
function spark(vals, { w = 160, h = 34, color = 'var(--chart-line)', fill = 'var(--chart-fill)' } = {}) {
  const pts = vals.map((v, i) => [i, v]).filter(p => ok(p[1]));
  if (pts.length < 2) return '';
  const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  const X = x => 2 + (x - x0) / (x1 - x0 || 1) * (w - 4), Y = y => h - 3 - (y - y0) / (y1 - y0 || 1) * (h - 8);
  const d = pts.map((p, i) => `${i ? 'L' : 'M'}${X(p[0]).toFixed(1)},${Y(p[1]).toFixed(1)}`).join('');
  const last = pts[pts.length - 1];
  return `<svg class="chart spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" style="direction:ltr;height:${h}px"><path d="${d}L${X(last[0])},${h}L${X(pts[0][0])},${h}Z" fill="${fill}" stroke="none"/><path d="${d}" fill="none" stroke="${color}" stroke-width="1.6" vector-effect="non-scaling-stroke"/><circle cx="${X(last[0])}" cy="${Y(last[1])}" r="2.6" fill="${color}"/></svg>`;
}
function bars(items, { w = 560, h = 170, fmt = v => fa(v), color = 'var(--chart-line)', yfmt } = {}) {
  const pad = { l: 34, r: 8, t: 14, b: 22 };
  const vals = items.map(i => i.v).filter(ok);
  const hi = Math.max(0, ...vals), lo = Math.min(0, ...vals);
  const ticks = niceTicks(lo, hi || 1, 3);
  const y0 = Math.min(lo, ticks[0]), y1 = Math.max(hi, ticks[ticks.length - 1]);
  const X = i => pad.l + (i + 0.5) * (w - pad.l - pad.r) / items.length;
  const Y = v => pad.t + (1 - (v - y0) / (y1 - y0 || 1)) * (h - pad.t - pad.b);
  const bw = Math.max(3, (w - pad.l - pad.r) / items.length * 0.62);
  let g = '<g class="grid">' + ticks.map(t => `<line x1="${pad.l}" x2="${w - pad.r}" y1="${Y(t)}" y2="${Y(t)}"/><text x="${pad.l - 6}" y="${Y(t) + 4}" text-anchor="end">${(yfmt || fmt)(t)}</text>`).join('') + '</g>';
  g += items.map((it, i) => ok(it.v) ? `<rect x="${X(i) - bw / 2}" y="${Math.min(Y(it.v), Y(0))}" width="${bw}" height="${Math.max(1, Math.abs(Y(it.v) - Y(0)))}" rx="2" fill="${it.c || color}"><title>${esc(it.tip || '')}</title></rect>` : '').join('');
  const every = Math.ceil(items.length / 13);
  g += items.map((it, i) => i % every === 0 || i === items.length - 1 ? `<text x="${X(i)}" y="${h - 6}" text-anchor="middle">${esc(it.l)}</text>` : '').join('');
  return `<svg class="chart" viewBox="0 0 ${w} ${h}" style="direction:ltr">${g}</svg>`;
}
function historyChart(a) {
  const D = S.D, w = 720, h = 250, pad = { l: 46, r: 14, t: 18, b: 30 };
  const last = D.meta.last_step;
  const rates = a.hist.filter(x => ok(x[1])), wins = a.hist.filter(x => ok(x[2]));
  const refs = [];
  if (a.v && ok(a.v.max_bid_partner) && a.status === 'active') refs.push({ v: a.v.max_bid_partner, t: 'سقف پیشنهاد', c: 'var(--good)' });
  if (a.v && ok(a.v.land_mkt)) refs.push({ v: a.v.land_mkt, t: 'بازار زمین', c: 'var(--info)' });
  const allv = [...rates.map(x => x[1]), ...wins.map(x => x[2]), ...refs.map(r => r.v)];
  if (!allv.length) return '<div class="empty">تاریخچهٔ قیمت ثبت نشده است.</div>';
  let lo = Math.min(...allv), hi = Math.max(...allv);
  const padv = (hi - lo) * 0.12 || hi * 0.1; lo = Math.max(0, lo - padv); hi += padv;
  const ticks = niceTicks(lo, hi, 4);
  lo = Math.min(lo, ticks[0]); hi = Math.max(hi, ticks[ticks.length - 1]);
  const X = s => pad.l + (s - 1) / Math.max(1, last - 1) * (w - pad.l - pad.r);
  const Y = v => pad.t + (1 - (v - lo) / (hi - lo)) * (h - pad.t - pad.b);
  let g = '<g class="grid">' + ticks.map(t => `<line x1="${pad.l}" x2="${w - pad.r}" y1="${Y(t)}" y2="${Y(t)}"/><text x="${pad.l - 7}" y="${Y(t) + 4}" text-anchor="end">${mil(t)}</text>`).join('') + '</g>';
  for (let s = 1; s <= last; s++) if (s === 1 || s % 5 === 0 || s === last) g += `<text x="${X(s)}" y="${h - 9}" text-anchor="middle">${fa(s)}</text>`;
  for (const r of refs) g += `<line x1="${pad.l}" x2="${w - pad.r}" y1="${Y(r.v)}" y2="${Y(r.v)}" stroke="${r.c}" stroke-dasharray="5 4" stroke-width="1.3"/><text x="${w - pad.r - 2}" y="${Y(r.v) - 5}" text-anchor="end" style="fill:${r.c};font-weight:700">${r.t} ${mil(r.v)}</text>`;
  if (rates.length) {
    const d = rates.map((p, i) => `${i ? 'L' : 'M'}${X(p[0])},${Y(p[1])}`).join('');
    g += `<path d="${d}L${X(rates[rates.length - 1][0])},${h - pad.b}L${X(rates[0][0])},${h - pad.b}Z" fill="var(--chart-fill)"/>`;
    g += `<path d="${d}" fill="none" stroke="var(--chart-line)" stroke-width="2.2" stroke-linejoin="round"/>`;
    g += rates.map(p => `<circle cx="${X(p[0])}" cy="${Y(p[1])}" r="3.6" fill="var(--surface)" stroke="var(--chart-line)" stroke-width="2"><title>مرحلهٔ ${fa(p[0])}: ${mil(p[1])} میلیون</title></circle>`).join('');
  }
  g += wins.map(p => `<path d="M${X(p[0])},${Y(p[2]) - 6}l6,6l-6,6l-6,-6z" fill="var(--chart-2)" stroke="var(--surface)" stroke-width="1.2"><title>برنده در مرحلهٔ ${fa(p[0])}: ${mil(p[2])} میلیون (${pct(p[3], true)})</title></path>`).join('');
  return `<svg class="chart" viewBox="0 0 ${w} ${h}" style="direction:ltr">${g}</svg>
    <div class="legend"><span><i style="background:var(--chart-line)"></i>قیمت پایهٔ هر مرحله (میلیون تومان/متر)</span><span><i style="background:var(--chart-2)"></i>پیشنهاد برنده</span>${refs.map(r => `<span><i style="background:${r.c}"></i>${r.t}</span>`).join('')}<span class="muted">محور افقی: شمارهٔ مرحله</span></div>`;
}

/* ================= views ================= */
const R = {}, AFTER = {};

R.overview = () => {
  const D = S.D, m = D.meta, sd = D.stage_diff, act = D.active;
  const cnt = vc => act.filter(a => a.vc === vc).length;
  const prevStage = D.stages.find(s => s.step === sd.prev) || {};
  const premPrev = median(sd.sold_prev.map(x => x.prem));
  const cityMed = D.stages.map(s => s.city_land_median_rate);
  const lastMed = [...cityMed].reverse().find(ok);
  const firstMed = cityMed.find(ok);
  const top = act.filter(a => ok(a.score) && !a.anomaly).sort((a, b) => b.score - a.score).slice(0, 8);
  const kpis = `<div class="kpis">
    <div class="kpi accent"><div class="kpi-l">قطعه‌های مسکونی در حال عرضه</div><div class="kpi-v">${fa(act.length)}<small>قطعه</small></div><div class="kpi-s">ارزش پایهٔ کل ${bil(sum(act.map(a => a.total)))} میلیارد تومان</div></div>
    <div class="kpi"><div class="kpi-l">تازه در مرحلهٔ ${fa(m.last_step)}</div><div class="kpi-v">${fa(sd.new.length)}<small>قطعه</small></div><div class="kpi-s">${fa(sd.carried.length)} از مراحل قبل · ${fa(sd.repriced.length)} با قیمت تازه</div></div>
    <div class="kpi"><div class="kpi-l">مناسب مشارکت ۶۰/۴۰</div><div class="kpi-v" style="color:var(--good)">${fa(cnt('buy'))}<small>قطعه</small></div><div class="kpi-s">به‌علاوهٔ ${fa(cnt('hold'))} قطعهٔ ارزان‌تر از بازار زمین</div></div>
    <div class="kpi"><div class="kpi-l">فروش مرحلهٔ ${fa(sd.prev)}</div><div class="kpi-v">${fa(sd.sold_prev.length)}<small>از ${fa(prevStage.residential)}</small></div><div class="kpi-s">میانهٔ اضافه‌پرداخت برنده ${pct(premPrev, false, 1)}</div></div>
    <div class="kpi"><div class="kpi-l">میانهٔ قیمت پایهٔ زمین (شهر)</div><div class="kpi-v">${mil(lastMed)}<small>میلیون/متر</small></div><div class="kpi-s"><span class="${clsSign(lastMed / firstMed - 1)}">${pct(lastMed / firstMed - 1, true)}</span> از مرحلهٔ ۱</div><div class="spark">${spark(cityMed, { w: 180, h: 30 })}</div></div>
  </div>`;
  const changes = D.changes && D.changes.items.length ? changesPanel(D.changes) : '';
  const best = `<div class="panel"><div class="panel-h"><h3>بهترین فرصت‌های این مرحله</h3><span class="hint">بر اساس امتیاز سرمایه‌گذاری (۱۰۰ = بهترین)</span><div class="tools"><a class="btn" href="#lots">همهٔ قطعه‌های فعال</a></div></div>
    <div class="panel-b flush">${table('top', [
      { k: 'star', t: '', sort: false, f: starBtn },
      { k: 'lot', t: 'قطعه', sort: false, cls: 'lot', f: lotCell },
      { k: 'vc', t: 'حکم', sort: false, f: a => vpill(a.vc) },
      { k: 'area', t: 'متراژ', n: 1, sort: false, f: a => m2(a.area) },
      { k: 'rl', t: 'پایه', n: 1, sort: false, f: a => mil(a.rl), tip: 'میلیون تومان در متر' },
      { k: 'cap', t: 'سقف پیشنهاد', n: 1, sort: false, f: a => `<b>${mil(a.v.max_bid_partner)}</b>` },
      { k: 'own', t: 'بازده مالک', n: 1, sort: false, f: a => `<span class="${clsSign(a.v.owner_real_ret_eff)}">${pct(a.v.owner_real_ret_eff)}</span>` },
      { k: 'score', t: 'امتیاز', n: 1, sort: false, f: a => `<span class="score">${fa(a.score)}</span>` },
    ], top, { click: true })}</div></div>`;
  const vcs = ['buy', 'thin', 'hold', 'avoid', 'na'];
  const mix = `<div class="panel"><div class="panel-h"><h3>ترکیب حکم قطعه‌های فعال</h3></div><div class="panel-b">
      <div class="mix">${vcs.map(v => cnt(v) ? `<i class="c-${v}" style="width:${cnt(v) / act.length * 100}%" title="${VC[v].t}: ${fa(cnt(v))}"></i>` : '').join('')}</div>
      <div class="legend">${vcs.map(v => `<span><i class="c-${v}"></i>${VC[v].t} <b>${fa(cnt(v))}</b></span>`).join('')}</div></div></div>`;
  const ins = `<div class="panel"><div class="panel-h"><h3>نکته‌های کلیدی</h3></div><div class="panel-b"><ul class="insights">${insights().map(x => `<li><span>${x}</span></li>`).join('')}</ul></div></div>`;
  const pulseItems = D.stages.map(s => ({ l: fa(s.step), v: s.sold, tip: `مرحلهٔ ${fa(s.step)} (${s.date_fa}): ${fa(s.sold)} فروش` }));
  const premItems = D.stages.map(s => ({ l: fa(s.step), v: s.median_premium, c: 'var(--chart-2)', tip: `مرحلهٔ ${fa(s.step)}: میانهٔ اضافه‌پرداخت ${pct(s.median_premium, false, 1)}` }));
  const pulse = `<div class="grid g-2e">
    <div class="panel"><div class="panel-h"><h3>تعداد قطعهٔ مسکونی فروخته‌شده در هر مرحله</h3></div><div class="panel-b">${bars(pulseItems)}</div></div>
    <div class="panel"><div class="panel-h"><h3>میانهٔ اضافه‌پرداخت برنده نسبت به قیمت پایه</h3></div><div class="panel-b">${bars(premItems, { fmt: v => pct(v), color: 'var(--chart-2)' })}</div></div></div>`;
  return `${kpis}${changes}<div class="grid g-2">${best}<div class="grid">${mix}${ins}</div></div>${stagePanel()}${pulse}`;
};

function insights() {
  const D = S.D, act = D.active, out = [];
  const top = act.filter(a => ok(a.score) && !a.anomaly).sort((a, b) => b.score - a.score)[0];
  if (top && top.v) out.push(`<b>بهترین گزینه:</b> ${esc(top.title)} (${m2(top.area)} متر). سقف پیشنهاد <b>${mil(top.v.max_bid_partner)} میلیون</b> در متر در برابر پایهٔ ${mil(top.rl)}، با بازده واقعی مالک ${pct(top.v.owner_real_ret_eff)} و سود سازنده ${pct(top.v.builder_margin)}.`);
  const buyLocs = [...new Set(act.filter(a => a.vc === 'buy').map(a => a.L.short))];
  if (buyLocs.length) out.push(`قطعه‌های «مناسب مشارکت» فقط در ${buyLocs.map(esc).join('، ')} هستند؛ تراکم بالا و قیمت آپارتمان نوساز آن‌جا هزینهٔ ساخت را جبران می‌کند.`);
  const holds = act.filter(a => a.vc === 'hold' && a.v).sort((a, b) => a.v.vs_land_mkt - b.v.vs_land_mkt);
  if (holds.length) out.push(`${fa(holds.length)} قطعه ارزان‌تر از بازار زمین قیمت خورده‌اند؛ بیشترین فاصله: ${esc(holds[0].title)} با ${pct(holds[0].v.vs_land_mkt)} نسبت به بازار.`);
  const cuts = D.stage_diff.repriced.filter(r => r.to < r.frm).sort((a, b) => a.to / a.frm - b.to / b.frm);
  if (cuts.length) { const a = assetFor(cuts[0].k); out.push(`بزرگ‌ترین کاهش قیمت این مرحله: ${esc(a.title)} از ${mil(cuts[0].frm)} به ${mil(cuts[0].to)} میلیون (${pct(cuts[0].to / cuts[0].frm - 1, true)}).`); }
  const prem = D.premium;
  out.push(`در کل فصل، میانهٔ اضافه‌پرداخت برنده‌ها ${pct(prem.median, false, 1)} بوده است. برای قطعه‌های پرطرفدار تا ۱۰ تا ۲۵٪ بالاتر از پایه هم پیشنهاد داده شده است.`);
  out.push('پرداخت اقساطی (۴۰٪ نقد و دو چک شش‌ماهه) با هزینهٔ سرمایهٔ ۳۵٪ معادل حدود ۱۲٪ تخفیف است و از ۱۰٪ تخفیف نقدی بهتر است.');
  return out;
}

function changesPanel(ch) {
  const label = { new: 'قطعهٔ تازه', status: 'تغییر وضعیت', price: 'تغییر قیمت پایه', verdict: 'تغییر حکم', maxbid: 'تغییر سقف پیشنهاد' };
  const icon = { new: 'plus', status: 'tag', price: 'up', verdict: 'target', maxbid: 'calc' };
  const items = ch.items.slice(0, 60).map(c => {
    const a = assetFor(c.k); if (!a) return '';
    let s = '';
    if (c.t === 'new') s = `${KIND[a.kind] || ''} · ${m2(a.area)} متر · ${mil(a.rl)} میلیون`;
    if (c.t === 'status') s = `${ST[c.frm] || c.frm} ← ${ST[c.to] || c.to}${c.price ? ` · <b>${tomanM2(c.price)}</b>` : ''}`;
    if (c.t === 'price') s = `${mil(c.frm)} ← ${mil(c.to)} میلیون (${pct(c.to / c.frm - 1, true)})`;
    if (c.t === 'verdict') s = `${VC[c.frm] ? VC[c.frm].t : c.frm} ← ${VC[c.to] ? VC[c.to].t : c.to}`;
    if (c.t === 'maxbid') s = `${mil(c.frm)} ← ${mil(c.to)} میلیون`;
    const w = W(a.k);
    return `<div class="li click" data-open="${a.k}"><span class="ico ${c.t}">${ic(icon[c.t])}</span><div class="grow"><div class="t">${esc(a.title)} ${w && w.star ? '<span class="pill sold plain">دنبال می‌کنید</span>' : ''}</div><div class="s">${label[c.t]}: ${s}</div></div></div>`;
  }).join('');
  return `<div class="panel"><div class="panel-h"><h3>تغییرات از به‌روزرسانی قبلی</h3><span class="hint">نسبت به ${esc(ch.since)} (مرحلهٔ ${fa(ch.since_step)}) · ${fa(ch.items.length)} تغییر</span></div><div class="panel-b flush"><div class="list" style="max-height:330px;overflow:auto">${items}</div></div></div>`;
}

function stagePanel() {
  const sd = S.D.stage_diff;
  const tabs = [
    ['new', `تازه در مرحلهٔ ${fa(sd.step)}`, sd.new.length],
    ['repriced', 'قیمت تازه', sd.repriced.length],
    ['sold', `فروخته در مرحلهٔ ${fa(sd.prev)}`, sd.sold_prev.length],
    ['left', 'خارج‌شده بدون برنده', sd.left_prev.length],
  ];
  const cur = S.tab.stage || 'new';
  let rows = '';
  if (cur === 'new') rows = sd.new.map(assetFor).sort((a, b) => (b.score || -1) - (a.score || -1)).map(a => li(a, `${KIND[a.kind] || ''} · ${m2(a.area)} متر · پایه ${mil(a.rl)} میلیون · کل ${bil(a.total)} میلیارد`, vpill(a.vc))).join('');
  if (cur === 'repriced') rows = sd.repriced.map(r => { const a = assetFor(r.k); return li(a, `مرحلهٔ ${fa(r.step)}: ${mil(r.frm)} ← اکنون ${mil(r.to)} میلیون`, `<b class="${clsSign(r.to / r.frm - 1)}">${pct(r.to / r.frm - 1, true)}</b>`); }).join('');
  if (cur === 'sold') rows = sd.sold_prev.sort((a, b) => (b.price || 0) - (a.price || 0)).map(r => { const a = assetFor(r.k); return li(a, `${m2(a.area)} متر · پایه ${tomanM2(rate_at_js(a, sd.prev))} · <span class="${clsSign(r.prem)}">${pct(r.prem, true, 1)} بالای پایه</span>${a.buyer ? ` · خریدار ${esc(a.buyer)}` : ''} · کل ${bil(r.price * a.area)} میلیارد`, `<span class="pill sold">فروخته شد · ${tomanM2(r.price)}</span>`); }).join('');
  if (cur === 'left') rows = sd.left_prev.map(assetFor).map(a => li(a, `آخرین پایه ${mil(a.rl)} میلیون · ${fa(a.n)} بار عرضه`, spill(a.status))).join('');
  return `<div class="panel"><div class="panel-h"><h3>تحولات مرحلهٔ ${fa(sd.step)} نسبت به ${fa(sd.prev)}</h3><span class="hint">${esc(S.D.stageDate[sd.step] || '')}</span></div>
    <div class="tabs">${tabs.map(([k, t, c]) => `<button class="${cur === k ? 'on' : ''}" data-tab="stage" data-v="${k}">${t}<span class="c">${fa(c)}</span></button>`).join('')}</div>
    <div class="list" style="max-height:420px;overflow:auto">${rows || '<div class="empty">موردی نیست.</div>'}</div></div>`;
}
const rate_at_js = (a, st) => { const h = a.hist.find(x => x[0] === st); return h ? h[1] : null; };
const li = (a, sub, right = '') => `<div class="li click" data-open="${a.k}">${starBtn(a)}<div class="grow"><div class="t">${esc(a.title)}${a.block ? ` <span class="muted small">بلوک ${esc(a.block)}</span>` : ''}</div><div class="s">${sub}</div></div><div class="r">${right}</div></div>`;

/* ---------- active lots screener ---------- */
R.lots = () => {
  const D = S.D, f = S.f.lots || (S.f.lots = { scope: 'all', loc: '', vcs: ['buy', 'thin', 'hold', 'avoid', 'na'], budget: '', amin: '', amax: '', star: false });
  let rows = D.active.filter(a => {
    if (f.scope === 'city' && a.scope !== 'city') return false;
    if (f.scope === 'sub' && a.scope === 'city') return false;
    if (f.loc && a.loc !== f.loc) return false;
    if (!f.vcs.includes(a.vc)) return false;
    if (f.budget && a.total > +f.budget * 1e9) return false;
    if (f.amin && a.area < +f.amin) return false;
    if (f.amax && a.area > +f.amax) return false;
    if (f.star && !(W(a.k) || {}).star) return false;
    return true;
  });
  const locs = [...new Set(D.active.map(a => a.loc))].map(l => [l, (D.locs[l] || {}).short || l]).sort((a, b) => a[1].localeCompare(b[1], 'fa'));
  const filt = `<div class="panel"><div class="panel-b"><div class="filters">
    <div class="field"><label>محدوده</label><div class="seg">${[['all', 'همه'], ['city', 'شهر مشهد'], ['sub', 'حومه']].map(([k, t]) => `<button class="${f.scope === k ? 'on' : ''}" data-f="lots.scope" data-v="${k}">${t}</button>`).join('')}</div></div>
    <div class="field w-m"><label for="f-loc">محله</label><select id="f-loc" class="inp" data-f="lots.loc"><option value="">همهٔ محله‌ها</option>${locs.map(([k, t]) => `<option value="${k}" ${f.loc === k ? 'selected' : ''}>${esc(t)}</option>`).join('')}</select></div>
    <div class="field w-s"><label for="f-budget">سقف بودجهٔ کل</label><div class="unit"><input id="f-budget" class="inp" type="number" min="0" step="1" value="${esc(f.budget)}" data-f="lots.budget" placeholder="همه"><span>میلیارد</span></div></div>
    <div class="field w-s"><label for="f-amin">متراژ از</label><input id="f-amin" class="inp" type="number" min="0" value="${esc(f.amin)}" data-f="lots.amin"></div>
    <div class="field w-s"><label for="f-amax">تا</label><input id="f-amax" class="inp" type="number" min="0" value="${esc(f.amax)}" data-f="lots.amax"></div>
    <div class="field"><label>حکم</label><div class="chips">${Object.keys(VC).map(v => `<button class="chip ${f.vcs.includes(v) ? 'on' : ''}" data-fv="${v}">${VC[v].t}</button>`).join('')}</div></div>
    <label class="check"><input type="checkbox" data-f="lots.star" ${f.star ? 'checked' : ''}> فقط دنبال‌شده‌ها</label>
  </div></div></div>`;
  const cols = [
    { k: 'star', t: '', sort: false, f: starBtn },
    { k: 'title', t: 'قطعه', cls: 'lot', f: lotCell, v: a => a.L.short + ' ' + String(a.qate).padStart(4, '0') },
    { k: 'vc', t: 'حکم', f: a => vpill(a.vc), v: a => ['buy', 'thin', 'hold', 'avoid', 'na'].indexOf(a.vc) * -1 },
    { k: 'score', t: 'امتیاز', n: 1, f: a => ok(a.score) ? `<span class="score">${fa(a.score)}</span>` : '—' },
    { k: 'area', t: 'متراژ', n: 1, f: a => m2(a.area) },
    { k: 'rl', t: 'پایه (م/متر)', n: 1, f: a => mil(a.rl) },
    { k: 'total', t: 'کل (میلیارد)', n: 1, f: a => bil(a.total) },
    { k: 'floors', t: 'طبقات', n: 1, f: a => a.v ? fa(a.v.floors) : '—', v: a => a.v && a.v.floors },
    { k: 'om2', t: 'سهم ۴۰٪ مالک', n: 1, f: a => a.v ? `${m2(a.v.owner_m2)} م` : '—', v: a => a.v && a.v.owner_m2, tip: 'متر مربع آپارتمان قابل فروش سهم صاحب زمین' },
    { k: 'own', t: 'بازده واقعی مالک', n: 1, f: a => a.v ? barPct(a.v.owner_real_ret_eff, 0.4) : '—', v: a => a.v && a.v.owner_real_ret_eff },
    { k: 'bm', t: 'سود سازنده', n: 1, f: a => a.v ? `<span class="${a.v.builder_margin >= 0.25 ? 'up' : a.v.builder_margin < 0.15 ? 'down' : ''}">${pct(a.v.builder_margin)}</span>` : '—', v: a => a.v && a.v.builder_margin },
    { k: 'cap', t: 'سقف پیشنهاد', n: 1, f: a => a.v ? `<b>${mil(a.v.max_bid_partner)}</b>` : '—', v: a => a.v && a.v.max_bid_partner },
    { k: 'room', t: 'جای رشد قیمت', n: 1, f: a => ok(a.room) ? `<span class="${clsSign(a.room)}">${pct(a.room, true)}</span>` : '—', tip: 'سقف پیشنهاد نسبت به قیمت پایهٔ فعلی' },
    { k: 'mkt', t: 'نسبت به بازار زمین', n: 1, f: a => a.v && ok(a.v.vs_land_mkt) ? `<span class="${clsSign(-a.v.vs_land_mkt)}">${pct(a.v.vs_land_mkt, true)}</span>` : '—', v: a => a.v && a.v.vs_land_mkt },
    { k: 'first', t: 'اولین عرضه', n: 1, f: a => `مرحلهٔ ${fa(a.first)}${a.n > 1 ? ` · ${fa(a.n)} بار` : ''}` },
  ];
  const foot = `<tfoot><tr><td></td><td colspan="5">${fa(rows.length)} قطعه</td><td class="n">${bil(sum(rows.map(a => a.total)))}</td><td colspan="9"></td></tr></tfoot>`;
  return `${filt}<div class="panel">${table('lots', cols, rows, { sort: { k: 'score', d: 'desc' }, foot })}</div>
    <p class="small muted" style="margin:0">بازده واقعی مالک یعنی بازده سهم ۴۰٪ صاحب زمین بعد از تورم و با احتساب اقساط، در ${fa(S.D.meta.months + 3)} ماه. سقف پیشنهاد بالاترین قیمت هر متر زمین است که هنوز ۱۵٪ بازده واقعی می‌دهد.</p>`;
};

/* ---------- map ---------- */
const ESRI = 'https://server.arcgisonline.com/ArcGIS/rest/services/';
const TILES = {
  light: { t: 'نقشهٔ روشن', a: 'Esri, HERE, OpenStreetMap', l: [[ESRI + 'Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', 16], [ESRI + 'Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}', 16]] },
  dark: { t: 'نقشهٔ تیره', a: 'Esri, HERE, OpenStreetMap', l: [[ESRI + 'Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', 16], [ESRI + 'Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}', 16]] },
  osm: { t: 'خیابان‌ها (نام فارسی)', a: '© OpenStreetMap', l: [['https://tile.openstreetmap.org/{z}/{x}/{y}.png', 19]] },
  sat: { t: 'ماهواره + معابر', a: 'Esri World Imagery', l: [[ESRI + 'World_Imagery/MapServer/tile/{z}/{y}/{x}', 19], [ESRI + 'Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}', 19], [ESRI + 'Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', 19]] },
};
const isDark = () => (document.documentElement.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')) === 'dark';
function baseLayers() {
  const out = {};
  for (const [k, t] of Object.entries(TILES)) {
    out[k] = L.layerGroup(t.l.map(([u, z], i) => L.tileLayer(u, { attribution: i ? '' : t.a, maxZoom: 20, maxNativeZoom: z })));
  }
  return out;
}
function colorOf(a, mode) {
  if (mode === 'price') {
    const v = a.rl || a.wprice || 0, t = Math.max(0, Math.min(1, Math.log(Math.max(v, 5e6) / 5e6) / Math.log(250e6 / 5e6)));
    return `hsl(${Math.round(150 - t * 150)} 62% ${isDark() ? 52 : 40}%)`;
  }
  if (a.status === 'active') return { buy: cssv('--good'), thin: cssv('--warn'), hold: cssv('--info'), avoid: cssv('--bad'), na: cssv('--na') }[a.vc] || cssv('--na');
  if (a.status === 'sold') return cssv('--brass');
  return cssv('--na');
}
R.map = () => {
  const f = S.f.map || (S.f.map = { st: ['active', 'sold', 'withdrawn'], mode: 'verdict', base: '', approx: false });
  const withPos = S.D.assets.filter(a => a.geo);
  const exact = withPos.filter(a => !a.geo.approx).length;
  return `<div class="panel"><div class="panel-h">
      <div class="chips">${[['active', 'در حال عرضه'], ['sold', 'فروخته‌شده'], ['withdrawn', 'خارج‌شده']].map(([k, t]) => `<button class="chip ${f.st.includes(k) ? 'on' : ''}" data-mapst="${k}">${t}</button>`).join('')}</div>
      <div class="seg">${[['verdict', 'رنگ: حکم و وضعیت'], ['price', 'رنگ: قیمت هر متر']].map(([k, t]) => `<button class="${f.mode === k ? 'on' : ''}" data-mapmode="${k}">${t}</button>`).join('')}</div>
      <label class="check"><input type="checkbox" data-mapapprox ${f.approx ? 'checked' : ''}> موقعیت‌های تقریبی قطعه‌های قدیمی</label>
      <span class="hint">${fa(exact)} قطعه با مختصات دقیق کروکی${withPos.length > exact ? ` · ${fa(withPos.length - exact)} تقریبی` : ''} · ${fa(S.D.assets.length - withPos.length)} بدون موقعیت</span>
    </div>
    <div style="position:relative">
      <div id="bigmap" style="height:calc(100vh - 200px);min-height:420px;direction:ltr"></div>
      <div id="mapLegend" class="map-legend"></div>
    </div></div>`;
};
AFTER.map = () => {
  if (!window.L) { $('#bigmap').innerHTML = '<div class="empty">کتابخانهٔ نقشه بارگذاری نشد.</div>'; return; }
  const f = S.f.map;
  const map = L.map('bigmap', { zoomControl: true, preferCanvas: true, attributionControl: true }).setView([36.31, 59.56], 11);
  S.maps.big = map;
  const bl = baseLayers();
  const baseKey = f.base || 'sat';
  bl[baseKey].addTo(map);
  L.control.layers(Object.fromEntries(Object.entries(bl).map(([k, l]) => [TILES[k].t, l])), {}, { position: 'topright' }).addTo(map);
  map.on('baselayerchange', e => { f.base = Object.keys(TILES).find(k => TILES[k].t === e.name); store.set('filters', S.f); });
  L.control.scale({ imperial: false, position: 'bottomright' }).addTo(map);
  const pts = [];
  const order = a => a.status === 'active' ? 2 : a.status === 'sold' ? 1 : 0;
  const list = S.D.assets.filter(a => a.geo && (!a.geo.approx || f.approx || a.status === 'active')
    && f.st.includes(a.status === 'sold_relisted_gone' ? 'withdrawn' : a.status)).sort((a, b) => order(a) - order(b));
  for (const a of list) {
    const r = Math.max(4, Math.min(13, Math.sqrt(a.area || 100) / 3.2)) * (a.status === 'active' ? 1.15 : 0.85);
    const c = colorOf(a, f.mode);
    const mk = L.circleMarker([a.geo.lat, a.geo.lon], { radius: r, color: a.status === 'active' ? (isDark() ? '#0a110f' : '#ffffff') : c, weight: a.status === 'active' ? 2 : 1, fillColor: c, fillOpacity: a.geo.approx ? 0.35 : (a.status === 'active' ? 0.92 : 0.6), dashArray: a.geo.approx ? '3 3' : null });
    mk.bindTooltip(`${esc(a.title)} · ${m2(a.area)} م${isSold(a) ? ' · ' + stagText(a) : ''}`, { direction: 'top', offset: [0, -r] });
    mk.bindPopup(() => popupHtml(a), { maxWidth: 300, minWidth: 250 });
    mk.addTo(map); pts.push([a.geo.lat, a.geo.lon]);
  }
  if (pts.length) map.fitBounds(L.latLngBounds(pts).pad(0.05), { maxZoom: 14 });
  const soldLabels = L.layerGroup(list.filter(isSold).map(a => L.marker([a.geo.lat, a.geo.lon], { interactive: false, keyboard: false,
    icon: L.divIcon({ className: 'sold-lbl', html: `<span>فروخته · ${mil(a.wprice)}</span>`, iconSize: null, iconAnchor: [-9, 9] }) })));
  const syncLabels = () => (map.getZoom() >= 19 ? soldLabels.addTo(map) : soldLabels.remove());   // plots are ~12 m wide: labels fit from zoom 19
  map.on('zoomend', syncLabels); syncLabels();
  $('#mapLegend').innerHTML = f.mode === 'price'
    ? `<b>قیمت پایه هر متر</b><div class="grad"></div><div class="gl"><span>۵ میلیون</span><span>۲۵۰ میلیون</span></div>`
    : `<b>حکم قطعه‌های فعال</b>${['buy', 'thin', 'hold', 'avoid', 'na'].map(v => `<span><i class="c-${v}"></i>${VC[v].t}</span>`).join('')}<span><i style="background:var(--brass)"></i>فروخته‌شده</span><span><i style="background:var(--na);opacity:.6"></i>خارج‌شده</span><span class="muted">اندازهٔ دایره = متراژ</span>`;
};
function popupHtml(a) {
  const v = a.v;
  return `<div class="pop"><div class="pop-h"><b>${esc(a.title)}</b>${a.block ? `<span class="muted"> · بلوک ${esc(a.block)}</span>` : ''}</div>
    <div class="pop-tags">${stag(a)} ${vpill(a.status === 'active' ? a.vc : null)}</div>
    <dl class="kv">
      <dt>متراژ</dt><dd>${m2(a.area)} متر</dd>
      <dt>${isSold(a) ? 'قیمت فروش' : 'قیمت پایه'}</dt><dd>${isSold(a) ? tomanM2(a.wprice) : mil(a.rl) + ' میلیون/متر'}</dd>
      ${v && a.status === 'active' ? `<dt>سقف پیشنهاد</dt><dd><b>${mil(v.max_bid_partner)}</b> میلیون</dd><dt>بازده واقعی مالک</dt><dd>${pct(v.owner_real_ret_eff)}</dd>` : ''}
      <dt>مراحل</dt><dd>${fa(a.first)} تا ${fa(a.last)}</dd>
    </dl>
    <button class="btn primary" data-open="${a.k}" style="width:100%;justify-content:center;margin-top:8px">پروندهٔ کامل قطعه</button>${a.geo && a.geo.approx ? '<div class="xs muted" style="margin-top:6px">موقعیت تقریبی (از قطعه‌های هم‌محله)</div>' : ''}</div>`;
}

/* ---------- calculator ---------- */
function calcDefaults(a) {
  const P = S.D.params;
  if (!a || !a.v) {
    const L0 = S.D.locs.emamat74;
    return { k: '', area: 300, rate: 180e6, prem: 0.03, pNew: L0.p_new, hard: Calc.hardCost(L0.p_new), floors: 6, far: null, shape: 1, adj: 0, cost_mult: 1, net_ratio: null,
      bs: P.PARTNER_BUILDER_SHARE, pay: 'inst', cc: P.CAPITAL_COST, months: P.MONTHS, bt: P.BUILDER_TARGET, ot: P.OWNER_TARGET, hair: P.SALE_HAIRCUT, xf: false, landMkt: L0.land };
  }
  const v = a.v, fct = v.facts || {};
  return { k: a.k, area: a.area, rate: v.land_rate_toman, prem: v.exp_premium || 0, pNew: v.p_new, hard: Calc.hardCost(v.p_new), floors: fct.far ? (fct.floors || Math.round(fct.far / P.OCCUPANCY)) : fct.floors,
    far: fct.far || null, shape: fct.shape || 1, adj: fct.adj || 0, cost_mult: fct.cost_mult || 1, net_ratio: fct.net_ratio || null,
    bs: P.PARTNER_BUILDER_SHARE, pay: 'inst', cc: P.CAPITAL_COST, months: P.MONTHS, bt: P.BUILDER_TARGET, ot: P.OWNER_TARGET, hair: P.SALE_HAIRCUT, xf: false, landMkt: v.land_mkt };
}
function calcRun(c, over = {}) {
  const facts = { floors: c.floors, shape: c.shape, adj: c.adj, cost_mult: c.cost_mult };
  if (c.far && c.floorsUntouched) facts.far = c.far;
  if (c.net_ratio) facts.net_ratio = c.net_ratio;
  return Calc.appraise(S.D.params, { area: c.area, rate: over.rate != null ? over.rate : c.rate, premium: c.prem, pNew: c.pNew * (over.pk || 1), facts,
    hardPpm: c.hard, builderShare: c.bs, capitalCost: c.cc, months: c.months, builderTarget: c.bt, ownerTarget: c.ot,
    saleHaircut: c.hair, payment: c.pay, extraFloor: c.xf });
}
R.calc = (k) => {
  const a = k != null ? assetFor(k) : (S.calc && S.calc.k ? assetFor(S.calc.k) : S.D.active.filter(x => ok(x.score)).sort((x, y) => y.score - x.score)[0]);
  if (!S.calc || (k != null && S.calc.k !== (a && a.k)) || (a && S.calc.k == null)) { S.calc = { ...calcDefaults(a), floorsUntouched: true }; }
  const c = S.calc;
  const opts = S.D.active.filter(x => x.v).sort((x, y) => (y.score || 0) - (x.score || 0));
  const num = (id, lbl, val, unit, step, help = '') => `<div class="field"><label for="c-${id}">${lbl}</label><div class="unit"><input id="c-${id}" class="inp" type="number" step="${step}" value="${val}" data-c="${id}"><span>${unit}</span></div>${help ? `<div class="help">${help}</div>` : ''}</div>`;
  const r1 = x => Math.round(x * 10) / 10;
  return `<div class="calc">
    <div class="panel calc-in"><div class="panel-h"><h3>ورودی‌ها</h3><div class="tools"><button class="btn" data-calc-reset>بازگشت به پیش‌فرض</button></div></div><div class="panel-b">
      <div class="field"><label for="c-lot">قطعه</label><select id="c-lot" class="inp" data-c="lot"><option value="">قطعهٔ دلخواه (ورود دستی)</option>${opts.map(x => `<option value="${x.k}" ${x.k === c.k ? 'selected' : ''}>${esc(x.title)} · ${m2(x.area)} م · ${VC[x.vc].t}</option>`).join('')}</select></div>
      <div class="fgrid">
        ${num('area', 'متراژ زمین', r1(c.area), 'متر', 1)}
        ${num('rate', 'قیمت پایهٔ هر متر', r1(c.rate / 1e6), 'میلیون', 0.5)}
        ${num('prem', 'اضافه‌پرداخت پیشنهادی', r1(c.prem * 100), '٪', 0.5, 'بالاتر از قیمت پایه')}
        ${num('pNew', 'قیمت آپارتمان نوساز', r1(c.pNew / 1e6), 'میلیون', 1, 'آگهی‌شده در محله')}
        ${num('hair', 'کسر از قیمت آگهی', r1((1 - c.hair) * 100), '٪', 1, 'چانه‌زنی و موقوفه بودن')}
        ${num('hard', 'هزینهٔ اجرای هر متر', r1(c.hard / 1e6), 'میلیون', 0.5, 'هزینهٔ سخت، بدون عوارض')}
        ${num('floors', 'طبقات روی پیلوت', c.floors, 'طبقه', 1, c.far && c.floorsUntouched ? `تراکم چاپ‌شده ${pct(c.far)} اعمال شده` : 'سطح اشغال ۶۰٪')}
        ${num('shape', 'ضریب شکل قطعه', c.shape, '×', 0.05, '۱ = مستطیل کامل')}
        ${num('bs', 'سهم سازنده', r1(c.bs * 100), '٪', 1)}
        ${num('months', 'مدت مجوز و ساخت', c.months, 'ماه', 1)}
        ${num('cc', 'هزینهٔ سرمایه سالانه', r1(c.cc * 100), '٪', 1, 'برای ارزش فعلی چک‌ها')}
        ${num('bt', 'سود هدف سازنده', r1(c.bt * 100), '٪', 1)}
        ${num('ot', 'بازده هدف مالک', r1(c.ot * 100), '٪', 1, 'برای سقف پیشنهاد')}
        <div class="field"><label>روش پرداخت زمین</label><div class="seg">${[['inst', '۴۰٪ نقد + ۲ چک'], ['cash', 'نقد با ۱۰٪ تخفیف']].map(([kk, t]) => `<button class="${c.pay === kk ? 'on' : ''}" data-cpay="${kk}">${t}</button>`).join('')}</div></div>
        <label class="check wide"><input type="checkbox" data-c="xf" ${c.xf ? 'checked' : ''}> خرید یک طبقهٔ مازاد (عوارض ۲۵٪ ارزش آن طبقه)</label>
      </div>
    </div></div>
    <div class="grid" id="calcOut">${calcOut()}</div>
  </div>`;
};
function calcOut() {
  const c = S.calc, r = calcRun(c);
  const bidRate = c.rate * (1 + c.prem);
  const vsMkt = c.landMkt ? bidRate / c.landMkt - 1 : null;
  const vc = Calc.verdict(r, vsMkt);
  const capGap = r.maxBidPartner / bidRate - 1;
  const ownerUnits = r.ownerM2 * (r.ownerRealShare / (1 - r.builderShare || 1)) / r.unitSize;
  const dec = `<div class="decision ${vc}"><div><div class="cap-l">سقف پیشنهاد هر متر زمین</div><div class="cap-v">${mil(r.maxBidPartner)} <small>میلیون تومان</small></div><div class="cap-l">پیشنهاد شما ${mil(bidRate)} · <span class="${clsSign(capGap)}">${capGap >= 0 ? 'زیر سقف' : 'بالای سقف'} ${pct(Math.abs(capGap))}</span></div></div>
    <div>${vpill(vc)}<p style="margin-top:6px">${VC[vc].d}</p></div></div>`;
  const tiles = `<div class="tiles">
    <div class="tile"><div class="l">بازده واقعی مالک (کل دوره)</div><div class="v ${clsSign(r.ownerRealRetEff)}">${pct(r.ownerRealRetEff)}</div></div>
    <div class="tile"><div class="l">بازده واقعی سالانه</div><div class="v ${clsSign(r.ownerRealAnnEff)}">${pct(r.ownerRealAnnEff)}</div></div>
    <div class="tile"><div class="l">سود سازنده روی هزینه</div><div class="v ${r.builderMargin >= r.builderTarget ? 'up' : 'down'}">${pct(r.builderMargin)}</div></div>
    <div class="tile"><div class="l">سهم مالک از آپارتمان‌ها</div><div class="v">${m2(r.ownerM2 * (r.ownerRealShare / (1 - r.builderShare || 1)))} <small>متر</small></div></div>
    <div class="tile"><div class="l">ارزش سهم مالک</div><div class="v">${bil(r.ownerRealValue)} <small>میلیارد</small></div></div>
    <div class="tile"><div class="l">هزینهٔ مؤثر زمین</div><div class="v">${bil(r.ownerCostEff)} <small>میلیارد</small></div></div>
  </div>`;
  const shareNote = r.ownerRealShare < (1 - r.builderShare) - 0.001
    ? `<div class="callout warn">با این فرض‌ها سازنده در تقسیم ${pct(r.builderShare)}/${pct(1 - r.builderShare)} به سود ${pct(r.builderTarget)} نمی‌رسد. سهم منصفانهٔ مالک فقط ${pct(Math.max(0, r.ownerFair))} است و بازده بالا با همین سهم حساب شده است.</div>` : '';
  const prog = `<div class="panel"><div class="panel-h"><h3>برنامهٔ ساخت</h3><span class="hint">سطح اشغال ۶۰٪ · راندمان فروش‌پذیر ${pct(S.D.params.NET_TO_GROSS)}</span></div><div class="panel-b"><div class="tiles">
    <div class="tile"><div class="l">طبقات روی پیلوت</div><div class="v">${fa(r.floors)}</div></div>
    <div class="tile"><div class="l">تراکم</div><div class="v">${pct(r.far)}</div></div>
    <div class="tile"><div class="l">زیربنای هر طبقه</div><div class="v">${m2(r.footprint)} <small>م</small></div></div>
    <div class="tile"><div class="l">زیربنای مسکونی</div><div class="v">${m2(r.gross)} <small>م</small></div></div>
    <div class="tile"><div class="l">قابل فروش</div><div class="v">${m2(r.net)} <small>م</small></div></div>
    <div class="tile"><div class="l">واحدها</div><div class="v">${fa(r.units)} <small>× ${fa(r.unitSize)} م</small></div></div>
    <div class="tile"><div class="l">پارکینگ پیلوت</div><div class="v">${fa(Math.min(r.units, r.groundSpaces))} <small>از ${fa(r.units)}</small></div></div>
    <div class="tile"><div class="l">زیرزمین</div><div class="v">${r.basement ? m2(r.basement) + ' <small>م</small>' : 'لازم نیست'}</div></div>
  </div></div></div>`;
  const money = `<div class="grid g-2e">
    <div class="panel"><div class="panel-h"><h3>مشارکت ${pct(r.builderShare)} سازنده / ${pct(1 - r.builderShare)} مالک</h3></div><div class="panel-b">
      <div class="split"><div class="own" style="width:${(1 - r.builderShare) * 100}%">مالک ${m2(r.ownerM2)} م</div><div class="bld" style="width:${r.builderShare * 100}%">سازنده ${m2(r.builderM2)} م</div></div>
      <dl class="kv" style="margin-top:12px">
        <dt>قیمت فروش مؤثر هر متر</dt><dd>${mil(r.salePpm)} میلیون</dd>
        <dt>درآمد سازنده</dt><dd>${bil(r.builderRev)} میلیارد</dd>
        <dt>هزینهٔ کل سازنده</dt><dd>${bil(r.builderCost)} میلیارد</dd>
        <dt>هزینهٔ ساخت هر متر فروش‌پذیر</dt><dd>${mil(r.buildCostPerNet)} میلیون</dd>
        <dt>سهم منصفانهٔ مالک</dt><dd>${pct(Math.max(0, r.ownerFair))}</dd>
        <dt>قیمت تمام‌شدهٔ هر متر برای مالک</dt><dd>${mil(r.ownerCostPerM2)} میلیون</dd>
        <dt>ضریب ارزش فعلی پرداخت</dt><dd>${fa(r.pv, 3)}</dd>
      </dl></div></div>
    <div class="panel"><div class="panel-h"><h3>اگر خودتان بسازید</h3></div><div class="panel-b"><dl class="kv">
        <dt>ارزش فروش کل پروژه</dt><dd>${bil(r.gdv)} میلیارد</dd>
        <dt>زمین با هزینهٔ انتقال</dt><dd>${bil(r.land)} میلیارد</dd>
        <dt>اجرا (اسکلت تا نازک‌کاری)</dt><dd>${bil(r.hard)} میلیارد</dd>
        <dt>عوارض، مهندسی و پیش‌بینی‌نشده</dt><dd>${bil(r.soft)} میلیارد</dd>
        <dt>هزینهٔ فروش</dt><dd>${bil(r.selling)} میلیارد</dd>
        <dt class="tot">سود</dt><dd class="tot ${clsSign(r.profit)}">${bil(r.profit)} میلیارد · ${pct(r.margin)}</dd>
        <dt>حداکثر قیمت زمین برای ۲۵٪ سود</dt><dd>${mil(r.rlv)} میلیون/متر</dd>
        <dt>سود در سناریوی بدبینانه</dt><dd class="${clsSign(r.marginStress)}">${pct(r.marginStress)}</dd>
      </dl></div></div></div>`;
  // sensitivity: owner real return vs bid (rows) and sale price (cols)
  const bidKs = [-0.10, -0.05, 0, 0.05, 0.10, 0.20], pks = [-0.15, -0.10, -0.05, 0, 0.05, 0.10];
  const cell = v => { const t = Math.max(-1, Math.min(1, v / 0.4)); const col = t >= 0 ? 'var(--good)' : 'var(--bad)'; return `background:color-mix(in srgb, ${col} ${Math.round(Math.abs(t) * 55 + 6)}%, var(--surface));`; };
  const heat = `<div class="panel"><div class="panel-h"><h3>حساسیت بازده واقعی مالک</h3><span class="hint">ردیف: قیمت پیشنهادی شما · ستون: تغییر قیمت آپارتمان</span></div><div class="panel-b"><div class="tbl-wrap"><table class="heat" style="width:100%;border-collapse:collapse">
    <thead><tr><th>پیشنهاد (میلیون)</th>${pks.map(p => `<th>${p ? pct(p, true) : 'قیمت فعلی'}</th>`).join('')}</tr></thead><tbody>
    ${bidKs.map(b => { const rate = bidRate * (1 + b); return `<tr><th>${mil(rate)}</th>${pks.map(p => { const x = calcRun({ ...c, prem: 0 }, { rate, pk: 1 + p }).ownerRealRetEff; return `<td class="${!b && !p ? 'cur' : ''}" style="${cell(x)}">${pct(x)}</td>`; }).join('')}</tr>`; }).join('')}
    </tbody></table></div></div></div>`;
  return dec + tiles + shareNote + prog + money + heat;
}
AFTER.calc = () => {};

/* ---------- market ---------- */
R.market = () => {
  const D = S.D;
  const minis = Object.entries(D.series).map(([k, s]) => {
    const vals = Array.from({ length: D.meta.last_step }, (_, i) => { const p = s.pts.find(x => x[0] === i + 1); return p ? p[1] : null; });
    const f = s.pts[0][1], l = s.pts[s.pts.length - 1][1];
    return `<a class="mini" href="#archive-${k}" style="text-decoration:none;color:inherit"><div class="h"><b>${esc((D.locs[k] || {}).short || s.name)}</b><span class="xs ${clsSign(l / f - 1)}">${pct(l / f - 1, true)}</span></div>
      <div class="v">${mil(l)} <span class="xs muted">میلیون/متر</span></div>${spark(vals, { w: 220, h: 40 })}<div class="xs muted">مرحلهٔ ${fa(s.pts[0][0])} تا ${fa(s.pts[s.pts.length - 1][0])} · ${fa(s.pts.length)} مرحله</div></a>`;
  }).join('');
  const locCols = [
    { k: 'short', t: 'محله', f: r => `<b>${esc(r.short)}</b><span class="sub muted xs" style="display:block">${r.district ? `منطقهٔ ${fa(r.district)} · ` : ''}${SCOPE[r.scope] || ''}</span>`, cls: 'lot' },
    { k: 'assets', t: 'قطعه', n: 1, f: r => fa(r.assets) },
    { k: 'sold', t: 'فروش', n: 1, f: r => fa(r.sold) },
    { k: 'active', t: 'فعال', n: 1, f: r => fa(r.active) },
    { k: 'sell_through', t: 'نرخ فروش', n: 1, f: r => pct(r.sell_through) },
    { k: 'median_premium', t: 'اضافه‌پرداخت', n: 1, f: r => pct(r.median_premium, false, 1) },
    { k: 'rate_first', t: 'پایهٔ اول', n: 1, f: r => mil(r.rate_first) },
    { k: 'rate_last', t: 'پایهٔ آخر', n: 1, f: r => mil(r.rate_last) },
    { k: 'new_lot_change', t: 'رشد قطعه‌های تازه', n: 1, f: r => ok(r.new_lot_change) ? `<span class="${clsSign(r.new_lot_change)}">${pct(r.new_lot_change, true)}</span>` : '—', tip: 'قیمت پایهٔ قطعه‌های تازهٔ مراحل ۱۸ به بعد نسبت به مراحل ۱ تا ۹' },
    { k: 'same_plot_annual', t: 'رشد سالانهٔ همان قطعه', n: 1, f: r => ok(r.same_plot_annual) ? pct(r.same_plot_annual, true) : '—' },
    { k: 'p_new', t: 'آپارتمان نوساز', n: 1, f: r => mil(r.p_new) },
    { k: 'land_mkt', t: 'بازار زمین', n: 1, f: r => mil(r.land_mkt) },
  ];
  const locRows = D.loc_rows.map(r => ({ ...r, k: null }));
  const stCols = [
    { k: 'step', t: 'مرحله', n: 1, f: s => `<b>${fa(s.step)}</b>` },
    { k: 'date_fa', t: 'تاریخ', f: s => esc(s.date_fa), v: s => s.step },
    { k: 'listings', t: 'کل آگهی‌ها', n: 1, f: s => fa(s.listings) },
    { k: 'residential', t: 'مسکونی', n: 1, f: s => fa(s.residential) },
    { k: 'new_assets', t: 'قطعهٔ تازه', n: 1, f: s => fa(s.new_assets) },
    { k: 'sold', t: 'فروش', n: 1, f: s => fa(s.sold) },
    { k: 'median_premium', t: 'میانهٔ اضافه‌پرداخت', n: 1, f: s => pct(s.median_premium, false, 1) },
    { k: 'city_land_median_rate', t: 'میانهٔ پایهٔ زمین شهر', n: 1, f: s => mil(s.city_land_median_rate) },
    { k: 'buyers_company', t: 'برندهٔ حقوقی', n: 1, f: s => fa(s.buyers_company) },
  ];
  return `<div class="sec-title"><h2>روند قیمت پایهٔ زمین، محله به محله</h2><p>میانهٔ قیمت پایهٔ هر مرحله (میلیون تومان در متر). روی هر کارت بزنید تا قطعه‌های آن محله را ببینید.</p></div>
    <div class="mini-grid">${minis}</div>
    <div class="panel"><div class="panel-h"><h3>کارنامهٔ محله‌ها</h3><span class="hint">قیمت‌ها میلیون تومان در متر</span></div>${table('locs', locCols, locRows, { sort: { k: 'assets', d: 'desc' }, click: false, maxH: 560 })}</div>
    <div class="panel"><div class="panel-h"><h3>آمار مراحل</h3><span class="hint">${fa(D.meta.missing_stage2)} آگهی از مرحلهٔ ۲ به‌خاطر خطای سرور سایت دریافت نشد</span></div>${table('stages', stCols, D.stages.map(s => ({ ...s, k: null })), { sort: { k: 'step', d: 'desc' }, click: false, maxH: 560 })}</div>`;
};

/* ---------- archive ---------- */
R.archive = () => {
  const D = S.D, f = S.f.archive || (S.f.archive = { preset: 'all', status: '', kind: '', scope: '', loc: '', q: '' });
  let rows = D.assets;
  if (f.preset === 'gone') { const idx = new Map(D.gone_top.map((k, i) => [k, i])); rows = rows.filter(a => idx.has(a.k)); }
  if (f.preset === 'repriced') { const s = new Set(D.repriced); rows = rows.filter(a => s.has(a.k)); }
  rows = rows.filter(a => (!f.status || a.status === f.status) && (!f.kind || a.kind === f.kind) && (!f.scope || a.scope === f.scope) && (!f.loc || a.loc === f.loc));
  if (f.q) { const t = norm(f.q).split(/\s+/).filter(Boolean); rows = rows.filter(a => t.every(x => a.q.includes(x))); }
  const locs = [...new Set(D.assets.map(a => a.loc))].filter(Boolean).map(l => [l, (D.locs[l] || {}).short || l]).sort((a, b) => a[1].localeCompare(b[1], 'fa'));
  const sel = (key, label, opts) => `<div class="field w-m"><label for="a-${key}">${label}</label><select id="a-${key}" class="inp" data-f="archive.${key}"><option value="">همه</option>${opts.map(([k, t]) => `<option value="${k}" ${f[key] === k ? 'selected' : ''}>${esc(t)}</option>`).join('')}</select></div>`;
  const filt = `<div class="panel"><div class="panel-b"><div class="filters">
    <div class="field"><label>مجموعه</label><div class="seg">${[['all', 'همه'], ['gone', 'ارزنده‌های خارج‌شده'], ['repriced', 'تغییر قیمت داده']].map(([k, t]) => `<button class="${f.preset === k ? 'on' : ''}" data-f="archive.preset" data-v="${k}">${t}</button>`).join('')}</div></div>
    ${sel('status', 'وضعیت', Object.entries(ST))}${sel('kind', 'نوع', Object.entries(KIND))}${sel('scope', 'محدوده', Object.entries(SCOPE))}${sel('loc', 'محله', locs)}
    <div class="field w-l"><label for="a-q">جست‌وجو</label><input id="a-q" class="inp" type="search" value="${esc(f.q)}" data-f="archive.q" placeholder="نام محله، قطعه، بلوک…"></div>
  </div></div></div>`;
  const cols = [
    { k: 'star', t: '', sort: false, f: starBtn },
    { k: 'title', t: 'قطعه', cls: 'lot', f: lotCell, v: a => a.L.short },
    { k: 'status', t: 'وضعیت', f: a => stag(a), v: a => a.status + (a.wprice ? String(1e10 - a.wprice) : '') },
    { k: 'area', t: 'متراژ', n: 1, f: a => m2(a.area) },
    { k: 'first', t: 'مراحل', n: 1, f: a => `${fa(a.first)}–${fa(a.last)}`, v: a => a.first },
    { k: 'n', t: 'دفعات', n: 1, f: a => fa(a.n) },
    { k: 'rf', t: 'پایهٔ اول', n: 1, f: a => mil(a.rf) },
    { k: 'rl', t: 'پایهٔ آخر', n: 1, f: a => mil(a.rl) },
    { k: 'rch', t: 'تغییر', n: 1, f: a => a.n > 1 ? `<span class="${clsSign(a.rch)}">${pct(a.rch, true)}</span>` : '—' },
    { k: 'wprice', t: 'برنده', n: 1, f: a => a.wprice ? `${mil(a.wprice)} <span class="xs muted">${fa(a.wstep)}</span>` : '—' },
    { k: 'wprem', t: 'اضافه‌پرداخت', n: 1, f: a => ok(a.wprem) ? pct(a.wprem, true, 1) : '—' },
    { k: 'paper_gain', t: 'سود کاغذی امروز', n: 1, f: a => ok(a.paper_gain) ? `<span class="${clsSign(a.paper_gain)}">${pct(a.paper_gain, true)}</span>` : '—', tip: 'قیمت پایهٔ امروز همان محله نسبت به قیمت پرداختی' },
    { k: 'cap', t: 'سقف پیشنهاد', n: 1, f: a => a.v ? mil(a.v.max_bid_partner) : '—', v: a => a.v && a.v.max_bid_partner },
  ];
  return `${filt}<div class="panel">${table('archive', cols, rows, { sort: f.preset === 'gone' ? { k: 'paper_gain', d: 'desc' } : { k: 'first', d: 'desc' }, pageSize: 60 })}</div>`;
};

/* ---------- watchlist ---------- */
R.watch = () => {
  const list = watched();
  if (!list.length) return `<div class="panel"><div class="panel-b"><div class="empty" style="padding:48px 16px">
    <div style="font-size:16px;font-weight:700;color:var(--ink);margin-bottom:6px">هنوز قطعه‌ای را دنبال نمی‌کنید</div>
    در جدول‌ها روی ستارهٔ کنار هر قطعه بزنید یا در پروندهٔ قطعه یادداشت بگذارید. این‌جا قیمت امروز با لحظهٔ دنبال‌کردن مقایسه می‌شود و Claude هم هنگام به‌روزرسانی تغییرات این قطعه‌ها را گزارش می‌کند.
    <div style="margin-top:14px"><a class="btn primary" href="#lots">رفتن به فرصت‌های فعال</a></div></div></div></div>`;
  const cols = [
    { k: 'star', t: '', sort: false, f: x => starBtn(x.a) },
    { k: 'title', t: 'قطعه', cls: 'lot', f: x => lotCell(x.a), v: x => x.a.L.short },
    { k: 'st', t: 'وضعیت امروز', f: x => `${stag(x.a)}${x.w.snap && x.w.snap.st !== x.a.status ? `<div class="xs muted">قبلاً: ${ST[x.w.snap.st]}</div>` : ''}`, v: x => x.a.status },
    { k: 'vc', t: 'حکم', f: x => vpill(x.a.vc), v: x => x.a.vc },
    { k: 'rl', t: 'پایهٔ امروز', n: 1, f: x => `${mil(x.a.rl)}${x.w.snap && ok(x.w.snap.rl) && x.w.snap.rl !== x.a.rl ? `<div class="xs ${clsSign(x.a.rl / x.w.snap.rl - 1)}">از ${mil(x.w.snap.rl)} (${pct(x.a.rl / x.w.snap.rl - 1, true)})</div>` : ''}`, v: x => x.a.rl },
    { k: 'cap', t: 'سقف پیشنهاد', n: 1, f: x => x.a.v ? `<b>${mil(x.a.v.max_bid_partner)}</b>` : '—', v: x => x.a.v && x.a.v.max_bid_partner },
    { k: 'mymax', t: 'سقف من', n: 1, f: x => ok(x.w.myMax) ? mil(x.w.myMax * 1e6) : '—', v: x => x.w.myMax },
    { k: 'mybid', t: 'پیشنهاد من', n: 1, f: x => ok(x.w.myBid) ? mil(x.w.myBid * 1e6) : '—', v: x => x.w.myBid },
    { k: 'out', t: 'نتیجه', f: x => esc(x.w.outcome || '—'), v: x => x.w.outcome || '' },
    { k: 'win', t: 'برنده', n: 1, f: x => x.a.wprice ? `${mil(x.a.wprice)} (${pct(x.a.wprem, true, 1)})` : '—', v: x => x.a.wprice },
    { k: 'note', t: 'یادداشت', cls: 'wrap', sort: false, f: x => `<span class="small">${esc((x.w.note || '').slice(0, 140))}</span>` },
    { k: 'at', t: 'از', f: x => esc(x.w.at || ''), v: x => x.w.at || '' },
  ];
  return `<div class="panel">${table('watch', cols, list.map(x => ({ ...x, k: x.a.k })), { sort: { k: 'cap', d: 'desc' } })}</div>
    ${S.local ? '<p class="small muted" style="margin:0">در نسخهٔ آنلاین، ستاره‌ها و یادداشت‌ها فقط در همین مرورگر ذخیره می‌شوند و به مک یا دستگاه‌های دیگر نمی‌روند.</p>' : ''}`;
};

/* ---------- method ---------- */
R.method = () => {
  const P = S.D.params, m = S.D.meta;
  return `<div class="grid g-2e">
  <div class="panel"><div class="panel-h"><h3>مدل مشارکت در ساخت</h3></div><div class="panel-b prose">
    <p>برای هر قطعه از روی کروکی و ضوابط تراکم مشهد برنامهٔ ساخت ساخته می‌شود. بعد دو مدل حساب می‌شود: ساخت با سرمایهٔ خودتان، و مشارکت ${pct(P.PARTNER_BUILDER_SHARE)} سازنده و ${pct(1 - P.PARTNER_BUILDER_SHARE)} صاحب زمین.</p>
    <h3>برنامهٔ فیزیکی</h3><ul>
      <li>زیربنای هر طبقه = متراژ × سطح اشغال ${pct(P.OCCUPANCY)} × ضریب شکل قطعه.</li>
      <li>طبقات روی پیلوت از کروکی و پهنهٔ تراکم: کم ۲ تا ۳، متوسط ۴ تا ۵ (گونهٔ ۲ در مناطق ۹ و ۱۱ پنج طبقه)، زیاد ۶ طبقه. اگر تراکم روی کروکی چاپ شده باشد، همان عدد اعمال می‌شود.</li>
      <li>قابل فروش = ${pct(P.NET_TO_GROSS)} زیربنای مسکونی. اندازهٔ واحد با سطح قیمت محله: ۱۳۰، ۱۱۵، ۱۰۰ یا ۸۵ متر.</li>
      <li>یک پارکینگ برای هر واحد: ${fa(P.PARK_GROUND_M2)} متر در پیلوت. اگر جا نشود زیرزمین با ${fa(P.PARK_BASEMENT_M2)} متر برای هر پارکینگ و هزینهٔ ${fa(P.BASEMENT_COST_FACTOR, 2)} برابر.</li></ul>
    <h3>هزینه و ارزش</h3><ul>
      <li>قیمت فروش = قیمت آگهی نوساز محله × ${fa(P.SALE_HAIRCUT, 2)} (کسر چانه و موقوفه بودن عرصه).</li>
      <li>هزینهٔ اجرا برای هر متر ناخالص: ۵۰، ۴۶، ۴۲ یا ۳۵ میلیون، بسته به سطح محله. پیلوت ${pct(P.PILOTI_COST_FACTOR)} یک طبقه.</li>
      <li>عوارض پروانه ${pct(P.PERMIT_GDV, false, 1)} ارزش پروژه، مهندسی و بیمه ${pct(P.ENGINEERING)} اجرا، پیش‌بینی‌نشده ${pct(P.CONTINGENCY)}، فروش ${pct(P.SELLING)}.</li>
      <li>مدت: ${fa(P.MONTHS)} ماه برای مجوز و ساخت، به‌علاوهٔ ۳ ماه برای پیدا کردن سازنده.</li></ul>
    <h3>تصمیم</h3><ul>
      <li><b>سهم منصفانهٔ مالک</b> سهمی است که سود سازنده را دقیقاً ${pct(P.BUILDER_TARGET)} نگه دارد. سهم واقعی مالک کمترینِ ${pct(1 - P.PARTNER_BUILDER_SHARE)} و سهم منصفانه است.</li>
      <li><b>سقف پیشنهاد</b> بالاترین قیمت هر متر زمین است که هنوز ${pct(P.OWNER_TARGET)} بازده واقعی برای مالک بماند.</li>
      <li>پرداخت ۴۰٪ نقد و دو چک ۶ و ۱۲ ماهه با هزینهٔ سرمایهٔ ${pct(P.CAPITAL_COST)} ارزش فعلی ${fa(P.PV, 3)} دارد، یعنی حدود ${pct(1 - P.PV)} تخفیف پنهان.</li>
      <li>امتیاز ۰ تا ۱۰۰: ۳۰٪ بازده مالک، ۲۰٪ سود سازنده، ۲۰٪ تخفیف نسبت به بازار زمین، ۱۵٪ سطح قیمت محله، ۱۵٪ بازده در سناریوی بدبینانه.</li>
      <li>همهٔ مبالغ به قیمت ثابت امروز است، پس بازده‌ها واقعی (بعد از تورم) هستند.</li></ul>
  </div></div>
  <div class="grid">
  <div class="panel"><div class="panel-h"><h3>داده و به‌روزرسانی</h3></div><div class="panel-b prose">
    <p>منبع: سامانهٔ مزایدهٔ <a href="https://amlak.razavi.ir/panel/auctions" target="_blank" rel="noopener">amlak.razavi.ir</a>. ${fa(m.n_stages)} مرحلهٔ هفتگی از ${esc(m.first_date)} تا ${esc(m.last_date)}، با ${fa(S.D.totals.listings)} آگهی و ${fa(S.D.assets.length)} قطعهٔ ردیابی‌شده.</p>
    <p>هر قطعه بین مراحل با محل، شمارهٔ قطعه، بلوک و متراژ دنبال می‌شود تا معلوم باشد اولین بار کِی آمده، قیمتش چطور عوض شده و در کدام مرحله فروخته شده است.</p>
    <p>موقعیت روی نقشه از «مختصات مرکز ملک» (UTM منطقهٔ ۴۰) است که روی هر کروکی چاپ شده.</p>
    <h3>به‌روزرسانی</h3>
    <p>به Claude بگویید <b>«مزایده را به‌روز کن»</b>. مراحل تازه و برنده‌های جدید دریافت می‌شوند، کروکی قطعه‌های تازه خوانده و ارزش‌گذاری می‌شوند و این صفحه خودکار پیام «داده‌های تازه آماده است» نشان می‌دهد.</p>
    <p class="small muted">آخرین به‌روزرسانی: ${esc(m.updated)} · برای اجرای داشبورد: فایل <code>start.command</code> در پوشهٔ پروژه.</p>
  </div></div>
  <div class="panel"><div class="panel-h"><h3>محدودیت‌ها</h3></div><div class="panel-b prose"><ul>
    <li>قیمت بازار از آگهی‌ها (دیوار، آریامرز، بازتاب) است، نه قیمت معامله. اطمینان هر قیمت کنار آن نوشته شده است.</li>
    <li>تراکم قطعی را پیش از پیشنهاد از شهرداری استعلام کنید. عدد طبقات از کروکی و ضوابط عمومی است.</li>
    <li>عرصهٔ این قطعه‌ها موقوفه است و خریدار مالک اعیان می‌شود. این در قیمت فروش لحاظ شده است.</li>
    <li>${fa(m.missing_stage2)} آگهی از مرحلهٔ ۲ به‌خاطر خطای سرور خود سایت دریافت نشد.</li>
    <li>نام برندگان ذخیره نمی‌شود، فقط حقیقی یا حقوقی بودن.</li></ul></div></div>
  <div class="panel"><div class="panel-h"><h3>منابع قیمت</h3></div><div class="panel-b prose"><ul>
    <li><a href="https://divar.ir/s/mashhad/buy-apartment" target="_blank" rel="noopener">دیوار</a> (آگهی‌های نوساز و زمین هر محله)</li>
    <li><a href="https://www.ariamarz.com/buy-apartment/mashhad" target="_blank" rel="noopener">آریامرز</a> و <a href="https://baztab.ir/market/housing/mashhad/" target="_blank" rel="noopener">بازتاب</a> (میانگین محله‌ها)</li>
    <li><a href="https://fararu.com/fa/news/989871" target="_blank" rel="noopener">کانون انبوه‌سازان</a> (هزینهٔ ساخت)</li>
    <li><a href="https://mashhadfoolad.com/number-of-floors-2/" target="_blank" rel="noopener">ضوابط طبقات مشهد</a> · <a href="https://shahraranews.ir/fa/news/390238" target="_blank" rel="noopener">عوارض ۱۴۰۵</a></li></ul></div></div>
  </div></div>`;
};

/* ================= lot dossier ================= */
function openLot(k, keep = false) {
  const a = assetFor(k);
  if (!a) { toast('این قطعه در داده‌ها پیدا نشد.'); return; }
  S.lotK = a.k;
  const dr = $('#drawer');
  const scroll = keep ? ($('.d-body', dr) || {}).scrollTop : 0;
  dr.innerHTML = dossier(a);
  dr.classList.add('on'); dr.setAttribute('aria-hidden', 'false');
  $('#scrim').classList.add('on');
  document.body.style.overflow = 'hidden';
  if (scroll) $('.d-body', dr).scrollTop = scroll;
  setTimeout(() => lotMap(a), 280);
}
function closeLot(fromRoute = false) {
  if (S.lotK == null) return;
  S.lotK = null;
  if (S.maps.lot) { try { S.maps.lot.remove(); } catch (e) { /* ignore */ } delete S.maps.lot; }
  $('#drawer').classList.remove('on'); $('#drawer').setAttribute('aria-hidden', 'true');
  $('#scrim').classList.remove('on');
  document.body.style.overflow = '';
  if (!fromRoute) location.hash = S.view || 'overview';
}
$('#scrim').addEventListener('click', () => closeLot());

function dossier(a) {
  const v = a.v, D = S.D, w = W(a.k) || {};
  const title = `${esc(a.L.short)} · قطعهٔ ${esc(a.qate || '—')}${a.block ? ` · بلوک ${esc(a.block)}` : ''}`;
  const head = `<div class="d-head"><div style="min-width:0"><div class="xs muted">${esc(a.L.name)}${a.L.district ? ` · منطقهٔ ${fa(a.L.district)}` : ''}</div><h2>${title}</h2>
      <div class="meta">${stag(a)} ${a.status === 'active' ? vpill(a.vc) : ''} <span class="tag">${KIND[a.kind] || a.kind}</span> <span class="tag">${esc(a.karbari || '')}</span> ${a.first === D.meta.last_step ? '<span class="pill new">تازه در این مرحله</span>' : ''}</div></div>
    <div class="acts">${starBtn(a)}${v ? `<a class="btn" href="#calc-${a.k}">${ic('calc')}ماشین‌حساب</a>` : ''}<button class="d-close" data-close aria-label="بستن">${ic('close')}</button></div></div>`;
  const img = a.img ? `<div class="sketch"><a href="${origUrl(a)}" target="_blank" rel="noopener"><img src="${a.img}" alt="کروکی قطعه" loading="lazy"></a><div class="cap"><span>کروکی مرحلهٔ ${fa(a.last)}</span><span>${S.local ? '' : `<a href="${origUrl(a)}" target="_blank" rel="noopener">کیفیت کامل</a> · `}<a href="${esc(a.kroki)}" target="_blank" rel="noopener">در سایت مزایده</a>${a.notice ? ` · <a href="${esc(a.notice)}" target="_blank" rel="noopener">اطلاعیه</a>` : ''}</span></div></div>`
    : '<div class="sketch"><div class="empty">تصویر کروکی موجود نیست.</div></div>';
  const lastH = a.hist[a.hist.length - 1] || [];
  const facts = `<dl class="facts">
    <div><dt>متراژ</dt><dd>${m2(a.area)} <small>متر</small></dd></div>
    <div><dt>${a.status === 'sold' ? 'قیمت برنده' : 'آخرین قیمت پایه'}</dt><dd>${mil(a.status === 'sold' ? a.wprice : a.rl)} <small>میلیون/متر</small></dd></div>
    <div><dt>قیمت کل</dt><dd>${bil((a.status === 'sold' ? a.wprice : a.rl) * a.area)} <small>میلیارد</small></dd></div>
    <div><dt>اولین عرضه</dt><dd>مرحلهٔ ${fa(a.first)} <small>${esc(D.stageDate[a.first] || '')}</small></dd></div>
    <div><dt>دفعات عرضه</dt><dd>${fa(a.n)} <small>بار · آخرین: مرحلهٔ ${fa(a.last)}</small></dd></div>
    <div><dt>تغییر قیمت پایه</dt><dd class="${clsSign(a.rch)}">${a.n > 1 ? pct(a.rch, true) : '—'} <small>${a.n > 1 ? `${mil(a.rf)} ← ${mil(a.rl)}` : ''}</small></dd></div>
    ${a.wprice ? `<div><dt>فروخته شد (مرحلهٔ ${fa(a.wstep)})</dt><dd>${tomanM2(a.wprice)} <small>${pct(a.wprem, true, 1)} بالای پایه · خریدار ${esc(a.buyer || '')} · کل ${bil(a.wprice * a.area)} میلیارد</small></dd></div>` : ''}
    ${v ? `<div><dt>بازار زمین محله</dt><dd>${mil(v.land_mkt)} <small>${ok(v.vs_land_mkt) ? `قیمت این قطعه ${pct(v.vs_land_mkt, true)}` : 'بدون نمونه'}</small></dd></div>` : ''}
    ${!v && a.garden_mkt ? `<div><dt>بازار باغ مشابه</dt><dd>${mil(a.garden_mkt)} <small>${pct(a.vs_garden_mkt, true)}</small></dd></div>` : ''}
    ${ok(a.paper_gain) ? `<div><dt>سطح امروز محله</dt><dd>${mil(a.loc_level_now)} <small>سود کاغذی ${pct(a.paper_gain, true)}</small></dd></div>` : ''}
  </dl>`;
  let decision = '', program = '', partner = '', scen = '', market = '';
  if (v) {
    const capGap = a.status === 'active' ? v.max_bid_partner / (a.rl * (1 + (v.exp_premium || 0))) - 1 : null;
    const vc = a.status === 'active' ? a.vc : Calc.verdict({ builderMargin: v.builder_margin, ownerRealRetEff: v.owner_real_ret_eff }, v.vs_land_mkt);
    decision = `<div class="decision ${vc}"><div><div class="cap-l">سقف پیشنهاد برای مشارکت ${pct(1 - D.params.PARTNER_BUILDER_SHARE)} مالک</div><div class="cap-v">${mil(v.max_bid_partner)} <small>میلیون/متر</small></div>
      <div class="cap-l">${a.status === 'active' ? `پایه + اضافه‌پرداخت مورد انتظار ${pct(v.exp_premium, false, 1)} = ${mil(a.rl * (1 + v.exp_premium))} · <span class="${clsSign(capGap)}">${capGap >= 0 ? `${pct(capGap)} جای رشد` : `${pct(-capGap)} بالاتر از سقف`}</span>` : esc(v.basis)}</div></div>
      <div>${vpill(vc)}<p style="margin-top:6px">${VC[vc].d}</p><p class="small" style="margin-top:6px;color:var(--ink-2)">${esc(v.plot_notes || '')}</p>
      ${!v.in_plot ? '<p class="small" style="margin-top:6px"><b>توجه:</b> طبقات از پیش‌فرض محله گرفته شده؛ کروکی این قطعه هنوز جداگانه بازبینی نشده است.</p>' : ''}</div></div>`;
    program = `<div class="panel"><div class="panel-h"><h3>چه چیزی می‌شود ساخت</h3><span class="hint">سطح اشغال ${pct(v.occupancy)} · تراکم ${pct(v.far)}</span></div><div class="panel-b"><div class="tiles">
      <div class="tile"><div class="l">طبقات روی پیلوت</div><div class="v">${fa(v.floors)}</div></div>
      <div class="tile"><div class="l">زیربنای هر طبقه</div><div class="v">${m2(v.footprint_m2)} <small>م</small></div></div>
      <div class="tile"><div class="l">زیربنای مسکونی</div><div class="v">${m2(v.gross_m2)} <small>م</small></div></div>
      <div class="tile"><div class="l">قابل فروش</div><div class="v">${m2(v.net_m2)} <small>م</small></div></div>
      <div class="tile"><div class="l">تعداد واحد</div><div class="v">${fa(v.units)} <small>× ${fa(v.unit_size)} م</small></div></div>
      <div class="tile"><div class="l">پارکینگ</div><div class="v">${v.basement_m2 ? `زیرزمین ${m2(v.basement_m2)} م` : `${fa(Math.min(v.units, v.parking_ground))} در پیلوت`}</div></div>
      <div class="tile"><div class="l">آپارتمان نوساز محله</div><div class="v">${mil(v.p_new)} <small>م/متر</small></div></div>
      <div class="tile"><div class="l">هزینهٔ ساخت هر متر فروش‌پذیر</div><div class="v">${mil(v.build_cost_per_net)} <small>م</small></div></div>
    </div></div></div>`;
    const realShare = v.owner_real_share;
    partner = `<div class="grid g-2e"><div class="panel"><div class="panel-h"><h3>مشارکت ۶۰/۴۰</h3><span class="hint">صاحب زمین فقط زمین را می‌آورد</span></div><div class="panel-b">
      <div class="split"><div class="own" style="width:40%">مالک ${m2(v.owner_m2)} م</div><div class="bld" style="width:60%">سازنده ${m2(v.builder_m2)} م</div></div>
      <dl class="kv" style="margin-top:12px">
        <dt>ارزش سهم مالک</dt><dd>${bil(v.owner_value)} میلیارد · حدود ${fa(v.owner_units, 1)} واحد</dd>
        <dt>هزینهٔ مؤثر زمین (با اقساط)</dt><dd>${bil(v.owner_cost_eff)} میلیارد</dd>
        <dt>قیمت تمام‌شدهٔ هر متر آپارتمان برای مالک</dt><dd>${mil(v.owner_cost_per_m2)} میلیون</dd>
        <dt>سود سازنده</dt><dd class="${v.builder_margin >= 0.25 ? 'up' : 'down'}">${pct(v.builder_margin)}</dd>
        <dt>سهم منصفانهٔ مالک</dt><dd>${pct(Math.max(0, v.owner_fair_share))}</dd>
        <dt class="tot">بازده واقعی مالک</dt><dd class="tot ${clsSign(v.owner_real_ret_eff)}">${pct(v.owner_real_ret_eff)} · سالانه ${pct(v.owner_real_ann_eff)}</dd>
      </dl>${realShare < 0.399 ? `<div class="callout warn" style="margin-top:10px">سازنده با ۶۰٪ به سود ۲۵٪ نمی‌رسد؛ بازده با سهم واقع‌بینانهٔ ${pct(realShare)} برای مالک حساب شده است.</div>` : ''}</div></div>
      <div class="panel"><div class="panel-h"><h3>اگر خودتان بسازید</h3></div><div class="panel-b"><dl class="kv">
        <dt>ارزش فروش کل پروژه</dt><dd>${bil(v.gdv)} میلیارد</dd>
        <dt>هزینهٔ زمین</dt><dd>${bil(v.land_cost)} میلیارد</dd>
        <dt>هزینهٔ ساخت و عوارض</dt><dd>${bil(v.build_cost)} میلیارد</dd>
        <dt class="tot">سود</dt><dd class="tot ${clsSign(v.margin)}">${pct(v.margin)}</dd>
        <dt>حداکثر قیمت زمین برای ۲۵٪ سود</dt><dd>${mil(v.rlv_ppm)} میلیون/متر</dd>
        <dt>قیمت فروش سربه‌سر</dt><dd>${mil(v.breakeven_ppm)} میلیون/متر</dd>
      </dl></div></div></div>`;
    const sc = [
      ['پایه', v.owner_real_ret_eff, v.builder_margin, v.max_bid_partner, v.margin, v.floors],
      ['بدبینانه (قیمت −۱۰٪، هزینه +۱۵٪)', v.pes_owner_real_ret_eff, v.pes_builder_margin, v.pes_max_bid_partner, v.pes_margin, v.floors],
      ['خوش‌بینانه (قیمت +۱۰٪، هزینه −۱۵٪)', v.opt_owner_real_ret_eff, v.opt_builder_margin, v.opt_max_bid_partner, v.opt_margin, v.floors],
      ['با خرید یک طبقهٔ مازاد', v.x_owner_real_ret_eff, v.x_builder_margin, v.x_max_bid_partner, v.x_margin, v.x_floors],
    ];
    scen = `<div class="panel"><div class="panel-h"><h3>سناریوها</h3></div><div class="tbl-wrap"><table class="tbl"><thead><tr><th>سناریو</th><th class="n">طبقات</th><th class="n">بازده واقعی مالک</th><th class="n">سود سازنده</th><th class="n">سقف پیشنهاد</th><th class="n">سود ساخت مستقل</th></tr></thead><tbody>
      ${sc.map(s => `<tr><td>${s[0]}</td><td class="n">${fa(s[5])}</td><td class="n ${clsSign(s[1])}">${pct(s[1])}</td><td class="n">${pct(s[2])}</td><td class="n"><b>${mil(s[3])}</b></td><td class="n ${clsSign(s[4])}">${pct(s[4])}</td></tr>`).join('')}</tbody></table></div></div>`;
    market = `<div class="callout"><b>منبع قیمت آپارتمان:</b> ${esc(v.p_src || '')} <span class="conf ${v.p_conf}">${CONF[v.p_conf] || ''}</span>${v.land_mkt_src ? `<br><b>منبع قیمت زمین:</b> ${esc(v.land_mkt_src)} <span class="conf ${v.land_mkt_conf}">${CONF[v.land_mkt_conf] || ''}</span>` : ''}</div>`;
  } else if (a.status === 'active') {
    decision = `<div class="decision"><div>${vpill('na')}</div><div><p>${VC.na.d}</p></div></div>`;
  }
  const hist = `<div class="panel"><div class="panel-h"><h3>تاریخچهٔ قیمت در ${fa(a.n)} مرحله</h3></div><div class="panel-b">${historyChart(a)}</div>
    <div class="tbl-wrap"><table class="tbl"><thead><tr><th>مرحله</th><th>تاریخ</th><th class="n">قیمت پایه (م/متر)</th><th class="n">قیمت کل (میلیارد)</th><th class="n">برنده</th><th class="n">اضافه‌پرداخت</th></tr></thead><tbody>
    ${a.hist.map(h => `<tr><td>${fa(h[0])}</td><td>${esc(D.stageDate[h[0]] || '')}</td><td class="n">${mil(h[1])}</td><td class="n">${bil(h[1] * a.area)}</td><td class="n">${h[2] ? mil(h[2]) : '—'}</td><td class="n">${ok(h[3]) ? pct(h[3], true, 1) : '—'}</td></tr>`).join('')}</tbody></table></div></div>`;
  const loc = `<div class="panel"><div class="panel-h"><h3>موقعیت</h3><span class="hint">${a.geo ? (a.geo.approx ? 'تقریبی، از قطعه‌های هم‌محله' : `مختصات کروکی: UTM ${fa(a.geo.x)} / ${fa(a.geo.y)}`) : 'مختصات در دسترس نیست'}</span>
      ${a.geo ? `<div class="tools"><a class="btn" target="_blank" rel="noopener" href="https://www.google.com/maps?q=${a.geo.lat},${a.geo.lon}">${ic('ext')}گوگل‌مپ</a><a class="btn" target="_blank" rel="noopener" href="https://neshan.org/maps/@${a.geo.lat},${a.geo.lon},17z">${ic('ext')}نشان</a></div>` : ''}</div>
      ${a.geo ? '<div id="lotmap" style="height:300px;direction:ltr;border-radius:0 0 12px 12px"></div>' : `<div class="panel-b muted">${esc(a.address || '')}</div>`}</div>`;
  const mine = `<div class="panel"><div class="panel-h"><h3>یادداشت و پیشنهاد من</h3><span class="saved" id="savedMark">ذخیره شد</span></div><div class="panel-b"><div class="note-box">
      <div class="field"><label for="n-max">سقف من (میلیون/متر)</label><input id="n-max" class="inp" type="number" step="0.5" value="${esc(w.myMax ?? '')}" data-note="myMax"></div>
      <div class="field"><label for="n-bid">پیشنهادی که دادم (میلیون/متر)</label><input id="n-bid" class="inp" type="number" step="0.5" value="${esc(w.myBid ?? '')}" data-note="myBid"></div>
      <div class="field"><label for="n-out">وضعیت من</label><select id="n-out" class="inp" data-note="outcome">${OUTCOME.map(o => `<option ${w.outcome === o ? 'selected' : ''} value="${o}">${o || '—'}</option>`).join('')}</select></div>
      <div class="field wide"><label for="n-note">یادداشت (بازدید، استعلام تراکم، تماس با سازنده…)</label><textarea id="n-note" class="inp" rows="3" data-note="note">${esc(w.note || '')}</textarea></div>
    </div></div></div>`;
  return head + `<div class="d-body"><div class="d-hero">${img}<div class="grid" style="gap:12px;align-content:start">${facts}</div></div>${decision}${program}${partner}${scen}${hist}${loc}${market}${mine}
    <p class="xs muted" style="margin:0">شناسهٔ قطعه ${fa(a.k)} · آگهی‌ها: ${a.ids.filter(x => x != null).map(x => fa(x)).join('، ')} · نشانی: ${esc(a.address || '')}</p></div>`;
}
function lotMap(a) {
  if (!a.geo || !window.L || !$('#lotmap')) return;
  if (S.maps.lot) { try { S.maps.lot.remove(); } catch (e) { /* ignore */ } }
  const map = L.map('lotmap', { zoomControl: true, scrollWheelZoom: false }).setView([a.geo.lat, a.geo.lon], a.geo.approx ? 15 : 17);
  S.maps.lot = map;
  const bl = baseLayers();
  bl.sat.addTo(map);
  L.control.layers({ [TILES.sat.t]: bl.sat, [TILES.osm.t]: bl.osm, [TILES.light.t]: bl.light, [TILES.dark.t]: bl.dark }, {}, { position: "topright" }).addTo(map);
  for (const o of S.D.assets) {
    if (!o.geo || o.k === a.k || Math.abs(o.geo.lat - a.geo.lat) > 0.02 || Math.abs(o.geo.lon - a.geo.lon) > 0.025) continue;
    L.circleMarker([o.geo.lat, o.geo.lon], { radius: 5, color: '#fff', weight: 1, fillColor: colorOf(o, 'verdict'), fillOpacity: 0.9 })
      .bindTooltip(`${esc(o.title)} · ${stagText(o)}`).on('click', () => { location.hash = 'lot-' + o.k; }).addTo(map);
  }
  L.circleMarker([a.geo.lat, a.geo.lon], { radius: 11, color: '#ffffff', weight: 3, fillColor: cssv('--brass'), fillOpacity: 1 }).bindTooltip('همین قطعه', { permanent: true, direction: 'top', offset: [0, -10] }).addTo(map);
}

/* ================= events ================= */
document.addEventListener('click', e => {
  const t = e.target;
  const star = t.closest('[data-star]');
  if (star) { e.stopPropagation(); e.preventDefault(); toggleStar(+star.dataset.star); return; }
  if (t.closest('[data-close]')) { closeLot(); return; }
  const srt = t.closest('[data-sort]');
  if (srt) {
    const id = srt.dataset.sort, k = srt.dataset.k, cur = S.sort[id] || {};
    S.sort[id] = { k, d: cur.k === k && cur.d === 'desc' ? 'asc' : 'desc' };
    store.set('sort', S.sort); S.page[id] = 0; show(S.view, S.arg, true); return;
  }
  const pg = t.closest('[data-page]');
  if (pg && !pg.disabled) { S.page[pg.dataset.page] = +pg.dataset.p; show(S.view, S.arg, true); return; }
  const tab = t.closest('[data-tab]');
  if (tab) { S.tab[tab.dataset.tab] = tab.dataset.v; show(S.view, S.arg, true); return; }
  const fbtn = t.closest('button[data-f]');
  if (fbtn) { setF(fbtn.dataset.f, fbtn.dataset.v); return; }
  const fv = t.closest('[data-fv]');
  if (fv) { const f = S.f.lots; const v = fv.dataset.fv; f.vcs = f.vcs.includes(v) ? f.vcs.filter(x => x !== v) : [...f.vcs, v]; store.set('filters', S.f); show('lots', null, true); return; }
  const mst = t.closest('[data-mapst]');
  if (mst) { const f = S.f.map, v = mst.dataset.mapst; f.st = f.st.includes(v) ? f.st.filter(x => x !== v) : [...f.st, v]; store.set('filters', S.f); show('map', null, true); return; }
  const mm = t.closest('[data-mapmode]');
  if (mm) { S.f.map.mode = mm.dataset.mapmode; store.set('filters', S.f); show('map', null, true); return; }
  const cp = t.closest('[data-cpay]');
  if (cp) { S.calc.pay = cp.dataset.cpay; show('calc', null, true); return; }
  if (t.closest('[data-calc-reset]')) { const a = S.calc.k ? assetFor(S.calc.k) : null; S.calc = { ...calcDefaults(a), floorsUntouched: true }; show('calc', null, true); return; }
  const op = t.closest('[data-open]');
  if (op && !t.closest('a[href]:not([data-open])') && !t.closest('input,select,textarea')) { location.hash = 'lot-' + op.dataset.open; }
});
function setF(path, val) {
  const [view, key] = path.split('.');
  S.f[view] = S.f[view] || {};
  S.f[view][key] = val;
  S.page[view] = 0;
  store.set('filters', S.f);
  show(view, null, true);
}
document.addEventListener('change', e => {
  const t = e.target;
  if (t.matches('select[data-f]')) setF(t.dataset.f, t.value);
  if (t.matches('input[type=checkbox][data-f]')) setF(t.dataset.f, t.checked);
  if (t.matches('#c-lot')) { const a = t.value ? assetFor(+t.value) : null; S.calc = { ...calcDefaults(a), floorsUntouched: true }; show('calc', null, true); }
  if (t.matches('[data-mapapprox]')) { S.f.map.approx = t.checked; store.set('filters', S.f); show('map', null, true); }
  if (t.matches('input[type=checkbox][data-c="xf"]')) { S.calc.xf = t.checked; $('#calcOut').innerHTML = calcOut(); }
  if (t.matches('[data-note]')) saveNote();
});
const refocus = (sel, fn) => { const el = $(sel); const pos = el && el.selectionStart; fn(); const n = $(sel); if (n) { n.focus(); try { n.setSelectionRange(pos, pos); } catch (e) { /* number inputs */ } } };
document.addEventListener('input', debounce(e => {
  const t = e.target;
  if (t.matches('input[data-f]:not([type=checkbox])')) { const id = '#' + t.id; refocus(id, () => setF(t.dataset.f, t.value)); }
  if (t.matches('input[data-c]:not([type=checkbox])')) {
    const c = S.calc, v = parseFloat(t.value); if (!isFinite(v)) return;
    const k = t.dataset.c;
    const map = { area: v, rate: v * 1e6, prem: v / 100, pNew: v * 1e6, hair: 1 - v / 100, hard: v * 1e6, floors: Math.max(1, Math.round(v)), shape: v, bs: v / 100, months: v, cc: v / 100, bt: v / 100, ot: v / 100 };
    if (k in map) c[k] = map[k];
    if (k === 'floors') c.floorsUntouched = false;
    if (k === 'pNew' && !c.hardTouched) { /* keep hard cost as entered */ }
    if (k === 'hard') c.hardTouched = true;
    $('#calcOut').innerHTML = calcOut();
  }
  if (t.matches('[data-note]')) saveNote();
}, 350));
function saveNote() {
  const k = S.lotK; if (k == null) return;
  const cur = W(k) || {};
  const num = id => { const v = parseFloat($(id).value); return isFinite(v) ? v : null; };
  const next = { ...cur, note: $('#n-note').value.trim(), myMax: num('#n-max'), myBid: num('#n-bid'), outcome: $('#n-out').value };
  if (!next.at) next.at = S.D.meta.updated;
  const empty = !next.star && !next.note && next.myMax == null && next.myBid == null && !next.outcome;
  putW(k, empty ? null : next).then(okk => { if (okk) { const m = $('#savedMark'); if (m) { m.classList.add('on'); setTimeout(() => m.classList.remove('on'), 1400); } renderNav(); } });
}

/* ---------- global search ---------- */
const qEl = $('#q'), qRes = $('#qres');
let qSel = 0, qHits = [];
qEl.addEventListener('input', () => {
  const t = norm(qEl.value).split(/\s+/).filter(Boolean);
  if (!t.length) { qRes.hidden = true; return; }
  qHits = S.D.assets.filter(a => t.every(x => a.q.includes(x))).sort((a, b) => (b.status === 'active') - (a.status === 'active') || b.last - a.last).slice(0, 14);
  qSel = 0;
  qRes.innerHTML = qHits.length ? qHits.map((a, i) => `<button type="button" class="${i === qSel ? 'on' : ''}" data-open="${a.k}"><span>${esc(a.title)}${a.block ? ` <span class="muted xs">بلوک ${esc(a.block)}</span>` : ''}</span>${stag(a)}<small>${m2(a.area)} م · ${mil(a.rl)}</small></button>`).join('') : '<div class="empty">چیزی پیدا نشد.</div>';
  qRes.hidden = false;
});
qEl.addEventListener('keydown', e => {
  if (e.key === 'Enter' && qHits[qSel]) { location.hash = 'lot-' + qHits[qSel].k; qRes.hidden = true; qEl.blur(); }
  if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { qSel = Math.max(0, Math.min(qHits.length - 1, qSel + (e.key === 'ArrowDown' ? 1 : -1))); $$('button', qRes).forEach((b, i) => b.classList.toggle('on', i === qSel)); e.preventDefault(); }
  if (e.key === 'Escape') { qRes.hidden = true; qEl.blur(); }
});
document.addEventListener('click', e => { if (!e.target.closest('#searchBox')) qRes.hidden = true; });
document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && S.lotK != null) closeLot();
  if (e.key === '/' && !e.target.closest('input,textarea,select')) { e.preventDefault(); qEl.focus(); }
});

boot().catch(err => {
  console.error(err);
  $('#view').innerHTML = `<div class="panel"><div class="panel-b"><div class="empty">داده‌ها بارگذاری نشد. داشبورد را با <code>start.command</code> اجرا کنید (نه با باز کردن مستقیم فایل).<br><span class="xs">${esc(err.message)}</span></div></div></div>`;
});
