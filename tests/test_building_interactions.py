import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest

from game.app import GameApp
from game.entities.building import Building
from game.entities.worker import Worker


@pytest.fixture
def app():
    a = GameApp()
    yield a


def test_townhall_trains_only_workers(app):
    townhall = next(e for e in app.world.entities
                    if isinstance(e, Building) and e.building_type == "townhall")
    app._build_ui_buttons(townhall)
    labels = [b.text for b in app.ui.buttons]
    assert labels == ["İşçi"]  # sadece köylü, asker yok


def test_right_click_assigns_worker_to_resource_building(app):
    worker = next(e for e in app.world.entities if isinstance(e, Worker))
    building = Building("woodcutter", worker.x + 1, worker.y + 1)
    app.world.add_entity(building)

    app.selection.select_single(worker)
    rect = app.renderer.entity_screen_rect(building)
    app._handle_right_click(rect.center)

    assert worker in building.assigned_workers
    assert worker.task == "working"


def test_right_click_empty_ground_moves_worker(app):
    worker = next(e for e in app.world.entities if isinstance(e, Worker))
    app.selection.select_single(worker)
    # boş zemine (hiçbir entity olmayan ekran köşesi) sağ tık
    app._handle_right_click((5, 5))
    assert worker.task is None
    assert worker.state_machine.current == "MOVE"
