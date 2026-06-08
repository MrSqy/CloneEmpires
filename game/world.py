from collections import deque
from typing import List, Optional
from game.constants import MAP_WIDTH, MAP_HEIGHT
from game.entities.base_entity import BaseEntity
from game.grid import cell_of


class World:
    def __init__(self):
        self.width = MAP_WIDTH
        self.height = MAP_HEIGHT
        self.entities: List[BaseEntity] = []
        self.tiles = [["grass" for _ in range(self.height)] for _ in range(self.width)]
        self.player_base_center = (MAP_WIDTH // 2, MAP_HEIGHT // 2)
        self._setup_zones()

    def _setup_zones(self):
        from game.constants import SAFE_ZONE_CENTER, NEUTRAL_ZONE_CENTER
        cx, cy = self.player_base_center
        for x in range(self.width):
            for y in range(self.height):
                dx = abs(x - cx)
                dy = abs(y - cy)
                dist = max(dx, dy)
                if dist > NEUTRAL_ZONE_CENTER // 2:
                    self.tiles[x][y] = "danger"
                elif dist > SAFE_ZONE_CENTER // 2:
                    self.tiles[x][y] = "neutral"
                else:
                    self.tiles[x][y] = "safe"

    # ----------------------------------------------------------- hücre işgali
    def occupied_cells(self, ignore=None, include_units=True):
        """Dolu hücrelerin kümesi. Binalar ve kaynaklar daima engel; birimler
        opsiyonel (yol planlarken kendi aralarında üst üste binmesinler)."""
        cells = set()
        for e in self.entities:
            if e is ignore or not e.is_alive():
                continue
            if hasattr(e, 'building_type') or hasattr(e, 'resource_type'):
                cells.add(cell_of(e.x, e.y))
            elif include_units and hasattr(e, 'unit_type'):
                cells.add(cell_of(e.x, e.y))
        return cells

    def make_blocked(self, ignore=None, include_units=True):
        """A* için engel fonksiyonu: sınır dışı veya dolu hücre -> True."""
        occ = self.occupied_cells(ignore, include_units)
        w, h = self.width, self.height

        def blocked(cell):
            x, y = cell
            if x < 0 or y < 0 or x >= w or y >= h:
                return True
            return cell in occ
        return blocked

    def cell_blocked(self, cell, ignore=None, include_units=True):
        return self.make_blocked(ignore, include_units)(cell)

    def unit_at_cell(self, cell, ignore=None):
        """cell'de (ignore hariç) canlı bir birim oturuyor mu? Hareket
        sırasında üst üste binmeyi önlemek için dinamik kontrol."""
        for e in self.entities:
            if e is ignore or not e.is_alive():
                continue
            if hasattr(e, 'unit_type') and cell_of(e.x, e.y) == cell:
                return True
        return False

    def nearest_free_cell(self, cell, ignore=None, include_units=True, max_radius=12):
        """cell'e en yakın engelsiz hücre (BFS). Bulunamazsa None."""
        blocked = self.make_blocked(ignore, include_units)
        if not blocked(cell):
            return cell
        seen = {cell}
        q = deque([(cell, 0)])
        dirs = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
        while q:
            (cx, cy), d = q.popleft()
            if d >= max_radius:
                continue
            for dx, dy in dirs:
                nc = (cx + dx, cy + dy)
                if nc in seen:
                    continue
                seen.add(nc)
                if not blocked(nc):
                    return nc
                q.append((nc, d + 1))
        return None

    def add_entity(self, entity: BaseEntity):
        entity.world = self
        self.entities.append(entity)

    def remove_entity(self, entity: BaseEntity):
        if entity in self.entities:
            self.entities.remove(entity)

    def get_entities_in_range(self, x: float, y: float, radius: float) -> List[BaseEntity]:
        result = []
        for e in self.entities:
            if not e.is_alive():
                continue
            dx = e.x - x
            dy = e.y - y
            if (dx ** 2 + dy ** 2) ** 0.5 <= radius:
                result.append(e)
        return result

    def get_entities_by_type(self, entity_type: str) -> List[BaseEntity]:
        return [e for e in self.entities if e.name.startswith(entity_type) and e.is_alive()]

    def _resolve_overlaps(self):
        """Aynı hücrede oturmuş (settled) birden fazla birim varsa, fazlasını
        en yakın boş kareye gönderir (MVP üst-üste-binme çözümü)."""
        seen = {}
        for e in self.entities:
            if not (hasattr(e, 'unit_type') and e.is_alive()):
                continue
            settled = getattr(e, '_settled', None)
            if settled is None or not settled() or getattr(e, 'path', None):
                continue  # hareket halindeki/route'taki birimleri rahatsız etme
            c = cell_of(e.x, e.y)
            if c in seen:
                free = self.nearest_free_cell(c, ignore=e)
                if free is not None and free != c:
                    e.move_to(float(free[0]), float(free[1]))
            else:
                seen[c] = e

    def update(self, dt: float):
        for e in self.entities:
            if hasattr(e, 'update'):
                e.update(dt)
        self._resolve_overlaps()
        self.entities = [e for e in self.entities if e.is_alive()]
