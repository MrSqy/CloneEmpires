"""Kayıt bütünlüğü, dosya hataları ve dünyalar arası yalıtım."""
import copy
import json
from pathlib import Path
from unittest.mock import patch
import pytest

from game.app import GameApp
from game.save_load import SaveManager, SaveError, LegacySaveError
from game.world import World
from game.economy import EconomyEngine
from game.entities.worker import Worker
from game.entities.unit import Unit
from game.entities.building import Building
from game.entities.resource import ResourceNode
from game.entities.projectile import Projectile
from game.production_queue import ProductionQueue


def rich_world():
    world, economy = World(), EconomyEngine()
    world.created_at = world.processed_at = 1000
    worker = Worker(24, 25)
    enemy = Unit('troll_knife', 30, 30)
    enemy.is_player = False
    worker.assign_task('gather', ResourceNode('wood', 25, 25, 100))
    worker.gather_timer = .75
    tower = Building('arrow_tower_1', 20, 20)
    tower.take_damage(300)
    resource = worker.task_target
    resource.harvest(100)
    resource.update(5)
    site = Building.create_construction_site('house', 22, 22)
    site.construction_progress = 40
    barracks = Building('barracks_spear_2', 23, 23)
    barracks.production_queue = ProductionQueue(barracks, economy)
    barracks.production_queue.enqueue('spearman')
    barracks.production_queue.update(1, world)
    inside = Worker(24, 26)
    wood = Building('woodcutter', 26, 26)
    wood.assign_worker(inside)
    wood.start_worker_production('fast', economy)
    wood.start_production()
    wood.update(2.5, economy)
    projectile = Projectile(29, 29, enemy, damage=18, source=tower)
    for e in [worker, enemy, tower, resource, site, barracks, inside, wood, projectile]:
        world.add_entity(e)
    economy.upgrade_storage()
    return world, economy


def test_full_roundtrip_preserves_types_relations_and_timers():
    manager = SaveManager()
    world, eco = rich_world()
    data = manager.serialize(world, eco, 'Kral', 2, 42, saved_at=1000,
                             camera={'x': 5, 'y': 768, 'zoom': 1.5})
    loaded, loaded_eco, meta = manager.restore(json.loads(json.dumps(data)))
    again = manager.serialize(loaded, loaded_eco, meta['king_name'], 2, 42,
                              camera=meta['camera'], xp_state=meta['xp_state'], saved_at=1000)
    assert data == again
    wk, enemy, tower, resource, site, bar, inside, wood, projectile = loaded.entities
    assert type(wk) is Worker and not enemy.is_player
    assert wk.task_target is resource and inside.is_inside_building is wood
    assert wood.assigned_workers == [inside]
    assert projectile.target is enemy and projectile.source is tower
    assert loaded_eco.storage_limit == 50500
    assert tower.tower_disabled and not site.is_constructed
    resource.update(25)
    assert resource.amount == 100


@pytest.mark.parametrize('break_data', [
    lambda d: d.pop('entities'),
    lambda d: d['entities'][0]['refs'].update(task_target='a' * 32),
    lambda d: d['entities'].append(copy.deepcopy(d['entities'][0])),
    lambda d: d['resources'].update(wood=-1),
    lambda d: d['camera'].update(zoom=float('nan')),
    lambda d: d['entities'][0]['stats'].update(attack_speed=0),
    lambda d: d['entities'][7].update(workers=[]),
    lambda d: d.update(xp_state={}),
    lambda d: d['entities'][0]['fields'].update(path=[[100, 24]]),
    lambda d: d['entities'][0]['fields'].update(path=[[24.5, 24]]),
])
def test_invalid_snapshot_does_not_mutate_existing_world(break_data):
    manager = SaveManager()
    world, eco = rich_world()
    data = manager.serialize(world, eco, 'Kral', 1, saved_at=1000)
    break_data(data)
    target, target_eco = World(), EconomyEngine()
    existing = Unit('archer', 10, 10)
    target.add_entity(existing)
    with pytest.raises(SaveError):
        manager.deserialize(data, target, target_eco)
    assert target.entities == [existing] and target_eco.resources['wood'] == 10000


def test_snapshot_does_not_alias_live_resources():
    manager = SaveManager()
    world, eco = rich_world()
    data = manager.serialize(world, eco, 'Kral', 1)
    old = data['resources']['wood']
    eco.resources['wood'] += 10
    assert data['resources']['wood'] == old


def test_atomic_failure_keeps_main_and_valid_backup(monkeypatch):
    manager = SaveManager()
    world, eco = rich_world()
    data = manager.serialize(world, eco, 'Kral', 1)
    manager.save_world(data)
    filename = world.world_id + '.json'
    old = manager._path(filename).read_bytes()
    data['resources']['wood'] += 1
    real_replace = __import__('os').replace
    def fail_main(src, dst):
        if Path(dst).name == filename:
            raise OSError('disk test failure')
        real_replace(src, dst)
    monkeypatch.setattr('game.save_load.os.replace', fail_main)
    with pytest.raises(OSError):
        manager.save_world(data)
    assert manager._path(filename).read_bytes() == old
    assert manager.load_from_file(filename + '.bak')['world_id'] == world.world_id
    assert not list(manager.save_dir.glob('.save-*'))


def test_legacy_and_broken_records_do_not_hide_other_worlds():
    manager = SaveManager()
    (manager.save_dir / 'autosave.json').write_text('{"resources": {"wood": 100}}')
    (manager.save_dir / 'broken.json').write_text('{')
    world, eco = rich_world()
    manager.save_world(manager.serialize(world, eco, 'Kral', 1))
    records = manager.list_worlds()
    assert len(records) == 3 and sum(not r['error'] for r in records) == 1
    with pytest.raises(LegacySaveError):
        manager.load_from_file('autosave.json')
    assert (manager.save_dir / 'autosave.json').exists()


def test_menu_does_not_overwrite_and_worlds_are_independent():
    now = [1000.0]
    app = GameApp(time_source=lambda: now[0])
    assert app.screen_mode == 'home' and not app.active_session
    app._autosave(100)
    assert not list(app.save_manager.save_dir.glob('*.json'))
    app.new_game('Birinci')
    first = app.world.world_id + '.json'
    app.economy.resources['wood'] = 321
    app._autosave(29)
    assert app.save_manager.load_from_file(first)['resources']['wood'] == 10000
    app._autosave(1)
    assert app.save_manager.load_from_file(first)['resources']['wood'] == 321
    before = app.save_manager._path(first).read_bytes()
    app.request_exit('home')
    app.new_game('İkinci')
    assert app.save_manager._path(first).read_bytes() == before
    assert app.load_game(first)
    assert app.world.name == 'Birinci' and app.economy.resources['wood'] == 321


def test_offline_gain_applies_once_and_backward_clock_does_not_repeat():
    now = [1000.0]
    app = GameApp(time_source=lambda: now[0])
    app.new_game('Test')
    b = Building('woodcutter', 20, 20)
    b.start_production()
    app.world.add_entity(b)
    app.economy.resources['wood'] = 0
    app.save_game()
    filename = app.world.world_id + '.json'
    now[0] += 60
    assert app.load_game(filename)
    earned = app.economy.resources['wood']
    assert earned == int(60 ** 1.05)
    assert app.load_game(filename) and app.economy.resources['wood'] == earned
    now[0] -= 30
    assert app.load_game(filename) and app.world.processed_at == 1060
    now[0] = 1060
    assert app.load_game(filename) and app.economy.resources['wood'] == earned


def test_failed_load_commit_keeps_active_session(monkeypatch):
    now = [1000.0]
    app = GameApp(time_source=lambda: now[0])
    app.new_game('İlk')
    filename = app.world.world_id + '.json'
    old = app.world
    monkeypatch.setattr(app.save_manager, 'save_world', lambda d: (_ for _ in ()).throw(OSError('disk')))
    now[0] += 100
    assert not app.load_game(filename)
    assert app.world is old


def test_exit_failure_requires_explicit_choice_and_backup_can_recover(monkeypatch):
    app = GameApp()
    app.new_game('Test')
    app.save_game()
    filename = app.world.world_id + '.json'
    app.save_manager._path(filename).write_text('{')
    assert app.load_game(filename, backup=True)
    with patch.object(app.save_manager, 'save_world', side_effect=OSError('disk')):
        app.request_exit('quit')
    assert app.running and app.screen_mode == 'save_error' and app.active_session
    app._menu_action('resume')
    assert app.screen_mode == 'game'
    app.request_exit('quit')
    assert not app.running


def test_save_error_retry_counts_waiting_production_once():
    app = GameApp()
    app.new_game('Test')
    b = Building('woodcutter', 20, 20)
    b.start_production()
    app.world.add_entity(b)
    app.economy.resources['wood'] = 0
    with patch.object(app.save_manager, 'save_world', side_effect=OSError('disk')):
        app.request_exit('home')
    app._error_elapsed = 10
    app._menu_action('retry')
    assert app.screen_mode == 'home'
    data = app.save_manager.load_from_file(app.world.world_id + '.json')
    assert data['resources']['wood'] == int(10**1.05)


def test_menu_name_unicode_and_click_flow():
    app = GameApp()
    app.menu.draw(app.screen, 'home', [])
    event = __import__('pygame').event.Event(__import__('pygame').MOUSEBUTTONDOWN,
                                            button=1, pos=(600, 250))
    app._menu_action(app.menu.handle_event(event, 'home'))
    assert app.screen_mode == 'new'
    event = __import__('pygame').event.Event(__import__('pygame').TEXTINPUT, text='Türkçe Dünya')
    app.menu.handle_event(event, 'new')
    app._menu_action('create')
    assert app.world.name == 'Türkçe Dünya'
    app.request_exit('home')
    app._menu_action('load')
    app.menu.draw(app.screen, 'load', app.records)
    event = __import__('pygame').event.Event(__import__('pygame').MOUSEBUTTONDOWN,
                                            button=1, pos=(1100, 150))
    app._menu_action(app.menu.handle_event(event, 'load'))
    assert app.screen_mode == 'game' and app.world.name == 'Türkçe Dünya'


def test_uncreatable_save_directory_keeps_game_playable(tmp_path):
    from game.app import GameApp
    obstacle = tmp_path / 'file'
    obstacle.write_text('preserve')
    app = GameApp(save_dir=obstacle / 'saves')
    assert app.screen_mode == 'home'
    app.new_game('Bellekte')
    assert app.active_session and app.screen_mode == 'game'
    assert 'Kayıt başarısız' in app.message
    app.request_exit('home')
    assert app.screen_mode == 'save_error' and app.active_session
    assert obstacle.read_text() == 'preserve'
