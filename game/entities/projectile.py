from game.entities.base_entity import BaseEntity


class Projectile(BaseEntity):
    """Homing projectile fired by towers (or units). Follows target until hit."""

    def __init__(self, x: float, y: float, target, speed: float = 10.0,
                 damage: float = 0, source=None):
        super().__init__("arrow", x, y)
        self.target = target
        self.speed = speed
        self.damage = damage
        self.source = source
        self.is_player = True

    def update(self, dt: float):
        if not self.target or not self.target.is_alive():
            self.state.alive = False
            return
        dx = self.target.x - self.state.position.x
        dy = self.target.y - self.state.position.y
        dist = (dx * dx + dy * dy) ** 0.5
        if dist < 0.3:
            self.target.take_damage(self.damage)
            self.state.alive = False
            return
        move = self.speed * dt
        if move >= dist:
            self.target.take_damage(self.damage)
            self.state.alive = False
            return
        self.state.position.x += (dx / dist) * move
        self.state.position.y += (dy / dist) * move
