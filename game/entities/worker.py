from game.entities.unit import Unit
from game.entities.resource import ResourceNode
from game.grid import cell_of, cell_distance, find_path


class Worker(Unit):
    """Kaynak toplayan ve inşaat yapan köylü. 1 menzilli (komşu hücreden çalışır)."""

    def __init__(self, x: float, y: float, level: int = 1):
        super().__init__("worker", x, y, level)
        self.gather_timer = 0.0
        self.task = None
        self.task_target = None
        self.is_inside_building = None  # None or Building instance

    def assign_task(self, task_type: str, target):
        self.task = task_type
        self.task_target = target
        self.path = []
        if task_type in ("gather", "build"):
            self.state_machine.transition("MOVE")

    # ---------------------------------------------------------- ızgara yardımcı
    def _within_range(self, x, y, rng=1) -> bool:
        return cell_distance(self.cell, cell_of(x, y)) <= rng

    def _approach_cell(self, gx, gy, dt) -> bool:
        """Hedef hücreye komşu (menzil 1) boş hücreye ızgara yolu izle.
        Menzile girince True döner."""
        if self._within_range(gx, gy, 1):
            self.path = []
            return True
        if not self.path:
            w = getattr(self, 'world', None)
            if w is None:
                self.path = [(gx, gy)]
            else:
                goal = w.nearest_free_cell((gx, gy), ignore=self)
                if goal is None:
                    return False
                self.path = find_path(self.cell, goal, w.make_blocked(ignore=self))
                if not self.path and self.cell != goal:
                    self.path = [goal]
        self._advance_along_path(dt)
        return self._within_range(gx, gy, 1)

    # ------------------------------------------------------------------ update
    def update(self, dt: float, world=None, economy=None):
        if self.state_machine.current == "DEAD":
            return
        if self.is_inside_building:
            return  # Inside building: frozen until removed

        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        if self.task == "gather" and self.task_target and world and economy:
            self._do_gather(dt, world, economy)
        elif self.task == "build" and self.task_target and world and economy:
            self._do_build(dt, world, economy)
        elif self.task == "working" and self.task_target is not None and self.task_target.is_alive():
            # Kaynak binasına atanmış: binanın komşusuna yürü, sonra çalış
            if self._approach_cell(*cell_of(self.task_target.x, self.task_target.y), dt):
                self.state_machine.transition("IDLE")
        elif self.state_machine.current == "MOVE":
            self._advance_along_path(dt)
            if not self.path:
                self.state_machine.transition("IDLE")

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

        # Within range: gather
        self.gather_timer += dt
        if self.gather_timer >= 2.0:
            self.gather_timer = 0.0
            # Harvest 10 resources
            harvested = target.harvest(10)
            if harvested > 0:
                economy.add_resources({target.resource_type: int(harvested)})
            # If depleted after this harvest, task ends
            if target.is_depleted():
                self.task = None
                self.path = []
                self.gather_timer = 0.0
                self.state_machine.transition("IDLE")

    def _do_build(self, dt: float, world, economy):
        target = self.task_target
        if not target or not target.is_alive():
            self.task = None
            self.path = []
            self.state_machine.transition("IDLE")
            return

        if not self._approach_cell(*cell_of(target.x, target.y), dt):
            return
        # Menzilde: inşaata katkı
        if hasattr(target, 'construction_progress'):
            target.construction_progress += 20 * dt
            if target.construction_progress >= 100:
                target.is_constructed = True
                self.task = None
                self.path = []
                self.state_machine.transition("IDLE")
