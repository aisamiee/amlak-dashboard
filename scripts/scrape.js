// Scrape auction stages of amlak.razavi.ir (year 1405) into raw HTML + JSON.
// Usage: node scrape.js <outDir> [minStep] [headed]
//   minStep: only (re)scrape stages >= minStep (default 1 = everything). Older raw pages are kept.
//   Each stage is written to a temp dir first and swapped in only when its first page succeeded,
//   so a failed run never deletes previously scraped pages.
const path = require('path');
const fs = require('fs');
const { chromium } = require('/Users/mohammadtaghisamiee/Desktop/loan-platform/node_modules/.pnpm/playwright-core@1.62.1/node_modules/playwright-core');

const OUT = process.argv[2];
const MIN_STEP = +(process.argv[3] || 1);
const HEADED = process.argv.includes('headed');
const EXE = '/Users/mohammadtaghisamiee/Library/Caches/ms-playwright/chromium-1234/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing';
const pad = n => String(n).padStart(2, '0');

(async () => {
  const browser = await chromium.launch({ executablePath: EXE, headless: !HEADED });
  const ctx = await browser.newContext({ locale: 'fa-IR', timezoneId: 'Asia/Tehran' });
  const page = await ctx.newPage();
  await page.goto('https://amlak.razavi.ir/panel/auctions', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForSelector("input[name='_token']", { state: 'attached', timeout: 60000 });
  console.log('page ready:', await page.title());

  const steps = await page.evaluate(async () => {
    const fd = new FormData(); fd.append('year', '1405'); fd.append('_token', document.querySelector("input[name='_token']").value);
    const r = await fetch('/panel/getStepsByYear', { method: 'POST', body: fd, headers: { 'X-Requested-With': 'XMLHttpRequest' } });
    return await r.json();
  });
  fs.writeFileSync(path.join(OUT, 'steps.json'), JSON.stringify(steps));
  const stepNums = Object.values(steps).map(s => +s.step).sort((a, b) => a - b);
  console.log('steps:', stepNums.join(','), '| scraping >=', MIN_STEP);

  for (const step of stepNums.filter(s => s >= MIN_STEP)) {
    const tmp = fs.mkdtempSync(path.join(OUT, `.tmp_s${pad(step)}_`));
    let pg = 1, okPages = 0;
    while (true) {
      const html = await page.evaluate(async ({ step, pg }) => {
        const fd = new FormData(); fd.append('year', '1405'); fd.append('step', String(step));
        fd.append('_token', document.querySelector("input[name='_token']").value);
        for (let t = 0; t < 3; t++) {
          try {
            const r = await fetch('/panel/auctions?page=' + pg, { method: 'POST', body: fd, headers: { 'X-Requested-With': 'XMLHttpRequest' } });
            if (r.ok) return await r.text();
          } catch (e) {}
          await new Promise(r => setTimeout(r, 1500));
        }
        return null;
      }, { step, pg });
      if (html === null) {
        // a server error on one page (stage 2 pages 6-7 do this): skip it and try the next page once
        console.log('FAIL', step, pg);
        if (pg > 1 && pg < 15) { pg++; continue; }
        break;
      }
      const n = (html.match(/col-md-12 mb-3 mb-3 border px-0/g) || []).length;
      fs.writeFileSync(path.join(tmp, `s${pad(step)}_p${pad(pg)}.html`), html);
      if (n > 0) okPages++;
      console.log(`step ${step} page ${pg} cards~${n}`);
      if (n < 12) break;          // last page
      pg++;
      await new Promise(r => setTimeout(r, 300));
    }
    if (okPages > 0) {
      for (const f of fs.readdirSync(OUT)) if (f.startsWith(`s${pad(step)}_p`)) fs.unlinkSync(path.join(OUT, f));
      for (const f of fs.readdirSync(tmp)) fs.renameSync(path.join(tmp, f), path.join(OUT, f));
    } else {
      console.log('KEEP old pages of step', step);
    }
    fs.rmSync(tmp, { recursive: true, force: true });
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
