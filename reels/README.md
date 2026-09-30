# Melontik × e-adam — Reels (1080×1920, 12 sn, 30 fps)

- `melontik-x-eadam-reels.mp4` — müzikli, yüklemeye hazır video
- `index.html` — animasyonun kaynağı (tarayıcıda açınca döngüde oynar)
- `music.py` — özgün arka plan müziği; tamamen kodla sentezlenir, telifsizdir → `assets/music.wav`
- `melontik-x-eadam-reels-kapak.png` / `.jpg` — Reels kapağı (1080×1920; içerik 3:4 profil kırpmasının içinde). Kaynak: `cover.html`
- `render.mjs` — MP4'ü yeniden üretir (music.wav varsa sese ekler):
  `python3 reels/music.py && FFMPEG=/path/to/ffmpeg node reels/render.mjs`
