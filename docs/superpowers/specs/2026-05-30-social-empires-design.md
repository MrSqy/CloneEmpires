# Social Empires Tarzı Strateji/Builder Oyunu — Tasarım Dokümanı

**Tarih:** 2026-05-30
**Teknoloji:** Python 3.10+, Pygame 2.x
**Platform:** Masaüstü (Windows/Linux/macOS)
**Mod:** Tek oyunculu MVP (çok oyunculu modüler olarak sonradan eklenebilir)

---

## 1. Temel Oyun Döngüsü ve MVP Kapsamı

Oyuncu başlangıçta bir **Town Hall** (Köy Merkezi) ile başlar. Etrafında sınırlı bir alanda bazı kaynak node'ları vardır. MVP'de şu döngü olur:

1. **Keşif** → Haritada kaynak node'larını ve AI düşman kamplarını keşfet
2. **Toplama** → İşçileri kaynak node'larına gönder veya yapıları çalıştır
3. **İnşaat** → Toplanan kaynaklarla bina inşa et
4. **Üretim** → Kışlalarda asker yetiştir
5. **Savaş** → Haritadaki AI düşman kamplarına saldır
6. **Gelişim** → Town Hall seviyesi yükselterek yeni bina ve birim türlerini aç

**MVP Sınırı:**
- 1 harita (80×80 tile)
- 3 asker tipi × 2 seviye = 6 birim (Mızraklı L1/L2, Atli L1/L2, Okçu L1/L2)
- 9 bina tipi (Town Hall, Ev, 3 Kışla, 4 Kaynak Evi)
- 5 kaynak (Odun, Taş, Gıda, Altın, Mücevher)
- 3 düşman kampı, 3 düşman tipi (Bıçaklı Troll, Sopalı Büyük Troll, Okçu Troll)

---

## 2. Mimari ve Proje Yapısı

```
social_empires/
├── main.py                 # Giriş noktası
├── requirements.txt
├── assets/                 # PNG sprite'ları, tileset'ler, ikonlar
│   ├── units/              # Asker ve düşman sprite'ları
│   ├── buildings/          # Bina sprite'ları
│   └── terrain/            # Zemin, ağaç, kaynak node'ları
├── saves/                  # JSON save dosyaları
└── game/
    ├── __init__.py
    ├── app.py              # Ana döngü, event handling, oyun durumu
    ├── constants.py        # Ekran boyutu, tile boyutları, renkler, kaynak limitleri
    ├── camera.py           # Isometrik kamera (zoom, pan)
    ├── isometric.py        # Isometrik projeksiyon math (world↔screen)
    ├── models.py           # Entity, Unit, Building, ResourceNode veri modelleri
    ├── world.py            # Harita, entity listesi, collision grid
    ├── renderer.py         # Isometrik çizim, depth sorting, efektler
    ├── combat.py           # Savaş sistemi, hasar hesabı, çatışma çözümleme
    ├── economy.py          # Kaynak yönetimi, f(t) üretim formülü
    ├── ai_controller.py    # Düşman AI'sı (patrol, agro, saldırı)
    ├── ui.py               # Kaynak paneli, alt bar, bina menüsü, birim bilgisi
    ├── selection.py        # Tekli/çoklu seçim, çift tıklama, sürükle-bırak, emir verme
    ├── entities/
    │   ├── base_entity.py  # Tüm entity'lerin ortak temel sınıfı
    │   ├── unit.py         # Asker ve düşman sınıfları (8 istatistik)
    │   ├── building.py     # Bina sınıfları (üretim, seviye, maliyet)
    │   └── resource.py     # Kaynak node'ları
    └── save_load.py        # Oyun kaydetme/yükleme (JSON)
```

**Temel Prensip:** Her entity `BaseEntity`'den türeyecek — konum, boyut, sprite, seçili durum gibi ortak özellikler burada. `Unit` sınıfı 8 savaş istatistiğini ve davranış state machine'ini (IDLE, MOVE, ATTACK, DEAD) taşıyacak. `Building` sınıfı üretim kuyruğunu, seviyeyi ve maliyeti yönetecek.

---

## 3. Isometrik Harita ve Kamera Sistemi

**Harita:** Tek sabit harita, **80×80 tile** boyutunda.

**Güvenlik Bölgeleri:**
- **Merkez 20×20** → Oyuncu üssü (Town Hall spawn noktası)
- **Merkez 40×40** → Güvenli bölge; düşman kampı yok, kaynaklar var
- **80×80 dış halka** → Riskli bölge; kaynaklar + 3 düşman kampı

**Zemin Türleri:**
- **Çimen** → Yürünebilir, bina kurulabilir
- **Toprak** → Yürünebilir, bina kurulabilir
- **Su** → Yürünemez, bina kurulamaz

**Tile Boyutu:** 64×32 piksel (2:1 oran, klasik isometrik diamond)

**Kaynak Node'ları (haritada önceden yerleştirilmiş):**
- Ağaç ormanları (odun)
- Taş yığınları (taş)
- Çiftlik alanları (gıda)
- Altın madenleri (altın)
- Nadir mücevher madenleri (mücevher — haritada 2-3 adet)

**Kamera:**
- **Zoom:** Ctrl + Mouse Wheel
- **Pan:** Mouse orta tuşuyla sürükle veya ekran kenarına götürünce edge-panning
- **Seçim:** Sol tık (tekli), sürükleyerek çoklu seçim (drag selection box)

**Derinlik Sıralaması:** Her frame'de entity'ler screen-Y koordinatına göre sıralanır (painters algorithm). Böylece alttaki nesneler üsttekilerin arkada kalır.

---

## 4. Savaş ve Ekonomi Sistemleri

### 4.1 Savaş Sistemi (Gerçek Zamanlı)

Her birimin 8 istatistiği vardır. Çatışma her frame kontrol edilir:

| İstatistik | Açıklama |
|---|---|
| Can (HP) | 0 olunca entity ölür |
| Fiziksel Hasar | Fiziksel saldırı gücü |
| Büyü Hasarı | Büyüsel saldırı gücü |
| Zırh | Fiziksel hasarı azaltır |
| Büyü Direnci | Büyü hasarını azaltır |
| Menzil | Saldırı menzili (tile veya piksel) |
| Hareket Hızı | Tile/saniye cinsinden hareket |
| Saldırı Hızı | Saniyedeki saldırı sayısı |

**Hasar Formülleri:**
- Fiziksel: `net = max(0, attacker.attack_phys - target.armor)`
- Büyü: `net = max(0, attacker.attack_magic - target.magic_resist)`

**Saldırı Hızı:** `cooldown = 1 / attack_speed` saniye.

**Menzil:**
- Yakın: Mızraklı, Atli, Bıçaklı Troll, Sopalı Büyük Troll → hedefe yanaşmalı
- Uzak: Okçu, Okçu Troll → menzil içinden ateş eder

**Ölüm:** Can ≤ 0 olunca entity kaybolur. Düşman kampındaki tüm troller ölürse kamp yok edilir ve **mücevher ganimeti** düşer.

**AI Davranışı:**
- Düşmanlar kendi kamp alanlarında **patrol** yapar
- Oyuncu birimleri **agro menziline** girerse hedef seçip saldırır
- Agro menzili ile attack menzili ayrı değerlerdir

### 4.2 Ekonomi Sistemi

**5 Kaynak:** Odun 🪵, Taş 🪨, Gıda 🍞, Altın 🪙, Mücevher 💎

**Kaynak Evleri (4 adet):**
- Oduncu Evi → Odun üretir
- Taş Ocağı → Taş üretir
- Çiftlik → Gıda üretir
- Altın Madeni Evi → Altın üretir

**Üretim Formülü:** Çalıştırılan süre `t` saniye için:
```
f(t) = base_rate × t^1.05 × bina_seviye_bonusu
```
- Örnek: 10 sn → ~12.2 birim, 20 sn → ~26.5 birim
- 2 kat süre ≈ 2.17 kat üretim → **f(at) > a·f(t)** sağlanır

**Mücevher (Özel Kaynak):**
- Haritadaki nadir mücevher madenlerinden işçi göndererek toplanır
- Düşman kampı yok edilince ganimet olarak düşer
- Town Hall yükseltme ve premium birimlerin maliyeti mücevherle ödenir
- Kaynak evi yoktur (evlerden üretilemez)

**Depo Limiti:** Başlangıç 500/kaynak. Her depo seviyesi +500 artırır.

---

## 5. UI ve Kontroller

### 5.1 Sol Üst Panel (Kaynak ve Level)

Sol üst köşede dikey bir panel bulunur, üstten aşağıya şu sırayla:

1. **Kral Adı** — Oyuncunun ana karakterinin adı (MVP'de placeholder/istikrarlı bir isim gösterilir; karakter oynanabilir tasarlanacak ama MVP kapsamında kontrol edilemez)
2. **Level / XP Çubuğu** — Yatay uzun bir bar. Town Hall seviyesi ve mevcut XP gösterilir. XP dolduğunda seviye atlanır.
3. **Kaynak Göstergeleri** — 3 satır halinde:
   - **Satır 1:** Odun 🪵 — Gıda 🍞
   - **Satır 2:** Taş 🪨 — Altın 🪙
   - **Satır 3:** Mücevher 💎 (tek başına, ortalanmış)
   
   Her kaynak ikonunun yanında mevcut miktarı ve depo limiti gösterilir (örn. `🪵 340/500`)

### 5.2 Alt Bar (Entity Eylem Paneli)

Ekranın altında yatay bir bar bulunur. Seçili entity'ye göre dinamik olarak değişir:

- **Bina seçiliyse:**
  - Kışla → Asker yetiştirme butonları (mızraklı/atlı/okçu, L1/L2, maliyetleriyle)
  - Kaynak Evi → Çalıştır / Durdur butonları, mevcut üretim durumu
  - Town Hall → Seviye yükseltme butonu (maliyetleriyle)
  - Ev → Nüfus kapasitesi bilgisi
  - Depo → Kapasite artırma butonu
  
- **Asker seçiliyse:**
  - Askerin portresi ve 8 istatistiği (büyük görünüm)
  - Özel yetenek butonları (MVP'de sadece "Saldır" / "Dur")

- **Çoklu asker seçiliyse (Social Empires tarzı):**
  - Her askerin küçük fotoğrafı yatay sıralanır
  - Her portrenin hemen altında mini can çubuğu
  - Tüm seçili askerler için toplu emir butonları (Saldır, Hareket, Dur)

### 5.3 Kontroller

| İşlem | Açıklama |
|---|---|
| Sol tık | Tekli seçim / hedefe emir |
| Çift sol tık | Aynı sınıftan tüm askerleri menzilli alanda seç |
| Sürükle + sol tık bırak | Çoklu seçim kutusu |
| Sağ tık | Seçili birimlere hareket/saldırı emri |
| Ctrl + Wheel | Zoom in/out |
| Orta tuş sürükle | Haritayı kaydır (pan) |
| ESC | Seçimi iptal / menüyü kapat |

**Çift Tıklama Seçimi:** Bir askere çift tıklanırsa, belirli bir menzildeki (örn. 10 tile yarıçap veya ekrandaki) aynı tipteki tüm dost askerler seçilir. Alt barda her biri küçük portre + can çubuğu olarak gösterilir.

**Bina İnşaat Menüsü:** Town Hall veya boş tile seçiliyken "İnşaat" butonu. Açılır menüde mevcut binalar (maliyetleriyle). Gri = yetersiz kaynak, Yeşil = inşa edilebilir.

---

## 6. Save / Load ve Ana Menü

- **Format:** JSON (`saves/save_*.json`)
- **Kaydedilen veri:**
  - Tüm entity listesi (konum, can, seviye, tip)
  - Kaynak miktarları
  - Bina durumları ve seviyeleri
  - Kamera pozisyonu ve zoom seviyesi
- **Otomatik kayıt:** Her **30 saniyede** bir arka planda `autosave.json`
- **Ana menü ekranı:** Yeni Oyun / Devam Et / Kayıt Yükle / Ayarlar / Çıkış

---

## 7. Teknoloji ve Bağımlılıklar

```
pygame>=2.5.0
```

**Geliştirme ortamı:** Python 3.10+, virtualenv önerilir.

**Asset gereksinimleri (MVP minimum):**
- Isometrik zemin tile'ları (çimen, toprak, su)
- Bina sprite'ları (9 bina tipi × 1-2 seviye)
- Birim sprite'ları (6 dost birim + 3 düşman)
- Kaynak node sprite'ları (ağaç, taş, çiftlik, altın madeni, mücevher madeni)
- UI ikonları (5 kaynak, butonlar, can çubuğu)

---

## 8. Gelecekteki Modüler Eklentiler (MVP dışı)

- Çok oyunculu modül (Node.js + Socket.io backend)
- Mana ve büyü sistemi (ana karakter için)
- Özel yetenekler (skill) ve aktif/passif yetenekler
- Yeni haritalar ve seviye sistemi
- Phaser.js ile web portu
- Kral / ana karakterin oynanabilir olması (haritada dolaşabilme, savaşa katılma)
