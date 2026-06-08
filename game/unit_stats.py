"""Birim tipine göre temel istatistik tablosu.

Her birim tipinin kendine özgü statları vardır; eskiden tüm birimler aynı
UnitStats default'unu paylaşıyordu (savaşı anlamsız kılıyordu). attack_range
yüksek olan birimler (okçu, mage, troll_archer) menzilli kabul edilir.
"""
from game.models import UnitStats

# Menzilli sayılma eşiği (tile). Bunun üstündeki birimler dur-ateş eder.
RANGED_THRESHOLD = 3.0

# unit_type -> taban stat sözlüğü (level 1 değerleri)
BASE_STATS = {
    "worker": dict(hp=50, attack_phys=3, armor=0, attack_range=1.0, vision_range=6.0,
                   move_speed=3.0, attack_speed=1.0),
    "spearman": dict(hp=150, attack_phys=15, armor=4, attack_range=2.0, vision_range=8.0,
                     move_speed=2.0, attack_speed=1.0),
    "swordsman": dict(hp=100, attack_phys=20, armor=6, attack_range=1.0, vision_range=7.0,
                      move_speed=2.2, attack_speed=1.1),
    "rider": dict(hp=140, attack_phys=18, armor=4, attack_range=1.0, vision_range=7.0,
                  move_speed=3.5, attack_speed=1.2),
    "archer": dict(hp=60, attack_phys=25, armor=1, attack_range=8.0, vision_range=14.0,
                   move_speed=2.0, attack_speed=1.3),
    "mage": dict(hp=70, attack_phys=0, attack_magic=28, armor=0, magic_resist=5,
                 attack_range=5.0, vision_range=10.0, move_speed=1.8, attack_speed=0.8),
    # Düşmanlar (troller) — can ve hasar yarısı
    "troll_knife": dict(hp=50, attack_phys=10, armor=2, attack_range=1.0, vision_range=6.0,
                        move_speed=2.0, attack_speed=1.0),
    "troll_club": dict(hp=75, attack_phys=12, armor=8, attack_range=1.2, vision_range=6.0,
                       move_speed=1.5, attack_speed=0.8),
    "troll_archer": dict(hp=30, attack_phys=12, armor=1, attack_range=5.5, vision_range=10.0,
                         move_speed=1.8, attack_speed=1.2),
}

# Bilinmeyen tipler için makul default
_DEFAULT = dict(hp=100, attack_phys=10, armor=2, attack_range=1.0, vision_range=6.0,
                move_speed=2.0, attack_speed=1.0)


def level_multiplier(level: int) -> float:
    """Her seviye hp ve hasarı ölçekler (L2 = 2x, L3 = 3x)."""
    return 1.0 + (level - 1) * 1.0


def get_unit_stats(unit_type: str, level: int = 1) -> UnitStats:
    """Belirtilen birim tipi ve seviyesi için yeni bir UnitStats üretir."""
    base = BASE_STATS.get(unit_type, _DEFAULT)
    mult = level_multiplier(level)
    stats = UnitStats()
    hp = base.get("hp", 100) * mult
    stats.hp = hp
    stats.max_hp = hp
    stats.attack_phys = base.get("attack_phys", 10) * mult
    stats.attack_magic = base.get("attack_magic", 0) * mult
    stats.armor = base.get("armor", 0)
    stats.magic_resist = base.get("magic_resist", 0)
    stats.attack_range = base.get("attack_range", 1.0)
    stats.vision_range = base.get("vision_range", 6.0)
    stats.move_speed = base.get("move_speed", 2.0)
    stats.attack_speed = base.get("attack_speed", 1.0)
    return stats


def is_ranged(unit_type: str) -> bool:
    base = BASE_STATS.get(unit_type, _DEFAULT)
    return base.get("attack_range", 1.0) >= RANGED_THRESHOLD
