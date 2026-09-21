from typing import Dict, List, Optional
from collections import deque
from game.entities.unit import Unit
from game.entities.building import Building

try:
    from game.entities.worker import Worker
except ImportError:
    Worker = None

UNIT_COSTS = {
    "worker": {"food": 10, "wood": 5},
    "spearman": {"food": 15, "wood": 10},
    "swordsman": {"food": 20, "gold": 15},
    "archer": {"food": 15, "wood": 15},
    "rider": {"food": 25, "gold": 20},
    "mage": {"food": 20, "gem": 10},
}

UNIT_TRAIN_TIME = {
    "worker": 3.0,
    "spearman": 4.0,
    "swordsman": 5.0,
    "archer": 4.5,
    "rider": 5.0,
    "mage": 6.0,
}

MAX_QUEUE_SIZE = 5


class ProductionQueue:
    """Production queue for training units at a building (Town Hall, Barracks)."""

    def __init__(self, building: Building, economy):
        self.building = building
        self.economy = economy
        self.queue: deque = deque()
        self.current_production: Optional[Dict] = None
        self.progress = 0.0
        self.max_progress = 0.0
        self.last_spawned = []

    def enqueue(self, unit_type: str) -> bool:
        """Add a unit to the production queue if affordable and queue not full."""
        from game.building_catalog import get_trains
        allowed = ["worker"] if self.building.building_type == "townhall" else get_trains(self.building.building_type)
        if unit_type not in allowed or not self.building.is_constructed:
            return False
        total_queued = len(self.queue) + (1 if self.current_production else 0)
        if total_queued >= MAX_QUEUE_SIZE:
            return False
        cost = UNIT_COSTS.get(unit_type, {})
        if not self.economy.can_afford(cost):
            return False

        if not self.economy.spend(cost):
            return False

        self.queue.append({
            "unit_type": unit_type,
            "train_time": UNIT_TRAIN_TIME[unit_type],
            "level": self.building.stats.level,
            "cost": dict(cost),
        })
        return True

    def update(self, dt: float, world) -> Optional[Unit]:
        """Ücretli kuyruğu ilerletir; gelişirken veya doğum alanı doluyken korur.

        Dönüş ilk doğan birimdir; aynı aralıkta doğanların tamamı last_spawned'dadır.
        """
        self.last_spawned = []
        if not self.building.is_constructed:
            return None
        remaining = max(0.0, dt)
        while self.current_production or self.queue:
            if self.current_production is None:
                self.current_production = self.queue.popleft()
                self.progress = 0.0
                self.max_progress = self.current_production["train_time"]
            needed = max(0.0, self.max_progress - self.progress)
            if remaining + 1e-9 < needed:
                self.progress += remaining
                break
            self.progress = self.max_progress
            remaining = max(0.0, remaining - needed)
            item = self.current_production
            unit = self._spawn_unit(item["unit_type"], world, item["level"])
            if unit is None:
                break  # Tamamlanan ücretli sipariş alan açılmasını bekler.
            self.last_spawned.append(unit)
            self.current_production = None
            self.progress = self.max_progress = 0.0
        return self.last_spawned[0] if self.last_spawned else None

    def _spawn_unit(self, unit_type: str, world, level=None) -> Optional[Unit]:
        """En yakın boş hücrede doğurur; yer yoksa siparişe dokunmaz."""
        from game.grid import cell_of
        cell = world.nearest_free_cell(cell_of(self.building.x, self.building.y),
                                       max_radius=max(world.width, world.height))
        if cell is None:
            return None
        lvl = self.building.stats.level if level is None else level
        unit = Worker(*cell, level=lvl) if unit_type == "worker" else Unit(unit_type, *cell, level=lvl)
        world.add_entity(unit)
        return unit

    def get_queue_status(self) -> Dict:
        """Return current queue status for UI display."""
        return {
            "current": self.current_production,
            "progress": self.progress,
            "max_progress": self.max_progress,
            "queued": list(self.queue),
        }

    def cancel_current(self):
        """Cancel current production and refund resources."""
        if self.current_production:
            unit_type = self.current_production["unit_type"]
            cost = self.current_production["cost"]
            self.economy.add_resources(cost)
            self.current_production = None
            self.progress = 0.0
            self.max_progress = 0.0

    def is_busy(self) -> bool:
        return self.current_production is not None or len(self.queue) > 0
