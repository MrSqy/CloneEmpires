from game.models import EntityState, Position

class BaseEntity:
    def __init__(self, name: str, x: float, y: float):
        self.name = name
        self.state = EntityState(position=Position(x, y))
        self.sprite = None
        self.width = 1.0
        self.height = 1.0
        self.world = None  # World.add_entity bağlar (ızgara pathing için)

    @property
    def x(self):
        return self.state.position.x

    @property
    def y(self):
        return self.state.position.y

    def is_alive(self):
        return self.state.alive
