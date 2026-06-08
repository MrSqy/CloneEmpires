import json
import os
from typing import Dict, Any
from game.world import World
from game.economy import EconomyEngine
from game.entities.unit import Unit
from game.entities.building import Building
from game.entities.resource import ResourceNode


class SaveManager:
    SAVE_DIR = "saves"

    def __init__(self):
        os.makedirs(self.SAVE_DIR, exist_ok=True)

    def serialize(self, world: World, economy: EconomyEngine,
                  king_name: str, level: int, xp: int = 0) -> Dict[str, Any]:
        entities_data = []
        for e in world.entities:
            ed = {"name": e.name, "x": e.x, "y": e.y, "alive": e.is_alive()}
            if isinstance(e, Unit):
                ed["type"] = "unit"
                ed["unit_type"] = e.unit_type
                ed["level"] = e.level
                ed["hp"] = e.stats.hp
            elif isinstance(e, Building):
                ed["type"] = "building"
                ed["building_type"] = e.building_type
                ed["level"] = e.stats.level
            elif isinstance(e, ResourceNode):
                ed["type"] = "resource"
                ed["resource_type"] = e.resource_type
                ed["amount"] = e.amount
            entities_data.append(ed)

        return {
            "king_name": king_name,
            "townhall_level": level,
            "xp": xp,
            "resources": economy.resources,
            "storage_level": economy.storage_level,
            "entities": entities_data,
        }

    def deserialize(self, data: Dict[str, Any], world: World, economy: EconomyEngine):
        economy.resources.update(data.get("resources", {}))
        economy.storage_level = data.get("storage_level", 0)

        for ed in data.get("entities", []):
            etype = ed.get("type")
            if etype == "unit":
                u = Unit(ed["unit_type"], ed["x"], ed["y"], level=ed.get("level", 1))
                u.stats.hp = ed.get("hp", u.stats.max_hp)
                if not ed.get("alive", True):
                    u.state.alive = False
                world.add_entity(u)
            elif etype == "building":
                b = Building(ed["building_type"], ed["x"], ed["y"])
                b.stats.level = ed.get("level", 1)
                world.add_entity(b)
            elif etype == "resource":
                r = ResourceNode(ed["resource_type"], ed["x"], ed["y"], ed.get("amount", 100))
                world.add_entity(r)

    def save_to_file(self, filename: str, data: Dict[str, Any]):
        path = os.path.join(self.SAVE_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_from_file(self, filename: str) -> Dict[str, Any]:
        path = os.path.join(self.SAVE_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
