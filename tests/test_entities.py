from game.entities.base_entity import BaseEntity
from game.entities.resource import ResourceNode
from game.entities.building import Building
from game.entities.unit import Unit

def test_base_entity_creation():
    e = BaseEntity("test", 5, 5)
    assert e.name == "test"
    assert e.state.position.x == 5

def test_resource_node_amount():
    r = ResourceNode("wood", 10, 10, initial_amount=100)
    assert r.resource_type == "wood"
    assert r.amount == 100
    r.harvest(20)
    assert r.amount == 80

def test_building_cost():
    b = Building("barracks", 5, 5, cost={"wood": 100, "stone": 50})
    assert b.cost["wood"] == 100
    assert b.can_upgrade({"wood": 200, "stone": 100})

def test_unit_take_damage():
    u = Unit("spearman", 0, 0)
    start_hp = u.stats.hp
    u.take_damage(20)
    assert u.stats.hp == start_hp - 20

def test_unit_state_machine():
    u = Unit("archer", 0, 0)
    assert u.state_machine.current == "IDLE"
    u.state_machine.transition("MOVE")
    assert u.state_machine.current == "MOVE"
