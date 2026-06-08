from typing import Dict, List, Tuple

XP_REWARDS = {
    "troll_knife": 15,
    "troll_club": 20,
    "troll_archer": 25,
    "troll_mage": 30,
    "boss": 100,
}

BUILDING_XP = {
    "woodcutter": 5,
    "quarry": 5,
    "farm": 5,
    "gold_mine": 10,
    "barracks": 15,
    "house": 3,
    "storage": 8,
    "townhall": 20,
}

UNIT_TRAIN_XP = {
    "worker": 2,
    "spearman": 5,
    "swordsman": 7,
    "archer": 6,
    "mage": 8,
}

class XPSystem:
    """Handles XP gains, level progression, and rewards."""
    
    def __init__(self, ui):
        self.ui = ui
        self.level = 1
        self.xp = 0
        self.max_xp = 100
        self.xp_multiplier = 1.0
    
    def add_xp(self, amount: int):
        """Add XP and handle level ups."""
        self.xp += int(amount * self.xp_multiplier)
        while self.xp >= self.max_xp:
            self.xp -= self.max_xp
            self._level_up()
        self._sync_ui()
    
    def _level_up(self):
        self.level += 1
        self.max_xp = int(self.max_xp * 1.5)
        self.xp_multiplier += 0.05
        # Bonus: increase storage on level up
        from game.economy import EconomyEngine
        # We can't directly modify economy here, but UI will reflect level
    
    def _sync_ui(self):
        """Sync xp/level to UI manager."""
        self.ui.xp = self.xp
        self.ui.max_xp = self.max_xp
        self.ui.townhall_level = self.level
    
    def reward_kill(self, enemy_type: str):
        xp = XP_REWARDS.get(enemy_type, 10)
        self.add_xp(xp)
    
    def reward_building_constructed(self, building_type: str):
        xp = BUILDING_XP.get(building_type, 5)
        self.add_xp(xp)
    
    def reward_unit_trained(self, unit_type: str):
        xp = UNIT_TRAIN_XP.get(unit_type, 3)
        self.add_xp(xp)
    
    def get_level(self) -> int:
        return self.level
    
    def get_xp_ratio(self) -> float:
        return self.xp / self.max_xp if self.max_xp > 0 else 0.0
