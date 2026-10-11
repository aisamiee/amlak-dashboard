const fs=require('fs'), path=require('path');
const { chromium } = require('/Users/mohammadtaghisamiee/Desktop/loan-platform/node_modules/.pnpm/playwright-core@1.62.1/node_modules/playwright-core');
const EXE='/Users/mohammadtaghisamiee/Library/Caches/ms-playwright/chromium-1234/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing';
const OUT=process.argv[2]; const urls=fs.readFileSync(process.argv[3],'utf8').split('\n').filter(Boolean);
(async()=>{
 const b=await chromium.launch({executablePath:EXE,headless:true}); const ctx=await b.newContext({locale:'fa-IR',timezoneId:'Asia/Tehran'}); const p=await ctx.newPage();
 await p.goto('https://amlak.razavi.ir/panel/auctions',{waitUntil:'domcontentloaded',timeout:60000});
 await p.waitForSelector("input[name='_token']",{state:'attached',timeout:60000});
 let ok=0, bad=0;
 for(const u of urls){
   const name=u.split('/').pop(); const f=path.join(OUT,name);
   if(fs.existsSync(f)){ok++; continue;}
   try{ const r=await ctx.request.get(u,{timeout:60000}); if(r.ok()){ fs.writeFileSync(f, await r.body()); ok++; } else { bad++; console.log('HTTP',r.status(),name); } }catch(e){ bad++; console.log('ERR',name,e.message.slice(0,80)); }
   await new Promise(r=>setTimeout(r,150));
 }
 console.log('ok',ok,'bad',bad); await b.close();
})();
