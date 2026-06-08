from game.isometric import world_to_screen, screen_to_world
from game.constants import TILE_WIDTH, TILE_HEIGHT


def test_world_to_screen_origin():
    sx, sy = world_to_screen(0, 0)
    assert sx == 0
    assert sy == 0


def test_world_to_screen_roundtrip():
    wx, wy = 5, 3
    sx, sy = world_to_screen(wx, wy)
    rx, ry = screen_to_world(sx, sy)
    assert abs(rx - wx) < 0.01
    assert abs(ry - wy) < 0.01
