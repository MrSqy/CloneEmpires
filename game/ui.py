import os
import pygame
from typing import List
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_UI_BG, COLOR_XP_BAR,
    COLOR_HP_GREEN, COLOR_HP_RED, RESOURCES, RESOURCE_LABELS
)
from game.economy import EconomyEngine
from game.entities.unit import Unit
from game.entities.building import Building
from game.entities.resource import ResourceNode
from game.building_catalog import CATEGORY_ORDER, items_in_category, get_cost

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")


class Button:
    def __init__(self, rect: pygame.Rect, text: str, callback, color=(60, 60, 60), hover_color=(90, 90, 90)):
        self.rect = rect
        self.text = text
        self.callback = callback
        self.color = color
        self.hover_color = hover_color
        self.hovered = False
    
    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 1)
        text_surf = font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def handle_event(self, event: pygame.event.Event, offset=(0, 0)) -> bool:
        mx, my = pygame.mouse.get_pos()
        rx, ry = self.rect.x + offset[0], self.rect.y + offset[1]
        self.hovered = rx <= mx <= rx + self.rect.w and ry <= my <= ry + self.rect.h
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.hovered:
            if self.callback:
                self.callback()
            return True
        return False


class UIManager:
    def __init__(self, economy: EconomyEngine):
        self.economy = economy
        self.font = pygame.font.SysFont("arial", 16)
        self.large_font = pygame.font.SysFont("arial", 20)
        self.king_name = "Kral Baran"
        self.townhall_level = 1
        self.xp = 0
        self.max_xp = 100
        self.buttons: List[Button] = []
        self.button_callbacks = {}  # type -> list of (label, callback_key)

        # Market durumu
        self.market_open = False
        self.last_market_tab = CATEGORY_ORDER[0]
        self.on_buy = None  # app tarafından set edilir: callback(building_type)
        self._icon_cache = {}

    # ------------------------------------------------------------------ Market
    def _market_icon(self, building_type: str):
        if building_type in self._icon_cache:
            return self._icon_cache[building_type]
        path = os.path.join(ASSETS_DIR, "buildings", f"{building_type}.png")
        img = None
        if os.path.exists(path):
            img = pygame.transform.smoothscale(
                pygame.image.load(path).convert_alpha(), (40, 40))
        self._icon_cache[building_type] = img
        return img

    def toggle_market(self):
        self.market_open = not self.market_open

    def close_market(self):
        self.market_open = False

    def _market_button_rect(self):
        return pygame.Rect(SCREEN_WIDTH - 130, SCREEN_HEIGHT - 150, 120, 36)

    def _market_layout(self):
        """Market panelinin tüm tıklanabilir bölgelerini hesaplar (çizim+tıklama paylaşır)."""
        panel_w, panel_h = 660, 440
        px = (SCREEN_WIDTH - panel_w) // 2
        py = (SCREEN_HEIGHT - panel_h) // 2
        panel = pygame.Rect(px, py, panel_w, panel_h)
        close = pygame.Rect(px + panel_w - 34, py + 8, 26, 26)

        tabs = []
        tab_w = panel_w // len(CATEGORY_ORDER)
        for i, cat in enumerate(CATEGORY_ORDER):
            tabs.append((pygame.Rect(px + i * tab_w, py + 44, tab_w, 32), cat))

        cards = []
        items = items_in_category(self.last_market_tab)
        card_w, card_h = 200, 120
        gap = 12
        start_x = px + 16
        start_y = py + 90
        cols = 3
        for idx, (bt, meta) in enumerate(items):
            row, col = divmod(idx, cols)
            cx = start_x + col * (card_w + gap)
            cy = start_y + row * (card_h + gap)
            card_rect = pygame.Rect(cx, cy, card_w, card_h)
            buy_rect = pygame.Rect(cx + 10, cy + card_h - 32, card_w - 20, 26)
            cost = get_cost(bt)
            affordable = (self.economy.can_afford(cost)
                          and self.townhall_level >= meta.get("level_req", 1))
            cards.append((card_rect, buy_rect, bt, meta, cost, affordable))

        return dict(panel=panel, close=close, tabs=tabs, cards=cards)

    def draw_market(self, screen: pygame.Surface):
        # Sabit market açma butonu (her zaman görünür)
        btn = self._market_button_rect()
        pygame.draw.rect(screen, (70, 50, 20), btn)
        pygame.draw.rect(screen, (200, 180, 120), btn, 2)
        label = self.font.render("Market", True, (255, 230, 180))
        screen.blit(label, label.get_rect(center=btn.center))

        if not self.market_open:
            return

        lay = self._market_layout()
        panel = lay["panel"]
        overlay = pygame.Surface((panel.w, panel.h), pygame.SRCALPHA)
        overlay.fill((25, 25, 30, 240))
        screen.blit(overlay, (panel.x, panel.y))
        pygame.draw.rect(screen, (180, 180, 200), panel, 2)

        title = self.large_font.render("Market", True, (255, 255, 255))
        screen.blit(title, (panel.x + 14, panel.y + 10))

        # Kapat butonu
        pygame.draw.rect(screen, (120, 40, 40), lay["close"])
        x_surf = self.font.render("X", True, (255, 255, 255))
        screen.blit(x_surf, x_surf.get_rect(center=lay["close"].center))

        # Sekmeler
        for rect, cat in lay["tabs"]:
            active = (cat == self.last_market_tab)
            pygame.draw.rect(screen, (80, 80, 110) if active else (45, 45, 55), rect)
            pygame.draw.rect(screen, (150, 150, 170), rect, 1)
            t = self.font.render(cat, True, (255, 255, 255) if active else (180, 180, 180))
            screen.blit(t, t.get_rect(center=rect.center))

        # Kartlar
        for card_rect, buy_rect, bt, meta, cost, affordable in lay["cards"]:
            pygame.draw.rect(screen, (40, 40, 50), card_rect)
            pygame.draw.rect(screen, (90, 90, 110), card_rect, 1)

            icon = self._market_icon(bt)
            if icon:
                screen.blit(icon, (card_rect.x + 8, card_rect.y + 8))
            else:
                pygame.draw.rect(screen, (110, 90, 60),
                                 (card_rect.x + 8, card_rect.y + 8, 40, 40))

            name = self.font.render(meta["label"], True, (255, 255, 255))
            screen.blit(name, (card_rect.x + 56, card_rect.y + 10))

            # Level gereksinimi badge
            if meta.get("level_req", 1) > 1:
                badge = self.font.render(f"Lv{meta['level_req']}", True, (255, 220, 120))
                screen.blit(badge, (card_rect.right - 36, card_rect.y + 10))

            cost_str = "  ".join(
                f"{RESOURCE_LABELS.get(k, k)}:{v}" for k, v in cost.items())
            cost_surf = self.font.render(cost_str, True, (200, 200, 200))
            screen.blit(cost_surf, (card_rect.x + 10, card_rect.y + 56))

            bcolor = (40, 110, 40) if affordable else (70, 70, 70)
            pygame.draw.rect(screen, bcolor, buy_rect)
            pygame.draw.rect(screen, (150, 150, 150), buy_rect, 1)
            buy_label = "Satın Al" if affordable else "Yetersiz"
            bl = self.font.render(buy_label, True, (255, 255, 255) if affordable else (170, 170, 170))
            screen.blit(bl, bl.get_rect(center=buy_rect.center))

    def handle_market_event(self, event: pygame.event.Event) -> bool:
        """Market ile ilgili tıklamaları işler. True dönerse olay tüketildi."""
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False
        pos = event.pos

        # Market açma/kapama butonu
        if self._market_button_rect().collidepoint(pos):
            self.toggle_market()
            return True

        if not self.market_open:
            return False

        lay = self._market_layout()
        if lay["close"].collidepoint(pos):
            self.close_market()
            return True

        for rect, cat in lay["tabs"]:
            if rect.collidepoint(pos):
                self.last_market_tab = cat
                return True

        for card_rect, buy_rect, bt, meta, cost, affordable in lay["cards"]:
            if buy_rect.collidepoint(pos):
                if affordable and self.on_buy:
                    self.on_buy(bt)
                    self.close_market()
                return True

        # Panel içine ama boş yere tıklama: tüket (kapatma)
        if lay["panel"].collidepoint(pos):
            return True

        # Panel dışına tıklama: kapat
        self.close_market()
        return True

    def draw(self, screen: pygame.Surface, selected_entities: List):
        self.draw_resource_panel(screen)
        self.draw_bottom_bar(screen, selected_entities)
        self.draw_market(screen)

    def draw_resource_panel(self, screen: pygame.Surface):
        panel_w = 220
        panel_h = 160
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill(COLOR_UI_BG)

        name_surf = self.large_font.render(self.king_name, True, (255, 255, 255))
        panel.blit(name_surf, (10, 5))

        pygame.draw.rect(panel, (50, 50, 50), (10, 30, 200, 14))
        xp_ratio = self.xp / self.max_xp if self.max_xp > 0 else 0
        pygame.draw.rect(panel, COLOR_XP_BAR, (10, 30, int(200 * xp_ratio), 14))
        level_text = self.font.render(f"Seviye {self.townhall_level}", True, (255, 255, 255))
        panel.blit(level_text, (10, 48))

        resource_rows = [
            [("wood", "Odun"), ("food", "Gıda")],
            [("stone", "Taş"), ("gold", "Altın")],
            [("gem", "Mücevher"),],
        ]
        y_offset = 68
        for row in resource_rows:
            x_offset = 10
            for res_key, res_label in row:
                amount = self.economy.resources.get(res_key, 0)
                text = self.font.render(f"{res_label}: {amount}", True, (255, 255, 255))
                panel.blit(text, (x_offset, y_offset))
                x_offset += 100
            y_offset += 22

        screen.blit(panel, (10, 10))

    def _draw_bar_hp(self, surface, x, y, w, ratio, color):
        h = 8
        pygame.draw.rect(surface, (40, 40, 40), (x, y, w, h))
        pygame.draw.rect(surface, color, (x, y, int(w * ratio), h))
        pygame.draw.rect(surface, (180, 180, 180), (x, y, w, h), 1)

    def draw_bottom_bar(self, screen: pygame.Surface, selected: List):
        if not selected:
            return
        bar_h = 110
        bar_y = SCREEN_HEIGHT - bar_h
        bar = pygame.Surface((SCREEN_WIDTH, bar_h), pygame.SRCALPHA)
        bar.fill((25, 25, 25, 235))
        # Top accent line
        pygame.draw.line(bar, (100, 100, 100), (0, 0), (SCREEN_WIDTH, 0), 2)

        if len(selected) == 1:
            entity = selected[0]
            if isinstance(entity, Unit):
                self._draw_unit_info(bar, entity, 14, 10)
            elif isinstance(entity, Building):
                self._draw_building_info(bar, entity, 14, 10)
                if hasattr(entity, 'assigned_workers') and entity.assigned_workers:
                    self._draw_worker_panel(bar, entity, SCREEN_WIDTH - 220, 10)
            elif isinstance(entity, ResourceNode):
                self._draw_resource_info(bar, entity, 14, 10)
        elif len(selected) > 1 and all(isinstance(e, Unit) for e in selected):
            x = 14
            for unit in selected:
                if not unit.is_alive():
                    continue
                pygame.draw.rect(bar, (80, 80, 80), (x, 10, 50, 50))
                pygame.draw.rect(bar, (150, 150, 150), (x, 10, 50, 50), 1)
                hp_ratio = unit.stats.hp / unit.stats.max_hp if unit.stats.max_hp > 0 else 0
                color = COLOR_HP_GREEN if hp_ratio > 0.5 else COLOR_HP_RED
                self._draw_bar_hp(bar, x, 64, 50, hp_ratio, color)
                name = self.font.render(unit.unit_type[:3], True, (220, 220, 220))
                bar.blit(name, (x + 4, 74))
                x += 62

        self.draw_buttons(bar)
        screen.blit(bar, (0, bar_y))

    def clear_buttons(self):
        self.buttons.clear()
    
    def add_button(self, x: int, y: int, w: int, h: int, text: str, callback,
                   color=(60, 60, 60), hover_color=(90, 90, 90)):
        btn = Button(pygame.Rect(x, y, w, h), text, callback, color, hover_color)
        self.buttons.append(btn)

    def build_worker_exit_buttons(self, building, on_remove=None):
        """Add exit buttons for workers inside a building.
        Call this after clear_buttons() when a building is selected.
        on_remove: optional callback(building, worker) to override default remove."""
        if not hasattr(building, 'assigned_workers') or not building.assigned_workers:
            return
        
        for i, worker in enumerate(building.assigned_workers):
            if not worker.is_alive():
                continue
            wx = SCREEN_WIDTH - 220 + i * 50 + 2
            wy = 10 + 22 + 2  # matching _draw_worker_panel positions
            
            def make_callback(b=building, w=worker):
                if on_remove:
                    return lambda: on_remove(b, w)
                return lambda: b.remove_worker(w)
            
            self.add_button(wx, wy, 36, 36, "", make_callback())
    
    def handle_event(self, event: pygame.event.Event):
        """Handle UI button clicks. Call this from app.py event loop."""
        if self.handle_market_event(event):
            return True
        for btn in self.buttons:
            if btn.handle_event(event, offset=(0, SCREEN_HEIGHT - 100)):
                return True
        return False
    
    def draw_buttons(self, surface: pygame.Surface):
        for btn in self.buttons:
            btn.draw(surface, self.font)

    def _draw_unit_info(self, surface, unit: Unit, x, y):
        title = self.large_font.render(f"{unit.unit_type.upper()}  (Seviye {unit.level})", True, (255, 220, 100))
        surface.blit(title, (x, y))
        # HP bar
        hp_ratio = unit.stats.hp / unit.stats.max_hp if unit.stats.max_hp > 0 else 0
        hp_color = COLOR_HP_GREEN if hp_ratio > 0.5 else COLOR_HP_RED
        self._draw_bar_hp(surface, x, y + 28, 180, hp_ratio, hp_color)
        hp_text = self.font.render(f"{unit.stats.hp:.0f} / {unit.stats.max_hp:.0f}", True, (255, 255, 255))
        surface.blit(hp_text, (x + 185, y + 26))
        # Compact stats line
        dmg = max(unit.stats.attack_phys, unit.stats.attack_magic)
        stats_line = self.font.render(
            f"Hasar: {dmg:.0f}  |  Zırh: {unit.stats.armor:.0f}  |  Menzil: {unit.stats.attack_range:.1f}  |  Hız: {unit.stats.move_speed:.1f}",
            True, (200, 200, 200))
        surface.blit(stats_line, (x, y + 42))
        # State
        state_text = self.font.render(f"Durum: {unit.state_machine.current}", True, (180, 180, 180))
        surface.blit(state_text, (x, y + 60))

    def _draw_building_info(self, surface, building: Building, x, y):
        title = self.large_font.render(f"{building.building_type.upper()}  (Seviye {building.stats.level})", True, (255, 220, 100))
        surface.blit(title, (x, y))
        y_off = 28

        # Kule bilgisi
        if getattr(building, 'is_tower', None) and building.is_tower():
            if getattr(building, 'tower_disabled', False):
                txt = self.font.render("Kule yıkık - ateş etmiyor", True, (255, 80, 80))
                surface.blit(txt, (x, y + y_off))
                y_off += 18
            else:
                hp_ratio = building.stats.hp / building.stats.max_hp if building.stats.max_hp > 0 else 0
                hp_color = COLOR_HP_GREEN if hp_ratio > 0.5 else COLOR_HP_RED
                self._draw_bar_hp(surface, x, y + y_off, 140, hp_ratio, hp_color)
                hp_txt = self.font.render(f"{building.stats.hp:.0f} / {building.stats.max_hp:.0f}", True, (255, 255, 255))
                surface.blit(hp_txt, (x + 145, y + y_off - 2))
                y_off += 18
                stat_txt = self.font.render(f"Hasar: {building.stats.attack:.0f}  |  Menzil: {building.stats.attack_range:.1f}", True, (200, 200, 200))
                surface.blit(stat_txt, (x, y + y_off))
                y_off += 18

        # Kaynak binası köylü/üretim bilgisi
        if building.resource_type() is not None:
            n = len(building.assigned_workers)
            txt = self.font.render(f"Köylü: {n}/4  |  Kaynak: {building.resource_type()}", True, (200, 200, 200))
            surface.blit(txt, (x, y + y_off))
            y_off += 18
            if building.worker_active and building.worker_mode:
                from game.work_modes import WORK_MODES, resource_gain, gem_reward
                mode = WORK_MODES[building.worker_mode]
                gain = resource_gain(building.worker_mode, max(1, n))
                mins = int(building.worker_timer // 60)
                secs = int(building.worker_timer % 60)
                txt = self.font.render(
                    f"Mod: {mode['label']} | Kalan: {mins}:{secs:02d} | +{gain} {building.resource_type()}",
                    True, (255, 255, 255))
                surface.blit(txt, (x, y + y_off))
                y_off += 18
            elif building.is_producing:
                txt = self.font.render("Pasif üretim: AKTİF", True, (100, 220, 100))
                surface.blit(txt, (x, y + y_off))
                y_off += 18

        # Üretim kuyruğu (baraka / köy)
        pq = getattr(building, 'production_queue', None)
        if pq is not None:
            status = pq.get_queue_status()
            remaining = len(status["queued"]) + (1 if status["current"] else 0)
            if remaining > 0 and status["current"]:
                mx = status["max_progress"] or 1.0
                pct = int(100 * status["progress"] / mx)
                cur = status["current"]["unit_type"]
                txt = self.font.render(f"Sırada: {remaining} | Üretiliyor: {cur} %{pct}", True, (200, 200, 200))
                surface.blit(txt, (x, y + y_off))
            else:
                txt = self.font.render("Üretim kuyruğu boş", True, (150, 150, 150))
                surface.blit(txt, (x, y + y_off))

    def _draw_resource_info(self, surface, node: ResourceNode, x, y):
        title = self.large_font.render(f"{node.resource_type.upper()} KAYNAĞI", True, (255, 220, 100))
        surface.blit(title, (x, y))
        y_off = 28
        if node.amount > 0:
            ratio = node.amount / node.max_amount
            self._draw_bar_hp(surface, x, y + y_off, 180, ratio, (0, 200, 0))
            amt_txt = self.font.render(f"{int(node.amount)} / {int(node.max_amount)}", True, (255, 255, 255))
            surface.blit(amt_txt, (x + 185, y + y_off - 2))
            y_off += 20
            desc = self.font.render("Toplanmaya hazır", True, (180, 180, 180))
            surface.blit(desc, (x, y + y_off))
        else:
            ratio = max(0.0, 1.0 - node.regrowth_timer / node.respawn_time)
            self._draw_bar_hp(surface, x, y + y_off, 180, ratio, (255, 140, 0))
            secs = int(node.regrowth_timer)
            regrow_txt = self.font.render(f"Yenileniyor... {secs}s", True, (255, 200, 100))
            surface.blit(regrow_txt, (x + 185, y + y_off - 2))
            y_off += 20
            desc = self.font.render("Kaynak tükendi, doğal yenilenme devam ediyor", True, (180, 180, 180))
            surface.blit(desc, (x, y + y_off))

    def _draw_worker_panel(self, surface: pygame.Surface, building, x: int, y: int):
        """Draw worker portraits on the right side of the bottom bar.
        building: a Building with assigned_workers list.
        x, y: top-left position on the bar surface."""
        if not hasattr(building, 'assigned_workers') or not building.assigned_workers:
            return
        
        font_small = pygame.font.SysFont("arial", 12)
        panel_title = self.font.render("Köylüler", True, (200, 200, 200))
        surface.blit(panel_title, (x, y))
        
        for i, worker in enumerate(building.assigned_workers):
            if not worker.is_alive():
                continue
            wx = x + i * 50
            wy = y + 22
            
            # Worker portrait background
            locked = getattr(building, 'worker_active', False)
            bg_color = (80, 80, 80) if locked else (100, 100, 100)
            pygame.draw.rect(surface, bg_color, (wx, wy, 40, 40))
            pygame.draw.rect(surface, (150, 150, 150), (wx, wy, 40, 40), 1)
            
            # Worker icon (colored circle for now)
            pygame.draw.circle(surface, (180, 150, 90), (wx + 20, wy + 18), 12)
            
            # Lock indicator if production is active
            if locked:
                lock_text = font_small.render("🔒", True, (255, 200, 50))
                surface.blit(lock_text, (wx + 25, wy + 2))
            
            # Worker label
            label = font_small.render(f"K{i+1}", True, (255, 255, 255))
            surface.blit(label, (wx + 12, wy + 42))
