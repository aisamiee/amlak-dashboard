const fs=require('fs'), path=require('path');
const { chromium } = require('/Users/mohammadtaghisamiee/Desktop/loan-platform/node_modules/.pnpm/playwright-core@1.62.1/node_modules/playwright-core');
const EXE='/Users/mohammadtaghisamiee/Library/Caches/ms-playwright/chromium-1234/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing';
const OUT=process.argv[2]; const jobs=JSON.parse(process.argv[3]);
(async()=>{
 const b=await chromium.launch({executablePath:EXE,headless:true}); const p=await (await b.newContext({locale:'fa-IR',timezoneId:'Asia/Tehran'})).newPage();
 await p.goto('https://amlak.razavi.ir/panel/auctions',{waitUntil:'domcontentloaded',timeout:60000});
 await p.waitForSelector("input[name='_token']",{state:'attached',timeout:60000});
 for(const [step,pg,extra] of jobs){
   const res=await p.evaluate(async({step,pg,extra})=>{const fd=new FormData(); if(step) fd.append('step',String(step)); fd.append('year','1405'); for(const [k,v] of Object.entries(extra||{})) fd.append(k,v); fd.append('_token',document.querySelector("input[name='_token']").value);
     const r=await fetch('/panel/auctions?page='+pg,{method:'POST',body:fd,headers:{'X-Requested-With':'XMLHttpRequest'}}); return {status:r.status, text:await r.text()};},{step,pg,extra});
   const n=(res.text.match(/col-md-12 mb-3 mb-3 border px-0/g)||[]).length;
   console.log(step,pg,JSON.stringify(extra||{}),'status',res.status,'cards',n,'len',res.text.length);
   fs.writeFileSync(path.join(OUT,`probe_s${step}_p${pg}.html`),res.text);
 }
 await b.close();
})();
