#!/usr/bin/env python3
"""
Re-creates assets/fragments/*.png from the client's launch video (not committed to the repo).
Usage: python3 scripts/prepare_fragments.py /path/to/Melontik-Chrome-Eklentisi-Lansman.mp4 [--ffmpeg /path/to/ffmpeg]
The committed PNGs are the output of this script; it only needs to be re-run if the source video changes.
"""
import argparse, os, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'assets', 'fragments')

# timestamp (s) -> crop boxes (x0, y0, x1, y1) on the 1920x1080 source frame
CROPS = {
    7.0:  {'dash_card_netkar': (222, 560, 890, 862), 'dash_revenue_403k': (870, 440, 1110, 560)},
    18.0: {'webstore_listing': (196, 468, 560, 592)},
    30.5: {'kar_detayi_card_a': (655, 452, 1235, 985)},
    38.5: {'pill_row_4': (368, 796, 1560, 908)},
    44.5: {'pill_big_332': (688, 886, 1222, 1012)},
    53.5: {'pill_604_flash': (660, 852, 1172, 972), 'flash_countdown': (672, 416, 1168, 468)},
    60.5: {'cards_row_3': (246, 648, 1672, 934)},
    68.5: {'hesapla_tooltip': (1050, 630, 1350, 812)},
    79.0: {'kar_detayi_card_b': (928, 378, 1458, 948), 'netkar_row_6277': (936, 800, 1450, 852)},
    90.5: {'logo_mark_bitmap': (836, 220, 1075, 459), 'wordmark_bitmap': (570, 487, 1348, 643)},
}

def grab(ffmpeg, src, t, dst):
    subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-ss', str(t), '-i', src, '-frames:v', '1', dst], check=True)

def key_pill(src, dst):
    """cut a green profit pill (+ its coral % badge) out of its white halo -> transparent PNG"""
    im = Image.open(src).convert('RGBA'); a = np.array(im).astype(int)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    green = (g > r + 25) & (g > b + 25) & (g > 120)
    coral = (r > 200) & (g > 80) & (g < 175) & (b < 150) & (r > g + 40)
    ys, xs = np.where(green); gx0, gy0, gx1, gy1 = xs.min(), ys.min(), xs.max(), ys.max()
    mask = Image.new('L', im.size, 0); d = ImageDraw.Draw(mask)
    d.rounded_rectangle([gx0, gy0, gx1, gy1], radius=(gy1 - gy0) // 2, fill=255)
    ys, xs = np.where(coral)
    if len(xs):
        d.ellipse([xs.min() - 1, ys.min() - 1, xs.max() + 1, ys.max() + 1], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(0.8))
    out = im.copy(); out.putalpha(mask); out = out.crop(mask.getbbox()); out.save(dst)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('video'); ap.add_argument('--ffmpeg', default=os.environ.get('FFMPEG', 'ffmpeg'))
    a = ap.parse_args(); os.makedirs(OUT, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for t, crops in CROPS.items():
            frame = os.path.join(tmp, f'f_{t}.png'); grab(a.ffmpeg, a.video, t, frame)
            im = Image.open(frame).convert('RGB')
            for name, box in crops.items():
                im.crop(box).save(os.path.join(OUT, name + '.png'), optimize=True); print(name, box)
    # derived crops used by the scene
    key_pill(os.path.join(OUT, 'pill_big_332.png'), os.path.join(OUT, 'pill_big_332_cut.png'))
    key_pill(os.path.join(OUT, 'pill_604_flash.png'), os.path.join(OUT, 'pill_604_flash_cut.png'))
    Image.open(os.path.join(OUT, 'dash_card_netkar.png')).crop((0, 150, 668, 250)).save(os.path.join(OUT, 'dash_netkar_row.png'))
    c = Image.open(os.path.join(OUT, 'kar_detayi_card_b.png'))
    c.crop((0, 0, 530, 80)).save(os.path.join(OUT, 'kar_detayi_header.png'))
    c.crop((300, 95, 530, 400)).save(os.path.join(OUT, 'kar_detayi_figures.png'))
    print('done ->', OUT)

if __name__ == '__main__':
    main()
