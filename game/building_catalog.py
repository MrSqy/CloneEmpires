"""Market / inşaat bina kataloğu.

Tüm satın alınabilir binalar burada tanımlı. Market sekmeleri ve maliyetler
bu tek kaynaktan üretilir. `base` alanı binanın davranışını belirler:
    - "resource"  -> kaynak üretir (building.py içindeki resource_map)
    - "barracks"  -> asker eğitir (trains listesi)
    - "tower"     -> savunma yapısı (şimdilik pasif)
    - "house"     -> nüfus
"""

# building_type -> metadata
CATALOG = {
    # --- Binalar ---
    "house": dict(category="Binalar", label="Ev", base="house",
                  cost={"wood": 30, "stone": 10}, level_req=1),
    # --- Kuleler ---
    "arrow_tower_1": dict(category="Kuleler", label="Ok Kulesi L1", base="tower",
                          cost={"wood": 80, "stone": 60}, level_req=1),
    "arrow_tower_2": dict(category="Kuleler", label="Ok Kulesi L2", base="tower",
                          cost={"wood": 160, "stone": 120, "gold": 40}, level_req=2),
    # --- Barakalar ---
    "barracks_spear_1": dict(category="Barakalar", label="Mızrakçı Barakası L1",
                             base="barracks", trains=["spearman"],
                             cost={"wood": 100, "stone": 50}, level_req=1),
    "barracks_spear_2": dict(category="Barakalar", label="Mızrakçı Barakası L2",
                             base="barracks", trains=["spearman"],
                             cost={"wood": 200, "stone": 100, "gold": 30}, level_req=2),
    "barracks_sword_1": dict(category="Barakalar", label="Kılıçlı Barakası L1",
                             base="barracks", trains=["swordsman"],
                             cost={"wood": 120, "stone": 60, "gold": 20}, level_req=1),
    "barracks_sword_2": dict(category="Barakalar", label="Kılıçlı Barakası L2",
                             base="barracks", trains=["swordsman"],
                             cost={"wood": 240, "stone": 120, "gold": 50}, level_req=2),
    "barracks_archer_1": dict(category="Barakalar", label="Okçu Barakası L1",
                              base="barracks", trains=["archer"],
                              cost={"wood": 100, "stone": 40, "gold": 20}, level_req=1),
    "barracks_archer_2": dict(category="Barakalar", label="Okçu Barakası L2",
                              base="barracks", trains=["archer"],
                              cost={"wood": 200, "stone": 80, "gold": 50}, level_req=2),
    # --- Kaynaklar ---
    "woodcutter": dict(category="Kaynaklar", label="Oduncu Evi", base="resource",
                       cost={"wood": 50, "stone": 20}, level_req=1),
    "farm": dict(category="Kaynaklar", label="Çiftlik", base="resource",
                 cost={"wood": 40, "stone": 10}, level_req=1),
    "gold_mine": dict(category="Kaynaklar", label="Altın Madeni", base="resource",
                      cost={"wood": 80, "stone": 40}, level_req=1),
    "quarry": dict(category="Kaynaklar", label="Taş Ocağı", base="resource",
                   cost={"wood": 60, "stone": 30}, level_req=1),
}

# Kule savaş statları (building_type -> combat)
TOWER_COMBAT = {
    "arrow_tower_1": dict(hp=300, attack=18, attack_range=6.0, attack_speed=1.0),
    "arrow_tower_2": dict(hp=500, attack=30, attack_range=7.0, attack_speed=1.2),
}

# Sekme sırası
CATEGORY_ORDER = ["Binalar", "Kuleler", "Barakalar", "Kaynaklar"]


def get_tower_combat(building_type: str):
    """Kule savaş statlarını döndürür; kule değilse None."""
    c = TOWER_COMBAT.get(building_type)
    return dict(c) if c else None


def items_in_category(category: str):
    """Bir kategorideki (building_type, meta) çiftlerini katalog sırasıyla döndürür."""
    return [(bt, meta) for bt, meta in CATALOG.items() if meta["category"] == category]


def get_cost(building_type: str):
    meta = CATALOG.get(building_type)
    return dict(meta["cost"]) if meta else {}


def get_base(building_type: str):
    meta = CATALOG.get(building_type)
    return meta["base"] if meta else None


def get_trains(building_type: str):
    meta = CATALOG.get(building_type)
    return list(meta.get("trains", [])) if meta else []


def get_upgrade(building_type: str):
    """Return the next-level building type, or None if max level.
    Matches by prefix so barracks_spear_1 upgrades to barracks_spear_2,
    not barracks_sword_2."""
    entry = CATALOG.get(building_type)
    if not entry:
        return None
    level = entry.get("level_req", 1)
    # Expected next-level name: "prefix_1" -> "prefix_2"
    expected = f"{building_type.rsplit('_', 1)[0]}_{level + 1}"
    return expected if expected in CATALOG else None
