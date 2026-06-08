from typing import Literal
from game.entities.unit import Unit
from game.grid import cell_of, cell_distance


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
        """Menzil hücre cinsinden: round(öklid hücre mesafesi) <= attack_range."""
        a = cell_of(attacker.x, attacker.y)
        b = cell_of(target.x, target.y)
        return cell_distance(a, b) <= attacker.stats.attack_range
