from game.entities.base_entity import BaseEntity

class ResourceNode(BaseEntity):
    def __init__(self, resource_type: str, x: float, y: float, initial_amount: float = 500):
        super().__init__(f"{resource_type}_node", x, y)
        self.resource_type = resource_type
        self.amount = initial_amount
        self.max_amount = initial_amount

        # Regeneration state
        self.respawn_time = 30.0  # Total time to fully regrow
        self.regrowth_timer = 0.0  # Counts down during regrowth
        self.regrowth_phase = 2    # 0=stump, 1=sapling, 2=full

    def harvest(self, amount: float) -> float:
        """Harvest resources. Returns actual amount harvested."""
        actual = min(amount, self.amount)
        self.amount -= actual
        if self.amount <= 0:
            self.amount = 0
            # Start regrowth instead of dying
            self.regrowth_timer = self.respawn_time
            self.regrowth_phase = 0
        return actual

    def is_depleted(self):
        """Returns True if currently depleted (regrowing or empty)."""
        return self.amount <= 0

    def can_be_harvested(self):
        """Returns True if resource has amount > 0 and is full."""
        return self.amount > 0 and self.regrowth_phase == 2

    def update(self, dt: float):
        """Process regrowth over time."""
        if self.amount > 0:
            return  # Only regrow when depleted

        if self.regrowth_timer > 0:
            self.regrowth_timer -= dt
            # Phase transitions
            if self.regrowth_timer <= self.respawn_time / 2 and self.regrowth_phase == 0:
                self.regrowth_phase = 1  # stump -> sapling at halfway
            if self.regrowth_timer <= 0:
                self.regrowth_timer = 0
                self.amount = self.max_amount
                self.regrowth_phase = 2  # fully regrown
