from typing import Dict, List, Tuple
from game.entities.building import Building
from game.building_catalog import CATALOG

# Maliyetler katalogdan türetilir; legacy anahtarlar geriye dönük uyumluluk için korunur.
BUILDING_COSTS = {bt: dict(meta["cost"]) for bt, meta in CATALOG.items()}
BUILDING_COSTS.setdefault("barracks", {"wood": 100, "stone": 50})
BUILDING_COSTS.setdefault("storage", {"wood": 50, "stone": 30})

class ConstructionManager:
    """Manages building placement and construction costs."""

    def __init__(self, world, economy):
        self.world = world
        self.economy = economy
        self.pending_constructions: List[Building] = []
        self.player_level = 1
        self.last_error = ""

    def can_build(self, building_type: str) -> bool:
        meta = CATALOG.get(building_type)
        if meta is None:
            self.last_error = "Bilinmeyen bina."
        elif self.player_level < meta.get("level_req", 1):
            self.last_error = "Oyuncu seviyesi yetersiz."
        elif not self.economy.can_afford(meta["cost"]):
            self.last_error = "Kaynak yetersiz."
        else:
            self.last_error = ""
            return True
        return False

    def placement_error(self, building_type, x, y):
        """Ödeme yapmadan tür, seviye, maliyet, sınır ve doluluğu kontrol eder."""
        from game.grid import cell_of
        if not self.can_build(building_type):
            return self.last_error
        gx, gy = cell_of(x, y)
        if not (0 <= gx < self.world.width and 0 <= gy < self.world.height):
            return "Harita dışına inşa edilemez."
        if self.world.tiles[gx][gy] != "safe":
            return "Yalnız yeşil bölgeye inşa edilebilir."
        if self.world.cell_blocked((gx, gy)):
            return "Bu hücre dolu."
        return ""

    def place_building(self, building_type: str, x: float, y: float):
        from game.grid import cell_of
        self.last_error = self.placement_error(building_type, x, y)
        if self.last_error:
            return None
        cost = BUILDING_COSTS[building_type]
        if not self.economy.spend(cost):
            return None
        building = Building.create_construction_site(building_type, *cell_of(x, y), cost=dict(cost))
        self.world.add_entity(building)
        self.pending_constructions.append(building)
        return building

    def get_available_buildings(self) -> List[str]:
        """Return list of building types that can be afforded."""
        return [bt for bt in BUILDING_COSTS if self.can_build(bt)]

    def update(self, dt: float):
        """Clean up finished constructions."""
        self.pending_constructions = [b for b in self.pending_constructions
                                      if b.is_alive() and not b.is_constructed]

    def get_cost(self, building_type: str) -> Dict[str, int]:
        return BUILDING_COSTS.get(building_type, {}).copy()
