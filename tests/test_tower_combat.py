from game.entities.building import Building
from game.entities.unit import Unit
from game.battle_manager import BattleManager
from game.world import World


def _world_with(*entities):
    w = World()
    for e in entities:
        w.add_entity(e)
    return w


def test_tower_has_combat_stats():
    t = Building("arrow_tower_1", 10, 10)
    assert t.is_tower() is True
    assert t.stats.max_hp == 300
    assert t.stats.attack == 18
    assert t.stats.attack_range == 6.0


def test_non_tower_buildings_are_not_towers():
    for bt in ("woodcutter", "house", "barracks_spear_1", "townhall"):
        b = Building(bt, 0, 0)
        assert b.is_tower() is False
        assert b.stats.max_hp == 0


def test_tower_fires_at_enemy_in_range():
    tower = Building("arrow_tower_1", 10, 10)
    enemy = Unit("troll_knife", 12, 10)  # menzil içinde (mesafe 2)
    enemy.is_player = False
    start_hp = enemy.stats.hp
    bm = BattleManager(_world_with(tower, enemy))
    bm.update(0.1)  # tower fires projectile
    bm.update(0.1)  # projectile travels and hits
    assert enemy.stats.hp < start_hp


def test_tower_does_not_fire_out_of_range():
    tower = Building("arrow_tower_1", 10, 10)
    enemy = Unit("troll_knife", 30, 30)  # menzil dışı
    enemy.is_player = False
    start_hp = enemy.stats.hp
    bm = BattleManager(_world_with(tower, enemy))
    bm.update(0.1)
    assert enemy.stats.hp == start_hp


def test_tower_disabled_at_zero_hp_but_not_removed():
    tower = Building("arrow_tower_1", 10, 10)
    tower.take_damage(1000)
    assert tower.stats.hp == 0
    assert tower.tower_disabled is True
    assert tower.is_alive() is True  # haritadan silinmez


def test_disabled_tower_stops_firing():
    tower = Building("arrow_tower_1", 10, 10)
    tower.take_damage(1000)
    enemy = Unit("troll_knife", 11, 10)
    enemy.is_player = False
    start_hp = enemy.stats.hp
    bm = BattleManager(_world_with(tower, enemy))
    bm.update(0.1)
    assert enemy.stats.hp == start_hp
