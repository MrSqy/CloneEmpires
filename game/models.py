from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Position:
    x: float = 0.0
    y: float = 0.0


@dataclass
class UnitStats:
    hp: float = 100.0
    max_hp: float = 100.0
    attack_phys: float = 10.0
    attack_magic: float = 0.0
    armor: float = 2.0
    magic_resist: float = 0.0
    attack_range: float = 1.0
    vision_range: float = 6.0
    move_speed: float = 2.0
    attack_speed: float = 1.0


@dataclass
class BuildingStats:
    level: int = 1
    max_level: int = 3
    production_rate: float = 1.0
    storage_bonus: int = 0
    # Savaş (yalnız kuleler için anlamlı; diğer binalarda 0)
    hp: float = 0.0
    max_hp: float = 0.0
    attack: float = 0.0
    attack_range: float = 0.0
    attack_speed: float = 1.0
    armor: float = 0.0
    magic_resist: float = 0.0


@dataclass
class EntityState:
    position: Position = field(default_factory=Position)
    selected: bool = False
    alive: bool = True
