import { chromium } from '/opt/node-tools/node_modules/playwright/index.mjs';
const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:3400}});
await p.goto('file://'+process.cwd()+'/kapak.html');await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(200);
await p.locator('#w').screenshot({path:'w.png'});await p.locator('#d').screenshot({path:'d.png'});await b.close();
