from typing import Dict, List
from game.entities.base_entity import BaseEntity
from game.models import BuildingStats
from game.grid import cell_of

# building_type -> ürettiği kaynak
RESOURCE_MAP = {
    "woodcutter": "wood",
    "quarry": "stone",
    "farm": "food",
    "gold_mine": "gold",
}

class Building(BaseEntity):
    def __init__(self, building_type: str, x: float, y: float,
                 cost: Dict[str, int] = None, stats: BuildingStats = None):
        super().__init__(building_type, x, y)
        self.building_type = building_type
        self.cost = cost or {}
        self.stats = stats or BuildingStats()
        self.production_timer = 0.0
        self.is_producing = False
        self.construction_progress = 0.0
        self.is_constructed = True  # Existing buildings start constructed
        self.build_time = 5.0  # Seconds to build (for construction sites)

        # Köylü atama / çalışma modu durumu
        self.assigned_workers: List = []
        self.worker_mode = None
        self.pending_worker_mode = None
        self.worker_timer = 0.0
        self.worker_active = False

        # Kule savaş durumu
        self.attack_cooldown = 0.0
        self.tower_disabled = False
        self._load_tower_combat()

    # ------------------------------------------------------------------- kuleler
    def _load_tower_combat(self):
        from game.building_catalog import get_tower_combat
        c = get_tower_combat(self.building_type)
        if not c:
            return
        self.stats.hp = c["hp"]
        self.stats.max_hp = c["hp"]
        self.stats.attack = c["attack"]
        self.stats.attack_range = c["attack_range"]
        self.stats.attack_speed = c["attack_speed"]

    def is_tower(self) -> bool:
        return self.stats.max_hp > 0 and self.stats.attack > 0

    def take_damage(self, amount: float):
        """Kule hasar alır. HP biterse yıkılmaz ama ateş etmeyi keser (yangın kalır)."""
        if self.stats.max_hp <= 0:
            return
        self.stats.hp = max(0.0, self.stats.hp - amount)
        if self.stats.hp <= 0:
            self.tower_disabled = True

    # ----------------------------------------------------- Köylü çalışma modları
    def resource_type(self):
        return RESOURCE_MAP.get(self.building_type)

    def assign_worker(self, worker) -> bool:
        from game.work_modes import MAX_WORKERS
        if self.worker_active:
            return False  # Cannot enter while production is running
        if self.resource_type() is None:
            return False
        if worker in self.assigned_workers or len(self.assigned_workers) >= MAX_WORKERS:
            return False
        self.assigned_workers.append(worker)
        worker.task = "working"
        worker.task_target = self
        worker.is_inside_building = self
        # Snap worker position to building center (hidden visually)
        worker.state.position.x = self.x
        worker.state.position.y = self.y
        return True

    def remove_worker(self, worker) -> bool:
        """Remove a worker from this building. Workers may exit even during active production."""
        if worker not in self.assigned_workers:
            return False
        self.assigned_workers.remove(worker)
        worker.task = None
        worker.task_target = None
        worker.is_inside_building = None
        # Move worker to a free neighboring cell
        w = getattr(self, 'world', None)
        if w is not None:
            free = w.nearest_free_cell(cell_of(self.x, self.y), ignore=worker)
            if free:
                worker.state.position.x = float(free[0])
                worker.state.position.y = float(free[1])
        # If last worker removed, stop production
        if not self.assigned_workers:
            self.cancel_worker_production()
        return True

    def start_worker_production(self, mode_key: str, economy) -> bool:
        """Modu başlatır; mücevher maliyetini peşin düşer. Başarılıysa True."""
        from game.work_modes import gem_cost, duration_seconds, WORK_MODES
        if mode_key not in WORK_MODES:
            return False
        if not self.assigned_workers or self.worker_active:
            return False
        if not economy.spend({"gem": gem_cost(mode_key)}):
            return False
        self.worker_mode = mode_key
        self.worker_timer = duration_seconds(mode_key)
        self.worker_active = True
        return True

    def _free_workers(self):
        for w in self.assigned_workers:
            if getattr(w, "task", None) == "working":
                w.task = None
                w.task_target = None
            w.is_inside_building = None
        self.assigned_workers = []

    def cancel_worker_production(self):
        """Üretimi iptal eder (kısmi ödeme yok, mücevher iadesi yok).
        Köylüler binada kalır; sadece üretim durur."""
        self.worker_active = False
        self.worker_mode = None
        self.worker_timer = 0.0

    def update_worker_production(self, dt: float, economy):
        """Zamanlı köylü üretimini ilerletir. Tamamlanınca ödül sözlüğü döner."""
        if not self.worker_active:
            return None
        # Atanan köylü kaybolduysa iptal (kısmi ödeme yok)
        alive = [w for w in self.assigned_workers if w.is_alive()]
        if not alive or len(alive) < len(self.assigned_workers):
            self.cancel_worker_production()
            return None

        self.worker_timer -= dt
        if self.worker_timer <= 0:
            from game.work_modes import resource_gain, gem_reward
            n = len(self.assigned_workers)
            rtype = self.resource_type()
            amount = resource_gain(self.worker_mode, n)
            gems = gem_reward(amount)
            economy.add_resources({rtype: amount, "gem": gems})
            reward = dict(resource=rtype, amount=amount, gems=gems, mode=self.worker_mode)
            self.worker_active = False
            self.worker_mode = None
            self.worker_timer = 0.0
            self._free_workers()
            return reward
        return None

    @classmethod
    def create_construction_site(cls, building_type: str, x: float, y: float, cost: Dict[str, int] = None):
        """Create a building that is under construction."""
        instance = cls(building_type, x, y, cost=cost)
        instance.is_constructed = False
        instance.construction_progress = 0.0
        return instance

    def can_build(self, resources: Dict[str, int]) -> bool:
        return all(resources.get(k, 0) >= v for k, v in self.cost.items())

    def start_production(self):
        self.is_producing = True
        self.production_timer = 0.0

    def stop_production(self):
        self.is_producing = False

    def update(self, dt: float, economy) -> bool:
        """Process production for this frame. Returns True if resources were produced."""
        if not self.is_producing:
            return False
        
        self.production_timer += dt
        
        # Determine resource type from building_type
        resource_map = {
            "woodcutter": "wood",
            "quarry": "stone",
            "farm": "food",
            "gold_mine": "gold",
        }
        
        res_type = resource_map.get(self.building_type)
        if not res_type:
            return False
        
        # Produce resources using f(t) formula
        from game.economy import EconomyEngine
        total = EconomyEngine.calculate_production(
            base_rate=self.stats.production_rate,
            duration=self.production_timer,
            building_level=self.stats.level
        )
        
        # Only deliver whole amounts
        amount = int(total)
        if amount > 0:
            economy.add_resources({res_type: amount})
            # Reset timer, keeping fractional remainder
            self.production_timer = 0.0
            return True
        
        return False

    def can_upgrade(self, resources: Dict[str, int]) -> bool:
        if self.stats.level >= self.stats.max_level:
            return False
        upgrade_cost = {k: v * 2 for k, v in self.cost.items()}
        return all(resources.get(k, 0) >= v for k, v in upgrade_cost.items())

    def upgrade(self, new_type: str):
        """Upgrade this building to a new type (next level)."""
        self.building_type = new_type
        from game.building_catalog import get_cost
        self.cost = get_cost(new_type)
        self.stats.level += 1
        self.is_constructed = False
        self.construction_progress = 0.0
        self._load_tower_combat()
