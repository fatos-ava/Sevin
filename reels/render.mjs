// index.html animasyonunu kare kare yakalayıp 1080x1920 MP4'e çevirir.
// Kullanım: node reels/render.mjs [çıktı.mp4] [fps]
// FFMPEG ortam değişkeni ile ffmpeg yolu verilebilir (varsayılan: ffmpeg).
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
import { existsSync } from 'node:fs';

const dir = path.dirname(fileURLToPath(import.meta.url));
const out = process.argv[2] || path.join(dir, 'melontik-x-eadam-reels.mp4');
const fps = Number(process.argv[3] || 30);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
await page.goto(pathToFileURL(path.join(dir, 'index.html')).href + '?capture');
await page.evaluate(() => document.fonts.ready);
const dur = await page.evaluate(() => window.DUR);

// assets/music.wav varsa (python3 reels/music.py ile üretilir) sese eklenir, -14 LUFS'a normalize edilir.
const music = path.join(dir, 'assets', 'music.wav');
const audio = existsSync(music)
  ? ['-i', music, '-map', '0:v', '-map', '1:a', '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11',
     '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest']
  : [];

const ff = spawn(process.env.FFMPEG || 'ffmpeg', [
  '-y', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-', ...audio,
  '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '17', '-preset', 'slow',
  '-movflags', '+faststart', out,
], { stdio: ['pipe', 'inherit', 'inherit'] });

const frames = Math.round(dur * fps);
for (let i = 0; i < frames; i++) {
  await page.evaluate(t => window.render(t), i / fps);
  const buf = await page.screenshot({ type: 'png' });
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  if (i % fps === 0) process.stdout.write(`\r${i}/${frames}`);
}
ff.stdin.end();
await new Promise(r => ff.on('close', r));
await browser.close();
console.log(`\n${out}`);
