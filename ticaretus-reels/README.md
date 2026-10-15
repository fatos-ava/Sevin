# Melontik × ticaretus — Reels (1080×1920, 12 sn, 30 fps)

- `melontik-x-ticaretus-reels.mp4` — müzikli, yüklemeye hazır video
- `melontik-x-ticaretus-reels-kapak.png` / `.jpg` — Reels kapağı (içerik 3:4 profil kırpmasının içinde). Kaynak: `cover.html`
- `index.html` — animasyonun kaynağı (tarayıcıda açınca döngüde oynar)
- `music.py` — bu videoya özel, kodla sentezlenen telifsiz müzik → `assets/music.wav`
- `render.mjs` — MP4'ü yeniden üretir:
  `python3 ticaretus-reels/music.py && FFMPEG=/path/to/ffmpeg node ticaretus-reels/render.mjs`
