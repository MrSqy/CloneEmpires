from game.building_catalog import (
    CATALOG, CATEGORY_ORDER, items_in_category, get_cost, get_base, get_trains
)
from game.construction_manager import BUILDING_COSTS


def test_all_categories_have_items():
    for cat in CATEGORY_ORDER:
        assert len(items_in_category(cat)) > 0


def test_catalog_costs_in_building_costs():
    for bt in CATALOG:
        assert bt in BUILDING_COSTS
        assert BUILDING_COSTS[bt] == get_cost(bt)


def test_legacy_keys_preserved():
    # Eski testler ve xp_system "barracks" anahtarına güveniyor
    assert "barracks" in BUILDING_COSTS
    assert "storage" in BUILDING_COSTS


def test_barracks_base_and_trains():
    assert get_base("barracks_spear_1") == "barracks"
    assert get_trains("barracks_archer_1") == ["archer"]
    assert get_base("woodcutter") == "resource"
    assert get_base("house") == "house"


def test_level_requirements():
    assert CATALOG["arrow_tower_2"]["level_req"] == 2
    assert CATALOG["house"]["level_req"] == 1
