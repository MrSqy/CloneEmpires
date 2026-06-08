from game.world import World
from game.economy import EconomyEngine
from game.entities.worker import Worker
from game.entities.resource import ResourceNode


def test_worker_gathers_and_delivers():
    world = World()
    economy = EconomyEngine()
    economy.resources["wood"] = 0

    # Köylü kaynağın hemen yanında başlasın
    worker = Worker(10.0, 10.0)
    node = ResourceNode("wood", 11.0, 10.0, initial_amount=100)
    world.add_entity(worker)
    world.add_entity(node)

    worker.assign_task("gather", node)

    # Toplama + teslim döngüsünü simüle et
    for _ in range(600):  # ~6 sn @ dt=0.01
        worker.update(0.01, world, economy)
        if economy.resources["wood"] > 0:
            break

    assert economy.resources["wood"] > 0
    assert node.amount < 100


def test_worker_gather_different_resource_types():
    world = World()
    economy = EconomyEngine()
    for rtype in ("stone", "gold", "food"):
        economy.resources[rtype] = 0
        worker = Worker(20.0, 20.0)
        node = ResourceNode(rtype, 20.5, 20.0, initial_amount=50)
        worker.assign_task("gather", node)
        for _ in range(600):
            worker.update(0.01, world, economy)
            if economy.resources[rtype] > 0:
                break
        assert economy.resources[rtype] > 0
