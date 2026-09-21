"""Yeni dünya, kayıt listesi ve kayıt hatası ekranları."""
from datetime import datetime
import pygame
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT


class SessionMenu:
    def __init__(self):
        self.name = ''
        self.page = 0
        self.buttons = []
        self.font = pygame.font.SysFont('arial', 18)
        self.title_font = pygame.font.SysFont('arial', 30)

    def _button(self, screen, rect, label, action, enabled=True):
        box = pygame.Rect(rect)
        pygame.draw.rect(screen, (54, 101, 72) if enabled else (65, 65, 65), box, border_radius=5)
        text = self.font.render(label, True, (245, 245, 245))
        screen.blit(text, text.get_rect(center=box.center))
        self.buttons.append((box, action, enabled))

    def draw(self, screen, mode, records, message=''):
        screen.fill((24, 30, 35))
        self.buttons = []
        title = {'home': 'CloneEmpires', 'new': 'Yeni dünya', 'load': 'Kayıtlı dünyalar',
                 'save_error': 'Kayıt tamamlanamadı'}[mode]
        screen.blit(self.title_font.render(title, True, (235, 215, 160)), (100, 60))
        if mode == 'home':
            self._button(screen, (450, 220, 380, 60), 'Yeni oyun', 'new')
            self._button(screen, (450, 300, 380, 60), 'Devam et', 'load', bool(records))
            self._button(screen, (450, 380, 380, 60), 'Çıkış', 'quit')
        elif mode == 'new':
            screen.blit(self.font.render('Dünya adı (isteğe bağlı):', True, (220, 220, 220)), (350, 210))
            pygame.draw.rect(screen, (65, 70, 78), (350, 250, 580, 50))
            screen.blit(self.font.render(self.name or 'Boş bırakırsan otomatik ad verilir', True, (230, 230, 230)), (363, 264))
            self._button(screen, (450, 340, 380, 55), 'Dünyayı oluştur', 'create')
            self._button(screen, (450, 415, 380, 50), 'Geri', 'home')
        elif mode == 'load':
            pages = max(1, (len(records) + 3) // 4)
            self.page = max(0, min(self.page, pages - 1))
            for index, record in enumerate(records[self.page * 4:self.page * 4 + 4]):
                y = 130 + index * 105
                pygame.draw.rect(screen, (42, 51, 57), (100, y, 1080, 94), border_radius=5)
                label = record['name'][:40]
                try:
                    stamp = datetime.fromtimestamp(record['saved_at']).strftime('%d.%m.%Y %H:%M') if record['saved_at'] else ''
                except (OverflowError, OSError, ValueError):
                    stamp = 'Tarih gösterilemiyor'
                detail = record['error'] or f"Seviye {record['level']}  ·  Son kayıt: {stamp}"
                screen.blit(self.font.render(label, True, (245, 225, 170)), (115, y + 12))
                screen.blit(self.font.render(detail[:95], True, (205, 205, 205)), (115, y + 48))
                self._button(screen, (1050, y + 8, 115, 34), 'Aç', ('open', record['filename']), not record['error'])
                if record['error'] and record['backup']:
                    self._button(screen, (1000, y + 50, 165, 34), 'Yedekten aç', ('backup', record['filename']))
            self._button(screen, (100, 585, 180, 45), 'Geri', 'home')
            self._button(screen, (700, 585, 160, 45), 'Önceki', 'previous', self.page > 0)
            self._button(screen, (880, 585, 160, 45), 'Sonraki', 'next', self.page + 1 < pages)
        else:
            lines = ('Oyun durumun bellekte korunuyor.',
                     'Tekrar deneyebilir veya oyuna geri dönebilirsin.',
                     'Kaydetmeden çıkarsan son kayıttan sonraki ilerleme kaybolur.')
            for i, line in enumerate(lines):
                screen.blit(self.font.render(line, True, (225, 225, 225)), (200, 200 + i * 35))
            self._button(screen, (200, 360, 250, 55), 'Tekrar dene', 'retry')
            self._button(screen, (470, 360, 250, 55), 'Oyuna dön', 'resume')
            self._button(screen, (740, 360, 300, 55), 'Kaydetmeden çık', 'discard')
        if message:
            screen.blit(self.font.render(message[:115], True, (255, 185, 135)), (100, SCREEN_HEIGHT - 50))

    def handle_event(self, event, mode):
        if mode == 'new':
            if event.type == pygame.TEXTINPUT:
                self.name = (self.name + ''.join(c for c in event.text if c.isprintable()))[:40]
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.name = self.name[:-1]
                elif event.key == pygame.K_RETURN:
                    return 'create'
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return 'resume' if mode == 'save_error' else 'home'
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, action, enabled in self.buttons:
                if enabled and rect.collidepoint(event.pos):
                    return action
        return None
