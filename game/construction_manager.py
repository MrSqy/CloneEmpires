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
    
    def can_build(self, building_type: str) -> bool:
        cost = BUILDING_COSTS.get(building_type, {})
        return self.economy.can_afford(cost)
    
    def place_building(self, building_type: str, x: float, y: float) -> Building:
        """Place a new building if affordable. Returns the building or None."""
        cost = BUILDING_COSTS.get(building_type, {})
        if not self.economy.spend(cost):
            return None
        
        building = Building.create_construction_site(building_type, x, y, cost=cost)
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
