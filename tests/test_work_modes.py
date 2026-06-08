import math
import pytest
from game.work_modes import (
    gem_cost, duration_seconds, worker_multiplier, resource_gain, gem_reward,
    WORK_MODES, MODE_ORDER,
)
from game.entities.building import Building
from game.entities.worker import Worker
from game.economy import EconomyEngine


# ---------------------------------------------------------------- saf formüller
def test_gem_cost_is_minutes_times_10():
    assert gem_cost("fast") == 20
    assert gem_cost("normal") == 50
    assert gem_cost("long") == 100
    assert gem_cost("marathon") == 300


def test_worker_multiplier_values():
    assert worker_multiplier(1) == 1.0
    assert worker_multiplier(2) == 1.25
    assert worker_multiplier(3) == 1.5
    assert worker_multiplier(4) == 2.0
    assert worker_multiplier(7) == 2.0  # clamp


def test_resource_gain_uses_ceil_and_multiplier():
    assert resource_gain("fast", 1) == 10
    assert resource_gain("fast", 4) == 20
    assert resource_gain("normal", 3) == 45
    assert resource_gain("long", 2) == math.ceil(75 * 1.25)  # 94


def test_gem_reward_ceil_div5():
    assert gem_reward(10) == 2
    assert gem_reward(30) == 6
    assert gem_reward(75) == 15
    assert gem_reward(250) == 50
    assert gem_reward(45) == 9


def test_mode_order_complete():
    assert MODE_ORDER == ["fast", "normal", "long", "marathon"]
    for m in MODE_ORDER:
        assert m in WORK_MODES


# ------------------------------------------------------------- bina entegrasyonu
def test_only_resource_buildings_accept_workers():
    barracks = Building("barracks_spear_1", 0, 0)
    w = Worker(0, 0)
    assert barracks.assign_worker(w) is False

    woodcutter = Building("woodcutter", 0, 0)
    assert woodcutter.assign_worker(w) is True


def test_max_four_workers():
    b = Building("woodcutter", 0, 0)
    workers = [Worker(0, 0) for _ in range(5)]
    results = [b.assign_worker(w) for w in workers]
    assert results == [True, True, True, True, False]
    assert len(b.assigned_workers) == 4


def test_start_production_requires_gems():
    b = Building("gold_mine", 0, 0)
    eco = EconomyEngine()
    eco.resources["gem"] = 0
    b.assign_worker(Worker(0, 0))
    assert b.start_worker_production("fast", eco) is False
    assert b.worker_active is False


def test_full_production_cycle_pays_resources_and_gems():
    b = Building("woodcutter", 0, 0)
    eco = EconomyEngine()
    eco.resources["gem"] = 100
    eco.resources["wood"] = 0
    b.assign_worker(Worker(0, 0))
    b.assign_worker(Worker(0, 0))  # 2 köylü -> ×1.25

    assert b.start_worker_production("fast", eco) is True
    assert eco.resources["gem"] == 80  # 100 - 20 maliyet

    # Süreyi büyük bir dt ile bitir
    reward = b.update_worker_production(10_000, eco)
    assert reward is not None
    expected_wood = resource_gain("fast", 2)  # ceil(10*1.25)=13
    assert eco.resources["wood"] == expected_wood
    assert eco.resources["gem"] == 80 + gem_reward(expected_wood)
    assert b.worker_active is False
    # köylüler serbest
    assert all(w.task is None for w in b.assigned_workers) or b.assigned_workers == []


def test_production_cancelled_if_worker_dies():
    b = Building("farm", 0, 0)
    eco = EconomyEngine()
    eco.resources["gem"] = 100
    eco.resources["food"] = 0
    w = Worker(0, 0)
    b.assign_worker(w)
    b.start_worker_production("normal", eco)

    # köylü ölürse iptal, kısmi ödeme yok
    w.state.alive = False
    reward = b.update_worker_production(1.0, eco)
    assert reward is None
    assert b.worker_active is False
    assert eco.resources["food"] == 0
