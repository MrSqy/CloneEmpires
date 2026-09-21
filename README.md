# CloneEmpires

Python ve Pygame ile yazılmış, Social Empires'ten ilham alan tek oyunculu izometrik strateji prototipi. Köylülerle kaynak topla, güvenli bölgeye binalar kur, asker üret ve trollerle savaş.

Projeyi ve kodunu adım adım öğrenmek için **[Türkçe proje rehberini](tutorial.md)** oku. Kabul edilen kararlar, ilk inceleme ve doğrulama kaydı **[uygulama planında](UYGULAMA_PLANI.md)** bulunuyor.

## Kurulum ve çalıştırma

Python 3.10 veya üzeri gerekir. Güncel doğrulama Linux / Python 3.12.3 üzerinde yapıldı.

```bash
git clone https://github.com/MrSqy/CloneEmpires.git
cd CloneEmpires
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Windows'ta sanal ortamı `py -m venv .venv` ile oluşturup PowerShell'de `.venv\Scripts\Activate.ps1` ile etkinleştirebilirsin. Windows/macOS çalıştırması bu teslimde doğrulanmadı.

Hazır PNG görseller depoda bulunuyor; oyunu açmak için yeniden üretmek gerekmez. Normal kurulum yalnız Pygame yükler. Testler ve isteğe bağlı görsel üretimi için:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
```

Görselleri gerçekten yenilemek istediğinde `python tools/generate_sprites.py` çalıştır. Bu komut Pillow kullanır ve `assets/` altındaki PNG'lerin üzerine yazar.

## Oyun akışı

- **Yeni oyun:** İsteğe bağlı bir dünya adı gir. Boş bırakırsan `Dünya 1` gibi kullanılmayan bir ad seçilir. Her dünya ayrı dosyaya kaydedilir.
- **Devam et:** Dünya adı, oyuncu seviyesi ve son kayıt zamanını gösteren listeden seç. Son kaydedilen dünya üsttedir.
- **Üretim:** Oyun kapalıyken veya başka dünyadayken açık pasif üretim, başlatılmış köylü işi, ödenmiş asker siparişleri, inşaat/geliştirme ve kaynak yenilenmesi ilerler. Hareket, savaş ve sahadaki kaynak toplama durur. Yeni ücretli iş kendiliğinden başlamaz.
- **İnşaat:** Marketten bina seçip yeşil bölgedeki boş hücreye yerleştir. Geçersiz yerde ücret kesilmez. İnşaat bitince XP (deneyim puanı) bir kez verilir.
- **Baraka geliştirme:** Kuyruk korunup geliştirme boyunca durur. Önceden verilmiş L1 siparişleri L1, geliştirmeden sonraki siparişler L2 olur. Doğrudan alınan L2 baraka da L2 asker üretir.
- **Köylü çalışması:** Köylüyü seçip kaynak binasına sağ tıkla; anında içeri alınır. Mod seçip `Köylü: Başlat` ile mücevher karşılığı işi başlat. `Pasif: Başlat` ayrı bir üretim kontrolüdür; ikisi birlikte çalışabilir.

## Kontroller

| Eylem | Sonuç |
| --- | --- |
| Sol tık | Birim/bina/kaynak seç; inşaat modunda yerleştir |
| Çift sol tık | Yakındaki aynı tür oyuncu birimlerini seç |
| Sağ tık | Seçili oyuncu birimine yürü/saldır emri; köylüye kaynak toplama veya binaya girme emri |
| Orta tuş sürükleme | Kamerayı kaydır |
| Fare tekerleği | İmleç altındaki noktayı koruyarak 0,5×–3× yakınlaştır |
| Esc | Seçimi, marketi ve inşaat modunu kapat; oturum menülerinde geri dön |
| 1 / 2 / 3 / 4 | Oduncu / çiftlik / L1 mızrakçı barakası / ev inşaatını seç |
| F5 veya Kaydet | Aktif dünyayı kaydet |
| F10 veya Menü | Kaydedip ana menüye dön |
| Pencereyi kapat | Aktif dünyayı kaydedip çık |

Düşmanlar bilgi için seçilebilir; oyuncu onlara emir veremez. Ulaşılamayan yolda birim bekler. Yeni birim için hiç boş hücre yoksa ödenmiş sipariş yer açılana kadar korunur.

## Kayıtlar

Kayıtlar çalışma dizininden bağımsız olarak repo içindeki `saves/` klasöründe tutulur:

- `<dünya-kimliği>.json`: Sürümlü dünya durumu; ad, ekonomi, XP, birimler, görev/hedef bağları, binalar, sayaçlar, kuyruklar ve kamera.
- `<dünya-kimliği>.json.bak`: Bir önceki sağlam kayıt.
- Geçici dosya tamamlandıktan sonra ana dosyanın yerini alır. Kayıt 30 saniyede bir, yeni dünyada, manuel istekte ve normal çıkışta alınır.
- Kaydetme başarısızsa oturum bellekte tutulur; çıkış sırasında **Tekrar dene / Oyuna dön / Kaydetmeden çık** seçenekleri gösterilir. Ana dosya bozuk ve yedek sağlamsa listede **Yedekten aç** görünür.
- Eski, sürümsüz `autosave.json` korunur; otomatik aktarım desteklenmez. Eski kayıt listede açıklamasıyla görünür.

Çevrimdışı üretim yerel saate dayanır. Saatin geri gitmesi negatif kazanç veya aynı sürenin tekrar ödenmesini üretmez; ileri alınması geliri etkileyebilir. Zorla kapatmada son başarılı kayıttan sonraki ilerleme kaybolabilir.

## Kapsam ve doğrulama

Oyuncu Town Hall'da köylü; üç baraka türünde mızrakçı, kılıçlı ve okçu üretir. Atlı/Mage modelleri kaynakta vardır fakat üretim arayüzleri yoktur. Evler henüz nüfus kuralı uygulamaz. Depo geliştirme arayüzü, kule tamir/geliştirme arayüzü, kazanma/kaybetme ekranı, ses ve çok oyunculu oyun bu kapsamda bulunmuyor.

21 Eylül 2026 doğrulaması:

- Temiz sanal ortamda **130 test geçti** (Pygame 2.6.1, pytest 9.1.1).
- Yalnız çalışma bağımlılığıyla açılış, sahne çizimi, kayıt ve normal kapanış geçti.
- Gerçek X11 penceresinde programatik girişle iki dünya oluşturma, market, köylü atama/üretim, yakınlaştırma, kontrollü savaş, kayıt seçimi, hata ekranından dönüş ve kaydederek kapanış geçti; ekran görüntüleri incelendi.
- Pillow 12.3.0 ile 85 PNG geçici klasörde üretildi ve açılarak doğrulandı; depodaki görseller değişmedi.
- Testler geçici kayıt klasörlerini kullanır. Uzun süreli elle oynanış, denge, FPS, fiziksel disk/güç kesintisi ve Windows/macOS çalıştırması doğrulanmadı.

## Dosya haritası

| Konum | Rol |
| --- | --- |
| `main.py`, `game/app.py` | Başlatma ve ana oyun döngüsü |
| `game/session_menu.py`, `game/save_load.py` | Oturum menüleri, doğrulama ve kayıt |
| `game/simulation.py` | Açık/kapalı oyunun ortak üretim hesabı |
| `game/entities/` | Birim, köylü, bina, doğal kaynak ve mermi |
| `game/world.py`, `game/grid.py` | Harita, doluluk ve yol bulma |
| `game/renderer.py`, `game/camera.py`, `game/ui.py` | Çizim, kamera ve kullanıcı arayüzü |
| `assets/`, `tools/generate_sprites.py` | Hazır görseller ve isteğe bağlı üreticisi |
| `tests/` | Davranış ve regresyon testleri |
| `tutorial.md` | Tüm dosyalar, fonksiyonlar ve uçtan uca öğretici örnekler |

Lisans: [MIT](LICENSE).
