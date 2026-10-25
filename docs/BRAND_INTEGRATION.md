# SlipSurfaceIQ — Kurumsal Kimlik Entegrasyonu

Bu kılavuz, kullanıcı tarafından seçilen neon S sembolünü SlipSurfaceIQ-Suite
Python/PySide6 masaüstü arayüzüne bağlayan görsel kimlik sözleşmesidir.

## Marka mimarisi

- Üst marka: **SlipSurfaceIQ**
- Platform: **SlipSurfaceIQ Suite**
- Türkçe slogan: **Modelle / Analiz Et / Tasarla**
- İngilizce: **Model / Analyze / Design**
- Tanımlayıcı: **GEOTECHNICAL ENGINEERING SUITE**
- Uygulama alanları: FEM, zemin mekaniği, kaya mekaniği, şevler, kazıklar,
  tüneller, temeller, iksa ve dayanma yapıları.

## Uygulama dosyaları

| Dosya | İçerik |
| --- | --- |
| slipsurface/desktop/assets/brand/symbol.svg | Asıl neondan izlenen düzenlenebilir S vektörü |
| slipsurface/desktop/assets/brand/app_icon.svg | Pencere ve işletim sistemi uygulama ikonu |
| slipsurface/desktop/brand.py | Renk paleti ve SVG simge yöneticisi |
| slipsurface/desktop/splash.py | Yerel Qt başlangıç ekranı |
| slipsurface/desktop/home.py | Kart ekranında logo, marka adı ve slogan |
| slipsurface/desktop/widgets.py | Tüm mühendislik modüllerinde marka işareti |
| slipsurface/desktop/theme.py | Açık/koyu tema renk ve kontrast kuralları |

**Ana renkler:** Midnight #0B1529, Cyan #00DDF5, Blue #238CFF,
Iris #6B4CFF, Violet #B629F4 ve Mist #EFF5FD.

Küçük logolar SVG biçiminde tutulur. Her programın kendine özgü teknik
modül ikonu korunur ve marka işaretiyle birlikte görünür.
Açık temada sayısal girişlerin okunabilirliği için koyu yazı/açık yüzey,
koyu temada ise Midnight ve yüksek kontrastlı form öğeleri kullanılır.
Yeşil/sarı/kırmızı mühendislik doğrulama durumları korunur.

## Başlatma ve uyumluluk

Ana başlatıcı değişmedi: python main.py.
Gerekirse python main.py --no-splash ile açılış ekranı kapatılır.
SLIPSURFACE_NO_SPLASH=1 çevre değişkeni de aynı işi görür.
python main.py --app pile doğrudan kazık modülünü başlatır.
Qt offscreen/minimal modunda splash otomatik devre dışıdır.
Uygulama web sunucusu, PyInstaller, EXE veya ek dağıtım paketi üretmez.

## Doğrulama

tests/test_brand_identity.py; marka simgeleri, SVG kaynakları, splash çıktısı,
tema renkleri, ana ekran, menü ve modül başlıklarını denetler.
Sayısal hesaplama ve proje okuma/kaydetme testleri değiştirilmez.

Gerçek Qt çalışma görüntüleri scripts/capture_native_ui.py ile elde edilir:
- docs/screenshots/brand-splash.png
- docs/screenshots/native-pyside6-home-light.png
- docs/screenshots/native-pyside6-home-dark.png
- docs/screenshots/modules/<modül>-light.png ve -dark.png

Kimlik entegrasyonu sayısal modellerin formüllerini veya dosya şemalarını değiştirmez.
