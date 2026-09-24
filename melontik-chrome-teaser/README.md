# Melontik Chrome Eklentisi — Instagram Story Teaser (9:16, 15 s)

Lansman için 1080×1920, 30 fps, 15 saniyelik sinematik teaser. Görüntü ve ses tamamen prosedürel olarak
üretilir (HTML5 Canvas + headless Chromium → PNG kareler → ffmpeg; ses numpy ile sentezlenir), bu yüzden
metin, tarih ve zamanlama tek bir dosyadan değiştirilip yeniden derlenebilir.

## Çıktılar

| Dosya | İçerik |
|---|---|
| `output/melontik_chrome_teaser_9x16.mp4` | Teaser (H.264 High, yuv420p, AAC 192 kb/s, 15.000 s) |
| `output/melontik_chrome_teaser_9x16_poster.png` | Kapanış karesi (logo + tarih) |
| `output/melontik_chrome_teaser_9x16_contact_sheet.png` | 2 fps kontak sayfası (hızlı gözden geçirme için) |

## Yapı (brief ile eşleşme)

| Zaman | Sahne |
|---|---|
| 0–3 s | Karanlıkta ince bir ışık çizgisi yanar (ilk karede), eğilir ve hacimli bir ışık hüzmesine açılır; 2.4 s'de hüzme bir kartın köşesine sürtünür. |
| 3–9 s | Ürünün yalnızca parçaları, hüzmenin aydınlattığı yerde: "Kâr Detayı" kart başlığı, maliyet sütununu tarayan ışık bandı, yeşil kâr rozetinin parlak zemindeki **yansıması**, "Net Kâr" satırına düşen ince ışık yarığı, 8'lik notalarda düşen maliyet plakaları, coral % işaretinin makro yayı. 8.5–9.0 s'de hüzme lense döner, beyaza yanar, 9.0'da siyaha kesilir. Kesmeler 120 BPM ızgarasında. |
| 9–13 s | Siyah 3 kare tutulur, ışık sütunu soldan girer ve metin harf harf belirir (ilk harf ~9.3 s): **YAKINDA / her şey / net.** (coral vurgu "net."). Arka plan yavaşça yaklaşır; 12.4'ten itibaren metin çözülür, coral çizgi yukarı çekilip bir noktaya toplanır. |
| 13–15 s | **Drop:** nokta Melontik diskine açılır, % işareti ışıkla çizilir (13.45'te çan sesiyle tamamlanır), "melontik" harf harf yükselir, coral çizgi ve **lansman tarihi** 13.6–14.0 arasında gelir ve ~1 s sabit durur; son kare temiz bir poster karesidir. |

Ses: sub drone + açılan pad, 120 BPM nabız (7–9 s'de 8'liklere bölünür), her kesmede cam "tink" (A minör pentatonik),
iki yükselen riser ve hızlanan tik ruloları, 8.875 ve 12.9'da nefes boşlukları, 13.0'da sub + 90–150 Hz gövde + 300–600 Hz
vuruş ile drop (telefon hoparlöründe de okunur), logo yerleşince çan parıltısı, A minör add9 → A majör çözülüş.
Master gerçek tepe -1 dBTP'ye normalize edilir (4× örnekleme). `python3 scripts/qa_check.py` süre, kare sayısı, drop hizası,
gerçek tepe, patlama, güvenli alan ve son kare sabitliğini denetler.

## Metin ve tarihi değiştirme

`src/timeline.json`:

```json
"launch_date": "GG.AA.YYYY",
"tagline": { "kicker": "YAKINDA", "line1": "her şey", "line2": "net.", "accent_line": 2 },
"caption": ""
```

* `launch_date` — kapanıştaki tarih (ör. `"15.10.2026"`).
* `tagline` — 9–13 s'deki metin. Brief'teki örnek için: `{ "kicker": "", "line1": "Her şey", "line2": "değişmek üzere.", "accent_line": 0 }`
  (`tagline_alternatives` altında hazır seçenekler var; `accent_line` coral renkli satırı seçer, 0 = yok).
* `caption` — tarihin altına isteğe bağlı küçük not (ör. `"Chrome Eklentisi"`); boşsa çizilmez.

Değişiklikten sonra `bash scripts/build.sh` çalıştırın (yaklaşık 8 dk); yalnızca bir aralığı yeniden çizmek için
`node scripts/render_frames.cjs --out build/frames --start 13 --end 15` ve ardından `bash scripts/encode.sh`.

## Derleme

Gereksinimler: Node 18+ ve `playwright` (Chromium ile), Python 3 + `numpy scipy pillow`, ffmpeg
(yoksa `pip install imageio-ffmpeg` ve `FFMPEG=<yol>` ile verin).

```bash
bash scripts/build.sh                 # ses + kareler + MP4 + kontak sayfası + poster
WORKERS=3 bash scripts/build.sh       # daha fazla paralel Chromium sayfası
node scripts/render_frames.cjs --out build/preview --times 2.5,6.5,13.3   # tek kareleri incele
python3 scripts/make_audio.py --out build/audio.wav                        # yalnızca ses
```

`PLAYWRIGHT_MODULE` ortam değişkeni, `playwright` global kurulumunun yolunu gösterebilir.
`src/index.html?preview` bir tarayıcıda (http üzerinden) açılırsa zaman kaydırıcılı canlı önizleme verir.

## Dosyalar

```
src/index.html        sayfa iskeleti: font/görsel ön yükleme, render(t)
src/scene.js          sahne: hüzme, parçacıklar, ışıklı fragmanlar, metin, kapanış kartı
src/lib.js            deterministik yardımcılar (easing, gürültü, grain, logo vektörü)
src/timeline.json     ortak zaman çizelgesi (kesmeler, vuruşlar, metin, tarih, marka renkleri)
scripts/render_frames.cjs   Playwright kare dışa aktarıcı
scripts/make_audio.py       prosedürel müzik/ses tasarımı
scripts/prepare_fragments.py lansman videosundan UI fragmanlarını kesen betik (kaynak video repoda değil)
scripts/build.sh            uçtan uca derleme
assets/fonts          Montserrat + Inter değişken fontları (OFL, wght 100–900), latin + latin-ext alt kümeleri (woff2)
assets/fragments      lansman videosundan kesilmiş ürün parçaları (PNG)
```

## Marka notları

Coral `#FD7755`, mürekkep `#25100C`, açık coral `#FEE3DC`, kâr yeşili `#5CBA39`; logo işareti kapanış kartındaki
oranlar ölçülerek vektörel olarak yeniden çizildi (halka merkezleri ±0.29R, çizgi 0.137R, ok kolu 0.242R); yazı tipi
Montserrat ExtraBold, wordmark/disk oranı (~3.3× disk çapı) markanın kendi kapanış kartıyla eşleşir. Metinler Instagram
güvenli alanında (üstten 250 px, alttan 340 px) kalır. Kodlama BT.709 sınırlı aralık olarak etiketlenir ve dönüştürülür.
