from typing import List
from game.entities.unit import Unit
from game.entities.building import Building
from game.combat import CombatEngine
from game.grid import cell_of, cell_distance


class BattleManager:
    """Handles combat between player units and enemy units."""

    def __init__(self, world):
        self.world = world

    def update(self, dt: float):
        """Process all combat interactions for this frame."""
        self._update_towers(dt)
        self._update_projectiles(dt)
        self._auto_acquire()
        units = [e for e in self.world.entities if isinstance(e, Unit) and e.is_alive()]

        for attacker in units:
            if attacker.state_machine.current != "ATTACK":
                continue
            if not attacker.target or not attacker.target.is_alive():
                attacker.state_machine.transition("IDLE")
                continue

            # Check if attacker is ready to strike (cooldown decremented in Unit.update)
            if attacker.attack_cooldown > 0:
                continue

            # Check range
            if not CombatEngine.in_range(attacker, attacker.target):
                continue

            # Deal damage
            damage_type = "magic" if attacker.stats.attack_magic > attacker.stats.attack_phys else "physical"
            damage = CombatEngine.calculate_damage(attacker, attacker.target, damage_type)
            CombatEngine.apply_damage(attacker.target, damage, attacker)

            # Reset attack cooldown
            attacker.perform_attack()

        # Counter-attack: units that were hit strike back at their last attacker
        for u in units:
            if getattr(u, 'manual_override', False):
                continue
            if u.last_attacker and u.last_attacker.is_alive():
                if u.state_machine.current in ("IDLE", "MOVE"):
                    u.halt_for_attack(u.last_attacker)

    def _auto_acquire(self):
        """Hareket/boşta olan oyuncu savaş birimi menziline düşman girince
        en yakın hücre merkezine oturup saldırıya geçer (kutsal kural)."""
        from game.entities.worker import Worker
        enemies = [e for e in self.world.entities
                   if isinstance(e, Unit) and e.is_alive() and not e.is_player]
        if not enemies:
            return
        for u in self.world.entities:
            if not (isinstance(u, Unit) and u.is_alive() and u.is_player):
                continue
            if isinstance(u, Worker):
                continue
            if u.stats.attack_phys <= 0 and u.stats.attack_magic <= 0:
                continue
            if u.state_machine.current not in ("IDLE", "MOVE"):
                continue
            if getattr(u, 'manual_override', False):
                continue
            ucell = cell_of(u.x, u.y)
            best = None
            target = None
            for en in enemies:
                d = cell_distance(ucell, cell_of(en.x, en.y))
                if d <= u.stats.vision_range and (best is None or d < best):
                    best = d
                    target = en
            if target is not None:
                u.halt_for_attack(target)

    def _update_towers(self, dt: float):
        """Oyuncu kuleleri menzildeki en yakın düşmana ateş eder."""
        towers = [e for e in self.world.entities
                  if isinstance(e, Building) and e.is_alive() and e.is_constructed
                  and e.is_tower() and not e.tower_disabled
                  and getattr(e, 'is_player', True)]
        if not towers:
            return
        enemies = [e for e in self.world.entities
                   if isinstance(e, Unit) and e.is_alive() and not e.is_player]

        for tower in towers:
            if tower.attack_cooldown > 0:
                tower.attack_cooldown -= dt
            tcell = cell_of(tower.x, tower.y)
            target = None
            best = None
            for en in enemies:
                d = cell_distance(tcell, cell_of(en.x, en.y))
                if d <= tower.stats.attack_range and (best is None or d < best):
                    best = d
                    target = en
            if target and tower.attack_cooldown <= 0:
                from game.entities.projectile import Projectile
                proj = Projectile(tower.x, tower.y, target, speed=10.0,
                                  damage=tower.stats.attack, source=tower)
                proj.is_player = True
                self.world.add_entity(proj)
                tower.attack_cooldown = 1.0 / tower.stats.attack_speed

    def _update_projectiles(self, dt: float):
        """Update homing projectiles and remove dead ones."""
        for e in list(self.world.entities):
            if hasattr(e, 'target') and hasattr(e, 'speed') and not hasattr(e, 'unit_type'):
                e.update(dt)

    def get_enemies_in_range(self, unit: Unit, radius: float = 10.0) -> List[Unit]:
        """Find enemy units within range of the given unit."""
        enemies = []
        for e in self.world.entities:
            if isinstance(e, Unit) and e.is_alive() and e.is_player != unit.is_player:
                dx = e.x - unit.x
                dy = e.y - unit.y
                if (dx ** 2 + dy ** 2) ** 0.5 <= radius:
                    enemies.append(e)
        return enemies

    def find_closest_enemy(self, unit: Unit) -> Unit:
        """Find the closest enemy to the given unit."""
        enemies = self.get_enemies_in_range(unit, radius=9999.0)
        if not enemies:
            return None
        return min(enemies, key=lambda e: ((e.x - unit.x) ** 2 + (e.y - unit.y) ** 2) ** 0.5)
