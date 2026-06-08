from game.save_load import SaveManager
from game.world import World
from game.economy import EconomyEngine
from game.entities.unit import Unit


def test_save_and_load():
    world = World()
    economy = EconomyEngine()
    world.add_entity(Unit("spearman", 10, 10))
    economy.resources["wood"] = 999

    manager = SaveManager()
    data = manager.serialize(world, economy, king_name="Test", level=2)
    assert data["king_name"] == "Test"
    assert data["townhall_level"] == 2
    assert len(data["entities"]) == 1

    world2 = World()
    economy2 = EconomyEngine()
    manager.deserialize(data, world2, economy2)
    assert economy2.resources["wood"] == 999
    assert len(world2.entities) == 1
