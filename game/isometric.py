from game.constants import TILE_WIDTH, TILE_HEIGHT


def world_to_screen(wx, wy, offset_x=0, offset_y=0):
    sx = (wx - wy) * (TILE_WIDTH // 2) + offset_x
    sy = (wx + wy) * (TILE_HEIGHT // 2) + offset_y
    return sx, sy


def screen_to_world(sx, sy, offset_x=0, offset_y=0):
    adj_x = sx - offset_x
    adj_y = sy - offset_y
    wx = (adj_x / (TILE_WIDTH // 2) + adj_y / (TILE_HEIGHT // 2)) / 2
    wy = (adj_y / (TILE_HEIGHT // 2) - adj_x / (TILE_WIDTH // 2)) / 2
    return wx, wy
