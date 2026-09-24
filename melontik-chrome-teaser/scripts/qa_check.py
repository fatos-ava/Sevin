#!/usr/bin/env python3
"""
Scripted QA for the rendered teaser.
  python3 scripts/qa_check.py [output/melontik_chrome_teaser_9x16.mp4]
Checks: duration/frame count/streams, drop alignment (audio transient at the drop frame), blow-out on key frames,
safe-area (no text pixels in Instagram's top/bottom overlay bands on text frames), end-frame stability.
Exit code 1 if any check fails.
"""
import json, os, subprocess, sys, wave, tempfile
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
FF = os.environ.get('FFMPEG') or '/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2'
mp4 = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'output', 'melontik_chrome_teaser_9x16.mp4')
tl = json.load(open(os.path.join(ROOT, 'src', 'timeline.json'), encoding='utf-8'))
FPS = tl['fps']; DUR = tl['duration']
fails = []
def check(ok, msg):
    print(('PASS ' if ok else 'FAIL ') + msg)
    if not ok: fails.append(msg)

# 1. container / streams
info = subprocess.run([FF, '-hide_banner', '-i', mp4], capture_output=True, text=True).stderr
print(info.strip().split('\n')[-4:] and '\n'.join(l for l in info.split('\n') if 'Duration' in l or 'Stream' in l))
import re
m = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', info); dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
check(abs(dur - DUR) < 0.05, f'duration {dur:.3f}s (target {DUR})')
check('1080x1920' in info, 'resolution 1080x1920')
check('yuv420p' in info, 'pixel format yuv420p')
check('Audio: aac' in info, 'AAC audio present')

with tempfile.TemporaryDirectory() as tmp:
    # 2. frame count
    subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-i', mp4, '-vsync', '0', os.path.join(tmp, 'f_%04d.png')], check=True)
    frames = sorted(f for f in os.listdir(tmp) if f.startswith('f_'))
    check(len(frames) == int(DUR * FPS), f'frame count {len(frames)} (target {int(DUR*FPS)})')
    def frame(n):
        return np.array(Image.open(os.path.join(tmp, frames[n])).convert('RGB')).astype(int)
    # 3. drop alignment: audio onset near the drop
    wav = os.path.join(tmp, 'a.wav')
    subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-i', mp4, '-ac', '1', '-ar', '48000', wav], check=True)
    w = wave.open(wav); sr = w.getframerate(); a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    drop = tl['hits']['drop']; i0 = int((drop - 0.3) * sr); i1 = int((drop + 0.3) * sr)
    seg = np.abs(a[i0:i1]); onset = i0 + int(np.argmax(seg > 0.5 * seg.max()))
    t_on = onset / sr
    check(abs(t_on - drop) <= 1.5 / FPS, f'drop transient at {t_on:.3f}s (target {drop}, tolerance 1.5 frames)')
    gap_rms = 20 * np.log10(np.sqrt(np.mean(a[int(12.92 * sr):int(12.99 * sr)] ** 2)) + 1e-9)
    check(gap_rms < -30, f'pre-drop breath rms {gap_rms:.1f} dBFS (< -30)')
    # 4. blow-out: share of near-white pixels on beam frames (whiteout frame is allowed)
    for n in (90, 135, 180, 210, 240, 255):
        f = frame(n); white = np.mean((f > 250).all(axis=2))
        check(white < 0.02, f'frame {n}: near-white share {white*100:.2f}% (< 2%)')
    f = frame(268); white = np.mean((f > 235).all(axis=2)); check(white > 0.3, f'frame 268 whiteout share {white*100:.1f}% (> 30%)')
    f = frame(271); dark = np.mean(f.sum(axis=2) < 60); check(dark > 0.97, f'frame 271 (just after 9.0 snap) dark share {dark*100:.1f}% (> 97%)')
    # 5. safe area: on text frames no bright (text) pixels in the overlay bands
    for n in (330, 345, 435, 449):
        f = frame(n); lum = f.mean(axis=2)
        top = np.mean(lum[:250] > 140); bot = np.mean(lum[1580:] > 140)
        check(top < 0.001 and bot < 0.001, f'frame {n}: bright pixels in overlay bands top {top*100:.3f}% bottom {bot*100:.3f}%')
    # 6. end stability: last two frames nearly identical, and the last frame is not black
    d = np.abs(frame(449) - frame(448)).mean(); check(d < 2.0, f'end stability mean diff {d:.2f} (< 2.0)')
    check(frame(449).mean() > 8, f'last frame not black (mean {frame(449).mean():.1f})')
    # 7. text legibility proxy: tagline frame has a substantial bright-text area in the safe centre
    f = frame(345); lum = f.mean(axis=2); txt = np.mean(lum[820:1220, 150:930] > 150); check(txt > 0.03, f'tagline text coverage {txt*100:.1f}% (> 3%)')

print('\nRESULT:', 'ALL CHECKS PASSED' if not fails else f'{len(fails)} FAILED')
sys.exit(1 if fails else 0)
