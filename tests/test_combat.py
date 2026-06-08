from game.combat import CombatEngine
from game.entities.unit import Unit


def test_physical_damage():
    attacker = Unit("spearman", 0, 0)
    attacker.stats.attack_phys = 20
    target = Unit("troll", 0, 0)
    target.stats.armor = 5
    dmg = CombatEngine.calculate_damage(attacker, target, "physical")
    assert dmg == 15


def test_magic_damage():
    attacker = Unit("mage", 0, 0)
    attacker.stats.attack_magic = 30
    target = Unit("troll", 0, 0)
    target.stats.magic_resist = 10
    dmg = CombatEngine.calculate_damage(attacker, target, "magic")
    assert dmg == 20


def test_damage_never_negative():
    attacker = Unit("weak", 0, 0)
    attacker.stats.attack_phys = 2
    target = Unit("tank", 0, 0)
    target.stats.armor = 10
    dmg = CombatEngine.calculate_damage(attacker, target, "physical")
    assert dmg == 0
