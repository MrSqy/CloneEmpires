"""Açık/kapalı oyunun ortak üretim saati; hareket ve savaşı ilerletmez."""
from game.entities.building import Building
from game.entities.resource import ResourceNode
from game.production_queue import ProductionQueue
from game.building_catalog import get_base

EPSILON = 1e-9


def _next_boundary(world, remaining):
    """Sonraki tamamlanma olayına kadar süreyi hesaplar; kare döngüsü kurmaz."""
    durations = [remaining]
    for b in world.entities:
        if not isinstance(b, Building) or not b.is_alive():
            continue
        if not b.is_constructed:
            durations.append(max(EPSILON, (100 - b.construction_progress) * b.build_time / 100))
            continue
        if b.worker_active and b.worker_timer > EPSILON:
            durations.append(b.worker_timer)
        queue = getattr(b, 'production_queue', None)
        if queue:
            if queue.current_production:
                duration = queue.max_progress - queue.progress
            elif queue.queue:
                duration = queue.queue[0]['train_time']
            else:
                continue
            if duration > EPSILON:
                durations.append(duration)
    return min(durations)


def _segment(world, economy, xp, dt):
    """Bir olay aralığını işler; tamamlanma ödüllerini burada tek kez verir."""
    for entity in list(world.entities):
        if not entity.is_alive():
            continue
        if isinstance(entity, ResourceNode):
            entity.update(dt)
        if not isinstance(entity, Building):
            continue
        if not entity.is_constructed:
            entity.construction_progress = min(100.0, entity.construction_progress + dt * 100 / entity.build_time)
            if entity.construction_progress >= 100 - EPSILON:
                entity.construction_progress = 100.0
                entity.is_constructed = True
                if get_base(entity.building_type) == 'barracks' and not hasattr(entity, 'production_queue'):
                    entity.production_queue = ProductionQueue(entity, economy)
                xp.reward_building_constructed(entity.building_type)
            continue  # İnşaatın kullandığı süre üretime tekrar verilmez.
        entity.update(dt, economy)
        if entity.update_worker_production(dt, economy):
            xp.reward_work_completed(entity.building_type)
        queue = getattr(entity, 'production_queue', None)
        if queue:
            queue.update(dt, world)
            for unit in queue.last_spawned:
                xp.reward_unit_trained(unit.unit_type)


def advance_production(world, economy, xp, duration):
    """Geçen süreyi olay sınırlarına böler; aynı API çevrimdışı da kullanılır."""
    remaining = max(0.0, duration)
    _segment(world, economy, xp, 0.0)
    while remaining > EPSILON:
        step = _next_boundary(world, remaining)
        _segment(world, economy, xp, step)
        remaining = max(0.0, remaining - step)
