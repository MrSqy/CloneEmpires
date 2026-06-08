import pygame


def load_placeholder(color, size=(32, 32)):
    surf = pygame.Surface(size)
    surf.fill(color)
    return surf


UNIT_COLORS = {
    "spearman": (0, 100, 255),
    "rider": (0, 150, 200),
    "archer": (0, 200, 150),
    "troll_knife": (200, 50, 50),
    "troll_club": (180, 30, 30),
    "troll_archer": (160, 20, 20),
}

BUILDING_COLORS = {
    "townhall": (139, 69, 19),
    "house": (160, 82, 45),
    "barracks_spear": (100, 100, 100),
    "barracks_rider": (120, 120, 120),
    "barracks_archer": (140, 140, 140),
    "woodcutter": (34, 139, 34),
    "quarry": (128, 128, 128),
    "farm": (255, 215, 0),
    "gold_mine": (218, 165, 32),
}

RESOURCE_COLORS = {
    "wood": (34, 100, 34),
    "stone": (100, 100, 100),
    "food": (200, 200, 50),
    "gold": (255, 215, 0),
    "gem": (138, 43, 226),
}
