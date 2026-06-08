# Social Empires Clone — Yapılacaklar Listesi

> Bu doküman, oyunun bir sonraki geliştirme evresi için kapsamlı bir roadmap'tir.  
> Her bölüm bağımsız olarak ele alınabilir, ancak sırası takip edilmesi önerilir.

---

## 1. Market Sistemi (Shop)

### 1.1. UI Konumu & Açılış/Kapanış
- **Konum:** Ekranın sağ alt köşesinde sabit bir "Market" butonu.
- **Açılış:** Butona tıklanınca ekranın ortasında veya sağ tarafında kayan bir panel açılır.
- **Kapanış:** ESC tuşu, X butonu veya market dışına tıklama ile kapanır.
- **State Persistence:** Market en son hangi kategori sekmesinde kapandıysa, bir sonraki açılışta o sekme varsayılan olarak gösterilir. (`UIManager` içinde `last_market_tab` değişkeni tutulur.)

### 1.2. 4 Kategori Sekmesi

| Sekme Adı | İçerik |
|-----------|--------|
| **Binalar** | Ev (House) |
| **Kuleler** | Level 1 Ok Kulesi, Level 2 Ok Kulesi |
| **Barakalar** | Level 1 Mızrakçı Barakası, Level 2 Mızrakçı Barakası, Level 1 Kılıçlı Barakası, Level 2 Kılıçlı Barakası, Level 1 Okçu Barakası, Level 2 Okçu Barakası |
| **Kaynaklar** | Kereste Binası (Woodcutter), Kasap (Butcher/Farm), Altın Madeni (Gold Mine), Taş Ocağı (Quarry) |

### 1.3. Market Item Kartı Tasarımı
Her item için standart bir kart:
- **İkon/Sprite** (sol üst)
- **İsim** (orta)
- **Maliyet** (alt: odun, taş, altın, gıda, mücevher)
- **Satın Al** butonu (maliyet karşılanıyorsa aktif, yetersizse gri/inaktif)
- **Level gereksinimi** varsa badge olarak göster

### 1.4. Satın Alma Akışı
1. Player karttaki "Satın Al" butonuna tıklar.
2. `ConstructionManager.place_building(building_type, x, y)` çağrılır.
3. Kaynaklar düşülür.
4. Bina inşaat alanında (construction site) olarak belirir.
5. Eğer yakında boşta işçi varsa otomatik olarak inşaat görevi atanır.
6. İnşaat tamamlanınca XP ödülü verilir.

---

## 2. Kaynak Binaları & Köylü Atama Sistemi

### 2.1. Kaynak Bina Tipleri

| Bina | Ürettiği Kaynak | Varsayılan Üretim Hızı |
|------|-----------------|------------------------|
| Kereste Binası | Odun | 1.0 |
| Kasap | Gıda | 1.0 |
| Altın Madeni | Altın | 0.8 |
| Taş Ocağı | Taş | 1.0 |

> Not: Bu binalar `Building.update(dt, economy)` ile `f(t)` formülüyle de üretim yapar, ancak köylü atama sistemi bu üretimi **ek olarak** boost eder.

### 2.2. Köylü Atama UI'si
- Kaynak binası seçildiğinde alt bar'da "Köylü Ata" butonu belirir.
- Mevcut boşta köylüler listelenir (dropdown veya küçük portreler).
- Max **4 köylü** atanabilir.
- Atanan köylüler binaya bağlanır (`building.assigned_workers: List[Worker]`).
- Köylü atandığında binanın `is_producing = True` olur (eğer çalışma modu seçiliyse).

### 2.3. Çalışma Modları (4 Mod)

| Mod | Süre | Taban Kaynak Kazanç | Mücevher Maliyeti |
|-----|------|---------------------|-------------------|
| Hızlı | 2 dk | 10 | 20 |
| Normal | 5 dk | 30 | 50 |
| Uzun | 10 dk | 75 | 100 |
| Maraton | 30 dk | 250 | 300 |

- **Mücevher maliyeti formülü:** `dakika × 10` (örn: 2 dk → 20 mücevher)
- **Kaynak kazancı formülü:** `taban_kazanç × köylü_multiplayer`
  - 1 köylü: ×1.0
  - 2 köylü: ×1.25
  - 3 köylü: ×1.5
  - 4 köylü: ×2.0
- **Toplam mücevher = kaynakların 5'e bölünmüş hali:** `ceil(kazanç / 5)`
  - Örn: 10 kaynak → `ceil(10/5) = 2` mücevher
  - 30 kaynak → `ceil(30/5) = 6` mücevher
  - 75 kaynak → `ceil(75/5) = 15` mücevher
  - 250 kaynak → `ceil(250/5) = 50` mücevher
- Float değer dönerse `math.ceil()` uygulanır.

### 2.4. Çalışma Akışı
1. Player köylü(leri) atar ve mod seçer.
2. `building.start_worker_production(mode, workers)` çağrılır.
3. Geri sayım başlar (`building.worker_timer`).
4. Süre dolunca:
   - Kaynaklar `economy.add_resources()` ile eklenir.
   - Mücevherler `economy.add_resources({"gem": ...})` ile eklenir.
   - Köylüler boşta duruma döner (`worker.task = None`).
   - XP ödülü verilir.
5. Eğer köylü binadan uzaklaştırılırsa/silinirse, üretim iptal olur (kısmi ödeme yok).

---

## 3. İyileştirmeler & Bugfix'ler

### 3.1. Spritelar (Procedural → Temiz)
- Mevcut `tools/generate_sprites.py` basit renkli kareler üretiyor.
- **Hedef:** Daha detaylı, social-empires tarzı izometrik sprite'lar.
- **Yaklaşım:**
  - Her entity tipi için `Pillow` ile katmanlı çizim (gövde + detay + gölge).
  - Veya hazır asset paketinden (itch.io, opengameart) izometrik sprite'lar entegre etmek.
  - En azından farklı bina seviyeleri ve birim tipleri görsel olarak ayırt edilebilir olmalı.

### 3.2. İzometrik Hitbox Düzeltmesi
- **Sorun:** Sol tık seçimi bazen kayıyor, entity'lerin hitbox'ı ile ekrandaki sprite hizası tutarsız.
- **Neden:** `screen_to_world` ve `world_to_screen` dönüşümlerinde offset hesaplaması eksik veya zoom ile birlikte kayma var.
- **Çözüm:**
  - `Renderer.draw_entities`'de her entity için `get_rect(center=...)` kullanılıyor.
  - Hitbox hesaplaması (`get_entities_in_range`) sadece `(x, y)` merkez noktası üzerinden yapılıyor.
  - **Düzeltme:** Seçim için entity'nin ekrandaki bounding box'ını (`sprite.get_rect()`) kullan, merkez nokta yerine.
  - Alternatif: `camera.screen_to_world` sonrası `(x, y)` ile entity merkezi arasındaki mesafe yerine, entity'nin genişliği/yüksekliği dikkate alınarak seçim yapılmalı.

### 3.3. Okçu Menzilli Saldırı Bug'ı
- **Sorun:** Okçu birimleri (archer) menzilli saldırmıyor. `attack_range` yüksek olmasına rağmen yaklaşma davranışı gösteriyor.
- **Neden:** `_approach_target` sadece `attack_range` kontrolü yapıyor, menzilli birimler için durup saldırması lazım. Ayrıca `BattleManager` okçular için fiziksel hasar yerine menzilli saldırı mantığı yok.
- **Çözüm:**
  - Okçu için `attack_range` default olarak 5.0+ yapılmalı (`UnitStats` veya setup'ta override).
  - `BattleManager`'da menzilli birimler için özel davranış: hedef menzildeyse hareket etme, sadece saldır.
  - Görsel olarak ok/okçu projektil efekti eklenebilir (ileri aşama).

### 3.4. Köylü Kaynak Çeşitliliği
- **Sorun:** Şu anda sadece ağaç (wood) kaynağı var. Köylüler sadece ağaç toplayabiliyor.
- **Hedef:** Çevrede ağaç, taş, altın, hayvan kaynakları olacak.
- **Yeni Kaynak Tipleri:**
  - `ResourceNode("stone", x, y, amount)` — Taş yığını
  - `ResourceNode("gold", x, y, amount)` — Altın cevheri
  - `ResourceNode("food", x, y, amount)` — Hayvan sürüsü / av hayvanı
- **Köylü Davranışı:**
  - Köylü bir kaynağa sağ tık ile gönderildiğinde, o kaynağın tipine göre toplama yapar.
  - **2 saniye** toplama süresi sonucunda **10 birim** kaynak verir.
  - Doldurma kapasitesine (`carry_capacity = 20`) ulaşınca veya kaynak tükenince ev/economy merkezine döner.
  - `Worker._do_gather`'da `resource_type` bazlı toplama mantığı zaten var.

---

## 4. Social Empires Mekanik Notları

### 4.1. Orijinal Oyundan İlham Alan Mekanikler
- **Town Hall merkezli büyüme:** Tüm üretim ve gelişme Town Hall etrafında şekillenir.
- **Bina seviyeleri:** Her bina 3 seviyeye kadar yükseltilebilir. Maliyet her seviyede 2× artar.
- **Güvenlik bölgeleri:**
  - `safe` (merkez 20×20): Düşman spawn olmaz.
  - `neutral` (orta halka): Zayıf düşmanlar.
  - `danger` (dış halka): Güçlü düşmanlar ve boss'lar.
- **AI Patroller:** Düşmanlar önceden tanımlanmış rotalarda devriye gezer.
- **Çift tıklama seçimi:** Aynı tipteki tüm birimleri bölgede seçer.

### 4.2. Eklenmesi Düşünülen İleri Seviye Mekanikler
- **Sınır duvarları ve kapılar:** Bina inşaatına ekleme.
- **Büyü kulesi:** Menzilli büyü hasarı (magic damage).
- **Boss savaşları:** Danger bölgede periyodik boss spawn'u.
- **PVP skor tablosu:** AI saldırı dalgalarına dayanma süresi.
- **Görev/quest sistemi:** "5 troll öldür", "10 odun topla" gibi günlük görevler.
- **Arkadaş sistemi:** Komşu köylerden kaynak/asker takviyesi (simüle edilebilir).

### 4.3. Ekonomi Dengesi Hatırlatmaları
- Depo limiti (`storage_limit`) oyuncuyu zorlar — yeni depo/storage binası inşa etmek gerekir.
- `f(t) = base_rate × t^1.05 × level_bonus` formülü uzun süreli üretimi ödüllendirir.
- Market sistemi ile doğrudan kaynak satın alma (mücevher ile) ekonomiyi hızlandırabilir — bunu dengelemek için maliyetler katlanarak artmalı.

---

## 5. Implementasyon Sırası Önerisi

1. **Market UI** — `UIManager` içinde yeni panel, 4 sekme, item kartları.
2. **Kaynak Binaları + Köylü Atama** — `Building`'e `assigned_workers` ve mod sistemi.
3. **Hitbox Düzeltmesi** — Seçim mantığını bounding box'a geçir.
4. **Okçu Menzil Fix** — `attack_range` değerleri ve `BattleManager` menzilli davranış.
5. **Yeni Kaynak Node'ları** — Taş, altın, hayvan.
6. **Köylü 2sn/10 kaynak toplama** — `Worker._do_gather`'da süre bazlı toplama.
7. **Sprite İyileştirmeleri** — `tools/generate_sprites.py` güncelleme veya asset entegrasyonu.
8. **Test Coverage** — Her yeni mekanik için unit/integration test.

---

*Son güncelleme: 2026-05-30*
