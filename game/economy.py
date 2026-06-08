from typing import Dict
from game.constants import RESOURCES, INITIAL_STORAGE, PRODUCTION_EXPONENT, STORAGE_PER_LEVEL


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
