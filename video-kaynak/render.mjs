import { chromium } from '/opt/node-tools/node_modules/playwright/index.mjs';
import { spawn } from 'child_process';
const mode = process.argv[2];
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto('file://' + process.cwd() + '/video.html');
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(300);
if (mode === 'stills') {
  for (const t of process.argv.slice(3).map(Number)) {
    await page.evaluate(t => render(t), t);
    await page.screenshot({ path: `still_${t}.png` });
  }
} else {
  const fps = 30, N = 90 * fps;
  const ff = spawn('ffmpeg', ['-v','error','-y','-f','image2pipe','-framerate',String(fps),'-c:v','mjpeg','-i','-',
    '-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-r',String(fps),'silent.mp4'], { stdio: ['pipe','inherit','inherit'] });
  for (let i = 0; i < N; i++) {
    await page.evaluate(t => render(t), i / fps);
    const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 300 === 0) console.log('frame', i);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
}
await browser.close();
