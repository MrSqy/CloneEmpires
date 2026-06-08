import random
from typing import List, Optional
from game.entities.unit import Unit
from game.entities.building import Building
from game.world import World
from game.grid import cell_of, cell_distance


class AIController:
    def __init__(self, world: World):
        self.world = world
        self.patrol_centers = []
        self.agro_radius = 8  # hücre cinsinden

    def register_patrol(self, x: float, y: float):
        self.patrol_centers.append((x, y))

    def update(self, dt: float):
        enemies = [e for e in self.world.entities
                   if isinstance(e, Unit) and not getattr(e, 'is_player', False) and e.is_alive()]
        players = [e for e in self.world.entities
                   if isinstance(e, Unit) and getattr(e, 'is_player', True) and e.is_alive()]
        # Düşmanlar oyuncu kulelerine de saldırabilir (yıkık olmayanlara)
        towers = [e for e in self.world.entities
                  if isinstance(e, Building) and e.is_alive() and e.is_constructed
                  and e.is_tower() and not e.tower_disabled]
        players = players + towers

        for enemy in enemies:
            if enemy.state_machine.current == "DEAD":
                continue
            target = self._find_target(enemy, players)
            if target:
                # Hedefleme + kovalama/saldırı Unit.update ızgara mantığında yürür
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
