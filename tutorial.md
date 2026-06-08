# CloneEmpires — Sıfırdan Tam Tur

> Bu döküman, **bu klasördeki** CloneEmpires projesinin **her Python dosyasını**, kullanılan **dillerin syntax'ını** ve **dosyalar arası bağlamı** sıfırdan başlayan biri için anlatır. Sonunda hem projeyi tamamen anlamış, hem de yeni özellik eklemek istediğinde nereye dokunacağını bilmiş olursun.

---

## İçindekiler

0. [Önsöz ve Nasıl Okunmalı](#0-önsöz-ve-nasıl-okunmalı)
1. [Projeye 30 Saniyelik Bakış](#1-projeye-30-saniyelik-bakış)
2. [Kullanılan Teknolojiler — "Bunlar Ne, Niye Var?"](#2-kullanılan-teknolojiler--bunlar-ne-niye-var)
3. [Yüksek-Düzey Dizin Haritası](#3-yüksek-düzey-dizin-haritası)
4. [Konfigürasyon Dosyaları](#4-konfigürasyon-dosyaları)
5. [Uygulama Açılışı (`main.py` → `game/app.py` → GameApp)](#5-uygulama-açılışı)
6. [Oyun Motoru Çekirdeği (renderer, camera, isometric, grid, world)](#6-oyun-motoru-çekirdeği)
7. [Varlık Sistemi (`entities/`)](#7-varlık-sistemi)
8. [Ekonomi & Üretim (`economy.py`, `production_queue.py`, `work_modes.py`)](#8-ekonomi--üretim)
9. [İnşaat & Geliştirme (`building_catalog.py`, `construction_manager.py`)](#9-inşaat--geliştirme)
10. [Savaş & Combat (`combat.py`, `battle_manager.py`, `unit_stats.py`, `xp_system.py`)](#10-savaş--combat)
11. [AI & Otomasyon (`ai_controller.py`)](#11-ai--otomasyon)
12. [UI Sistemi (`ui.py`, `selection.py`)](#12-ui-sistemi)
13. [Kaydetme & Yükleme (`save_load.py`)](#13-kaydetme--yükleme)
14. [Test Kapsamı (`tests/`)](#14-test-kapsamı)
15. [Asset Sistemi (`assets/`, `tools/generate_sprites.py`)](#15-asset-sistemi)
16. [Tipik Geliştirici Akışları (Mini Tarifler)](#16-tipik-geliştirici-akışları)
17. [Hızlı Syntax Kartı](#17-hızlı-syntax-kartı)
18. [Sözlük ve Kısaltmalar](#18-sözlük-ve-kısaltmalar)
19. [İleri Adımlar / Önerilen Egzersizler](#19-ileri-adımlar)

---

## 0. Önsöz ve Nasıl Okunmalı

### Hedef kitle
Bu doküman, **Python temellerine aşina** ama Pygame, oyun motoru mimarisi, izometrik projeksiyon veya RTS (Real-Time Strategy) oyun geliştirme tecrübesi olmayan biri için yazılmıştır.

### Ön gereksinimler
- **Python 3.10+** (`python --version` ile kontrol et)
- Bir terminal (bash, zsh, PowerShell hepsi olur)

### Hızlı kurulum komutları

```bash
cd CloneEmpires
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows
pip install -r requirements.txt
python tools/generate_sprites.py   # procedural asset üret
python main.py                     # oyunu başlat
pytest tests/ -v                   # testleri çalıştır
```

Kaynak: `README.md:28-48`.

### Sıfırdan başlıyorum, nasıl okumalıyım?
Tutorial **sıralı okunmak için** tasarlandı, ama acelen varsa şu rota en hızlı kavramaya yarar:

1. Bölüm 1 → projenin ne olduğunu anla.
2. Bölüm 2 → kullanılan teknolojileri öğren.
3. Bölüm 4 → konfigürasyon dosyalarını gör.
4. Bölüm 5 → uygulama hangi sırayla başlıyor anla.
5. Bölüm 7 → varlık (entity) sistemini gör (tüm oyun bunun üzerine kurulu).
6. Bölüm 8 → ekonomi & üretim akışını anla.
7. Bölüm 10 → savaş sistemini anla.
8. Bölüm 16 → "Yeni özellik eklemek istesem ne yapardım?" tariflerini oku.

### Bu projedeki dil tercihi
Kod yorumları çoğunlukla **Türkçe**, değişken ve fonksiyon isimleri **İngilizce**. UI metinleri (butonlar, paneller) Türkçe.

---

## 1. Projeye 30 Saniyelik Bakış

**CloneEmpires**, klasik Facebook oyunu Social Empires'ten ilham alan, **Python & Pygame** ile geliştirilmiş izometrik RTS oyunudur.

Önemli özellikler:
- **İzometrik görünüm**: Zoom (0.5x–3x), kaydırma, z-sıralamalı entity render.
- **İnşaat sistemi**: Town Hall, barakalar, kaynak binaları ve kuleler inşa edin.
- **Savaş mekaniği**: Grid-tabanlı hareket, menzilli/melee ayrımı, homing projectile'lar, counter-attack.
- **Kaynak ekonomisi**: Odun, taş, gıda, altın ve nadir mücevher. `f(t)` üretim formülü ile pasif gelir.
- **Köylü sistemi**: Kaynak binalarına atama, 4 farklı çalışma modu, üretim kuyruğu.
- **Geliştirme**: Barakalar ve kuleler Level 2'ye yükseltilebilir.
- **Kaydetme**: Otomatik 30 saniyede bir autosave. Manuel save/load desteği.

### Üst-düzey veri akışı

```
+-------------------+     +-------------------+     +-------------------+
|   Kullanıcı       |     |   main.py         |     |   pygame          |
|   (tıklama, tuş)  | --> |   GameApp.run()   | --> |   display/surface |
+-------------------+     +--------+----------+     +--------+----------+
                                   |                          ^
                                   v                          |
                          +--------+----------+               |
                          |  Event Loop       |               |
                          |  _handle_events() |               |
                          +--------+----------+               |
                                   |                          |
                                   v                          |
                          +--------+----------+               |
                          |  Update Loop      |               |
                          |  _update(dt)      |               |
                          |  - world          |               |
                          |  - battle_manager |               |
                          |  - ai_controller  |               |
                          |  - economy        |               |
                          +--------+----------+               |
                                   |                          |
                                   v                          |
                          +--------+----------+               |
                          |  Render Loop      |---------------+
                          |  _render()        |
                          |  - renderer       |
                          |  - ui             |
                          +-------------------+
```

**İlişkili dosyalar:** `main.py`, `game/app.py`.

---

## 2. Kullanılan Teknolojiler — "Bunlar Ne, Niye Var?"

### 2.1. Python 3.10+

Proje tamamen Python ile yazılmıştır. Sık kullanılan syntax'lar:

| Syntax | Anlam | Örnek |
|---|---|---|
| `@dataclass` | Veri sınıfı — otomatik `__init__` üretir | `@dataclass class Position: x: float = 0.0` |
| `typing.List`, `Dict`, `Optional` | Tip ipuçları (runtime etkisi yok) | `def foo(x: Optional[int]) -> List[str]` |
| `@property` | Metodu attribute gibi çağırma | `@property def x(self): return self.state.position.x` |
| `isinstance(obj, Class)` | Tip kontrolü | `isinstance(e, Unit)` |
| `list comprehension` | Tek satırda liste üretimi | `[e for e in entities if e.is_alive()]` |
| `deque` | Çift taraflı kuyruk (queue) | `from collections import deque` |

### 2.2. Pygame 2.5+

**Pygame**, Python'da 2D oyun geliştirmek için kullanılan en yaygın kütüphanedir. SDL2 üzerine kuruludur.

Temel kavramlar:
- **Surface**: Bellekteki 2D piksel dizisi (ekran da bir Surface).
- **Rect**: Dikdörtgen geometri — çarpışma, konumlandırma için.
- **Event loop**: `pygame.event.get()` ile olayları (tıklama, tuş, kapatma) okursun.
- **Blit**: Bir Surface'ı başka Surface üzerine kopyalama (`screen.blit(image, rect)`).
- **Clock**: `pygame.time.Clock()` → `tick(FPS)` ile sabit kare hızı.

```python
import pygame
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill((0, 0, 0))
    pygame.display.flip()
    clock.tick(60)
```

### 2.3. Pillow (PIL)

Procedural sprite üretimi için kullanılır (`tools/generate_sprites.py`). `Image`, `ImageDraw` sınıfları ile PNG oluşturur.

### 2.4. pytest

Python ekosisteminin standart test framework'ü. `assert` ifadeleri ile çalışır.

```bash
pytest tests/ -v      # verbose modda çalıştır
pytest tests/test_combat.py -v   # tek dosya
```

### 2.5. dataclasses

Python 3.7+ ile gelen standart kütüphane. Basit veri taşıyıcı sınıflar için boilerplate azaltır.

```python
from dataclasses import dataclass

@dataclass
class UnitStats:
    hp: float = 100.0
    max_hp: float = 100.0
    attack_phys: float = 10.0
```

**İlişkili dosyalar:** `requirements.txt`, `game/models.py`.

---

## 3. Yüksek-Düzey Dizin Haritası

```
CloneEmpires/
├── .venv/                          # Python sanal ortam (pip install ile gelir)
├── assets/                         # Oyun görselleri (PNG)
│   ├── buildings/                  # Bina sprite'ları
│   ├── effects/                    # Ateş animasyonu
│   ├── terrain/                    # Zemin + kaynak node'ları
│   └── units/                      # Birim sprite'ları (idle, walk, attack)
├── game/                           # Ana oyun motoru
│   ├── app.py                      # Ana döngü (GameApp)
│   ├── renderer.py                 # İzometrik render & sprite cache
│   ├── camera.py                   # Kaydırma & zoom
│   ├── isometric.py                # Dünya ↔ Ekran dönüşümü
│   ├── grid.py                     # A* pathfinding, cell math
│   ├── world.py                    # Entity listesi, tile haritası, zone'lar
│   ├── constants.py                # Ekran, tile, renk, üretim sabitleri
│   ├── models.py                   # Dataclass'lar (Position, UnitStats, BuildingStats, EntityState)
│   ├── economy.py                  # Kaynak motoru
│   ├── production_queue.py         # Baraka üretim kuyruğu
│   ├── work_modes.py               # Köylü çalışma modları
│   ├── building_catalog.py         # Bina kataloğu & maliyetler
│   ├── construction_manager.py     # İnşaat yerleştirme
│   ├── combat.py                   # Hasar hesaplama
│   ├── battle_manager.py           # Savaş döngüsü, kule, projectile
│   ├── unit_stats.py               # Birim stat tablosu
│   ├── xp_system.py                # XP & seviye atlama
│   ├── ai_controller.py            # Düşman AI'sı
│   ├── ui.py                       # Bottom bar, market, butonlar
│   ├── selection.py                # Seçim yöneticisi
│   ├── save_load.py                # JSON save/load
│   ├── assets.py                   # Renk haritaları (fallback)
│   └── entities/                   # Varlık sınıfları
│       ├── base_entity.py          # Temel sınıf
│       ├── unit.py                 # Savaş birimi + StateMachine
│       ├── building.py             # Bina + köylü atama
│       ├── worker.py               # Köylü (Unit'ten türemiş)
│       ├── resource.py             # Kaynak node'u
│       └── projectile.py           # Homing ok/mermi
├── tests/                          # pytest testleri (85+)
│   ├── conftest.py                 # pytest fixtures
│   └── test_*.py                   # Her modül için testler
├── tools/
│   └── generate_sprites.py         # Procedural PNG üretici (Pillow)
├── saves/                          # Otomatik kayıtlar (.json)
├── main.py                         # Giriş noktası
├── requirements.txt                # Bağımlılıklar
├── pytest.ini                      # Test ayarları
└── README.md                       # Proje açıklaması
```

> **Not:** `__pycache__/`, `.pytest_cache/`, `.git/`, `saves/*.json` **elle düzenlenmez**. Bunlar sırasıyla bytecode cache, test cache, git repo ve oyun kayıtlarıdır.

---

## 4. Konfigürasyon Dosyaları

### 4.1. `requirements.txt`

```
pygame>=2.5.0
pytest>=7.0.0
```

Kaynak: `requirements.txt:1-2`.

- `pygame>=2.5.0` → Oyun motoru, pencere, grafik, ses, input.
- `pytest>=7.0.0` → Test çerçevesi. Production çalışması için gerekli değil, ama CI/CD olmadan kod güveni sağlamak için şart.

### 4.2. `pytest.ini`

```ini
[pytest]
addopts = -p no:launch_testing -p no:launch_ros
testpaths = tests
```

Kaynak: `pytest.ini:1-5`.

- `addopts = -p no:launch_testing -p no:launch_ros` → Sistem genelinde kurulu ROS (Robot Operating System) pytest eklentilerinin otomatik yüklenip testleri çökertmesini engeller.
- `testpaths = tests` → Test dosyalarının aranacağı klasör.

### 4.3. `.gitignore`

```
__pycache__/
*.py[cod]
.venv/
venv/
.vscode/
.idea/
.env
.env.local
game/__pycache__/
.pytest_cache/
.coverage
htmlcov/
saves/*
!saves/.gitkeep
Archive/
```

Kaynak: `.gitignore:1-65`.

- `saves/*` + `!saves/.gitkeep` → saves klasörü boş olarak repo'da tutulur ama içindeki .json kayıtları commit edilmez.
- `Archive/` → Eski plan/döküman arşivi.

---

## 5. Uygulama Açılışı

### 5.1. `main.py`

```python
from game.app import GameApp

if __name__ == "__main__":
    app = GameApp()
    app.run()
```

Kaynak: `main.py:1-5`.

Açıklama:
- **`if __name__ == "__main__"`** → Dosya doğrudan çalıştırıldığında bu blok çalışır; import edildiğinde çalışmaz.
- `GameApp()` → Tüm oyun alt sistemlerini başlatır.
- `app.run()` → Ana oyun döngüsünü başlatır.

### 5.2. `game/app.py` — GameApp Sınıfı

```python
class GameApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Social Empires Clone")
        self.clock = pygame.time.Clock()
        self.running = True

        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.world = World()
        self.economy = EconomyEngine()
        self.renderer = Renderer(self.screen, self.camera)
        self.ui = UIManager(self.economy)
        self.selection = SelectionManager()
        self.save_manager = SaveManager()
        self.ai = AIController(self.world)
        self.battle_manager = BattleManager(self.world)
        self.xp_system = XPSystem(self.ui)
        self.construction_manager = ConstructionManager(self.world, self.economy)
        self.ui.on_buy = self._enter_build_mode

        self._setup_world()
        ...
```

Kaynak: `game/app.py:24-51`.

**GameApp**, oyunun **orkestratörüdür**. Tüm alt sistemleri tek bir yerde örnekler ve döngüyü yönetir.

Sırayla şunları oluşturur:
1. `Camera` — ekran kaydırma & zoom.
2. `World` — harita, entity listesi, zone'lar.
3. `EconomyEngine` — kaynaklar, depolama, üretim hesapları.
4. `Renderer` — ekrana çizim.
5. `UIManager` — alt bar, market, butonlar.
6. `SelectionManager` — birim/bina seçimi.
7. `SaveManager` — kaydetme/yükleme.
8. `AIController` — düşman AI.
9. `BattleManager` — savaş & projectile & counter-attack.
10. `XPSystem` — deneyim puanı & seviye.
11. `ConstructionManager` — inşaat yerleştirme.

```python
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self._handle_events()
            self._update(dt)
            self._render()
            self._autosave(dt)
        pygame.quit()
```

Kaynak: `game/app.py:102-110`.

Klasik **game loop** yapısı:
1. **`dt`** (delta time): Bir önceki frame'den bu frame'e geçen süre (saniye cinsinden). Tüm hareket ve animasyonlar `dt` ile çarpılarak kare hızından bağımsız çalışır.
2. `_handle_events()` → Kullanıcı input'u (tıklama, tuş, kaydırma).
3. `_update(dt)` → Oyun mantığı (hareket, savaş, ekonomi, AI).
4. `_render()` → Ekrana çizim.
5. `_autosave(dt)` → 30 saniyede bir otomatik kayıt.

### 5.3. `_setup_world()` — Başlangıç durumu

```python
    def _setup_world(self):
        cx, cy = self.world.player_base_center
        townhall = Building("townhall", cx, cy)
        self.world.add_entity(townhall)
        townhall.production_queue = ProductionQueue(townhall, self.economy)

        from game.isometric import world_to_screen
        self.camera.x, self.camera.y = world_to_screen(cx, cy)

        self.world.add_entity(Unit("spearman", cx + 2, cy, level=1))
        self.world.add_entity(Unit("spearman", cx + 3, cy + 1, level=1))
        self.world.add_entity(Worker(cx + 1, cy + 2, level=1))
        self.world.add_entity(Worker(cx + 2, cy + 2, level=1))

        self._setup_resources(cx, cy)
        ...
```

Kaynak: `game/app.py:52-79`.

- Town Hall merkeze konur, üretim kuyruğu bağlanır.
- 2 mızraklı birim ve 2 köylü oyuncu üssüne yerleştirilir.
- 3 troll (bıçaklı, sopalı, okçu) haritanın köşelerine konur; `AIController`'a patrol noktası kaydedilir.

**İlişkili dosyalar:** `main.py`, `game/app.py`, `game/world.py`.

---

## 6. Oyun Motoru Çekirdeği

Bu bölümde izometrik projeksiyondan pathfinding'e kadar oyunun teknik altyapısı anlatılır.

### 6.1. `game/isometric.py` — Dünya ↔ Ekran Dönüşümü

```python
from game.constants import TILE_WIDTH, TILE_HEIGHT

def world_to_screen(wx, wy, offset_x=0, offset_y=0):
    sx = (wx - wy) * (TILE_WIDTH // 2) + offset_x
    sy = (wx + wy) * (TILE_HEIGHT // 2) + offset_y
    return sx, sy

def screen_to_world(sx, sy, offset_x=0, offset_y=0):
    adj_x = sx - offset_x
    adj_y = sy - offset_y
    wx = (adj_x / (TILE_WIDTH // 2) + adj_y / (TILE_HEIGHT // 2)) / 2
    wy = (adj_y / (TILE_HEIGHT // 2) - adj_x / (TILE_WIDTH // 2)) / 2
    return wx, wy
```

Kaynak: `game/isometric.py:4-15`.

Bu fonksiyonlar **izometrik projeksiyonun** matematiğini yapar:
- `world_to_screen`: Dünya koordinatlarını (grid hücreleri) ekran piksellerine çevirir.
- `screen_to_world`: Ters dönüşüm — tıklanan piksel hangi dünya hücresine denk geliyor?

TILE_WIDTH = 64, TILE_HEIGHT = 32 olduğunda:
- X dünyada sağa ilerlerken ekranda sağa-aşağı gider.
- Y dünyada yukarı ilerlerken ekranda sola-aşağı gider.

### 6.2. `game/camera.py` — Kamera & Zoom

```python
class Camera:
    def __init__(self, screen_width, screen_height):
        self.x = 0
        self.y = 0
        self.zoom = 1.0
        self.sw = screen_width
        self.sh = screen_height

    def pan(self, dx, dy):
        self.x += dx
        self.y += dy

    def change_zoom(self, delta, mouse_x, mouse_y):
        old_zoom = self.zoom
        self.zoom = max(MIN_ZOOM, min(MAX_ZOOM, self.zoom + delta))
        if self.zoom != old_zoom:
            factor = self.zoom / old_zoom
            self.x = mouse_x - (mouse_x - self.x) * factor
            self.y = mouse_y - (mouse_y - self.y) * factor

    def world_to_screen(self, wx, wy):
        from game.isometric import world_to_screen as w2s
        sx, sy = w2s(wx, wy)
        sx = (sx - self.x) * self.zoom + self.sw // 2
        sy = (sy - self.y) * self.zoom + self.sh // 2
        return sx, sy

    def screen_to_world(self, sx, sy):
        from game.isometric import screen_to_world as s2w
        adj_x = (sx - self.sw // 2) / self.zoom + self.x
        adj_y = (sy - self.sh // 2) / self.zoom + self.y
        return s2w(adj_x, adj_y)
```

Kaynak: `game/camera.py:1-35`.

- `pan(dx, dy)` → Orta tık sürükleme ile haritayı kaydırma.
- `change_zoom(delta, mouse_x, mouse_y)` → Fare imlecinin altındaki noktayı sabit tutarak zoom (zoom towards cursor).
- `world_to_screen` / `screen_to_world` → İzometrik dönüşüm + kamera offset + zoom kombinasyonu.

### 6.3. `game/grid.py` — Izgara Matematiği & A* Pathfinding

```python
"""Izgara (cell-decomposition) yardımcıları.

Kutsal kural: her karakter daima bir hücre merkezinde oturur ve hareket eden
karakter bir adımı başka bir hücrenin merkezinde sonlandırır.
"""

import math
import heapq

_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
_SQRT2 = math.sqrt(2)

def cell_of(x, y):
    return (int(round(x)), int(round(y)))

def cell_distance(a, b):
    return int(round(math.hypot(a[0] - b[0], a[1] - b[1])))

def in_range(a, b, rng):
    return cell_distance(a, b) <= rng

def find_path(start, goal, blocked, max_nodes=8000):
    if start == goal:
        return []
    open_heap = [(0.0, start)]
    came = {}
    g = {start: 0.0}
    nodes = 0
    while open_heap and nodes < max_nodes:
        _, cur = heapq.heappop(open_heap)
        if cur == goal:
            path = []
            while cur in came:
                path.append(cur)
                cur = came[cur]
            path.reverse()
            return path
        nodes += 1
        cx, cy = cur
        for dx, dy in _DIRS:
            ncell = (cx + dx, cy + dy)
            if blocked(ncell):
                continue
            if dx != 0 and dy != 0:
                if blocked((cx + dx, cy)) and blocked((cx, cy + dy)):
                    continue
                step = _SQRT2
            else:
                step = 1.0
            ng = g[cur] + step
            if ncell not in g or ng < g[ncell]:
                g[ncell] = ng
                came[ncell] = cur
                f = ng + math.hypot(ncell[0] - goal[0], ncell[1] - goal[1])
                heapq.heappush(open_heap, (f, ncell))
    return []
```

Kaynak: `game/grid.py:1-77`.

Açıklamalar:
- **`cell_of(x, y)`** → Sürekli dünya koordinatını en yakın hücre merkezine yuvarlar. Bu projenin **"kutsal kuralı"**: her birim her zaman bir hücre merkezindedir.
- **`cell_distance(a, b)`** → İki hücre arası öklid mesafesini yuvarlar (`round`). Menzil karşılaştırmaları bu değeri kullanır.
- **`find_path(start, goal, blocked)`** → A* algoritması (8 yönlü). `blocked` bir callable'dır; engelli hücre için `True` döner. Köşe kesme (corner cutting) engellenir.

### 6.4. `game/world.py` — Dünya, Zone'lar ve Entity Yönetimi

```python
class World:
    def __init__(self):
        self.width = MAP_WIDTH
        self.height = MAP_HEIGHT
        self.entities: List[BaseEntity] = []
        self.tiles = [["grass" for _ in range(self.height)] for _ in range(self.width)]
        self.player_base_center = (MAP_WIDTH // 2, MAP_HEIGHT // 2)
        self._setup_zones()

    def _setup_zones(self):
        from game.constants import SAFE_ZONE_CENTER, NEUTRAL_ZONE_CENTER
        cx, cy = self.player_base_center
        for x in range(self.width):
            for y in range(self.height):
                dx = abs(x - cx)
                dy = abs(y - cy)
                dist = max(dx, dy)
                if dist > NEUTRAL_ZONE_CENTER // 2:
                    self.tiles[x][y] = "danger"
                elif dist > SAFE_ZONE_CENTER // 2:
                    self.tiles[x][y] = "neutral"
                else:
                    self.tiles[x][y] = "safe"
```

Kaynak: `game/world.py:8-30`.

- **Zone sistemi**: Oyuncu üssü merkezden itibaren 3 halkalı:
  - **safe** (yeşil) → 20 hücre yarıçapına kadar. İnşaat serbest.
  - **neutral** (kahverengi) → 40 hücreye kadar.
  - **danger** (mavi) → Dışarısı; tehlikeli.
- `occupied_cells()` → Binalar, kaynaklar ve isteğe bağlı olarak birimlerin kapladığı hücreleri döner.
- `make_blocked()` → A* için engel fonksiyonu üretir.
- `nearest_free_cell()` → BFS ile verilen hücreye en yakın boş hücreyi bulur (üst üste binmeyi önler).

```python
    def _resolve_overlaps(self):
        seen = {}
        for e in self.entities:
            if not (hasattr(e, 'unit_type') and e.is_alive()):
                continue
            settled = getattr(e, '_settled', None)
            if settled is None or not settled() or getattr(e, 'path', None):
                continue
            c = cell_of(e.x, e.y)
            if c in seen:
                free = self.nearest_free_cell(c, ignore=e)
                if free is not None and free != c:
                    e.move_to(float(free[0]), float(free[1]))
            else:
                seen[c] = e
```

Kaynak: `game/world.py:115-131`.

- **Üst üste binme çözümü**: Aynı hücrede birden fazla birim varsa, fazlaları en yakın boş hücreye gönderilir.

### 6.5. `game/renderer.py` — Çizim Motoru

```python
class Renderer:
    def __init__(self, screen: pygame.Surface, camera: Camera):
        self.screen = screen
        self.camera = camera
        self._sprite_cache = {}
        self._scaled_cache = {}

    def _load_image(self, subdir: str, name: str):
        key = f"{subdir}/{name}"
        if key in self._sprite_cache:
            return self._sprite_cache[key]
        path = os.path.join(ASSETS_DIR, subdir, name)
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            self._sprite_cache[key] = img
            return img
        self._sprite_cache[key] = None
        return None
```

Kaynak: `game/renderer.py:14-31`.

- **Sprite cache**: Her PNG bir kere yüklenir; sonraki çağrılarda bellekten döner.
- **Scaled cache**: Zoom oranında ölçeklenmiş sprite'lar önbelleğe alınır (`round(zoom, 2)` anahtarı ile).

```python
    def draw_map(self, world):
        corners = {}
        default = (100, 100, 100)
        for x in range(world.width):
            for y in range(world.height):
                color = self.TILE_COLORS.get(world.tiles[x][y], default)
                pts = [
                    self._iso_corner(x, y, corners),
                    self._iso_corner(x + 1, y, corners),
                    self._iso_corner(x + 1, y + 1, corners),
                    self._iso_corner(x, y + 1, corners),
                ]
                pygame.draw.polygon(self.screen, color, pts)
```

Kaynak: `game/renderer.py:71-85`.

- **Elmas poligon çizimi**: Her tile, paylaşılan köşe noktalarından (`_iso_corner`) oluşan bir elmas olarak çizilir. Bu, komşu tile'lar arasında dikiş/boşluk olmamasını sağlar.

```python
    def draw_entities(self, entities: List[BaseEntity]):
        z = self.camera.zoom
        sorted_entities = sorted(entities, key=lambda e: e.y)
        for e in sorted_entities:
            if not e.is_alive():
                continue
            if getattr(e, 'is_inside_building', None):
                continue
            cx, cy = self._screen_center(e.x, e.y)
            ...
```

Kaynak: `game/renderer.py:157-184`.

- **Z-sıralama**: Entity'ler `e.y` değerine göre sıralanır (küçük y = arkada, büyük y = önde). Bu, izometrik derinlik yanılsaması için zorunludur.
- **Animasyon**: Birimlerin `unit_type_{action}_{frame}.png` sprite'ları `pygame.time.get_ticks()` ile zamanlanır.
- **Altın rozet**: `level >= 2` birimlerin üzerinde küçük altın daire çizilir.
- **Yangın**: Yıkık kulelerde `fire_{frame}.png` animasyonu.

**İlişkili dosyalar:** `game/isometric.py`, `game/camera.py`, `game/grid.py`, `game/world.py`, `game/renderer.py`.

---

## 7. Varlık Sistemi

Tüm oyun nesneleri `entities/` klasöründe tanımlanır. `BaseEntity` temel sınıftır; diğerleri bunu genişletir.

### 7.1. `game/entities/base_entity.py`

```python
from game.models import EntityState, Position

class BaseEntity:
    def __init__(self, name: str, x: float, y: float):
        self.name = name
        self.state = EntityState(position=Position(x, y))
        self.sprite = None
        self.width = 1.0
        self.height = 1.0
        self.world = None

    @property
    def x(self):
        return self.state.position.x

    @property
    def y(self):
        return self.state.position.y

    def is_alive(self):
        return self.state.alive
```

Kaynak: `game/entities/base_entity.py:1-21`.

- `@property` ile `x` ve `y` attribute gibi okunur ama aslında `state.position`'dan gelir.
- `world` → `World.add_entity()` tarafından set edilir; pathfinding ve çarpışma için kullanılır.

### 7.2. `game/entities/unit.py` — Savaş Birimi & State Machine

```python
class StateMachine:
    def __init__(self):
        self.current = "IDLE"
        self.valid_transitions = {
            "IDLE": ["MOVE", "ATTACK", "DEAD"],
            "MOVE": ["IDLE", "ATTACK", "DEAD"],
            "ATTACK": ["IDLE", "MOVE", "DEAD"],
            "DEAD": [],
        }

    def transition(self, new_state: str) -> bool:
        if new_state in self.valid_transitions.get(self.current, []):
            self.current = new_state
            return True
        return False
```

Kaynak: `game/entities/unit.py:5-19`.

**State Machine** (durum makinesi), birimin ne yaptığını kontrol eder. Geçersiz durum geçişlerini engeller (örneğin "DEAD"den "MOVE"a geçilemez).

```python
class Unit(BaseEntity):
    def __init__(self, unit_type: str, x: float, y: float, level: int = 1):
        super().__init__(unit_type, x, y)
        self.unit_type = unit_type
        self.level = level
        self.stats = get_unit_stats(unit_type, level)
        self.state_machine = StateMachine()
        self.attack_cooldown = 0.0
        self.target = None
        self.target_pos = None
        self.path = []
        self.is_player = True
        self.last_attacker = None
        self.manual_override = False
```

Kaynak: `game/entities/unit.py:21-34`.

- `stats` → `unit_stats.py` tablosundan çekilir.
- `path` → A* ile hesaplanan hücre listesi. Birim her frame bu listedeki bir sonraki hücreye doğru hareket eder.
- `manual_override` → Oyuncu sağ tık ile hareket ettirdiğinde `True` olur; bu durumda auto-acquire ve counter-attack devre dışı kalır.

```python
    def _advance_along_path(self, dt: float):
        if not self.path:
            return
        if self._settled() and self._next_cell_occupied():
            self.path = []
            self.target_pos = None
            return
        tx, ty = self.path[0]
        dx = tx - self.x
        dy = ty - self.y
        dist = (dx * dx + dy * dy) ** 0.5
        step = self.stats.move_speed * dt
        if dist <= step or dist < 1e-6:
            self.state.position.x = float(tx)
            self.state.position.y = float(ty)
            self.path.pop(0)
            self.target_pos = (float(self.path[0][0]), float(self.path[0][1])) if self.path else None
        else:
            self.state.position.x += dx / dist * step
            self.state.position.y += dy / dist * step
```

Kaynak: `game/entities/unit.py:127-151`.

**Kutsal kural**: Birim her zaman bir hücre merkezinde başlar ve her adımı başka bir hücre merkezinde sonlandırır. `dist <= step` kontrolü ile "bir adımı geçme" sağlanır; tam merkeze oturulur.

```python
    def _update_attack(self, dt: float):
        if not self.target or not self.target.is_alive():
            self.target = None
            self.path = []
            self.target_pos = None
            self.state_machine.transition("IDLE")
            return
        if not self._settled():
            if not self.path:
                self.path = [self.cell]
                self.target_pos = (float(self.cell[0]), float(self.cell[1]))
            self._advance_along_path(dt)
            return
        if self._in_attack_range(self.target):
            self.path = []
            self.target_pos = None
            return
        self._chase(dt)
```

Kaynak: `game/entities/unit.py:80-100`.

- Saldırı mantığı:
  1. Hedef ölüyse temizle.
  2. **Kutsal kural**: Saldırmadan önce mutlaka bir hücre merkezine otur.
  3. Menzildeyse dur (hasar `BattleManager`'da uygulanır).
  4. Menzil dışındaysa A* ile kovalamaya başla.

### 7.3. `game/entities/worker.py` — Köylü

```python
class Worker(Unit):
    def __init__(self, x: float, y: float, level: int = 1):
        super().__init__("worker", x, y, level)
        self.gather_timer = 0.0
        self.task = None
        self.task_target = None
        self.is_inside_building = None

    def assign_task(self, task_type: str, target):
        self.task = task_type
        self.task_target = target
        self.path = []
        if task_type in ("gather", "build"):
            self.state_machine.transition("MOVE")
```

Kaynak: `game/entities/worker.py:6-21`.

- `Worker`, `Unit`'ten türemiştir (inheritance). Bu yüzden hareket, saldırı ve durum makinesi davranışlarını miras alır.
- `is_inside_building` → Köylü bir kaynak binasına atandığında `True` olur; renderer bu durumda köylüyü **çizmez**.

```python
    def _do_gather(self, dt: float, world, economy):
        target = self.task_target
        if not target or not target.is_alive() or target.is_depleted():
            self.task = None
            self.path = []
            self.gather_timer = 0.0
            self.state_machine.transition("IDLE")
            return

        if not self._approach_cell(*cell_of(target.x, target.y), dt):
            return

        self.gather_timer += dt
        if self.gather_timer >= 2.0:
            self.gather_timer = 0.0
            harvested = target.harvest(10)
            if harvested > 0:
                economy.add_resources({target.resource_type: int(harvested)})
            if target.is_depleted():
                self.task = None
                ...
```

Kaynak: `game/entities/worker.py:70-95`.

- Toplama döngüsü: Hedefe komşu hücreye yürü → 2 saniye bekle → 10 kaynak topla → ekonomiye ekle.

### 7.4. `game/entities/building.py` — Bina

```python
class Building(BaseEntity):
    def __init__(self, building_type: str, x: float, y: float,
                 cost: Dict[str, int] = None, stats: BuildingStats = None):
        super().__init__(building_type, x, y)
        self.building_type = building_type
        self.cost = cost or {}
        self.stats = stats or BuildingStats()
        self.is_producing = False
        self.construction_progress = 0.0
        self.is_constructed = True
        self.build_time = 5.0
        self.assigned_workers: List = []
        self.worker_mode = None
        self.worker_active = False
```

Kaynak: `game/entities/building.py:14-33`.

- `is_constructed` → Yeni yerleştirilen binalar `False` başlar; zamanla otomatik inşa edilir.
- `assigned_workers` → Bu binaya atanmış köylü listesi.
- `worker_active` → Köylü üretim modu çalışıyor mu?

```python
    def assign_worker(self, worker) -> bool:
        from game.work_modes import MAX_WORKERS
        if self.worker_active:
            return False
        if self.resource_type() is None:
            return False
        if worker in self.assigned_workers or len(self.assigned_workers) >= MAX_WORKERS:
            return False
        self.assigned_workers.append(worker)
        worker.task = "working"
        worker.task_target = self
        worker.is_inside_building = self
        worker.state.position.x = self.x
        worker.state.position.y = self.y
        return True
```

Kaynak: `game/entities/building.py:66-81`.

- Köylü binaya atanır; pozisyonu bina merkezine çekilir (görsel olarak gizlenir).
- En fazla 4 köylü atanabilir (`MAX_WORKERS`).

### 7.5. `game/entities/resource.py` — Kaynak Node'u

```python
class ResourceNode(BaseEntity):
    def __init__(self, resource_type: str, x: float, y: float, initial_amount: float = 500):
        super().__init__(f"{resource_type}_node", x, y)
        self.resource_type = resource_type
        self.amount = initial_amount
        self.max_amount = initial_amount
        self.respawn_time = 30.0
        self.regrowth_timer = 0.0
        self.regrowth_phase = 2    # 0=stump, 1=sapling, 2=full

    def harvest(self, amount: float) -> float:
        actual = min(amount, self.amount)
        self.amount -= actual
        if self.amount <= 0:
            self.amount = 0
            self.regrowth_timer = self.respawn_time
            self.regrowth_phase = 0
        return actual
```

Kaynak: `game/entities/resource.py:1-24`.

- Kaynak tükendiğinde **ölmez**; 30 saniyede yeniden büyür.
- `regrowth_phase` → Renderer farklı sprite kullanır (stump → sapling → full).

### 7.6. `game/entities/projectile.py` — Homing Mermi

```python
class Projectile(BaseEntity):
    def __init__(self, x: float, y: float, target, speed: float = 10.0,
                 damage: float = 0, source=None):
        super().__init__("arrow", x, y)
        self.target = target
        self.speed = speed
        self.damage = damage
        self.source = source

    def update(self, dt: float):
        if not self.target or not self.target.is_alive():
            self.state.alive = False
            return
        dx = self.target.x - self.state.position.x
        dy = self.target.y - self.state.position.y
        dist = (dx * dx + dy * dy) ** 0.5
        if dist < 0.3:
            self.target.take_damage(self.damage)
            self.state.alive = False
            return
        ...
```

Kaynak: `game/entities/projectile.py:1-33`.

- **Homing**: Hedefe doğru her frame yönelir.
- Hedefe 0.3 birimden yakınsa hasar verir ve `alive = False` olur (bir sonraki frame temizlenir).

**İlişkili dosyalar:** `game/entities/base_entity.py`, `game/entities/unit.py`, `game/entities/worker.py`, `game/entities/building.py`, `game/entities/resource.py`, `game/entities/projectile.py`.

---

## 8. Ekonomi & Üretim

### 8.1. `game/economy.py` — Kaynak Motoru

```python
class EconomyEngine:
    def __init__(self):
        self.resources: Dict[str, int] = {r: 10000 for r in RESOURCES}
        self.storage_limit = INITIAL_STORAGE
        self.storage_level = 0

    @staticmethod
    def calculate_production(base_rate: float, duration: float, building_level: int = 1) -> float:
        level_bonus = 1.0 + (building_level - 1) * 0.2
        return base_rate * (duration ** PRODUCTION_EXPONENT) * level_bonus

    def add_resources(self, amounts: Dict[str, int]):
        for k, v in amounts.items():
            if k in self.resources:
                self.resources[k] += v
        self.cap_resources()

    def can_afford(self, cost: Dict[str, int]) -> bool:
        return all(self.resources.get(k, 0) >= v for k, v in cost.items())

    def spend(self, cost: Dict[str, int]) -> bool:
        if not self.can_afford(cost):
            return False
        for k, v in cost.items():
            self.resources[k] -= v
        return True
```

Kaynak: `game/economy.py:1-34`.

- **Üretim formülü**: `base_rate * (duration ^ 1.05) * level_bonus`. Zamanla üretim hızı artar (sürenin 1.05 kuvveti).
- `cap_resources()` → Depo limitini aşan kaynaklar kesilir.
- `can_afford` / `spend` → Maliyet kontrolü ve ödeme.

### 8.2. `game/production_queue.py` — Baraka Üretim Kuyruğu

```python
UNIT_COSTS = {
    "worker": {"food": 10, "wood": 5},
    "spearman": {"food": 15, "wood": 10},
    ...
}

UNIT_TRAIN_TIME = {
    "worker": 3.0,
    "spearman": 4.0,
    ...
}

MAX_QUEUE_SIZE = 5

class ProductionQueue:
    def __init__(self, building: Building, economy):
        self.building = building
        self.economy = economy
        self.queue: deque = deque()
        self.current_production: Optional[Dict] = None
        self.progress = 0.0
        self.max_progress = 0.0

    def enqueue(self, unit_type: str) -> bool:
        total_queued = len(self.queue) + (1 if self.current_production else 0)
        if total_queued >= MAX_QUEUE_SIZE:
            return False
        cost = UNIT_COSTS.get(unit_type, {})
        if not self.economy.can_afford(cost):
            return False
        if not self.economy.spend(cost):
            return False
        self.queue.append({"unit_type": unit_type, "train_time": UNIT_TRAIN_TIME.get(unit_type, 4.0)})
        return True

    def update(self, dt: float, world) -> Optional[Unit]:
        if self.current_production is None and self.queue:
            self.current_production = self.queue.popleft()
            self.progress = 0.0
            self.max_progress = self.current_production["train_time"]
        if self.current_production:
            self.progress += dt
            if self.progress >= self.max_progress:
                unit_type = self.current_production["unit_type"]
                new_unit = self._spawn_unit(unit_type, world)
                self.current_production = None
                self.progress = 0.0
                return new_unit
        return None
```

Kaynak: `game/production_queue.py:1-79`.

- **Queue (kuyruk)**: En fazla 5 birim sıraya alınabilir.
- **Ön ödeme**: `enqueue` anında maliyet düşülür; iptal edilirse `cancel_current()` ile iade edilir.
- **Spawn**: Bina etrafında rastgele bir boş hücreye birim oluşturulur.

### 8.3. `game/work_modes.py` — Köylü Çalışma Modları

```python
WORK_MODES = {
    "fast":     dict(label="Hızlı",   minutes=2,  base=10),
    "normal":   dict(label="Normal",  minutes=5,  base=30),
    "long":     dict(label="Uzun",    minutes=10, base=75),
    "marathon": dict(label="Maraton", minutes=30, base=250),
}

MODE_ORDER = ["fast", "normal", "long", "marathon"]

WORKER_MULTIPLIER = {1: 1.0, 2: 1.25, 3: 1.5, 4: 2.0}
MAX_WORKERS = 4

def gem_cost(mode_key: str) -> int:
    return WORK_MODES[mode_key]["minutes"] * 10

def resource_gain(mode_key: str, worker_count: int) -> int:
    base = WORK_MODES[mode_key]["base"]
    return math.ceil(base * worker_multiplier(worker_count))

def gem_reward(resource_amount: int) -> int:
    return math.ceil(resource_amount / 5)
```

Kaynak: `game/work_modes.py:1-45`.

- Köylüler kaynak binasına atanır, bir mod seçilir, **mücevher maliyeti** peşin ödenir.
- Süre dolunca: kaynak + `resource_amount / 5` kadar mücevher kazanılır.
- Çok köylü → çarpan: 2 köylü = ×1.25, 4 köylü = ×2.0.

**İlişkili dosyalar:** `game/economy.py`, `game/production_queue.py`, `game/work_modes.py`.

---

## 9. İnşaat & Geliştirme

### 9.1. `game/building_catalog.py` — Bina Kataloğu

```python
CATALOG = {
    "house": dict(category="Binalar", label="Ev", base="house",
                  cost={"wood": 30, "stone": 10}, level_req=1),
    "arrow_tower_1": dict(category="Kuleler", label="Ok Kulesi L1", base="tower",
                          cost={"wood": 80, "stone": 60}, level_req=1),
    "barracks_spear_1": dict(category="Barakalar", label="Mızrakçı Barakası L1",
                             base="barracks", trains=["spearman"],
                             cost={"wood": 100, "stone": 50}, level_req=1),
    "woodcutter": dict(category="Kaynaklar", label="Oduncu Evi", base="resource",
                       cost={"wood": 50, "stone": 20}, level_req=1),
    ...
}

TOWER_COMBAT = {
    "arrow_tower_1": dict(hp=300, attack=18, attack_range=6.0, attack_speed=1.0),
    "arrow_tower_2": dict(hp=500, attack=30, attack_range=7.0, attack_speed=1.2),
}
```

Kaynak: `game/building_catalog.py:12-55`.

- **Tek kaynak**: Tüm satın alınabilir binalar burada tanımlı.
- `base` alanı davranışı belirler: `"resource"`, `"barracks"`, `"tower"`, `"house"`.
- `get_upgrade(building_type)` → Aynı prefix'in `_2` versiyonunu bulur (`barracks_spear_1` → `barracks_spear_2`).

### 9.2. `game/construction_manager.py`

```python
class ConstructionManager:
    def __init__(self, world, economy):
        self.world = world
        self.economy = economy
        self.pending_constructions: List[Building] = []

    def can_build(self, building_type: str) -> bool:
        cost = BUILDING_COSTS.get(building_type, {})
        return self.economy.can_afford(cost)

    def place_building(self, building_type: str, x: float, y: float) -> Building:
        cost = BUILDING_COSTS.get(building_type, {})
        if not self.economy.spend(cost):
            return None
        building = Building.create_construction_site(building_type, x, y, cost=cost)
        self.world.add_entity(building)
        self.pending_constructions.append(building)
        return building
```

Kaynak: `game/construction_manager.py:10-31`.

- `place_building` → Maliyet düşülür, inşaat alanı (`is_constructed=False`) oluşturulur.
- `app.py` içinde `_update` döngüsünde `construction_progress` otomatik artar:
  ```python
  e.construction_progress += dt * (100.0 / e.build_time)
  if e.construction_progress >= 100:
      e.is_constructed = True
  ```

**İlişkili dosyalar:** `game/building_catalog.py`, `game/construction_manager.py`, `game/app.py:373-389`.

---

## 10. Savaş & Combat

### 10.1. `game/combat.py` — Hasar Motoru

```python
class CombatEngine:
    @staticmethod
    def calculate_damage(attacker: Unit, target: Unit,
                         damage_type: Literal["physical", "magic"]) -> float:
        if damage_type == "physical":
            raw = attacker.stats.attack_phys
            mitigation = target.stats.armor
        else:
            raw = attacker.stats.attack_magic
            mitigation = target.stats.magic_resist
        return max(0.0, raw - mitigation)

    @staticmethod
    def apply_damage(target: Unit, amount: float, attacker=None):
        target.take_damage(amount)
        if attacker is not None:
            target.last_attacker = attacker

    @staticmethod
    def in_range(attacker: Unit, target: Unit) -> bool:
        a = cell_of(attacker.x, attacker.y)
        b = cell_of(target.x, target.y)
        return cell_distance(a, b) <= attacker.stats.attack_range
```

Kaynak: `game/combat.py:1-29`.

- **Hasar formülü**: `raw - mitigation` (basit çıkarma). Negatif hasar olmaz (`max(0.0, ...)`).
- `last_attacker` → Counter-attack sistemi için kullanılır.

### 10.2. `game/battle_manager.py` — Savaş Döngüsü

```python
class BattleManager:
    def update(self, dt: float):
        self._update_towers(dt)
        self._update_projectiles(dt)
        self._auto_acquire()
        units = [e for e in self.world.entities if isinstance(e, Unit) and e.is_alive()]

        for attacker in units:
            if attacker.state_machine.current != "ATTACK":
                continue
            if attacker.attack_cooldown > 0:
                continue
            if not CombatEngine.in_range(attacker, attacker.target):
                continue
            damage_type = "magic" if attacker.stats.attack_magic > attacker.stats.attack_phys else "physical"
            damage = CombatEngine.calculate_damage(attacker, attacker.target, damage_type)
            CombatEngine.apply_damage(attacker.target, damage, attacker)
            attacker.perform_attack()

        for u in units:
            if getattr(u, 'manual_override', False):
                continue
            if u.last_attacker and u.last_attacker.is_alive():
                if u.state_machine.current in ("IDLE", "MOVE"):
                    u.halt_for_attack(u.last_attacker)
```

Kaynak: `game/battle_manager.py:14-51`.

Sırayla şunları yapar:
1. **_update_towers** → Oyuncu kuleleri menzildeki en yakın düşmana `Projectile` ateşler.
2. **_update_projectiles** → Ok/mermileri hareket ettirir.
3. **_auto_acquire** → Boşta veya hareket halindeki oyuncu birimleri menziline düşman girince otomatik saldırıya geçer.
4. **Hasar uygulama** → `ATTACK` durumundaki birimler menzilindeyse hasar verir ve cooldown sıfırlar.
5. **Counter-attack** → Hasar alan birim, saldıranı kovalamaya başlar (manuel hareket ettirilenler hariç).

### 10.3. `game/unit_stats.py` — Birim İstatistik Tablosu

```python
BASE_STATS = {
    "worker": dict(hp=50, attack_phys=3, armor=0, attack_range=1.0, vision_range=6.0, move_speed=3.0, attack_speed=1.0),
    "spearman": dict(hp=150, attack_phys=15, armor=4, attack_range=2.0, vision_range=8.0, move_speed=2.0, attack_speed=1.0),
    "swordsman": dict(hp=100, attack_phys=20, armor=6, attack_range=1.0, vision_range=7.0, move_speed=2.2, attack_speed=1.1),
    "rider": dict(hp=140, attack_phys=18, armor=4, attack_range=1.0, vision_range=7.0, move_speed=3.5, attack_speed=1.2),
    "archer": dict(hp=60, attack_phys=25, armor=1, attack_range=8.0, vision_range=14.0, move_speed=2.0, attack_speed=1.3),
    "mage": dict(hp=70, attack_phys=0, attack_magic=28, armor=0, magic_resist=5, attack_range=5.0, vision_range=10.0, move_speed=1.8, attack_speed=0.8),
    "troll_knife": dict(hp=50, attack_phys=10, armor=2, ...),
    ...
}

def level_multiplier(level: int) -> float:
    return 1.0 + (level - 1) * 1.0

def get_unit_stats(unit_type: str, level: int = 1) -> UnitStats:
    base = BASE_STATS.get(unit_type, _DEFAULT)
    mult = level_multiplier(level)
    stats = UnitStats()
    hp = base.get("hp", 100) * mult
    stats.hp = hp
    stats.max_hp = hp
    stats.attack_phys = base.get("attack_phys", 10) * mult
    ...
    return stats
```

Kaynak: `game/unit_stats.py:1-61`.

- Her birim tipinin kendine özgü istatistikleri vardır.
- **Level çarpanı**: L2 = 2x, L3 = 3x (hem can hem hasar).
- `is_ranged()` → `attack_range >= 3.0` ise menzilli sayılır.

### 10.4. `game/xp_system.py` — Deneyim & Seviye

```python
class XPSystem:
    def __init__(self, ui):
        self.ui = ui
        self.level = 1
        self.xp = 0
        self.max_xp = 100
        self.xp_multiplier = 1.0

    def add_xp(self, amount: int):
        self.xp += int(amount * self.xp_multiplier)
        while self.xp >= self.max_xp:
            self.xp -= self.max_xp
            self._level_up()
        self._sync_ui()

    def _level_up(self):
        self.level += 1
        self.max_xp = int(self.max_xp * 1.5)
        self.xp_multiplier += 0.05
```

Kaynak: `game/xp_system.py:30-51`.

- XP kaynakları: Düşman öldürme, bina inşaatı, birim eğitimi.
- Seviye atlayınca `max_xp` %50 artar; sonraki XP kazançları %5 artar.
- `_sync_ui()` → `UIManager`'a yansıtır.

**İlişkili dosyalar:** `game/combat.py`, `game/battle_manager.py`, `game/unit_stats.py`, `game/xp_system.py`.

---

## 11. AI & Otomasyon

### 11.1. `game/ai_controller.py` — Düşman AI

```python
class AIController:
    def __init__(self, world: World):
        self.world = world
        self.patrol_centers = []
        self.agro_radius = 8

    def register_patrol(self, x: float, y: float):
        self.patrol_centers.append((x, y))

    def update(self, dt: float):
        enemies = [e for e in self.world.entities
                   if isinstance(e, Unit) and not getattr(e, 'is_player', False) and e.is_alive()]
        players = [e for e in self.world.entities
                   if isinstance(e, Unit) and getattr(e, 'is_player', True) and e.is_alive()]
        towers = [e for e in self.world.entities
                  if isinstance(e, Building) and e.is_alive() and e.is_constructed
                  and e.is_tower() and not e.tower_disabled]
        players = players + towers

        for enemy in enemies:
            target = self._find_target(enemy, players)
            if target:
                enemy.attack_target(target)
            else:
                if enemy.state_machine.current == "ATTACK":
                    enemy.target = None
                    enemy.state_machine.transition("IDLE")
                self._patrol(enemy)

    def _find_target(self, enemy: Unit, players: List) -> Optional[Unit]:
        ecell = cell_of(enemy.x, enemy.y)
        closest = None
        min_dist = None
        for p in players:
            d = cell_distance(ecell, cell_of(p.x, p.y))
            if d <= self.agro_radius and (min_dist is None or d < min_dist):
                min_dist = d
                closest = p
        return closest

    def _patrol(self, unit: Unit):
        if unit.state_machine.current == "MOVE":
            return
        if random.random() < 0.01:
            cx, cy = cell_of(unit.x, unit.y)
            unit.move_to(cx + random.randint(-3, 3), cy + random.randint(-3, 3))
```

Kaynak: `game/ai_controller.py:1-58`.

- **Agro sistemi**: Düşmanlar 8 hücre yarıçapındaki oyuncu birimlerine veya kulelere saldırır.
- **Patrol**: Hedef yoksa rastgele yürür (%1 olasılık/frame).
- Kuleler de `players` listesine eklenir; AI kulelere saldırabilir.

**İlişkili dosyalar:** `game/ai_controller.py`.

---

## 12. UI Sistemi

### 12.1. `game/ui.py` — UIManager

```python
class Button:
    def __init__(self, rect: pygame.Rect, text: str, callback,
                 color=(60, 60, 60), hover_color=(90, 90, 90)):
        self.rect = rect
        self.text = text
        self.callback = callback
        self.color = color
        self.hover_color = hover_color
        self.hovered = False

    def handle_event(self, event: pygame.event.Event, offset=(0, 0)) -> bool:
        mx, my = pygame.mouse.get_pos()
        rx, ry = self.rect.x + offset[0], self.rect.y + offset[1]
        self.hovered = rx <= mx <= rx + self.rect.w and ry <= my <= ry + self.rect.h
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.hovered:
            if self.callback:
                self.callback()
            return True
        return False
```

Kaynak: `game/ui.py:17-42`.

- `Button` sınıfı: Pygame Rect + callback tabanlı basit buton.
- `offset` → Alt bardaki butonlar ekranın altına sabitlendiği için y offset gerekir.

```python
class UIManager:
    def __init__(self, economy: EconomyEngine):
        self.economy = economy
        self.king_name = "Kral Baran"
        self.townhall_level = 1
        self.xp = 0
        self.max_xp = 100
        self.buttons: List[Button] = []
        self.market_open = False
        self.on_buy = None
```

Kaynak: `game/ui.py:45-61`.

**UI katmanları**:
1. **Kaynak paneli** (sol üst): Kral adı, seviye, XP barı, 5 kaynak miktarı.
2. **Alt bar** (bottom): Seçili entity'nin bilgileri, butonlar, HP barları.
3. **Market** (orta): Kategori sekmeleri, bina kartları, maliyetler.

```python
    def draw_market(self, screen: pygame.Surface):
        # ... market paneli, sekmeler, kartlar
        for card_rect, buy_rect, bt, meta, cost, affordable in lay["cards"]:
            # ... kart çizimi
            bcolor = (40, 110, 40) if affordable else (70, 70, 70)
            pygame.draw.rect(screen, bcolor, buy_rect)
            buy_label = "Satın Al" if affordable else "Yetersiz"
            ...
```

Kaynak: `game/ui.py:117-181`.

- Market kartları: `building_catalog.py`'den dinamik üretilir.
- `affordable` → Hem kaynak hem seviye gereksinimi kontrol edilir.

### 12.2. `game/selection.py` — Seçim Yöneticisi

```python
class SelectionManager:
    def __init__(self):
        self.selected: List[BaseEntity] = []

    def select_single(self, entity: Optional[BaseEntity]):
        self.clear_selection()
        if entity:
            entity.state.selected = True
            self.selected.append(entity)

    def select_same_class(self, unit: Unit, all_units: List[Unit], radius: float = 10.0):
        same_type = [u for u in all_units
                     if u.unit_type == unit.unit_type and u.is_alive()
                     and ((u.x - unit.x) ** 2 + (u.y - unit.y) ** 2) ** 0.5 <= radius]
        self.select_multiple(same_type)

    def get_selected_units(self) -> List[Unit]:
        return [e for e in self.selected
                if isinstance(e, Unit) and not getattr(e, 'is_inside_building', None)]
```

Kaynak: `game/selection.py:1-40`.

- **Tek seçim**: Sol tık.
- **Aynı tipte tümünü seç**: Çift sol tık (`radius=10.0` içindeki aynı tipteki birimler).
- `get_selected_units()` → Köylüler binanın içindeyse seçime dahil edilmez.

**İlişkili dosyalar:** `game/ui.py`, `game/selection.py`.

---

## 13. Kaydetme & Yükleme

### 13.1. `game/save_load.py`

```python
class SaveManager:
    SAVE_DIR = "saves"

    def serialize(self, world: World, economy: EconomyEngine,
                  king_name: str, level: int, xp: int = 0) -> Dict[str, Any]:
        entities_data = []
        for e in world.entities:
            ed = {"name": e.name, "x": e.x, "y": e.y, "alive": e.is_alive()}
            if isinstance(e, Unit):
                ed["type"] = "unit"
                ed["unit_type"] = e.unit_type
                ed["level"] = e.level
                ed["hp"] = e.stats.hp
            elif isinstance(e, Building):
                ed["type"] = "building"
                ed["building_type"] = e.building_type
                ed["level"] = e.stats.level
            elif isinstance(e, ResourceNode):
                ed["type"] = "resource"
                ed["resource_type"] = e.resource_type
                ed["amount"] = e.amount
            entities_data.append(ed)

        return {
            "king_name": king_name,
            "townhall_level": level,
            "xp": xp,
            "resources": economy.resources,
            "storage_level": economy.storage_level,
            "entities": entities_data,
        }

    def deserialize(self, data: Dict[str, Any], world: World, economy: EconomyEngine):
        economy.resources.update(data.get("resources", {}))
        economy.storage_level = data.get("storage_level", 0)
        for ed in data.get("entities", []):
            etype = ed.get("type")
            if etype == "unit":
                u = Unit(ed["unit_type"], ed["x"], ed["y"], level=ed.get("level", 1))
                u.stats.hp = ed.get("hp", u.stats.max_hp)
                ...
```

Kaynak: `game/save_load.py:1-65`.

- **Format**: JSON. İnsan tarafından okunabilir, elle düzenlenebilir.
- `autosave.json` → Her 30 saniyede bir `app.py` içinde `_autosave()` tarafından yazılır.
- `deserialize` → Entity'leri tipine göre yeniden oluşturur; `isinstance` kontrolü ile doğru sınıfı seçer.

**İlişkili dosyalar:** `game/save_load.py`, `game/app.py:461-469`.

---

## 14. Test Kapsamı

### 14.1. `tests/conftest.py`

```python
import pytest

@pytest.fixture
def dummy_surface():
    import pygame
    pygame.init()
    return pygame.Surface((64, 32))
```

Kaynak: `tests/conftest.py:1-7`.

- `dummy_surface` → Renderer testlerinde kullanılan Pygame surface fixture'ı.

### 14.2. Test dosyaları özeti

| Dosya | Ne test ediyor? |
|---|---|
| `test_entities.py` | BaseEntity, ResourceNode, Building, Unit oluşturma, hasar, state machine |
| `test_grid_movement.py` | `cell_of`, `cell_distance`, A* pathfinding, üst üste binme, hareket, kutsal kural, köylü toplama |
| `test_combat.py` | Fiziksel/magik hasar hesabı, negatif hasar engeli |
| `test_economy.py` | `f(t)` üretim formülü, depo limiti |
| `test_building_interactions.py` | Town Hall butonları, sağ tık ile köylü atama, boş zemine hareket |
| `test_gather.py` | Köylü toplama + teslim, farklı kaynak türleri |
| `test_isometric.py` | Dünya↔ekran dönüşümü, round-trip doğruluk |
| `test_selection_hitbox.py` | Entity seçimi (merkez, uzak, önde/arkada, ölü entity) |
| `test_tower_combat.py` | Kule statları, ateş etme, menzil dışı, yıkık kule davranışı |
| `test_integration.py` | Hareket, saldırı, üretim kuyruğu, XP, inşaat, savaş (kapsamlı senaryolar) |
| `test_market.py` | Katalog kategorileri, maliyetler, legacy anahtarlar, seviye gereksinimleri |
| `test_save_load.py` | JSON serialize/deserialize döngüsü |
| `test_unit_stats.py` | Birim stat farklılıkları, menzillilik, seviye ölçekleme, mage magik hasarı |
| `test_world.py` | Dünya oluşturma, entity ekleme, menzil içi sorgu |
| `test_work_modes.py` | Çalışma modu formülleri, köylü atama, üretim döngüsü, iptal |

**İlişkili dosyalar:** `tests/` klasöründeki tüm dosyalar.

---

## 15. Asset Sistemi

### 15.1. `assets/` klasörü

Sprite'lar `assets/` altında kategorilere ayrılmıştır:
- `assets/buildings/` → Bina PNG'leri (townhall.png, barracks_spear_1.png, arrow_tower_2.png, ...)
- `assets/units/` → Birim PNG'leri (idle, walk_0/1, attack_0/1)
- `assets/terrain/` → Zemin (grass.png, dirt.png, water.png) + kaynak node'ları (wood_node.png, wood_node_stump.png, wood_node_sapling.png)
- `assets/effects/` → Ateş animasyonu (fire_0/1/2.png)

### 15.2. `tools/generate_sprites.py` — Procedural Üretici

```python
from PIL import Image, ImageDraw

def iso_box(draw, cx, cy, w, h, height, top_color, side_color, front_color):
    half_w, half_h = w // 2, h // 2
    draw.polygon([(cx, cy - half_h), (cx + half_w, cy), (cx, cy + half_h), (cx - half_w, cy)],
                 fill=top_color, outline=(0, 0, 0))
    draw.polygon([(cx, cy + half_h), (cx + half_w, cy), (cx + half_w, cy + height),
                  (cx, cy + half_h + height)], fill=side_color, outline=(0, 0, 0))
    draw.polygon([(cx, cy + half_h), (cx - half_w, cy), (cx - half_w, cy + height),
                  (cx, cy + half_h + height)], fill=front_color, outline=(0, 0, 0))

def generate_buildings():
    _draw_building("townhall", (160, 120, 70), ...)
    _draw_building("woodcutter", (60, 130, 60), ...)
    for cls, roof in barracks.items():
        for lvl in (1, 2):
            _draw_building(f"barracks_{cls}_{lvl}", roof, ...)
```

Kaynak: `tools/generate_sprites.py:38-118`.

- **Pillow** ile tamamen kodla çizilmiş sprite'lardır. Harici grafik programına gerek yoktur.
- `iso_box` fonksiyonu izometrik kutu çizer (üst + yan + ön yüz).
- Birimler: Gövde + silah + animasyon kareleri (yürüme: zıplama + bacaklar, saldırı: silah sallanışı).
- Kaynak aşamaları: `stump` (kök) → `sapling` (filiz) → `node` (tam).

Çalıştırma:
```bash
python tools/generate_sprites.py
```

**İlişkili dosyalar:** `tools/generate_sprites.py`, `assets/` altındaki tüm PNG'ler.

---

## 16. Tipik Geliştirici Akışları (Mini Tarifler)

### Tarif: Yeni birim ekleme (örnek: "giant")

1. `game/unit_stats.py` içinde `BASE_STATS`'a ekle:
   ```python
   "giant": dict(hp=300, attack_phys=40, armor=10, attack_range=1.5, vision_range=8.0,
                 move_speed=1.2, attack_speed=0.7),
   ```
2. `game/production_queue.py` içinde `UNIT_COSTS` ve `UNIT_TRAIN_TIME`'a ekle.
3. `game/xp_system.py` içinde `UNIT_TRAIN_XP`'ye ekle.
4. `tools/generate_sprites.py` içinde `generate_units()` listesine ekle:
   ```python
   ("giant", (120, 80, 60), "club"),
   ```
5. Sprite'ları yeniden üret: `python tools/generate_sprites.py`.
6. Test ekle: `tests/test_unit_stats.py` içinde `get_unit_stats("giant")` kontrolü.

### Tarif: Yeni bina ekleme (örnek: "mage_tower")

1. `game/building_catalog.py` içinde `CATALOG`'a ekle:
   ```python
   "mage_tower": dict(category="Kuleler", label="Büyü Kulesi", base="tower",
                      cost={"wood": 100, "stone": 80, "gem": 20}, level_req=1),
   ```
2. Aynı dosyada `TOWER_COMBAT`'a ekle:
   ```python
   "mage_tower": dict(hp=250, attack=25, attack_range=5.0, attack_speed=0.8),
   ```
3. `tools/generate_sprites.py` içinde `_draw_building` çağrısı ekle.
4. `game/construction_manager.py` otomatik olarak `CATALOG`'dan maliyeti çeker; dokunmaya gerek yok.
5. `game/xp_system.py` içinde `BUILDING_XP`'ye ekle.

### Tarif: Yeni kaynak türü ekleme (örnek: "iron")

1. `game/constants.py` içinde `RESOURCES` listesine `"iron"` ekle; `RESOURCE_LABELS`'a `"iron": "Demir"` ekle.
2. `game/entities/building.py` içinde `RESOURCE_MAP`'e ekle:
   ```python
   "iron_mine": "iron",
   ```
3. `game/building_catalog.py` içinde `"iron_mine"` ekle (`base="resource"`).
4. `tools/generate_sprites.py` içinde `generate_resources()` ve `generate_resource_phases()` fonksiyonlarına iron node çizimi ekle.
5. Sprite'ları yeniden üret.

### Tarif: Yeni çalışma modu ekleme

1. `game/work_modes.py` içinde `WORK_MODES`'a ekle:
   ```python
   "mega": dict(label="Mega", minutes=60, base=600),
   ```
2. `MODE_ORDER`'a `"mega"` ekle.
3. `WORKER_MULTIPLIER` zaten geneldir; değiştirmeye gerek yok.

### Tarif: Test yazma

```python
# tests/test_giant.py
def test_giant_has_high_hp():
    from game.unit_stats import get_unit_stats
    stats = get_unit_stats("giant")
    assert stats.hp >= 300
```

Çalıştır: `pytest tests/test_giant.py -v`.

---

## 17. Hızlı Syntax Kartı

### Python OOP (bu projede sık kullanılan)

| Syntax | Anlam |
|---|---|
| `class X(Y):` | `Y`'den türeme (inheritance) |
| `super().__init__(...)` | Üst sınıfın `__init__`'ini çağırma |
| `@property def x(self):` | Metodu attribute gibi çağırma (`obj.x`) |
| `@dataclass` | Veri sınıfı — otomatik init, repr, eq |
| `isinstance(obj, Class)` | Tip kontrolü |
| `getattr(obj, 'attr', default)` | Güvenli attribute okuma |
| `hasattr(obj, 'attr')` | Attribute var mı? |
| `list comprehension` | `[e for e in list if cond]` |
| `dict comprehension` | `{k: v for k, v in ...}` |
| `lambda x: x > 5` | Tek satırlık anonim fonksiyon |
| `functools.partial` veya `lambda` ile closure | Callback'lere argüman bağlama (`lambda u=ut: pq.enqueue(u)`) |

### Pygame (sık kullanılan)

| Syntax | Anlam |
|---|---|
| `pygame.init()` | Pygame'i başlat |
| `display.set_mode((w, h))` | Pencere oluştur |
| `Surface((w, h))` | Bellekte resim/çizim alanı |
| `blit(source, dest_rect)` | Resmi ekrana yapıştır |
| `draw.rect(surf, color, rect)` | Dikdörtgen çiz |
| `draw.polygon(surf, color, pts)` | Çokgen çiz (elmas zemin) |
| `draw.circle(surf, color, center, r)` | Daire çiz |
| `event.get()` | Olayları oku (tıklama, tuş, kapatma) |
| `mouse.get_pos()` | Fare pozisyonu |
| `time.Clock().tick(FPS)` | Kare hızını sınırla, dt döndür |
| `image.load(path).convert_alpha()` | PNG yükle (transparan) |
| `transform.scale(img, (w, h))` | Ölçeklendir |
| `font.render(text, True, color)` | Metin surface'ı üret |

### İzometrik Hesaplamalar

| İşlem | Formül |
|---|---|
| Dünya → Ekran | `sx = (wx - wy) * (TILE_WIDTH // 2)` |
| | `sy = (wx + wy) * (TILE_HEIGHT // 2)` |
| Ekran → Dünya | `wx = (sx/(TW/2) + sy/(TH/2)) / 2` |
| | `wy = (sy/(TH/2) - sx/(TW/2)) / 2` |
| Hücre merkezi | `cell_of(x, y) = (round(x), round(y))` |
| Menzil kontrolü | `round(euclid(cell_a, cell_b)) <= range` |

---

## 18. Sözlük ve Kısaltmalar

| Terim | Anlamı |
|---|---|
| **RTS** | Real-Time Strategy — Gerçek zamanlı strateji oyunu |
| **Isometric** | İzometrik projeksiyon — 2.5D görünüm, 45° açı |
| **Entity** | Oyun dünyasındaki herhangi bir nesne (birim, bina, kaynak) |
| **Sprite** | 2D oyun görseli (PNG) |
| **Tile** | Zemin parçası / ızgara hücresi |
| **Cell** | Grid üzerindeki bir kare; `(int, int)` koordinat |
| **A*** | A-Star pathfinding algoritması |
| **dt** | Delta time — Bir frame'in süresi (saniye) |
| **FPS** | Frame Per Second — Saniyedeki kare sayısı |
| **Blit** | Bir surface'ı başka surface üzerine kopyalama |
| **HP** | Health Points — Can puanı |
| **XP** | Experience Points — Deneyim puanı |
| **Agro** | Düşmanın oyuncuyu fark edip saldırması |
| **Homing** | Hedefi takip eden mermi/ok |
| **State Machine** | Durum makinesi — birimin davranış durumlarını yönetir |
| **Cooldown** | Tekrar kullanım için bekleme süresi |
| **MVP** | Minimum Viable Product — En temel çalışan sürüm |
| **Procedural** | Kodla otomatik üretilen (elle çizilmemiş) |

---

## 19. İleri Adımlar / Önerilen Egzersizler

1. **Yeni birim ekle**: `giant` veya `catapult` tipi oluştur. Stat tablosu, sprite üretimi, üretim kuyruğuna kayıt.
2. **Alan efekti (AoE) ekle**: Mage'in saldırısı hedef + komşu hücrelere hasar versin. `CombatEngine`'e `radius` parametresi ekleyerek başlayabilirsin.
3. **Ses sistemi**: `pygame.mixer` ile saldırı, inşaat, üretim tamamlanma sesleri ekle.
4. **Market satın alma**: Şu an market sadece inşaat moduna sokuyor. Maliyet düşme ve inşaat yerleştirme arasında gerçek "satın alma" akışı eklenebilir.
5. **Kayıt/yükleme UI'sı**: `save_load.py`'deki JSON'u oyun içi menüden kaydet/yükle yap.
6. **Çok oyunculu temel**: `socket` ile LAN üzerinden 2 oyuncu; `World`'de `is_player` flag'ı zaten hazır.
7. **Depo binası**: `EconomyEngine.upgrade_storage()` var ama UI'da buton yok. Depo binası inşaat edilip `storage_level` artırılabilir.
8. **Yol bulma iyileştirmesi**: `find_path`'e `max_nodes` yerine dinamik `max_nodes` (harita boyutuna göre) ekle.
9. **Animasyon frame hızı**: `ANIM_FRAME_MS` sabit; birim hızına göre dinamik yap.
10. **Köylü otomatik atama**: Boşta duran köylüler otomatik olarak en yakın kaynak binasına atanabilir.

> **Not:** Her egzersizden önce ilgili test dosyasına yeni testler yazmayı unutma. Test-driven yaklaşım bu projede çok işe yarar.

---

*Doküman sonu. Soruların olursa ilgili dosyayı ve satır aralığını belirterek sorabilirsin.*
