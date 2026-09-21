import pygame
import time
from game.session_menu import SessionMenu
from game.simulation import advance_production
from game.save_load import SaveError
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from game.camera import Camera
from game.world import World
from game.economy import EconomyEngine
from game.renderer import Renderer
from game.ui import UIManager
from game.selection import SelectionManager
from game.save_load import SaveManager
from game.entities.unit import Unit
from game.entities.building import Building
from game.entities.resource import ResourceNode
from game.entities.worker import Worker
from game.ai_controller import AIController
from game.battle_manager import BattleManager
from game.xp_system import XPSystem
from game.construction_manager import ConstructionManager
from game.production_queue import ProductionQueue
from game.building_catalog import get_base, get_trains, get_upgrade
from game.grid import cell_of


class GameApp:
    def __init__(self, save_dir=None, time_source=None):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Social Empires Clone")
        self.clock = pygame.time.Clock()
        self.running = True

        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.world = World()
        self.economy = EconomyEngine()
        self.renderer = Renderer(self.screen, self.camera)
        self.ui = UIManager(self.economy)
        self.selection = SelectionManager()
        self.save_manager = SaveManager(save_dir)
        self.time_source = time_source or time.time
        self.menu = SessionMenu()
        self.screen_mode = "home"
        self.records = self.save_manager.list_worlds()
        self.message = ""
        self.message_timer = 0.0
        self.active_session = False
        self.pending_exit = None
        self._error_elapsed = 0.0
        self.ai = AIController(self.world)
        self.battle_manager = BattleManager(self.world)
        self.xp_system = XPSystem(self.ui)
        self.construction_manager = ConstructionManager(self.world, self.economy)
        self.ui.on_buy = self._enter_build_mode

        self._setup_world()
        self.autosave_timer = 0.0
        self.click_timer = 0.0
        self.last_click_pos = None
        self._build_mode = None
        self.pending_confirm = None  # {"building": b, "worker": w}

    def _setup_world(self):
        cx, cy = self.world.player_base_center
        townhall = Building("townhall", cx, cy)
        self.world.add_entity(townhall)
        townhall.production_queue = ProductionQueue(townhall, self.economy)

        # Kamerayı başlangıçta oyuncu üssüne ortala
        from game.isometric import world_to_screen
        self.camera.x, self.camera.y = world_to_screen(cx, cy)

        self.world.add_entity(Unit("spearman", cx + 2, cy, level=1))
        self.world.add_entity(Unit("spearman", cx + 3, cy + 1, level=1))

        # Başlangıç köylüleri (kaynak toplama için)
        self.world.add_entity(Worker(cx + 1, cy + 2, level=1))
        self.world.add_entity(Worker(cx + 2, cy + 2, level=1))

        self._setup_resources(cx, cy)

        w, h = self.world.width, self.world.height
        self.world.add_entity(Unit("troll_knife", 4, 4))
        self.world.add_entity(Unit("troll_club", w - 5, h - 5))
        self.world.add_entity(Unit("troll_archer", w - 5, 4))
        for e in self.world.entities:
            if isinstance(e, Unit) and "troll" in e.unit_type:
                e.is_player = False
                self.ai.register_patrol(e.x, e.y)

    def _setup_resources(self, cx, cy):
        """Haritaya çeşitli kaynak node'ları (odun/taş/altın/gıda) ve nadir mücevher dağıtır."""
        # (resource_type, dx, dy, küme_boyutu, miktar)
        clusters = [
            ("wood", -7, -3, 5, 150),
            ("wood", 6, -5, 4, 150),
            ("stone", 6, 4, 4, 150),
            ("stone", -8, 5, 3, 150),
            ("gold", -9, -6, 3, 150),
            ("food", 5, 7, 4, 150),
            ("food", -5, 8, 3, 150),
        ]
        for res_type, dx, dy, count, amount in clusters:
            for i in range(count):
                rx = cx + dx + (i % 3)
                ry = cy + dy + (i // 3)
                self.world.add_entity(ResourceNode(res_type, rx, ry, amount))

        # Nadir mücevher madenleri (tehlikeli bölge), 2-3 adet
        for gx, gy in [(9, 9), (39, 11), (11, 39)]:
            self.world.add_entity(ResourceNode("gem", gx, gy, 60))

    def _snapshot(self, world=None, economy=None, xp=None, camera=None, king_name=None):
        world = world or self.world
        xp = xp or self.xp_system
        return self.save_manager.serialize(
            world, economy or self.economy, king_name or self.ui.king_name, xp.level, xp.xp,
            xp_state={k: getattr(xp, k) for k in ('level', 'xp', 'max_xp', 'xp_multiplier')},
            camera=camera or {k: getattr(self.camera, k) for k in ('x', 'y', 'zoom')},
            saved_at=self.time_source())

    def _notify(self, text):
        self.message, self.message_timer = text, 5.0

    def save_game(self):
        if not self.active_session:
            return True
        try:
            data = self._snapshot()
            self.save_manager.save_world(data)
        except (OSError, SaveError, ValueError, OverflowError) as exc:
            self._notify(f'Kayıt başarısız: {exc}')
            return False
        self.world.processed_at = data['processed_at']
        self._notify('Dünya kaydedildi.')
        return True

    def new_game(self, name=''):
        self.selection.clear_selection()
        self.world, self.economy = World(), EconomyEngine()
        names = {r['name'] for r in self.save_manager.list_worlds()}
        index = 1
        while f'Dünya {index}' in names:
            index += 1
        self.world.name = name.strip()[:40] or f'Dünya {index}'
        self.world.created_at = self.world.processed_at = self.time_source()
        self.ui = UIManager(self.economy)
        self.ui.on_buy = self._enter_build_mode
        self.xp_system = XPSystem(self.ui)
        self.ai = AIController(self.world)
        self.battle_manager = BattleManager(self.world)
        self.construction_manager = ConstructionManager(self.world, self.economy)
        self.camera.zoom = 1.0
        self._setup_world()
        self.active_session = True
        self.screen_mode = 'game'
        self._build_mode = self.pending_confirm = None
        self.autosave_timer = 0.0
        self.save_game()

    def load_game(self, filename, backup=False):
        try:
            data = self.save_manager.load_from_file(filename + '.bak' if backup else filename)
            if filename != data['world_id'] + '.json':
                raise SaveError('Kayıt kimliği dosyayla uyuşmuyor.')
            world, economy, metadata = self.save_manager.restore(data)
            ui = UIManager(economy)
            ui.king_name = metadata['king_name']
            xp = XPSystem(ui)
            for key, value in metadata['xp_state'].items():
                setattr(xp, key, value)
            xp._sync_ui()
            elapsed = max(0.0, self.time_source() - world.processed_at)
            advance_production(world, economy, xp, elapsed)
            updated = self._snapshot(world, economy, xp, metadata['camera'], ui.king_name)
            # Ödül ve işlenmiş zaman kalıcı olmadan oturum yayımlanmaz.
            self.save_manager.save_world(updated)
        except (OSError, SaveError, ValueError, OverflowError) as exc:
            self._notify(f'Dünya açılamadı: {exc}')
            return False
        self.selection.clear_selection()
        self.world, self.economy, self.ui, self.xp_system = world, economy, ui, xp
        self.world.processed_at = updated['processed_at']
        self.ui.on_buy = self._enter_build_mode
        for key, value in metadata['camera'].items():
            setattr(self.camera, key, value)
        self.ai, self.battle_manager = AIController(world), BattleManager(world)
        self.construction_manager = ConstructionManager(world, economy)
        self.construction_manager.player_level = xp.level
        self.active_session, self.screen_mode = True, 'game'
        self.autosave_timer = 0.0
        self._build_mode = self.pending_confirm = None
        self._notify('Dünya açıldı; çevrimdışı süre işlendi.')
        return True

    def _finish_exit(self, destination):
        self.active_session = False
        if destination == 'quit':
            self.running = False
        else:
            self.screen_mode = 'home'
            self.records = self.save_manager.list_worlds()
        self.pending_exit = None

    def request_exit(self, destination):
        if self.screen_mode == "save_error" and self._error_elapsed:
            advance_production(self.world, self.economy, self.xp_system, self._error_elapsed)
            self._error_elapsed = 0.0
        if self.save_game():
            self._finish_exit(destination)
        else:
            self.pending_exit, self.screen_mode = destination, 'save_error'

    def _menu_action(self, action):
        if isinstance(action, tuple):
            self.load_game(action[1], backup=action[0] == 'backup')
        elif action in ('home', 'new', 'load'):
            self.screen_mode = action
            self.records = self.save_manager.list_worlds()
            if action == 'new':
                self.menu.name = ''
                pygame.key.start_text_input()
        elif action == 'create':
            pygame.key.stop_text_input()
            self.new_game(self.menu.name)
        elif action == 'quit':
            self.running = False
        elif action == 'previous':
            self.menu.page -= 1
        elif action == 'next':
            self.menu.page += 1
        elif action == 'retry':
            self.request_exit(self.pending_exit)
        elif action == 'resume':
            # Hata ekranında geçen süre üretime dahil, savaş/hareket donuktur.
            advance_production(self.world, self.economy, self.xp_system, self._error_elapsed)
            self._error_elapsed = 0.0
            self.screen_mode, self.pending_exit = 'game', None
        elif action == 'discard':
            self._finish_exit(self.pending_exit)

    def run(self):
        self._error_elapsed = 0.0
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.click_timer += dt
            self.message_timer = max(0.0, self.message_timer - dt)
            self._handle_events()
            if not self.running:
                break
            if self.screen_mode == 'game':
                self._update(dt)
                self._render()
                self._autosave(dt)
            else:
                if self.screen_mode == 'save_error':
                    self._error_elapsed += dt
                self.menu.draw(self.screen, self.screen_mode, self.records, self.message)
                pygame.display.flip()
        pygame.quit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if self.screen_mode == 'save_error':
                    continue
                if self.active_session:
                    self.request_exit('quit')
                else:
                    self.running = False
                continue
            if self.screen_mode != 'game':
                self._menu_action(self.menu.handle_event(event, self.screen_mode))
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F5:
                self.save_game()
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F10:
                self.request_exit('home')
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if pygame.Rect(980, 10, 130, 32).collidepoint(event.pos):
                    self.save_game()
                    continue
                if pygame.Rect(1120, 10, 145, 32).collidepoint(event.pos):
                    self.request_exit('home')
                    continue

            if self.pending_confirm:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    box_w, box_h = 400, 150
                    bx = (SCREEN_WIDTH - box_w) // 2
                    by = (SCREEN_HEIGHT - box_h) // 2
                    mx, my = event.pos
                    if bx + 60 <= mx <= bx + 160 and by + 80 <= my <= by + 120:
                        # Evet: remove worker and cancel production
                        b = self.pending_confirm["building"]
                        w = self.pending_confirm["worker"]
                        b.remove_worker(w)
                        b.cancel_worker_production()
                        self.pending_confirm = None
                        self._build_ui_buttons(b)
                    elif bx + 240 <= mx <= bx + 340 and by + 80 <= my <= by + 120:
                        # Hayır: keep worker, dismiss dialog
                        self.pending_confirm = None
                continue

            if self.ui.handle_event(event):
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.selection.clear_selection()
                    self.ui.clear_buttons()
                    self.ui.close_market()
                    self._build_mode = None
                elif event.key == pygame.K_1:
                    self._enter_build_mode("woodcutter")
                elif event.key == pygame.K_2:
                    self._enter_build_mode("farm")
                elif event.key == pygame.K_3:
                    self._enter_build_mode("barracks_spear_1")
                elif event.key == pygame.K_4:
                    self._enter_build_mode("house")

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self._handle_left_click(event.pos)
                elif event.button == 3:
                    self._handle_right_click(event.pos)
                elif event.button == 4:
                    self.camera.change_zoom(0.1, event.pos[0], event.pos[1])
                elif event.button == 5:
                    self.camera.change_zoom(-0.1, event.pos[0], event.pos[1])

            elif event.type == pygame.MOUSEMOTION:
                if event.buttons[1]:
                    self.camera.pan(-event.rel[0] / self.camera.zoom,
                                    -event.rel[1] / self.camera.zoom)

    def _enter_build_mode(self, building_type: str):
        self.construction_manager.player_level = self.xp_system.level
        if self.construction_manager.can_build(building_type):
            self._build_mode = building_type
        else:
            self._build_mode = None
            self._notify(self.construction_manager.last_error)

    def _handle_left_click(self, pos):
        wx, wy = self.camera.screen_to_world(pos[0], pos[1])

        is_double_click = False
        if self.click_timer < 0.3 and self.last_click_pos:
            dx = pos[0] - self.last_click_pos[0]
            dy = pos[1] - self.last_click_pos[1]
            if (dx * dx + dy * dy) ** 0.5 < 10:
                is_double_click = True

        self.click_timer = 0.0
        self.last_click_pos = pos

        if self._build_mode:
            self.construction_manager.player_level = self.xp_system.level
            building = self.construction_manager.place_building(self._build_mode, wx, wy)
            if building:
                self._build_mode = None
            else:
                self._notify(self.construction_manager.last_error)
            return

        entity = self.renderer.pick_entity_at(pos, self.world.entities)
        if entity:
            if is_double_click and isinstance(entity, Unit) and entity.is_player:
                self.selection.select_same_class(
                    entity,
                    [e for e in self.world.entities if isinstance(e, Unit) and e.is_player]
                )
            else:
                self.selection.select_single(entity)
            self._build_ui_buttons(entity)
        else:
            self.selection.clear_selection()
            self.ui.clear_buttons()

    def _build_ui_buttons(self, entity):
        self.ui.clear_buttons()
        if not entity or not isinstance(entity, Building):
            return
        if not entity.is_constructed:
            return

        pq = getattr(entity, 'production_queue', None)
        base = get_base(entity.building_type)

        unit_labels = {"worker": "İşçi", "spearman": "Mızrakçı",
                       "swordsman": "Kılıççı", "archer": "Okçu", "rider": "Atlı"}

        if entity.building_type == "townhall":
            trains = ["worker"]
        elif base == "barracks":
            trains = get_trains(entity.building_type)
        else:
            trains = []

        x = 300
        for ut in trains:
            self.ui.add_button(x, 10, 90, 30, unit_labels.get(ut, ut),
                (lambda u=ut: pq.enqueue(u)) if pq else None)
            x += 96

        # Baraka geliştirme butonu
        if base == "barracks":
            upgrade_type = get_upgrade(entity.building_type)
            if upgrade_type:
                from game.building_catalog import get_cost
                def do_upgrade(b=entity, ut=upgrade_type):
                    if not b.is_constructed:
                        return
                    from game.building_catalog import CATALOG
                    meta = CATALOG.get(ut)
                    if meta and self.ui.townhall_level < meta.get("level_req", 1):
                        return
                    cost = get_cost(ut)
                    if self.economy.can_afford(cost) and self.economy.spend(cost):
                        b.upgrade(ut)
                        self._build_ui_buttons(b)
                self.ui.add_button(700, 10, 100, 30, "Geliştir", do_upgrade)

        # Kaynak binaları: köylü atama + çalışma modları + pasif f(t) üretimi
        if base == "resource":
            def toggle_passive():
                if entity.is_producing:
                    entity.stop_production()
                else:
                    entity.start_production()
                self._build_ui_buttons(entity)

            def toggle_workers():
                if entity.worker_active:
                    entity.cancel_worker_production()
                elif entity.pending_worker_mode:
                    if entity.start_worker_production(entity.pending_worker_mode, self.economy):
                        entity.pending_worker_mode = None
                    else:
                        self._notify('Köylü atanmalı ve yeterli mücevher olmalı.')
                else:
                    self._notify('Önce bir köylü çalışma modu seç.')
                self._build_ui_buttons(entity)

            self.ui.add_button(300, 10, 175, 30,
                'Pasif: Durdur' if entity.is_producing else 'Pasif: Başlat', toggle_passive)
            self.ui.add_button(485, 10, 200, 30,
                'Köylü: Durdur' if entity.worker_active else 'Köylü: Başlat', toggle_workers)

            from game.work_modes import MODE_ORDER, WORK_MODES
            x = 300
            for m in MODE_ORDER:
                def select_mode(b=entity, mm=m):
                    if not b.worker_active:
                        b.pending_worker_mode = mm
                        self._build_ui_buttons(b)
                selected = entity.pending_worker_mode == m
                color = (80, 140, 80) if selected else (60, 60, 60)
                hover = (110, 170, 110) if selected else (90, 90, 90)
                self.ui.add_button(x, 50, 100, 30, WORK_MODES[m]["label"],
                    select_mode, color=color, hover_color=hover)
                x += 104

            # Worker exit buttons (right panel)
            self.ui.build_worker_exit_buttons(entity, on_remove=self._on_remove_worker)

    def _on_remove_worker(self, building, worker):
        if building.worker_active and len(building.assigned_workers) == 1:
            self.pending_confirm = {"building": building, "worker": worker}
            return
        building.remove_worker(worker)
        self._build_ui_buttons(building)

    def _handle_right_click(self, pos):
        wx, wy = self.camera.screen_to_world(pos[0], pos[1])
        units = self.selection.get_selected_units()
        if not units:
            return

        target = self.renderer.pick_entity_at(pos, self.world.entities)
        enemy = None
        resource = None
        res_building = None
        if isinstance(target, ResourceNode) and target.is_alive():
            resource = target
        elif (isinstance(target, Building) and target.is_alive()
              and target.is_constructed and get_base(target.building_type) == "resource"):
            res_building = target
        elif isinstance(target, Unit) and not target.is_player and target.is_alive():
            enemy = target

        for u in units:
            if isinstance(u, Worker):
                if res_building:
                    # Kabul edilen davranış: anında ata ve bina içinde gizle.
                    res_building.assign_worker(u)
                elif resource:
                    u.assign_task("gather", resource)
                elif enemy:
                    u.task = u.task_target = None
                    u.attack_target(enemy)
                else:
                    u.task = None
                    u.move_to(wx, wy)
            elif enemy:
                u.attack_target(enemy)
            else:
                u.move_to(wx, wy)

    def _update(self, dt: float):
        for entity in list(self.world.entities):
            if isinstance(entity, Worker):
                entity.update(dt, self.world, self.economy)
            elif isinstance(entity, Unit):
                entity.update(dt)
        self.world._resolve_overlaps()
        self.battle_manager.update(dt)
        self.ai.update(dt)
        advance_production(self.world, self.economy, self.xp_system, dt)
        self.construction_manager.player_level = self.xp_system.level
        self.construction_manager.update(dt)
        for entity in self.world.entities:
            if isinstance(entity, Unit) and not entity.is_alive() and not entity.is_player:
                self.xp_system.reward_kill(entity.unit_type)
        self.world.entities = [e for e in self.world.entities if e.is_alive()]
        if self.selection.selected:
            selected = self.selection.selected[0]
            if not selected.is_alive():
                self.selection.clear_selection()
                self.ui.clear_buttons()
            elif isinstance(selected, Building):
                self._build_ui_buttons(selected)
        errors = [u.movement_error for u in self.selection.get_selected_units() if u.movement_error]
        if errors:
            self._notify(errors[0])

    def _render(self):
        self.screen.fill((0, 0, 0))
        self.renderer.draw_map(self.world)
        self.renderer.draw_entities(self.world.entities)
        for e in self.world.entities:
            if e.is_alive() and not getattr(e, "is_inside_building", None) and hasattr(e, 'stats') and hasattr(e.stats, 'hp'):
                self.renderer.draw_hp_bar(e)
            if e.is_alive() and hasattr(e, 'gather_timer') and e.gather_timer > 0:
                self.renderer.draw_gather_bar(e)
            if e.is_alive() and isinstance(e, Building):
                self.renderer.draw_building_overlays(e)

        if self._build_mode:
            mx, my = pygame.mouse.get_pos()
            wx, wy = self.camera.screen_to_world(mx, my)
            sx, sy = self.camera.world_to_screen(wx, wy)
            error = self.construction_manager.placement_error(self._build_mode, wx, wy)
            color = (255, 60, 60) if error else (0, 255, 0)
            pygame.draw.circle(self.screen, color, (int(sx), int(sy)), 20, 2)
            font = pygame.font.SysFont("arial", 14)
            label = font.render(f"İnşaat: {self._build_mode}", True, (0, 255, 0))
            self.screen.blit(label, (mx + 10, my - 20))

        self.ui.draw(self.screen, self.selection.selected)
        for rect, label in [(pygame.Rect(980, 10, 130, 32), 'Kaydet (F5)'),
                            (pygame.Rect(1120, 10, 145, 32), 'Menü (F10)')]:
            pygame.draw.rect(self.screen, (45, 60, 50), rect)
            text = self.ui.font.render(label, True, (255, 255, 255))
            self.screen.blit(text, text.get_rect(center=rect.center))
        if self.message_timer > 0:
            text = self.ui.font.render(self.message[:110], True, (255, 230, 160))
            self.screen.blit(text, (240, 60))
        if self.pending_confirm:
            self._draw_confirm_dialog()
        pygame.display.flip()

    def _draw_confirm_dialog(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        box_w, box_h = 400, 150
        bx = (SCREEN_WIDTH - box_w) // 2
        by = (SCREEN_HEIGHT - box_h) // 2
        pygame.draw.rect(self.screen, (40, 40, 40), (bx, by, box_w, box_h))
        pygame.draw.rect(self.screen, (200, 200, 200), (bx, by, box_w, box_h), 2)
        font = pygame.font.SysFont("arial", 16)
        text = font.render("Son köylü çıkarsa üretim iptal olacak. Devam?", True, (255, 255, 255))
        self.screen.blit(text, (bx + 20, by + 30))
        pygame.draw.rect(self.screen, (80, 140, 80), (bx + 60, by + 80, 100, 40))
        pygame.draw.rect(self.screen, (200, 200, 200), (bx + 60, by + 80, 100, 40), 1)
        yes = font.render("Evet", True, (255, 255, 255))
        self.screen.blit(yes, (bx + 90, by + 90))
        pygame.draw.rect(self.screen, (180, 60, 60), (bx + 240, by + 80, 100, 40))
        pygame.draw.rect(self.screen, (200, 200, 200), (bx + 240, by + 80, 100, 40), 1)
        no = font.render("Hayır", True, (255, 255, 255))
        self.screen.blit(no, (bx + 270, by + 90))

    def _autosave(self, dt: float):
        if not self.active_session:
            return
        self.autosave_timer += dt
        if self.autosave_timer >= 30:
            self.autosave_timer %= 30
            self.save_game()
