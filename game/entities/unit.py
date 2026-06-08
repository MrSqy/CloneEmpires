from game.entities.base_entity import BaseEntity
from game.unit_stats import get_unit_stats
from game.grid import cell_of, cell_distance, find_path

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
        self.stats = get_unit_stats(unit_type, level)
        self.state_machine = StateMachine()
        self.attack_cooldown = 0.0
        self.target = None
        self.target_pos = None
        self.path = []  # gidilecek hücre merkezleri (ızgara waypoint'leri)
        self.is_player = True
        self.last_attacker = None
        self.manual_override = False

    # ----------------------------------------------------------------- ızgara
    @property
    def cell(self):
        return cell_of(self.x, self.y)

    def _settled(self):
        """Birim tam bir hücre merkezinde mi?"""
        return abs(self.x - round(self.x)) < 1e-3 and abs(self.y - round(self.y)) < 1e-3

    def _in_attack_range(self, target) -> bool:
        return cell_distance(self.cell, cell_of(target.x, target.y)) <= self.stats.attack_range

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

    def update(self, dt: float):
        """Her frame. Izgara-kilitli hareket + saldırı kovalama."""
        if self.state_machine.current == "DEAD":
            return

        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        if self.state_machine.current == "MOVE":
            self._advance_along_path(dt)
            if not self.path:
                self.manual_override = False
                self.state_machine.transition("IDLE")
        elif self.state_machine.current == "ATTACK":
            self._update_attack(dt)

    def _update_attack(self, dt: float):
        if not self.target or not self.target.is_alive():
            self.target = None
            self.path = []
            self.target_pos = None
            self.state_machine.transition("IDLE")
            return
        # Kutsal kural: saldırmadan önce bir hücre merkezine otur
        if not self._settled():
            if not self.path:
                self.path = [self.cell]
                self.target_pos = (float(self.cell[0]), float(self.cell[1]))
            self._advance_along_path(dt)
            return
        if self._in_attack_range(self.target):
            # menzilde: yerinde dur (hasar BattleManager'da uygulanır)
            self.path = []
            self.target_pos = None
            return
        # menzil dışı: ızgara üzerinden yaklaş
        self._chase(dt)

    def _chase(self, dt: float):
        if self.path:
            self._advance_along_path(dt)
            return
        w = getattr(self, 'world', None)
        if w is None or not self.target:
            return
        goal = w.nearest_free_cell(cell_of(self.target.x, self.target.y), ignore=self)
        if goal is None:
            return
        path = find_path(self.cell, goal, w.make_blocked(ignore=self))
        if path:
            self.path = path
            self.target_pos = (float(path[0][0]), float(path[0][1]))
            self._advance_along_path(dt)

    def _next_cell_occupied(self) -> bool:
        w = getattr(self, 'world', None)
        if w is None or not self.path:
            return False
        nxt = self.path[0]
        if nxt == self.cell:
            return False
        return w.unit_at_cell(nxt, ignore=self)

    def _advance_along_path(self, dt: float):
        """Bir sonraki hücre merkezine doğru ilerler; varınca tam oturur ve
        waypoint'i düşürür. Bir seyahat daima bir merkezde sonlanır."""
        if not self.path:
            return
        # Kutsal kural korunur: bir merkezde otururken sıradaki hücre başka bir
        # birimle doluysa o merkezde kal (üst üste binmeyi önler). Yeni leg'e
        # ancak hedef hücre boşken başlanır.
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

    def _compute_path_to(self, goal_cell):
        w = getattr(self, 'world', None)
        if w is None:
            return [goal_cell] if goal_cell != self.cell else []
        free = w.nearest_free_cell(goal_cell, ignore=self)
        if free is not None:
            goal_cell = free
        path = find_path(self.cell, goal_cell, w.make_blocked(ignore=self))
        if not path and goal_cell != self.cell:
            path = [goal_cell]
        return path

    def move_to(self, x: float, y: float):
        """Birime bir hücreye gitme emri (ızgara yolu hesaplanır).
        Manuel komut verildiğinde auto-counter-attack ve auto-acquire devre dışı kalır."""
        self.target = None
        self.last_attacker = None
        self.manual_override = True
        if hasattr(self, 'gather_timer'):
            self.gather_timer = 0.0
        self.path = self._compute_path_to(cell_of(x, y))
        self.target_pos = (float(self.path[0][0]), float(self.path[0][1])) if self.path else None
        self.state_machine.transition("MOVE")

    def attack_target(self, target: 'Unit'):
        """Birime başka bir birime/binaya saldırma emri."""
        if self.target is target and self.state_machine.current == "ATTACK":
            return
        self.manual_override = False
        self.target = target
        self.path = []
        self.target_pos = None
        self.attack_cooldown = 1.0 / self.stats.attack_speed
        self.state_machine.transition("ATTACK")

    def halt_for_attack(self, target: 'Unit'):
        """Hareket halindeyken menzile düşman girince: en yakın hücre merkezine
        oturup saldırıya geçer (kutsal kural)."""
        self.manual_override = False
        self.target = target
        self.path = []
        self.target_pos = None
        self.attack_cooldown = 1.0 / self.stats.attack_speed
        self.state_machine.transition("ATTACK")
