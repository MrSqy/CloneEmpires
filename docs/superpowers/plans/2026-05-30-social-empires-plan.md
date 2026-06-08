# Social Empires Tarzı Strateji/Builder Oyunu — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pygame tabanlı, isometrik, gerçek zamanlı strateji/builder oyunu MVP'si.

**Architecture:** Entity-Component benzeri bir yapı ile BaseEntity'den türeyen Unit/Building/ResourceNode sınıfları. Isometrik projeksiyon math'i ve kamera IoT Grid Simulator deneyiminden uyarlanacak. Gerçek zamanlı savaş ve f(t) ekonomisi ayrı motor modülleri olarak implemente edilecek.

**Tech Stack:** Python 3.10+, Pygame 2.x, pytest

---

## File Structure

```
social_empires/
├── requirements.txt
├── main.py
├── game/
│   ├── __init__.py
│   ├── constants.py
│   ├── isometric.py
│   ├── camera.py
│   ├── models.py
│   ├── world.py
│   ├── economy.py
│   ├── combat.py
│   ├── ai_controller.py
│   ├── renderer.py
│   ├── ui.py
│   ├── selection.py
│   ├── save_load.py
│   ├── app.py
│   └── entities/
│       ├── __init__.py
│       ├── base_entity.py
│       ├── resource.py
│       ├── building.py
│       └── unit.py
├── tests/
│   ├── __init__.py
│   ├── test_isometric.py
│   ├── test_economy.py
│   ├── test_combat.py
│   ├── test_entities.py
│   ├── test_world.py
│   └── test_save_load.py
└── assets/
    ├── terrain/
    ├── buildings/
    └── units/
```

---

### Task 1: Proje İskeleti

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `game/__init__.py`
- Create: `game/entities/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Klasör yapısını oluştur**

```bash
mkdir -p game/entities tests assets/terrain assets/buildings assets/units
```

- [ ] **Step 2: requirements.txt yaz**

```
pygame>=2.5.0
pytest>=7.0.0
```

- [ ] **Step 3: .gitignore yaz**

```
__pycache__/
*.pyc
*.pyo
.env
saves/
!saves/.gitkeep
```

- [ ] **Step 4: `tests/conftest.py` — Pygame mock/fixture hazırlığı**

```python
import pytest

@pytest.fixture
def dummy_surface():
    import pygame
    pygame.init()
    return pygame.Surface((64, 32))
```

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: project skeleton and dependencies"
```

---

### Task 2: Constants

**Files:**
- Create: `game/constants.py`
- Test: `tests/test_constants.py` (opsiyonel, sadece değerlerin varlığı)

- [ ] **Step 1: constants.py yaz**

```python
import pygame

# Ekran
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Isometrik Tile
TILE_WIDTH = 64
TILE_HEIGHT = 32

# Harita
MAP_WIDTH = 80
MAP_HEIGHT = 80

# Güvenlik Bölgeleri
SAFE_ZONE_CENTER = 20
NEUTRAL_ZONE_CENTER = 40

# Renkler
COLOR_GRASS = (34, 139, 34)
COLOR_DIRT = (139, 90, 43)
COLOR_WATER = (30, 144, 255)
COLOR_UI_BG = (30, 30, 30, 200)
COLOR_HP_GREEN = (0, 255, 0)
COLOR_HP_RED = (255, 0, 0)
COLOR_XP_BAR = (255, 215, 0)

# Kaynaklar
RESOURCES = ["wood", "stone", "food", "gold", "gem"]
RESOURCE_LABELS = {
    "wood": "Odun",
    "stone": "Taş",
    "food": "Gıda",
    "gold": "Altın",
    "gem": "Mücevher",
}
INITIAL_STORAGE = 500
STORAGE_PER_LEVEL = 500

# Üretim
PRODUCTION_EXPONENT = 1.05

# Zoom sınırları
MIN_ZOOM = 0.5
MAX_ZOOM = 3.0
```

- [ ] **Step 2: Commit**

```bash
git add game/constants.py
git commit -m "feat: add game constants"
```

---

### Task 3: Isometrik Math + Kamera

**Files:**
- Create: `game/isometric.py`
- Create: `game/camera.py`
- Test: `tests/test_isometric.py`

- [ ] **Step 1: Test yaz — isometric dönüşümler**

```python
# tests/test_isometric.py
from game.isometric import world_to_screen, screen_to_world
from game.constants import TILE_WIDTH, TILE_HEIGHT

def test_world_to_screen_origin():
    sx, sy = world_to_screen(0, 0)
    assert sx == 0
    assert sy == 0

def test_world_to_screen_roundtrip():
    wx, wy = 5, 3
    sx, sy = world_to_screen(wx, wy)
    rx, ry = screen_to_world(sx, sy)
    assert abs(rx - wx) < 0.01
    assert abs(ry - wy) < 0.01
```

- [ ] **Step 2: Test çalıştır — FAIL bekleniyor**

```bash
pytest tests/test_isometric.py -v
```
Expected: `ImportError` veya `ModuleNotFoundError`

- [ ] **Step 3: isometric.py implemente et**

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

- [ ] **Step 4: camera.py implemente et**

```python
from game.constants import MIN_ZOOM, MAX_ZOOM

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
        # Zoom merkezini mouse pozisyonuna göre ayarla
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

- [ ] **Step 5: Test çalıştır — PASS bekleniyor**

```bash
pytest tests/test_isometric.py -v
```

- [ ] **Step 6: Commit**

```bash
git add game/isometric.py game/camera.py tests/test_isometric.py
git commit -m "feat: add isometric projection and camera system"
```

---

### Task 4: Veri Modelleri

**Files:**
- Create: `game/models.py`

- [ ] **Step 1: models.py yaz — Entity, UnitStats, BuildingStats, ResourceNode**

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Position:
    x: float = 0.0
    y: float = 0.0

@dataclass
class UnitStats:
    hp: float = 100.0
    max_hp: float = 100.0
    attack_phys: float = 10.0
    attack_magic: float = 0.0
    armor: float = 2.0
    magic_resist: float = 0.0
    attack_range: float = 1.0  # tile cinsinden
    move_speed: float = 2.0    # tile/saniye
    attack_speed: float = 1.0  # saldırı/saniye

@dataclass
class BuildingStats:
    level: int = 1
    max_level: int = 3
    production_rate: float = 1.0
    storage_bonus: int = 0

@dataclass
class EntityState:
    position: Position = field(default_factory=Position)
    selected: bool = False
    alive: bool = True
```

- [ ] **Step 2: Commit**

```bash
git add game/models.py
git commit -m "feat: add data models for entities"
```

---

### Task 5: Base Entity + Kaynak Node'ları

**Files:**
- Create: `game/entities/base_entity.py`
- Create: `game/entities/resource.py`
- Test: `tests/test_entities.py`

- [ ] **Step 1: Test yaz**

```python
# tests/test_entities.py
from game.entities.base_entity import BaseEntity
from game.entities.resource import ResourceNode

def test_base_entity_creation():
    e = BaseEntity("test", 5, 5)
    assert e.name == "test"
    assert e.state.position.x == 5

def test_resource_node_amount():
    r = ResourceNode("wood", 10, 10, initial_amount=100)
    assert r.resource_type == "wood"
    assert r.amount == 100
    r.harvest(20)
    assert r.amount == 80
```

- [ ] **Step 2: Test çalıştır — FAIL**

```bash
pytest tests/test_entities.py -v
```

- [ ] **Step 3: base_entity.py implemente et**

```python
from game.models import EntityState, Position

class BaseEntity:
    def __init__(self, name: str, x: float, y: float):
        self.name = name
        self.state = EntityState(position=Position(x, y))
        self.sprite = None
        self.width = 1.0
        self.height = 1.0

    @property
    def x(self):
        return self.state.position.x

    @property
    def y(self):
        return self.state.position.y

    def is_alive(self):
        return self.state.alive
```

- [ ] **Step 4: resource.py implemente et**

```python
from game.entities.base_entity import BaseEntity

class ResourceNode(BaseEntity):
    def __init__(self, resource_type: str, x: float, y: float, initial_amount: float = 500):
        super().__init__(f"{resource_type}_node", x, y)
        self.resource_type = resource_type
        self.amount = initial_amount
        self.max_amount = initial_amount

    def harvest(self, amount: float) -> float:
        actual = min(amount, self.amount)
        self.amount -= actual
        if self.amount <= 0:
            self.state.alive = False
        return actual

    def is_depleted(self):
        return self.amount <= 0
```

- [ ] **Step 5: Test çalıştır — PASS**

```bash
pytest tests/test_entities.py -v
```

- [ ] **Step 6: Commit**

```bash
git add game/entities/base_entity.py game/entities/resource.py tests/test_entities.py
git commit -m "feat: add base entity and resource node classes"
```

---

### Task 6: Bina Sistemi

**Files:**
- Create: `game/entities/building.py`
- Test: `tests/test_entities.py` (genişlet)

- [ ] **Step 1: Test yaz — bina maliyet ve üretim**

```python
def test_building_cost():
    from game.entities.building import Building
    b = Building("barracks", 5, 5, cost={"wood": 100, "stone": 50})
    assert b.cost["wood"] == 100
    assert b.can_upgrade({"wood": 200, "stone": 100})
```

- [ ] **Step 2: Test çalıştır — FAIL**

```bash
pytest tests/test_entities.py::test_building_cost -v
```

- [ ] **Step 3: building.py implemente et**

```python
from typing import Dict
from game.entities.base_entity import BaseEntity
from game.models import BuildingStats

class Building(BaseEntity):
    def __init__(self, building_type: str, x: float, y: float,
                 cost: Dict[str, int] = None, stats: BuildingStats = None):
        super().__init__(building_type, x, y)
        self.building_type = building_type
        self.cost = cost or {}
        self.stats = stats or BuildingStats()
        self.production_timer = 0.0
        self.is_producing = False

    def can_build(self, resources: Dict[str, int]) -> bool:
        return all(resources.get(k, 0) >= v for k, v in self.cost.items())

    def start_production(self):
        self.is_producing = True
        self.production_timer = 0.0

    def stop_production(self):
        self.is_producing = False

    def update(self, dt: float) -> Dict[str, float]:
        if not self.is_producing:
            return {}
        self.production_timer += dt
        # Üretim economy.py'de hesaplanacak, burada sadece zaman tut
        return {}

    def can_upgrade(self, resources: Dict[str, int]) -> bool:
        if self.stats.level >= self.stats.max_level:
            return False
        # Basit: maliyet 2 katı
        upgrade_cost = {k: v * 2 for k, v in self.cost.items()}
        return all(resources.get(k, 0) >= v for k, v in upgrade_cost.items())
```

- [ ] **Step 4: Test çalıştır — PASS**

```bash
pytest tests/test_entities.py -v
```

- [ ] **Step 5: Commit**

```bash
git add game/entities/building.py tests/test_entities.py
git commit -m "feat: add building class with production and upgrade logic"
```

---

### Task 7: Birim Sistemi

**Files:**
- Create: `game/entities/unit.py`
- Test: `tests/test_entities.py` (genişlet)

- [ ] **Step 1: Test yaz — birim hasar ve state machine**

```python
def test_unit_take_damage():
    from game.entities.unit import Unit
    u = Unit("spearman", 0, 0)
    u.take_damage(20)
    assert u.stats.hp == 80

def test_unit_state_machine():
    from game.entities.unit import Unit
    u = Unit("archer", 0, 0)
    assert u.state_machine.current == "IDLE"
    u.state_machine.transition("MOVE")
    assert u.state_machine.current == "MOVE"
```

- [ ] **Step 2: Test çalıştır — FAIL**

```bash
pytest tests/test_entities.py::test_unit_take_damage -v
```

- [ ] **Step 3: unit.py implemente et**

```python
from game.entities.base_entity import BaseEntity
from game.models import UnitStats

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

class Unit(BaseEntity):
    def __init__(self, unit_type: str, x: float, y: float, level: int = 1):
        super().__init__(unit_type, x, y)
        self.unit_type = unit_type
        self.level = level
        self.stats = UnitStats()
        self.state_machine = StateMachine()
        self.attack_cooldown = 0.0
        self.target = None

    def take_damage(self, amount: float):
        self.stats.hp -= amount
        if self.stats.hp <= 0:
            self.stats.hp = 0
            self.state.alive = False
            self.state_machine.transition("DEAD")

    def is_ready_to_attack(self, dt: float) -> bool:
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
            return False
        return self.state_machine.current in ("IDLE", "ATTACK")

    def perform_attack(self):
        self.attack_cooldown = 1.0 / self.stats.attack_speed
```

- [ ] **Step 4: Test çalıştır — PASS**

```bash
pytest tests/test_entities.py -v
```

- [ ] **Step 5: Commit**

```bash
git add game/entities/unit.py tests/test_entities.py
git commit -m "feat: add unit class with stats and state machine"
```

---

### Task 8: Ekonomi Motoru

**Files:**
- Create: `game/economy.py`
- Test: `tests/test_economy.py`

- [ ] **Step 1: Test yaz — f(t) formülü ve depo limiti**

```python
# tests/test_economy.py
from game.economy import EconomyEngine

def test_production_formula():
    engine = EconomyEngine()
    result = engine.calculate_production(base_rate=1.0, duration=10.0)
    assert result > 10.0  # t^1.05 > t
    assert result < 13.0

def test_storage_limit():
    engine = EconomyEngine()
    engine.resources["wood"] = 600
    engine.storage_limit = 500
    engine.cap_resources()
    assert engine.resources["wood"] == 500
```

- [ ] **Step 2: Test çalıştır — FAIL**

```bash
pytest tests/test_economy.py -v
```

- [ ] **Step 3: economy.py implemente et**

```python
from typing import Dict
from game.constants import RESOURCES, INITIAL_STORAGE, PRODUCTION_EXPONENT, STORAGE_PER_LEVEL

class EconomyEngine:
    def __init__(self):
        self.resources: Dict[str, int] = {r: 100 for r in RESOURCES}  # Başlangıç kaynakları
        self.storage_limit = INITIAL_STORAGE
        self.storage_level = 0

    def calculate_production(self, base_rate: float, duration: float, building_level: int = 1) -> float:
        level_bonus = 1.0 + (building_level - 1) * 0.2
        return base_rate * (duration ** PRODUCTION_EXPONENT) * level_bonus

    def add_resources(self, amounts: Dict[str, int]):
        for k, v in amounts.items():
            if k in self.resources:
                self.resources[k] += v
        self.cap_resources()

    def cap_resources(self):
        for k in self.resources:
            self.resources[k] = min(self.resources[k], self.storage_limit)

    def can_afford(self, cost: Dict[str, int]) -> bool:
        return all(self.resources.get(k, 0) >= v for k, v in cost.items())

    def spend(self, cost: Dict[str, int]) -> bool:
        if not self.can_afford(cost):
            return False
        for k, v in cost.items():
            self.resources[k] -= v
        return True

    def upgrade_storage(self):
        self.storage_level += 1
        self.storage_limit = INITIAL_STORAGE + (self.storage_level * STORAGE_PER_LEVEL)
```

- [ ] **Step 4: Test çalıştır — PASS**

```bash
pytest tests/test_economy.py -v
```

- [ ] **Step 5: Commit**

```bash
git add game/economy.py tests/test_economy.py
git commit -m "feat: add economy engine with f(t) production formula"
```

---

### Task 9: Savaş Motoru

**Files:**
- Create: `game/combat.py`
- Test: `tests/test_combat.py`

- [ ] **Step 1: Test yaz — fiziksel ve büyü hasarı**

```python
# tests/test_combat.py
from game.combat import CombatEngine
from game.entities.unit import Unit

def test_physical_damage():
    attacker = Unit("spearman", 0, 0)
    attacker.stats.attack_phys = 20
    target = Unit("troll", 0, 0)
    target.stats.armor = 5
    dmg = CombatEngine.calculate_damage(attacker, target, "physical")
    assert dmg == 15

def test_magic_damage():
    attacker = Unit("mage", 0, 0)
    attacker.stats.attack_magic = 30
    target = Unit("troll", 0, 0)
    target.stats.magic_resist = 10
    dmg = CombatEngine.calculate_damage(attacker, target, "magic")
    assert dmg == 20

def test_damage_never_negative():
    attacker = Unit("weak", 0, 0)
    attacker.stats.attack_phys = 2
    target = Unit("tank", 0, 0)
    target.stats.armor = 10
    dmg = CombatEngine.calculate_damage(attacker, target, "physical")
    assert dmg == 0
```

- [ ] **Step 2: Test çalıştır — FAIL**

```bash
pytest tests/test_combat.py -v
```

- [ ] **Step 3: combat.py implemente et**

```python
from typing import Literal
from game.entities.unit import Unit

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
    def apply_damage(target: Unit, amount: float):
        target.take_damage(amount)

    @staticmethod
    def in_range(attacker: Unit, target: Unit) -> bool:
        dx = attacker.x - target.x
        dy = attacker.y - target.y
        distance = (dx ** 2 + dy ** 2) ** 0.5
        return distance <= attacker.stats.attack_range
```

- [ ] **Step 4: Test çalıştır — PASS**

```bash
pytest tests/test_combat.py -v
```

- [ ] **Step 5: Commit**

```bash
git add game/combat.py tests/test_combat.py
git commit -m "feat: add combat engine with damage calculation"
```

---

### Task 10: Dünya ve Harita

**Files:**
- Create: `game/world.py`
- Test: `tests/test_world.py`

- [ ] **Step 1: Test yaz — entity ekleme ve harita tile erişimi**

```python
# tests/test_world.py
from game.world import World
from game.entities.unit import Unit
from game.entities.building import Building

def test_world_creation():
    w = World()
    assert w.width == 80
    assert w.height == 80

def test_add_entity():
    w = World()
    u = Unit("spearman", 10, 10)
    w.add_entity(u)
    assert len(w.entities) == 1

def test_get_entities_in_range():
    w = World()
    w.add_entity(Unit("a", 10, 10))
    w.add_entity(Unit("b", 12, 10))
    result = w.get_entities_in_range(10, 10, 3)
    assert len(result) == 2
```

- [ ] **Step 2: Test çalıştır — FAIL**

```bash
pytest tests/test_world.py -v
```

- [ ] **Step 3: world.py implemente et**

```python
from typing import List, Optional
from game.constants import MAP_WIDTH, MAP_HEIGHT
from game.entities.base_entity import BaseEntity

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

    def add_entity(self, entity: BaseEntity):
        self.entities.append(entity)

    def remove_entity(self, entity: BaseEntity):
        if entity in self.entities:
            self.entities.remove(entity)

    def get_entities_in_range(self, x: float, y: float, radius: float) -> List[BaseEntity]:
        result = []
        for e in self.entities:
            if not e.is_alive():
                continue
            dx = e.x - x
            dy = e.y - y
            if (dx ** 2 + dy ** 2) ** 0.5 <= radius:
                result.append(e)
        return result

    def get_entities_by_type(self, entity_type: str) -> List[BaseEntity]:
        return [e for e in self.entities if e.name.startswith(entity_type) and e.is_alive()]

    def update(self, dt: float):
        for e in self.entities:
            if hasattr(e, 'update'):
                e.update(dt)
        # Ölü entity'leri temizle
        self.entities = [e for e in self.entities if e.is_alive()]
```

- [ ] **Step 4: Test çalıştır — PASS**

```bash
pytest tests/test_world.py -v
```

- [ ] **Step 5: Commit**

```bash
git add game/world.py tests/test_world.py
git commit -m "feat: add world with zones and entity management"
```

---

### Task 11: AI Kontrolcü

**Files:**
- Create: `game/ai_controller.py`

- [ ] **Step 1: ai_controller.py implemente et**

```python
import random
from typing import List, Optional
from game.entities.unit import Unit
from game.world import World

class AIController:
    def __init__(self, world: World):
        self.world = world
        self.patrol_centers = []
        self.agro_radius = 8.0
        self.attack_radius = 1.5

    def register_patrol(self, x: float, y: float):
        self.patrol_centers.append((x, y))

    def update(self, dt: float):
        enemies = [e for e in self.world.entities
                   if isinstance(e, Unit) and not getattr(e, 'is_player', False) and e.is_alive()]
        players = [e for e in self.world.entities
                   if isinstance(e, Unit) and getattr(e, 'is_player', True) and e.is_alive()]

        for enemy in enemies:
            if enemy.state_machine.current == "DEAD":
                continue
            target = self._find_target(enemy, players)
            if target:
                if self._in_attack_range(enemy, target):
                    enemy.state_machine.transition("ATTACK")
                    enemy.target = target
                else:
                    enemy.state_machine.transition("MOVE")
                    # Basit hareket: hedefe doğru
                    self._move_toward(enemy, target, dt)
            else:
                enemy.state_machine.transition("IDLE")
                self._patrol(enemy, dt)

    def _find_target(self, enemy: Unit, players: List[Unit]) -> Optional[Unit]:
        closest = None
        min_dist = self.agro_radius
        for p in players:
            d = ((enemy.x - p.x) ** 2 + (enemy.y - p.y) ** 2) ** 0.5
            if d < min_dist:
                min_dist = d
                closest = p
        return closest

    def _in_attack_range(self, attacker: Unit, target: Unit) -> bool:
        d = ((attacker.x - target.x) ** 2 + (attacker.y - target.y) ** 2) ** 0.5
        return d <= attacker.stats.attack_range

    def _move_toward(self, unit: Unit, target: Unit, dt: float):
        dx = target.x - unit.x
        dy = target.y - unit.y
        dist = (dx ** 2 + dy ** 2) ** 0.5
        if dist > 0:
            move = unit.stats.move_speed * dt
            unit.state.position.x += (dx / dist) * min(move, dist)
            unit.state.position.y += (dy / dist) * min(move, dist)

    def _patrol(self, unit: Unit, dt: float):
        # Basit patrol: rastgele küçük hareketler
        if random.random() < 0.01:
            unit.state.position.x += random.uniform(-0.5, 0.5)
            unit.state.position.y += random.uniform(-0.5, 0.5)
```

- [ ] **Step 2: Commit**

```bash
git add game/ai_controller.py
git commit -m "feat: add enemy AI with patrol and agro logic"
```

---

### Task 12: Renderer

**Files:**
- Create: `game/renderer.py`

- [ ] **Step 1: renderer.py implemente et**

```python
import pygame
from typing import List
from game.camera import Camera
from game.entities.base_entity import BaseEntity
from game.constants import TILE_WIDTH, TILE_HEIGHT, COLOR_GRASS, COLOR_DIRT, COLOR_WATER

class Renderer:
    def __init__(self, screen: pygame.Surface, camera: Camera):
        self.screen = screen
        self.camera = camera

    def draw_tile(self, sx: float, sy: float, color):
        points = [
            (sx, sy + TILE_HEIGHT // 2),
            (sx + TILE_WIDTH // 2, sy),
            (sx + TILE_WIDTH, sy + TILE_HEIGHT // 2),
            (sx + TILE_WIDTH // 2, sy + TILE_HEIGHT),
        ]
        pygame.draw.polygon(self.screen, color, points)
        pygame.draw.polygon(self.screen, (0, 0, 0), points, 1)

    def draw_map(self, world):
        for x in range(world.width):
            for y in range(world.height):
                sx, sy = self.camera.world_to_screen(x, y)
                tile = world.tiles[x][y]
                if tile == "safe":
                    color = COLOR_GRASS
                elif tile == "neutral":
                    color = COLOR_DIRT
                else:
                    color = COLOR_WATER
                self.draw_tile(sx, sy, color)

    def draw_entities(self, entities: List[BaseEntity]):
        # Depth sorting: Y koordinatına göre sırala
        sorted_entities = sorted(entities, key=lambda e: e.y)
        for e in sorted_entities:
            if not e.is_alive():
                continue
            sx, sy = self.camera.world_to_screen(e.x, e.y)
            # Placeholder: renkli kare
            rect = pygame.Rect(sx - 16, sy - 16, 32, 32)
            color = (200, 200, 200)
            if hasattr(e, 'unit_type'):
                color = (0, 100, 255) if getattr(e, 'is_player', True) else (255, 0, 0)
            elif hasattr(e, 'building_type'):
                color = (139, 69, 19)
            pygame.draw.rect(self.screen, color, rect)
            if e.state.selected:
                pygame.draw.rect(self.screen, (255, 255, 0), rect, 2)

    def draw_hp_bar(self, entity: BaseEntity):
        if not hasattr(entity, 'stats'):
            return
        sx, sy = self.camera.world_to_screen(entity.x, entity.y)
        hp = entity.stats.hp
        max_hp = entity.stats.max_hp
        ratio = hp / max_hp if max_hp > 0 else 0
        bar_w = 32
        bar_h = 4
        pygame.draw.rect(self.screen, (255, 0, 0), (sx - 16, sy - 24, bar_w, bar_h))
        pygame.draw.rect(self.screen, (0, 255, 0), (sx - 16, sy - 24, int(bar_w * ratio), bar_h))
```

- [ ] **Step 2: Commit**

```bash
git add game/renderer.py
git commit -m "feat: add isometric renderer with depth sorting"
```

---

### Task 13: UI ve Seçim

**Files:**
- Create: `game/ui.py`
- Create: `game/selection.py`

- [ ] **Step 1: selection.py implemente et**

```python
from typing import List, Optional, Tuple
from game.entities.base_entity import BaseEntity
from game.entities.unit import Unit

class SelectionManager:
    def __init__(self):
        self.selected: List[BaseEntity] = []
        self.select_box_start: Optional[Tuple[int, int]] = None
        self.select_box_end: Optional[Tuple[int, int]] = None

    def select_single(self, entity: Optional[BaseEntity]):
        self.clear_selection()
        if entity:
            entity.state.selected = True
            self.selected.append(entity)

    def select_multiple(self, entities: List[BaseEntity]):
        self.clear_selection()
        for e in entities:
            e.state.selected = True
            self.selected.append(e)

    def select_same_class(self, unit: Unit, all_units: List[Unit], radius: float = 10.0):
        """Çift tıklama: aynı tipteki tüm birimleri seç"""
        same_type = [u for u in all_units
                     if u.unit_type == unit.unit_type and u.is_alive()
                     and ((u.x - unit.x) ** 2 + (u.y - unit.y) ** 2) ** 0.5 <= radius]
        self.select_multiple(same_type)

    def clear_selection(self):
        for e in self.selected:
            e.state.selected = False
        self.selected.clear()

    def get_selected_units(self) -> List[Unit]:
        return [e for e in self.selected if isinstance(e, Unit)]
```

- [ ] **Step 2: ui.py implemente et**

```python
import pygame
from typing import List, Dict
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_UI_BG, COLOR_XP_BAR,
    COLOR_HP_GREEN, COLOR_HP_RED, RESOURCES, RESOURCE_LABELS
)
from game.economy import EconomyEngine
from game.entities.unit import Unit
from game.entities.building import Building

class UIManager:
    def __init__(self, economy: EconomyEngine):
        self.economy = economy
        self.font = pygame.font.SysFont("arial", 16)
        self.large_font = pygame.font.SysFont("arial", 20)
        self.king_name = "Kral Baran"
        self.townhall_level = 1
        self.xp = 0
        self.max_xp = 100

    def draw(self, screen: pygame.Surface, selected_entities: List):
        self.draw_resource_panel(screen)
        self.draw_bottom_bar(screen, selected_entities)

    def draw_resource_panel(self, screen: pygame.Surface):
        panel_w = 220
        panel_h = 160
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill(COLOR_UI_BG)

        # Kral adı
        name_surf = self.large_font.render(self.king_name, True, (255, 255, 255))
        panel.blit(name_surf, (10, 5))

        # XP çubuğu
        pygame.draw.rect(panel, (50, 50, 50), (10, 30, 200, 14))
        xp_ratio = self.xp / self.max_xp if self.max_xp > 0 else 0
        pygame.draw.rect(panel, COLOR_XP_BAR, (10, 30, int(200 * xp_ratio), 14))
        level_text = self.font.render(f"Seviye {self.townhall_level}", True, (255, 255, 255))
        panel.blit(level_text, (10, 48))

        # Kaynaklar
        resource_rows = [
            [("wood", "Odun"), ("food", "Gıda")],
            [("stone", "Taş"), ("gold", "Altın")],
            [("gem", "Mücevher"),],
        ]
        y_offset = 68
        for row in resource_rows:
            x_offset = 10
            for res_key, res_label in row:
                amount = self.economy.resources.get(res_key, 0)
                text = self.font.render(f"{res_label}: {amount}", True, (255, 255, 255))
                panel.blit(text, (x_offset, y_offset))
                x_offset += 100
            y_offset += 22

        screen.blit(panel, (10, 10))

    def draw_bottom_bar(self, screen: pygame.Surface, selected: List):
        if not selected:
            return
        bar_h = 100
        bar_y = SCREEN_HEIGHT - bar_h
        bar = pygame.Surface((SCREEN_WIDTH, bar_h), pygame.SRCALPHA)
        bar.fill((20, 20, 20, 220))

        if len(selected) == 1:
            entity = selected[0]
            if isinstance(entity, Unit):
                self._draw_unit_info(bar, entity, 10, 10)
            elif isinstance(entity, Building):
                self._draw_building_info(bar, entity, 10, 10)
        elif len(selected) > 1 and all(isinstance(e, Unit) for e in selected):
            # Çoklu asker: portre + can çubuğu
            x = 10
            for unit in selected:
                if not unit.is_alive():
                    continue
                pygame.draw.rect(bar, (100, 100, 100), (x, 10, 50, 50))
                hp_ratio = unit.stats.hp / unit.stats.max_hp if unit.stats.max_hp > 0 else 0
                color = COLOR_HP_GREEN if hp_ratio > 0.5 else COLOR_HP_RED
                pygame.draw.rect(bar, color, (x, 64, 50, 6))
                x += 60

        screen.blit(bar, (0, bar_y))

    def _draw_unit_info(self, surface, unit: Unit, x, y):
        texts = [
            f"Tip: {unit.unit_type} (Seviye {unit.level})",
            f"Can: {unit.stats.hp:.0f}/{unit.stats.max_hp:.0f}",
            f"Fiziksel Hasar: {unit.stats.attack_phys}",
            f"Büyü Hasarı: {unit.stats.attack_magic}",
            f"Zırh: {unit.stats.armor} | Büyü Direnci: {unit.stats.magic_resist}",
            f"Hız: {unit.stats.move_speed} | Saldırı Hızı: {unit.stats.attack_speed}",
            f"Menzil: {unit.stats.attack_range}",
        ]
        for i, text in enumerate(texts):
            surf = self.font.render(text, True, (255, 255, 255))
            surface.blit(surf, (x, y + i * 18))

    def _draw_building_info(self, surface, building: Building, x, y):
        text = f"{building.building_type} (Seviye {building.stats.level})"
        surf = self.font.render(text, True, (255, 255, 255))
        surface.blit(surf, (x, y))
        if building.is_producing:
            prod = self.font.render("Üretim devam ediyor...", True, (0, 255, 0))
            surface.blit(prod, (x, y + 20))
```

- [ ] **Step 3: Commit**

```bash
git add game/ui.py game/selection.py
git commit -m "feat: add UI manager and selection system"
```

---

### Task 14: Save / Load

**Files:**
- Create: `game/save_load.py`
- Test: `tests/test_save_load.py`

- [ ] **Step 1: Test yaz**

```python
# tests/test_save_load.py
import json
from game.save_load import SaveManager
from game.world import World
from game.economy import EconomyEngine
from game.entities.unit import Unit

def test_save_and_load():
    world = World()
    economy = EconomyEngine()
    world.add_entity(Unit("spearman", 10, 10))
    economy.resources["wood"] = 999

    manager = SaveManager()
    data = manager.serialize(world, economy, king_name="Test", level=2)
    assert data["king_name"] == "Test"
    assert data["townhall_level"] == 2
    assert len(data["entities"]) == 1

    world2 = World()
    economy2 = EconomyEngine()
    manager.deserialize(data, world2, economy2)
    assert economy2.resources["wood"] == 999
    assert len(world2.entities) == 1
```

- [ ] **Step 2: Test çalıştır — FAIL**

```bash
pytest tests/test_save_load.py -v
```

- [ ] **Step 3: save_load.py implemente et**

```python
import json
import os
from typing import Dict, Any
from game.world import World
from game.economy import EconomyEngine
from game.entities.unit import Unit
from game.entities.building import Building
from game.entities.resource import ResourceNode

class SaveManager:
    SAVE_DIR = "saves"

    def __init__(self):
        os.makedirs(self.SAVE_DIR, exist_ok=True)

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
        economy.storage_limit = economy.storage_limit  # Recalculate

        for ed in data.get("entities", []):
            etype = ed.get("type")
            if etype == "unit":
                u = Unit(ed["unit_type"], ed["x"], ed["y"], level=ed.get("level", 1))
                u.stats.hp = ed.get("hp", u.stats.max_hp)
                if not ed.get("alive", True):
                    u.state.alive = False
                world.add_entity(u)
            elif etype == "building":
                b = Building(ed["building_type"], ed["x"], ed["y"])
                b.stats.level = ed.get("level", 1)
                world.add_entity(b)
            elif etype == "resource":
                r = ResourceNode(ed["resource_type"], ed["x"], ed["y"], ed.get("amount", 100))
                world.add_entity(r)

    def save_to_file(self, filename: str, data: Dict[str, Any]):
        path = os.path.join(self.SAVE_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_from_file(self, filename: str) -> Dict[str, Any]:
        path = os.path.join(self.SAVE_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
```

- [ ] **Step 4: Test çalıştır — PASS**

```bash
pytest tests/test_save_load.py -v
```

- [ ] **Step 5: Commit**

```bash
git add game/save_load.py tests/test_save_load.py
git commit -m "feat: add save/load system with JSON serialization"
```

---

### Task 15: Ana Oyun Döngüsü (App)

**Files:**
- Create: `game/app.py`
- Create: `main.py`

- [ ] **Step 1: app.py implemente et**

```python
import pygame
import sys
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from game.camera import Camera
from game.world import World
from game.economy import EconomyEngine
from game.renderer import Renderer
from game.ui import UIManager
from game.selection import SelectionManager
from game.save_load import SaveManager
from game.entities.unit import Unit
from game.entities.building import Building
from game.entities.resource import ResourceNode
from game.ai_controller import AIController

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

        self._setup_world()
        self.autosave_timer = 0.0

    def _setup_world(self):
        # Town Hall
        cx, cy = self.world.player_base_center
        self.world.add_entity(Building("townhall", cx, cy))
        # Başlangıç birimleri
        self.world.add_entity(Unit("spearman", cx + 2, cy, level=1))
        self.world.add_entity(Unit("spearman", cx + 3, cy + 1, level=1))
        # Kaynak node'ları
        for i in range(5):
            self.world.add_entity(ResourceNode("wood", cx - 5 - i, cy - 3, 200))
        # Düşman kampları (harita kenarları)
        self.world.add_entity(Unit("troll_knife", 5, 5))
        self.world.add_entity(Unit("troll_club", 75, 75))
        self.world.add_entity(Unit("troll_archer", 75, 5))
        for e in self.world.entities:
            if isinstance(e, Unit) and "troll" in e.unit_type:
                e.is_player = False
                self.ai.register_patrol(e.x, e.y)

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self._handle_events()
            self._update(dt)
            self._render()
            self._autosave(dt)
        pygame.quit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.selection.clear_selection()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Sol tık
                    self._handle_left_click(event.pos)
                elif event.button == 3:  # Sağ tık
                    self._handle_right_click(event.pos)
                elif event.button == 4:  # Wheel up
                    self.camera.change_zoom(0.1, event.pos[0], event.pos[1])
                elif event.button == 5:  # Wheel down
                    self.camera.change_zoom(-0.1, event.pos[0], event.pos[1])
            elif event.type == pygame.MOUSEMOTION:
                if event.buttons[1]:  # Orta tuş sürükle
                    self.camera.pan(-event.rel[0] / self.camera.zoom,
                                    -event.rel[1] / self.camera.zoom)

    def _handle_left_click(self, pos):
        wx, wy = self.camera.screen_to_world(pos[0], pos[1])
        # Basit: en yakın entity'yi seç
        entities = self.world.get_entities_in_range(wx, wy, 2.0)
        if entities:
            self.selection.select_single(entities[0])
        else:
            self.selection.clear_selection()

    def _handle_right_click(self, pos):
        wx, wy = self.camera.screen_to_world(pos[0], pos[1])
        units = self.selection.get_selected_units()
        for u in units:
            u.state_machine.transition("MOVE")
            # Basit hedef atama
            u.target_pos = (wx, wy)

    def _update(self, dt: float):
        self.world.update(dt)
        self.ai.update(dt)
        # Bina üretimlerini economy'ye aktar
        for e in self.world.entities:
            if isinstance(e, Building) and e.is_producing:
                produced = e.update(dt)
                if produced:
                    self.economy.add_resources(produced)

    def _render(self):
        self.screen.fill((0, 0, 0))
        self.renderer.draw_map(self.world)
        self.renderer.draw_entities(self.world.entities)
        for e in self.world.entities:
            if e.is_alive() and hasattr(e, 'stats'):
                self.renderer.draw_hp_bar(e)
        self.ui.draw(self.screen, self.selection.selected)
        pygame.display.flip()

    def _autosave(self, dt: float):
        self.autosave_timer += dt
        if self.autosave_timer >= 30.0:
            self.autosave_timer = 0.0
            data = self.save_manager.serialize(
                self.world, self.economy,
                self.ui.king_name, self.ui.townhall_level, self.ui.xp
            )
            self.save_manager.save_to_file("autosave.json", data)
```

- [ ] **Step 2: main.py implemente et**

```python
from game.app import GameApp

if __name__ == "__main__":
    app = GameApp()
    app.run()
```

- [ ] **Step 3: Commit**

```bash
git add game/app.py main.py
git commit -m "feat: add main game loop with app and entry point"
```

---

### Task 16: Asset Placeholder'ları

**Files:**
- Modify: `game/renderer.py` — placeholder sprite oluşturma

- [ ] **Step 1: Renderer'a placeholder desteği ekle**

`game/renderer.py` içinde `draw_entities` metodunu güncelle — renkli kareler yerine basit pygame Surface'ler kullan. Mevcut implementasyon zaten placeholder. Ek olarak `assets.py` oluştur:

```python
# game/assets.py
import pygame

def load_placeholder(color, size=(32, 32)):
    surf = pygame.Surface(size)
    surf.fill(color)
    return surf

UNIT_COLORS = {
    "spearman": (0, 100, 255),
    "rider": (0, 150, 200),
    "archer": (0, 200, 150),
    "troll_knife": (200, 50, 50),
    "troll_club": (180, 30, 30),
    "troll_archer": (160, 20, 20),
}

BUILDING_COLORS = {
    "townhall": (139, 69, 19),
    "house": (160, 82, 45),
    "barracks_spear": (100, 100, 100),
    "barracks_rider": (120, 120, 120),
    "barracks_archer": (140, 140, 140),
    "woodcutter": (34, 139, 34),
    "quarry": (128, 128, 128),
    "farm": (255, 215, 0),
    "gold_mine": (218, 165, 32),
}

RESOURCE_COLORS = {
    "wood": (34, 100, 34),
    "stone": (100, 100, 100),
    "food": (200, 200, 50),
    "gold": (255, 215, 0),
    "gem": (138, 43, 226),
}
```

- [ ] **Step 2: Commit**

```bash
git add game/assets.py
git commit -m "feat: add asset placeholder colors"
```

---

## Self-Review Checklist

### 1. Spec Coverage

| Spec Bölümü | İlgili Task |
|---|---|
| 80×80 harita, güvenlik bölgeleri | Task 10 |
| Isometrik tilemap, kamera | Task 3 |
| 8 istatistikli savaş | Task 7, 9 |
| f(t) ekonomisi | Task 8 |
| 5 kaynak, mücevher özel | Task 8 |
| Alt bar UI, çift tıklama | Task 13 |
| 30s autosave | Task 15 |
| Sol üst panel (Kral adı, Level, Kaynaklar) | Task 13 |
| Save/Load JSON | Task 14 |

**Eksiklik:** `game/assets.py` Task 16'da oluşturuldu ama renderer henüz onu kullanmıyor. Bu MVP sonrası polish aşamasında bağlanacak.

### 2. Placeholder Scan

- ✅ Tüm task'lerde kod var
- ✅ Tüm test'lerde assertion var
- ✅ "TBD", "TODO" yok

### 3. Type Consistency

- `BaseEntity.state.alive` tüm task'lerde tutarlı
- `UnitStats` alan adları Task 7 ve Task 9'da aynı
- `EconomyEngine.resources` Dict[str, int] olarak tutarlı

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-30-social-empires-plan.md`.**

**Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
