import os
import pygame
from typing import List
from game.camera import Camera
from game.entities.base_entity import BaseEntity
from game.constants import TILE_WIDTH, TILE_HEIGHT

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")

ANIM_FRAME_MS = 150  # animasyon kare süresi (~6.6 fps)
FIRE_FRAME_MS = 180


class Renderer:
    def __init__(self, screen: pygame.Surface, camera: Camera):
        self.screen = screen
        self.camera = camera
        self._sprite_cache = {}
        self._scaled_cache = {}

    def _load_image(self, subdir: str, name: str):
        key = f"{subdir}/{name}"
        if key in self._sprite_cache:
            return self._sprite_cache[key]
        path = os.path.join(ASSETS_DIR, subdir, name)
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            self._sprite_cache[key] = img
            return img
        self._sprite_cache[key] = None
        return None

    # ---------------------------------------------------------------- ölçekleme
    def _scaled(self, sprite, zoom):
        """Sprite'ı zoom oranında ölçekler (cache'li). zoom≈1 ise orijinali döner."""
        if abs(zoom - 1.0) < 1e-3:
            return sprite
        key = (id(sprite), round(zoom, 2))
        cached = self._scaled_cache.get(key)
        if cached is None:
            w = max(1, int(sprite.get_width() * zoom))
            h = max(1, int(sprite.get_height() * zoom))
            cached = pygame.transform.scale(sprite, (w, h))
            self._scaled_cache[key] = cached
        return cached

    def _screen_center(self, wx, wy):
        """Bir dünya hücresinin ekrandaki merkez noktası (zoom-uyumlu)."""
        sx, sy = self.camera.world_to_screen(wx, wy)
        z = self.camera.zoom
        return sx + (TILE_WIDTH // 2) * z, sy + (TILE_HEIGHT // 2) * z

    # ------------------------------------------------------------------- zemin
    TILE_COLORS = {
        "safe": (34, 139, 34), "grass": (34, 139, 34),
        "neutral": (139, 90, 43), "dirt": (139, 90, 43),
        "danger": (30, 144, 255), "water": (30, 144, 255),
    }

    def _iso_corner(self, gx, gy, cache):
        """Izgara köşe noktasının (lattice) ekran koordinatı; paylaşılan köşeler
        aynı int'e yuvarlanır → komşu elmaslar arasında dikiş/boşluk olmaz."""
        key = (gx, gy)
        pt = cache.get(key)
        if pt is None:
            sx, sy = self.camera.world_to_screen(gx - 0.5, gy - 0.5)
            pt = (int(round(sx)), int(round(sy)))
            cache[key] = pt
        return pt

    def draw_map(self, world):
        """Zemini PNG ölçekleme yerine elmas poligon olarak çizer (zoom-uyumlu,
        her seviyede dikişsiz). Köşeler ortak lattice fonksiyonundan gelir."""
        corners = {}
        default = (100, 100, 100)
        for x in range(world.width):
            for y in range(world.height):
                color = self.TILE_COLORS.get(world.tiles[x][y], default)
                pts = [
                    self._iso_corner(x, y, corners),
                    self._iso_corner(x + 1, y, corners),
                    self._iso_corner(x + 1, y + 1, corners),
                    self._iso_corner(x, y + 1, corners),
                ]
                pygame.draw.polygon(self.screen, color, pts)

    # ----------------------------------------------------------------- sprite
    def _entity_sprite(self, e):
        if hasattr(e, 'unit_type'):
            return self._load_image("units", f"{e.unit_type}.png")
        if hasattr(e, 'building_type'):
            if hasattr(e, 'is_constructed') and not e.is_constructed:
                return self._load_image("buildings", "construction.png")
            return self._load_image("buildings", f"{e.building_type}.png")
        if hasattr(e, 'resource_type'):
            # Pick sprite based on regrowth phase
            phase = getattr(e, 'regrowth_phase', 2)
            if phase == 0:
                return self._load_image("terrain", f"{e.resource_type}_node_stump.png")
            elif phase == 1:
                return self._load_image("terrain", f"{e.resource_type}_node_sapling.png")
            else:
                return self._load_image("terrain", f"{e.resource_type}_node.png")
        return None

    def _anim_action(self, e):
        """Birimin mevcut aksiyonunu döndürür: 'walk' / 'attack' / None(idle)."""
        task = getattr(e, 'task', None)
        if task == 'working':
            return 'attack'
        if task in ('gather', 'build'):
            tgt = getattr(e, 'task_target', None)
            if tgt is not None:
                dx = tgt.x - e.x
                dy = tgt.y - e.y
                if (dx * dx + dy * dy) ** 0.5 <= 1.6:
                    return 'attack'
            return 'walk'
        sm = getattr(e, 'state_machine', None)
        if sm is not None:
            if sm.current == 'ATTACK':
                return 'attack'
            if sm.current == 'MOVE':
                return 'walk'
        return None

    def _animated_sprite(self, e):
        """Birim için duruma göre animasyon karesi; yoksa base sprite'a düşer."""
        if not hasattr(e, 'unit_type'):
            return self._entity_sprite(e)
        action = self._anim_action(e)
        if action:
            frame = (pygame.time.get_ticks() // ANIM_FRAME_MS) % 2
            img = self._load_image("units", f"{e.unit_type}_{action}_{frame}.png")
            if img:
                return img
        return self._load_image("units", f"{e.unit_type}.png")

    def entity_screen_rect(self, e) -> pygame.Rect:
        """Entity'nin ekranda kapladığı bounding box (seçim için çizimle aynı geometri)."""
        cx, cy = self._screen_center(e.x, e.y)
        sprite = self._entity_sprite(e)
        if sprite:
            sprite = self._scaled(sprite, self.camera.zoom)
            return sprite.get_rect(center=(int(cx), int(cy)))
        half = max(1, int(16 * self.camera.zoom))
        return pygame.Rect(int(cx) - half, int(cy) - half, half * 2, half * 2)

    def pick_entity_at(self, screen_pos, entities):
        """Verilen ekran noktasındaki en öndeki (en büyük y) canlı entity'yi döndürür."""
        hits = [e for e in entities
                if e.is_alive() and self.entity_screen_rect(e).collidepoint(screen_pos)]
        if not hits:
            return None
        return max(hits, key=lambda e: e.y)

    def draw_entities(self, entities: List[BaseEntity]):
        z = self.camera.zoom
        sorted_entities = sorted(entities, key=lambda e: e.y)
        for e in sorted_entities:
            if not e.is_alive():
                continue
            if getattr(e, 'is_inside_building', None):
                continue  # Workers inside buildings are not drawn on map
            cx, cy = self._screen_center(e.x, e.y)

            if hasattr(e, 'unit_type'):
                sprite = self._animated_sprite(e)
            else:
                sprite = self._entity_sprite(e)

            if sprite:
                scaled = self._scaled(sprite, z)
                rect = scaled.get_rect(center=(int(cx), int(cy)))
                self.screen.blit(scaled, rect)
            else:
                half = max(1, int(16 * z))
                rect = pygame.Rect(int(cx) - half, int(cy) - half, half * 2, half * 2)
                color = (200, 200, 200)
                if hasattr(e, 'unit_type'):
                    color = (0, 100, 255) if getattr(e, 'is_player', True) else (255, 0, 0)
                elif hasattr(e, 'building_type'):
                    color = (139, 69, 19)
                pygame.draw.rect(self.screen, color, rect)

            # Altın rozet: seviye 2+ birimler (göğüs bölgesi)
            if hasattr(e, 'level') and e.level >= 2 and hasattr(e, 'unit_type'):
                badge_r = max(2, int(4 * z))
                badge_x = int(cx - 2 * z)
                badge_y = int(cy - 4 * z)
                pygame.draw.circle(self.screen, (255, 215, 0), (badge_x, badge_y), badge_r)
                pygame.draw.circle(self.screen, (180, 150, 0), (badge_x, badge_y), badge_r, 1)

            # Yıkık kule: ateş animasyonu
            if getattr(e, 'tower_disabled', False):
                self._draw_fire(int(cx), int(cy), z)

            # Projectile arrow
            if hasattr(e, 'target') and hasattr(e, 'speed') and not hasattr(e, 'unit_type'):
                tip_x = int(cx + 6 * z)
                tip_y = int(cy - 3 * z)
                pygame.draw.line(self.screen, (255, 200, 0), (int(cx), int(cy)), (tip_x, tip_y), max(1, int(2 * z)))

            if e.state.selected:
                half = max(1, int(18 * z))
                pygame.draw.rect(self.screen, (255, 255, 0),
                                 (int(cx) - half, int(cy) - half, half * 2, half * 2), 2)

    def _draw_fire(self, cx, cy, zoom):
        frame = (pygame.time.get_ticks() // FIRE_FRAME_MS) % 3
        img = self._load_image("effects", f"fire_{frame}.png")
        if img:
            scaled = self._scaled(img, zoom)
            rect = scaled.get_rect(center=(cx, cy - int(8 * zoom)))
            self.screen.blit(scaled, rect)
        else:
            pygame.draw.circle(self.screen, (255, 140, 0), (cx, cy - int(8 * zoom)),
                               max(2, int(6 * zoom)))

    # -------------------------------------------------------------------- HP
    def draw_hp_bar(self, entity: BaseEntity):
        if not hasattr(entity, 'stats') or not hasattr(entity.stats, 'hp'):
            return
        max_hp = getattr(entity.stats, 'max_hp', 0)
        if max_hp <= 0:
            return
        z = self.camera.zoom
        cx, cy = self._screen_center(entity.x, entity.y)
        ratio = max(0.0, min(1.0, entity.stats.hp / max_hp))
        bar_w = int(32 * z)
        bar_h = max(2, int(4 * z))
        bx = int(cx) - bar_w // 2
        by = int(cy) - int(24 * z)
        pygame.draw.rect(self.screen, (255, 0, 0), (bx, by, bar_w, bar_h))
        pygame.draw.rect(self.screen, (0, 255, 0), (bx, by, int(bar_w * ratio), bar_h))

    def draw_gather_bar(self, entity: BaseEntity):
        """Draw a small progress bar above units that are gathering."""
        if not hasattr(entity, 'gather_timer') or entity.gather_timer <= 0:
            return
        z = self.camera.zoom
        cx, cy = self._screen_center(entity.x, entity.y)
        ratio = min(1.0, entity.gather_timer / 2.0)
        bar_w = int(24 * z)
        bar_h = max(2, int(3 * z))
        bx = int(cx) - bar_w // 2
        by = int(cy) - int(30 * z)
        pygame.draw.rect(self.screen, (30, 30, 30), (bx, by, bar_w, bar_h))
        pygame.draw.rect(self.screen, (255, 200, 50), (bx, by, int(bar_w * ratio), bar_h))

    def draw_resource_overlay(self, entity: BaseEntity):
        """Draw resource amount bar (green) or regrowth timer (orange) above resource nodes."""
        if not hasattr(entity, 'amount') or not hasattr(entity, 'max_amount'):
            return
        z = self.camera.zoom
        cx, cy = self._screen_center(entity.x, entity.y)
        cx, cy = int(cx), int(cy)
        bar_w = int(32 * z)
        bar_h = max(2, int(4 * z))
        bx = cx - bar_w // 2
        by = cy - int(20 * z)
        pygame.draw.rect(self.screen, (30, 30, 30), (bx, by, bar_w, bar_h))
        if entity.amount > 0:
            ratio = max(0.0, min(1.0, entity.amount / entity.max_amount))
            pygame.draw.rect(self.screen, (0, 200, 0), (bx, by, int(bar_w * ratio), bar_h))
        else:
            ratio = max(0.0, min(1.0, 1.0 - entity.regrowth_timer / entity.respawn_time))
            pygame.draw.rect(self.screen, (255, 140, 0), (bx, by, int(bar_w * ratio), bar_h))
        pygame.draw.rect(self.screen, (200, 200, 200), (bx, by, bar_w, bar_h), 1)

    # -------------------------------------------------------- bina overlay'leri
    def draw_building_overlays(self, building):
        """Bina başına dünya-uzayı overlay: üretim barı, köylü süre barı, inşaat barı."""
        z = self.camera.zoom
        cx, cy = self._screen_center(building.x, building.y)
        cx, cy = int(cx), int(cy)

        # Construction progress bar (green)
        if not building.is_constructed:
            ratio = max(0.0, min(1.0, building.construction_progress / 100.0))
            self._overlay_bar(cx, cy, z, ratio, (0, 220, 0))
            return

        # Baraka / köy binası üretim kuyruğu
        pq = getattr(building, 'production_queue', None)
        if pq is not None:
            status = pq.get_queue_status()
            remaining = len(status["queued"]) + (1 if status["current"] else 0)
            if remaining > 0:
                mx = status["max_progress"] or 1.0
                ratio = max(0.0, min(1.0, status["progress"] / mx))
                self._overlay_bar(cx, cy, z, ratio, (80, 160, 255))
                self._overlay_count(cx, cy, z, remaining)
            return

        # Kaynak binası köylü üretimi
        if getattr(building, 'worker_active', False) and building.worker_mode:
            from game.work_modes import duration_seconds
            total = duration_seconds(building.worker_mode) or 1.0
            ratio = max(0.0, min(1.0, 1.0 - building.worker_timer / total))
            self._overlay_bar(cx, cy, z, ratio, (120, 220, 120))

    def _overlay_bar(self, cx, cy, z, ratio, color):
        bar_w = int(40 * z)
        bar_h = max(3, int(5 * z))
        bx = cx - bar_w // 2
        by = cy + int(18 * z)
        pygame.draw.rect(self.screen, (30, 30, 30), (bx, by, bar_w, bar_h))
        pygame.draw.rect(self.screen, color, (bx, by, int(bar_w * ratio), bar_h))
        pygame.draw.rect(self.screen, (200, 200, 200), (bx, by, bar_w, bar_h), 1)

    def _overlay_count(self, cx, cy, z, count):
        font = pygame.font.SysFont("arial", max(12, int(14 * z)))
        surf = font.render(str(count), True, (255, 255, 0))
        rect = surf.get_rect(center=(cx, cy - int(30 * z)))
        bg = pygame.Surface((rect.w + 6, rect.h + 2), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 160))
        self.screen.blit(bg, (rect.x - 3, rect.y - 1))
        self.screen.blit(surf, rect)
