# CloneEmpires

> **Isometric RTS — Build, Battle, Conquer.**

CloneEmpires, klasik Facebook oyunu **Social Empires**'ten ilham alan, Python & Pygame ile geliştirilmiş izometrik strateji oyunudur. Kaynak toplayın, ordunuzu kurun, kuleler dikin ve troll ordularına karşı üssünüzü savunun.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Pygame](https://img.shields.io/badge/pygame-2.5+-green.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)

---

## Özellikler

| Alan | Detay |
|------|-------|
| 🏗️ **İnşaat Sistemi** | Town Hall, barakalar, kaynak binaları ve kuleler inşa edin. Yeşil güvenli bölgede serbest inşaat. |
| ⚔️ **Savaş Mekaniği** | Grid-tabanlı hareket, menzilli/melee ayrımı, homing projectile'lar, counter-attack. |
| 🪵 **Kaynak Ekonomisi** | Odun, taş, gıda, altın ve nadir mücevher madenleri. f(t) üretim formülü ile pasif gelir. |
| 👷 **Köylü Sistemi** | Kaynak binalarına atama, 4 farklı çalışma modu (Maraton/Hızlı/Normal/Kısa), üretim kuyruğu. |
| 🏰 **Baraka & Asker** | Mızrakçı, Kılıçlı, Okçu, Atlı, Mage. Level 2 barakalar 2 kat güçlü L2 asker üretir. |
| 🎯 **Geliştirme** | Barakalar ve kuleler Level 2'ye yükseltilebilir (tadilat + kaynak şartı). |
| 💾 **Kaydetme** | Otomatik 30 saniyede bir autosave. Manuel save/load desteği. |
| 🎨 **İzometrik Görünüm** | Zoom (0.5x–3x), kaydırma, z-sıralamalı entity render. |

---

## Kurulum

```bash
# 1. Repoyu klonlayın
git clone https://github.com/MrSqy/CloneEmpires.git
cd CloneEmpires

# 2. Sanal ortam oluşturun
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows

# 3. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 4. Sprite'ları oluşturun (procedural assetler)
python tools/generate_sprites.py

# 5. Oyunu başlatın
python main.py
```

---

## Kontroller

| Tuş / Eylem | Fonksiyon |
|-------------|-----------|
| **Sol Tık** | Birim/bina seç, inşaat yerleştir |
| **Çift Sol Tık** | Aynı tipteki tüm birimleri seç |
| **Sağ Tık** | Seçili birimleri hareket ettir / saldır / kaynak topla |
| **Orta Tık Sürükle** | Haritayı kaydır |
| **Tekerlek** | Yakınlaştır / Uzaklaştır |
| **ESC** | Seçimi temizle, pencereyi kapat |
| **1** | Oduncu Evi inşaat modu |
| **2** | Çiftlik inşaat modu |
| **3** | Mızrakçı Barakası inşaat modu |
| **4** | Ev inşaat modu |

---

## Birimler & Statlar

| Birim | Can | Hasar | Menzil | Görüş | Özellik |
|-------|-----|-------|--------|-------|---------|
| **Mızraklı** | 150 | 15 | 2 | 8 | Dengeli tank |
| **Kılıçlı** | 100 | 20 | 1 | 7 | Yüksek hasar |
| **Okçu** | 60 | 25 | 8 | 14 | Uzaktan ölüm |
| **Mage** | 70 | 28 (büyü) | 5 | 10 | Büyü hasarı |
| **Atlı** | 140 | 18 | 1 | 7 | Hızlı hücum |

> **Level 2** birimlerde altın rozet görünür; can ve hasar **2 kat**.

---

## Proje Yapısı

```
CloneEmpires/
├── game/                 # Ana oyun motoru
│   ├── app.py            # Ana döngü (GameApp)
│   ├── renderer.py       # İzometrik render & sprite cache
│   ├── battle_manager.py # Savaş, projectile, AI acquire
│   ├── economy.py        # f(t) üretim & depolama
│   ├── entities/         # Unit, Building, Worker, Resource, Projectile
│   ├── grid.py           # A* pathfinding, cell math
│   ├── ui.py             # Bottom bar, market, butonlar
│   └── ...
├── assets/               # Procedural PNG sprite'lar
├── tests/                # 85+ pytest testi
├── tools/                # Sprite generator (Pillow)
├── saves/                # Otomatik kayıtlar
└── main.py               # Giriş noktası
```

---

## Test

```bash
pytest tests/ -v
```

---

## Yol Haritası

- [ ] Custom model/asset entegrasyonu
- [ ] Market sistemi (bina satın alma)
- [ ] Çok oyunculu temelleri
- [ ] Ses & müzik
- [ ] Alan genişletme (yeşil → kahverengi bölge)

---

## Lisans

MIT License — detaylar için [LICENSE](LICENSE) dosyasına bakın.

---

> *Made with ☕ & Pygame by Baran.*
