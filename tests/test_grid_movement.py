import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from game.grid import cell_of, cell_distance, in_range, find_path
from game.world import World
from game.entities.unit import Unit
from game.entities.worker import Worker
from game.entities.building import Building
from game.entities.resource import ResourceNode
from game.battle_manager import BattleManager


# ------------------------------------------------------------------ grid çekirdek
def test_cell_of_rounds_to_center():
    assert cell_of(3.4, 5.6) == (3, 6)
    assert cell_of(3.0, 5.0) == (3, 5)


def test_range_round_euclid():
    # 1 menzilli: 3x3 köşeyi vurur (1.41->1)
    assert in_range((0, 0), (1, 1), 1) is True
    # 2 menzilli: 5x5 köşesini vuramaz (2.83->3)
    assert cell_distance((0, 0), (2, 2)) == 3
    assert in_range((0, 0), (2, 2), 2) is False
    assert in_range((0, 0), (2, 1), 2) is True  # 2.23->2


def test_astar_routes_around_obstacle():
    def blocked(c):
        if not (0 <= c[0] < 10 and 0 <= c[1] < 10):
            return True
        return c[0] == 2 and 0 <= c[1] <= 3  # dikey duvar
    path = find_path((0, 0), (4, 0), blocked)
    assert path and path[-1] == (4, 0)
    assert all(not blocked(c) for c in path)


# --------------------------------------------------------------------- occupancy
def test_buildings_and_units_block_cells():
    w = World()
    b = Building("townhall", 10, 10)
    u = Unit("spearman", 8, 10)
    w.add_entity(b)
    w.add_entity(u)
    assert w.cell_blocked((10, 10)) is True
    assert w.cell_blocked((8, 10)) is True
    assert w.cell_blocked((8, 10), ignore=u) is False
    assert w.cell_blocked((9, 9)) is False


def test_nearest_free_cell_avoids_building():
    w = World()
    w.add_entity(Building("townhall", 10, 10))
    nf = w.nearest_free_cell((10, 10))
    assert nf is not None and not w.cell_blocked(nf)


# ------------------------------------------------------------- ızgara hareket
def test_unit_move_ends_on_cell_center():
    w = World()
    u = Unit("spearman", 10, 10)
    w.add_entity(u)
    u.move_to(14, 10)
    for _ in range(200):
        u.update(0.05)
        if u.state_machine.current == "IDLE":
            break
    assert u.cell == (14, 10)
    assert u._settled()  # tam merkezde


def test_walking_unit_halts_at_center_and_attacks():
    """Kutsal kural + Senaryo 1: yürüyen dost birim menzile düşman girince
    en yakın hücre merkezine oturup saldırır."""
    w = World()
    ally = Unit("spearman", 10, 10)
    ally.is_player = True
    w.add_entity(ally)
    ally.move_to(25, 10)
    ally.manual_override = False  # allow auto-acquire in this test
    bm = BattleManager(w)
    for _ in range(15):
        ally.update(0.05)
    enemy = Unit("troll_knife", ally.cell[0] + 1, 10)
    enemy.is_player = False
    w.add_entity(enemy)
    start_hp = enemy.stats.hp
    for _ in range(60):
        ally.update(0.05)
        enemy.update(0.05)
        bm.update(0.05)
    assert ally.state_machine.current == "ATTACK"
    assert ally._settled()           # hücre merkezinde durdu
    assert enemy.stats.hp < start_hp  # saldırdı


def test_worker_gathers_from_adjacent_cell():
    from game.economy import EconomyEngine
    w = World()
    eco = EconomyEngine()
    wk = Worker(10, 10)
    res = ResourceNode("wood", 11, 10, 200)  # adjacent cell
    w.add_entity(wk)
    w.add_entity(res)
    wk.assign_task("gather", res)
    gathered = False
    for _ in range(120):
        wk.update(0.05, w, eco)
        if eco.resources["wood"] > 0:
            gathered = True
            break
    assert gathered
    # toplama anında kaynağa komşu (1 menzil) olmalı
    assert cell_distance(wk.cell, cell_of(res.x, res.y)) <= 1
