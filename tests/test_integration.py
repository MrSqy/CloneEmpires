import pytest
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
import pygame
pygame.init()

from game.world import World
from game.economy import EconomyEngine
from game.ui import UIManager
from game.entities.unit import Unit
from game.entities.building import Building
from game.entities.worker import Worker
from game.entities.resource import ResourceNode
from game.battle_manager import BattleManager
from game.xp_system import XPSystem
from game.construction_manager import ConstructionManager
from game.production_queue import ProductionQueue


class TestUnitMovementAndAttack:
    def test_unit_move_to(self):
        unit = Unit("spearman", 0, 0)
        unit.move_to(10, 0)
        assert unit.state_machine.current == "MOVE"
        assert unit.target_pos == (10, 0)

    def test_unit_attack_target(self):
        attacker = Unit("spearman", 0, 0)
        target = Unit("troll", 5, 0)
        attacker.attack_target(target)
        assert attacker.state_machine.current == "ATTACK"
        assert attacker.target == target

    def test_unit_movement(self):
        unit = Unit("spearman", 0, 0)
        unit.move_to(3, 0)
        for _ in range(120):
            unit.update(1 / 60.0)
        assert unit.x > 2.5

    def test_combat_damage(self):
        attacker = Unit("spearman", 0, 0)
        target = Unit("troll", 0.5, 0)
        attacker.attack_target(target)
        world = World()
        world.add_entity(attacker)
        world.add_entity(target)
        bm = BattleManager(world)
        for _ in range(120):
            attacker.update(1 / 60.0)
            bm.update(1 / 60.0)
        assert target.stats.hp < 100.0

    def test_unit_death(self):
        unit = Unit("spearman", 0, 0)
        unit.take_damage(150)
        assert unit.stats.hp == 0
        assert not unit.is_alive()
        assert unit.state_machine.current == "DEAD"


class TestWorkerSystem:
    def test_worker_creation(self):
        w = Worker(5, 5)
        assert w.unit_type == "worker"
        assert w.stats.move_speed == 3.0

    def test_worker_assign_task(self):
        w = Worker(5, 5)
        node = ResourceNode("wood", 10, 10, 100)
        w.assign_task("gather", node)
        assert w.task == "gather"
        assert w.state_machine.current == "MOVE"

    def test_worker_update_without_args(self):
        w = Worker(5, 5)
        w.update(1 / 60.0)

    def test_worker_gather_deliver(self):
        from game.world import World
        economy = EconomyEngine()
        w = Worker(5, 5)
        node = ResourceNode("wood", 5.5, 5.5, 100)
        world = World()
        world.add_entity(w)
        world.add_entity(node)
        w.assign_task("gather", node)
        for _ in range(300):
            w.update(1 / 60.0, world, economy)
        assert economy.resources["wood"] > 0 or w.task is None


class TestProductionQueue:
    def test_enqueue_worker(self):
        economy = EconomyEngine()
        for r in economy.resources:
            economy.resources[r] = 1000
        th = Building("townhall", 10, 10)
        pq = ProductionQueue(th, economy)
        assert pq.enqueue("worker") is True
        pq.update(0, World())  # Move from queue to current
        assert pq.current_production is not None

    def test_production_completion(self):
        economy = EconomyEngine()
        for r in economy.resources:
            economy.resources[r] = 1000
        th = Building("townhall", 10, 10)
        pq = ProductionQueue(th, economy)
        pq.enqueue("worker")
        world = World()
        new_unit = pq.update(10.0, world)
        assert new_unit is not None
        assert isinstance(new_unit, Unit)

    def test_cancel_refund(self):
        economy = EconomyEngine()
        economy.storage_limit = 2000
        for r in economy.resources:
            economy.resources[r] = 1000
        th = Building("townhall", 10, 10)
        pq = ProductionQueue(th, economy)
        before = economy.resources["food"]
        pq.enqueue("worker")
        pq.update(0, World())  # Move from queue to current
        pq.cancel_current()
        assert economy.resources["food"] == before


class TestXPSystem:
    def test_add_xp(self):
        ui = UIManager(EconomyEngine())
        xp = XPSystem(ui)
        xp.add_xp(50)
        assert xp.xp == 50
        assert xp.level == 1

    def test_level_up(self):
        ui = UIManager(EconomyEngine())
        xp = XPSystem(ui)
        xp.add_xp(150)
        assert xp.level == 2
        assert xp.max_xp == 150

    def test_reward_kill(self):
        ui = UIManager(EconomyEngine())
        xp = XPSystem(ui)
        xp.reward_kill("troll_knife")
        assert xp.xp > 0

    def test_reward_building(self):
        ui = UIManager(EconomyEngine())
        xp = XPSystem(ui)
        xp.reward_building_constructed("woodcutter")
        assert xp.xp > 0


class TestConstructionManager:
    def test_can_build(self):
        economy = EconomyEngine()
        for r in economy.resources:
            economy.resources[r] = 1000
        world = World()
        cm = ConstructionManager(world, economy)
        assert cm.can_build("woodcutter") is True

    def test_place_building(self):
        economy = EconomyEngine()
        for r in economy.resources:
            economy.resources[r] = 1000
        world = World()
        cm = ConstructionManager(world, economy)
        b = cm.place_building("woodcutter", 10, 10)
        assert b is not None
        assert b.building_type == "woodcutter"
        assert b.is_constructed is False
        assert b.construction_progress == 0.0

    def test_insufficient_funds(self):
        economy = EconomyEngine()
        for r in economy.resources:
            economy.resources[r] = 0
        world = World()
        cm = ConstructionManager(world, economy)
        assert cm.can_build("woodcutter") is False
        b = cm.place_building("woodcutter", 10, 10)
        assert b is None


class TestBuildingProduction:
    def test_resource_building_production(self):
        economy = EconomyEngine()
        b = Building("woodcutter", 0, 0)
        b.is_producing = True
        b.stats.production_rate = 10.0
        initial_wood = economy.resources["wood"]
        b.update(5.0, economy)
        assert economy.resources["wood"] > initial_wood

    def test_non_resource_building_no_production(self):
        economy = EconomyEngine()
        b = Building("barracks", 0, 0)
        b.is_producing = True
        initial_wood = economy.resources["wood"]
        b.update(5.0, economy)
        assert economy.resources["wood"] == initial_wood


class TestBattleManager:
    def test_find_closest_enemy(self):
        world = World()
        player = Unit("spearman", 0, 0)
        enemy1 = Unit("troll", 5, 0)
        enemy2 = Unit("troll", 10, 0)
        enemy1.is_player = False
        enemy2.is_player = False
        world.add_entity(player)
        world.add_entity(enemy1)
        world.add_entity(enemy2)
        bm = BattleManager(world)
        closest = bm.find_closest_enemy(player)
        assert closest == enemy1

    def test_get_enemies_in_range(self):
        world = World()
        player = Unit("spearman", 0, 0)
        enemy = Unit("troll", 3, 0)
        enemy.is_player = False
        world.add_entity(player)
        world.add_entity(enemy)
        bm = BattleManager(world)
        enemies = bm.get_enemies_in_range(player, radius=5.0)
        assert len(enemies) == 1

    def test_battle_manager_damage(self):
        world = World()
        attacker = Unit("spearman", 0, 0)
        target = Unit("troll", 0.5, 0)
        attacker.attack_target(target)
        world.add_entity(attacker)
        world.add_entity(target)
        bm = BattleManager(world)
        initial_hp = target.stats.hp
        for _ in range(120):
            attacker.update(1 / 60.0)
            bm.update(1 / 60.0)
        assert target.stats.hp < initial_hp
