import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from game.camera import Camera
from game.renderer import Renderer
from game.entities.unit import Unit
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT


@pytest.fixture(scope="module")
def renderer():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    cam = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
    return Renderer(screen, cam)


def test_pick_at_entity_center(renderer):
    u = Unit("spearman", 10, 10)
    rect = renderer.entity_screen_rect(u)
    picked = renderer.pick_entity_at(rect.center, [u])
    assert picked is u


def test_pick_misses_when_far(renderer):
    u = Unit("spearman", 10, 10)
    rect = renderer.entity_screen_rect(u)
    far = (rect.center[0] + 500, rect.center[1] + 500)
    assert renderer.pick_entity_at(far, [u]) is None


def test_pick_returns_front_entity(renderer):
    back = Unit("spearman", 10, 10)
    front = Unit("archer", 10.0, 10.5)  # daha büyük y -> önde
    # Aynı ekran noktasına yakın olacak şekilde örtüşsünler
    rect = renderer.entity_screen_rect(front)
    picked = renderer.pick_entity_at(rect.center, [back, front])
    assert picked is front


def test_dead_entity_not_picked(renderer):
    u = Unit("spearman", 10, 10)
    u.state.alive = False
    rect = renderer.entity_screen_rect(u)
    assert renderer.pick_entity_at(rect.center, [u]) is None
