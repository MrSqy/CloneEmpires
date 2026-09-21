"""Onaylanan yerleştirme, üretim, hareket ve arayüz kuralları."""
import json
from unittest.mock import patch
import pygame
import pytest
from game.app import GameApp
from game.world import World
from game.economy import EconomyEngine
from game.entities.unit import Unit
from game.entities.worker import Worker
from game.entities.building import Building
from game.entities.resource import ResourceNode
from game.production_queue import ProductionQueue
from game.construction_manager import ConstructionManager
from game.simulation import advance_production
from game.ui import UIManager
from game.xp_system import XPSystem
from game.save_load import SaveManager
from game.camera import Camera
from game.grid import find_path


def simulation():
    pygame.init()
    world, eco = World(), EconomyEngine()
    xp = XPSystem(UIManager(eco))
    return world, eco, xp


def test_upgrade_pauses_preserves_progress_and_ordered_levels():
    app = GameApp()
    app.xp_system.add_xp(100)
    app.world.entities = []
    b = Building('barracks_spear_1', 24, 24)
    app.world.add_entity(b)
    b.production_queue = ProductionQueue(b, app.economy)
    for _ in range(2):
        assert b.production_queue.enqueue('spearman')
    b.production_queue.update(1, app.world)
    app._build_ui_buttons(b)
    next(btn for btn in app.ui.buttons if btn.text == 'Geliştir').callback()
    assert b.production_queue.current_production['level'] == 1
    advance_production(app.world, app.economy, app.xp_system, 4)
    assert b.production_queue.progress == 1
    advance_production(app.world, app.economy, app.xp_system, 8)
    units = [e for e in app.world.entities if isinstance(e, Unit)]
    assert len(units) == 2 and all(u.level == 1 for u in units)
    assert b.production_queue.enqueue('spearman')
    advance_production(app.world, app.economy, app.xp_system, 4)
    assert app.world.entities[-1].level == 2


def test_direct_level2_requires_player_level_and_trains_level2():
    world, eco, xp = simulation()
    cm = ConstructionManager(world, eco)
    assert cm.place_building('barracks_spear_2', 24, 24) is None
    cm.player_level = 2
    b = cm.place_building('barracks_spear_2', 24, 24)
    advance_production(world, eco, xp, 5)
    assert b.stats.level == 2
    b.production_queue.enqueue('spearman')
    advance_production(world, eco, xp, 4)
    assert world.entities[-1].stats.hp == 300


@pytest.mark.parametrize('position', [(48, 24), (-1, 24), (0, 0), (24, 24)])
def test_rejected_placement_does_not_spend(position):
    world, eco, xp = simulation()
    world.add_entity(Building('townhall', 24, 24))
    before = dict(eco.resources)
    assert ConstructionManager(world, eco).place_building('house', *position) is None
    assert eco.resources == before


def test_build_xp_once_and_coordinates_snap():
    app = GameApp()
    app.world.entities = []
    app._enter_build_mode('house')
    app._handle_left_click(app.camera.world_to_screen(24.2, 24.1))
    assert app.xp_system.xp == 0
    assert (app.world.entities[0].x, app.world.entities[0].y) == (24, 24)
    app._update(5)
    assert app.xp_system.xp == 3
    app._update(100)
    assert app.xp_system.xp == 3


def test_no_path_never_crosses_solid_wall():
    world = World()
    u = Unit('spearman', 10, 10)
    world.add_entity(u)
    for y in range(world.height):
        world.add_entity(Building('house', 11, y))
    assert not find_path(u.cell, (12, 10), world.make_blocked(ignore=u))
    u.move_to(12, 10)
    for _ in range(60):
        u.update(.1)
    assert u.cell == (10, 10) and u.movement_error


def test_dynamic_obstacle_replans_without_walking_through():
    world = World()
    u = Unit('spearman', 20, 20)
    world.add_entity(u)
    u.move_to(24, 20)
    wall = Building('house', 21, 20)
    world.add_entity(wall)
    for _ in range(100):
        u.update(.1)
        assert u.cell != (21, 20)
    assert u.cell == (24, 20)


def test_completed_order_waits_for_space_without_refund_or_loss():
    world, eco, xp = simulation()
    b = Building('townhall', 24, 24)
    world.add_entity(b)
    q = ProductionQueue(b, eco)
    q.enqueue('worker')
    paid = dict(eco.resources)
    with patch.object(world, 'nearest_free_cell', return_value=None):
        assert q.update(100, world) is None
        assert q.current_production and q.progress == q.max_progress
    assert eco.resources == paid
    assert isinstance(q.update(0, world), Worker)
    assert q.current_production is None


def test_enemy_commands_and_hidden_worker_selection():
    app = GameApp()
    enemy = Unit('troll_knife', 24, 24)
    enemy.is_player = False
    app.world.entities = []
    app.world.add_entity(enemy)
    app._handle_left_click(app.renderer.entity_screen_rect(enemy).center)
    app._handle_right_click(app.camera.world_to_screen(30, 24))
    assert enemy.state_machine.current == 'IDLE' and not enemy.path
    worker, b = Worker(24, 24), Building('woodcutter', 25, 24)
    app.world.entities = []
    app.world.add_entity(worker)
    app.world.add_entity(b)
    b.assign_worker(worker)
    assert app.renderer.pick_entity_at(app.renderer.entity_screen_rect(b).center, app.world.entities) is b


def test_button_edges_use_event_position():
    world, eco, xp = simulation()
    calls = []
    ui = UIManager(eco)
    ui.add_button(300, 10, 100, 30, 'test', lambda: calls.append(True))
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(301, 621))
    with patch('pygame.mouse.get_pos', return_value=(0, 0)):
        assert ui.handle_event(event)
    assert calls == [True]
    for pos in ((299, 621), (400, 621), (301, 619), (301, 650)):
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)
        assert not ui.handle_event(event)
    assert calls == [True]


@pytest.mark.parametrize('point', [(640, 360), (100, 100), (1100, 600)])
def test_zoom_keeps_world_point_under_cursor(point):
    cam = Camera(1280, 720)
    cam.x, cam.y = 50, 768
    original = cam.screen_to_world(*point)
    for delta in (.1, .3, -1, 5, -.7):
        cam.change_zoom(delta, *point)
        assert cam.screen_to_world(*point) == pytest.approx(original)


def test_production_same_for_all_steps_and_offline_roundtrip():
    totals = []
    for step in (1/60, 1/30, 1, 60):
        world, eco, xp = simulation()
        eco.resources['wood'] = 0
        b = Building('woodcutter', 24, 24)
        b.start_production()
        world.add_entity(b)
        for _ in range(round(60 / step)):
            advance_production(world, eco, xp, step)
        totals.append(eco.resources['wood'])
    assert totals == [int(60**1.05)] * 4


def test_storage_overflow_is_not_paid_again_and_restart_resets_session():
    world, eco, xp = simulation()
    b = Building('woodcutter', 24, 24)
    world.add_entity(b)
    b.start_production()
    eco.resources['wood'] = eco.storage_limit
    advance_production(world, eco, xp, 60)
    eco.resources['wood'] = 0
    advance_production(world, eco, xp, 0)
    assert eco.resources['wood'] == 0
    b.stop_production()
    b.start_production()
    advance_production(world, eco, xp, 1)
    assert eco.resources['wood'] == 1


def test_offline_finishes_paid_jobs_but_does_not_gather_move_or_fight():
    world, eco, xp = simulation()
    b = Building('farm', 24, 24)
    worker = Worker(25, 24)
    b.assign_worker(worker)
    b.start_worker_production('fast', eco)
    townhall = Building('townhall', 26, 26)
    townhall.production_queue = ProductionQueue(townhall, eco)
    for _ in range(3):
        townhall.production_queue.enqueue('worker')
    enemy = Unit('troll_knife', 24, 25)
    enemy.is_player = False
    gatherer = Worker(20, 20)
    node = ResourceNode('wood', 21, 20, 100)
    gatherer.assign_task('gather', node)
    regrowing = ResourceNode('stone', 22, 20, 100)
    regrowing.harvest(100)
    for e in (b, worker, townhall, enemy, gatherer, node, regrowing):
        world.add_entity(e)
    food, gems = eco.resources['food'], eco.resources['gem']
    advance_production(world, eco, xp, 3600)
    assert eco.resources['food'] == food + 10 and eco.resources['gem'] == gems + 2
    assert not b.worker_active and not townhall.production_queue.is_busy()
    assert len([e for e in world.entities if isinstance(e, Worker)]) == 5
    assert (enemy.x, enemy.y) == (24, 25) and enemy.stats.hp == 50
    assert node.amount == 100 and regrowing.amount == 100
    advance_production(world, eco, xp, 3600)
    assert eco.resources['food'] == food + 10


def test_new_obstacle_mid_step_returns_to_safe_cell_and_replans():
    world = World()
    unit = Unit('spearman', 20, 20)
    world.add_entity(unit)
    unit.move_to(24, 20)
    unit.update(.1)
    world.add_entity(Building('house', 21, 20))
    for _ in range(100):
        unit.update(.1)
        assert unit.cell != (21, 20)
    assert unit.cell == (24, 20)


def test_offline_order_matches_small_steps_across_build_and_upgrade():
    snapshots = []
    for step in (.1, 15):
        world, eco, xp = simulation()
        world.created_at = world.processed_at = 1000
        b = Building('barracks_spear_1', 24, 24)
        world.add_entity(b)
        b.production_queue = ProductionQueue(b, eco)
        for _ in range(3):
            b.production_queue.enqueue('spearman')
        b.production_queue.update(1, world)
        b.upgrade('barracks_spear_2')
        for _ in range(round(15 / step)):
            advance_production(world, eco, xp, step)
        snapshots.append(([(u.unit_type, u.level, u.cell) for u in world.entities if isinstance(u, Unit)],
                          xp.level, xp.xp, b.production_queue.progress))
    assert snapshots[0][:-1] == snapshots[1][:-1]
    assert snapshots[0][-1] == pytest.approx(snapshots[1][-1])


def test_worker_build_completion_uses_shared_xp_event_once():
    world, eco, xp = simulation()
    b = Building.create_construction_site('house', 24, 24)
    b.construction_progress = 99
    w = Worker(25, 24)
    for e in (b, w):
        world.add_entity(e)
    w.assign_task('build', b)
    w.update(.1, world, eco)
    assert not b.is_constructed
    advance_production(world, eco, xp, 0)
    assert b.is_constructed and xp.xp == 3
    advance_production(world, eco, xp, 10)
    assert xp.xp == 3


def test_worker_manual_movement_ticks_cooldown_once():
    world = World()
    worker = Worker(24, 24)
    world.add_entity(worker)
    worker.move_to(27, 24)
    worker.attack_cooldown = 1
    worker.update(.1, world, EconomyEngine())
    assert worker.attack_cooldown == pytest.approx(.9)


@pytest.mark.parametrize('kind', ['gather', 'attack'])
def test_unreachable_task_retries_at_bounded_frequency(kind):
    world = World()
    unit = Worker(10, 10) if kind == 'gather' else Unit('spearman', 10, 10)
    target = ResourceNode('wood', 14, 10, 100) if kind == 'gather' else Unit('troll_knife', 14, 10)
    for e in (unit, target):
        world.add_entity(e)
    for y in range(world.height):
        world.add_entity(Building('house', 11, y))
    if kind == 'gather':
        unit.assign_task('gather', target)
    else:
        unit.attack_target(target)
    module = 'worker' if kind == 'gather' else 'unit'
    with patch(f'game.entities.{module}.find_path', wraps=find_path) as search:
        for _ in range(60):
            if kind == 'gather':
                unit.update(.01, world, EconomyEngine())
            else:
                unit.update(.01)
        assert 1 <= search.call_count <= 2
    assert unit.cell == (10, 10) and unit.movement_error
