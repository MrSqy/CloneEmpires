from game.world import World
from game.entities.unit import Unit
from game.entities.building import Building


def test_world_creation():
    w = World()
    assert w.width == 48
    assert w.height == 48


def test_add_entity():
    w = World()
    u = Unit("spearman", 10, 10)
    w.add_entity(u)
    assert len(w.entities) == 1


def test_get_entities_in_range():
    w = World()
    w.add_entity(Unit("a", 10, 10))
    w.add_entity(Unit("b", 12, 10))
    result = w.get_entities_in_range(10, 10, 3)
    assert len(result) == 2
