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

    def enqueue(self, unit_type: str) -> bool:
        """Add a unit to the production queue if affordable and queue not full."""
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
            "train_time": UNIT_TRAIN_TIME.get(unit_type, 4.0),
        })
        return True

    def update(self, dt: float, world) -> Optional[Unit]:
        """Process production. Returns a new Unit when one finishes."""
        if self.current_production is None and self.queue:
            self.current_production = self.queue.popleft()
            self.progress = 0.0
            self.max_progress = self.current_production["train_time"]

        if self.current_production:
            self.progress += dt
            if self.progress >= self.max_progress:
                # Production complete
                unit_type = self.current_production["unit_type"]
                new_unit = self._spawn_unit(unit_type, world)
                self.current_production = None
                self.progress = 0.0
                self.max_progress = 0.0
                return new_unit

        return None

    def _spawn_unit(self, unit_type: str, world) -> Unit:
        """Spawn the unit near the building."""
        bx, by = self.building.x, self.building.y
        # Spawn slightly offset from building
        import random
        offset_x = random.choice([-2, -1, 1, 2])
        offset_y = random.choice([-2, -1, 1, 2])
        sx, sy = bx + offset_x, by + offset_y

        lvl = getattr(self.building, 'stats', None)
        lvl = lvl.level if lvl else 1
        if unit_type == "worker" and Worker is not None:
            unit = Worker(sx, sy, level=lvl)
        else:
            unit = Unit(unit_type, sx, sy, level=lvl)

        unit.is_player = True
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
            cost = UNIT_COSTS.get(unit_type, {})
            self.economy.add_resources(cost)
            self.current_production = None
            self.progress = 0.0
            self.max_progress = 0.0

    def is_busy(self) -> bool:
        return self.current_production is not None or len(self.queue) > 0
