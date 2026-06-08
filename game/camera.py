from game.constants import MIN_ZOOM, MAX_ZOOM


class Camera:
    def __init__(self, screen_width, screen_height):
        self.x = 0
        self.y = 0
        self.zoom = 1.0
        self.sw = screen_width
        self.sh = screen_height

    def pan(self, dx, dy):
        self.x += dx
        self.y += dy

    def change_zoom(self, delta, mouse_x, mouse_y):
        old_zoom = self.zoom
        self.zoom = max(MIN_ZOOM, min(MAX_ZOOM, self.zoom + delta))
        if self.zoom != old_zoom:
            factor = self.zoom / old_zoom
            self.x = mouse_x - (mouse_x - self.x) * factor
            self.y = mouse_y - (mouse_y - self.y) * factor

    def world_to_screen(self, wx, wy):
        from game.isometric import world_to_screen as w2s
        sx, sy = w2s(wx, wy)
        sx = (sx - self.x) * self.zoom + self.sw // 2
        sy = (sy - self.y) * self.zoom + self.sh // 2
        return sx, sy

    def screen_to_world(self, sx, sy):
        from game.isometric import screen_to_world as s2w
        adj_x = (sx - self.sw // 2) / self.zoom + self.x
        adj_y = (sy - self.sh // 2) / self.zoom + self.y
        return s2w(adj_x, adj_y)
