from game.unit_stats import get_unit_stats, is_ranged, level_multiplier
from game.entities.unit import Unit


def test_unit_types_have_distinct_stats():
    spear = get_unit_stats("spearman")
    archer = get_unit_stats("archer")
    sword = get_unit_stats("swordsman")
    # Statlar artık tipe göre farklılaşmalı
    assert spear.hp != archer.hp
    assert sword.attack_phys != archer.attack_phys


def test_archer_is_ranged():
    assert is_ranged("archer")
    assert is_ranged("mage")
    assert is_ranged("troll_archer")
    assert not is_ranged("spearman")
    assert not is_ranged("worker")


def test_archer_attack_range_high():
    archer = get_unit_stats("archer")
    assert archer.attack_range >= 5.0


def test_level_scaling():
    l1 = get_unit_stats("spearman", level=1)
    l2 = get_unit_stats("spearman", level=2)
    assert l2.hp > l1.hp
    assert l2.attack_phys > l1.attack_phys
    assert abs(level_multiplier(2) - 2.0) < 1e-9
    assert l2.hp == l1.hp * 2.0


def test_unit_uses_table_stats():
    archer = Unit("archer", 0, 0)
    spear = Unit("spearman", 0, 0)
    assert archer.stats.attack_range >= 5.0
    assert spear.stats.hp != archer.stats.hp


def test_worker_stats_from_table():
    from game.entities.worker import Worker
    w = Worker(0, 0)
    assert w.stats.move_speed == 3.0
    assert w.stats.hp == 50


def test_mage_uses_magic_damage():
    mage = get_unit_stats("mage")
    assert mage.attack_magic > 0
    assert mage.attack_magic > mage.attack_phys
