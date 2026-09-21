# CloneEmpires — inceleme, ortak kararlar ve uygulama sonucu

## 1. Durum ve kapsam

- İnceleme tarihi: **21 Eylül 2026**.
- Klasör: `/home/baranbeey/Masaüstü/git_analiz/CloneEmpires`.
- Dal: `main`; incelenen commit: `9f6d785703df42709c9f98e4e6020aab865d28a0`.
- Uzak adres: `https://github.com/MrSqy/CloneEmpires.git`. İlk inceleme yerel commit üzerinde yapıldı. Commit/push hazırlığında git fetch origin çalıştırıldı; başlangıç HEAD ve origin/main aynı 9f6d785 commitindeydi.
- Başlangıçta yalnızca izlenmeyen `AGENTS.md` vardı; mevcut talimat korundu. Önceden `UYGULAMA_PLANI.md` yoktu.
- Kullanıcı önce Bitirme'nin bekleyene alınmasını, ardından başka başlamamış repo seçilmesini istedi. Üst klasördeki `PROJE_DURUMLARI.txt` içinde **Bitirme BEKLEYEN**, **CloneEmpires İŞLENEN** durumuna getirildi.
- **Yetkili aşama:** Kullanıcının “Bu kapsamı uygula.” talimatıyla K1–K5 ve T1–T10 uygulaması kabul edildi; yerel uygulama ve doğrulama tamamlandı. Sonuç bölüm 7’de.
- **Güncel durum:** Kod, testler, bağımlılık listeleri, README ve mevcut tutorial.md onaylanan kapsamda güncellendi. Kullanıcı sonraki mesajında gerekli commitlerin oluşturulmasını ve pushlanmasını açıkça onayladı; yayın düzeni bölüm 8’de. Bölüm 2–5 ilk incelemenin tarihsel kaydıdır; o bölümlerdeki hata sonuçları ve satır numaraları başlangıç commitine aittir, son davranışı anlatmaz.
- İnceleme, kararlar ve son doğrulama bu dosyada tutuluyor. Model/görev ayarı değiştirilmedi; yeni görev oluşturulmadı.

## 2. İlk incelemede oyun nasıl çalışıyordu? (tarihsel)

CloneEmpires, Python ile yazılmış ve Pygame ile çizilen tek oyunculu bir gerçek zamanlı strateji prototipi. Gerçek zamanlı olması, oyuncu sıradaki hamlesini düşünürken de hareketin, savaşın ve üretimin devam etmesi demek. İzometrik görünüm, kareli oyun dünyasının ekrana elmas biçiminde yansıtılmasıyla oluşuyor.

### Açılış ve temel döngü

`main.py` → `GameApp()` → alt sistemlerin kurulması → `_setup_world()` → `run()`.

- Harita 48 × 48 hücre. Merkezde Town Hall, iki mızrakçı ve iki köylü var; dış bölgelerde üç troll bulunuyor.
- Beş kaynak türünün her biri 10.000 ile başlıyor; depo üst sınırı 50.000. Bunlar kaynakta sabit değerler; dengeli bir oyun başlangıcı oldukları henüz doğrulanmadı.
- Her karede önce klavye/fare olayları işleniyor, sonra oyun durumu ilerliyor, ardından sahne ve arayüz çiziliyor. Son olarak 30 saniyelik otomatik kayıt sayacı kontrol ediliyor.
- `dt`, iki güncelleme arasında geçen saniye. Örneğin 1/60 saniyelik adım, bir saniyeyi 60 küçük parçaya bölüyor. Kod bunu hareket, üretim ve savaşta kullanıyor; bütün sistemlerin farklı adımlarda aynı sonucu verdiği varsayılamaz (B9).
- Ana çalışma akışı `GameApp._update()` içinde. Ayrı `World.update()` metodu var, fakat gerçek oyun döngüsü onu çağırmıyor; ikisinin eşdeğer olduğu varsayılmamalı.

### Kullanıcı eylemlerinin kod içindeki yolu

| Eylem | Geçtiği bileşenler ve mevcut sonuç |
| --- | --- |
| Köylüyle kaynak toplama | Sol tıkla seçim → sağ tıkta kaynak hedefi → `Worker.assign_task()` → kaynağa yaklaşma → her yaklaşık 2 saniyede en fazla 10 kaynak → `EconomyEngine.add_resources()`. Kaynak tükenince görev biter; düğüm 30 saniyede yeniden büyür. |
| Bina satın alma | Market kartı → `_enter_build_mode()` → haritada sol tık → güvenli bölge kontrolü → `ConstructionManager.place_building()` → kaynak kesilmesi ve inşaat nesnesi → `_update()` ile yaklaşık 5 saniyede tamamlanma. Yerleştirme çakışma kontrolü eksik (B5). |
| Asker üretme | Town Hall işçi üretir; katalogdaki barakalar mızrakçı, kılıçlı veya okçu üretir. Buton → `ProductionQueue.enqueue()` → peşin ödeme → en fazla 5 sipariş → süre dolunca yeni birim. |
| Kaynak binasında çalışma | Köylü binaya atanıp anında merkezine taşınır ve gizlenir. En fazla 4 köylü kabul edilir. Mod seçilince mücevher peşin ödenir; 2/5/10/30 dakika sonunda kaynak ve mücevher ödülü verilir. Pasif üretim ayrıca açılabilir. |
| Savaş | Birim emri veya otomatik hedef bulma → yol/menzil kontrolü → `BattleManager` ve `CombatEngine` ile hasar. Kuleler hedefi takip eden mermi nesnesi oluşturur; normal savaş birimlerinin hasarı doğrudan uygulanır. Düşman davranışını `AIController` yönetir. |
| Kayıt | `SaveManager.serialize()` mevcut durumun bir bölümünü JSON verisine dönüştürür → `saves/autosave.json`. Oyun açılışına veya kullanıcı arayüzüne bağlanmış yükleme akışı yok (B1–B2). |

### Dosya ve bileşen haritası

| Dosya / grup | Rolü ve ilişkileri |
| --- | --- |
| `main.py`, `game/app.py` | Başlatma, olaylar, ana döngü, kullanıcı komutları, alt sistemlerin bağlanması ve otomatik kayıt. |
| `game/world.py`, `game/grid.py` | Harita, nesne listesi, dolu hücreler ve A* yol araması. A*, engelleri dikkate alarak hedefe bir hücre dizisi arar. |
| `game/isometric.py`, `game/camera.py` | Dünya koordinatını ekrana ve ekran tıklamasını dünyaya çevirme, kamera ve yakınlaştırma. |
| `game/renderer.py`, `game/assets.py` | Sahne, görsel yükleme/ölçekleme ve göstergeler. `assets.py` eski renk/placeholder yardımcıları içeriyor; mevcut ana çizim akışına import edilmiyor. |
| `game/ui.py`, `game/selection.py` | Market, bilgi panelleri, butonlar, tekli/çoklu seçim. |
| `game/entities/base_entity.py`, `game/models.py` | Ortak konum/canlılık verisi ve birim/bina istatistik yapıları. |
| `game/entities/unit.py`, `worker.py` | Hareket/saldırı durumları; köylüye özgü toplama, inşa ve bina içi çalışma. |
| `game/entities/building.py`, `resource.py`, `projectile.py` | Bina üretimi/inşaat/kule davranışı, kaynak yenilenmesi ve mermi hareketi. |
| `game/building_catalog.py`, `construction_manager.py` | Market seçenekleri, maliyetler, bina türleri ve yerleştirme. |
| `game/economy.py`, `production_queue.py`, `work_modes.py` | Kaynak bakiyeleri/depo, asker siparişleri ve köylü üretim kuralları. |
| `game/combat.py`, `battle_manager.py`, `ai_controller.py` | Hasar hesabı, savaş yürütme ve düşman hedef seçimi. |
| `game/unit_stats.py`, `xp_system.py`, `constants.py` | Birim değerleri, deneyim/seviye ve ekran/harita/ekonomi sabitleri. |
| `game/save_load.py` | Kısmi durum dönüştürme ve JSON dosya okuma/yazma. |
| `assets/buildings`, `units`, `terrain`, `effects` | Depoda mevcut PNG görseller. Bu incelemede yeniden üretilmedi. |
| `tools/generate_sprites.py` | Pillow ile PNG üretir ve mevcut görsellerin üzerine yazabilir. Yan etkileri incelendi, çalıştırılmadı. |
| `tests/`, `pytest.ini` | 15 test modülünde toplam 85 test; ortak yardımcılar ve pytest yapılandırması. |
| `requirements.txt`, `.gitignore`, `LICENSE` | Bağımlılıklar, Git dışında tutulacak dosyalar ve lisans metni. |
| `saves/.gitkeep` | Boş kayıt klasörünü Git'te tutar. Kullanıcı kayıtları Git dışında bırakılır. |
| `README.md`, `tutorial.md`, `AGENTS.md` | Tanıtım/kurulum, mevcut öğretici rehber ve çalışma sınırları. `__init__.py` dosyaları Python paket sınırlarını tanımlar. |

Bu harita inceleme özetidir; uygulama sonunda tüm dosya/fonksiyon kapsamı için mevcut `tutorial.md` güncellenecek, aynı amaçla ikinci rehber açılmayacak.

## 3. İlk incelemede yapılan kontroller (tarihsel)

### Mevcut testler

Testler okunarak dosya yazma davranışı kontrol edildi. `SaveManager()` çalışma klasöründe `saves` oluşturduğu için testlerin çalışma klasörü geçici dizine alındı. Kaynak ve test dosyaları yerinden çalıştırıldı; bytecode ve pytest önbelleği kapatıldı. Ortamın başka pytest eklentilerini yüklememesi için otomatik eklenti yüklemesi devre dışı bırakıldı.

- Python **3.12.3**, pytest **7.4.4**, Pygame **2.6.1**.
- Sistem Python'unda Pygame yoktu; yalnızca `/tmp/cloneempires-audit-env` sanal ortamına kuruldu. Ortam mevcut sistem paketlerini görebiliyor; bu yüzden temiz kurulum doğrulaması sayılmaz.
- Ekran ve ses için SDL `dummy` sürücüleri kullanıldı: fiziksel pencere/donanım yerine görünmez test yüzeyi.
- Sonuç: **85 geçti, 0 başarısız; 2 bağımlılık kullanımdan kaldırma uyarısı; pytest süresi 0,25 saniye.** Bu bir oyun performans ölçümü değildir.

Çalıştırılan komut (çalışma klasörü `/tmp/cloneempires-audit.MeCedk`):

```bash
env PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH=/home/baranbeey/Masaüstü/git_analiz/CloneEmpires \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
  /tmp/cloneempires-audit-env/bin/python -B -m pytest \
  /home/baranbeey/Masaüstü/git_analiz/CloneEmpires/tests \
  -q -p no:cacheprovider
```

### Ayrı tekrar üretim ve çizim kontrolleri

- Geçici betik: `/tmp/cloneempires-audit.MeCedk/reproduce.py`.
- Sonuç verisi: `/tmp/cloneempires-audit.MeCedk/evidence.json`.
- Başlangıç sahnesi: `/tmp/cloneempires-audit.MeCedk/initial_scene.png`; görüntü açılıp incelendi.
- Betik, değişmemiş kaynak kodla aşağıdaki B1–B9 bulgularını tekrar üretti. B8 yakınlaştırma kontrolü ayrıca kısa Python komutuyla yapıldı.
- 120 adet 1/60 saniyelik durum güncellemesi; 0,5×, 1× ve 3× yakınlaştırmada sahne çizimi; dört market kategorisinin çizimi hatasız tamamlandı.
- Gerçek pencerede uzun süreli oynanış, fiziksel fare hissi, GPU/FPS ve oyun dengesi doğrulanmadı. Test yüzeyinin çizilmesi bunların kanıtı değildir.
- `/tmp` dosyaları geçicidir. Kalıcı kanıt özeti ve yeniden üretim adımları aşağıda tutuluyor; uygulama aşamasındaki testler geçici dosyalara bağımlı olmamalı.

## 4. İlk incelemenin bulguları ve önerileri (tarihsel)

Bu bölüm uygulama öncesindeki tekrar üretimleri korur: P1 ilerlemeyi/temel kuralları bozan, P2 etkileşim ve tutarlılığı etkileyen işler. Kabul edilen davranışlar bölüm 6’da, çözümler ve son kontroller bölüm 7’dedir.

### B1 — P1: Yeniden açılış eski otomatik kaydı üzerine yazar

- **Kanıtlanmış davranış:** `game/app.py:25–50`, `102–109`, `461–469`; yükleme çağrısı yok. `game/save_load.py:66–69` aynı dosyayı doğrudan yazma modunda açıyor.
- **Tekrar:** Geçici `autosave.json` içine odun=123 yaz → `GameApp()` oluştur → `_autosave(30)` çağır. Yeni oyunda odun=10.000; eski dosyada da odun=10.000 oluyor.
- **Etki:** Önceki oturumun kaydı, uygulama açıldıktan 30 saniye sonra yeni dünyanın kaydıyla değişiyor.
- **Çözüm yönü/fayda:** Yeni oyun ve devam et davranışını açıkça belirlemek; son sağlam kaydı koruyan dosya yazımı ve hatada kullanıcıya bildirim. Bu, ilerleme kaybını önler.
- **Kabul edilen karar (K1):** Açılışta Yeni oyun / Devam et seçimi olacak.
- **Kabul edilen karar (K2):** Her yeni oyun ayrı kayıt oluşturacak; önceki dünyalar korunacak.
- **Kabul edilen karar (K3):** Yeni oyunda isteğe bağlı dünya adı, boş bırakılırsa otomatik ad; Devam et altında ad/seviye/son kayıt zamanını gösteren ve son oynanan dünyayı üstte tutan kayıt listesi olacak. Oyuncu açacağı dünyayı seçecek.
- **Risk/açık karar:** Yedekleme ve eski kayıt biçimiyle uyumluluk davranışları henüz kesinleştirilmedi. Doğrudan dosya yazımı kesintide bozulma riski de taşıyor; gerçek disk kesintisi testi yapılmadı.
- **Kabul kontrolü:** Uygulamayı mevcut kayıtla aç; yeni oyun oluştur ve ilerlet; önceki dünyanın kaydı değişmesin. Her dünyanın ilerlemesi kendi kaydına yazılsın. Bozuk kayıt/yazma hatasında sağlam dosya ve çalışan oturum korunsun.
- **Dosyalar:** `game/app.py`, `game/save_load.py`, gerekirse `game/ui.py`, `tests/test_save_load.py`, yeni uygulama akışı testleri.

### B2 — P1: Kayıt verisi oyun durumunu eksik geri kuruyor

- **Kanıtlanmış davranış:** `game/save_load.py:17–64`. Doğrudan serialize → JSON → deserialize deneyinde:

| Önce | Geri yükledikten sonra |
| --- | --- |
| `Worker` köylü | Düz `Unit`; `assign_task` yok, kaynak toplama yeteneği kayıp. |
| `is_player=False` düşman | `is_player=True`. |
| Canı 0, devre dışı kule | Canı 300, tekrar aktif. |
| %40 tamamlanmış ev | Tamamlanmış bina. |
| Tükenmiş, yeniden büyüyecek odun düğümü | Maksimum miktarı 0; 31 saniye sonra hâlâ boş. |
| Town Hall üretim kuyruğu | Kuyruk nesnesi yok. |
| Depo seviyesi 1, sınır 50.500 | Seviye 1, sınır 50.000. |

- Köylü atamaları, görev/hedef ilişkileri, üretim sayaçları ve kuyrukları formatta yer almıyor. XP/oyuncu adı veriye yazılıyor fakat mevcut `deserialize` bunları ilgili sistemlere uygulamıyor. Dolu bir dünyaya yüklemede ekleme davranışı var; mevcut nesneleri değiştiren tam yükleme akışı bulunmuyor.
- **Etki:** Yükleme arayüzü tek başına eklense bile oturumun devamı doğru kurulamaz. Yukarıdaki deneyler API düzeyinde yapıldı; oyunda çalışan yükleme menüsü bulunduğu anlamına gelmez.
- **Çözüm yönü/fayda:** Sürümlü kayıt biçimi, doğru nesne alt türleri ve sabit kimliklerle ilişkileri geri kurma; yükleme tamamlanmadan mevcut dünyayı değiştirmeme.
- **Kabul edilen kararlar (K4–K5):** Oyun kapalıyken veya oyuncu başka dünyadayken üretim ilerleyecek; hareket, savaş ve sahadaki köylü toplaması duracak. Tamamlanma/tekrar kuralları bölüm 6'daki K5 tablosunda kesinleştirildi.
- **Risk/açık karar:** Eski kayıtlarda hiç saklanmamış bilgi geri kazanılamaz. Eski formatı koruyarak destek durumunu bildirme ve çevrimdışı hesabın ayrıntıları, bölüm 6'daki toplu öneri paketinde (T2–T3) sunuluyor.
- **Kabul kontrolü:** Köylü, düşman, yaralı kule, yarım inşaat, tükenmiş kaynak, kuyruk, ekonomi ve XP içeren oturumu kaydet/yükle; üretim için kararlaştırılacak çevrimdışı süre farkı dışında kritik durumlar eşleşsin, oyuna devam edilebilsin. Çevrimdışı süre sıfırsa üretim farkı oluşmasın; aynı zaman aralığı tekrar yüklemede ikinci kez ödüllendirilmesin.
- **Dosyalar:** `game/save_load.py`, `game/app.py`, nesne sınıfları, `production_queue.py`, `xp_system.py`, kayıt testleri.

### B3 — P1: Baraka geliştirme aktif siparişi kaybediyor

- **Kanıtlanmış davranış:** `game/app.py:244–260`, `382–388`. Bekleyen kuyruk kopyalanıyor, `current_production` ve ilerleme sıfırlanıyor.
- **Tekrar:** İki mızrakçı için ödeme yap → ilk siparişi 1 saniye ilerlet → arayüzün Geliştir geri çağrısını çalıştır → simülasyonu 20 saniye ilerlet. **İki siparişten yalnızca bir asker üretiliyor.**
- **Etki:** Aktif askerin maliyeti ve ilerlemesi kayboluyor.
- **Çözüm yönü/fayda:** Aktif siparişi ve ilerlemesini de saklamak veya geliştirmeden önce açık bir iptal/iade kuralı uygulamak; ödenmiş siparişin kaybolmasını önlemek.
- **Risk/açık karar:** Geliştirme sırasında üretim durup kaldığı yerden mi sürsün? Alternatif, kuyruk doluyken geliştirmeyi engellemek. İade ve üretilecek askerin seviyesi de belirlenmeli.
- **Kabul kontrolü:** Aktif+bekleyen sipariş, boş kuyruk, tamamlanmaya yakın sipariş ve geliştirme sırasında kaydet/yükle senaryolarında adet/maliyet/ilerleme tutarlı olsun.
- **Dosyalar:** `game/app.py`, `game/production_queue.py`, `game/entities/building.py`, üretim/geliştirme testleri.

### B4 — P1: Marketten doğrudan L2 baraka almak L1 asker üretiyor

- **Kanıtlanmış davranış:** `game/entities/building.py:15–25`, `game/models.py:26–29`, `game/production_queue.py:90–95`; bina türündeki `_2`, istatistik seviyesine aktarılmıyor.
- **Tekrar:** Oyuncu seviyesini 2 yap → gerçek yerleştirme akışından `barracks_spear_2` satın al → inşaatı bitir → asker üret. Bina istatistik seviyesi=1, asker seviyesi=1, can=150; L2 mızrakçı tablosunun beklenen canı 300.
- **Etki:** Marketin sunduğu L2 ürün ile alınan davranış uyuşmuyor. L1'i geliştirerek oluşturmak farklı sonuç verebiliyor.
- **Çözüm yönü/fayda:** Bina seviyesini katalogdan tutarlı başlatmak ve yükleme/yükseltme ile aynı modele bağlamak.
- **Risk/açık karar:** L2 bina doğrudan satılmaya devam edecek mi, yoksa yalnızca geliştirmeyle mi elde edilecek? `level_req` oyuncu gereksinimi ile bina seviyesinin tek alan gibi kullanılmaması değerlendirilmeli.
- **Kabul kontrolü:** Kullanıcının seçtiği edinme yolları aynı L2 istatistiklerini üretsin; L1 davranışı korunsun.
- **Dosyalar:** `game/building_catalog.py`, `game/entities/building.py`, `game/production_queue.py`, market/üretim testleri.

### B5 — P1: Dolu hücreye bina konabiliyor; inşaat XP'si iki kez veriliyor

- **Kanıtlanmış davranış:** `game/app.py:189–196`, `373–389`; `game/construction_manager.py:22–31`. Yerleştirmede sınır/güvenli bölge var, hücre doluluğu yok. XP yerleştirmede ve tamamlanmada ayrı ayrı veriliyor.
- **Tekrar:** Merkezdeki Town Hall hücresine arayüzün yerleştirme yoluyla ev koy. Aynı hücrede `townhall` ve `house` oluşuyor. XP, yerleştirmede **3**, tamamlanmada **6** oluyor.
- **Etki:** Üs geometrisi ve seçim bozulabilir; deneyim iki ayrı aşamada artıyor. Çift ödülün istenip istenmediği ürün kararı, mevcut iki çağrı ise doğrulandı.
- **Çözüm yönü/fayda:** Maliyeti kesmeden önce ortak yerleştirme doğrulaması; geçerli/geçersiz önizleme. XP için açık tek olay veya bilinçli iki aşamalı ödül kuralı.
- **Risk/açık karar:** Binalar mevcut modeldeki gibi tek hücre mi kaplasın, yoksa görsel boyuta uygun çok hücreli alan mı? İkinci seçenek yol bulma ve kayıt kapsamını büyütür. XP'nin tamamlanmada verilmesi öneridir.
- **Kabul kontrolü:** Bina/kaynak üstü ve sınır dışı yerleştirme reddedilsin, kaynak kesilmesin; geçerli yerde doğru maliyet ve kararlaştırılmış XP verilsin.
- **Dosyalar:** `game/construction_manager.py`, `game/app.py`, `game/world.py`, yerleştirme/XP testleri.

### B6 — P1: Yol bulunamadığında birim engelin içinden geçiyor

- **Kanıtlanmış davranış:** `game/entities/unit.py:153–163`. A* boş yol döndürünce doğrudan hedef tek adımlık yol yapılıyor. Köylü yaklaşmasında da benzer fallback var (`game/entities/worker.py:38–43`); ayrı köylü duvar senaryosu çalıştırılmadı.
- **Tekrar:** x=11 sütununun tamamını binalarla kapat → askeri (10,10)'dan (12,10)'a gönder. A* sonucu `[]`; birimin kullandığı yol `[(12,10)]`; sonunda duvarın öte tarafına geçiyor.
- **Etki:** Yapıların ve harita engellerinin hareket kuralı deliniyor.
- **Çözüm yönü/fayda:** Ulaşılamayan hedefi ayrı durum olarak ele almak; güvenli konumda durma ve kullanıcıya geri bildirim. Böylece başarısız arama geçersiz harekete dönüşmez.
- **Risk/açık karar:** Yerinde durmak mı, ulaşılabilir en yakın noktaya gitmek mi? Hareketli birimler yolu kapattığında yeniden arama sıklığı da tasarlanmalı.
- **Kabul kontrolü:** Tam duvar, kapalı halka, harita dışı hedef ve yolun sonradan kapanması; engelden geçiş olmadan belirlenmiş davranış.
- **Dosyalar:** `game/entities/unit.py`, `game/entities/worker.py`, gerekirse `game/world.py`, hareket testleri.

### B7 — P2: Seçim ile komut yetkisi ayrılmamış

- **Kanıtlanmış davranış:** `game/selection.py:38–40`, `game/app.py:199–208`, `311–345`. Seçili birimleri alırken oyuncuya ait olma koşulu bulunmuyor.
- **Tekrar:** Sol tık işleyicisiyle düşman seç → boş yere sağ tık işle. Düşman `MOVE` durumuna geçiyor ve oyuncunun verdiği hedef için yol alıyor. AI sonraki güncellemelerde emri değiştirebilir; kalıcı tam kontrol iddiası yok.
- **Çözüm yönü/fayda:** Düşmanı bilgi görmek için seçebilmek ile ona hareket/saldırı emri verebilmek ayrılmalı. Komutlar yalnızca canlı ve oyuncuya ait uygun birimlere gitmeli.
- **Risk/açık karar:** Düşman bilgileri görüntülenebilsin mi? Bu öneri düşman seçimini bütünüyle kapatmayı gerektirmiyor.
- **Kabul kontrolü:** Düşman seçimi bilgi gösterebilsin; sağ tık komutu durumunu/hedefini değiştirmesin. Oyuncu ve karma seçim testleri eklensin.
- **Dosyalar:** `game/selection.py`, `game/app.py`, seçim/komut testleri.

### B8 — P2: Görünürlük ve tıklama geometrisi tutarsız

- **Gizli köylü — tekrar üretildi:** `game/renderer.py:149–165` çizimde bina içindeki köylüyü atlıyor, seçimde atlamıyor. Köylünün binadan önce listelendiği senaryoda bina merkezine tıklama binayı değil görünmez `Worker` nesnesini seçiyor.
- **Buton kayması — tekrar üretildi:** `game/ui.py:268–270` alt çubuğu 110 piksel yükseklikte çiziyor; `330–336` tıklama için 100 piksel kullanıyor. Örnek butonun görünen üst kenarı y=620, etkin üst kenarı y=630. Görünen üst bölümdeki tıklama tüketilmiyor. Deneyde fiziksel fare yerine kontrollü fare konumu kullanıldı.
- **Yakınlaştırma — sayısal kontrol:** `game/camera.py:16–22`; merkezdeki imlecin altındaki dünya noktası tek 0,1 yakınlaştırmada `(24,24)` → `(24.275,26.275)` değişiyor. Rehberin imleç altındaki noktayı sabit tutma açıklamasıyla uyuşmuyor.
- **Çözüm yönü/fayda:** Çizim ve seçim için ortak görünürlük/geometri; butonların aynı ekran dikdörtgenini paylaşması ve olayın konumunun kullanılması; zoom öncesi/sonrası imleç altındaki dünya noktasının korunması.
- **Risk/açık karar:** Görsel tasarımı değiştirmek ayrı kapsamdır. Önce mevcut görünümdeki etkileşim hatalarını düzeltmek önerilir.
- **Kabul kontrolü:** Gizli/ölü nesneler seçilmesin; buton merkez ve kenarları uyumlu olsun; kamera konumu/zoom değişse de imleç sabitleme doğru kalsın. Sonunda gerçek pencerede fare testi gerekli.
- **Dosyalar:** `game/renderer.py`, `game/ui.py`, `game/camera.py`, seçim ve kamera/arayüz testleri.

### B9 — P2: Aynı süre, farklı pasif üretim miktarı veriyor

- **Kanıtlanmış davranış:** `game/entities/building.py:176–209`; `game/economy.py:12–14`. Tam sayıya dönüştürülen üretim teslim edilince sayaç sıfırlanıyor; yorumun söylediği kesirli kalan korunmuyor.
- **Tekrar:** Odunu 0 olan aynı seviye oduncu evinde toplam 60 saniyeyi farklı güncelleme adımlarıyla ilerlet: 1/60 saniye → **60 odun**; 1/30 saniye → **58 odun**; 1 saniye → **60 odun**; 10 saniye → **66 odun**. Bunlar kontrollü simülasyon adımlarıdır, fiziksel FPS ölçümü değildir.
- **Etki:** Üretim, geçen sürenin güncellemelere nasıl bölündüğüne göre değişiyor.
- **Çözüm yönü/fayda:** Toplam hak edilmiş üretimden daha önce teslim edileni çıkarmak veya kararlaştırılan sabit üretim aralığında kalan zamanı/miktarı taşımak.
- **Risk/açık karar:** `t^1.05` toplam oturum süresine mi, üretim döngüsüne mi uygulansın? Pasif üretim ve mücevherli köylü modları aynı anda çalışabilsin mi? Düzeltme getiriyi etkileyebileceği için denge değerleri kullanıcıyla konuşulmalı.
- **Kabul kontrolü:** Eşit toplam süre, farklı adımlarda kararlaştırılmış yuvarlama toleransı içinde aynı üretimi versin; durdur/başlat ve kaydet/yükle kalan süreyi doğru işlesin.
- **Dosyalar:** `game/entities/building.py`, `game/economy.py`, ekonomi/üretim testleri.

### B10 — P2: Test ve dokümanlar bazı gerçek davranışları güvenceye almıyor

- **Kaynakta doğrulanan boşluk:** `tests/test_save_load.py:7–23` bir mızrakçı, nesne adedi ve odun değerine bakıyor; B2 durumlarını kapsamıyor.
- `tests/test_grid_movement.py:98–115` toplama kanıtı olarak `wood > 0` kullanıyor; ekonomi zaten 10.000 odunla başlıyor. Bu koşul toplama başlamadan da doğru. `tests/test_integration.py:79–90` benzer zayıf koşul içeriyor. Toplamanın doğru çalıştığını kontrol eden başka testler mevcut; bütün test paketinin değersiz olduğu sonucu çıkarılmamalı.
- **Bağımlılık bildirimi:** README kurulumun parçası olarak görsel üreticiyi çalıştırıyor (`README.md:43–44`); üretici `PIL` import ediyor (`tools/generate_sprites.py:11`); `requirements.txt` Pillow içermiyor. Temiz sanal ortamdan tüm kurulum denenmedi; bu bulgu manifest/kaynak karşılaştırmasıdır. Depodaki hazır PNG'lerle çizim yapılabildi.
- **Doküman uyumsuzlukları:** README manuel save/load var diyor (satır 23), fakat oyunda yükleme girişi yok. Market çalışırken yol haritasında hâlâ yapılmamış (satır 116). Atlı/Mage istatistik ve görselleri mevcut, ama katalog/arayüzde üretim yolları yok. Kule geliştirme fonksiyonel parçaları var, mevcut Geliştir butonu yalnız barakaya bağlanıyor.
- `tutorial.md:594–595` güvenli/nötr bölge yarıçaplarını 20/40 diye anlatıyor; kod yarı değerleri kullanıyor. `tutorial.md:1093` doğumu boş hücreye yerleştiriyor diyor, fakat `_spawn_unit` boşluk kontrolü yapmadan rastgele ofset seçiyor. Bunlar kaynak karşılaştırması; ayrı görsel/oynanış senaryoları çalıştırılmadı.
- **Çözüm yönü/fayda:** Her kabul edilen hatayı gerçek kullanıcı senaryosunu yakalayan testle korumak; kurulum yolunu hazır görsel kullanımı/isteğe bağlı üretim olarak netleştirmek; mevcut rehberi ve README'yi son davranışa eşlemek.
- **Risk/açık karar:** Dokümanda yazan her özelliği geliştirmek mi, mevcut kapsamı doğru belgelemek mi? Atlı/Mage, kule geliştirme ve depo arayüzü ayrı özellik kararlarıdır.
- **Kabul kontrolü:** İlgili hata eski sürümde testle görünür olmalı; çözümden sonra geçmeli. Temiz ortam kurulumu ve gerçek pencere kontrolü ayrıca yapılmalı. README'den `tutorial.md` erişilebilir olmalı.
- **Dosyalar:** İlgili `tests/` dosyaları, `requirements.txt`, `README.md`, `tutorial.md`; yeni özellikler seçilirse ilgili ürün dosyaları.

## 5. İlk incelemede görüşmeye açılan ürün konuları

Bunlar ilk incelemede görüşmeye açıldı. Ekonomi değerlerinin ve anında köylü atamasının korunması T7–T8 ile, yeni içeriklerin dışarıda kalması T10 ile kararlaştırıldı. Aşağıdaki liste görüşme geçmişidir:

1. **Oyunun hedefi:** Kalıcı üs geliştirme mi, kısa süreli kazanma/kaybetme senaryosu mu? Mevcut akışta açık bir kazanma/kaybetme ekranı yok; ana bina ve evler normal savaş hedefi değil.
2. **Ekonomi:** 10.000 başlangıç kaynağı, 50.000 depo ve uzun üretim süreleri korunacak mı? Kaynakta debug etiketi bulunmadığından bunların geçici deneme değerleri olduğu varsayılmadı.
3. **Köylü deneyimi:** Binaya atamada anında içeri alınması mı, binaya yürüyüp ulaşınca üretime katılması mı? İkinci seçenek görev yaşam döngüsünü değiştirir.
4. **İçerik:** Evlerin nüfus etkisi, depo geliştirme, Atlı/Mage erişimi, kule tamiri/geliştirmesi, ses, yeni görseller veya çok oyunculu yapı ayrı kapsamlar. Birinin kabulü diğerlerini kapsamaz.
5. **Performans:** Haritanın tamamını çizme ve nesne listelerinde tekrarlı tarama var; henüz ölçülmüş performans sorunu yok. Oyuncunun hedef birim sayısı ve donanımı belirlenmeden performans kazancı iddia edilmemeli.

## 6. Birlikte kararlaştırılan uygulama kapsamı

Kullanıcı kalan tavsiyeleri tek paket hâlinde istedi ve daha sonra “Bu kapsamı uygula.” diyerek T1–T10’u kabul etti. Aşağıdaki ilk sıralama görüşme gerekçesini korur; kesin ürün kararları K1–K5 ve T1–T10 başlıklarındadır.

| Sıra | Konuşulacak karar | Önerilen başlangıç yaklaşımı ve önemli maliyet |
| --- | --- | --- |
| 1 | Kayıt/oturum yaşamı, açılış ve eski kayıtlar | Yeni oyun / Devam et (K1), her yeni oyun için ayrı kayıt (K2), adlandırma ve kayıt seçme akışı (K3), çevrimdışı üretim ve kapsamı (K4–K5) kabul edildi. Kalan kayıt/zaman ayrıntıları T1–T3 paketinde öneriliyor. |
| 2 | Sipariş ve bina seviyesi | Geliştirmede aktif üretimi ilerlemesiyle durdur/sürdür; doğrudan L2 ile yükseltilmiş L2 eşdeğerliği. Üretilecek askerin hangi seviyeyi alacağı kararlaştırılmalı. |
| 3 | Yerleştirme, hareket ve komut kuralları | Önce mevcut tek hücre modelinde çakışma kontrolü, ulaşılamaz hedefte durma, komutları oyuncu birimleriyle sınırlama. Çok hücreli binalar daha geniş tasarım işi. |
| 4 | Seçim/buton/kamera ve ekonomi tutarlılığı | Mevcut görünümü koruyarak etkileşim geometrisini düzeltme; üretim formülünü seçilen anlamıyla zaman adımından bağımsızlaştırma. Denge değişiklikleri ayrı konuşulmalı. |
| 5 | Yeni özellikler ve oyun hedefi | Önceki kararlar sonrasında yalnız seçilen özellikler. Yeni görsel veya çok oyunculu geliştirme otomatik kapsam değil. |

### Kabul edilmiş istekler

- Bitirme bekleyecek; aktif inceleme CloneEmpires üzerinde.
- İnceleme sonuçları, önerilerin fayda/riskleri ve kararlar kullanıcıyla ayrıntılı konuşulacak.
- Uygulamaya birlikte karar verildikten sonra geçilecek.
- İnceleme ve karar kaydı bu dosyada tutulacak.
- Kullanıcının son çalışma tercihi: Kalan tavsiyeleri tek seferde, birlikte değerlendirilebilecek bir paket halinde sun; her küçük karar için ayrı soru turu açma. Yeni önemli bulgu veya kapsam değişikliği doğarsa yine açıkça bildir.

### Kabul edilmiş ürün kararları

- **K1 — Açılış seçimi (21 Eylül 2026):** Kullanıcı, “Yeni oyun / Devam et olsun” dedi. Oyun açılışında bu iki seçenek sunulacak; son kayıt kendiliğinden başlatılmayacak.
- **K2 — Ayrı oyun kayıtları (21 Eylül 2026):** Kullanıcı, “Ayrı kayıt oluşturmak mantıklı” dedi. Her Yeni oyun ayrı bir dünya kaydı oluşturacak. Önceki dünyalar korunacak; bir dünyadaki ilerleme başka dünyanın kaydının üzerine yazılmayacak.
- **K3 — Dünya adı ve kayıt seçme akışı (21 Eylül 2026):** Kullanıcı önerilen akışa “Uygun. Devam edebilirsin.” yanıtını verdi. Yeni oyun oluştururken dünya adı isteğe bağlı olacak; boş bırakılırsa “Dünya 1” gibi otomatik ad verilecek. Devam et kayıt listesini açacak; dünya adı, oyuncu seviyesi ve son kayıt zamanı gösterilecek. Son oynanan dünya üstte yer alacak; oyuncu istediği dünyayı seçip açacak. Oynarken ilerleme yalnız açık olan dünyanın kaydına yazılacak.
- **K4 — Çevrimdışı üretim (21 Eylül 2026):** Kullanıcı, “Üretim devam etsin.” dedi. Sunulan üretimin ilerleyip hareket ve savaşın durduğu seçenek kabul edildi. Oyun kapalıyken veya oyuncu başka dünyadayken üretim süreleri ilerleyecek. Ayrıntılar daha sonra K5 ile kabul edildi.
- **K5 — Çevrimdışı çalışma kuralları (21 Eylül 2026):** Kullanıcı sunulan kuralların tamamına “Uygun” dedi. Aşağıdaki tablo kabul edilmiştir. Dünya açılırken geçen süre hesaplanarak uygulanacak; oyunun arka planda açık kalması gerekmeyecek.
- Kullanıcının sonraki “Bu kapsamı uygula.” talimatıyla K1–K5 ve T1–T10 birlikte uygulama kapsamı oldu.

**K5 kapsamında kabul edilen çevrimdışı davranışlar:**

| Sistem | Kabul edilen davranış |
| --- | --- |
| Pasif kaynak üretimi | Önceden açılmış üretim geçen süre için kaynak kazandıracak; depo kapasitesi aşılmayacak. |
| Süreli köylü üretimi | Başlatılmış çalışma modu tamamlanıp ödülünü bir kez verecek; kendiliğinden yeni mod başlatıp mücevher harcamayacak. |
| Asker/işçi üretim kuyruğu | Ücreti önceden ödenmiş siparişler sırayla ilerleyecek; süre yeterliyse kuyruk bitecek, yeni sipariş eklenmeyecek. |
| İnşaat, geliştirme ve doğal kaynak yenilenmesi | Bu sayaçlar ilerleyecek. Geliştirme ile üretim arasındaki sıralama T4'te ayrıca öneriliyor. |
| Sahadaki köylünün doğrudan kaynak toplaması | Hareket ve savaş gibi duracak. |

### Kabul edilen toplu kapsam — T1–T10

**Paket durumu: UYGULANDI.** Kullanıcı K1–K5 ve aşağıdaki T1–T10 paketini açıkça kabul etti. Maddelerin öneri dili karar görüşmesinden korunmuştur; bu teslimde yeni onay bekleyen madde yoktur. Kontroller ve sınırlar bölüm 7’de belirtilmiştir.

#### T1 — Kayıt zamanları ve sağlam son kaydı koruma (B1)

- Her dünya açılış/ilerleme verisini ayrı kayıt kimliğiyle tutsun; görünen dünya adı dosya kimliğinin yerine kullanılmasın.
- Mevcut 30 saniyelik otomatik kayıt korunsun. Ayrıca yeni dünya ilk oluşturulduğunda, menüye dönerken ve normal pencere kapatmada kayıt alınsın. Basit bir manuel Kaydet eylemi eklensin.
- Yeni dosya önce geçici dosyaya eksiksiz yazılsın; tamamlanınca asıl kaydın yerine geçirilsin. Dünya başına bir önceki sağlam sürüm yedek olarak korunsun. Yeni kayıt başarısızsa asıl kayıt/yedek bozulmasın.
- Kayıt hatası kullanıcıya açıkça gösterilsin. Kaydedip çıkma başarısız olursa oturum otomatik terk edilmesin; tekrar deneme veya kaydetmeden çıkma seçimi sunulsun. Ana kayıt bozuksa sağlam yedeğe dönme seçeneği gösterilsin.
- **Fayda/sonuç:** Oturumlar ve son sağlam durum korunur. Zorla kapatma/güç kesintisinde son başarılı kayıttan sonraki ilerleme yine kaybolabilir; sıfır veri kaybı vaadi yok.
- **Kabul:** Otomatik/manüel/çıkış kayıtları, başarısız yazım ve bozuk ana kayıt senaryoları; dünya A kaydedilirken B değişmesin.

#### T2 — Tam durum kaydı ve eski biçimin ele alınması (B2)

- Birim alt türü/tarafı/canı, görevler ve hedefleri, bina durumu, köylü atamaları, aktif+bekleyen siparişler ve ilerlemeleri, üretim süreleri, kaynak yenilenmesi, ekonomi/XP ve kamera korunacak şekilde kayıt biçimi tamamlanıp sürümlensin. Nesneler arasındaki bağlar sabit kimliklerle geri kurulsun.
- Yüklenen veri doğrulanıp geçici dünyada eksiksiz kurulmadan mevcut oturum değiştirilmesin. Bilinmeyen/bozuk biçim sessizce kısmen yüklenmesin.
- Eski `autosave.json` aslı korunarak tanınsın; mevcut eksik biçim bu ilk kapsamda otomatik dönüştürülmesin. Kullanıcıya eski sürüm kaydı olduğu ve doğrudan açılamadığı açıkça bildirilsin. Eksik geçmişi tahmin ederek geçerliymiş gibi açmak yerine eski kayıt aktarımı ayrı özellik olarak bırakılması öneriliyor.
- **Fayda/sonuç:** Kayıttan devam etmek oyun durumunu bozmaz. Bedeli: eski biçimli kayıtlar için otomatik devam desteği bu pakette olmayacak; kayıt dosyası silinmeyecek.
- **Kabul:** Tam durumun kayıt/yükleme karşılaştırması, eksik/geçersiz alanlar ve eski biçimin zarar görmeden reddedilmesi.

#### T3 — Çevrimdışı süreyi bir kez uygulama (K4–K5, B2/B9)

- Her dünya en son işlenmiş zamanını tutsun. Dünya açılırken yalnız o zamandan sonraki süre hesaplansın; sonuç ve yeni zaman birlikte kaydedilsin. Aynı süre tekrar açılışta yeniden kazanç üretmesin.
- Geçen süre kare kare simüle edilmesin; biten inşaat, geliştirme ve sipariş olayları zaman sırasıyla işlensin. Kaynak formülü T8 ile çevrimiçi/çevrimdışı ortak olsun.
- Depo kapasitesine ek keyfî çevrimdışı saat limiti konmasın. Doluyken kaybedilen taşma, kapasite açıldığında geçmişten geri verilmesin.
- Saat geriye alınırsa negatif süre/kazanç oluşmasın ve işlenmiş zaman geriye taşınmasın. Tek oyunculu yerel saat esas alınsın; çevrimiçi saat sunucusu veya hile önleme sistemi eklenmesin. Saatin ileri alınması üretimi etkileyebilir; bu yaklaşımın bilinen sınırıdır.
- **Fayda/sonuç:** Uzun süre kapalı kalan dünya hızlı ve tutarlı açılır. Aynı ödülün tekrar verilmesi önlenir; yerel saat güvenilirliği sınırlaması kalır.
- **Kabul:** Sıfır/kısa/uzun süre, tekrar yükleme, saat geri gitmesi, dolu depo ve birden fazla dünya; sipariş/XP/ödül yalnız bir kez işlensin.

#### T4 — Baraka geliştirme, sipariş koruma ve L2 (B3–B4)

- Geliştirme sırasında aktif ve bekleyen siparişler duraklatılsın; geliştirme bitince aktif sipariş kalan süresinden, diğerleri sırayla devam etsin. Ödenen kaynak, sipariş veya ilerleme kaybolmasın.
- Siparişin asker seviyesi sipariş verildiği anda belirlensin. L1'de verilmiş sipariş L1 kalsın; geliştirmeden sonra verilen yeni sipariş L2 üretsin. Böylece eski siparişin niteliği sonradan değişmesin.
- L2 barakalar marketten doğrudan alınabilsin; doğrudan alınan ve yükseltilen L2 aynı bina/asker istatistiklerini kullansın. Oyuncunun seviye gereksinimi ile binanın kendi seviyesi ayrı veriler olsun.
- Çevrimdışı hesapta önce geliştirme için geçen süre, sonra üretime kalan süre uygulansın. İptal edilen sipariş için mevcut iade davranışı korunup aynı maliyet iki kez iade edilmesin.
- **Fayda/sonuç:** Sipariş kaybı ve L2 tutarsızlığı çözülür. Önemli oyun tercihi: yükseltme öncesindeki siparişler otomatik L2'ye dönüşmez.
- **Kabul:** Aktif+bekleyen kuyrukla geliştirme, kayıt/yükleme ve çevrimdışı tamamlanma; L1 sipariş ve yeni L2 sipariş istatistikleri.

#### T5 — Yerleştirme ve deneyim puanı (B5)

- Mevcut tek hücreli bina modeli kullanılsın. Harita sınırı, güvenli bölge, hücre doluluğu, bina türü/seviye gereksinimi ve maliyet ortak yerleştirme kontrolünden geçsin; başarısızsa ücret kesilmesin.
- Önizleme uygun yerde yeşil, uygun olmayan yerde kırmızı olsun; reddin nedeni kısa metinle gösterilsin. Yeni bir çok hücreli bina sistemi bu pakete eklenmesin.
- İnşaat/geliştirme XP'si yalnız tamamlanma olayında bir kez verilsin. Kaynak binasının çalışma ödülü ayrı olay olarak korunsun; kaynak üretim sürecinin bina yapımıyla karıştırılması önlensin.
- **Fayda/sonuç:** Binalar aynı yere yığılmaz, maliyet/ödül tek işlemle tutarlı yürür. Mevcut çift inşaat XP'si kalkacağı için seviye atlama hızı azalabilir.
- **Kabul:** Dolu/sınır dışı/yetersiz kaynaklı yerleştirme ve tamamlanma anında tek XP; çevrimdışı yükleme aynı ödülü yinelemesin.

#### T6 — Hareket, doğum ve oyuncu komutları (B6–B7)

- Ulaşılamayan hedefte birim güvenli konumda dursun ve kısa geri bildirim verilsin. Engel içinden doğrudan hedefe giden yedek yol kaldırılıp asker/köylü yaklaşmalarına aynı kural uygulansın.
- Yol hareketli bir nesneyle kapanırsa güvenli hücreden sınırlı sıklıkta tekrar yol aransın; yol bulunamazsa geçersiz hareket yapılmasın.
- Yeni üretilen birim geçerli boş hücrede doğsun. Yer yoksa tamamlanan sipariş yer açılana kadar korunsun; ödeme veya birim kaybolmasın, doğum/XP iki kez gerçekleşmesin.
- Düşman bilgi almak için seçilebilsin; hareket/saldırı komutları yalnız canlı, oyuncuya ait ve kullanılabilir birimlere gitsin.
- **Fayda/sonuç:** Engel ve taraf kuralları korunur. Bazı emirler artık hareket yerine durma/yer bekleme ile sonuçlanır; arayüz bunu açıklamalı.
- **Kabul:** Duvar, kapalı alan, sonradan engellenen yol, dolu doğum alanı, düşman ve karma seçim testleri.

#### T7 — Mevcut arayüzde etkileşim düzeltmeleri (B8)

- Gizli/ölü nesneler harita seçiminden çıkarılsın. Bina içindeki köylü, binanın tıklamasını yakalamasın.
- Buton çizimi ve olay işleme aynı ekran dikdörtgenini kullansın; olayın kendi konumu esas alınsın. Yakınlaştırmada imlecin altındaki dünya noktası korunsun.
- Köylünün binaya atandığında anında içeri alınması mevcut davranış olarak korunsun; binaya yürüme/varış animasyonu ayrı özellik olarak bırakılsın.
- **Fayda/sonuç:** Mevcut görünüm üzerinde tıklama ve kamera davranışı düzelir. Görsel tasarımın yenilenmesi bu pakete dahil değil.
- **Kabul:** Gizli köylü, buton kenarları, farklı zoom/kamera konumları ve gerçek pencerede fare kontrolü.

#### T8 — Üretim formülü ve oyun dengesi sınırı (B9)

- Mevcut `t^1.05` formülü korunsun, bir pasif üretim oturumunun toplam süresine uygulansın. Her adımda toplam hak edilmiş miktardan daha önce işlenmiş miktar çıkarılsın; kesirli kalan kaybolmasın.
- Kaydet/yükle veya çevrimdışı kalma bu süreyi sıfırlamasın. Açık bir Durdur işlemi oturumu bitirsin; sonraki Başlat yeni oturum başlatsın. Depo doluyken işlenmiş fakat sığmamış üretim sonradan yeniden verilmesin.
- Pasif üretim ve ücretli köylü çalışma modu birlikte kullanılabilsin; ayrı sayaçları olsun. İki üretim türünün durdurma/başlatma kontrolleri hangi sistemi etkilediğini açıkça göstersin.
- Başlangıç kaynakları, maliyetler, çalışma modu ödülleri ve temel savaş istatistikleri bu pakette korunup hata düzeltmelerinden sonra oynanışla ayrıca değerlendirilsin.
- **Fayda/sonuç:** Aynı süre, aynı işlem sırasıyla açık/kapalı oyunda aynı kazancı verir. Formül doğru birikince bugünkü hatalı getiriden farklı, özellikle uzun oturumlarda daha yüksek kazanç oluşabilir; bu ayrı bir gizli denge değişikliği olarak bırakılmamalı.
- **Kabul:** 30/60 güncelleme, tek büyük süre ve çevrimdışı hesapta eşit üretim; durdur/başlat, dolu depo, kesirli kalan ve kayıt/yükleme.

#### T9 — Kurulum, davranış testleri ve mevcut rehber (B10)

- Hazır PNG'ler ile doğrudan çalıştırma ana kurulum yolu olsun. Görsel üretimi isteğe bağlı açıklansın; kullanılan Pillow bağımlılığı geliştirme/üretim gereksinimleri içinde açıkça bildirilsin. Gerekçe olmadan bağımlılık sürümleri yükseltilmesin.
- B1–B10 için gerçek davranışı yakalayan testler eklensin; başlangıçta zaten pozitif olan kaynak miktarını toplama kanıtı sayan kontroller düzeltilsin. Mevcut 85 test, tam durum kayıt/yükleme, çevrimdışı üretim ve arayüz kontrolleri birlikte çalıştırılsın.
- `tutorial.md` son kaynakla eşleştirilip AGENTS.md'nin kapsamlı öğretici rehber gereğini karşılasın; README'den bağlantı verilsin. Var olan/erişilemeyen/planlanan özellikler doğru ayrılsın.
- **Fayda/sonuç:** Kurulum tekrarlanabilir ve hata düzeltmeleri korunabilir olur. Test ortamı başarısı ile gerçek oynanış kanıtı ayrı raporlanır.
- **Kabul:** Temiz kurulum, testler, kaynak-doküman karşılaştırması ve gerçek pencere kontrolleri; yapılamayan doğrulamalar açıkça yazılır.

#### T10 — Bu ilk uygulamanın ürün kapsamı

- Mevcut tek oyunculu üs geliştirme prototipi üzerinde K1–K5 ve T1–T9 uygulanması öneriliyor. Bu, nihai oyun türüne ilişkin kalıcı karar değil; ilk uygulamanın sınırı.
- Atlı/Mage üretim yolları, ev/nüfus etkisi, depo arayüzü, kule tamir/geliştirme arayüzü, kazanma/kaybetme senaryoları, yeni görseller, ses ve çok oyunculu özellikler bu paketin ardından değerlendirilsin. Kaynaktaki erişilemeyen özellikler belgede mevcutmuş gibi sunulmasın.
- Ölçülmemiş performans iddialarıyla kapsam büyütülmesin. Çevrimdışı hesabın uzun süreyi kare kare işletmemesi bu özelliğin gereği olarak ele alınsın; diğer optimizasyonlar ölçümle gerekçelendirilsin.
- **Fayda/sonuç:** İlk uygulamanın kapsamı incelenmiş sorunlara ve kabul edilmiş kayıt/üretim davranışına bağlı kalır. Yeni içerik ve oyun hedefi tasarımı sonraki aşamada kalır.

**Uygulama kararı:** K1–K5 ve T1–T10 bütünü uygulandı. İlk uygulama talimatından sonra kullanıcı ayrıca commit/push yetkisi verdi. Önceki bulgular tarihsel kanıt olarak korunuyor; son doğrulama aşağıda.

### Uygulama başladığında önerilen commit ayrımı

Commit/push ancak ayrıca kullanıcının talimatı kapsarsa yapılır. Olası gruplar: (1) kayıt biçimi ve durumun geri kurulması, (2) açılış/kayıt dosyası yaşam döngüsü, (3) kuyruk/geliştirme ve L2 tutarlılığı, (4) yerleştirme/XP, (5) hareket/komut sınırları, (6) arayüz/kamera, (7) üretim zaman hesabı. Her davranış değişikliğinin regresyon testi aynı anlamlı grupla birlikte olmalı; rehber ilgili adımlarda güncellenmeli. Gruplar yalnız seçilen maddelere göre kesinleştirilecek.

### Doğrulama ve rehber teslim koşulları

- Önce seçilen hataların tekrar üretimleri kalıcı testlere dönüştürülmeli; yalnız hatayı örten beklenti değişiklikleri yapılmamalı.
- İlgili testler ve mevcut 85 test çalıştırılmalı; kayıtlar testte geçici dizine yönlendirilmeli.
- Kayıt/geliştirme/üretim birleşik senaryoları ve gerçek pencere üzerinden seçim, market, kamera, savaş, kapanış ve devam et kontrolleri yapılmalı. Yapılmayan kontroller açıkça belirtilmeli.
- Mevcut `tutorial.md`, ilk kullanımda kavram açıklamaları ve uçtan uca örneklerle güncellenmeli; dosya/fonksiyon/sınıf/blok kapsamı, hata yolları, bağımlılıklar, üretilen görseller ve testler gerçek kaynakla karşılaştırılmalı. README bağlantısı eklenmeli.
- İlk inceleme ürün dosyalarını değiştirmedi; daha sonra verilen açık uygulama talimatı ile bu koşullar tamamlandı. Elle uzun oynanış ve platform sınırları ayrıca raporlandı.


## 7. Uygulama sonucu ve son doğrulama — 21 Eylül 2026

K1–K5 / T1–T10 kapsamı yerel kaynakta uygulandı. İlk uygulama teslimi commit/push içermiyordu; kullanıcının sonraki açık talimatıyla değişiklikler bölüm 8’deki commitlere ayrıldı. Bitirme bekleyende korundu; tamamlanan bu kapsam sonrasında CloneEmpires üst durum dosyasında TAMAMLANAN bölümüne alındı. Başka repo dosyaları değiştirilmedi.

### Değişen davranış ve kanıt eşlemesi

| Kapsam | Son davranış / ana dosyalar | Kontrol |
| --- | --- | --- |
| T1, K1–K3 | `session_menu.py`, `app.py`, `save_load.py`: Yeni oyun/Devam et, isteğe bağlı ad, ayrı kimlik/dosya, son kayıt sırası, 30 saniyelik/manuel/ilk/çıkış kaydı; atomik yazma, sağlam yedek, hata ekranı | Menüde yazmama, 29/30 saniye sınırı, iki dünyanın ayrılığı, replace hatası, eski/bozuk kayıt ve yedekten kurtarma, yazılamayan klasörde bellekte oyun; gerçek X11 akışı |
| T2 | `save_load.py`: sürüm 1, tüm ilgili alt tür/istatistik/görev/bağ/sayaç/kuyruk/kamera/XP; geçici dünyada doğrulama; eski sürümsüz dosya korunarak ret | Zengin JSON gidiş-dönüş, 10 bozulma varyantı, bağımsız anlık görüntü, hatalı yüklemede aktif dünya korunması |
| T3, K4–K5 | `simulation.py`, `app.py`: olay sınırlarına göre offline üretim, sonuç+zamanı birlikte yazmadan oturumu açmama; yerel saatte geri gitmeme | Tekrarlanan açılış/geri saat, bir saatlik üretim, iş/kuyruk/yenilenme, donan saha toplama/hareket/savaş, büyük/küçük adım karşılaştırması |
| T4 | `production_queue.py`, `building.py`, katalog: geliştirmede kuyruk korunur; siparişin seviyesi/maliyeti verildiği anda saklanır; doğrudan L2 stats doğru | Aktif+bekleyen L1 siparişle geliştirme, yeni L2 sipariş, doğrudan L2 için seviye şartı, iptal iadesi, boş doğum hücresi bekleme |
| T5 | `construction_manager.py`, `simulation.py`, XP: tek ortak konum/koşul kontrolü, ödeme öncesi ret, tamamlanmada tek XP | Dolu/sınır dışı/güvensiz yer, kaynak/seviye retleri, hücre merkezine oturma, köylü katkısıyla da tek XP |
| T6 | `unit.py`, `worker.py`, `world.py`, seçim: ulaşılamayan yolda güvenli bekleme, yarım saniyelik yeniden arama; duvardan doğrudan geçiş yok; boş hücrede doğum | Tam duvar, sonradan/mid-step engel, toplama/saldırıda sınırlı arama, dolu dünya kuyruğu, düşman emir sınırı |
| T7 | `camera.py`, `ui.py`, `renderer.py`: imleç noktasını koruyan zoom, aynı buton dikdörtgeni ve event.pos, görünmeyen/ölü nesnelerin seçim dışı olması | Üç ekran noktası ve zoom sınırları, dört dış buton kenarı, farklı gerçek fare konumunda event.pos, gizli köylü, X11 seçim/market/zoom |
| T8 | `building.py`, `simulation.py`: toplam t^1.05 hakkının yeni farkı; kapasite taşması işlenmiş sayılır; ayrı pasif/ücretli iş kontrolleri | 30/60 FPS, 1 saniye ve tek büyük adım eşitliği; dolu depo, yeniden başlatma, kayıt/offline süre, X11'de iki üretimin birlikte çalışması |
| T9 | `requirements*.txt`, README, tutorial, tests: yalnız Pygame çalışma kurulumu; pytest/Pillow geliştirme listesi; kapsamlı Türkçe rehber | Temiz kurulum, 130 test, 85 PNG'nin geçici üretimi/doğrulaması, kaynak/dosya/fonksiyon/bağlantı karşılaştırması |
| T10 | Yeni içerik/oyun hedefi/grafik/ses/multiplayer eklenmedi; mevcut denge sayıları korundu | README ve rehber gerçek erişilebilir özelliklerle eşlendi; Atlı/Mage, nüfus/depo, kule tamiri/geliştirme UI'si kapsam dışında |

### Çalıştırılan kontroller

1. **Temiz kurulum:** `/tmp/cloneempires-clean-env` sistem paketlerini görmeyen Python 3.12.3 sanal ortamıdır. Önce yalnız `requirements.txt` kuruldu (Pygame 2.6.1). pytest ve Pillow bulunmadığı doğrulanırken başlangıç, hazır PNG çizimi, kayıt ve normal kapanış çalıştı. Ardından `requirements-dev.txt` ile pytest 9.1.1 ve Pillow 12.3.0 kuruldu. Mevcut alt sürüm şartları yükseltilmedi; bunlar paket çözümleyicinin bu ortamda kurduğu sürümlerdir.
2. **Tüm testler:** `PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /tmp/cloneempires-clean-env/bin/python -B -m pytest tests -q -p no:cacheprovider` → **130 geçti**. İlk 85 test korundu; toplama ve yerleştirmedeki zayıf/yanlış beklentiler gerçek davranışla düzeltildi. Ortak fixture bütün SaveManager kayıtlarını geçici dizine yönlendirir.
3. **Gerçek pencere:** SDL `x11`, 1280×720, programatik SDL fare/metin olayları. Yeni oyun/Türkçe isim, market sekmesi/kart satın alma, kaynak binası inşası, pasif üretim, köylü seçip sağ tıkla atama, Hızlı mod/ücretli üretim, zoom noktası, düşman bilgi seçimi ve komut alamaması, oyuncuyla kontrollü savaş/hasar, F5 karşılığı üst Kaydet düğmesi, Menü, ikinci dünya, ilk dünyadan devam, yapay yazma hatası/Oyuna dön ve QUIT ile kayıt geçti. Oyun/kayıt listesi/hata ekranı görüntüleri açılıp incelendi. Son geçici çıktı: `/tmp/user/1000/cloneempires-window-xo4z5xri/result.json`; betik `/tmp/cloneempires-window-check.py`. Bunlar kalıcı kaynak bağımlılığı değildir.
4. **İsteğe bağlı görsel üretimi:** `generate_sprites.ASSETS_DIR` geçici dizine yönlendirildi; 85 PNG üretildi. Her dosya Pillow ile doğrulandı ve dosya adları depodaki 85 PNG ile eşleşti. Asılların SHA-256 özetleri önce/sonra aynıydı. Çıktı: `/tmp/user/1000/cloneempires-sprites-4a7_utga`.
5. **Rehber:** Tek ana rehber `tutorial.md` yeniden düzenlendi; README bağlantısı eklendi. 148 proje dosyası, 53 Python dosyası, 395 elle tanımlanmış fonksiyon ve 36 sınıf için kapsam sağlandı. Paket işaretleri, yapılandırma, lisans, kayıt çıktıları, tüm PNG'ler ve isteğe bağlı üretici de açıklandı. Python kaynak blokları gerçek dosyalarla, Markdown yerel bağlantıları mevcut dosyalarla karşılaştırıldı; `git diff --check` uygulandı.

### Doğrulanmayan veya tasarım gereği sınırlı kalan noktalar

- Pencere kontrolü gerçek X11 üzerinde programatiktir; uzun süreli fiziksel fare/klavye oynanışı, denge ve FPS ölçümü değildir. Windows/macOS çalıştırılmadı. Ses yeni kapsamda bulunmaz; testler dummy ses sürücüsünü kullanır.
- Fiziksel disk arızası/güç kesintisi uygulanmadı; dosya hatası enjeksiyonu atomik main/backup korumasını sınar. Son başarılı kayıttan sonraki bellekteki ilerleme zorla kapatmada kaybolabilir.
- Yerel saatin ileri alınması geliri etkileyebilir; çevrimiçi saat/doğrulama yoktur. Aynı kayıt dizinine iki oyun sürecinin eşzamanlı yazımı için kilit eklenmedi.
- Üretim adım tutarlılığı, savaş/hareket/AI için bütün motorun deterministik olması anlamına gelmez. Rastgele devriye, tek karelik hareket adımı ve saha toplamasının mevcut mantığı korunur.
- Eski `autosave.json` aktarılmaz. Harita/seçim/önbellek ve animasyon durumunun kalıcılık sınırları rehberde açıklanır; kaynakta tanımlı ama arayüzde erişilemeyen özellikler tamamlanmış ürün özelliği gibi sunulmaz.

Son ürün rehberi: [tutorial.md](tutorial.md). Kısa kurulum ve kontroller: [README.md](README.md).


## 8. Kullanıcı onayıyla commit ve push hazırlığı

Kullanıcı, “Tamamdır, gerekli commitleri atarak pushlayabilirsin” diyerek yayın yetkisi verdi. Hedef uzak depo `origin` (`https://github.com/MrSqy/CloneEmpires.git`), dal `main` olarak korundu. Fetch sonrası başlangıç dalında uzak/yerel ayrışma yoktu; geçmişi yeniden yazma veya force push gerekmiyor.

Birbirine bağlı kayıt/oturum/üretim ve kurallar, ilgili birleşik regresyon testleriyle tek çalışır değişiklik grubunda tutuldu. Son commit düzeni:

1. `ae66c71` — `feat: add persistent worlds and consistent production rules`: Oyun kodu, menü/kayıt/offline üretim ve bütün ilgili davranış testleri.
2. `e6dffee` — `build: separate runtime and development dependencies`: Çalışma ve isteğe bağlı geliştirme/görsel üretim bağımlılıkları.
3. `docs: publish Turkish project guide and implementation decisions`: README, kapsamlı tutorial.md, repo AGENTS.md ve bu uygulama/karar kaydı.

Commit hazırlığında temiz sanal ortamda **130 test yeniden geçti**; dosya farkı denetimi temizdi. Kayıt dosyaları, geçici test çıktıları ve üst klasördeki diğer proje durumları bu reponun commit kapsamına alınmadı. Push sonrası uzak dalın son commit kimliğiyle yerel HEAD’in eşleşmesi ayrıca kontrol edilir; yayın sonucu görev kapanışında bildirilir.
