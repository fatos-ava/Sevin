#!/usr/bin/env node
/**
 * Renders the teaser to PNG frames with headless Chromium (Playwright).
 * Usage:
 *   node scripts/render_frames.cjs --out build/frames            # all frames (0..DURATION at FPS)
 *   node scripts/render_frames.cjs --out build/preview --times 0.5,2,4.5   # specific timestamps
 *   node scripts/render_frames.cjs --out build/frames --start 0 --end 5     # a time range
 * Options: --fps 30 --workers 2 --scale 1 (0.5 for fast previews)
 */
const path = require('path');
const fs = require('fs');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || '/opt/node22/lib/node_modules/playwright');

const args = process.argv.slice(2);
const opt = (name, def) => { const i = args.indexOf('--' + name); return i >= 0 ? args[i + 1] : def; };
const OUT = path.resolve(opt('out', 'build/frames'));
const FPS = parseFloat(opt('fps', '30'));
const WORKERS = parseInt(opt('workers', '2'), 10);
const SCALE = parseFloat(opt('scale', '1'));
const timeline = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../src/timeline.json'), 'utf8'));
const DURATION = timeline.duration;
const START = parseFloat(opt('start', '0'));
const END = parseFloat(opt('end', String(DURATION)));
const TIMES = opt('times', null);

fs.mkdirSync(OUT, { recursive: true });

let jobs = [];
if (TIMES) {
  TIMES.split(',').map(Number).forEach((t, i) => jobs.push({ t, name: `p_${String(t).replace('.', '_')}.png`, idx: Math.round(t * FPS) }));
} else {
  const n0 = Math.round(START * FPS), n1 = Math.min(Math.round(END * FPS), Math.round(DURATION * FPS)) - 1;
  for (let n = n0; n <= n1; n++) jobs.push({ t: n / FPS, name: `f_${String(n).padStart(4, '0')}.png`, idx: n });
}

(async () => {
  const t0 = Date.now();
  const browser = await chromium.launch({ args: ['--no-sandbox', '--allow-file-access-from-files', '--disable-dev-shm-usage', '--force-color-profile=srgb', '--disable-lcd-text', '--font-render-hinting=none'] });
  const url = 'file://' + path.resolve(__dirname, '../src/index.html');
  const workers = Math.max(1, Math.min(WORKERS, jobs.length));
  let next = 0, done = 0;
  async function worker(id) {
    const page = await browser.newPage({ viewport: { width: Math.round(1080 * SCALE), height: Math.round(1920 * SCALE) }, deviceScaleFactor: 1 });
    page.on('pageerror', e => { console.error('PAGE ERROR', e.message); });
    page.on('console', m => { if (m.type() === 'error') console.error('CONSOLE', m.text()); });
    await page.addInitScript(tlJson => { window.TIMELINE = tlJson; }, timeline);
    await page.goto(url);
    await page.waitForFunction('window.appReady === true', { timeout: 60000 });
    if (SCALE !== 1) await page.evaluate(s => window.setScale(s), SCALE);
    while (true) {
      const j = jobs[next++]; if (!j) break;
      await page.evaluate(({ t, idx }) => window.render(t, idx), { t: j.t, idx: j.idx });
      await page.screenshot({ path: path.join(OUT, j.name), type: 'png', omitBackground: false });
      done++;
      if (done % 30 === 0 || done === jobs.length) console.log(`[${id}] ${done}/${jobs.length} frames  ${((Date.now() - t0) / 1000).toFixed(1)}s`);
    }
    await page.close();
  }
  await Promise.all(Array.from({ length: workers }, (_, i) => worker(i)));
  await browser.close();
  console.log(`done: ${jobs.length} frames -> ${OUT} in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
})().catch(e => { console.error(e); process.exit(1); });
