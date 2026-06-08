from typing import List, Optional, Tuple
from game.entities.base_entity import BaseEntity
from game.entities.unit import Unit


class SelectionManager:
    def __init__(self):
        self.selected: List[BaseEntity] = []
        self.select_box_start: Optional[Tuple[int, int]] = None
        self.select_box_end: Optional[Tuple[int, int]] = None

    def select_single(self, entity: Optional[BaseEntity]):
        self.clear_selection()
        if entity:
            entity.state.selected = True
            self.selected.append(entity)

    def select_multiple(self, entities: List[BaseEntity]):
        self.clear_selection()
        for e in entities:
            e.state.selected = True
            if hasattr(e, 'manual_override'):
                e.manual_override = False
            self.selected.append(e)

    def select_same_class(self, unit: Unit, all_units: List[Unit], radius: float = 10.0):
        same_type = [u for u in all_units
                     if u.unit_type == unit.unit_type and u.is_alive()
                     and not getattr(u, 'is_inside_building', None)
                     and ((u.x - unit.x) ** 2 + (u.y - unit.y) ** 2) ** 0.5 <= radius]
        self.select_multiple(same_type)

    def clear_selection(self):
        for e in self.selected:
            e.state.selected = False
        self.selected.clear()

    def get_selected_units(self) -> List[Unit]:
        return [e for e in self.selected
                if isinstance(e, Unit) and not getattr(e, 'is_inside_building', None)]
