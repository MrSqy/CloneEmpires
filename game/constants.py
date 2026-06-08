import pygame

# Screen
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Isometric Tile
TILE_WIDTH = 64
TILE_HEIGHT = 32

# Map (karakterlere oranla daha sıkı; yeşil güvenli alan ~20x20 korunur)
MAP_WIDTH = 48
MAP_HEIGHT = 48

# Security Zones
SAFE_ZONE_CENTER = 20
NEUTRAL_ZONE_CENTER = 40

# Colors
COLOR_GRASS = (34, 139, 34)
COLOR_DIRT = (139, 90, 43)
COLOR_WATER = (30, 144, 255)
COLOR_UI_BG = (30, 30, 30, 200)
COLOR_HP_GREEN = (0, 255, 0)
COLOR_HP_RED = (255, 0, 0)
COLOR_XP_BAR = (255, 215, 0)

# Resources
RESOURCES = ["wood", "stone", "food", "gold", "gem"]
RESOURCE_LABELS = {
    "wood": "Odun",
    "stone": "Taş",
    "food": "Gıda",
    "gold": "Altın",
    "gem": "Mücevher",
}
INITIAL_STORAGE = 50000
STORAGE_PER_LEVEL = 500

# Production
PRODUCTION_EXPONENT = 1.05

# Zoom limits
MIN_ZOOM = 0.5
MAX_ZOOM = 3.0
